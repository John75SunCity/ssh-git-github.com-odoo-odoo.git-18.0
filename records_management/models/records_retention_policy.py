from odoo import models, fields, api

class RecordsRetentionPolicy(models.Model):
    _name = 'records.retention.policy'
    _description = 'Document Retention Policy'

    name = fields.Char('Policy Name', required=True)
    retention_years = fields.Integer('Retention Period (Years)', required=True)
    description = fields.Text('Description')
    active = fields.Boolean(default=True)

    document_ids = fields.One2many('records.document', 'retention_policy_id', string='Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    @api.depends('document_ids')
    def _compute_document_count(self):
        for policy in self:
            policy.document_count = len(policy.document_ids)
