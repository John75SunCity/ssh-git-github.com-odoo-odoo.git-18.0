from datetime import date
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _name = 'hr.employee'
    _inherit = 'hr.employee'
    _description = 'Hr Employee Records Management Extension'

    # ============================================================================
    # FIELDS
    # ============================================================================
    records_manager_id = fields.Many2one('hr.employee', string="Records Manager")
    naid_security_clearance = fields.Selection([
        ('none', 'None'),
        ('level_1', 'Level 1 (Basic)'),
        ('level_2', 'Level 2 (Confidential)'),
        ('level_3', 'Level 3 (Top Secret)')
    ], string="NAID Security Clearance", default='none')
    
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


