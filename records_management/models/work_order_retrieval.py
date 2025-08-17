from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class WorkOrderRetrieval(models.Model):
    _name = 'work.order.retrieval'
    _description = 'Work Order Retrieval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Work Order', required=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company')
    state = fields.Selection()
    partner_id = fields.Many2one('res.partner', string='Customer')
    user_id = fields.Many2one('res.users', string='Assigned To')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code('work.order.retrieval') or _('New')
            return super(WorkOrderRetrieval, self).create(vals_list)

