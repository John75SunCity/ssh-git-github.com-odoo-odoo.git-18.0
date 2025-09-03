# -*- coding: utf-8 -*-
"""
Discount Rule Module

Manages discount rules that can be applied to services or products based on
various criteria like quantity, volume, or specific timeframes.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DiscountRule(models.Model):
    _name = 'discount.rule'
    _description = 'Discount Rule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, priority, id'

    # ============================================================================
    # CORE & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string='Rule Name', required=True, tracking=True)
    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        ondelete="cascade",
        help="The billing configuration this rule belongs to.",
    )
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    currency_id = fields.Many2one(related='config_id.currency_id', string='Currency', store=True, comodel_name='res.currency')
    active = fields.Boolean(string='Active', default=True)
    priority = fields.Integer(string='Priority', default=10, help="Lower number indicates higher priority.")

    # ============================================================================
    # RULE CONFIGURATION
    # ============================================================================
    rule_type = fields.Selection([
        ('quantity_based', 'Quantity Based'),
        ('volume_based', 'Volume Based'),
        ('time_based', 'Time-Based Promotion')
    ], string='Rule Type', required=True, default='quantity_based', tracking=True)

    threshold = fields.Float(string='Minimum Threshold', help="Minimum quantity or volume to trigger the discount.", tracking=True)

    discount_percentage = fields.Float(string='Discount (%)', help="Percentage-based discount.", tracking=True)
    discount_amount = fields.Monetary(
        string="Fixed Discount Amount", help="Fixed amount discount.", tracking=True, currency_field="currency_id"
    )

    start_date = fields.Date(string='Start Date', help="The date from which this rule is effective.", tracking=True)
    end_date = fields.Date(string='End Date', help="The date until which this rule is effective.", tracking=True)

    # ============================================================================
    # WORKFLOW
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', default='draft', required=True, tracking=True, compute='_compute_state', store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('start_date', 'end_date', 'active')
    def _compute_state(self):
        """Compute the state of the rule based on dates and active flag."""
        today = fields.Date.today()
        for rule in self:
            if not rule.active:
                rule.state = 'draft'
            elif rule.end_date and rule.end_date < today:
                rule.state = 'expired'
            elif rule.start_date and rule.start_date > today:
                rule.state = 'draft' # Not yet active
            else:
                rule.state = 'active'

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_date', 'end_date')
    def _check_date_validity(self):
        for rule in self:
            if rule.start_date and rule.end_date and rule.start_date > rule.end_date:
                raise ValidationError(_("The start date cannot be after the end date."))

    @api.constrains('discount_percentage', 'discount_amount')
    def _check_discount_values(self):
        for rule in self:
            if rule.discount_percentage < 0 or rule.discount_percentage > 100:
                raise ValidationError(_("Discount percentage must be between 0 and 100."))
            if rule.discount_amount < 0:
                raise ValidationError(_("Discount amount cannot be negative."))
            if rule.discount_percentage > 0 and rule.discount_amount > 0:
                raise ValidationError(_("Please provide either a discount percentage or a fixed amount, not both."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the selected discount rules."""
        self.ensure_one()
        self.write({'active': True})
        self.message_post(body=_("Rule(s) activated."))

    def action_deactivate(self):
        """Deactivate the selected discount rules."""
        self.ensure_one()
        self.write({'active': False})
        self.message_post(body=_("Rule(s) deactivated."))
