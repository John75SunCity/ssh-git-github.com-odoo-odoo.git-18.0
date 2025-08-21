# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class RecordsRequest(models.Model):
    _name = 'records.request'
    _description = 'Records Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    request_type_id = fields.Many2one('records.request.type', string='Request Type', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    request_line_ids = fields.One2many('records.request.line', 'request_id', string='Request Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    destruction_address_id = fields.Many2one('res.partner', string='Destruction Address', related='partner_id.destruction_address_id', readonly=False)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('records.request') or _('New')
        return super(RecordsRequest, self).create(vals)
