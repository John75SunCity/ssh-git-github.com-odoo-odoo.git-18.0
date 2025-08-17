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
from odoo import models, fields""


class BinKey(models.Model):
    _name = 'bin.key'
    _description = 'Bin Access Key'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    assigned_to_id = fields.Many2one('res.partner')
    current_holder_id = fields.Many2one('res.users')
    assigned_to_id = fields.Many2one('res.partner')
    current_holder_id = fields.Many2one('res.users')
    name = fields.Char(required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    partner_id = fields.Many2one()
    state = fields.Selection()
    currency_id = fields.Many2one()
    key_code = fields.Char()
    description = fields.Text()
    key_type = fields.Selection()
    access_level = fields.Selection()
    valid_from = fields.Date()
    valid_to = fields.Date(string='Valid To')
    assigned_to_id = fields.Many2one('res.partner')
    current_holder_id = fields.Many2one('res.users')
    unlock_service_ids = fields.One2many()
    bin_ids = fields.Many2many('shred.bin')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    key_number = fields.Char(string='Key Number', required=True)
    bin_location = fields.Char(string='Bin Location')
    assigned_to = fields.Many2one('res.partner')
    issue_date = fields.Date(string='Issue Date')
    return_date = fields.Date(string='Return Date')
    security_deposit_required = fields.Boolean(string='Security Deposit Required')
    security_deposit_amount = fields.Monetary(string='Security Deposit Amount')
    emergency_access = fields.Boolean(string='Emergency Access')
    last_maintenance_date = fields.Date(string='Last Maintenance Date')
    next_maintenance_due = fields.Date(string='Next Maintenance Due')
    action_assign_key = fields.Char(string='Action Assign Key')
    action_mark_lost = fields.Char(string='Action Mark Lost')
    action_reactivate_key = fields.Char(string='Action Reactivate Key')
    action_retire_key = fields.Char(string='Action Retire Key')
    action_return_key = fields.Char(string='Action Return Key')
    action_view_management_records = fields.Char(string='Action View Management Records')
    action_view_unlock_services = fields.Char(string='Action View Unlock Services')
    assigned = fields.Char(string='Assigned')
    assigned_date = fields.Date(string='Assigned Date')
    assignment_date = fields.Date(string='Assignment Date')
    assignment_reason = fields.Char(string='Assignment Reason')
    available = fields.Char(string='Available')
    bin_position = fields.Char(string='Bin Position')
    bin_rack = fields.Char(string='Bin Rack')
    bin_shelf = fields.Char(string='Bin Shelf')
    button_box = fields.Char(string='Button Box')
    charge_amount = fields.Float(string='Charge Amount')
    context = fields.Char(string='Context')
    current_holder = fields.Char(string='Current Holder')
    customer_id = fields.Many2one('res.partner', string='Customer Id')
    domain = fields.Char()
