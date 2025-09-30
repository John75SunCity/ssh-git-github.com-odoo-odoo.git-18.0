# -*- coding: utf-8 -*-
from odoo import api, fields, models

class RecordsSeries(models.Model):
    _name = 'records.series'
    _description = 'Records Series'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, tracking=True)
    code = fields.Char(string='Code', required=True, tracking=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one(comodel_name='res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    document_type_ids = fields.Many2many(
        'records.document.type',
        relation='records_series_document_type_rel',
        column1='series_id',
        column2='document_type_id',
        string='Document Types'
    )
    retention_policy_id = fields.Many2one(comodel_name='records.retention.policy', string='Retention Policy')
    document_ids = fields.One2many('records.document', 'series_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for series in self:
            series.document_count = len(series.document_ids)
