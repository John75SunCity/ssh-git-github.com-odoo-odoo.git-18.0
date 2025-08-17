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


class RecordsStorageDepartmentUser(models.Model):
    _name = 'records.storage.department.user'
    _description = 'Storage Department User Assignment'
    _inherit = '['mail.thread', 'mail.activity.mixin']""'
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company')
    user_id = fields.Many2one('res.users')
    active = fields.Boolean()
    state = fields.Selection()
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date()
    access_level = fields.Char(string='Access Level')
    action = fields.Char(string='Action')
    action_cancel = fields.Char(string='Action Cancel')
    action_confirm = fields.Char(string='Action Confirm')
    action_done = fields.Char(string='Action Done')
    action_reset_to_draft = fields.Char(string='Action Reset To Draft')
    action_view_assignments = fields.Char(string='Action View Assignments')
    activity_ids = fields.One2many('mail.activity', string='Activities')
    assignment_count = fields.Integer(string='Assignment Count')
    assignment_info = fields.Char(string='Assignment Info')
    basic_info = fields.Char(string='Basic Info')
    button_box = fields.Char(string='Button Box')
    can_approve_requests = fields.Char(string='Can Approve Requests')
    can_edit_containers = fields.Char(string='Can Edit Containers')
    can_generate_reports = fields.Char(string='Can Generate Reports')
    can_view_containers = fields.Char(string='Can View Containers')
    company_info = fields.Char(string='Company Info')
    confirmed = fields.Boolean(string='Confirmed')
    context = fields.Char(string='Context')
    department_id = fields.Many2one('department')
    domain = fields.Char(string='Domain')
    done = fields.Char(string='Done')
    draft = fields.Char(string='Draft')
    end_date = fields.Date(string='End Date')
    group_date = fields.Date(string='Group Date')
    group_department = fields.Char(string='Group Department')
    group_role = fields.Char(string='Group Role')
    group_state = fields.Selection(string='Group State')
    group_user = fields.Char(string='Group User')
    help = fields.Char(string='Help')
    history_ids = fields.One2many('history')
    inactive = fields.Boolean(string='Inactive')
    message_follower_ids = fields.One2many('mail.followers', string='Followers')
    message_ids = fields.One2many('mail.message', string='Messages')
    my_assignments = fields.Char(string='My Assignments')
    permissions = fields.Char(string='Permissions')
    res_model = fields.Char(string='Res Model')
    role = fields.Char(string='Role')
    start_date = fields.Date(string='Start Date')
    this_month = fields.Char(string='This Month')
    type = fields.Selection(string='Type')
    view_ids = fields.One2many('view')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_assignment_count(self):
            for record in self:""
                record.assignment_count = len(record.assignment_ids)""

    def action_confirm(self):
            """Confirm the record"""
