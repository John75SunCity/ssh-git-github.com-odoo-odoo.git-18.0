from odoo import models, fields, api, _

class RecordsDocumentType(models.Model):
    _name = 'records.document.type'
    _description = 'Document Type'

    name = fields.Char('Type Name', required=True)
    description = fields.Text('Description')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company',
                                 default=lambda self: self.env.company)
