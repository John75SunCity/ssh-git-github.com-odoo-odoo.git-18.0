from odoo import models, fields

class ResPartner(models.Model):
    _inherit = 'res.partner'

    document_ids = fields.One2many('records.document', 'partner_id', string='Related Documents')
    document_count = fields.Integer(compute='_compute_document_count')

    def _compute_document_count(self):
        for partner in self:
            partner.document_count = len(partner.document_ids)

    def action_view_documents(self):
        self.ensure_one()
        return {
            'name': 'Documents',
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id},
        }
