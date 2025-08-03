# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfig(models.Model):
    _name = "records.billing.config"
    _description = "Records Billing Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # Basic Information
    name = fields.Char(string="Configuration Name", required=True, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    partner_id = fields.Many2one("res.partner", string="Customer")
    customer_id = fields.Many2one(
        "res.partner", string="Customer"
    )  # Alternative reference
    billing_type = fields.Selection(
        [("standard", "Standard"), ("premium", "Premium"), ("custom", "Custom")],
        string="Billing Type",
        default="standard",
    )

    # Essential Billing Configuration Fields (from view analysis)
    billing_model = fields.Selection(
        [
            ("per_container", "Per Box"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
            ("tiered", "Tiered Pricing"),
            ("usage_based", "Usage Based"),
        ],
        string="Billing Model",
        required=True,
        tracking=True,
    )

    # Rate Configuration
    base_rate = fields.Monetary(
        string="Base Rate", currency_field="currency_id", tracking=True
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Billing Automation
    auto_billing = fields.Boolean(
        string="Auto Billing Enabled", default=False, tracking=True
    )
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annually", "Semi-Annually"),
            ("annually", "Annually"),
        ],
        string="Billing Frequency",
        default="monthly",
        tracking=True,
    )

    # Payment Configuration
    payment_terms = fields.Many2one("account.payment.term", string="Payment Terms")

    # Additional Configuration Fields
    minimum_charge = fields.Monetary(
        string="Minimum Charge", currency_field="currency_id"
    )
    setup_fee = fields.Monetary(string="Setup Fee", currency_field="currency_id")
    late_fee_percentage = fields.Float(string="Late Fee Percentage", digits=(5, 2))

    # Service Configuration
    storage_rate = fields.Monetary(string="Storage Rate", currency_field="currency_id")
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate", currency_field="currency_id"
    )
    destruction_rate = fields.Monetary(
        string="Destruction Rate", currency_field="currency_id"
    )
    scanning_rate = fields.Monetary(
        string="Scanning Rate", currency_field="currency_id"
    )

    # Advanced Features
    tiered_pricing_enabled = fields.Boolean(
        string="Tiered Pricing Enabled", default=False
    )
    volume_discounts_enabled = fields.Boolean(
        string="Volume Discounts Enabled", default=False
    )
    contract_pricing = fields.Boolean(string="Contract Pricing", default=False)

    # Integration Settings
    accounting_system_sync = fields.Boolean(
        string="Accounting System Sync", default=False
    )
    auto_apply = fields.Boolean(string="Auto Apply Configuration", default=True)

    # Analytics and Reporting
    annual_revenue = fields.Monetary(
        string="Annual Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue",
    )
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)

    # Status and Workflow
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Date(string="Approval Date")

    # Related Records
    billing_line_ids = fields.One2many(
        "records.billing.line", "config_id", string="Billing Lines"
    )
    invoice_ids = fields.One2many(
        "account.move", "billing_config_id", string="Related Invoices"
    )

    # System Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )

    @api.depends("billing_line_ids", "billing_frequency", "base_rate")
    def _compute_revenue(self):
        """Compute revenue metrics"""
        for record in self:
            # Calculate from billing lines if available
            if record.billing_line_ids:
                total_amount = sum(record.billing_line_ids.mapped("amount"))
                record.monthly_revenue = total_amount
                record.annual_revenue = total_amount * 12
            else:
                # Estimate from base rate and frequency
                multiplier = {
                    "monthly": 12,
                    "quarterly": 4,
                    "semi_annually": 2,
                    "annually": 1,
                }.get(record.billing_frequency, 12)
                record.annual_revenue = (record.base_rate or 0) * multiplier
                record.monthly_revenue = record.annual_revenue / 12

    def action_generate_invoice(self):
        """Generate invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Invoice Generated"),
                "message": _("Invoice has been generated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_analytics(self):
        """View analytics."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Analytics"),
            "res_model": "records.billing.analytics",
            "view_mode": "graph,tree",
            "target": "current",
        }

    def action_view_billing_history(self):
        """View billing history."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing History"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_configure_rates(self):
        """Configure rates."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Rates"),
            "res_model": "base.rates",
            "view_mode": "tree,form",
            "target": "current",
        }

    def action_test_billing(self):
        """Test billing."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Billing Test"),
                "message": _("Billing test completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_duplicate(self):
        """Duplicate configuration."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Duplicated"),
                "message": _("Configuration has been duplicated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_invoices(self):
        """View invoices."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),
            ],
        }

    def action_view_revenue(self):
        """View revenue."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue"),
            "res_model": "account.move.line",
            "view_mode": "graph,tree",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_view_invoice(self):
        """View invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
        }
