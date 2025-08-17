from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api


class BinKeyHistory(models.Model):
    _name = 'bin.key.history'
    _description = 'Bin Key History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='User')
    active = fields.Boolean(string='Active')
    partner_bin_key_id = fields.Many2one()
    action_type = fields.Selection()
    date = fields.Datetime(string='Date', required=True)
    notes = fields.Text(string='Notes')
    location_id = fields.Many2one('records.location', string='Location')
    partner_id = fields.Many2one()
    state = fields.Selection()
    access_level_granted = fields.Char(string='Access Level Granted')
    assigned_to = fields.Char(string='Assigned To')
    assignment_date = fields.Date(string='Assignment Date')
    assignment_location = fields.Char(string='Assignment Location')
    assignment_reason = fields.Char(string='Assignment Reason')
    authorization_reason = fields.Char(string='Authorization Reason')
    authorized_by = fields.Char(string='Authorized By')
    additional_notes = fields.Text(string='Additional Notes')
    deposit_amount = fields.Float(string='Deposit Amount')
    expected_return_date = fields.Date(string='Expected Return Date')
    return_date = fields.Date(string='Return Date')
    return_location = fields.Char(string='Return Location')
    security_deposit_taken = fields.Boolean(string='Security Deposit Taken')
    duration_hours = fields.Float(string='Duration Hours')
    emergency = fields.Boolean(string='Emergency')
    witness_signature = fields.Char(string='Witness Signature')
    key_id = fields.Many2one('bin.key')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("bin.key.history") or "New"

            return super().create(vals_list)


    def action_activate(self):
            """Activate the history record"""
            self.ensure_one()
            self.write({'state': 'active'})


    def action_deactivate(self):
            """Deactivate the history record"""
            self.ensure_one()
            self.write({'state': 'inactive'})


    def action_archive(self):
            """Archive the history record"""
            self.ensure_one()
            self.write({'state': 'archived'})

