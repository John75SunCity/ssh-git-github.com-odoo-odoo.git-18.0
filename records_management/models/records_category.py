# -*- coding: utf-8 -*-
from odoo import api, fields, models

class RecordsCategory(models.Model):
    _name = 'records.category'
    _description = 'Records Category'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'
    _order = 'complete_name'

    name = fields.Char(string='Name', required=True)
    code = fields.Char(string="Code")
    arch = fields.Text(string="Architecture")
    state = fields.Selection([("draft", "Draft"), ("active", "Active")], default="draft")
    model = fields.Char(string="Related Model")
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    parent_path = fields.Char(index=True)
    complete_name = fields.Char(
        'Complete Name', compute='_compute_complete_name',
        recursive=True, store=True)
    parent_id = fields.Many2one('records.category', string='Parent Category', index=True, ondelete='cascade')
    child_ids = fields.One2many('records.category', 'parent_id', string='Child Categories')
    document_type_ids = fields.One2many('records.document.type', 'category_id', string='Document Types')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')

    @api.depends('name', 'parent_id.complete_name')
    def _compute_complete_name(self):
        for category in self:
            if category.parent_id:
                category.complete_name = '%s / %s' % (category.parent_id.complete_name, category.name)
            else:
                category.complete_name = category.name

    @api.depends('document_type_ids')
    def _compute_document_count(self):
        for category in self:
            category.document_count = len(category.document_type_ids)
