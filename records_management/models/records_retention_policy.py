# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class RecordsRetentionPolicy(models.Model):
    _name = "records.retention.policy"
    _description = "Records Retention Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Policy Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Policy Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Policy Owner",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # RETENTION POLICY DETAILS
    # ============================================================================

    # Retention Period
    retention_period_years = fields.Integer(
        string="Retention Period (Years)",
        required=True,
        help="Number of years to retain documents (0 = permanent)",
    )

    retention_period_months = fields.Integer(
        string="Additional Months",
        default=0,
        help="Additional months beyond years",
    )

    # Policy Type
    policy_type = fields.Selection(
        [
            ("legal", "Legal Requirement"),
            ("business", "Business Need"),
            ("regulatory", "Regulatory Compliance"),
            ("operational", "Operational"),
        ],
        string="Policy Type",
        required=True,
        tracking=True,
    )

    # Document Categories
    document_type_ids = fields.Many2many(
        "records.document.type",
        string="Applicable Document Types",
        help="Document types this policy applies to",
    )

    # Geographic Scope
    jurisdiction = fields.Selection(
        [
            ("federal", "Federal"),
            ("state", "State"),
            ("local", "Local"),
            ("international", "International"),
        ],
        string="Jurisdiction",
        default="federal",
    )

    # ============================================================================
    # DATES & VERSIONING
    # ============================================================================

    # Effective Dates
    effective_date = fields.Date(
        string="Effective Date",
        required=True,
        tracking=True,
    )

    expiration_date = fields.Date(
        string="Expiration Date",
        tracking=True,
    )

    # Version Control
    version_number = fields.Char(string="Version Number", default="1.0", tracking=True)
    version_date = fields.Date(string="Version Date", default=fields.Date.today)

    # Parent/Child Versioning
    parent_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Previous Version",
    )

    version_history_ids = fields.One2many(
        "records.policy.version",
        "policy_id",
        string="Version History",
    )

    # Review Dates
    last_review_date = fields.Date(string="Last Review Date", tracking=True)
    next_review_date = fields.Date(string="Next Review Date", tracking=True)

    # ============================================================================
    # COMPLIANCE & LEGAL
    # ============================================================================

    # Legal Requirements
    legal_citation = fields.Text(string="Legal Citation")
    regulatory_authority = fields.Char(string="Regulatory Authority")
    compliance_notes = fields.Text(string="Compliance Notes")

    # Approval Process
    requires_approval = fields.Boolean(
        string="Requires Approval",
        default=True,
        help="Whether policy changes require approval",
    )

    approved = fields.Boolean(string="Approved", default=False, tracking=True)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Date(string="Approval Date")

    # Review Requirements
    review_frequency = fields.Selection(
        [
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
            ("annually", "Annually"),
            ("biannually", "Bi-annually"),
        ],
        string="Review Frequency",
        default="annually",
    )

    # ============================================================================
    # DESTRUCTION & DISPOSAL
    # ============================================================================

    # Destruction Settings
    destruction_method = fields.Selection(
        [
            ("shredding", "Shredding"),
            ("incineration", "Incineration"),
            ("pulping", "Pulping"),
            ("digital_wipe", "Digital Wiping"),
        ],
        string="Destruction Method",
        default="shredding",
    )

    auto_destruction = fields.Boolean(
        string="Auto Destruction",
        default=False,
        help="Automatically schedule destruction when retention period expires",
    )

    destruction_approval_required = fields.Boolean(
        string="Destruction Approval Required",
        default=True,
    )

    # Exceptions
    exceptions_allowed = fields.Boolean(
        string="Exceptions Allowed",
        default=False,
        help="Allow exceptions to this retention policy",
    )

    exception_approval_required = fields.Boolean(
        string="Exception Approval Required",
        default=True,
    )

    # ============================================================================
    # ANALYTICS & METRICS
    # ============================================================================

    # Document Metrics
    document_count = fields.Integer(
        string="Documents Covered",
        compute="_compute_document_metrics",
        store=True,
    )

    documents_eligible_for_destruction = fields.Integer(
        string="Eligible for Destruction",
        compute="_compute_destruction_metrics",
        store=True,
    )

    # Compliance Metrics
    compliance_score = fields.Float(
        string="Compliance Score (%)",
        digits=(5, 2),
        compute="_compute_compliance_metrics",
        store=True,
    )

    policy_violations = fields.Integer(
        string="Policy Violations",
        compute="_compute_violation_metrics",
        store=True,
    )

    exception_count = fields.Integer(
        string="Active Exceptions",
        compute="_compute_exception_metrics",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    document_ids = fields.One2many(
        "records.document",
        "retention_policy_id",
        string="Covered Documents",
    )

    exception_ids = fields.One2many(
        "retention.policy.exception",
        "policy_id",
        string="Policy Exceptions",
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("document_ids")
    def _compute_document_metrics(self):
        """Compute document metrics for this policy"""
        for record in self:
            try:
                record.document_count = len(record.document_ids)
            except Exception:
                # Fallback if relationship doesn't exist yet
                record.document_count = 0

    @api.depends("document_ids", "retention_period_years", "retention_period_months")
    def _compute_destruction_metrics(self):
        """Compute documents eligible for destruction"""
        for record in self:
            try:
                if record.retention_period_years == 0:  # Permanent retention
                    record.documents_eligible_for_destruction = 0
                else:
                    cutoff_date = fields.Date.today() - relativedelta(
                        years=record.retention_period_years,
                        months=record.retention_period_months,
                    )
                    eligible_docs = record.document_ids.filtered(
                        lambda d: d.creation_date and d.creation_date <= cutoff_date
                    )
                    record.documents_eligible_for_destruction = len(eligible_docs)
            except Exception:
                record.documents_eligible_for_destruction = 0

    @api.depends("document_ids")
    def _compute_compliance_metrics(self):
        """Compute compliance score"""
        for record in self:
            try:
                if not record.document_ids:
                    record.compliance_score = 100.0
                else:
                    # Simple compliance calculation - can be enhanced
                    compliant_docs = record.document_ids.filtered(
                        lambda d: d.compliant_with_policy
                    )
                    record.compliance_score = (
                        len(compliant_docs) / len(record.document_ids) * 100
                    )
            except Exception:
                record.compliance_score = 100.0

    @api.depends("exception_ids")
    def _compute_violation_metrics(self):
        """Compute policy violations"""
        for record in self:
            try:
                violations = record.exception_ids.filtered(
                    lambda e: e.exception_type == "violation"
                )
                record.policy_violations = len(violations)
            except Exception:
                record.policy_violations = 0

    @api.depends("exception_ids")
    def _compute_exception_metrics(self):
        """Compute active exceptions"""
        for record in self:
            try:
                active_exceptions = record.exception_ids.filtered(
                    lambda e: e.state == "active"
                )
                record.exception_count = len(active_exceptions)
            except Exception:
                record.exception_count = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_activate_policy(self):
        """Activate the retention policy"""
        self.ensure_one()
        if not self.approved:
            raise UserError(_("Policy must be approved before activation."))

        self.write({"state": "active"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Policy Activated"),
                "message": _("Retention policy has been activated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_documents(self):
        """View documents covered by this policy"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Covered Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("retention_policy_id", "=", self.id)],
        }

    def action_view_exceptions(self):
        """View policy exceptions"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Policy Exceptions"),
            "res_model": "retention.policy.exception",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("policy_id", "=", self.id)],
        }

    def action_schedule_review(self):
        """Schedule policy review"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Review"),
            "res_model": "calendar.event",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Policy Review: {self.name}",
                "default_description": f"Scheduled review for retention policy {self.name}",
                "default_user_id": self.user_id.id,
            },
        }

    def action_compliance_report(self):
        """Generate compliance report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.retention_policy_compliance_report",
            "report_type": "qweb-pdf",
            "data": {"policy_id": self.id},
            "context": {"active_id": self.id},
        }

    def action_bulk_apply_policy(self):
        """Apply policy to multiple documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Policy to Documents"),
            "res_model": "retention.policy.bulk.apply.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_policy_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("retention_period_years", "retention_period_months")
    def _check_retention_period(self):
        """Ensure retention period is valid"""
        for record in self:
            if record.retention_period_years < 0:
                raise ValidationError(_("Retention period years cannot be negative."))
            if (
                record.retention_period_months < 0
                or record.retention_period_months > 11
            ):
                raise ValidationError(
                    _("Retention period months must be between 0 and 11.")
                )

    @api.constrains("effective_date", "expiration_date")
    def _check_date_sequence(self):
        """Ensure dates are in logical sequence"""
        for record in self:
            if record.effective_date and record.expiration_date:
                if record.expiration_date <= record.effective_date:
                    raise ValidationError(
                        _("Expiration date must be after effective date.")
                    )

    @api.constrains("version_number")
    def _check_version_format(self):
        """Ensure version number follows semantic versioning format"""
        import re

        for record in self:
            if record.version_number:
                pattern = r"^\d+\.\d+(\.\d+)?$"
                if not re.match(pattern, record.version_number):
                    raise ValidationError(
                        _(
                            "Version number must follow format: X.Y or X.Y.Z (e.g., 1.0 or 1.2.3)"
                        )
                    )

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("name"):
            vals["name"] = _("New Retention Policy")

        if not vals.get("code"):
            vals["code"] = (
                self.env["ir.sequence"].next_by_code("retention.policy") or "RP001"
            )

        # Set next review date based on frequency
        if vals.get("review_frequency") and not vals.get("next_review_date"):
            effective_date = fields.Date.from_string(
                vals.get("effective_date", fields.Date.today())
            )
            if vals["review_frequency"] == "monthly":
                vals["next_review_date"] = effective_date + relativedelta(months=1)
            elif vals["review_frequency"] == "quarterly":
                vals["next_review_date"] = effective_date + relativedelta(months=3)
            elif vals["review_frequency"] == "biannually":
                vals["next_review_date"] = effective_date + relativedelta(months=6)
            else:  # annually
                vals["next_review_date"] = effective_date + relativedelta(years=1)

        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Policy status changed from %s to %s")
                    % (old_state, new_state)
                )

        return super().write(vals)

    def name_get(self):
        """Custom name_get to show additional information"""
        result = []
        for record in self:
            name = record.name
            if record.retention_period_years is not False:
                if record.retention_period_years == 0:
                    name += " (Permanent)"
                else:
                    name += f" ({record.retention_period_years}Y"
                    if record.retention_period_months:
                        name += f"{record.retention_period_months}M"
                    name += ")"
            if record.document_count:
                name += f" [{record.document_count} docs]"
            result.append((record.id, name))
        return result
