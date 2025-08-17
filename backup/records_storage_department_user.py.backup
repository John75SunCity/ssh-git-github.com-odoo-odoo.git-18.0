# -*- coding: utf-8 -*-

Storage Department User Assignment


from odoo import models, fields, api, _



class RecordsStorageDepartmentUser(models.Model):

        Storage Department User Assignment


    _name = "records.storage.department.user"
    _description = "Storage Department User Assignment"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

        # Core fields
    name = fields.Char(string="Name", required=True, tracking=True),
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company),
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user),
    active = fields.Boolean(default=True)

        # Basic state management
    state = fields.Selection([)]
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    

        # Common fields
    description = fields.Text(
    notes = fields.Text(
    date = fields.Date(default=fields.Date.today),
    access_level = fields.Char(string='Access Level'),
    action = fields.Char(string='Action'),
    action_cancel = fields.Char(string='Action Cancel'),
    action_confirm = fields.Char(string='Action Confirm'),
    action_done = fields.Char(string='Action Done'),
    action_reset_to_draft = fields.Char(string='Action Reset To Draft'),
    action_view_assignments = fields.Char(string='Action View Assignments'),
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True),
    assignment_count = fields.Integer(string='Assignment Count', compute='_compute_assignment_count', store=True),
    assignment_info = fields.Char(string='Assignment Info'),
    basic_info = fields.Char(string='Basic Info'),
    button_box = fields.Char(string='Button Box'),
    can_approve_requests = fields.Char(string='Can Approve Requests'),
    can_edit_containers = fields.Char(string='Can Edit Containers'),
    can_generate_reports = fields.Char(string='Can Generate Reports'),
    can_view_containers = fields.Char(string='Can View Containers'),
    company_info = fields.Char(string='Company Info'),
    confirmed = fields.Boolean(string='Confirmed', default=False),
    context = fields.Char(string='Context'),
    department_id = fields.Many2one('department', string='Department Id'),
    domain = fields.Char(string='Domain'),
    done = fields.Char(string='Done'),
    draft = fields.Char(string='Draft'),
    end_date = fields.Date(string='End Date'),
    group_date = fields.Date(string='Group Date'),
    group_department = fields.Char(string='Group Department'),
    group_role = fields.Char(string='Group Role'),
    group_state = fields.Selection([], string='Group State')  # TODO: Define selection options
    group_user = fields.Char(string='Group User'),
    help = fields.Char(string='Help'),
    history_ids = fields.One2many('history', 'records_storage_department_user_id', string='History Ids'),
    inactive = fields.Boolean(string='Inactive', default=False),
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True),
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True),
    my_assignments = fields.Char(string='My Assignments'),
    permissions = fields.Char(string='Permissions'),
    res_model = fields.Char(string='Res Model'),
    role = fields.Char(string='Role'),
    start_date = fields.Date(string='Start Date'),
    this_month = fields.Char(string='This Month'),
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_ids = fields.One2many('view', 'records_storage_department_user_id', string='View Ids'),
    view_mode = fields.Char(string='View Mode')

    @api.depends('assignment_ids')
    def _compute_assignment_count(self):
        for record in self:
            record.assignment_count = len(record.assignment_ids)

    def action_confirm(self):
        """Confirm the record"""

        self.ensure_one()
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""

        self.ensure_one()
        self.write({'state': 'done'})
