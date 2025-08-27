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
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer')
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='Assigned To')
    completion_date = fields.Datetime(string='Completion Date', help="Date and time when the retrieval was completed")
    delivery_method = fields.Selection([('scan', 'Scan & Email'), ('physical', 'Physical Delivery')], string='Delivery Method')

    # Link to retrieval team (for One2many in maintenance.team)
    retrieval_team_id = fields.Many2one('maintenance.team', string='Retrieval Team')

    # ============================================================================
    # METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.retrieval.work.order') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        """Auto-set completion_date when state changes to completed"""
        if 'state' in vals and vals['state'] == 'completed':
            vals['completion_date'] = fields.Datetime.now()
        return super().write(vals)

