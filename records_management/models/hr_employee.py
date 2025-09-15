from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = 'hr.employee'
    _description = 'Hr Employee Records Management Extension'

    # ============================================================================
    # FIELDS
    # ============================================================================
    records_manager_id = fields.Many2one('hr.employee', string="Records Manager")
    records_department_id = fields.Many2one('records.department', string="Records Department", 
                                          help="Department this employee belongs to for records management purposes")
    
    naid_security_clearance = fields.Selection([
        ('none', 'None'),
        ('level_1', 'Level 1 (Basic)'),
        ('level_2', 'Level 2 (Confidential)'),
        ('level_3', 'Level 3 (Top Secret)')
    ], string="NAID Security Clearance", default='none')
    
    key_management_level = fields.Selection([
        ('none', 'No Key Access'),
        ('basic', 'Basic Keys'),
        ('intermediate', 'Intermediate Keys'),
        ('master', 'Master Key Access'),
        ('admin', 'Administrative Keys')
    ], string="Key Management Level", default='none', 
       help="Level of physical key management access for storage areas")

    records_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read-Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator')
    ], string="Records Access Level", default='none', tracking=True)

    records_notes = fields.Text(string='Records Management Notes')
    naid_certification_date = fields.Date(string='NAID Certification Date')
    certification_status = fields.Selection([
        ('none', 'Not Certified'),
        ('valid', 'Valid'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired')
    ], string="Certification Status", compute='_compute_certification_status', store=True)
    
    naid_certified = fields.Boolean(string="NAID Certified", compute='_compute_naid_certified', store=True,
                                   help="True if employee has valid NAID certification")

    access_description = fields.Char(string="Access Description", compute='_compute_access_description')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('naid_certification_date')
    def _compute_certification_status(self):
        """Compute NAID certification status based on the certification date."""
        for record in self:
            if record.naid_certification_date:
                days_since = (date.today() - record.naid_certification_date).days
                if days_since > 365:
                    record.certification_status = 'expired'
                elif days_since > 330:
                    record.certification_status = 'expiring'
                else:
                    record.certification_status = 'valid'
            else:
                record.certification_status = 'none'
    
    @api.depends('certification_status')
    def _compute_naid_certified(self):
        """Compute if employee is currently NAID certified."""
        for record in self:
            record.naid_certified = record.certification_status in ('valid', 'expiring')

    @api.depends('records_access_level')
    def _compute_access_description(self):
        """Compute access level description."""
        access_levels = {
            'none': 'No access to any records.',
            'read': 'Read-only access to public records.',
            'write': 'Standard read/write access to most records.',
            'admin': 'Full administrative access to all records.'
        }
        for record in self:
            record.access_description = access_levels.get(record.records_access_level, 'No access defined')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_grant_records_access(self):
        """Grant enhanced records access to the employee."""
        self.ensure_one()
        if self.records_access_level == 'none':
            self.records_access_level = "read"
        elif self.records_access_level == 'read':
            self.records_access_level = "write"
        else:
            raise UserError(_("The employee already has write or admin access."))

    def action_revoke_records_access(self):
        """Revoke all records access from the employee."""
        self.ensure_one()
        self.records_access_level = "none"
