# -*- coding: utf-8 -*-
"""
Customer Billing Profile Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerBillingProfile(models.Model):
    """
    Customer Billing Profile - Manages billing configurations for customers
    """

    _name = "records.customer.billing.profile"
    _description = "Customer Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Profile Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    description = fields.Text(string="Description", tracking=True)

    # ============================================================================
    # CUSTOMER INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )

    # ============================================================================
    # BILLING CYCLES AND SCHEDULING
    # ============================================================================
    storage_billing_cycle = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("custom", "Custom"),
        ],
        string="Storage Billing Cycle",
        default="monthly",
        tracking=True,
    )

    service_billing_cycle = fields.Selection(
        [
            ("immediate", "Immediate"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("custom", "Custom"),
        ],
        string="Service Billing Cycle",
        default="immediate",
        tracking=True,
    )

    next_storage_billing_date = fields.Date(
        string="Next Storage Billing Date",
        compute="_compute_next_storage_billing_date",
        store=True,
    )

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_method = fields.Selection(
        [
            ("automatic", "Automatic"),
            ("manual", "Manual Review Required"),
            ("approval", "Approval Required"),
        ],
        string="Billing Method",
        default="automatic",
    )

    invoice_delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("postal", "Postal Mail"),
            ("portal", "Customer Portal"),
            ("both", "Email + Portal"),
        ],
        string="Invoice Delivery",
        default="email",
    )

    preferred_contact_method = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("portal", "Customer Portal"),
        ],
        string="Preferred Contact Method",
        default="email",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("terminated", "Terminated"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # FINANCIAL SETTINGS
    # ============================================================================
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    credit_limit = fields.Monetary(string="Credit Limit", currency_field="currency_id")
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

    # Billing rates
    storage_rate_per_box = fields.Monetary(
        string="Storage Rate per Box", currency_field="currency_id"
    )
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate", currency_field="currency_id"
    )
    destruction_rate = fields.Monetary(
        string="Destruction Rate", currency_field="currency_id"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    contact_count = fields.Integer(
        string="Contact Count", compute="_compute_contact_count"
    )
    current_balance = fields.Monetary(
        string="Current Balance",
        compute="_compute_current_balance",
        currency_field="currency_id",
    )
    payment_reliability_score = fields.Float(
        string="Payment Reliability Score", compute="_compute_payment_reliability"
    )

    # ============================================================================
    # COMMUNICATION PREFERENCES
    # ============================================================================
    send_billing_notifications = fields.Boolean(
        string="Send Billing Notifications", default=True
    )
    send_overdue_reminders = fields.Boolean(
        string="Send Overdue Reminders", default=True
    )
    billing_email = fields.Char(string="Billing Email")
    billing_phone = fields.Char(string="Billing Phone")

    # ============================================================================
    # POLICY SETTINGS
    # ============================================================================
    retention_policy_billing = fields.Selection(
        [
            ("standard", "Standard Retention"),
            ("extended", "Extended Retention"),
            ("permanent", "Permanent Retention"),
            ("custom", "Custom Policy"),
        ],
        string="Retention Policy Billing",
        default="standard",
    )

    auto_renew_contracts = fields.Boolean(string="Auto-Renew Contracts", default=False)
    require_approval_over_amount = fields.Monetary(
        string="Require Approval Over Amount",
        currency_field="currency_id",
        help="Invoices over this amount require approval",
    )

    # ============================================================================
    # DATES AND TRACKING
    # ============================================================================
    profile_start_date = fields.Date(
        string="Profile Start Date", default=fields.Date.today
    )
    last_billing_date = fields.Date(string="Last Billing Date")
    last_payment_date = fields.Date(string="Last Payment Date")

    # ============================================================================
    # NOTES AND COMMENTS
    # ============================================================================
    billing_notes = fields.Text(string="Billing Notes")
    special_instructions = fields.Text(string="Special Instructions")
    internal_notes = fields.Text(string="Internal Notes")

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    def _compute_contact_count(self):
        """Count related billing contacts"""
        for record in self:
            # Simple count - in real implementation would count related contacts
            record.contact_count = 1

    @api.depends("storage_billing_cycle", "last_billing_date")
    def _compute_next_storage_billing_date(self):
        """Calculate next billing date based on cycle"""
        for record in self:
            if record.last_billing_date and record.storage_billing_cycle:
                from dateutil.relativedelta import relativedelta

                last_date = record.last_billing_date

                if record.storage_billing_cycle == "monthly":
                    record.next_storage_billing_date = last_date + relativedelta(
                        months=1
                    )
                elif record.storage_billing_cycle == "quarterly":
                    record.next_storage_billing_date = last_date + relativedelta(
                        months=3
                    )
                elif record.storage_billing_cycle == "semi_annual":
                    record.next_storage_billing_date = last_date + relativedelta(
                        months=6
                    )
                elif record.storage_billing_cycle == "annual":
                    record.next_storage_billing_date = last_date + relativedelta(
                        years=1
                    )
                else:
                    record.next_storage_billing_date = False
            else:
                record.next_storage_billing_date = fields.Date.today()

    def _compute_current_balance(self):
        """Calculate current outstanding balance"""
        for record in self:
            # Simplified calculation - in real implementation would sum unpaid invoices
            record.current_balance = 0.0

    @api.depends("partner_id")
    def _compute_payment_reliability(self):
        """Calculate payment reliability score"""
        for record in self:
            # Simplified score - in real implementation would analyze payment history
            record.payment_reliability_score = 85.0

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_activate_profile(self):
        """Activate the billing profile"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError("Only draft profiles can be activated")

        self.write({"state": "active", "profile_start_date": fields.Date.today()})
        self.message_post(body="Billing profile activated")

    def action_suspend_profile(self):
        """Suspend the billing profile"""
        self.ensure_one()
        if self.state != "active":
            raise UserError("Only active profiles can be suspended")

        self.write({"state": "suspended"})
        self.message_post(body="Billing profile suspended")

    def action_terminate_profile(self):
        """Terminate the billing profile"""
        self.ensure_one()
        if self.state in ["terminated"]:
            raise UserError("Profile is already terminated")

        self.write({"state": "terminated"})
        self.message_post(body="Billing profile terminated")

    def action_generate_invoice(self):
        """Generate invoice based on profile settings"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generate Invoice",
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_billing_profile_id": self.id,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("credit_limit")
    def _check_credit_limit(self):
        """Validate credit limit is positive"""
        for record in self:
            if record.credit_limit and record.credit_limit < 0:
                raise ValidationError("Credit limit must be positive")

    @api.constrains("storage_rate_per_box", "retrieval_rate", "destruction_rate")
    def _check_rates(self):
        """Validate billing rates are positive"""
        for record in self:
            rates = [
                record.storage_rate_per_box,
                record.retrieval_rate,
                record.destruction_rate,
            ]
            if any(rate and rate < 0 for rate in rates):
                raise ValidationError("Billing rates must be positive")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create for automatic naming"""
        for vals in vals_list:
            if "name" not in vals or vals["name"] == "/":
                partner = self.env["res.partner"].browse(vals.get("partner_id"))
                vals["name"] = (
                    f"Billing Profile - {partner.name}"
                    if partner
                    else "New Billing Profile"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write for state change tracking"""
        if "state" in vals:
            for record in self:
                old_state = record.state
                new_state = vals["state"]
                if old_state != new_state:
                    record.message_post(
                        body=f"Profile state changed from {old_state} to {new_state}"
                    )
        return super().write(vals)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name}"
            if record.partner_id:
                name += f" ({record.partner_id.name})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name or customer name"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("partner_id.name", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
