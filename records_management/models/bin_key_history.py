# -*- coding: utf-8 -*-
from odoo import models, fields, api




class BinKeyHistory(models.Model):
    _name = "bin.key.history"
    _description = "Bin Key History"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date desc"

    name = fields.Char(string="Reference", required=True, default="New")
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key", string="Partner Bin Key", required=True)
    action_type = fields.Selection(
        [
            ("created", "Created"),
            ("assigned", "Assigned"),
            ("returned", "Returned"),
            ("lost", "Lost"),
            ("replaced", "Replaced"),
            ("deactivated", "Deactivated"),
        ],
        string="Action Type",
        required=True,
        tracking=True,
    )

    date = fields.Datetime(string="Date", default=fields.Datetime.now, required=True)
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    )
    notes = fields.Text(string="Notes")

    # Location tracking
    location_id = fields.Many2one("records.location", string="Location")

    # Control fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    active = fields.Boolean(string="Active", default=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft')
    access_level_granted = fields.Char(string='Access Level Granted')
    action_view_key_details = fields.Char(string='Action View Key Details')
    active_assignments = fields.Char(string='Active Assignments')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    additional_notes = fields.Char(string='Additional Notes')
    assigned_to = fields.Char(string='Assigned To')
    assignment_date = fields.Date(string='Assignment Date')
    assignment_location = fields.Char(string='Assignment Location')
    assignment_reason = fields.Char(string='Assignment Reason')
    authorization_reason = fields.Char(string='Authorization Reason')
    authorized_by = fields.Char(string='Authorized By')
    button_box = fields.Char(string='Button Box')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    create_uid = fields.Char(string='Create Uid')
    deposit_amount = fields.Float(string='Deposit Amount', digits=(12, 2))
    domain = fields.Char(string='Domain')
    duration_hours = fields.Char(string='Duration Hours')
    emergency = fields.Char(string='Emergency')
    expected_return_date = fields.Date(string='Expected Return Date')
    group_action_type = fields.Selection([], string='Group Action Type')  # TODO: Define selection options
    group_assigned_to = fields.Char(string='Group Assigned To')
    group_assignment_date = fields.Date(string='Group Assignment Date')
    group_authorized_by = fields.Char(string='Group Authorized By')
    group_company = fields.Char(string='Group Company')
    group_key = fields.Char(string='Group Key')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive', default=False)
    key_id = fields.Many2one('key', string='Key Id')
    last_week = fields.Char(string='Last Week')
    lost = fields.Char(string='Lost')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    overdue = fields.Char(string='Overdue')
    res_model = fields.Char(string='Res Model')
    return_date = fields.Date(string='Return Date')
    return_location = fields.Char(string='Return Location')
    returned = fields.Char(string='Returned')
    security_deposit_taken = fields.Char(string='Security Deposit Taken')
    this_month = fields.Char(string='This Month')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    witness_signature = fields.Char(string='Witness Signature'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("bin.key.history") or "New"
                    )
        return super().create(vals_list)
