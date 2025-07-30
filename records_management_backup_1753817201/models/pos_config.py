# -*- coding: utf-8 -*-
"""
Enhanced POS Configuration for Records Management
"""

from odoo import models, fields, api, _


class PosConfig(models.Model):
    """
    Enhanced POS Configuration for Records Management
    """

    _name = "pos.performance.data"
    _description = "Enhanced POS Configuration for Records Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})


class PosConfigExtension(models.Model):
    """
    POS Configuration Extension for Records Management
    """

    _inherit = "pos.config"  # Inherit from existing pos.config model
    _description = "POS Configuration Extension for Records Management"

    # POS Module Integration Fields (for view compatibility)
    module_pos_discount = fields.Boolean(
        string='POS Discount Module',
        default=False,
        help='Enable POS discount module integration'
    )
    
    module_pos_loyalty = fields.Boolean(
        string='POS Loyalty Module',
        default=False,
        help='Enable POS loyalty module integration'
    )
    
    module_pos_mercury = fields.Boolean(
        string='POS Mercury Module',
        default=False,
        help='Enable POS mercury module integration'
    )
    
    module_pos_reprint = fields.Boolean(
        string='POS Reprint Module',
        default=False,
        help='Enable POS reprint module integration'
    )
    
    module_pos_restaurant = fields.Boolean(
        string='POS Restaurant Module',
        default=False,
        help='Enable POS restaurant module integration'
    )

    # Records Management specific fields
    records_integration_enabled = fields.Boolean(
        string='Enable Records Integration',
        default=False,
        help='Enable integration with Records Management system'
    )
    
    # Analytics fields for the view
    avg_transaction_time = fields.Float(
        string='Average Transaction Time',
        default=0.0,
        help='Average time per transaction in minutes'
    )
    
    total_transactions = fields.Integer(
        string='Total Transactions',
        default=0,
        help='Total number of transactions processed'
    )
