# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

class RecordsRetrievalWorkOrder(models.Model):
    _name = 'records.retrieval.work.order'
    _description = 'Records Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Work Order', required=True, index=True, copy=False, readonly=True,,
    default=lambda self: _('New'))
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    
    partner_id = fields.Many2one('res.partner', string='Customer',,
    required=True),
    company_id = fields.Many2one('res.company', string='Company',,
    default=lambda self: self.env.company),
    user_id = fields.Many2one('res.users', string='Assigned To',,
    default=lambda self: self.env.user)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name') = self.env['ir.sequence'].next_by_code('records.retrieval.work.order') or _('New')
        return super(RecordsRetrievalWorkOrder, self).create(vals_list)
