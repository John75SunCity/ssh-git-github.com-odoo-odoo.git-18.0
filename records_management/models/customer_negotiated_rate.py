# -*- coding: utf-8 -*-
"""
Customer Negotiated Rate Module

Manages special pricing agreements with customers for specific services or
container types, including an approval workflow and automated application.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class CustomerNegotiatedRate(models.Model):
    _name = 'customer.negotiated.rate'
    _description = 'Customer Negotiated Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'partner_id, priority, effective_date desc'

    # ============================================================================
    # CORE & WORKFLOW
    # ============================================================================
    name = fields.Char(string="Rate Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted for Approval'),
        ('approved', 'Approved'),
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected')
    ], string='Status', default='draft', required=True, tracking=True)
    priority = fields.Integer(string='Priority', default=10, help="Lower number means higher priority for auto-application.")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    billing_profile_id = fields.Many2one(
        "customer.billing.profile", string="Billing Profile", domain="[('partner_id', '=', partner_id)]"
    )

    # ============================================================================
    # RATE CONFIGURATION
    # ============================================================================
    rate_type = fields.Selection([
        ('storage', 'Storage'),
        ('service', 'Service'),
        ('volume_discount', 'Volume Discount')
    ], string='Rate Type', required=True, default='storage', tracking=True)
    container_type_id = fields.Many2one('records.container.type', string='Container Type', help="Apply this rate to a specific container type.")
    service_type_id = fields.Many2one('records.service.type', string='Service Type', help="Apply this rate to a specific service type.")
    effective_date = fields.Date(string='Effective Date', required=True, default=fields.Date.context_today, tracking=True)
    expiration_date = fields.Date(string='Expiration Date', tracking=True)
    is_current = fields.Boolean(string='Is Currently Active', compute='_compute_is_current', store=True)
    auto_apply = fields.Boolean(string='Auto-Apply Rate', default=True, help="If checked, this rate will be automatically applied to new matching services/containers.")
    contract_reference = fields.Char(string='Contract Reference', tracking=True)

    # ============================================================================
    # FINANCIALS & PRICING
    # ============================================================================
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency')
    monthly_rate = fields.Monetary(string='Monthly Rate', tracking=True, currency_field='currency_id')
    annual_rate = fields.Monetary(string='Annual Rate', compute='_compute_annual_rate', inverse='_inverse_annual_rate', store=True, currency_field='currency_id')
    setup_fee = fields.Monetary(string='One-Time Setup Fee', currency_field='currency_id')
    per_service_rate = fields.Monetary(string='Per Service Rate', currency_field='currency_id')
    per_hour_rate = fields.Monetary(string='Per Hour Rate', currency_field='currency_id')
    per_document_rate = fields.Monetary(string='Per Document Rate', currency_field='currency_id')
    minimum_volume = fields.Integer(string='Minimum Volume/Quantity')
    maximum_volume = fields.Integer(string='Maximum Volume/Quantity')
    discount_percentage = fields.Float(string='Discount (%)')

    # ============================================================================
    # APPROVAL
    # ============================================================================
    approval_required = fields.Boolean(string='Approval Required', default=True)
    approved_by_id = fields.Many2one('res.users', string='Approved By', readonly=True, copy=False)
    approval_date = fields.Datetime(string='Approval Date', readonly=True, copy=False)

    # ============================================================================
    # ANALYTICS & COMPARISON
    # ============================================================================
    base_rate_comparison = fields.Monetary(string='Base Rate Comparison', compute='_compute_rate_comparison', store=True, currency_field='currency_id')
    savings_amount = fields.Monetary(string='Savings Amount', compute='_compute_rate_comparison', store=True, currency_field='currency_id')
    savings_percentage = fields.Float(string='Savings (%)', compute='_compute_rate_comparison', store=True)
    containers_using_rate = fields.Integer(string='Containers Using Rate', compute='_compute_usage_stats')
    monthly_revenue_impact = fields.Monetary(string='Monthly Revenue Impact', compute='_compute_usage_stats', currency_field='currency_id')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('effective_date', 'expiration_date', 'state')
    def _compute_is_current(self):
        """Determine if a rate is currently active based on dates and state."""
        today = fields.Date.today()
        for rate in self:
            is_effective = rate.effective_date <= today
            is_not_expired = not rate.expiration_date or rate.expiration_date >= today
            rate.is_current = rate.state == 'active' and is_effective and is_not_expired

    @api.depends('monthly_rate')
    def _compute_annual_rate(self):
        """Calculate annual rate from monthly rate."""
        for rate in self:
            rate.annual_rate = rate.monthly_rate * 12

    def _inverse_annual_rate(self):
        """Calculate monthly rate from annual rate."""
        for rate in self:
            rate.monthly_rate = (rate.annual_rate / 12) if rate.annual_rate else 0.0

    @api.depends('rate_type', 'monthly_rate', 'container_type_id')
    def _compute_rate_comparison(self):
        """Compare negotiated rate to the standard base rate."""
        # Use the correct model name for base rates
        base_rate_model = self.env.get('base.rate')
        if not base_rate_model:
            self.update({'base_rate_comparison': 0, 'savings_amount': 0, 'savings_percentage': 0})
            return

        base_rate_rec = base_rate_model.search([('company_id', '=', self.env.company.id)], limit=1)
        if not base_rate_rec:
            self.update({'base_rate_comparison': 0, 'savings_amount': 0, 'savings_percentage': 0})
            return

        for rate in self:
            if rate.rate_type != 'storage' or not rate.container_type_id:
                rate.base_rate_comparison = 0.0
                rate.savings_amount = 0.0
                rate.savings_percentage = 0.0
                continue

            # Simplified: assumes base rate is on container type. Adjust if needed.
            base_rate = rate.container_type_id.standard_rate
            rate.base_rate_comparison = base_rate
            rate.savings_amount = base_rate - rate.monthly_rate
            if base_rate > 0:
                rate.savings_percentage = ((base_rate - rate.monthly_rate) / base_rate) * 100
            else:
                rate.savings_percentage = 0.0

    @api.depends('partner_id', 'is_current', 'rate_type', 'container_type_id', 'monthly_rate')
    def _compute_usage_stats(self):
        """Compute usage statistics for this rate."""
        for rate in self:
            if not rate.partner_id or not rate.is_current or rate.rate_type != 'storage':
                rate.containers_using_rate = 0
                rate.monthly_revenue_impact = 0.0
                continue

            domain = [('partner_id', '=', rate.partner_id.id), ('state', '!=', 'destroyed')]
            if rate.container_type_id:
                domain.append(('container_type_id', '=', rate.container_type_id.id))

            container_count = self.env['records.container'].search_count(domain)
            rate.containers_using_rate = container_count
            rate.monthly_revenue_impact = container_count * (rate.monthly_rate or 0.0)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update fields when customer changes."""
        if self.partner_id:
            if not self.name or self.name == _('New'):
                self.name = _('Rate for %s') % self.partner_id.name

            billing_profile = self.env['customer.billing.profile'].search([
                ('partner_id', '=', self.partner_id.id),
                ('active', '=', True)
            ], limit=1)
            if billing_profile:
                self.billing_profile_id = billing_profile.id

    @api.onchange('rate_type')
    def _onchange_rate_type(self):
        """Clear irrelevant fields when rate type changes."""
        if self.rate_type == 'storage':
            self.service_type_id = False
            self.per_service_rate = 0.0
            self.per_hour_rate = 0.0
            self.per_document_rate = 0.0
        elif self.rate_type == 'service':
            self.container_type_id = False
            self.monthly_rate = 0.0
            self.annual_rate = 0.0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('effective_date', 'expiration_date')
    def _check_date_validity(self):
        for rate in self:
            if rate.expiration_date and rate.effective_date > rate.expiration_date:
                raise ValidationError(_('Effective date cannot be after expiration date.'))

    @api.constrains('minimum_volume', 'maximum_volume')
    def _check_volume_range(self):
        for rate in self:
            if rate.maximum_volume and rate.minimum_volume > rate.maximum_volume:
                raise ValidationError(_('Minimum volume cannot be greater than maximum volume.'))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        for rate in self:
            if not (0 <= rate.discount_percentage <= 100):
                raise ValidationError(_('Discount percentage must be between 0 and 100.'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit_for_approval(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft rates can be submitted for approval.'))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Rate submitted for approval."))

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_('Only submitted rates can be approved.'))

        vals = {
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now()
        }
        self.write(vals)
        self.message_post(body=_("Rate approved by %s.") % self.env.user.name)

        # Automatically activate if the effective date is today or in the past
        if self.effective_date <= fields.Date.today():
            self.action_activate()

    def action_reject(self):
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Rate rejected by %s.") % self.env.user.name)

    def action_activate(self):
        for rate in self:
            if rate.state != 'approved':
                raise UserError(_('Only approved rates can be activated.'))
            if rate.effective_date > fields.Date.today():
                raise UserError(_('Cannot activate rate before its effective date (%s).') % rate.effective_date)
            rate.write({'state': 'active'})
            rate.message_post(body=_("Rate activated."))

    def action_expire(self):
        self.write({'state': 'expired'})
        self.message_post(body=_("Rate manually expired."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
        self.message_post(body=_("Rate reset to draft."))

    # ============================================================================
    # CRON METHODS
    # ============================================================================
    @api.model
    def _cron_activate_pending_rates(self):
        """Cron job to activate approved rates when their effective date is reached."""
        rates_to_activate = self.search([
            ('state', '=', 'approved'),
            ('effective_date', '<=', fields.Date.today())
        ])
        rates_to_activate.action_activate()

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_effective_rate(self, rate_field):
        """Get the effective rate for a specific field, considering discounts and current status"""
        self.ensure_one()

        if not self.is_current or self.state != "active":
            return 0.0

        # Get the base rate value
        base_rate = getattr(self, rate_field, 0.0) or 0.0

        # Apply discount if configured
        if self.discount_percentage and base_rate > 0:
            discount_amount = base_rate * (self.discount_percentage / 100)
            return base_rate - discount_amount

        return base_rate

    def get_rate_comparison(self, base_rate_model=None):
        """Compare negotiated rate to base rate for analytics"""
        self.ensure_one()

        comparison_data = {
            "negotiated_rate": self.monthly_rate or 0.0,
            "base_rate": 0.0,
            "savings_amount": 0.0,
            "savings_percentage": 0.0,
        }

        if base_rate_model:
            # Try to find matching base rate
            base_rate = base_rate_model.search([("service_type", "=", self.rate_type), ("active", "=", True)], limit=1)

            if base_rate:
                base_value = getattr(base_rate, "monthly_rate", 0.0) or getattr(base_rate, "standard_rate", 0.0) or 0.0
                comparison_data["base_rate"] = base_value

                if base_value > 0 and self.monthly_rate:
                    comparison_data["savings_amount"] = base_value - self.monthly_rate
                    comparison_data["savings_percentage"] = ((base_value - self.monthly_rate) / base_value) * 100

        return comparison_data
