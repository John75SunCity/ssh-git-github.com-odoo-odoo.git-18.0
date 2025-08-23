from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsCustomerBillingProfile(models.Model):
    """
    Customer Billing Profile for Records Management.
    Handles billing cycles, rates, auto-billing, and analytics for each customer/department.
    """
    _name = 'records.customer.billing.profile'
    _description = 'Records Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Profile Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, ondelete='cascade', tracking=True)
    department_id = fields.Many2one('records.department', string="Department", domain="[('partner_id', '=', partner_id)]", tracking=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('terminated', 'Terminated'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi_annually', 'Semi-Annually'),
        ('annually', 'Annually'),
    ], string="Billing Frequency", default='monthly', required=True, tracking=True)
    billing_cycle_day = fields.Integer(string="Billing Cycle Day", default=1, help="Day of the month to generate invoices (1-31).")
    payment_terms_id = fields.Many2one('account.payment.term', string="Payment Terms")
    next_billing_date = fields.Date(string="Next Billing Date", compute='_compute_next_billing_date', store=True)
    last_invoice_date = fields.Date(string="Last Invoice Date", readonly=True)
    auto_billing_enabled = fields.Boolean(string="Enable Auto-Billing", default=False, tracking=True)
    invoice_delivery_method = fields.Selection([
        ('email', 'Email'),
        ('portal', 'Portal Only'),
        ('none', 'None'),
    ], string="Invoice Delivery", default='email', tracking=True)
    email_template_id = fields.Many2one('mail.template', string="Invoice Email Template", domain="[('model', '=', 'account.move')]")
    billing_contact_ids = fields.Many2many('res.partner', 'billing_profile_contact_rel', 'profile_id', 'contact_id', string="Billing Contacts")

    # ============================================================================
    # ADVANCED BILLING OPTIONS
    # ============================================================================
    auto_generate_service_invoices = fields.Boolean(string='Auto Generate Service Invoices', default=False)
    auto_generate_storage_invoices = fields.Boolean(string='Auto Generate Storage Invoices', default=False)
    invoice_due_days = fields.Integer(string='Invoice Due Days', default=30, help="Number of days after invoice date before due.")
    service_billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Service Billing Cycle', default='monthly')
    storage_billing_cycle = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
    ], string='Storage Billing Cycle', default='monthly')
    storage_bill_in_advance = fields.Boolean(string='Storage Bill In Advance', default=False)
    storage_advance_months = fields.Integer(string='Storage Advance Months', default=1)
    prepaid_enabled = fields.Boolean(string='Enable Prepaid Billing', default=False)
    prepaid_months = fields.Integer(string='Prepaid Months', default=0)
    prepaid_discount_percent = fields.Float(string='Prepaid Discount (%)', default=0.0)

    # ============================================================================
    # PRICING & RATES
    # ============================================================================
    use_negotiated_rates = fields.Boolean(string="Use Negotiated Rates", default=False, tracking=True)
    storage_rate = fields.Monetary(string="Default Storage Rate", tracking=True)
    retrieval_rate = fields.Monetary(string="Default Retrieval Rate", tracking=True)
    destruction_rate = fields.Monetary(string="Default Destruction Rate", tracking=True)
    pickup_rate = fields.Monetary(string="Default Pickup Rate", tracking=True)
    delivery_rate = fields.Monetary(string="Default Delivery Rate", tracking=True)
    minimum_monthly_charge = fields.Monetary(string="Minimum Monthly Charge", tracking=True)

    # ============================================================================
    # ANALYTICS & METRICS
    # ============================================================================
    total_invoiced = fields.Monetary(string="Total Invoiced", compute='_compute_invoice_totals', store=True)
    invoice_count = fields.Integer(string="Invoice Count", compute='_compute_invoice_totals', store=True)
    average_monthly_revenue = fields.Monetary(string="Avg. Monthly Revenue", compute='_compute_revenue_metrics', store=True)
    last_payment_date = fields.Date(string="Last Payment Date", compute='_compute_payment_metrics', store=True)
    payment_status = fields.Selection([
        ('current', 'Current'),
        ('overdue_15', 'Overdue (15+ days)'),
        ('overdue_30', 'Overdue (30+ days)'),
        ('overdue_60', 'Overdue (60+ days)'),
    ], string="Payment Status", compute='_compute_payment_metrics', store=True)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name')
    def _compute_display_name(self):
        """Compute display name for profile."""
        for record in self:
            if record.partner_id and record.name:
                record.display_name = f"{record.partner_id.name} - {record.name}"
            else:
                record.display_name = record.name or _("New Profile")

    @api.depends('partner_id')
    def _compute_invoice_totals(self):
        """Compute total invoiced and invoice count."""
        for record in self:
            if record.partner_id:
                invoices = self.env["account.move"].search([
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                ])
                record.total_invoiced = sum(invoices.mapped("amount_total"))
                record.invoice_count = len(invoices)
            else:
                record.total_invoiced = 0.0
                record.invoice_count = 0

    @api.depends('last_invoice_date', 'billing_frequency', 'billing_cycle_day')
    def _compute_next_billing_date(self):
        """Compute the next billing date based on last invoice and frequency."""
        for record in self:
            if not record.billing_frequency:
                record.next_billing_date = False
                continue
            base_date = record.last_invoice_date or fields.Date.today()
            day = min(record.billing_cycle_day or 1, 28)  # Avoid invalid dates
            if record.billing_frequency == 'monthly':
                next_date = base_date + relativedelta(months=1)
            elif record.billing_frequency == 'quarterly':
                next_date = base_date + relativedelta(months=3)
            elif record.billing_frequency == 'semi_annually':
                next_date = base_date + relativedelta(months=6)
            elif record.billing_frequency == 'annually':
                next_date = base_date + relativedelta(years=1)
            else:
                record.next_billing_date = False
                continue
            import calendar
            year = next_date.year
            month = next_date.month
            last_day = calendar.monthrange(year, month)[1]
            valid_day = min(day, last_day)
            record.next_billing_date = next_date.replace(day=valid_day)

    @api.depends('create_date', 'total_invoiced')
    def _compute_revenue_metrics(self):
        """Compute average monthly revenue."""
        for record in self:
            if record.create_date and record.total_invoiced > 0:
                from math import ceil
                days_active = (fields.Date.today() - record.create_date.date()).days
                months_active = ceil(days_active / 30.44) if days_active > 0 else 1
                record.average_monthly_revenue = record.total_invoiced / months_active if months_active > 0 else 0.0
            else:
                record.average_monthly_revenue = 0.0

    @api.depends('partner_id', 'total_invoiced')
    def _compute_payment_metrics(self):
        """Compute last payment date and payment status."""
        for record in self:
            if record.partner_id:
                payments = self.env["account.payment"].search([
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "posted"),
                ], order='date desc', limit=1)
                record.last_payment_date = payments.date if payments else False
                overdue_invoices = self.env["account.move"].search([
                    ("partner_id", "=", record.partner_id.id),
                    ("move_type", "=", "out_invoice"),
                    ("state", "=", "posted"),
                    ("payment_state", "in", ["not_paid", "partial"]),
                    ("invoice_date_due", "<", fields.Date.today()),
                ])
                overdue_invoices_with_due_date = [inv for inv in overdue_invoices if inv.invoice_date_due]
                if not overdue_invoices_with_due_date:
                    record.payment_status = "current"
                else:
                    days_overdue = max((fields.Date.today() - inv.invoice_date_due).days for inv in overdue_invoices_with_due_date)
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
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('billing_cycle_day')
    def _check_billing_cycle_day(self):
        """Ensure billing cycle day is valid."""
        for record in self:
            if not (1 <= (record.billing_cycle_day or 1) <= 31):
                raise ValidationError(_("Billing cycle day must be between 1 and 31."))

    @api.constrains('partner_id', 'state')
    def _check_unique_active_profile(self):
        """Ensure only one active billing profile per customer/department."""
        for record in self:
            if record.state == 'active':
                domain = [
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id)
                ]
                if record.department_id:
                    domain.append(('department_id', '=', record.department_id.id))
                if self.search(domain, limit=1):
                    raise ValidationError(_("Customer '%s' already has an active billing profile for this department.") % record.partner_id.name)

    # ============================================================================
    # ACTION METHODS
    def action_view_invoices(self):
        """Open customer invoices related to this profile."""
        self.ensure_one()
        domain = [("partner_id", "=", self.partner_id.id), ("move_type", "=", "out_invoice")]
        if self.department_id:
            domain.append(("department_id", "=", self.department_id.id))
        return {
            "name": _("Customer Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": domain,
            "context": {"default_partner_id": self.partner_id.id},
        }

    def action_activate(self):
        """Activate this billing profile."""
        self.ensure_one()
        self._check_unique_active_profile()
        self.write({"state": "active"})
        self.message_post(body=_("Billing profile activated."))

    def action_suspend(self):
        """Suspend this billing profile."""
        self.ensure_one()
        self.write({"state": "suspended"})
        self.message_post(body=_("Billing profile suspended."))

    def action_terminate(self):
        """Terminate this billing profile if no unpaid invoices."""
        self.ensure_one()
        unpaid_invoices = self.env["account.move"].search([
            ("partner_id", "=", self.partner_id.id),
            ("move_type", "=", "out_invoice"),
            ("payment_state", "in", ["not_paid", "partial"]),
        ])
        if unpaid_invoices:
            raise UserError(_("Cannot terminate a profile with unpaid invoices."))
        self.write({"state": "terminated", "active": False})
        self.message_post(body=_("Billing profile terminated."))

    def action_reset_to_draft(self):
        """Reset profile to draft state."""
        self.ensure_one()
        self.write({"state": "draft"})
        self.message_post(body=_("Billing profile reset to draft."))
        self.ensure_one()
        unpaid_invoices = self.env["account.move"].search([
            ("partner_id", "=", self.partner_id.id),
            ("move_type", "=", "out_invoice"),
            ("payment_state", "in", ["not_paid", "partial"]),
        ])
        if unpaid_invoices:
            raise UserError(_("Cannot terminate a profile with unpaid invoices."))
        self.write({"state": "terminated", "active": False})
        self.message_post(body=_("Billing profile terminated."))

    def action_reset_to_draft(self):
        """Reset profile to draft state."""
        self.ensure_one()
        self.write({"state": "draft"})
        self.message_post(body=_("Billing profile reset to draft."))



