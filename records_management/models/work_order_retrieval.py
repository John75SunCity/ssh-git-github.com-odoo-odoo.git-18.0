# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class WorkOrderRetrieval(models.Model):
    _name = 'work.order.retrieval'
    _description = 'Work Order Retrieval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Work Order', required=True, index=True, copy=False, readonly=True, default=lambda self: _('New'))
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned To', default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.retrieval') or _('New')
        return super(WorkOrderRetrieval, self).create(vals_list)
