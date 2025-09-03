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
    )
    quantity = fields.Float(
        string="Quantity", default=1.0, required=True
    )
    unit_price = fields.Float(
        string="Unit Price", related="product_id.lst_price", readonly=True
    )

    # Customer Information (pre-filled from visitor)
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="visitor_id.partner_id",
        readonly=True,
    )
    create_new_customer = fields.Boolean(
        string="Create New Customer from Visitor",
        help="If the visitor is not linked to a customer, check this to create one.",
    )

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("visitor_id")
    def _onchange_visitor_id(self):
        """Warn if the visitor is not linked to a customer."""
        if self.visitor_id and not self.visitor_id.partner_id:
            self.create_new_customer = True
            return {
                "warning": {
                    "title": _("No Linked Customer"),
                    "message": _(
                        "This visitor is not linked to a customer record. A new customer will be created."
                    ),
                }
            }
        else:
            self.create_new_customer = False

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
        """Creates a Point of Sale order from the wizard data."""
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
        if self.create_new_customer and not customer:
            customer = self._create_customer_from_visitor()

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
        order_line_vals = (0, 0, {"product_id": self.product_id.id, "qty": self.quantity, "price_unit": self.unit_price, "full_product_name": self.product_id.display_name})

        return {
            "session_id": pos_session.id,
            "partner_id": customer.id if customer else False,
            "lines": [order_line_vals],
            "pricelist_id": customer.property_product_pricelist.id if customer else pos_session.config_id.pricelist_id.id,
        }

    def _create_customer_from_visitor(self):
        """Creates a new customer (res.partner) from the visitor's details."""
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
        self.visitor_id.partner_id = new_partner.id  # Link back to visitor
        self.message_post(body=_("Created new customer: %s", new_partner.name))
        return new_partner
