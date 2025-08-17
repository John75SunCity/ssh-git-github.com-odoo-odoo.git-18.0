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
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class LocationReportWizard(models.Model):
    _name = 'location.report.wizard'
    _description = 'Location Report Wizard'
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
    action_export_csv = fields.Char(string='Action Export Csv')
    action_generate_report = fields.Char(string='Action Generate Report')
    action_print_report = fields.Char(string='Action Print Report')
    current_utilization = fields.Char(string='Current Utilization')
    include_child_locations = fields.Char(string='Include Child Locations')
    location_id = fields.Many2one('location')
    location_name = fields.Char(string='Location Name')
    report_date = fields.Date(string='Report Date')
    total_capacity = fields.Char(string='Total Capacity')
    utilization_percentage = fields.Char(string='Utilization Percentage')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_capacity(self):
            for record in self:""
                record.total_capacity = sum(record.line_ids.mapped('amount'))""
