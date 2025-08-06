# -*- coding: utf-8 -*-
"""
Visitor Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class Visitor(models.Model):
    """
    Visitor Management
    Track visitors to the records management facility
    """

    _name = 'visitor'
    _description = 'Visitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, name'
    _rec_name = "name"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Visitor Name', required=True, tracking=True)
    description = fields.Text(string='Visit Details', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Host/Escort', 
                            default=lambda self: self.env.user, tracking=True)

    # ==========================================
    # VISITOR INFORMATION
    # ==========================================
    visitor_company = fields.Char(string='Visitor Company', tracking=True)
    phone = fields.Char(string='Phone Number', tracking=True)
    email = fields.Char(string='Email', tracking=True)

    # Identification
    id_type = fields.Selection([
        ('drivers_license', "Driver's License"),
        ('passport', 'Passport'),
        ('state_id', 'State ID'),
        ('company_id', 'Company ID'),
        ('other', 'Other')
    ], string='ID Type', tracking=True)
    id_number = fields.Char(string='ID Number', tracking=True)

    # ==========================================
    # VISIT DETAILS
    # ==========================================
    visit_date = fields.Date(string='Visit Date', 
                            default=fields.Date.today, required=True, tracking=True)
    check_in_time = fields.Datetime(string='Check-in Time', tracking=True)
    check_out_time = fields.Datetime(string='Check-out Time', tracking=True)

    visit_purpose = fields.Selection([
        ('customer_visit', 'Customer Visit'),
        ('audit', 'Audit'),
        ('inspection', 'Inspection'),
        ('maintenance', 'Maintenance'),
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('meeting', 'Meeting'),
        ('other', 'Other')
    ], string='Visit Purpose', required=True, tracking=True)

    # ==========================================
    # LOCATION ACCESS
    # ==========================================
    areas_accessed = fields.Text(string='Areas Accessed', tracking=True)
    escort_required = fields.Boolean(string='Escort Required', default=True, tracking=True)
    escort_assigned = fields.Many2one('res.users', string='Assigned Escort', tracking=True)

    # ==========================================
    # STATUS
    # ==========================================
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('in_facility', 'In Facility'),
        ('checked_out', 'Checked Out'),
        ('no_show', 'No Show')
    ], string='Status', default='scheduled', tracking=True, required=True)

    # ==========================================
    # RELATED RECORDS
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Related Customer',
                                domain=[('is_company', '=', True)], tracking=True)

    # ==========================================
    # SECURITY AND COMPLIANCE
    # ==========================================
    background_check = fields.Boolean(string='Background Check Required', tracking=True)
    background_check_passed = fields.Boolean(string='Background Check Passed', tracking=True)
    safety_briefing = fields.Boolean(string='Safety Briefing Given', tracking=True)

    # Badge information
    badge_number = fields.Char(string='Visitor Badge Number', tracking=True)
    badge_returned = fields.Boolean(string='Badge Returned', tracking=True)

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string='Visit Notes', tracking=True)
    security_notes = fields.Text(string='Security Notes', tracking=True)

    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_check_in(self):
        """Check in visitor"""
        self.ensure_one()
        if self.status not in ['scheduled']:
            raise ValidationError(_('Only scheduled visitors can check in'))

        self.write({
            'status': 'checked_in',
            'check_in_time': fields.Datetime.now()
        })
        self.message_post(body=_('Visitor checked in'))

    def action_enter_facility(self):
        """Mark visitor as entered facility"""
        self.ensure_one()
        if self.status != 'checked_in':
            raise ValidationError(_('Only checked-in visitors can enter facility'))

        if self.escort_required and not self.escort_assigned:
            raise ValidationError(_('Escort must be assigned for this visitor'))

        self.write({'status': 'in_facility'})
        self.message_post(body=_('Visitor entered facility'))

    def action_check_out(self):
        """Check out visitor"""
        self.ensure_one()
        if self.status not in ['checked_in', 'in_facility']:
            raise ValidationError(_('Only checked-in or in-facility visitors can check out'))

        self.write({
            'status': 'checked_out',
            'check_out_time': fields.Datetime.now()
        })
        self.message_post(body=_('Visitor checked out'))

    def action_mark_no_show(self):
        """Mark visitor as no show"""
        self.ensure_one()
        if self.status != 'scheduled':
            raise ValidationError(_('Only scheduled visitors can be marked as no show'))

        self.write({'status': 'no_show'})
        self.message_post(body=_('Visitor marked as no show'))

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('check_in_time', 'check_out_time')
    def _check_visit_times(self):
        """Validate visit times"""
        for record in self:
            if record.check_in_time and record.check_out_time:
                if record.check_out_time <= record.check_in_time:
                    raise ValidationError(_('Check-out time must be after check-in time'))
