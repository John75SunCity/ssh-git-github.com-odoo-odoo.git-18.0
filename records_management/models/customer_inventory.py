from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventory(models.Model):
    _name = 'customer.inventory'
    _description = 'Customer Inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='User')
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    message_ids = fields.One2many('mail.message', string='Messages')
    activity_ids = fields.One2many('mail.activity', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', string='Followers')
    card = fields.Char(string='Card')
    help = fields.Char(string='Help')
    last_updated = fields.Char(string='Last Updated')
    partner_id = fields.Many2one('res.partner')
    res_model = fields.Char(string='Res Model')
    status = fields.Selection(string='Status')
    total_containers = fields.Char(string='Total Containers')
    total_documents = fields.Char(string='Total Documents')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_containers(self):
            for record in self:
                record.total_containers = sum(record.line_ids.mapped('amount'))


    def _compute_total_documents(self):
            for record in self:
                record.total_documents = sum(record.line_ids.mapped('amount'))

        # TODO: Add specific fields for this model:
            pass

