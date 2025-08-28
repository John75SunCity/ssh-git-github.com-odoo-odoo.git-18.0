# -*- coding: utf-8 -*-
from odoo import api, fields, models


class AdvancedBillingProfile(models.Model):
    _name = 'advanced.billing.profile'
    _description = 'Advanced Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Profile Name', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # Billing Configuration
    billing_frequency = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annual'),
        ('weekly', 'Weekly')
    ], string='Billing Frequency', default='monthly', required=True, tracking=True)

    billing_cycle_day = fields.Integer(string='Billing Cycle Day', default=1,
                                      help='Day of the month/quarter/year when billing occurs')
    auto_billing = fields.Boolean(string='Auto Billing', default=True, tracking=True)
    discount_percentage = fields.Float(string='Discount %', digits=(5,2), tracking=True)

    # Related billing configuration
    company_id = fields.Many2one('res.company', string='Company',
                                default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='company_id.currency_id', string='Currency',
                                 store=True, readonly=True)

    # Billing lines
    billing_line_ids = fields.One2many('advanced.billing.line', 'billing_profile_id',
                                      string='Billing Lines')

    # Contact management
    contact_ids = fields.One2many('advanced.billing.contact', 'billing_profile_id',
                                 string='Billing Contacts')
    primary_contact_id = fields.Many2one('advanced.billing.contact', string='Primary Contact',
                                        domain="[('billing_profile_id', '=', id)]")

    # Status and computed fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('archived', 'Archived')
    ], default='draft', string='Status', tracking=True)

    # Computed fields
    total_monthly_amount = fields.Monetary(string='Total Monthly Amount',
                                          compute='_compute_totals', store=True,
                                          currency_field='currency_id')
    contact_count = fields.Integer(string='Contact Count', compute='_compute_counts')

    @api.depends('billing_line_ids.amount', 'billing_frequency', 'discount_percentage')
    def _compute_totals(self):
        for profile in self:
            base_amount = sum(profile.billing_line_ids.mapped('amount'))
            # Apply discount
            discounted_amount = base_amount * (1 - (profile.discount_percentage / 100))

            # Convert to monthly equivalent
            if profile.billing_frequency == 'weekly':
                profile.total_monthly_amount = discounted_amount * 4.33
            elif profile.billing_frequency == 'quarterly':
                profile.total_monthly_amount = discounted_amount / 3
            elif profile.billing_frequency == 'annually':
                profile.total_monthly_amount = discounted_amount / 12
            else:  # monthly
                profile.total_monthly_amount = discounted_amount

    @api.depends('contact_ids')
    def _compute_counts(self):
        for profile in self:
            profile.contact_count = len(profile.contact_ids)

    def action_activate(self):
        """Activate the billing profile"""
        self.state = 'active'

    def action_suspend(self):
        """Suspend the billing profile"""
        self.state = 'suspended'

    def action_archive(self):
        """Archive the billing profile"""
        self.state = 'archived'
        self.active = False
