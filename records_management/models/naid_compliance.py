# -*- coding: utf-8 -*-
from odoo import models, fields, api


class NaidCompliance(models.Model):
    _name = "naid.compliance"
    _description = "NAID Compliance Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Compliance Check", required=True, tracking=True)
    check_date = fields.Date(string="Check Date", required=True)
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
    )

    # Essential NAID Compliance Fields (from view analysis)
    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("pending", "Pending Certification"),
            ("expired", "Expired"),
        ],
        string="NAID Certification Level",
        required=True,
        tracking=True,
    )

    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("pending_review", "Pending Review"),
            ("remediation_required", "Remediation Required"),
            ("under_audit", "Under Audit"),
        ],
        string="Compliance Status",
        default="pending_review",
        tracking=True,
    )

    # Certification Dates
    certification_date = fields.Date(string="Certification Date", tracking=True)
    expiry_date = fields.Date(string="Expiry Date", tracking=True)

    # Audit Management
    audit_required = fields.Boolean(string="Audit Required", default=True)
    audit_date = fields.Date(string="Audit Date")
    audit_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("semi_annual", "Semi-Annual"),
            ("annual", "Annual"),
        ],
        string="Audit Frequency",
        default="annual",
    )

    # Certificate Management
    certificate_valid = fields.Boolean(
        string="Certificate Valid", compute="_compute_certificate_status"
    )
    certificate_number = fields.Char(string="Certificate Number")

    # Facility Information
    facility_name = fields.Char(string="Facility Name", required=True)
    facility_address = fields.Text(string="Facility Address")
    facility_contact = fields.Many2one("res.partner", string="Facility Contact")

    # Compliance Requirements
    physical_security_verified = fields.Boolean(
        string="Physical Security Verified", default=False
    )
    access_control_verified = fields.Boolean(
        string="Access Control Verified", default=False
    )
    personnel_screening_verified = fields.Boolean(
        string="Personnel Screening Verified", default=False
    )
    destruction_process_verified = fields.Boolean(
        string="Destruction Process Verified", default=False
    )

    # Documentation
    compliance_documentation = fields.Text(string="Compliance Documentation")
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )

    # Reporting and Analytics
    compliance_score = fields.Float(
        string="Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_score",
    )
    risk_level = fields.Selection(
        [
            ("low", "Low Risk"),
            ("medium", "Medium Risk"),
            ("high", "High Risk"),
            ("critical", "Critical Risk"),
        ],
        string="Risk Level",
        compute="_compute_risk_level",
    )

    # Audit History
    audit_history_ids = fields.One2many(
        "naid.audit.log", "compliance_id", string="Audit History"
    )
    last_audit_date = fields.Date(
        string="Last Audit Date", compute="_compute_last_audit"
    )

    # Reminder and Notifications
    audit_reminder = fields.Date(string="Audit Reminder Date")
    notification_sent = fields.Boolean(string="Notification Sent", default=False)

    # Related Records
    employee_ids = fields.Many2many("hr.employee", string="Certified Employees")
    equipment_ids = fields.Many2many(
        "maintenance.equipment", string="Certified Equipment"
    )

    @api.depends("certification_date", "expiry_date")
    def _compute_certificate_status(self):
        """Compute if certificate is valid"""
        for record in self:
            if record.certification_date and record.expiry_date:
                today = fields.Date.today()
                record.certificate_valid = record.expiry_date >= today
            else:
                record.certificate_valid = False

    @api.depends(
        "physical_security_verified",
        "access_control_verified",
        "personnel_screening_verified",
        "destruction_process_verified",
    )
    def _compute_compliance_score(self):
        """Compute compliance score based on verification checks"""
        for record in self:
            checks = [
                record.physical_security_verified,
                record.access_control_verified,
                record.personnel_screening_verified,
                record.destruction_process_verified,
            ]
            score = (sum(checks) / len(checks)) * 100 if checks else 0
            record.compliance_score = score

    @api.depends("compliance_score", "certificate_valid")
    def _compute_risk_level(self):
        """Compute risk level based on compliance score and certificate status"""
        for record in self:
            if not record.certificate_valid:
                record.risk_level = "critical"
            elif record.compliance_score < 50:
                record.risk_level = "high"
            elif record.compliance_score < 75:
                record.risk_level = "medium"
            else:
                record.risk_level = "low"

    @api.depends("audit_history_ids")
    def _compute_last_audit(self):
        """Compute last audit date from audit history"""
        for record in self:
            if record.audit_history_ids:
                record.last_audit_date = max(
                    record.audit_history_ids.mapped("audit_date")
                )
            else:
                record.last_audit_date = False

    # Additional fields for comprehensive compliance management
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Compliance Manager", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)

    # =============================================================================
    # NAID COMPLIANCE ACTION METHODS
    # =============================================================================

    def action_compliance_report(self):
        """Generate compliance report."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.naid_compliance_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_conduct_audit(self):
        """Conduct NAID compliance audit."""
        self.ensure_one()
        # Create audit activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"NAID Compliance Audit: {self.name}",
            note="Conduct comprehensive NAID compliance audit including documentation review, facility inspection, and process verification.",
            user_id=self.user_id.id,
        )
        self.message_post(body="NAID compliance audit scheduled and initiated.")
        return True

    def action_download_certificate(self):
        """Download NAID certificate."""
        self.ensure_one()
        if not self.certificate_id:
            from odoo.exceptions import UserError

            raise UserError("No certificate associated with this compliance record.")

        return {
            "type": "ir.actions.act_url",
            "url": f"/web/content/naid.certificate/{self.certificate_id.id}/certificate_file?download=true",
            "target": "new",
        }

    def action_generate_certificate(self):
        """Generate new NAID certificate."""
        self.ensure_one()
        # Create new certificate record
        certificate_vals = {
            "name": f"NAID Certificate - {self.name}",
            "compliance_id": self.id,
            "issue_date": fields.Date.today(),
            "expiry_date": fields.Date.today().replace(
                year=fields.Date.today().year + 1
            ),
            "certification_level": self.compliance_level,
        }

        certificate = self.env["naid.certificate"].create(certificate_vals)
        self.certificate_id = certificate.id
        self.message_post(body=f"New NAID certificate generated: {certificate.name}")

        return {
            "type": "ir.actions.act_window",
            "name": "Generated Certificate",
            "res_model": "naid.certificate",
            "res_id": certificate.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_renew_certificate(self):
        """Renew existing NAID certificate."""
        self.ensure_one()
        if not self.certificate_id:
            from odoo.exceptions import UserError

            raise UserError(
                "No certificate to renew. Please generate a new certificate first."
            )

        # Update certificate expiry date
        new_expiry = fields.Date.today().replace(year=fields.Date.today().year + 1)
        self.certificate_id.write(
            {
                "expiry_date": new_expiry,
                "renewal_date": fields.Date.today(),
            }
        )

        self.message_post(body=f"NAID certificate renewed until {new_expiry}")
        return True

    def action_schedule_audit(self):
        """Schedule next compliance audit."""
        self.ensure_one()

        # Calculate next audit date (typically annual)
        next_audit_date = fields.Date.today().replace(year=fields.Date.today().year + 1)

        # Create new compliance record for next audit
        next_audit_vals = {
            "name": f"Scheduled Audit - {fields.Date.today().year + 1}",
            "check_date": next_audit_date,
            "compliance_level": self.compliance_level,
            "state": "pending",
        }

        next_audit = self.create(next_audit_vals)

        # Schedule activity for next audit
        next_audit.activity_schedule(
            "mail.mail_activity_data_todo",
            date_deadline=next_audit_date,
            summary="Annual NAID Compliance Audit Due",
            note="Annual NAID compliance audit is due. Please conduct comprehensive review and documentation.",
            user_id=self.user_id.id,
        )

        self.message_post(body=f"Next NAID audit scheduled for {next_audit_date}")
        return True

    def action_view_audit_details(self):
        """View detailed audit information."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Audit Details",
            "res_model": "naid.compliance",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_audit_history(self):
        """View compliance audit history."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "NAID Audit History",
            "res_model": "naid.compliance",
            "view_mode": "tree,form",
            "domain": [("company_id", "=", self.company_id.id)],
            "context": {"search_default_company_id": self.company_id.id},
        }

    def action_view_certificates(self):
        """View all NAID certificates."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "NAID Certificates",
            "res_model": "naid.certificate",
            "view_mode": "tree,form",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "default_compliance_id": self.id,
                "search_default_compliance_id": self.id,
            },
        }

    def action_view_destruction_records(self):
        """View destruction records related to this compliance."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Destruction Records",
            "res_model": "naid.destruction.record",
            "view_mode": "tree,form",
            "domain": [("compliance_id", "=", self.id)],
            "context": {
                "default_compliance_id": self.id,
                "search_default_compliance_id": self.id,
            },
        }
