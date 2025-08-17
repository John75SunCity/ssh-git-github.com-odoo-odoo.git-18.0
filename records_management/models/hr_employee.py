from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class HrEmployee(models.Model):
    _description = 'Hr Employee Records Management Extension'
    _inherit = 'hr.employee'

    # ============================================================================
    # FIELDS
    # ============================================================================
    records_manager_id = fields.Many2one()
    naid_security_clearance = fields.Selection()
    records_access_level = fields.Selection()
    records_notes = fields.Text(string='Records Management Notes')
    naid_certification_date = fields.Char(string='Naid Certification Date')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_grant_records_access(self):
            """Grant enhanced records access to employee"""

            self.ensure_one()
            if self.records_access_level == "read":
                self.records_access_level = "write"


    def action_revoke_records_access(self):
            """Revoke records access from employee"""

            self.ensure_one()
            self.records_access_level = "read"
            """_summary_""""


    def _compute_certification_status(self):
            """Compute NAID certification status"""
            for record in self:
                if record.naid_certification_date:
                    from datetime import date
                    days_since = (date.today() - record.naid_certification_date).days
                    if days_since > 365:
                        record.certification_status = 'expired'
                    elif days_since > 330:
                        record.certification_status = 'expiring'
                    else:
                        record.certification_status = 'valid'
                else:
                    record.certification_status = 'none'    @api.depends('records_access_level')

    def _compute_access_description(self):
            """Compute access level description"""
            for record in self:
                access_levels = {}
                    'basic': 'Basic access to public records',
                    'standard': 'Standard access to most records',
                    'elevated': 'Elevated access including confidential records',
                    'admin': 'Full administrative access to all records'

                record.access_description = access_levels.get(record.records_access_level, 'No access defined')


