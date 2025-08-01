# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NaidCompliance(models.Model):
    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(string="Compliance Check", required=True, tracking=True)
    sequence = fields.Integer(string="Sequence", default=10)
    policy_type = fields.Selection(
        [
            ("access_control", "Access Control"),
            ("document_handling", "Document Handling"),
            ("destruction", "Destruction Process"),
            ("employee_screening", "Employee Screening"),
            ("facility_security", "Facility Security"),
            ("equipment", "Equipment Maintenance"),
            ("audit", "Audit Requirements"),
        ],
        string="Policy Type",
        tracking=True,
    )
    description = fields.Text(string="Description")
    mandatory = fields.Boolean(string="Mandatory", default=True, tracking=True)
    automated_check = fields.Boolean(string="Automated Check", default=False)
    check_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("per_operation", "Per Operation"),
        ],
        string="Check Frequency",
    )
    implementation_notes = fields.Text(string="Implementation Notes")
    violation_consequences = fields.Text(string="Violation Consequences")
    review_frequency_months = fields.Integer(
        string="Review Frequency (Months)", default=12
    )

    # Original fields
    check_date = fields.Date(string="Check Date")
    compliance_level = fields.Selection(
        [("aaa", "AAA Certified"), ("aa", "AA Certified"), ("a", "A Certified")],
        string="NAID Level",
    )
    certificate_id = fields.Many2one("naid.certificate", string="Certificate")
    audit_results = fields.Text(string="Audit Results")
    corrective_actions = fields.Text(string="Corrective Actions")
    next_review_date = fields.Date(string="Next Review Date")
    state = fields.Selection(
        [
            ("pending", "Pending"),
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
        ],
        default="pending",
        tracking=True,
    )

    # Company field for multi-company support
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    active = fields.Boolean(string="Active", default=True)
