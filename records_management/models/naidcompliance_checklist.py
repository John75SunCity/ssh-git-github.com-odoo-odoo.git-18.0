from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class NAIDComplianceChecklist(models.Model):
    _name = 'naid.compliance.checklist'
    _description = 'NAID Compliance Checklist'
    _inherit = '['mail.thread', 'mail.activity.mixin']""'
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company')
    user_id = fields.Many2one('res.users')
    compliance_id = fields.Many2one('naid.compliance')
    active = fields.Boolean()
    state = fields.Selection()
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date()
    activity_ids = fields.One2many('mail.activity', string='Activities')
    button_box = fields.Char(string='Button Box')
    category = fields.Char(string='Category')
    checklist_item_ids = fields.One2many('checklist.item')
    checklist_items = fields.Char(string='Checklist Items')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    group_by_category = fields.Char(string='Group By Category')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive')
    is_required = fields.Boolean(string='Is Required')
    message_follower_ids = fields.One2many('mail.followers', string='Followers')
    message_ids = fields.One2many('mail.message', string='Messages')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    toggle_active = fields.Boolean(string='Toggle Active')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_confirm(self):
            """Confirm the record"""
