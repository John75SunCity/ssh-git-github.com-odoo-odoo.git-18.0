# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsCustomerBillingProfile(models.Model):
    """Customer Billing Profile for Records Management:"
        Manages customer-specific billing configurations, payment terms,
    and automated billing preferences for records management services.:

    _name = "records.customer.billing.profile"
    _description = "Records Customer Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "partner_id, name"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Profile Name",
        required=True,
        tracking=True,
        help="Name for this billing profile":
            pass


    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Customer name with billing profile"


    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True


        # ============================================================================
    # CUSTOMER RELATIONSHIP FIELDS
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer this billing profile applies to"


    billing_contact_ids = fields.One2many(
        "records.billing.contact",
        "customer_billing_profile_id",
        string="Billing Contacts"


    department_id = fields.Many2one(
        "records.department",
        string="Records Department",
        help="Primary records department for this customer":


        # ============================================================================
    # BILLING CONFIGURATION FIELDS
        # ============================================================================
    ,
    billing_frequency = fields.Selection([))
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("semi_annual", "Semi-Annual"),
        ("annual", "Annual"),
        ("on_demand", "On Demand"),

        default="monthly",
        required=True,
        tracking=True

    payment_terms = fields.Selection([))
        ("net_15", "Net 15"),
        ("net_30", "Net 30"),
        ("net_45", "Net 45"),
        ("net_60", "Net 60"),
        ("prepaid", "Prepaid"),

        default="net_30",
        required=True

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True


        # ============================================================================
    # SERVICE RATE FIELDS
        # ============================================================================
    use_negotiated_rates = fields.Boolean(
        string="Use Negotiated Rates",
        default=False,
        help="Use customer-specific negotiated rates instead of standard rates"


    storage_rate = fields.Monetary(
        string="Storage Rate per Container",
        currency_field="currency_id",
        help="Monthly storage rate per container"


    retrieval_rate = fields.Monetary(
        string="Retrieval Rate per Request",
        currency_field="currency_id",
        help="Rate per document retrieval request"


    destruction_rate = fields.Monetary(
        string="Destruction Rate per Container",
        currency_field="currency_id",
        help="Rate per container destruction"


    pickup_rate = fields.Monetary(
        string="Pickup Rate per Service",
        currency_field="currency_id",
        help="Rate per pickup service request"


    delivery_rate = fields.Monetary(
        string="Delivery Rate per Service",
        currency_field="currency_id",
        help="Rate per delivery service request"


        # ============================================================================
    # CONTAINER-SPECIFIC RATE FIELDS
        # ============================================================================
    type01_storage_rate = fields.Monetary(
        string="TYPE 1 Storage Rate",
        currency_field="currency_id",
        ,
    help="Monthly rate for TYPE 1 standard boxes (1.2 CF)":


    type02_storage_rate = fields.Monetary(
        string="TYPE 2 Storage Rate",
        currency_field="currency_id",
        ,
    help="Monthly rate for TYPE 2 legal/banker boxes (2.4 CF)":


    type03_storage_rate = fields.Monetary(
        string="TYPE 3 Storage Rate",
        currency_field="currency_id",
        ,
    help="Monthly rate for TYPE 3 map boxes (0.875 CF)":


    type04_storage_rate = fields.Monetary(
        string="TYPE 4 Storage Rate",
        currency_field="currency_id",
        ,
    help="Monthly rate for TYPE 4 odd size/temp boxes (5.0 CF)":


    type06_storage_rate = fields.Monetary(
        string="TYPE 6 Storage Rate",
        currency_field="currency_id",
        ,
    help="Monthly rate for TYPE 6 pathology boxes (0.42 CF)":


        # ============================================================================
    # BILLING AUTOMATION FIELDS
        # ============================================================================
    auto_billing_enabled = fields.Boolean(
        string="Auto Billing Enabled",
        default=True,
        help="Automatically generate invoices based on schedule"


    ,
    invoice_delivery_method = fields.Selection([))
        ("email", "Email"),
        ("portal", "Customer Portal"),
        ("mail", "Physical Mail"),
        ("both", "Email and Portal"),

        default="email",
        required=True

    email_template_id = fields.Many2one(
        "mail.template",
        string="Invoice Email Template",
        help="Email template used for invoice delivery":


    billing_contact_email = fields.Char(
        string="Billing Contact Email",
        help="Primary email for billing communications":


    billing_cycle_day = fields.Integer(
        string="Billing Cycle Day",
        default=1,
        help="Day of month/quarter/year for billing cycle":


        # ============================================================================
    # DISCOUNT AND PRICING FIELDS
        # ============================================================================
    volume_discount_enabled = fields.Boolean(
        string="Volume Discount Enabled",
        default=False,
        help="Apply volume discounts based on container count"


    volume_discount_threshold = fields.Integer(
        string="Volume Discount Threshold",
        help="Minimum containers for volume discount":


    volume_discount_percentage = fields.Float(
        string="Volume Discount %",
        help="Percentage discount for volume customers":


    early_payment_discount = fields.Float(
        string="Early Payment Discount %",
        help="Discount for payments made early":


    early_payment_days = fields.Integer(
        string="Early Payment Days",
        help="Days early to qualify for discount":


    minimum_monthly_charge = fields.Monetary(
        string="Minimum Monthly Charge",
        currency_field="currency_id",
        help="Minimum charge per billing period"


        # ============================================================================
    # BILLING HISTORY AND ANALYTICS FIELDS
        # ============================================================================
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True


    last_invoice_date = fields.Datetime(
        string="Last Invoice Date",
        readonly=True,
        help="Date of last generated invoice"


    next_billing_date = fields.Date(
        string="Next Billing Date",
        compute="_compute_next_billing_date",
        store=True,
        help="Calculated next billing date based on frequency"


    total_invoiced = fields.Monetary(
        string="Total Invoiced",
        currency_field="currency_id",
        compute="_compute_invoice_totals",
        store=True,
        help="Total amount invoiced for this customer":


    invoice_count = fields.Integer(
        string="Invoice Count",
        compute="_compute_invoice_totals",
        store=True


    average_monthly_revenue = fields.Monetary(
        string="Average Monthly Revenue",
        currency_field="currency_id",
        compute="_compute_revenue_metrics",
        help="Average monthly revenue from this customer"


    last_payment_date = fields.Date(
        string="Last Payment Date",
        compute="_compute_payment_metrics",
        help="Date of most recent payment"


    ,
    payment_status = fields.Selection([))
        ("current", "Current"),
        ("overdue_15", "15 Days Overdue"),
        ("overdue_30", "30 Days Overdue"),
        ("overdue_60", "60+ Days Overdue"),


        # ============================================================================
    # WORKFLOW STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),

        help='Current status of the billing profile'

    # ============================================================================
        # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities"


    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers"


    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        ,
    string="Messages"


        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends("partner_id", "name")
    def _compute_display_name(self):
        """Generate display name from partner and profile name"""
        for record in self:
            if record.partner_id and record.name:
                record.display_name = _("%s - %s", record.partner_id.name, record.name)
            else:
                record.display_name = record.name or _("New Profile")

    @api.depends("partner_id")
    def _compute_invoice_totals(self):
        """Compute invoice totals for this customer""":
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move").search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),

                record.total_invoiced = sum(invoices.mapped("amount_total"))
                record.invoice_count = len(invoices)
            else:
                record.total_invoiced = 0.0
                record.invoice_count = 0

    @api.depends("billing_frequency", "billing_cycle_day", "last_invoice_date")
    def _compute_next_billing_date(self):
        """Calculate next billing date based on frequency"""
        from datetime import timedelta
        from dateutil.relativedelta import relativedelta

        for record in self:
            if not record.last_invoice_date:
                # First billing - use today
    base_date = fields.Date.today()
            else:
                base_date = record.last_invoice_date

            if record.billing_frequency == "monthly":
                record.next_billing_date = base_date + relativedelta(months=1)
            elif record.billing_frequency == "quarterly":
                record.next_billing_date = base_date + relativedelta(months=3)
            elif record.billing_frequency == "semi_annual":
                record.next_billing_date = base_date + relativedelta(months=6)
            elif record.billing_frequency == "annual":
                record.next_billing_date = base_date + relativedelta(years=1)
            else:
                record.next_billing_date = False

    @api.depends("total_invoiced", "created_date")
    def _compute_revenue_metrics(self):
        """Calculate revenue analytics"""
        from dateutil.relativedelta import relativedelta

        for record in self:
            if record.created_date and record.total_invoiced:
                months_active = relativedelta(fields.Date.today(), record.created_date.date()).months + 1
                if months_active > 0:
                    record.average_monthly_revenue = record.total_invoiced / months_active
                else:
                    record.average_monthly_revenue = 0.0
            else:
                record.average_monthly_revenue = 0.0

    def _compute_payment_metrics(self):
        """Calculate payment status and metrics"""
        for record in self:
            if record.partner_id:
                # Get most recent payment
                payments = self.env["account.payment"].search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "posted"),


                record.last_payment_date = payments[0].date if payments else False:
                # Calculate payment status based on overdue invoices
                overdue_invoices = self.env["account.move"].search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", ["not_paid", "partial"]),
                    ("invoice_date_due", "<", fields.Date.today()),


                if not overdue_invoices:
                    record.payment_status = "current"
                else:
                    days_overdue = max([)]
                        (fields.Date.today() - inv.invoice_date_due).days
                        for inv in overdue_invoices:


                    if days_overdue >= 60:
                        record.payment_status = "overdue_60"
                    elif days_overdue >= 30:
                        record.payment_status = "overdue_30"
                    elif days_overdue >= 15:
                        record.payment_status = "overdue_15"
                    else:
                        record.payment_status = "current"
            else:
                record.last_payment_date = False
                record.payment_status = "current"

    # ============================================================================
        # CONSTRAINT VALIDATIONS
    # ============================================================================
    @api.constrains("volume_discount_threshold", "volume_discount_percentage")
    def _check_volume_discount(self):
        """Validate volume discount configuration"""
        for record in self:
            if record.volume_discount_enabled:
                if record.volume_discount_threshold <= 0:
                    raise ValidationError(_("Volume discount threshold must be greater than 0"))
                if not (0 < record.volume_discount_percentage <= 100):
                    raise ValidationError(_("Volume discount percentage must be between 0 and 100"))

    @api.constrains("early_payment_discount", "early_payment_days")
    def _check_early_payment_discount(self):
        """Validate early payment discount configuration"""
        for record in self:
            if record.early_payment_discount > 0:
                if record.early_payment_days <= 0:
                    raise ValidationError(_("Early payment days must be greater than 0"))
                if record.early_payment_discount > 25:
                    raise ValidationError(_("Early payment discount cannot exceed 25%"))

    @api.constrains("billing_cycle_day")
    def _check_billing_cycle_day(self):
        """Validate billing cycle day"""
        for record in self:
            if not (1 <= record.billing_cycle_day <= 31):
                raise ValidationError(_("Billing cycle day must be between 1 and 31"))

    @api.constrains("partner_id")
    def _check_unique_active_profile(self):
        """Ensure only one active profile per customer"""
        for record in self:
            if record.state == 'active':
                existing = self.search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id)

                if existing:
                    raise ValidationError(_("Customer %s already has an active billing profile", record.partner_id.name))

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_view_invoices(self):
        """View invoices for this customer""":
        self.ensure_one()
        return {}
            "name": _("Customer Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": []
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),

            "context": {"default_partner_id": self.partner_id.id},


    def action_generate_invoice(self):
        """Generate invoice for this customer""":
        self.ensure_one()

        # Create billing record
        billing_vals = {}
            'partner_id': self.partner_id.id,
            'billing_profile_id': self.id,
            'billing_date': fields.Date.today(),
            'state': 'draft',


        billing_record = self.env['records.billing'].create(billing_vals)

        # Update last invoice date
        self.write({'last_invoice_date': fields.Datetime.now()})

        return {}
            "type": "ir.actions.act_window",
            "name": _("Generated Invoice"),
            "res_model": "records.billing",
            "res_id": billing_record.id,
            "view_mode": "form",
            "target": "current",


    def action_duplicate_profile(self):
        """Duplicate this billing profile"""
        self.ensure_one()

        copy_vals = {}
            'name': _("%s (Copy)", self.name),
            'partner_id': False,  # Clear partner to allow selection
            'state': 'draft',
            'active': False,  # Start inactive


        new_profile = self.copy(copy_vals)

        return {}
            "name": _("Duplicate Billing Profile"),
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": new_profile.id,
            "view_mode": "form",
            "target": "current",


    def action_activate_profile(self):
        """Activate billing profile"""
        for record in self:
            # Check for existing active profiles:
            existing_active = self.search([)]
                ("partner_id", "=", record.partner_id.id),
                ("state", "=", "active"),
                ("id", "!=", record.id)


            if existing_active:
                # Suspend existing active profile
                existing_active.write({"state": "suspended"})

            record.write({"state": "active"})
            record.message_post(body=_("Billing profile activated"))

    def action_suspend_profile(self):
        """Suspend billing profile"""
        for record in self:
            record.write({"state": "suspended"})
            record.message_post(body=_("Billing profile suspended"))

    def action_terminate_profile(self):
        """Terminate billing profile"""
        for record in self:
            if record.invoice_count > 0:
                # Check for unpaid invoices:
                unpaid_invoices = self.env["account.move"].search([)]
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("payment_state", "in", ["not_paid", "partial"]),


                if unpaid_invoices:
                    raise UserError(_("Cannot terminate profile with unpaid invoices"))

            record.write({"state": "terminated"})
            record.message_post(body=_("Billing profile terminated"))

    def action_test_billing_configuration(self):
        """Test billing configuration"""
        self.ensure_one()

        # Validate configuration
        errors = []

        if self.use_negotiated_rates:
            if not self.storage_rate:
                errors.append(_("Storage rate is required for negotiated rates")):
        if self.volume_discount_enabled:
            if not self.volume_discount_threshold:
                errors.append(_("Volume discount threshold is required"))

        if self.auto_billing_enabled:
            if not self.billing_contact_email:
                errors.append(_("Billing contact email is required for auto billing")):
        if errors:
            message = _("Configuration Issues:\n%s", "\n".join(errors))
            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "message": message,
                    "type": "warning",


        else:
            return {}
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {}
                    "message": _("Billing configuration is valid"),
                    "type": "success",



    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_effective_rate(self, service_type, container_type=None):
        """Get effective rate for a service considering negotiated rates""":
        self.ensure_one()

        if not self.use_negotiated_rates:
            # Fall back to base rates
            base_rate = self.env['base.rate'].get_active_rate_for_company(self.company_id.id)
            if base_rate:
                return base_rate.get_service_rate(service_type)
            return 0.0

        # Container-specific storage rates
        if service_type == 'storage' and container_type:
            rate_field = f"{container_type}_storage_rate"
            return getattr(self, rate_field, 0.0) or self.storage_rate or 0.0

        # Service-specific rates
        service_rates = {}
            'storage': self.storage_rate,
            'retrieval': self.retrieval_rate,
            'destruction': self.destruction_rate,
            'pickup': self.pickup_rate,
            'delivery': self.delivery_rate,


        return service_rates.get(service_type, 0.0)

    def calculate_volume_discount(self, container_count):
        """Calculate volume discount based on container count"""
        self.ensure_one()

        if not self.volume_discount_enabled:
            return 0.0

        if container_count >= self.volume_discount_threshold:
            return self.volume_discount_percentage / 100

        return 0.0

    def get_payment_terms_days(self):
        """Get payment terms in days"""
        self.ensure_one()

        terms_map = {}
            'net_15': 15,
            'net_30': 30,
            'net_45': 45,
            'net_60': 60,
            'prepaid': 0,


        return terms_map.get(self.payment_terms, 30)

    def is_due_for_billing(self):
        """Check if customer is due for billing""":
        self.ensure_one()

        if not self.auto_billing_enabled or self.state != 'active':
            return False

        if not self.next_billing_date:
            return True  # First billing

        return fields.Date.today() >= self.next_billing_date

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    def get_billing_summary(self):
        """Get billing summary for reporting""":
        self.ensure_one()

        return {}
            'customer': self.partner_id.name,
            'profile': self.name,
            'frequency': dict(self._fields['billing_frequency'].selection)[self.billing_frequency],
            'payment_terms': dict(self._fields['payment_terms'].selection)[self.payment_terms],
            'total_invoiced': self.total_invoiced,
            'invoice_count': self.invoice_count,
            'average_monthly': self.average_monthly_revenue,
            'payment_status': dict(self._fields['payment_status'].selection).get(self.payment_status, 'Unknown'),
            'next_billing': self.next_billing_date,


    @api.model
    def get_dashboard_metrics(self):
        """Get dashboard metrics for billing profiles""":
        active_profiles = self.search([('state', '=', 'active')])

        return {}
            'active_profiles': len(active_profiles),
            'total_revenue': sum(active_profiles.mapped('total_invoiced')),
            'average_revenue_per_customer': sum(active_profiles.mapped('average_monthly_revenue')) / len(active_profiles) if active_profiles else 0,:
            'overdue_customers': len(active_profiles.filtered(lambda p: p.payment_status != 'current')),
            'due_for_billing': len(active_profiles.filtered('is_due_for_billing')),



    """"))))))))))))))))))))))))))))))))))
