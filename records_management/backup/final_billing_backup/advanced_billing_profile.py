from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class RecordsBillingProfile(models.Model):
    _name = 'advanced.billing.profile'
    _description = 'Records Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Profile Name", required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True, domain="[('is_company', '=', True)]")
    department_id = fields.Many2one('records.department', string="Department", tracking=True, help="Link this profile to a specific customer department.")

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('semi-annually', 'Semi-Annually'),
        ('annually', 'Annually'),
    ], string="Billing Frequency", default='monthly', required=True, tracking=True)
    billing_cycle_day = fields.Integer(string="Billing Day of Month", default=1, tracking=True, help="The day of the month to generate invoices (e.g., 1 for the first day).")
    payment_term_id = fields.Many2one('account.payment.term', string="Payment Terms", tracking=True)
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string="Currency", readonly=True)
    fiscal_position_id = fields.Many2one('account.fiscal.position', string='Fiscal Position', help="Fiscal Position for tax determination.")
    auto_billing = fields.Boolean(string="Automated Billing", default=True, help="Enable automatic generation of recurring invoices for this profile.")
    consolidate_invoices = fields.Boolean(string="Consolidate Invoices", default=True, help="Group all billable services for this profile into a single invoice.")

    # ============================================================================
    # CONTACTS & COMMUNICATION
    # ============================================================================
    billing_contact_ids = fields.One2many('advanced.billing.contact', 'profile_id', string="Billing Contacts")
    send_reminders = fields.Boolean(string="Send Payment Reminders", default=True)
    email_invoices = fields.Boolean(string="Email Invoices Automatically", default=True)

    # ============================================================================
    # SERVICES & PRICING
    # ============================================================================
    billing_service_ids = fields.Many2many('product.product', string="Billable Services", domain="[('type', '=', 'service')]")
    require_purchase_orders = fields.Boolean(string="Require Purchase Orders")
    discount_percentage = fields.Float(string="Discount (%)", digits=(16, 2), tracking=True)
    minimum_monthly_charge = fields.Monetary(string="Minimum Monthly Charge", tracking=True)

    # ============================================================================
    # FINANCIAL & STATE FIELDS
    # ============================================================================
    credit_limit = fields.Monetary(string="Credit Limit", tracking=True)
    current_balance = fields.Monetary(string="Current Balance", compute='_compute_current_balance')
    available_credit = fields.Monetary(string="Available Credit", compute='_compute_available_credit')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    ], string="Status", default='draft', required=True, tracking=True)
    last_billing_date = fields.Date(string="Last Billing Date", readonly=True)
    next_billing_date = fields.Date(string="Next Billing Date", compute='_compute_next_billing_date', store=True)
    total_billed_amount = fields.Monetary(string="Total Billed", compute='_compute_billing_totals')

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('billing_contact_ids', 'billing_contact_ids.is_primary')
    def _compute_primary_contact(self):
        for profile in self:
            primary = profile.billing_contact_ids.filtered('is_primary')
            profile.primary_contact_id = primary[0] if primary else False

    @api.depends('partner_id')
    def _compute_current_balance(self):
        for profile in self:
            if profile.partner_id:
                # This is a simplified calculation. A real implementation might be more complex.
                profile.current_balance = profile.partner_id.total_due
            else:
                profile.current_balance = 0.0

    @api.depends('credit_limit', 'current_balance')
    def _compute_available_credit(self):
        for profile in self:
            profile.available_credit = profile.credit_limit - profile.current_balance

    @api.depends('last_billing_date', 'billing_frequency', 'billing_cycle_day')
    def _compute_next_billing_date(self):
        for profile in self:
            if not profile.last_billing_date or not profile.billing_frequency:
                profile.next_billing_date = False
                continue

            last_date = profile.last_billing_date
            months_to_add = {'monthly': 1, 'quarterly': 3, 'semi-annually': 6, 'annually': 12}.get(profile.billing_frequency, 1)
            next_date = last_date + relativedelta(months=months_to_add)
            profile.next_billing_date = next_date.replace(day=profile.billing_cycle_day) if profile.billing_cycle_day <= 28 else next_date

    @api.depends('billing_service_ids', 'billing_service_ids.price')
    def _compute_billing_totals(self):
        for profile in self:
            total_billed = sum(profile.billing_service_ids.mapped('price'))
            profile.total_billed_amount = total_billed - (total_billed * (profile.discount_percentage / 100.0))

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update fields when partner changes"""
        pass

    @api.onchange('billing_cycle_day')
    def _onchange_billing_cycle_day(self):
        """Validate billing cycle day"""
        if not 1 <= self.billing_cycle_day <= 31:
            raise ValidationError(_("Billing Day of Month must be between 1 and 31."))

    def action_view_services(self):
        """View associated billing services"""
        self.ensure_one()
        pass

    def action_view_invoices(self):
        """View invoices for this customer"""
        self.ensure_one()
        pass

    def action_create_contact(self):
        """Create new billing contact for this profile"""
        self.ensure_one()
        pass

    def action_generate_invoice(self):
        """Generate invoice for this billing profile"""
        self.ensure_one()
        pass

    def action_activate(self):
        """Activate billing profile"""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Billing profile activated"))

    def action_suspend(self):
        """Suspend billing profile"""
        self.ensure_one()
        self.write({'state': 'suspended'})
        self.message_post(body=_("Billing profile suspended"))

    def action_close(self):
        """Close billing profile"""
        self.ensure_one()
        self.write({'state': 'closed'})
        self.message_post(body=_("Billing profile closed"))

    def _check_credit_limit_value(self, amount):
        """Check if amount would exceed credit limit"""
        self.ensure_one()
        if self.credit_limit > 0 and (self.current_balance + amount) > self.credit_limit:
            raise UserError(_("This transaction would exceed the customer's credit limit."))
        return True

    @api.constrains('credit_limit')
    def _check_credit_limit(self):
        """Validate credit limit is not negative"""
        for profile in self:
            if profile.credit_limit < 0:
                raise ValidationError(_("Credit limit cannot be negative."))

    @api.constrains('billing_cycle_day')
    def _check_billing_cycle_day(self):
        """Validate billing cycle day"""
        for profile in self:
            if not 1 <= profile.billing_cycle_day <= 31:
                raise ValidationError(_("Billing Day of Month must be between 1 and 31."))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        """Validate discount percentage"""
        for profile in self:
            if not 0.0 <= profile.discount_percentage <= 100.0:
                raise ValidationError(_("Discount percentage must be between 0 and 100."))

    def name_get(self):
        """Custom name display with partner name"""
        result = []
        for profile in self:
            name = f"{profile.partner_id.name} - {profile.name}"
            result.append((profile.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name or partner name"""
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('partner_id.name', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_profile_for_partner(self, partner_id):
        """Get active billing profile for a specific partner"""
        return self.search([
            ('partner_id', '=', partner_id),
            ('state', '=', 'active')
        ], limit=1)

    def get_profile_summary(self):
        """Get profile summary for reporting"""
        self.ensure_one()
        return {
            'name': self.name,
            'partner': self.partner_id.name,
            'next_billing_date': self.next_billing_date,
            'current_balance': self.current_balance,
        }
