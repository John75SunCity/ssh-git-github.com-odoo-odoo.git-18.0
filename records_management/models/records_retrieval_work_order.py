from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsRetrievalWorkOrder(models.Model):
    _name = 'records.retrieval.work.order'
    _description = 'Records Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Work Order', required=True, readonly=True)
    state = fields.Selection()
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='Assigned To')

    # ============================================================================
    # METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.retrieval.work.order') or _('New')
        return super().create(vals_list)

