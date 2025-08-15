# -*- coding: utf-8 -*-
"""
Container Access Visitor Model

Track visitors accessing container storage areas.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerAccessVisitor(models.Model):
    """Container Access Visitor"""

    _name = "container.access.visitor"
    _description = "Container Access Visitor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "visit_date desc, visit_time desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Visitor Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the visitor"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this visitor record"
    )

    # ============================================================================
    # VISITOR INFORMATION
    # ============================================================================
    visitor_type = fields.Selection([
        ('customer', 'Customer'),
        ('employee', 'Employee'),
        ('contractor', 'Contractor'),
        ('auditor', 'Auditor'),
        ('inspector', 'Inspector'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other')
    ], string='Visitor Type', required=True, tracking=True)

    company_name = fields.Char(
        string="Company/Organization",
        help="Company or organization the visitor represents"
    )

    identification_type = fields.Selection([
        ('drivers_license', "Driver's License"),
        ('passport', 'Passport'),
        ('employee_id', 'Employee ID'),
        ('government_id', 'Government ID'),
        ('other', 'Other')
    ], string='ID Type')

    identification_number = fields.Char(
        string="ID Number",
        help="Identification number"
    )

    contact_phone = fields.Char(
        string="Phone Number",
        help="Contact phone number"
    )

    contact_email = fields.Char(
        string="Email",
        help="Contact email address"
    )

    # ============================================================================
    # VISIT DETAILS
    # ============================================================================
    visit_date = fields.Date(
        string="Visit Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date of the visit"
    )

    visit_time = fields.Datetime(
        string="Visit Time",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Time of arrival"
    )

    departure_time = fields.Datetime(
        string="Departure Time",
        tracking=True,
        help="Time of departure"
    )

    purpose = fields.Text(
        string="Purpose of Visit",
        required=True,
        help="Purpose of the visit"
    )

    # ============================================================================
    # ACCESS CONTROL
    # ============================================================================
    authorized_by_id = fields.Many2one(
        "res.users",
        string="Authorized By",
        required=True,
        tracking=True,
        help="Staff member who authorized the visit"
    )

    escort_required = fields.Boolean(
        string="Escort Required",
        default=True,
        help="Whether visitor must be escorted"
    )

    escort_id = fields.Many2one(
        "hr.employee",
        string="Escort",
        help="Employee escorting the visitor"
    )

    access_areas = fields.Text(
        string="Authorized Areas",
        help="Areas the visitor is authorized to access"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Customer",
        help="Customer this visit is related to"
    )

    work_order_id = fields.Many2one(
        "container.access.work.order",
        string="Work Order",
        help="Related container access work order"
    )

    container_ids = fields.Many2many(
        "records.container",
        string="Accessed Containers",
        help="Containers accessed during the visit"
    )

    access_activity_ids = fields.One2many(
        "container.access.activity",
        "visitor_id",
        string="Access Activities",
        help="Activities performed during the visit"
    )

    # ============================================================================
    # SECURITY FIELDS
    # ============================================================================
    security_clearance = fields.Selection([
        ('none', 'None'),
        ('basic', 'Basic'),
        ('standard', 'Standard'),
        ('high', 'High'),
        ('top_secret', 'Top Secret')
    ], string='Security Clearance', default='none')

    badge_number = fields.Char(
        string="Badge Number",
        help="Visitor badge number assigned"
    )

    # ============================================================================
    # STATUS
    # ============================================================================
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'In Progress'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, tracking=True)

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('visit_time', 'departure_time')
    def _compute_visit_duration(self):
        """Calculate visit duration in hours"""
        for record in self:
            if record.visit_time and record.departure_time:
                delta = record.departure_time - record.visit_time
                record.visit_duration = delta.total_seconds() / 3600
            else:
                record.visit_duration = 0.0

    visit_duration = fields.Float(
        string="Visit Duration (Hours)",
        compute='_compute_visit_duration',
        help="Duration of the visit in hours"
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_check_in(self):
        """Check in the visitor"""
        self.ensure_one()
        if self.status != 'scheduled':
            raise UserError(_('Can only check in scheduled visitors'))
        
        self.write({
            'status': 'checked_in',
            'visit_time': fields.Datetime.now()
        })
        self.message_post(body=_('Visitor checked in'))

    def action_start_visit(self):
        """Start the visit"""
        self.ensure_one()
        if self.status != 'checked_in':
            raise UserError(_('Visitor must be checked in first'))
        
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Visit started'))

    def action_check_out(self):
        """Check out the visitor"""
        self.ensure_one()
        if self.status not in ('checked_in', 'in_progress'):
            raise UserError(_('Can only check out active visitors'))
        
        self.write({
            'status': 'checked_out',
            'departure_time': fields.Datetime.now()
        })
        self.message_post(body=_('Visitor checked out'))

    def action_cancel_visit(self):
        """Cancel the visit"""
        self.ensure_one()
        if self.status in ('checked_out', 'cancelled'):
            raise UserError(_('Cannot cancel completed or already cancelled visits'))
        
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Visit cancelled'))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('visit_date', 'visit_time')
    def _check_visit_date(self):
        """Validate visit date and time"""
        for record in self:
            if record.visit_time and record.visit_time.date() != record.visit_date:
                raise ValidationError(_('Visit time must be on the same date as visit date'))

    @api.constrains('departure_time', 'visit_time')
    def _check_departure_time(self):
        """Validate departure time is after visit time"""
        for record in self:
            if record.departure_time and record.visit_time:
                if record.departure_time <= record.visit_time:
                    raise ValidationError(_('Departure time must be after visit time'))

    @api.constrains('escort_required', 'escort_id')
    def _check_escort(self):
        """Validate escort is assigned when required"""
        for record in self:
            if record.escort_required and record.status in ('checked_in', 'in_progress') and not record.escort_id:
                raise ValidationError(_('Escort must be assigned when escort is required'))
