from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import timedelta


class Visitor(models.Model):
    _name = 'visitor'
    _description = 'Visitor Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'visit_date desc, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Visitor Name", required=True, tracking=True)
    visitor_company = fields.Char(string="Visitor's Company", tracking=True)
    phone = fields.Char(string="Phone")
    email = fields.Char(string="Email")

    id_type = fields.Selection([
        ('drivers_license', "Driver's License"),
        ('passport', 'Passport'),
        ('national_id', 'National ID Card'),
        ('other', 'Other')
    ], string="ID Type", tracking=True)
    id_number = fields.Char(string="ID Number", tracking=True)

    visit_date = fields.Date(string="Visit Date", default=fields.Date.context_today, required=True)
    check_in_time = fields.Datetime(string="Check-in Time", readonly=True, copy=False)
    check_out_time = fields.Datetime(string="Check-out Time", readonly=True, copy=False)
    visit_duration = fields.Float(string="Visit Duration (Minutes)", compute='_compute_visit_duration', store=True)

    visit_purpose = fields.Selection([
        ('meeting', 'Meeting'),
        ('delivery', 'Delivery/Pickup'),
        ('maintenance', 'Maintenance/Service'),
        ('audit', 'Audit/Inspection'),
        ('interview', 'Interview'),
        ('other', 'Other')
    ], string="Purpose of Visit", required=True)
    areas_accessed = fields.Text(string="Areas Accessed", help="List all secured areas the visitor was granted access to.")

    escort_required = fields.Boolean(string="Escort Required", default=True)
    escort_assigned_id = fields.Many2one('res.users', string="Assigned Escort")

    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('checked_in', 'Checked-In'),
        ('checked_out', 'Checked-Out'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='scheduled', required=True, tracking=True)

    partner_id = fields.Many2one('res.partner', string="Related Customer/Vendor")

    background_check_passed = fields.Boolean(string="Background Check Passed")
    safety_briefing_completed = fields.Boolean(string="Safety Briefing Completed")
    badge_number = fields.Char(string="Badge Number")
    badge_returned = fields.Boolean(string="Badge Returned")

    naid_compliance_verified = fields.Boolean(string="NAID Compliance Verified", help="Check if all NAID compliance steps were followed for this visit.")

    notes = fields.Text(string="General Notes")
    security_notes = fields.Text(string="Security Notes", groups="records_management.group_records_manager")

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('check_in_time', 'check_out_time')
    def _compute_visit_duration(self):
        for record in self:
            if record.check_in_time and record.check_out_time:
                duration = record.check_out_time - record.check_in_time
                record.visit_duration = duration.total_seconds() / 60
            else:
                record.visit_duration = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_check_in(self):
        self.ensure_one()
        if self.status != 'scheduled':
            raise UserError(_("Only scheduled visitors can be checked in."))
        self.write({
            'status': 'checked_in',
            'check_in_time': fields.Datetime.now()
        })
        self.message_post(body=_("Visitor checked in."))

    def action_check_out(self):
        self.ensure_one()
        if self.status != 'checked_in':
            raise UserError(_("Only checked-in visitors can be checked out."))
        self.write({
            'status': 'checked_out',
            'check_out_time': fields.Datetime.now()
        })
        self.message_post(body=_("Visitor checked out."))

    def action_cancel(self):
        self.write({'status': 'cancelled'})
        self.message_post(body=_("Visit has been cancelled."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def _create_audit_log(self, event_type, details):
        """
        Placeholder for creating a detailed audit log entry in a separate
        NAID compliance audit model.
        """
        # In a real implementation, this would create a record in 'naid.audit.log'
        # self.env['naid.audit.log'].create({...})
        pass
