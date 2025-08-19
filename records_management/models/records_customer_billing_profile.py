from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsCustomerBillingProfile(models.Model):
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
    payment_terms_id = fields.Many2one('account.payment.term', string="Payment Terms")
    billing_cycle_day = fields.Integer(string="Billing Cycle Day", default=1, help="Day of the month to generate invoices (1-31).")
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
        for record in self:
            if record.partner_id and record.name:
                record.display_name = f"{record.partner_id.name} - {record.name}"
            else:
                record.display_name = record.name or _("New Profile")

    @api.depends('partner_id')
    def _compute_invoice_totals(self):
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
        for record in self:
            if not record.billing_frequency:
                record.next_billing_date = False
                continue

            base_date = record.last_invoice_date or fields.Date.today()
            day = min(record.billing_cycle_day, 28) # Avoid issues with short months

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
            
            record.next_billing_date = next_date.replace(day=day)

    @api.depends('create_date', 'total_invoiced')
    def _compute_revenue_metrics(self):
        for record in self:
            if record.create_date and record.total_invoiced > 0:
                months_active = relativedelta(fields.Date.today(), record.create_date.date()).months + 1
                record.average_monthly_revenue = record.total_invoiced / months_active if months_active > 0 else 0.0
            else:
                record.average_monthly_revenue = 0.0

    @api.depends('partner_id', 'total_invoiced')
    def _compute_payment_metrics(self):
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

                if not overdue_invoices:
                    record.payment_status = "current"
                else:
                    days_overdue = max((fields.Date.today() - inv.invoice_date_due).days for inv in overdue_invoices)
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
        for record in self:
            if not (1 <= record.billing_cycle_day <= 31):
                raise ValidationError(_("Billing cycle day must be between 1 and 31."))

    @api.constrains('partner_id', 'state')
    def _check_unique_active_profile(self):
        for record in self:
            if record.state == 'active':
                domain = [
                    ("partner_id", "=", record.partner_id.id),
                    ("state", "=", "active"),
                    ("id", "!=", record.id)
                ]
                if record.department_id:
                    domain.append(('department_id', '=', record.department_id.id))
                else:
                    domain.append(('department_id', '=', False))
                
                if self.search(domain):
                    raise ValidationError(_("Customer '%s' already has an active billing profile for this department.", record.partner_id.name))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_invoices(self):
        self.ensure_one()
        return {
            "name": _("Customer Invoices"),
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.partner_id.id), ("move_type", "=", "out_invoice")],
            "context": {"default_partner_id": self.partner_id.id},
        }

    def action_activate(self):
        self.ensure_one()
        self._check_unique_active_profile()
        self.write({"state": "active"})
        self.message_post(body=_("Billing profile activated."))

    def action_suspend(self):
        self.ensure_one()
        self.write({"state": "suspended"})
        self.message_post(body=_("Billing profile suspended."))

    def action_terminate(self):
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
        self.ensure_one()
        self.write({"state": "draft"})
        self.message_post(body=_("Billing profile reset to draft."))



