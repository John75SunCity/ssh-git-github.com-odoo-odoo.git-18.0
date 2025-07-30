# -*- coding: utf-8 -*-
"""
Shredding Work Order
"""

from odoo import models, fields, api, _


class WorkOrderShredding(models.Model):
    """
    Shredding Work Order
    """

    _name = "work.order.shredding"
    _description = "Shredding Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Work Order Manager', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    
    # Customer relationship
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True,
                                 domain=[('is_company', '=', True)])

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
