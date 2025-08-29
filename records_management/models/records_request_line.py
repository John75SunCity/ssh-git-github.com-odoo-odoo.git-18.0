# -*- coding: utf-8 -*-
from odoo import fields, models

class RecordsRequestLine(models.Model):
    _name = 'records.request.line'
    _description = 'Records Request Line'

    request_id = fields.Many2one('records.request', string='Request', required=True, ondelete='cascade')
    document_id = fields.Many2one('records.document', string='Document')
    box_id = fields.Many2one('records.container', string='Box')
    container_id = fields.Many2one('records.container', string='Container')
    company_id = fields.Many2one('res.company', string='Company', related='request_id.company_id', store=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='request_id.partner_id', store=True, readonly=True)
    state = fields.Selection(related='request_id.state', string='Status', store=True)
    request_type_id = fields.Many2one('records.request.type', string='Request Type', related='request_id.request_type_id', store=True, readonly=True)
