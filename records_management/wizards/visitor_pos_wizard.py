# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import UserError




class VisitorPosWizard(models.TransientModel):
    _name = "visitor.pos.wizard"
    _description = "Visitor Pos Wizard"

    # Wizard Fields
    name = fields.Char(string="Name", required=True, default="New Walk-in Service")
    pos_config_id = fields.Many2one(
        "pos.config",
        string="Point of Sale",
        required=True,
        help="The Point of Sale configuration to use.",
    )
    pos_session_id = fields.Many2one(
        "pos.session",
        string="POS Session",
        readonly=True,
        help="The current POS session.",
    )

    # Customer Information
    existing_customer_id = fields.Many2one("res.partner", string="Existing Customer")
    visitor_name = fields.Char(string="New Customer Name")
    visitor_email = fields.Char(string="New Customer Email")
    visitor_phone = fields.Char(string="New Customer Phone")
    create_new_customer = fields.Boolean(string="Create New Customer", default=False)

    # Service Details
    service_type = fields.Selection(
        [("shredding", "Shredding"), ("storage", "Storage"), ("scanning", "Scanning")],
        string="Service Type",
        required=True,
    )
    document_type = fields.Many2one("records.document.type", string="Document Type")
    quantity = fields.Float(string="Quantity", default=1.0)
    unit_price = fields.Float(string="Unit Price", digits="Product Price")
    total_amount = fields.Float(
        string="Total Amount",
        compute="_compute_total_amount",
        readonly=True,
        digits="Account",
    )

    # Payment
    payment_method_id = fields.Many2one(
        "pos.payment.method", string="Payment Method", required=True
    )

    @api.depends("quantity", "unit_price")
    def _compute_total_amount(self):
        for wizard in self:
            wizard.total_amount = wizard.quantity * wizard.unit_price

    def action_execute(self):
        """Execute the wizard action: create customer, create order, and process payment."""

        self.ensure_one()

        partner = self._find_or_create_customer()
        order = self._create_pos_order(partner)

        # This would typically open the POS payment screen
        # For this wizard, we simulate the payment creation
        self._create_payment(order)

        order.action_pos_order_paid()

        return {"type": "ir.actions.act_window_close"}

    def _find_or_create_customer(self):
        if self.create_new_customer:
            if not self.visitor_name:
                raise UserError(_("A name is required to create a new customer."))
            return self.env["res.partner"].create(
                {
                    "name": self.visitor_name,
                    "email": self.visitor_email,
                    "phone": self.visitor_phone,
                }
            )
        return self.existing_customer_id

    def _create_pos_order(self, partner):
        product = self._get_service_product()
        order_line = (
            0,
            0,
            {
                "product_id": product.id,
                "qty": self.quantity,
                "price_unit": self.unit_price,
                "price_subtotal": self.total_amount,
                "price_subtotal_incl": self.total_amount,
            },
        )

        return self.env["pos.order"].create(
            {
                "session_id": self.pos_config_id.current_session_id.id,
                "partner_id": partner.id if partner else False,
                "lines": [order_line],
                "amount_total": self.total_amount,
                "amount_paid": 0,
                "amount_tax": 0,
                "amount_return": 0,
            }
        )

    def _get_service_product(self):
        # This logic should be adapted to how service products are configured
        product_map = {
            "shredding": "walkin_shredding_service",
            "storage": "walkin_storage_service",
            "scanning": "walkin_scanning_service",
        }
        product = self.env.ref(
            f"records_management.{product_map.get(self.service_type)}",
            raise_if_not_found=False,
        )
        if not product:
            raise UserError(
                _("The product for the selected service type is not configured.")
            )
        return product

    def _create_payment(self, order):
        self.env["pos.payment"].create(
            {
                "pos_order_id": order.id,
                "payment_method_id": self.payment_method_id.id,
                "amount": self.total_amount,
            }
        )

    def action_cancel(self):
        """Cancel the wizard."""

        self.ensure_one()
        return {"type": "ir.actions.act_window_close"}
