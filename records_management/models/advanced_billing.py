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
    payment_terms = fields.Selection(
        [
            ("immediate", "Immediate Payment"),
            ("net_15", "Net 15 Days"),
            ("net_30", "Net 30 Days"),
            ("net_45", "Net 45 Days"),
            ("net_60", "Net 60 Days"),
            ("custom", "Custom Terms"),
        ],
        string="Payment Terms",
        default="net_30",
    )

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
    message_ids = fields.One2many(
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities", domain=[('res_model', '=', _name)]
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", domain=[('res_model', '=', _name)]
    )
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
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Line Description", compute="_compute_name", store=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # BILLING DETAILS
    # ============================================================================
    billing_id = fields.Many2one(
        "advanced.billing", string="Billing", required=True, ondelete="cascade"
    )
    product_id = fields.Many2one("product.product", string="Product")
    quantity = fields.Float(string="Quantity", default=1.0)
    price_unit = fields.Float(string="Unit Price")
    price_total = fields.Float(
        string="Total", compute="_compute_price_total", store=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("product_id", "quantity")
    def _compute_name(self):
        for line in self:
            if line.product_id:
                line.name = f"{line.product_id.name} x {line.quantity}"
            else:
                line.name = f"Billing Line {line.id or 'Unsaved'}"

    @api.depends("quantity", "price_unit")
    def _compute_price_total(self):
        for line in self:
            line.price_total = line.quantity * line.price_unit


class RecordsAdvancedBillingPeriod(models.Model):
    _name = "records.advanced.billing.period"
    _description = "Advanced Billing Period"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Period Name", compute="_compute_name", store=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # PERIOD DETAILS
    # ============================================================================
    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    billing_ids = fields.One2many(
        "advanced.billing", "billing_period_id", string="Billings"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("start_date", "end_date")
    def _compute_name(self):
        for period in self:
            if period.start_date and period.end_date:
                period.name = f"Billing Period {period.start_date} - {period.end_date}"
            else:
                period.name = f"Billing Period {period.id or 'Unsaved'}"
                # ============================================================================
                # AUTO-GENERATED ACTION METHODS (from comprehensive validation)
                # ============================================================================
    # ============================================================================

    def action_generate_storage_lines(self):
        """Generate Storage Lines - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_generate_storage_lines_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_generate_service_lines(self):
        """Generate Service Lines - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_generate_service_lines_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

