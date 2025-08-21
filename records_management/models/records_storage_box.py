# -*- coding: utf-8 -*-
from odoo import api, fields, models, _

class RecordsStorageBox(models.Model):
    _name = 'records.storage.box'
    _description = 'Records Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Name', required=True, copy=False, readonly=True, index=True, default=lambda self: _('New'))
    box_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large'),
    ], string='Box Size', required=True, tracking=True)
    location_id = fields.Many2one('stock.location', string='Location', required=True, tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_use', 'In Use'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed'),
    ], string='Status', default='draft', tracking=True)
    document_ids = fields.One2many('records.document', 'storage_box_id', string='Documents')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)

    @api.depends('document_ids')
    def _compute_document_count(self):
        for box in self:
            box.document_count = len(box.document_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('records.storage.box') or _('New')
        return super(RecordsStorageBox, self).create(vals)
