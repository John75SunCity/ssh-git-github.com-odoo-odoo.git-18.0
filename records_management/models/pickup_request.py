# -*- coding: utf-8 -*-
"""
Pickup Request
"""

from odoo import models, fields, api, _


class PickupRequest(models.Model):
    """
    Pickup Request
    """

    _name = "pickup.request"
    _description = "Pickup Request"
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
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')
    
    # Location tracking
    location_id = fields.Many2one("records.location", string="Pickup Location", tracking=True)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
