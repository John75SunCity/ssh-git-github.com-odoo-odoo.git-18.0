# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class AdvancedBilling(models.Model):
    _name = "advanced.billing"
    _description = "Advanced Billing"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # Billing fields
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    billing_period_id = fields.Many2one(
        "records.advanced.billing.period", string="Billing Period"
    )
    currency_id = fields.Many2one("res.currency", string="Currency")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    payment_term_id = fields.Many2one("account.payment.term", string="Payment Terms")

    # State management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("invoiced", "Invoiced"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Mail thread fields
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )

    # Action methods
    def action_confirm(self):
        """Confirm billing"""
        self.ensure_one()
        self.write({"state": "confirmed"})

    def action_generate_invoice(self):
        """Generate invoice"""
        self.ensure_one()
        # Invoice generation logic here
        self.write({"state": "invoiced"})

    def action_cancel(self):
        """Cancel billing"""
        self.ensure_one()
        self.write({"state": "cancelled"})


class AdvancedBillingLine(models.Model):
    _name = "advanced.billing.line"
    _description = "Advanced Billing Line"

    billing_id = fields.Many2one(
        "advanced.billing", string="Billing", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    price_unit = fields.Float(string="Unit Price")
    price_total = fields.Float(
        string="Total", compute="_compute_price_total", store=True
    )

    @api.depends("quantity", "price_unit")
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit


class RecordsAdvancedBillingPeriod(models.Model):
    _name = "records.advanced.billing.period"
    _description = "Advanced Billing Period"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Name", required=True)
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    billing_ids = fields.One2many(
        "advanced.billing", "billing_period_id", string="Billings"
    )
