# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class RecordsDestructionJob(models.Model):
    _name = 'records.destruction.job'
    _description = 'Records Destruction Job'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    destruction_date = fields.Date(string='Destruction Date', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    destruction_line_ids = fields.One2many('records.destruction.line', 'job_id', string='Destruction Lines')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.destruction.job') or _('New')
        return super(RecordsDestructionJob, self).create(vals_list)

class RecordsDestructionLine(models.Model):
    _name = 'records.destruction.line'
    _description = 'Records Destruction Line'

    job_id = fields.Many2one('records.destruction.job', string='Destruction Job', required=True, ondelete='cascade')
    box_id = fields.Many2one('records.container', string='Box')
    container_id = fields.Many2one('records.container', string='Container')
    destruction_date = fields.Date(string='Destruction Date', related='job_id.destruction_date', store=True)
    state = fields.Selection(related='job_id.state', string='Status', store=True)
    user_id = fields.Many2one(related='job_id.user_id', string='Responsible', store=True, comodel_name='res.users')
    company_id = fields.Many2one('res.company', string='Company', related='job_id.company_id', store=True, readonly=True)
