# -*- coding: utf-8 -*-
"""
Destruction Item
"""

from odoo import models, fields, api, _


class DestructionItem(models.Model):
    """
    Destruction Item
    """

    _name = "destruction.item"
    _description = "Destruction Item"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Relationships
    shredding_service_id = fields.Many2one('shred.svc', string='Shredding Service')
    destruction_record_id = fields.Many2one('naid.destruction.record', string='Destruction Record')

    # Item details
    item_type = fields.Selection([
        ('box', 'Records Box'),
        ('media', 'Digital Media'),
        ('equipment', 'IT Equipment'),
        ('documents', 'Loose Documents')
    ], string='Item Type', required=True)
    
    quantity = fields.Integer(string='Quantity', default=1)
    weight = fields.Float(string='Weight (lbs)')
    barcode = fields.Char(string='Barcode/Serial Number')

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
