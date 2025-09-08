# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class VisitorPosWizard(models.TransientModel):
    _name = "visitor.pos.wizard"
    _description = "Visitor POS Wizard"

    # ============================================================================
    # FIELDS - Step 1: Visitor & Service Selection
    # ============================================================================
    visitor_id = fields.Many2one(
        "visitor",
        string="Visitor",
        required=True,
        help="Select the visitor to create a POS order for.",
    )
    pos_config_id = fields.Many2one(
        "pos.config",
        string="Point of Sale",
        required=True,
        default=lambda self: self.env["pos.config"].search([], limit=1),
        help="The POS configuration to use for this transaction.",
    )

    # Service Details
    product_id = fields.Many2one(
        "product.product",
        string="Service/Product",
        required=True,
        domain="[('sale_ok', '=', True), ('available_in_pos', '=', True)]",
        help="Product or service to include on the generated POS order.",
    )
    quantity = fields.Float(string="Quantity", default=1.0, required=True)
    unit_price = fields.Float(
        string="Unit Price",
        compute="_compute_unit_price",
        readonly=True,
        help="Computed from the customer's pricelist (or POS configuration pricelist) for a single unit.",
    )

    # Customer Information (pre-filled from visitor)
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        help="Selected or newly created customer to associate with the POS order. Editable when creating a new one.",
    )
    create_new_customer = fields.Boolean(
        string="Create New Customer from Visitor",
        help="If the visitor is not linked to a customer, check this to create one.",
    )

    # Internal helper (not exposed) to hold derived pricelist for compute clarity (no store required)
    pricelist_id = fields.Many2one(
        "product.pricelist",
        string="Effective Pricelist",
        compute="_compute_pricelist_id",
        help="Pricelist used for computing the unit price (partner pricelist first, otherwise POS config pricelist).",
    )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("visitor_id")
    def _onchange_visitor_id(self):
        """Prefill partner or prompt creation depending on visitor linkage."""
        if not self.visitor_id:
            return
        if self.visitor_id.partner_id:
            # Existing linked partner → no new customer creation needed
            self.partner_id = self.visitor_id.partner_id
            self.create_new_customer = False
        else:
            # No linked partner → allow user to create/choose one
            self.partner_id = False
            self.create_new_customer = True
            return {
                "warning": {
                    "title": _("No Linked Customer"),
                    "message": _(
                        "This visitor is not linked to a customer record. You can create or select one using the Customer field."
                    ),
                }
            }

    @api.onchange("partner_id")
    def _onchange_partner_id(self):
        """If user selects a partner manually while create_new_customer is checked, defer linking until action."""
        # Recompute unit price contextually when partner changes (compute handles but onchange improves reactivity)
        for wizard in self:
            wizard._compute_unit_price()

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be positive."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_create_pos_order(self):
        """Creates a Point of Sale order from the wizard data with dynamic pricelist pricing."""
        self.ensure_one()

        pos_session = self.env["pos.session"].search(
            [("config_id", "=", self.pos_config_id.id), ("state", "=", "opened")],
            limit=1,
        )

        if not pos_session:
            raise UserError(
                _(
                    "No active POS session found for '%s'. Please open a session."
                )
                % self.pos_config_id.name
            )

        customer = self.partner_id
        # Create or link customer as needed
        if self.create_new_customer:
            if not customer:
                # Create from visitor details
                customer = self._create_customer_from_visitor()
            # Link newly created / selected partner back to visitor if not already linked
            if customer and not self.visitor_id.partner_id:
                self.visitor_id.partner_id = customer.id

        order_vals = self._prepare_pos_order_values(pos_session, customer)
        pos_order = self.env["pos.order"].create(order_vals)

        # Return an action to open the created POS order
        return {
            "type": "ir.actions.act_window",
            "name": _("POS Order"),
            "res_model": "pos.order",
            "res_id": pos_order.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _prepare_pos_order_values(self, pos_session, customer):
        """Prepare the dictionary of values for the new POS order."""
        self.ensure_one()
        order_line_vals = (
            0,
            0,
            {
                "product_id": self.product_id.id,
                "qty": self.quantity,
                "price_unit": self.unit_price,
                "full_product_name": self.product_id.display_name,
            },
        )

        return {
            "session_id": pos_session.id,
            "partner_id": customer.id if customer else False,
            "lines": [order_line_vals],
            "pricelist_id": customer.property_product_pricelist.id if customer else pos_session.config_id.pricelist_id.id,
        }

    def _create_customer_from_visitor(self):
        """Create a new customer (res.partner) from the visitor's details."""
        self.ensure_one()
        if not self.visitor_id.name:
            raise UserError(_("Visitor must have a name to create a customer record."))
        partner_vals = {
            "name": self.visitor_id.name,
            "company_name": self.visitor_id.visitor_company,
            "phone": self.visitor_id.phone,
            "email": self.visitor_id.email,
        }
        new_partner = self.env["res.partner"].create(partner_vals)
        return new_partner

    # =========================================================================
    # COMPUTE HELPERS
    # =========================================================================
    @api.depends("partner_id", "pos_config_id")
    def _compute_pricelist_id(self):
        for wizard in self:
            pricelist = False
            if wizard.partner_id and wizard.partner_id.property_product_pricelist:
                pricelist = wizard.partner_id.property_product_pricelist
            elif wizard.pos_config_id and wizard.pos_config_id.pricelist_id:
                pricelist = wizard.pos_config_id.pricelist_id
            wizard.pricelist_id = pricelist

    @api.depends("product_id", "partner_id", "pos_config_id")
    def _compute_unit_price(self):
        for wizard in self:
            price = 0.0
            product = wizard.product_id
            if not product:
                wizard.unit_price = 0.0
                continue
            # Determine pricelist
            pricelist = (
                wizard.partner_id.property_product_pricelist
                if wizard.partner_id and wizard.partner_id.property_product_pricelist
                else wizard.pos_config_id.pricelist_id
            )
            if pricelist:
                try:
                    # Use standard pricelist API for unit price
                    price = pricelist.get_product_price(product, 1.0, wizard.partner_id or False)
                except Exception:
                    # Fallback to list price if any incompatibility
                    price = product.lst_price
            else:
                price = product.lst_price
            wizard.unit_price = price
