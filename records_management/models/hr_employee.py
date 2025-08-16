# -*- coding: utf-8 -*-
from odoo import models, fields




class HrEmployee(models.Model):
    _inherit = "hr.employee"
    _description = "Hr Employee Records Management Extension"

    # Records Management specific fields (don't redefine base fields)
    records_manager_id = fields.Many2one(
        "res.users",
        string="Records Manager",
        help="User responsible for this employee's records management",
    )

    # NAID compliance fields
    naid_security_clearance = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic"),
            ("advanced", "Advanced"),
            ("certified", "Certified"),
        ],
        string="NAID Security Level",
        default="none",
        tracking=True,
    )

    # Records access permissions
    records_access_level = fields.Selection(
        [("read", "Read Only"), ("write", "Read/Write"), ("admin", "Administrator")],
        string="Records Access Level",
        default="read",
        tracking=True,
    )

    # Documentation
    records_notes = fields.Text(string="Records Management Notes")
    naid_certification_date = fields.Char(string="Naid Certification Date", help="NAID certification date")

    # Action methods
    def action_grant_records_access(self):
        """Grant enhanced records access to employee"""

        self.ensure_one()
        if self.records_access_level == "read":
            self.records_access_level = "write"

    def action_revoke_records_access(self):
        """Revoke records access from employee"""

        self.ensure_one()
        self.records_access_level = "read"
        """_summary_
        """
    @api.depends('naid_certification_date')
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
            access_levels = {
                'basic': 'Basic access to public records',
                'standard': 'Standard access to most records',
                'elevated': 'Elevated access including confidential records',
                'admin': 'Full administrative access to all records'
            }
            record.access_description = access_levels.get(record.records_access_level, 'No access defined')
