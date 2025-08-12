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