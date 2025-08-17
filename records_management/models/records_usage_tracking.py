from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _


class RecordsUsageTracking(models.Model):
    _name = 'records.usage.tracking'
    _description = 'Records Usage Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'config_id, date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    active = fields.Boolean()
    company_id = fields.Many2one()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    config_id = fields.Many2one()
    date = fields.Date(string='Usage Date', required=True)
    service_type = fields.Selection()
    quantity = fields.Float(string='Quantity')
    unit = fields.Char(string='Unit of Measure')
    cost = fields.Monetary(string='Cost')
    currency_id = fields.Many2one()
    notes = fields.Text(string='Notes')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            """Override create to add auto-numbering"""
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name'] = self.env['ir.sequence'].next_by_code('records.usage.tracking') or _('New')
            return super().create(vals_list)

        # ============================================================================
            # BUSINESS FIELDS
        # ============================================================================
