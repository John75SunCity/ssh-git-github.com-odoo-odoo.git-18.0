# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class VisitorPosWizard(models.TransientModel):
    _name = 'visitor.pos.wizard'
    _description = 'Wizard to Link POS Transaction to Visitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Original fields
    visitor_id = fields.Many2one('frontdesk.visitor', string='Visitor', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Transaction', domain="[('partner_id', '=', partner_id)]")
    service_type = fields.Selection([
        ('document_shred', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform_shred', 'Uniform Shredding'),
    ], string='Service Type', help='Suggested based on visitor notes.')
    notes = fields.Text(string='Additional Notes')

    # Enhanced wizard fields - all 113 missing fields
    name = fields.Char(string='Service Name', required=True, default='Walk-in Service')
    visitor_name = fields.Char(string='Visitor Name', related='visitor_id.name', readonly=True)
    visitor_email = fields.Char(string='Visitor Email', related='visitor_id.email', readonly=True)
    visitor_phone = fields.Char(string='Visitor Phone', related='visitor_id.phone', readonly=True)
    
    # Mail tracking fields (explicit declaration for view compatibility)