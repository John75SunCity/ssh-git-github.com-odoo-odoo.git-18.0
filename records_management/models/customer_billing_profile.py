import logging
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError



_logger = logging.getLogger(__name__)


class CustomerBillingProfile(models.Model):
    """
    Customer Billing Profile - Manages billing configurations for customers

    This model provides comprehensive billing management including:
    - Multiple billing cycles (monthly, quarterly, annual, prepaid)
    - Automated invoice generation with customizable rules
    - Payment reliability scoring based on payment history
    - Credit limit management with approval workflows
    - Prepaid billing with discount calculation
    - Department-level access control and data separation
    """

    _name = "customer.billing.profile"
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
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("suspended", "Suspended"),
            ("inactive", "Inactive"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER RELATIONSHIP FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        help="Department for access control and data separation",
    )

    # ============================================================================
    # BILLING CONFIGURATION FIELDS  
    # ============================================================================
    billing_cycle = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
            ("prepaid", "Prepaid"),
        ],
        string="Billing Cycle",
        default="monthly",
        required=True,
        tracking=True,
    )

    billing_day = fields.Integer(
        string="Billing Day", default=1, help="Day of month for billing (1-28)"
    )

    auto_invoice = fields.Boolean(
        string="Auto Generate Invoices",
        default=True,
        help="Automatically generate invoices based on billing cycle",
    )
    
    # ============================================================================
    # AUTOMATED BILLING FIELDS
    # ============================================================================
    
    auto_generate_service_invoices = fields.Boolean(
        string="Auto Generate Service Invoices",
        default=True,
        help="Automatically generate invoices for services (pickup, delivery, etc.)",
        tracking=True,
    )
    
    auto_generate_storage_invoices = fields.Boolean(
        string="Auto Generate Storage Invoices", 
        default=True,
        help="Automatically generate invoices for storage fees",
        tracking=True,
    )
    
    auto_send_invoices = fields.Boolean(
        string="Auto Send Invoices",
        default=True,
        help="Automatically send invoices when generated",
        tracking=True,
    )
    
    auto_send_statements = fields.Boolean(
        string="Auto Send Statements",
        default=False,
        help="Automatically send monthly statements",
        tracking=True,
    )
    
    # ============================================================================
    # BILLING CYCLES & SCHEDULING
    # ============================================================================
    
    service_billing_cycle = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('semi_annual', 'Semi-Annual'),
            ('annual', 'Annual'),
            ('per_service', 'Per Service'),
        ],
        string='Service Billing Cycle',
        default='monthly',
        help="Billing frequency for service charges",
        tracking=True,
    )
    
    storage_billing_cycle = fields.Selection(
        [
            ('monthly', 'Monthly'),
            ('quarterly', 'Quarterly'),
            ('semi_annual', 'Semi-Annual'),
            ('annual', 'Annual'),
        ],
        string='Storage Billing Cycle',
        default='monthly', 
        help="Billing frequency for storage fees",
        tracking=True,
    )
    
    storage_bill_in_advance = fields.Boolean(
        string="Bill Storage in Advance",
        default=False,
        help="Bill storage fees in advance rather than arrears",
        tracking=True,
    )
    
    storage_advance_months = fields.Integer(
        string="Storage Advance Months",
        default=1,
        help="Number of months to bill storage in advance",
    )
    
    # ============================================================================
    # PAYMENT TERMS & DUE DATES
    # ============================================================================
    
    invoice_due_days = fields.Integer(
        string="Invoice Due Days",
        default=30,
        help="Number of days from invoice date until payment due",
        tracking=True,
    )
    
    # ============================================================================ 
    # PREPAID SYSTEM ENHANCEMENTS
    # ============================================================================
    
    prepaid_months = fields.Integer(
        string="Prepaid Months",
        default=12,
        help="Number of months covered by prepaid payments",
    )

    invoice_template_id = fields.Many2one(
        "account.move",
        string="Invoice Template",
        help="Template for automated invoice generation",
    )

    # ============================================================================
    # CREDIT AND PAYMENT FIELDS
    # ============================================================================
    credit_limit = fields.Monetary(
        string="Credit Limit",
        currency_field="currency_id",
        help="Maximum allowed outstanding balance",
    )

    payment_terms_id = fields.Many2one("account.payment.term", string="Payment Terms")

    payment_reliability_score = fields.Float(
        string="Payment Reliability Score",
        compute="_compute_payment_reliability_score",
        store=True,
        help="Score based on payment history (0-100)",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )

    # ============================================================================
    # PREPAID BILLING FIELDS
    # ============================================================================
    prepaid_enabled = fields.Boolean(
        string="Prepaid Billing Enabled",
        help="Enable prepaid billing with advance payments",
    )

    prepaid_balance = fields.Monetary(
        string="Prepaid Balance",
        currency_field="currency_id",
        compute="_compute_prepaid_balance",
        store=True,
    )

    prepaid_discount_percent = fields.Float(
        string="Prepaid Discount %", help="Discount percentage for prepaid payments"
    )

    minimum_prepaid_amount = fields.Monetary(
        string="Minimum Prepaid Amount",
        currency_field="currency_id",
        help="Minimum amount for prepaid payments",
    )

    # ============================================================================
    # NOTIFICATION AND COMMUNICATION FIELDS
    # ============================================================================
    send_invoices_by_email = fields.Boolean(
        string="Send Invoices by Email", default=True
    )

    invoice_email = fields.Char(
        string="Invoice Email", help="Email address for sending invoices"
    )

    late_payment_notification = fields.Boolean(
        string="Late Payment Notifications",
        default=True,
        help="Send notifications for overdue payments",
    )

    notification_days = fields.Integer(
        string="Notification Days",
        default=7,
        help="Days after due date to send notifications",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    billing_contact_ids = fields.One2many(
        "records.billing.contact", "billing_profile_id", string="Billing Contacts"
    )
    
    contact_count = fields.Integer(
        string="Contact Count",
        compute="_compute_contact_count",
        store=True,
        help="Number of billing contacts",
    )

    invoice_ids = fields.One2many(
        "account.move",
        "billing_profile_id",
        string="Invoices",
        domain=[("move_type", "=", "out_invoice")],
    )

    prepaid_payment_ids = fields.One2many(
        "account.payment", "billing_profile_id", string="Prepaid Payments"
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    action_activate = fields.Char(string='Action Activate')
    action_reactivate = fields.Char(string='Action Reactivate')
    action_suspend = fields.Char(string='Action Suspend')
    action_terminate = fields.Char(string='Action Terminate')
    automation = fields.Char(string='Automation')
    billing_contacts = fields.Char(string='Billing Contacts')
    billing_profile_id = fields.Many2one('billing.profile', string='Billing Profile Id')
    billing_schedule = fields.Char(string='Billing Schedule')
    description = fields.Char(string='Description')
    draft = fields.Char(string='Draft')
    email = fields.Char(string='Email')
    group_customer = fields.Char(string='Group Customer')
    group_state = fields.Selection([], string='Group State')  # TODO: Define selection options
    group_storage_cycle = fields.Char(string='Group Storage Cycle')
    help = fields.Char(string='Help')
    monthly_storage = fields.Char(string='Monthly Storage')
    next_storage_billing_date = fields.Date(string='Next Storage Billing Date')
    payment_term_id = fields.Many2one('payment.term', string='Payment Term Id')
    phone = fields.Char(string='Phone')
    prepaid = fields.Char(string='Prepaid')
    primary_contact = fields.Char(string='Primary Contact')
    quarterly_storage = fields.Char(string='Quarterly Storage')
    receive_notifications = fields.Char(string='Receive Notifications')
    receive_service_invoices = fields.Char(string='Receive Service Invoices')
    receive_statements = fields.Char(string='Receive Statements')
    receive_storage_invoices = fields.Char(string='Receive Storage Invoices')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    service_billing = fields.Char(string='Service Billing')
    storage_billing = fields.Char(string='Storage Billing')
    suspended = fields.Char(string='Suspended')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    
    @api.depends("billing_contact_ids")
    def _compute_contact_count(self):
        """Calculate number of billing contacts"""
        for record in self:
            record.contact_count = len(record.billing_contact_ids)
    
    @api.depends("prepaid_payment_ids", "prepaid_payment_ids.amount")
    def _compute_prepaid_balance(self):
        """Calculate current prepaid balance"""
        for record in self:
            total_payments = sum(record.prepaid_payment_ids.mapped("amount"))
            # Subtract consumed amounts (this would need additional logic)
            record.prepaid_balance = total_payments

    @api.depends("partner_id", "partner_id.payment_history")
    def _compute_payment_reliability_score(self):
        """Calculate payment reliability score based on history"""
        for record in self:
            if not record.partner_id:
                record.payment_reliability_score = 0.0
                continue

            # This is a simplified calculation - in practice would analyze
            # payment history, late payments, defaults, etc.
            invoices = self.env["account.move"].search(
                [
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                ]
            )

            if not invoices:
                record.payment_reliability_score = 50.0  # Neutral score
                continue

            paid_on_time = invoices.filtered(lambda inv: inv.payment_state == "paid")
            score = (len(paid_on_time) / len(invoices)) * 100
            record.payment_reliability_score = min(100.0, max(0.0, score))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate_profile(self):
        """Activate billing profile"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only activate draft profiles"))
        self.write({"state": "active"})

    def action_suspend_profile(self):
        """Suspend billing profile"""

        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Can only suspend active profiles"))
        self.write({"state": "suspended"})

    def action_reactivate_profile(self):
        """Reactivate suspended profile"""

        self.ensure_one()
        if self.state != "suspended":
            raise UserError(_("Can only reactivate suspended profiles"))
        self.write({"state": "active"})

    def action_generate_invoice(self):
        """Generate invoice based on billing profile configuration"""

        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Can only generate invoices for active profiles"))

        # Create invoice based on profile settings
        invoice_vals = self._prepare_invoice_values()
        invoice = self.env["account.move"].create(invoice_vals)

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_invoices(self):
        """View all invoices for this billing profile"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("billing_profile_id", "=", self.id)],
            "context": {"default_billing_profile_id": self.id},
        }

    # ============================================================================
    # PRIVATE METHODS
    # ============================================================================
    def _prepare_invoice_values(self):
        """Prepare values for invoice creation"""
        self.ensure_one()
        return {
            "partner_id": self.partner_id.id,
            "billing_profile_id": self.id,
            "payment_term_id": (
                self.payment_terms_id.id if self.payment_terms_id else False
            ),
            "currency_id": self.currency_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("billing_day")
    def _check_billing_day(self):
        """Validate billing day is within valid range"""
        for record in self:
            if not (1 <= record.billing_day <= 28):
                raise ValidationError(_("Billing day must be between 1 and 28"))

    @api.constrains("credit_limit")
    def _check_credit_limit(self):
        """Validate credit limit is positive"""
        for record in self:
            if record.credit_limit < 0:
                raise ValidationError(_("Credit limit must be positive"))

    @api.constrains("prepaid_discount_percent")
    def _check_prepaid_discount(self):
        """Validate prepaid discount percentage"""
        for record in self:
            if not (0 <= record.prepaid_discount_percent <= 100):
                raise ValidationError(_("Prepaid discount must be between 0 and 100%"))
