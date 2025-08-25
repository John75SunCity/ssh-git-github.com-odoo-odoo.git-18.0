from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class ContainerAccessVisitor(models.Model):
    _name = 'container.access.visitor'
    _description = 'Container Access Visitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, visit_time desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Visitor Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(string='Active', default=True)

    # ============================================================================
    # VISITOR INFORMATION FIELDS
    # ============================================================================
    visitor_type = fields.Selection([
        ('employee', 'Employee'),
        ('contractor', 'Contractor'),
        ('customer', 'Customer'),
        ('vendor', 'Vendor'),
        ('other', 'Other')
    ], string='Visitor Type', required=True, tracking=True)

    company_name = fields.Char(string='Company Name')
    identification_type = fields.Selection([
        ('drivers_license', "Driver's License"),
        ('passport', 'Passport'),
        ('id_card', 'ID Card'),
        ('employee_badge', 'Employee Badge')
    ], string='Identification Type', required=True)

    identification_number = fields.Char(string='Identification Number', required=True)
    contact_phone = fields.Char(string='Phone Number')
    contact_email = fields.Char(string='Email Address')

    # ============================================================================
    # VISIT SCHEDULING FIELDS
    # ============================================================================
    visit_date = fields.Date(string='Visit Date', required=True, tracking=True, index=True)
    visit_time = fields.Datetime(string='Check-in Time', tracking=True)
    departure_time = fields.Datetime(string='Check-out Time', tracking=True)
    purpose = fields.Text(string='Purpose of Visit', required=True)

    # ============================================================================
    # AUTHORIZATION FIELDS
    # ============================================================================
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', required=True, tracking=True)
    escort_required = fields.Boolean(string='Escort Required', default=False)
    escort_id = fields.Many2one('res.users', string='Escort', tracking=True)
    access_areas = fields.Text(string='Authorized Access Areas')

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    work_order_id = fields.Many2one('container.access.work.order', string='Related Work Order')
    container_ids = fields.Many2many('records.container', string='Accessed Containers')
    access_activity_ids = fields.One2many('container.access.activity', 'visitor_id', string='Access Activities')

    # ============================================================================
    # SECURITY FIELDS
    # ============================================================================
    security_clearance = fields.Selection([
        ('basic', 'Basic'),
        ('elevated', 'Elevated'),
        ('restricted', 'Restricted'),
        ('confidential', 'Confidential')
    ], string='Security Clearance', default='basic')

    badge_number = fields.Char(string='Visitor Badge Number')
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked In'),
        ('in_progress', 'Visit In Progress'),
        ('checked_out', 'Checked Out'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, tracking=True)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    visit_duration = fields.Float(string='Visit Duration (Hours)', compute='_compute_visit_duration', store=True)

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
    @api.constrains('visit_time', 'visit_date')
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

    @api.constrains('escort_required', 'escort_id', 'status')
    def _check_escort(self):
        """Validate escort is assigned when required"""
        for record in self:
            if record.escort_required and record.status in ('checked_in', 'in_progress') and not record.escort_id:
                raise ValidationError(_('Escort must be assigned when escort is required'))
