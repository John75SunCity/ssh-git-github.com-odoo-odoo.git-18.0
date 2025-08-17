# -*- coding: utf-8 -*-

Records Billing Profile Management Module

This module provides comprehensive billing profile management for the Records Management:
    pass
System. It serves as the central configuration point for customer billing preferences,:
payment terms, and contact management.

Key Features
- Customer billing configuration and preferences
- Payment terms and billing frequency management
- Integration with billing contacts and services
- Automated billing rule application
- Credit limit and payment history tracking

Business Processes
1. Profile Creation: Setting up billing profiles for customers:
2. Contact Management: Managing billing contacts per profile
3. Payment Terms: Configuring payment schedules and terms
4. Service Association: Linking profiles to billing services
5. Credit Management: Monitoring credit limits and payment history

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBillingProfile(models.Model):
    """Records Billing Profile
    
        Central configuration point for customer billing preferences,""":
    payment terms, and automated billing processes.

    _name = "records.billing.profile"
    _description = "Records Billing Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, partner_id"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Profile Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the billing profile"
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this billing profile":
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this billing profile is active"
    

        # ============================================================================
    # CUSTOMER RELATIONSHIP
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        ondelete="cascade",
        help="Customer associated with this billing profile"
    

    department_id = fields.Many2one(
        "records.department",
        string="Department",
        related="partner_id.records_department_id",
        store=True,
        help="Records department for this customer":
    

        # ============================================================================
    # BILLING CONFIGURATION
        # ============================================================================
    billing_frequency = fields.Selection([)]
        ("monthly", "Monthly"),
        ("quarterly", "Quarterly"),
        ("annually", "Annually"),
        ("on_demand", "On Demand"),
        ("weekly", "Weekly"),
        ("bi_weekly", "Bi-Weekly"),
    
        default="monthly",
       tracking=True,
       help="How often to generate bills for this profile"
    billing_cycle_day = fields.Integer(
        string="Billing Cycle Day",
        default=1,
        help="Day of month to generate bills (1-31)"
    

    payment_term_id = fields.Many2one(
        "account.payment.term",
        string="Payment Terms",
        help="Payment terms for this billing profile":
    

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
        help="Currency for billing":
    

    fiscal_position_id = fields.Many2one(
        "account.fiscal.position",
        string="Fiscal Position",
        help="Fiscal position for tax calculations":
    

        # ============================================================================
    # CONTACT RELATIONSHIPS
        # ============================================================================
    billing_contact_ids = fields.One2many(
        "records.billing.contact",
        "billing_profile_id",
        string="Billing Contacts",
        help="Contacts associated with this billing profile"
    

    primary_contact_id = fields.Many2one(
        "records.billing.contact",
        string="Primary Contact",
        compute="_compute_primary_contact",
        store=True,
        help="Primary billing contact for this profile":
    

    invoice_email = fields.Char(
        string="Invoice Email",
        help="Email address for sending invoices":
    

        # ============================================================================
    # SERVICE RELATIONSHIPS
        # ============================================================================
    billing_service_ids = fields.Many2many(
        "records.billing.service",
        "billing_profile_service_rel",
        "profile_id",
        "service_id",
        string="Associated Services",
        help="Billing services associated with this profile"
    

        # ============================================================================
    # CREDIT AND LIMITS
        # ============================================================================
    credit_limit = fields.Monetary(
        string="Credit Limit",
        currency_field="currency_id",
        default=0.0,
        help="Credit limit for this customer":
    

    current_balance = fields.Monetary(
        string="Current Balance",
        currency_field="currency_id",
        compute="_compute_current_balance",
        store=True,
        help="Current outstanding balance"
    

    available_credit = fields.Monetary(
        string="Available Credit",
        currency_field="currency_id",
        compute="_compute_available_credit",
        store=True,
        help="Available credit (limit - current balance)"
    

        # ============================================================================
    # BILLING PREFERENCES
        # ============================================================================
    auto_billing = fields.Boolean(
        string="Auto Billing",
        default=True,
        help="Automatically generate bills based on billing frequency"
    

    consolidate_invoices = fields.Boolean(
        string="Consolidate Invoices",
        default=False,
        help="Consolidate multiple services into single invoice"
    

    send_reminders = fields.Boolean(
        string="Send Payment Reminders",
        default=True,
        help="Send automated payment reminder emails"
    

    email_invoices = fields.Boolean(
        string="Email Invoices",
        default=True,
        help="Automatically email invoices when generated"
    

    require_purchase_orders = fields.Boolean(
        string="Require Purchase Orders",
        default=False,
        help="Require purchase order numbers for billing":
    

        # ============================================================================
    # PRICING AND DISCOUNTS
        # ============================================================================
    discount_percentage = fields.Float(
        string="Discount Percentage",
        digits=(5, 2),
        default=0.0,
        help="Default discount percentage for this customer":
    

    minimum_monthly_charge = fields.Monetary(
        string="Minimum Monthly Charge",
        currency_field="currency_id",
        default=0.0,
        help="Minimum monthly billing amount"
    

        # ============================================================================
    # WORKFLOW STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([)]
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('closed', 'Closed'),
    
        help='Current status of the billing profile'

    # ============================================================================
        # BILLING HISTORY TRACKING
    # ============================================================================
    last_billing_date = fields.Date(
        string="Last Billing Date",
        help="Date of last billing generation"
    

    next_billing_date = fields.Date(
        string="Next Billing Date",
        compute="_compute_next_billing_date",
        store=True,
        help="Next scheduled billing date"
    

    total_billed_amount = fields.Monetary(
        string="Total Billed Amount",
        currency_field="currency_id",
        compute="_compute_billing_totals",
        store=True,
        help="Total amount billed to date"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    

        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    @api.depends("billing_contact_ids", "billing_contact_ids.primary_contact")
    def _compute_primary_contact(self):
        """Compute primary contact for this billing profile""":
        for record in self:
            primary_contact = record.billing_contact_ids.filtered()
                lambda c: c.primary_contact and c.active
            
            record.primary_contact_id = ()
                primary_contact[0] if primary_contact else False:
            

    @api.depends("partner_id")
    def _compute_current_balance(self):
        """Compute current outstanding balance"""
        for record in self:
            # Integration with account.move to calculate balance
            if record.partner_id:
                domain = []
                    ('partner_id', '=', record.partner_id.id),
                    ('move_type', 'in', ['out_invoice', 'out_refund']),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial'])
                
                
                invoices = self.env['account.move'].search(domain)
                record.current_balance = sum(invoices.mapped('amount_residual'))
            else:
                record.current_balance = 0.0

    @api.depends("credit_limit", "current_balance")
    def _compute_available_credit(self):
        """Compute available credit"""
        for record in self:
            record.available_credit = record.credit_limit - record.current_balance

    @api.depends("billing_frequency", "last_billing_date", "billing_cycle_day")
    def _compute_next_billing_date(self):
        """Compute next billing date based on frequency"""
        from datetime import datetime, timedelta
        from dateutil.relativedelta import relativedelta
        
        for record in self:
            if not record.last_billing_date:
                # If no last billing date, use today
    base_date = fields.Date.today()
            else:
                base_date = record.last_billing_date
            
            if record.billing_frequency == 'monthly':
                next_date = base_date + relativedelta(months=1)
            elif record.billing_frequency == 'quarterly':
                next_date = base_date + relativedelta(months=3)
            elif record.billing_frequency == 'annually':
                next_date = base_date + relativedelta(years=1)
            elif record.billing_frequency == 'weekly':
                next_date = base_date + timedelta(weeks=1)
            elif record.billing_frequency == 'bi_weekly':
                next_date = base_date + timedelta(weeks=2)
            else:  # on_demand
                next_date = False
            
            record.next_billing_date = next_date

    @api.depends("partner_id")
    def _compute_billing_totals(self):
        """Compute total billing amounts"""
        for record in self:
            if record.partner_id:
                domain = []
                    ('partner_id', '=', record.partner_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted')
                
                
                invoices = self.env['account.move'].search(domain)
                record.total_billed_amount = sum(invoices.mapped('amount_total'))
            else:
                record.total_billed_amount = 0.0

    # Count fields for UI:
    @api.depends("billing_contact_ids")
    def _compute_contact_count(self):
        """Compute number of billing contacts"""
        for record in self:
            record.contact_count = len(record.billing_contact_ids)

    contact_count = fields.Integer(
        string="Contact Count",
        compute="_compute_contact_count",
        store=True,
        help="Number of billing contacts"
    

    @api.depends("billing_service_ids")
    def _compute_service_count(self):
        """Compute number of associated services"""
        for record in self:
            record.service_count = len(record.billing_service_ids)

    service_count = fields.Integer(
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Number of associated billing services"
    

        # ============================================================================
    # ONCHANGE METHODS
        # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update fields when partner changes"""
        if self.partner_id:
            # Set default payment terms from partner
            if self.partner_id.property_payment_term_id:
                self.payment_term_id = self.partner_id.property_payment_term_id
            
            # Set invoice email from partner
            if self.partner_id.email:
                self.invoice_email = self.partner_id.email
            
            # Set default name if not set:
            if not self.name:
                self.name = _("Billing Profile - %s", self.partner_id.name)

    @api.onchange('billing_cycle_day')
    def _onchange_billing_cycle_day(self):
        """Validate billing cycle day"""
        if self.billing_cycle_day and not (1 <= self.billing_cycle_day <= 31):
            return {}
                'warning': {}
                    'title': _('Invalid Billing Cycle Day'),
                    'message': _('Billing cycle day must be between 1 and 31')
                
            

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_view_contacts(self):
        """View billing contacts for this profile""":
        self.ensure_one()

        return {}
            "type": "ir.actions.act_window",
            "name": _("Billing Contacts: %s", self.name),
            "res_model": "records.billing.contact",
            "view_mode": "tree,form",
            "domain": [("billing_profile_id", "=", self.id)],
            "context": {}
                "default_billing_profile_id": self.id,
                "default_partner_id": self.partner_id.id,
            
        

    def action_view_services(self):
        """View associated billing services"""
        self.ensure_one()

        return {}
            "type": "ir.actions.act_window",
            "name": _("Billing Services: %s", self.name),
            "res_model": "records.billing.service",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.billing_service_ids.ids)],
            "context": {}
                "default_profile_id": self.id,
            
        

    def action_view_invoices(self):
        """View invoices for this customer""":
        self.ensure_one()

        return {}
            "type": "ir.actions.act_window",
            "name": _("Invoices: %s", self.partner_id.name),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "domain": []
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice")
            
            "context": {}
                "default_partner_id": self.partner_id.id,
                "default_move_type": "out_invoice",
            
        

    def action_create_contact(self):
        """Create new billing contact for this profile""":
        self.ensure_one()

        return {}
            "type": "ir.actions.act_window",
            "name": _("New Billing Contact"),
            "res_model": "records.billing.contact",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_billing_profile_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_name": _("%s Contact", self.partner_id.name),
            
        

    def action_generate_invoice(self):
        """Generate invoice for this billing profile""":
        self.ensure_one()
        
        if self.state != 'active':
            raise ValidationError(_("Can only generate invoices for active profiles")):
        # Create invoice based on billing services
        invoice_lines = []
        
        for service in self.billing_service_ids:
            if service.active:
                line_vals = service._prepare_invoice_line()
                if line_vals:
                    invoice_lines.append((0, 0, line_vals))
        
        if not invoice_lines:
            raise ValidationError(_("No billable services found for this profile")):
        invoice_vals = {}
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'payment_term_id': self.payment_term_id.id,
            'fiscal_position_id': self.fiscal_position_id.id,
            'invoice_line_ids': invoice_lines,
        
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Update last billing date
        self.write({'last_billing_date': fields.Date.today()})
        
        # Send email if configured:
        if self.email_invoices and self.invoice_email:
            invoice.action_send_and_print()
        
        return {}
            "type": "ir.actions.act_window",
            "name": _("Generated Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "res_id": invoice.id,
            "target": "current",
        

    def action_activate(self):
        """Activate billing profile"""
        self.write({'state': 'active'})
        self.message_post(body=_("Billing profile activated"))

    def action_suspend(self):
        """Suspend billing profile"""
        self.write({'state': 'suspended'})
        self.message_post(body=_("Billing profile suspended"))

    def action_close(self):
        """Close billing profile"""
        self.write({'state': 'closed'})
        self.message_post(body=_("Billing profile closed"))

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    def check_credit_limit(self, amount):
        """Check if amount would exceed credit limit""":
        self.ensure_one()
        
        if self.credit_limit > 0:
            new_balance = self.current_balance + amount
            if new_balance > self.credit_limit:
                return False
        return True

    def get_billing_address(self):
        """Get billing address for invoices""":
        self.ensure_one()
        
        # Use partner's invoice address
        invoice_partner = self.partner_id.address_get(['invoice'])['invoice']
        return self.env['res.partner'].browse(invoice_partner)

    def calculate_discount_amount(self, base_amount):
        """Calculate discount amount based on profile settings"""
        self.ensure_one()
        
        if self.discount_percentage > 0:
            return base_amount * (self.discount_percentage / 100)
        return 0.0

    @api.model
    def run_scheduled_billing(self):
        """Run scheduled billing for all active profiles""":
    today = fields.Date.today()
        
        profiles = self.search([)]
            ('state', '=', 'active'),
            ('auto_billing', '=', True),
            ('next_billing_date', '<=', today)
        
        
        for profile in profiles:
            try:
                profile.action_generate_invoice()
            except Exception as e
                # Log error and continue with other profiles
                profile.message_post()
                    body=_("Automatic billing failed: %s", str(e)),
                    message_type='comment',
                    subtype_id=self.env.ref('mail.mt_note').id
                

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains("credit_limit")
    def _check_credit_limit(self):
        """Validate credit limit is not negative"""
        for record in self:
            if record.credit_limit < 0:
                raise ValidationError(_("Credit limit cannot be negative"))

    @api.constrains("billing_cycle_day")
    def _check_billing_cycle_day(self):
        """Validate billing cycle day"""
        for record in self:
            if record.billing_cycle_day and not (1 <= record.billing_cycle_day <= 31):
                raise ValidationError(_("Billing cycle day must be between 1 and 31"))

    @api.constrains("discount_percentage")
    def _check_discount_percentage(self):
        """Validate discount percentage"""
        for record in self:
            if not (0 <= record.discount_percentage <= 100):
                raise ValidationError(_("Discount percentage must be between 0 and 100"))

    @api.constrains('partner_id')
    def _check_unique_active_profile(self):
        """Ensure only one active profile per partner"""
        for record in self:
            if record.state == 'active':
                existing = self.search([)]
                    ('partner_id', '=', record.partner_id.id),
                    ('state', '=', 'active'),
                    ('id', '!=', record.id)
                
                if existing:
                    raise ValidationError(_())
                        "Partner %s already has an active billing profile: %s",
                        record.partner_id.name,
                        existing[0].name
                    

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with partner name"""
        result = []
        for record in self:
            name = _("%(profile)s (%(partner)s)", {)}
                'profile': record.name,
                'partner': record.partner_id.name
            
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name or partner name"""
        args = args or []
        domain = []
        
        if name:
            domain = []
                "|", "|",
                ("name", operator, name),
                ("partner_id.name", operator, name),
                ("partner_id.ref", operator, name),
            
        
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_profile_for_partner(self, partner_id):
        """Get active billing profile for a specific partner""":
        return self.search([)]
            ("partner_id", "=", partner_id),
            ("state", "=", "active")
        

    def get_profile_summary(self):
        """Get profile summary for reporting""":
        self.ensure_one()
        return {}
            'profile_name': self.name,
            'partner_name': self.partner_id.name,
            'billing_frequency': self.billing_frequency,
            'credit_limit': self.credit_limit,
            'current_balance': self.current_balance,
            'available_credit': self.available_credit,
            'contact_count': self.contact_count,
            'service_count': self.service_count,
            'state': self.state,
            'next_billing_date': self.next_billing_date,
        

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_billing_dashboard_data(self):
        """Get data for billing dashboard""":
    today = fields.Date.today()
        
        return {}
            'total_profiles': self.search_count([,
            'active_profiles': self.search_count([('state', '=', 'active')]),
            'suspended_profiles': self.search_count([('state', '=', 'suspended')]),
            'profiles_due_billing': self.search_count([)]
                ('state', '=', 'active'),
                ('auto_billing', '=', True),
                ('next_billing_date', '<=', today)
            
            'total_outstanding': sum(self.search([.mapped('current_balance')),
            'profiles_over_limit': self.search_count([)]
                ('credit_limit', '>', 0),
                ('current_balance', '>', self.env.context.get('credit_limit', 0))
            
        

    @api.model
    def generate_billing_report(self, date_from=None, date_to=None):
        """Generate comprehensive billing report"""
        domain = []
        
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))
        
        profiles = self.search(domain)
        
        return {}
            'profiles': [profile.get_profile_summary() for profile in profiles],:
            'total_profiles': len(profiles),
            'total_credit_limit': sum(profiles.mapped('credit_limit')),
            'total_outstanding': sum(profiles.mapped('current_balance')),
            'average_balance': sum(profiles.mapped('current_balance')) / len(profiles) if profiles else 0,:
        
