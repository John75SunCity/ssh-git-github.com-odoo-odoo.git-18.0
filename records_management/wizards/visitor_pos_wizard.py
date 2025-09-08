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
    help="Selected or newly created customer to associate with the POS order. Editable when 'Create New Customer' is enabled.",
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
        """When partner changes: recompute unit price and reprice service lines."""
        for wizard in self:
            wizard._compute_unit_price()
            wizard._reprice_service_items()

    @api.onchange("pricelist_id")
    def _onchange_pricelist_id(self):  # pricelist_id is computed; triggered indirectly when partner/config changes
        for wizard in self:
            wizard._reprice_service_items()

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

    # =========================================================================
    # REPRICING LOGIC FOR SERVICE ITEM LINES
    # =========================================================================
    def _reprice_service_items(self):
        """Recompute unit price, discount, subtotal and aggregated totals for service_item_ids.

        Expected line fields (from view): product_id, quantity, unit_price, discount_percent, subtotal, tax_id.
        Aggregates updated: base_amount, total_discount, tax_amount, total_amount.
        """
        self.ensure_one()
        if not self.service_item_ids:
            # Still recompute header totals to zero if empty
            self._update_pricing_totals()
            return
        partner = self.partner_id
        pricelist = None
        if partner and partner.property_product_pricelist:
            pricelist = partner.property_product_pricelist
        elif self.pos_config_id and self.pos_config_id.pricelist_id:
            pricelist = self.pos_config_id.pricelist_id
        for line in self.service_item_ids:
            product = line.product_id
            if not product:
                continue
            # Compute base price via pricelist (qty for future volume rules; here per unit then * quantity)
            price_unit = product.lst_price
            if pricelist:
                try:
                    price_unit = pricelist.get_product_price(product, 1.0, partner or False)
                except Exception:
                    price_unit = product.lst_price
            line.unit_price = price_unit
            # Apply discount percent if present to compute subtotal before tax
            qty = line.quantity or 0.0
            discount = (line.discount_percent or 0.0) / 100.0
            line.subtotal = price_unit * qty * (1 - discount)
            # Taxes recomputed only if tax_id present; store-only wizard assumption (no tax engine invocation)
        self._update_pricing_totals()

    def _update_pricing_totals(self):
        """Aggregate wizard monetary totals from service_item_ids and express surcharge logic."""
        base = 0.0
        discount_total = 0.0
        tax_total = 0.0  # Placeholder: real tax computation could use tax_id.compute_all
        for line in self.service_item_ids:
            qty = line.quantity or 0.0
            unit_price = line.unit_price or 0.0
            line_discount = (line.discount_percent or 0.0) / 100.0
            base += unit_price * qty
            discount_total += unit_price * qty * line_discount
            tax_total += 0.0  # Extend if tax computation needed
        # Express surcharge simple multiplier (placeholder: could link to config)
        express = 0.0
        if getattr(self, 'express_service', False):
            express = base * 0.15  # 15% surcharge example
        total = base - discount_total + express + tax_total
        # Assign to monetary fields if defined
        if 'base_amount' in self._fields:
            self.base_amount = base
        if 'total_discount' in self._fields:
            self.total_discount = discount_total
        if 'express_surcharge' in self._fields:
            self.express_surcharge = express
        if 'tax_amount' in self._fields:
            self.tax_amount = tax_total
        if 'total_amount' in self._fields:
            self.total_amount = total
