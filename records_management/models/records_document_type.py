# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class RecordsDocumentType(models.Model):
    """Model for document types in records management."""
    _name = 'records.document.type'
    _description = 'Record Document Type'
    _order = 'name'

    name = fields.Char(string='Type Name', required=True, translate=True)
    description = fields.Text(string='Description', translate=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        readonly=True
    )

    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        store=False
    )

    @api.depends('name')
    def _compute_document_count(self) -> None:
        for record in self:
            count = self.env['records.document'].search_count([
                ('document_type_id', '=', record.id)
            ])
            record.document_count = count

    def action_view_type_documents(self) -> dict:
        """View all documents of this type"""
        self.ensure_one()
        return {
            'name': _('Documents of Type: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': {'default_document_type_id': self.id},
        }
