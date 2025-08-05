# -*- coding: utf-8 -*-

from datetime import datetime, timedelta

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
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
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
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & BILLING RELATIONSHIPS
    # ============================================================================

    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    billing_contact_id = fields.Many2one("res.partner", string="Billing Contact")
    account_manager = fields.Many2one("res.users", string="Account Manager")

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================

    billing_type = fields.Selection(
        [("standard", "Standard"), ("premium", "Premium"), ("custom", "Custom")],
        string="Billing Type",
        default="standard",
        tracking=True,
    )
    service_category = fields.Selection(
        [
            ("storage", "Storage Services"),
            ("retrieval", "Retrieval Services"),
            ("destruction", "Destruction Services"),
            ("scanning", "Scanning Services"),
            ("transport", "Transport Services"),
            ("consultation", "Consultation Services"),
            ("all", "All Services"),
        ],
        string="Service Category",
        default="storage",
        tracking=True,
    )

    # ============================================================================
    # RATE STRUCTURE & PRICING
    # ============================================================================

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    billing_model = fields.Selection(
        [
            ("per_container", "Per Container"),
            ("per_cubic_foot", "Per Cubic Foot"),
            ("flat_rate", "Flat Rate"),
            ("tiered", "Tiered Pricing"),
            ("volume_based", "Volume Based"),
            ("custom", "Custom Pricing"),
        ],
        string="Billing Model",
        default="per_container",
        required=True,
        tracking=True,
    )

    # Rate Configuration
    base_rate = fields.Float(string="Base Rate", digits="Product Price", default=0.0)
    setup_fee = fields.Float(string="Setup Fee", digits="Product Price", default=0.0)
    monthly_minimum = fields.Float(
        string="Monthly Minimum", digits="Product Price", default=0.0
    )

    # ============================================================================
    # SERVICE PRICING
    # ============================================================================

    storage_rate = fields.Float(
        string="Storage Rate", digits="Product Price", default=0.0
    )
    retrieval_rate = fields.Float(
        string="Retrieval Rate", digits="Product Price", default=0.0
    )
    transport_rate = fields.Float(
        string="Transport Rate", digits="Product Price", default=0.0
    )
    scanning_rate = fields.Float(
        string="Scanning Rate", digits="Product Price", default=0.0
    )
    destruction_rate = fields.Float(
        string="Destruction Rate", digits="Product Price", default=0.0
    )

    # ============================================================================
    # DISCOUNTS & PROMOTIONS
    # ============================================================================

    discount_percentage = fields.Float(
        string="Discount %", digits="Discount", default=0.0
    )
    volume_discount_threshold = fields.Integer(
        string="Volume Discount Threshold", default=0
    )
    volume_discount_rate = fields.Float(
        string="Volume Discount Rate", digits="Discount", default=0.0
    )

    # ============================================================================
    # BILLING SCHEDULE
    # ============================================================================

    billing_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
        ],
        string="Billing Frequency",
        default="monthly",
        required=True,
    )
    billing_day = fields.Integer(
        string="Billing Day of Month", default=1, help="Day of month for billing"
    )
    advance_billing_days = fields.Integer(string="Advance Billing Days", default=30)

    # ============================================================================
    # TERMS & CONDITIONS
    # ============================================================================

    payment_terms = fields.Many2one("account.payment.term", string="Payment Terms")
    credit_limit = fields.Float(
        string="Credit Limit", digits="Product Price", default=0.0
    )
    late_fee_percentage = fields.Float(
        string="Late Fee %", digits="Discount", default=0.0
    )
    grace_period_days = fields.Integer(string="Grace Period (Days)", default=0)

    # ============================================================================
    # DATE TRACKING
    # ============================================================================

    effective_date = fields.Date(
        string="Effective Date", default=fields.Date.today, required=True
    )
    expiry_date = fields.Date(string="Expiry Date")
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")

    # ============================================================================
    # AUTOMATION & NOTIFICATIONS
    # ============================================================================

    auto_invoice = fields.Boolean(string="Auto Generate Invoices", default=False)
    auto_payment_reminder = fields.Boolean(
        string="Auto Payment Reminders", default=False
    )
    invoice_email_template = fields.Many2one(
        "mail.template", string="Invoice Email Template"
    )
    reminder_email_template = fields.Many2one(
        "mail.template", string="Reminder Email Template"
    )

    # ============================================================================
    # AUDIT & COMPLIANCE
    # ============================================================================

    audit_trail = fields.Text(string="Audit Trail", readonly=True)
    compliance_notes = fields.Text(string="Compliance Notes")
    regulatory_requirements = fields.Text(string="Regulatory Requirements")

    # ============================================================================
    # RELATIONSHIP FIELDS - One2many relationships to related models
    # ============================================================================

    billing_line_ids = fields.One2many(
        "records.billing.line",
        "config_id",
        string="Billing Lines",
        help="Detailed billing line items for this configuration",
    )
    usage_tracking_ids = fields.One2many(
        "records.usage.tracking",
        "config_id",
        string="Usage Tracking Records",
        help="Usage tracking records for billing analysis",
    )
    invoice_log_ids = fields.One2many(
        "invoice.generation.log",
        "config_id",
        string="Invoice Generation Logs",
        help="Historical invoice generation records",
    )
    discount_rule_ids = fields.One2many(
        "discount.rule",
        "config_id",
        string="Discount Rules",
        help="Discount rules applied to this billing configuration",
    )
    revenue_analytics_ids = fields.One2many(
        "revenue.analytics",
        "config_id",
        string="Revenue Analytics",
        help="Revenue analytics and reporting data",
    )
    promotional_discount_ids = fields.One2many(
        "records.promotional.discount",
        "config_id",
        string="Promotional Discounts",
        help="Active promotional discounts for this configuration",
    )

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_activate(self):
        """Activate billing configuration"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation."))
        self.write({"state": "active"})
        self.message_post(body=_("Billing configuration activated"))

    def action_suspend(self):
        """Suspend billing configuration"""
        self.ensure_one()
        self.write({"state": "suspended"})
        self.message_post(body=_("Billing configuration suspended"))

    def action_archive(self):
        """Archive billing configuration"""
        self.ensure_one()
        self.write({"state": "archived", "active": False})
        self.message_post(body=_("Billing configuration archived"))

    def calculate_service_charge(self, service_type, quantity=1.0):
        """Calculate charges for specific service"""
        self.ensure_one()
        rate_map = {
            "storage": self.storage_rate,
            "retrieval": self.retrieval_rate,
            "transport": self.transport_rate,
            "scanning": self.scanning_rate,
            "destruction": self.destruction_rate,
        }

        base_charge = rate_map.get(service_type, 0.0) * quantity

        # Apply volume discount if applicable
        if quantity >= self.volume_discount_threshold and self.volume_discount_rate:
            discount = base_charge * (self.volume_discount_rate / 100.0)
            base_charge -= discount

        # Apply general discount
        if self.discount_percentage:
            general_discount = base_charge * (self.discount_percentage / 100.0)
            base_charge -= general_discount

        return max(base_charge, 0.0)

    def get_next_billing_date(self):
        """Calculate next billing date based on frequency"""
        self.ensure_one()
        if not self.effective_date:
            return False

        base_date = self.effective_date
        today = fields.Date.today()

        if self.billing_frequency == "monthly":
            # Calculate next monthly billing
            if base_date.day <= self.billing_day:
                next_date = base_date.replace(day=self.billing_day)
            else:
                # Move to next month
                if base_date.month == 12:
                    next_date = base_date.replace(
                        year=base_date.year + 1, month=1, day=self.billing_day
                    )
                else:
                    next_date = base_date.replace(
                        month=base_date.month + 1, day=self.billing_day
                    )
        elif self.billing_frequency == "quarterly":
            next_date = base_date + timedelta(days=90)
        elif self.billing_frequency == "semi_annual":
            next_date = base_date + timedelta(days=180)
        elif self.billing_frequency == "annual":
            next_date = base_date.replace(year=base_date.year + 1)
        else:
            next_date = base_date + timedelta(days=30)

        return next_date

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("discount_percentage")
    def _check_discount_percentage(self):
        for record in self:
            if record.discount_percentage < 0 or record.discount_percentage > 100:
                raise ValidationError(
                    _("Discount percentage must be between 0 and 100")
                )

    @api.constrains("volume_discount_rate")
    def _check_volume_discount_rate(self):
        for record in self:
            if record.volume_discount_rate < 0 or record.volume_discount_rate > 100:
                raise ValidationError(
                    _("Volume discount rate must be between 0 and 100")
                )

    @api.constrains("billing_day")
    def _check_billing_day(self):
        for record in self:
            if record.billing_day < 1 or record.billing_day > 31:
                raise ValidationError(_("Billing day must be between 1 and 31"))

    @api.constrains("effective_date", "expiry_date")
    def _check_date_consistency(self):
        for record in self:
            if record.expiry_date and record.effective_date > record.expiry_date:
                raise ValidationError(_("Effective date cannot be after expiry date"))

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    total_monthly_charges = fields.Float(
        string="Total Monthly Charges",
        compute="_compute_total_monthly_charges",
        digits="Product Price",
        store=True,
    )

    @api.depends("storage_rate", "monthly_minimum", "setup_fee")
    def _compute_total_monthly_charges(self):
        for record in self:
            total = record.storage_rate + record.setup_fee
            record.total_monthly_charges = max(total, record.monthly_minimum)

    is_expired = fields.Boolean(
        string="Is Expired",
        compute="_compute_is_expired",
        store=True,
    )

    @api.depends("expiry_date")
    def _compute_is_expired(self):
        today = fields.Date.today()
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < today

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("records.billing.config")
                    or "NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        if "state" in vals and vals["state"] == "active":
            vals["last_review_date"] = fields.Date.today()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state == "active":
                raise UserError(_("Cannot delete active billing configurations"))
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    def _log_audit_trail(self, action, details=""):
        """Log actions to audit trail"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = self.env.user.name
        log_entry = f"[{timestamp}] {user}: {action}"
        if details:
            log_entry += f" - {details}"

        current_audit = self.audit_trail or ""
        self.audit_trail = (
            f"{current_audit}\n{log_entry}" if current_audit else log_entry
        )

    def generate_billing_summary(self):
        """Generate comprehensive billing summary"""
        self.ensure_one()
        return {
            "config_name": self.name,
            "customer": self.partner_id.name if self.partner_id else "N/A",
            "billing_model": dict(self._fields["billing_model"].selection)[
                self.billing_model
            ],
            "base_rate": self.base_rate,
            "monthly_minimum": self.monthly_minimum,
            "next_billing_date": self.get_next_billing_date(),
            "status": self.state,
        }
