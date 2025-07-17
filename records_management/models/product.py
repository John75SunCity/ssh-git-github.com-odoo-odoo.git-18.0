# -*- coding: utf-8 -*-
from odoo import fields, models, api

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    shred_type = fields.Selection([
        ('document', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform', 'Uniform Shredding'),
    ], string='Shred Type', help='Type of shredding service for NAID-compliant categorization.')
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True, help='Flag if this product meets NAID AAA standards.')
    retention_note = fields.Text(string='Retention Note', compute='_compute_retention_note', store=True, 
                                 help='Computed note for ISO data integrity (e.g., retention policies).')

    @api.depends('detailed_type')
    def _compute_retention_note(self):
        for rec in self:
            if rec.detailed_type == 'service' and rec.shred_type:
                rec.retention_note = f"Service: {rec.shred_type}. Retain logs for 7 years per NAID standards."
            else:
                rec.retention_note = ""
