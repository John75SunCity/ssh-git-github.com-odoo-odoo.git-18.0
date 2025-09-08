# -*- coding: utf-8 -*-
"""
Base Rate Configuration Module

Manages the base pricing rates for all services and products within the
Records Management system. This model serves as the foundation for customer
billing and can be customized with volume and location-based modifiers.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BaseRate(models.Model):
    _name = 'base.rate'
    _description = 'Base Rate Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'company_id, effective_date desc'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(string='Rate Name', required=True, tracking=True, default="Default Base Rates")
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Rate Manager', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True, help="Indicates if this rate card is currently active.")
    effective_date = fields.Date(string='Effective Date', default=fields.Date.context_today, required=True, tracking=True)
    expiration_date = fields.Date(string='Expiration Date', tracking=True)
    version = fields.Char(string='Version', default='1.0', tracking=True)
    description = fields.Text(string='Description')
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', string='Currency', readonly=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True)

    # ============================================================================
    # CONTAINER STORAGE RATES (Based on Business Rules)
    # ============================================================================
    standard_box_rate = fields.Monetary(
        string="Standard Box Rate (Type 01)", help="Rate for 1.2 CF Standard Box.", currency_field="currency_id"
    )
    legal_box_rate = fields.Monetary(
        string="Legal/Banker Box Rate (Type 02)", help="Rate for 2.4 CF Legal/Banker Box.", currency_field="currency_id"
    )
    map_box_rate = fields.Monetary(
        string="Map Box Rate (Type 03)", help="Rate for 0.875 CF Map Box.", currency_field="currency_id"
    )
    odd_size_rate = fields.Monetary(
        string="Odd Size/Temp Box Rate (Type 04)",
        help="Rate for 5.0 CF Odd Size/Temp Box.",
        currency_field="currency_id",
    )
    pathology_rate = fields.Monetary(
        string="Pathology Box Rate (Type 06)", help="Rate for 0.042 CF Pathology Box.", currency_field="currency_id"
    )

    # ============================================================================
    # SERVICE & HOURLY RATES
    # ============================================================================
    pickup_rate = fields.Monetary(string="Pickup Rate", currency_field="currency_id")
    delivery_rate = fields.Monetary(string="Delivery Rate", currency_field="currency_id")
    destruction_rate = fields.Monetary(string="Destruction Rate", currency_field="currency_id")
    document_retrieval_rate = fields.Monetary(string="Document Retrieval Rate", currency_field="currency_id")
    scanning_rate = fields.Monetary(string="Scanning Rate (per page)", currency_field="currency_id")
    indexing_rate = fields.Monetary(string="Indexing Rate (per item)", currency_field="currency_id")
    technician_hourly_rate = fields.Monetary(string="Technician Hourly Rate", currency_field="currency_id")
    supervisor_hourly_rate = fields.Monetary(string="Supervisor Hourly Rate", currency_field="currency_id")

    # ============================================================================
    # ONE-TIME FEES
    # ============================================================================
    new_customer_setup_fee = fields.Monetary(string='New Customer Setup Fee')
    container_setup_fee = fields.Monetary(string='Container Setup Fee')
    barcode_generation_fee = fields.Monetary(string='Barcode Generation Fee')

    # ============================================================================
    # VOLUME-BASED PRICING MODIFIERS
    # ============================================================================
    enable_volume_tiers = fields.Boolean(string='Enable Volume Tiers')
    small_volume_threshold = fields.Integer(string='Small Volume Threshold', help="Upper limit for small volume pricing.")
    small_volume_multiplier = fields.Float(string='Small Volume Multiplier', default=1.0)
    large_volume_threshold = fields.Integer(string='Large Volume Threshold', help="Lower limit for large volume discount.")
    large_volume_multiplier = fields.Float(string='Large Volume Multiplier', default=1.0)
    enterprise_volume_threshold = fields.Integer(string='Enterprise Volume Threshold', help="Lower limit for enterprise discount.")
    enterprise_volume_multiplier = fields.Float(string='Enterprise Volume Multiplier', default=1.0)

    # ============================================================================
    # LOCATION-BASED PRICING MODIFIERS
    # ============================================================================
    enable_location_modifiers = fields.Boolean(string='Enable Location Modifiers')
    premium_location_multiplier = fields.Float(string='Premium Location Multiplier', default=1.2)
    standard_location_multiplier = fields.Float(string='Standard Location Multiplier', default=1.0)
    economy_location_multiplier = fields.Float(string='Economy Location Multiplier', default=0.9)

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billing_frequency_default = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Default Billing Frequency', default='monthly')
    proration_method = fields.Selection([
        ('none', 'No Proration'),
        ('daily', 'Daily'),
        ('monthly', 'Monthly')
    ], string='Proration Method', default='daily')
    minimum_monthly_charge = fields.Monetary(string='Minimum Monthly Charge')

    # ============================================================================
    # COMPUTED ANALYSIS & USAGE FIELDS
    # ============================================================================
    average_container_rate = fields.Monetary(string='Avg. Container Rate', compute='_compute_rate_analysis', store=True)
    rate_per_cubic_foot = fields.Monetary(string='Avg. Rate per CF', compute='_compute_rate_analysis', store=True)
    total_service_rate = fields.Monetary(string='Total Service Rate', compute='_compute_rate_analysis', store=True)
    customers_using_rates = fields.Integer(string='Customers Using Rates', compute='_compute_usage_stats', store=True)
    containers_at_base_rates = fields.Integer(string='Containers at Base Rates', compute='_compute_usage_stats', store=True)

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends(
        'standard_box_rate', 'legal_box_rate', 'map_box_rate', 'odd_size_rate', 'pathology_rate',
        'pickup_rate', 'delivery_rate', 'destruction_rate', 'document_retrieval_rate', 'scanning_rate', 'indexing_rate'
    )
    def _compute_rate_analysis(self):
        """Compute rate analysis metrics based on business container specifications."""
        for rate in self:
            # Weighted average based on typical usage: Type 01 (60%), Type 02 (25%), others (15% total)
            total_rate = (
                (rate.standard_box_rate or 0.0) * 0.60 +
                (rate.legal_box_rate or 0.0) * 0.25 +
                (rate.map_box_rate or 0.0) * 0.05 +
                (rate.odd_size_rate or 0.0) * 0.05 +
                (rate.pathology_rate or 0.0) * 0.05
            )
            rate.average_container_rate = total_rate

            # Weighted volume based on container specs
            total_volume = (1.2 * 0.60) + (2.4 * 0.25) + (0.875 * 0.05) + (5.0 * 0.05) + (0.042 * 0.05)
            rate.rate_per_cubic_foot = total_rate / total_volume if total_volume > 0 else 0.0

            # Sum all service rates
            rate.total_service_rate = (
                (rate.pickup_rate or 0.0) + (rate.delivery_rate or 0.0) + (rate.destruction_rate or 0.0) +
                (rate.document_retrieval_rate or 0.0) + (rate.scanning_rate or 0.0) + (rate.indexing_rate or 0.0)
            )

    @api.depends('active', 'company_id')
    def _compute_usage_stats(self):
        """Compute statistics on rate usage."""
        for rate in self:
            if not rate.active or not rate.company_id:
                rate.customers_using_rates = 0
                rate.containers_at_base_rates = 0
                continue

            # Count customers without negotiated rates
            negotiated_partners = self.env['customer.negotiated.rate'].search([
                ('state', '=', 'active'),
                ('company_id', '=', rate.company_id.id)
            ]).mapped('partner_id')

            base_rate_customers = self.env['res.partner'].search([
                ('is_company', '=', True),
                ('company_id', '=', rate.company_id.id),
                ('id', 'not in', negotiated_partners.ids)
            ])
            rate.customers_using_rates = len(base_rate_customers)

            # Count containers for customers using base rates
            rate.containers_at_base_rates = self.env['records.container'].search_count([
                ('partner_id', 'in', base_rate_customers.ids),
                ('active', '=', True)
            ])

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('effective_date', 'expiration_date')
    def _check_date_validity(self):
        """Validate date range."""
        for rate in self:
            if rate.expiration_date and rate.effective_date > rate.expiration_date:
                raise ValidationError(_('Effective date cannot be after expiration date.'))

    @api.constrains('enable_volume_tiers', 'small_volume_threshold', 'large_volume_threshold', 'enterprise_volume_threshold')
    def _check_volume_thresholds(self):
        """Validate volume thresholds are in ascending order."""
        for rate in self:
            if rate.enable_volume_tiers:
                if rate.small_volume_threshold >= rate.large_volume_threshold:
                    raise ValidationError(_('Large volume threshold must be greater than small volume threshold.'))
                if rate.large_volume_threshold >= rate.enterprise_volume_threshold:
                    raise ValidationError(_('Enterprise volume threshold must be greater than large volume threshold.'))

    @api.constrains('active', 'company_id')
    def _check_unique_active_rate(self):
        """Ensure only one active base rate per company."""
        for rate in self:
            if rate.active:
                other_active = self.search([
                    ('company_id', '=', rate.company_id.id),
                    ('active', '=', True),
                    ('id', '!=', rate.id)
                ])
                if other_active:
                    raise ValidationError(_('Only one active base rate configuration is allowed per company.'))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_container_rate(self, container_type):
        """Get the rate for a specific container type based on business rules."""
        self.ensure_one()
        base_rates = {
            'type_01': self.standard_box_rate,
            'type_02': self.legal_box_rate,
            'type_03': self.map_box_rate,
            'type_04': self.odd_size_rate,
            'type_06': self.pathology_rate,
        }
        return base_rates.get(container_type, self.standard_box_rate or 0.0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate these rates and deactivate others for the same company."""
        self.ensure_one()
        other_rates = self.search([
            ('company_id', '=', self.company_id.id),
            ('active', '=', True),
            ('id', '!=', self.id)
        ])
        other_rates.write({'active': False, 'state': 'archived'})
        self.write({'active': True, 'state': 'active'})
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Success'),
                'message': _('Base rates activated successfully.'),
                'type': 'success'
            }
        }

    def action_expire(self):
        """Expire these rates."""
        self.ensure_one()
        self.write({"expiration_date": fields.Date.today(), "active": False, "state": "archived"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {"title": _("Success"), "message": _("Base rates expired successfully."), "type": "success"},
        }

    def action_run_forecast(self):
        """Open revenue forecaster with these rates."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            # Project policy: interpolate after translation for consistency
            "name": _("Revenue Forecast - %s") % self.name,
            "res_model": "revenue.forecaster",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_base_rate_id": self.id,
                "default_forecast_period": "12_months",
            },
        }

    def action_approve_changes(self):
        """Approve rate changes (manager action)."""
        self.ensure_one()
        self.write({'state': 'active'})
        self.message_post(body=_("Rate changes approved by %s") % self.env.user.name)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Approved"),
                'message': _("Rate changes have been approved."),
                'type': 'success'
            },
        }

    def action_view_customers_using_rate(self):
        """View customers using this base rate."""
        self.ensure_one()

        # Find customers without negotiated rates
        negotiated_partners = (
            self.env["customer.negotiated.rate"]
            .search([("state", "=", "active"), ("company_id", "=", self.company_id.id)])
            .mapped("partner_id")
        )

        base_rate_customers = self.env["res.partner"].search(
            [
                ("is_company", "=", True),
                ("company_id", "=", self.company_id.id),
                ("id", "not in", negotiated_partners.ids),
            ]
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Customers Using Base Rates"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("id", "in", base_rate_customers.ids)],
            "context": {
                "search_default_is_company": 1,
            },
        }

    def action_view_negotiated_rates(self):
        """View negotiated rates for customers."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Negotiated Rates"),
            "res_model": "customer.negotiated.rate",
            "view_mode": "tree,form",
            "domain": [("company_id", "=", self.company_id.id)],
            "context": {
                "search_default_active": 1,
            },
        }

    def action_activate_rates(self):
        """Legacy method - redirect to action_activate."""
        self.ensure_one()
        return self.action_activate()

    def action_archive_rates(self):
        """Archive these rates."""
        self.ensure_one()
        self.write({'active': False, 'state': 'archived'})
        return True

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set a default name if not provided."""
        for vals in vals_list:
            if not vals.get('name'):
                company_name = None
                if vals.get('company_id'):
                    company = self.env['res.company'].browse(vals.get('company_id'))
                    company_name = company.name if company else None
                company_name = company_name or (self.env.company.name if self.env.company else '')
                vals["name"] = _("Base Rates for %s") % company_name
        return super().create(vals_list)
