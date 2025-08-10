# -*- coding: utf-8 -*-
"""
Records Billing Configuration Module

This module provides advanced billing configuration management for the Records Management System.
It implements comprehensive billing automation with support for multiple billing frequencies,
prepaid services, proration, and detailed audit trails.

Key Features:
- Multiple billing frequencies (monthly, quarterly, annually, on-demand)
- Prepaid billing support with discount calculations and validation
- Advanced rate configuration with service-specific pricing
- Multi-currency support with proper currency field relationships
- Comprehensive audit trails with secure logging and timestamps
- Customer assignment with department-level billing management
- Minimum charge enforcement and proration capabilities
- Enterprise-grade approval workflows and notification systems

Business Processes:
1. Configuration Setup: Define billing frequencies, rates, and customer assignments
2. Rate Management: Configure service-specific rates with validation and constraints
3. Prepaid Processing: Handle prepaid billing with discount calculations and validation
4. Audit Compliance: Maintain complete audit trails for all billing configuration changes
5. Invoice Automation: Generate invoices automatically based on configured frequencies
6. Customer Notifications: Send billing-related notifications to stakeholders

Technical Implementation:
- Modern Odoo 18.0 patterns with mail.thread inheritance
- Secure domain filtering preventing data leakage between customers
- Comprehensive validation with @api.constrains decorators
- Proper relationship management with One2many/Many2one integrity
- Currency field validation and multi-company support

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfig(models.Model):
    _name = "records.billing.config"
    _description = "Records Billing Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Configuration Name", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Configuration Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Billing Manager",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("on_demand", "On Demand"),
        ],
        string="Billing Frequency",
        default="monthly",
    )

    billing_day = fields.Selection(
        [
            ("1", "1st of Month"),
            ("15", "15th of Month"),
            ("30", "Last Day of Month"),
        ],
        string="Billing Day",
        default="1",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # Rate Configuration
    default_storage_rate = fields.Monetary(
        string="Default Storage Rate",
        currency_field="currency_id",
        help="Default monthly storage rate per box",
    )
    default_retrieval_rate = fields.Monetary(
        string="Default Retrieval Rate",
        currency_field="currency_id",
        help="Default rate per retrieval request",
    )
    default_destruction_rate = fields.Monetary(
        string="Default Destruction Rate",
        currency_field="currency_id",
        help="Default rate per destruction certificate",
    )

    # ============================================================================
    # ADVANCED SETTINGS
    # ============================================================================
    auto_invoice = fields.Boolean(
        string="Auto Generate Invoices",
        default=True,
        help="Automatically generate invoices based on billing frequency",
    )
    prorate_charges = fields.Boolean(
        string="Prorate Charges",
        default=True,
        help="Prorate charges for partial billing periods",
    )

    minimum_charge = fields.Monetary(
        string="Minimum Monthly Charge",
        currency_field="currency_id",
        help="Minimum charge per billing cycle (applies only when billing for a single month)",
    )

    # Prepaid Billing Support
    prepaid_enabled = fields.Boolean(
        string="Enable Prepaid Billing",
        default=False,
        help="Allow customers to prepay for services",
    )
    prepaid_discount_rate = fields.Float(
        string="Prepaid Discount Rate (%)",
        help="Discount percentage for prepaid services",
    )
    prepaid_minimum_months = fields.Integer(
        string="Minimum Prepaid Months",
        default=3,
        help="Minimum months required for prepaid billing",
    )
    prepaid_maximum_months = fields.Integer(
        string="Maximum Prepaid Months",
        default=24,
        help="Maximum months allowed for prepaid billing",
    )

    # ============================================================================
    # AUDIT & COMPLIANCE
    # ============================================================================
    audit_trail_ids = fields.One2many(
        "records.billing.config.audit",
        "config_id",
        string="Audit Trail",
        readonly=True,
        help="Log of configuration changes. This field is readonly and is updated programmatically via the _log_audit_trail method.",
    )
    last_modified_date = fields.Datetime(
        string="Last Modified",
        default=lambda self: fields.Datetime.now(),
        readonly=True,
    )
    last_modified_by = fields.Many2one(
        "res.users", string="Last Modified By", readonly=True
    )

    # ============================================================================
    # RELATIONSHIP FIELDS (PROPER ODOO 18.0 PATTERNS)
    # ============================================================================
    partner_ids = fields.Many2many(
        "res.partner",
        "billing_config_partner_rel",
        "config_id",
        "partner_id",
        string="Assigned Customers",
        domain="[('is_company', '=', True)]",
    )

    rate_line_ids = fields.One2many(
        "records.billing.config.line", "config_id", string="Rate Configuration Lines"
    )

    # Mail Framework Fields (SECURE - No domains needed)
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    customer_count = fields.Integer(
        string="Customer Count", compute="_compute_customer_count", store=True
    )
    rate_count = fields.Integer(
        string="Rate Lines Count", compute="_compute_rate_count", store=True
    )
    is_active_config = fields.Boolean(
        string="Is Active Configuration",
        compute="_compute_is_active_config",
        store=True,
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("partner_ids")
    def _compute_customer_count(self):
        for record in self:
            record.customer_count = len(record.partner_ids)

    @api.depends("rate_line_ids")
    def _compute_rate_count(self):
        for record in self:
            record.rate_count = len(record.rate_line_ids)

    @api.depends("state", "active")
    def _compute_is_active_config(self):
        for record in self:
            record.is_active_config = record.active and record.state == "active"

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("prepaid_minimum_months", "prepaid_maximum_months")
    def _check_prepaid_months(self):
        for record in self:
            if record.prepaid_enabled:
                if record.prepaid_minimum_months <= 0:
                    raise ValidationError(
                        _("Prepaid minimum months must be greater than 0")
                    )
                if record.prepaid_maximum_months <= record.prepaid_minimum_months:
                    raise ValidationError(
                        _("Prepaid maximum months must be greater than minimum months")
                    )

    @api.constrains(
        "default_storage_rate", "default_retrieval_rate", "default_destruction_rate"
    )
    def _check_default_rates(self):
        for record in self:
            if record.default_storage_rate < 0:
                raise ValidationError(_("Storage rate cannot be negative"))
            if record.default_retrieval_rate < 0:
                raise ValidationError(_("Retrieval rate cannot be negative"))
            if record.default_destruction_rate < 0:
                raise ValidationError(_("Destruction rate cannot be negative"))

    @api.constrains("prepaid_discount_rate")
    def _check_discount_rate(self):
        for record in self:
            if record.prepaid_enabled and (
                record.prepaid_discount_rate < 0 or record.prepaid_discount_rate > 100
            ):
                raise ValidationError(_("Discount rate must be between 0 and 100"))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    def write(self, vals):
        # Only update audit fields if not a system or bulk update
        if not self.env.context.get("skip_audit_update"):
            vals["last_modified_date"] = fields.Datetime.now()
            vals["last_modified_by"] = self.env.user.id
        return super(RecordsBillingConfig, self).write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["last_modified_date"] = fields.Datetime.now()
            vals["last_modified_by"] = self.env.user.id
        return super(RecordsBillingConfig, self).create(vals_list)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _log_audit_trail(self, action, details=""):
        """Log actions to audit trail using related audit model"""
        self.ensure_one()
        self.env["records.billing.config.audit"].create(
            {
                "config_id": self.id,
                "action": action,
                "details": details,
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now(),
            }
        )

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    def calculate_storage_cost(self, box_count, months=1):
        """Calculate storage cost based on configuration"""
        self.ensure_one()
        storage_rate = (
            self.default_storage_rate if self.default_storage_rate is not None else 0.0
        )
        box_count = box_count if box_count is not None else 0
        months = months if months is not None else 1
        minimum_charge = self.minimum_charge if self.minimum_charge is not None else 0.0

        base_cost = storage_rate * box_count * months

        if base_cost < minimum_charge and months == 1:
            base_cost = minimum_charge

        return base_cost

    def calculate_prepaid_discount(self, amount, months):
        """Calculate prepaid discount if applicable"""
        self.ensure_one()
        prepaid_min_months = (
            self.prepaid_minimum_months if self.prepaid_minimum_months else 0
        )
        if not self.prepaid_enabled or months < prepaid_min_months:
            return 0.0

        return amount * (self.prepaid_discount_rate / 100)

    # ============================================================================
    # ACTION METHODS (SECURE IMPLEMENTATIONS)
    # ============================================================================
    def action_activate(self):
        """Activate billing configuration"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft configurations can be activated"))
        self._log_audit_trail("Configuration Activated")
        self.write(
            {
                "state": "active",
                "last_modified_date": fields.Datetime.now(),
                "last_modified_by": self.env.user.id,
            }
        )

    def action_suspend(self):
        """Suspend billing configuration"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active configurations can be suspended"))
        self._log_audit_trail("Configuration Suspended")
        self.write(
            {
                "state": "suspended",
                "last_modified_date": fields.Datetime.now(),
                "last_modified_by": self.env.user.id,
            }
        )

    def action_archive(self):
        """Archive billing configuration"""
        self.ensure_one()
        self._log_audit_trail("Configuration Archived")
        self.write(
            {
                "state": "archived",
                "active": False,
                "last_modified_date": fields.Datetime.now(),
                "last_modified_by": self.env.user.id,
            }
        )

    def action_duplicate(self):
        """Duplicate configuration"""
        self.ensure_one()
        copy = self.copy(
            {
                "name": f"{self.name} (Copy)",
                "code": f"{self.code}_copy" if self.code else False,
                "state": "draft",
            }
        )
        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Configuration"),
            "res_model": "records.billing.config",
            "res_id": copy.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_configure_rates(self):
        """Open rate configuration wizard"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Rates"),
            "res_model": "records.billing.config.line",
            "view_mode": "tree,form",
            "domain": [("config_id", "=", self.id)],
            "context": {"default_config_id": self.id},
            "target": "current",
        }

    def action_view_customers(self):
        """View assigned customers"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assigned Customers"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.partner_ids.ids)],
            "target": "current",
        }

    def action_generate_report(self):
        """Generate billing configuration report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.billing_config_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": dict(self.env.context),
        }

    def action_test_billing(self):
        """Test billing calculation"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Test Billing Calculation"),
            "res_model": "records.billing.test.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_config_id": self.id},
        }


class RecordsBillingConfigAudit(models.Model):
    _name = "records.billing.config.audit"
    _description = "Billing Configuration Audit Trail"
    _order = "timestamp desc"

    config_id = fields.Many2one(
        "records.billing.config",
        string="Configuration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    action = fields.Char(string="Action", required=True)
    details = fields.Text(string="Details")
    user_id = fields.Many2one("res.users", string="User", required=True)
    timestamp = fields.Datetime(
        string="Timestamp", required=True, default=lambda self: fields.Datetime.now()
    )


class RecordsBillingConfigLine(models.Model):
    _name = "records.billing.config.line"
    _description = "Billing Configuration Line"
    _order = "sequence, service_type"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    config_id = fields.Many2one(
        "records.billing.config",
        string="Configuration",
        required=True,
        ondelete="cascade",
        index=True,
    )
    sequence = fields.Integer(string="Sequence", default=10)
    service_type = fields.Selection(
        [
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("destruction", "Destruction"),
            ("scanning", "Scanning"),
            ("delivery", "Delivery"),
        ],
        string="Service Type",
        required=True,
    )
    name = fields.Char(string="Service Name", required=True)
    rate = fields.Monetary(string="Rate", currency_field="currency_id", required=True)
    currency_id = fields.Many2one(
        "res.currency", related="config_id.currency_id", store=True, readonly=True
    )
    unit_type = fields.Selection(
        [
            ("per_box", "Per Box"),
            ("per_request", "Per Request"),
            ("per_item", "Per Item"),
            ("per_hour", "Per Hour"),
            ("flat_rate", "Flat Rate"),
        ],
        string="Unit Type",
        required=True,
        default="per_box",
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("rate")
    def _check_rate(self):
        for record in self:
            if record.rate < 0:
                raise ValidationError(_("Rate cannot be negative"))

    # ============================================================================
    # DISPLAY METHODS
    # ============================================================================
    def name_get(self):
        result = []
        for record in self:
            currency_symbol = (
                record.currency_id.symbol
                if record.currency_id and record.currency_id.symbol
                else ""
            )
            name = f"{record.name} ({record.service_type.title()}) - {record.rate} {currency_symbol}"
            result.append((record.id, name))
        return result
