# -*- coding: utf-8 -*-
"""
Customer Category Module

Defines categories for customers to apply specific billing models,
service level agreements (SLAs), and priority levels.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerCategory(models.Model):
    """
    Represents a category for customers, allowing for grouped settings
    and configurations.
    """
    _name = 'customer.category'
    _description = 'Customer Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Category Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    # Additional contact summary fields referenced in views (functional, stored)
    email = fields.Char(string='Primary Email', help="Representative email shown in category overviews")
    phone = fields.Char(string='Primary Phone', help="Representative phone displayed in category views")
    is_company = fields.Boolean(string='Is Company', help="Flag used in views for filtering / display consistency")

    # ============================================================================
    # CONFIGURATION
    # ============================================================================
    default_billing_model = fields.Selection([
        ('standard', 'Standard'),
        ('prepaid', 'Prepaid'),
        ('contract', 'Contract-Based')
    ], string='Default Billing Model', default='standard', tracking=True)

    priority_level = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string='Default Priority', default='0', tracking=True)

    sla_hours = fields.Integer(
        string='SLA Response Hours',
        help="Default Service Level Agreement response time in hours for customers in this category."
    )

    # ============================================================================
    # RELATED RECORDS
    # ============================================================================
    partner_ids = fields.One2many('res.partner', 'category_id', string='Customers')
    customer_count = fields.Integer(string='Customer Count', compute='_compute_customer_count', store=True)
    total_active_customers = fields.Integer(string='Active Customers', compute='_compute_customer_count', store=True,
                                           help="Number of active customers in this category")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('partner_ids')
    def _compute_customer_count(self):
        """Calculates the number of customers in this category."""
        for record in self:
            record.customer_count = len(record.partner_ids)
            record.total_active_customers = len(record.partner_ids.filtered(lambda p: p.active))

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('sla_hours')
    def _check_sla_hours(self):
        """Ensures that SLA hours are not negative."""
        for record in self:
            if record.sla_hours < 0:
                raise ValidationError(_("SLA Response Hours cannot be negative."))
