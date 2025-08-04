# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsRetentionPolicy(models.Model):
    _name = "records.retention.policy"
    _description = "Records Retention Policy"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    retention_period_years = fields.Integer(
        string="Retention Period (Years)",
        required=True,
        tracking=True,
        help="Number of years to retain records (0 = permanent retention)",
    )

    # Enhanced Retention Configuration
    retention_period_months = fields.Integer(
        string="Additional Months",
        default=0,
        tracking=True,
        help="Additional months beyond the year period",
    )
    retention_period = fields.Char(
        string="Retention Period", help="Complete retention period description"
    )
    minimum_retention_years = fields.Integer(
        string="Minimum Retention (Years)",
        default=1,
        tracking=True,
        help="Minimum required retention period",
    )
    maximum_retention_years = fields.Integer(
        string="Maximum Retention (Years)",
        tracking=True,
        help="Maximum allowed retention period (0 = no limit)",
    )
    trigger_event = fields.Selection(
        [
            ("creation", "Document Creation"),
            ("last_access", "Last Access Date"),
            ("completion", "Process Completion"),
            ("expiration", "Contract/Agreement Expiration"),
            ("custom", "Custom Trigger"),
        ],
        string="Retention Trigger",
        default="creation",
        required=True,
        tracking=True,
        help="Event that triggers the retention period",
    )

    # Legal and Compliance Configuration
    legal_citation = fields.Text(
        string="Legal Citation",
        tracking=True,
        help="Legal basis or citation for this retention policy",
    )
    regulatory_framework = fields.Selection(
        [
            ("gdpr", "GDPR (General Data Protection Regulation)"),
            ("hipaa", "HIPAA (Health Insurance Portability and Accountability Act)"),
            ("sox", "SOX (Sarbanes-Oxley Act)"),
            ("pci_dss", "PCI DSS (Payment Card Industry Data Security Standard)"),
            ("iso27001", "ISO 27001"),
            ("nist", "NIST Framework"),
            ("custom", "Custom/Other"),
        ],
        string="Regulatory Framework",
        tracking=True,
        help="Primary regulatory framework governing this policy",
    )
    jurisdiction = fields.Char(
        string="Jurisdiction",
        tracking=True,
        help="Legal jurisdiction where this policy applies",
    )

    # Destruction Configuration
    auto_destruction_enabled = fields.Boolean(
        string="Auto-Destruction Enabled",
        default=False,
        tracking=True,
        help="Enable automatic destruction when retention period expires",
    )
    grace_period_days = fields.Integer(
        string="Grace Period (Days)",
        default=30,
        tracking=True,
        help="Grace period before automatic destruction",
    )
    destruction_notification_days = fields.Integer(
        string="Destruction Notification (Days)",
        default=90,
        tracking=True,
        help="Days before destruction to send notification",
    )
    destruction_witness_required = fields.Boolean(
        string="Destruction Witness Required",
        default=False,
        tracking=True,
        help="Whether destruction witness is required",
    )
    legal_review_required = fields.Boolean(
        string="Legal Review Required",
        default=False,
        tracking=True,
        help="Whether legal review is required before destruction",
    )

    # Document Lifecycle Management
    interim_review_required = fields.Boolean(
        string="Interim Review Required",
        default=False,
        tracking=True,
        help="Require periodic review during retention period",
    )
    interim_review_frequency = fields.Selection(
        [
            ("annually", "Annually"),
            ("biannually", "Biannually"),
            ("quarterly", "Quarterly"),
            ("monthly", "Monthly"),
        ],
        string="Interim Review Frequency",
        tracking=True,
        help="Frequency of interim reviews",
    )

    # Related Records and Statistics
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
        store=True,
        help="Number of documents subject to this policy",
    )
    documents_eligible_for_destruction = fields.Integer(
        string="Eligible for Destruction",
        compute="_compute_destruction_eligible_count",
        help="Number of documents eligible for destruction",
    )
    total_storage_cost = fields.Monetary(
        string="Total Storage Cost",
        compute="_compute_total_storage_cost",
        currency_field="currency_id",
        help="Total storage cost for documents under this policy",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Policy Effectiveness Metrics
    compliance_score = fields.Float(
        string="Compliance Score (%)",
        compute="_compute_compliance_metrics",
        store=True,
        help="Overall compliance score for this policy",
    )
    policy_violations = fields.Integer(
        string="Policy Violations",
        compute="_compute_compliance_metrics",
        store=True,
        help="Number of policy violations",
    )
    last_compliance_check = fields.Datetime(
        string="Last Compliance Check",
        tracking=True,
        help="Date of last compliance verification",
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

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("document_count")
    def _compute_document_count(self):
        """Compute number of documents subject to this policy."""
        for record in self:
            record.document_count = self.env["records.document"].search_count(
                [("retention_policy_id", "=", record.id)]
            )

    @api.depends("document_count")
    def _compute_destruction_eligible_count(self):
        """Compute number of documents eligible for destruction."""
        for record in self:
            today = fields.Date.today()
            record.documents_eligible_for_destruction = self.env[
                "records.document"
            ].search_count(
                [
                    ("retention_policy_id", "=", record.id),
                    ("destruction_eligible_date", "<=", today),
                    ("legal_hold", "=", False),
                    ("destruction_approved", "=", False),
                ]
            )

    @api.depends("document_count")
    def _compute_total_storage_cost(self):
        """Compute total storage cost for documents under this policy."""
        for record in self:
            documents = self.env["records.document"].search(
                [("retention_policy_id", "=", record.id)]
            )
            total_cost = sum(doc.storage_cost_per_month or 0.0 for doc in documents)
            record.total_storage_cost = total_cost

    @api.depends("document_count")
    def _compute_compliance_metrics(self):
        """Compute compliance metrics for this policy."""
        today = fields.Date.today()

        for record in self:
            documents = self.env["records.document"].search(
                [("retention_policy_id", "=", record.id)]
            )

            if documents:
                # Calculate compliance score
                compliant_docs = documents.filtered(lambda d: d.compliance_verified)
                record.compliance_score = (len(compliant_docs) / len(documents)) * 100

                # Calculate violations (documents that should have been destroyed but weren't)
                overdue_docs = documents.filtered(
                    lambda d: d.destruction_eligible_date
                    and d.destruction_eligible_date < today
                    and not d.legal_hold
                    and not d.destruction_approved
                    and d.state != "destroyed"
                )
                record.policy_violations = len(overdue_docs)
            else:
                record.compliance_score = 100.0
                record.policy_violations = 0

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    @api.constrains(
        "retention_period_years", "minimum_retention_years", "maximum_retention_years"
    )
    def _check_retention_periods(self):
        """Validate retention period configurations."""
        for record in self:
            if record.retention_period_years < 0:
                raise ValidationError(_("Retention period years must be non-negative."))
            if record.minimum_retention_years < 0:
                raise ValidationError(
                    _("Minimum retention years must be non-negative.")
                )
            if record.maximum_retention_years and record.maximum_retention_years < 0:
                raise ValidationError(
                    _("Maximum retention years must be non-negative.")
                )
            if record.minimum_retention_years > record.retention_period_years:
                raise ValidationError(
                    _(
                        "Minimum retention period cannot exceed the standard retention period."
                    )
                )
            if (
                record.maximum_retention_years
                and record.retention_period_years > record.maximum_retention_years
            ):
                raise ValidationError(
                    _("Retention period cannot exceed the maximum retention period.")
                )

    @api.constrains("retention_period_months")
    def _check_retention_months(self):
        """Validate retention months."""
        for record in self:
            if (
                record.retention_period_months < 0
                or record.retention_period_months > 11
            ):
                raise ValidationError(
                    _("Retention period months must be between 0 and 11.")
                )

    @api.constrains("grace_period_days", "destruction_notification_days")
    def _check_notification_periods(self):
        """Validate notification and grace periods."""
        for record in self:
            if record.grace_period_days < 0:
                raise ValidationError(_("Grace period must be non-negative."))
            if record.destruction_notification_days < 0:
                raise ValidationError(
                    _("Destruction notification period must be non-negative.")
                )

    @api.onchange("auto_destruction_enabled")
    def _onchange_auto_destruction(self):
        """Update related fields when auto-destruction is enabled."""
        if not self.auto_destruction_enabled:
            self.grace_period_days = 0
            self.destruction_notification_days = 0

    @api.onchange("interim_review_required")
    def _onchange_interim_review(self):
        """Set default interim review frequency when enabled."""
        if self.interim_review_required and not self.interim_review_frequency:
            self.interim_review_frequency = "annually"

    @api.onchange("regulatory_framework")
    def _onchange_regulatory_framework(self):
        """Set default values based on regulatory framework."""
        if self.regulatory_framework == "gdpr":
            self.destruction_notification_days = 30
            self.legal_review_required = True
            self.stakeholder_notification_required = True
        elif self.regulatory_framework == "hipaa":
            self.minimum_retention_years = 6
            self.destruction_witness_required = True
            self.compliance_officer = self.env.user
        elif self.regulatory_framework == "sox":
            self.minimum_retention_years = 7
            self.legal_review_required = True
            self.version_control_enabled = True

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    def action_activate_policy(self):
        """Activate retention policy for enforcement."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot activate archived retention policy."))

        # Update state to active and notes
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nPolicy activated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create policy activation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Retention policy activated: %s") % self.name,
            note=_(
                "Retention policy has been activated and is now enforced across all applicable records."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Retention policy activated and enforced: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Policy Activated"),
                "message": _("Retention policy %s is now active and being enforced.")
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_deactivate_policy(self):
        """Deactivate retention policy to suspend enforcement."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot deactivate archived retention policy."))

        # Update state to inactive and notes
        self.write(
            {
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nPolicy deactivated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create policy deactivation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Retention policy deactivated: %s") % self.name,
            note=_(
                "Retention policy has been deactivated and enforcement is suspended."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Retention policy deactivated - enforcement suspended: %s")
            % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Policy Deactivated"),
                "message": _(
                    "Retention policy %s has been deactivated and enforcement is suspended."
                )
                % self.name,
                "type": "warning",
                "sticky": False,
            },
        }

    def action_review_policy(self):
        """Review retention policy for compliance and updates."""
        self.ensure_one()

        # Update notes with review information
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nPolicy reviewed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create policy review activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Retention policy review: %s") % self.name,
            note=_(
                "Retention policy requires comprehensive review for compliance and effectiveness."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today() + fields.timedelta(days=7),
        )

        self.message_post(
            body=_("Retention policy review initiated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Policy Review: %s") % self.name,
            "res_model": "records.retention.policy",
            "res_id": self.id,
            "view_mode": "form",
            "target": "current",
            "context": {
                "form_view_initial_mode": "edit",
                "default_state": "draft",  # For review mode
            },
        }

    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # Records Retention Policy Management Fields
    approval_status = fields.Selection(
        [("pending", "Pending"), ("approved", "Approved"), ("rejected", "Rejected")],
        default="pending",
    )
    changed_by = fields.Many2one("res.users", "Changed By")
    compliance_rate = fields.Float("Compliance Rate %", default=0.0)
    destruction_efficiency_rate = fields.Float(
        "Destruction Efficiency Rate %", default=0.0
    )
    destruction_method = fields.Selection(
        [
            ("shred", "Shred"),
            ("incinerate", "Incinerate"),
            ("pulp", "Pulp"),
            ("degauss", "Degauss"),
        ],
        default="shred",
    )
    audit_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")],
        default="annually",
    )
    compliance_framework = fields.Selection(
        [("gdpr", "GDPR"), ("hipaa", "HIPAA"), ("sox", "SOX"), ("custom", "Custom")],
        default="custom",
    )
    destruction_approval_required = fields.Boolean(
        "Destruction Approval Required", default=True
    )
    legal_hold_override = fields.Boolean("Legal Hold Override", default=False)
    policy_automation_enabled = fields.Boolean(
        "Policy Automation Enabled", default=False
    )
    policy_enforcement_level = fields.Selection(
        [("advisory", "Advisory"), ("mandatory", "Mandatory"), ("strict", "Strict")],
        default="mandatory",
    )
    policy_review_cycle = fields.Selection(
        [("annual", "Annual"), ("biennial", "Biennial"), ("triennial", "Triennial")],
        default="annual",
    )
    regulatory_compliance_verified = fields.Boolean(
        "Regulatory Compliance Verified", default=False
    )
    retention_calculation_method = fields.Selection(
        [
            ("creation_date", "Creation Date"),
            ("last_access", "Last Access"),
            ("custom", "Custom"),
        ],
        default="creation_date",
    )
    retention_extension_allowed = fields.Boolean(
        "Retention Extension Allowed", default=True
    )
    retention_monitoring_enabled = fields.Boolean(
        "Retention Monitoring Enabled", default=True
    )
    risk_assessment_completed = fields.Boolean(
        "Risk Assessment Completed", default=False
    )
    stakeholder_notification_required = fields.Boolean(
        "Stakeholder Notification Required", default=True
    )
    version_control_enabled = fields.Boolean("Version Control Enabled", default=True)
    action = fields.Selection(
        [("archive", "Archive"), ("destroy", "Destroy"), ("review", "Review")],
        string="Action",
    )
    applicable_document_type_ids = fields.Many2many(
        "records.document.type", string="Applicable Document Types"
    )
    compliance_officer = fields.Many2one("res.users", string="Compliance Officer")
    compliance_rate = fields.Float("Compliance Rate (%)", default=0.0)
    legal_reviewer = fields.Many2one("res.users", string="Legal Reviewer")
    review_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("yearly", "Yearly")],
        string="Review Frequency",
        default="yearly",
    )
    notification_enabled = fields.Boolean("Notifications Enabled", default=True)
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High")],
        string="Priority",
        default="normal",
    )

    # Records Retention Policy Management Fields

    def action_view_exceptions(self):
        """View all retention policy exceptions and violations."""
        self.ensure_one()

        # Create activity to track exception review
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Policy exceptions reviewed: %s") % self.name,
            note=_(
                "Retention policy exceptions and violations have been reviewed and addressed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Retention Policy Exceptions: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("retention_policy_id", "=", self.id),
                ("state", "in", ["exception", "violation"]),
            ],
            "context": {
                "default_retention_policy_id": self.id,
                "search_default_retention_policy_id": self.id,
                "search_default_exceptions": True,
            },
        }

    def action_view_policy_documents(self):
        """View all documents affected by this retention policy."""
        self.ensure_one()

        # Create activity to track document review
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Policy documents reviewed: %s") % self.name,
            note=_(
                "All documents subject to this retention policy have been reviewed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Documents under Policy: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("retention_policy_id", "=", self.id)],
            "context": {
                "default_retention_policy_id": self.id,
                "search_default_retention_policy_id": self.id,
                "search_default_group_by_state": True,
            },
        }

    def action_run_compliance_check(self):
        """Run comprehensive compliance check for this policy."""
        self.ensure_one()

        # Update last compliance check date
        self.write({"last_compliance_check": fields.Datetime.now()})

        # Recompute compliance metrics
        self._compute_compliance_metrics()

        # Create compliance check activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Compliance check completed: %s") % self.name,
            note=_("Compliance check completed. Score: %.1f%%, Violations: %d")
            % (self.compliance_score, self.policy_violations),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Check Complete"),
                "message": _("Compliance score: %.1f%%, Violations: %d")
                % (self.compliance_score, self.policy_violations),
                "type": "success" if self.policy_violations == 0 else "warning",
                "sticky": False,
            },
        }

    def action_schedule_destruction_run(self):
        """Schedule automatic destruction run for eligible documents."""
        self.ensure_one()

        if not self.auto_destruction_enabled:
            raise UserError(_("Auto-destruction is not enabled for this policy."))

        eligible_count = self.documents_eligible_for_destruction
        if eligible_count == 0:
            raise UserError(_("No documents are currently eligible for destruction."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Destruction Run"),
            "res_model": "destruction.schedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_retention_policy_id": self.id,
                "default_eligible_document_count": eligible_count,
                "default_auto_destruction": True,
            },
        }

    def action_export_policy_report(self):
        """Export comprehensive policy report."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_url",
            "url": f"/records/report/retention_policy/{self.id}",
            "target": "new",
        }

    def action_clone_policy(self):
        """Clone this retention policy with a new name."""
        self.ensure_one()

        # Create copy with modified name
        copy_vals = {
            "name": f"{self.name} (Copy)",
            "code": f"{self.code}_copy" if self.code else False,
            "state": "draft",
        }

        new_policy = self.copy(copy_vals)

        return {
            "type": "ir.actions.act_window",
            "name": _("Cloned Policy"),
            "res_model": "records.retention.policy",
            "res_id": new_policy.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_bulk_apply_to_documents(self):
        """Bulk apply this policy to selected documents."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Policy to Documents"),
            "res_model": "bulk.policy.application.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_retention_policy_id": self.id,
                "default_policy_name": self.name,
            },
        }

    def get_policy_statistics(self):
        """Get comprehensive statistics for this retention policy."""
        self.ensure_one()

        documents = self.env["records.document"].search(
            [("retention_policy_id", "=", self.id)]
        )

        stats = {
            "total_documents": len(documents),
            "eligible_for_destruction": self.documents_eligible_for_destruction,
            "compliance_score": self.compliance_score,
            "policy_violations": self.policy_violations,
            "documents_by_state": {},
            "monthly_destruction_trend": [],
            "storage_cost_projection": 0,
        }

        # Documents by state
        state_counts = {}
        for state in ["draft", "active", "inactive", "archived"]:
            state_counts[state] = len(
                documents.filtered(lambda d, s=state: d.state == s)
            )
        stats["documents_by_state"] = state_counts

        # Calculate storage cost projection
        monthly_cost = sum(doc.storage_cost_per_month or 0 for doc in documents)
        years_remaining = self.retention_period_years
        stats["storage_cost_projection"] = monthly_cost * 12 * years_remaining

        return stats

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values and initialize policy."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _(
                    "New Retention Policy %s"
                ) % fields.Datetime.now().strftime("%Y%m%d-%H%M%S")

            # Auto-generate code if not provided
            if not vals.get("code"):
                code_base = vals.get("name", "POLICY").upper().replace(" ", "_")[:20]
                vals["code"] = f"{code_base}_{fields.Datetime.now().strftime('%Y%m%d')}"

            # Set default retention period if not provided
            if not vals.get("retention_period_years"):
                vals["retention_period_years"] = 7  # Default 7 years

            # Set minimum retention based on regulatory framework
            if vals.get("regulatory_framework"):
                framework_defaults = {
                    "gdpr": {
                        "minimum_retention_years": 1,
                        "legal_review_required": True,
                    },
                    "hipaa": {
                        "minimum_retention_years": 6,
                        "destruction_witness_required": True,
                    },
                    "sox": {
                        "minimum_retention_years": 7,
                        "version_control_enabled": True,
                    },
                    "pci_dss": {
                        "minimum_retention_years": 3,
                        "naid_compliance_required": True,
                    },
                }
                defaults = framework_defaults.get(vals["regulatory_framework"], {})
                for key, value in defaults.items():
                    if key not in vals:
                        vals[key] = value

        records = super().create(vals_list)

        # Post-creation activities
        for record in records:
            # Create policy creation activity
            record.activity_schedule(
                "mail.mail_activity_data_done",
                summary=_("Retention policy created: %s") % record.name,
                note=_(
                    "New retention policy has been created and configured with default settings."
                ),
                user_id=record.user_id.id,
            )

            # Log policy creation
            record.message_post(
                body=_("Retention policy created with %d year retention period")
                % record.retention_period_years,
                message_type="notification",
            )

        return records

    @api.model
    def get_active_policies_summary(self):
        """Get summary of all active retention policies."""
        active_policies = self.search([("state", "=", "active")])

        summary = {
            "total_policies": len(active_policies),
            "total_documents_covered": sum(p.document_count for p in active_policies),
            "average_compliance_score": (
                sum(p.compliance_score for p in active_policies) / len(active_policies)
                if active_policies
                else 0
            ),
            "total_violations": sum(p.policy_violations for p in active_policies),
            "policies_by_framework": {},
        }

        # Group by framework
        framework_list = ["gdpr", "hipaa", "sox", "pci_dss", "custom"]
        for framework in framework_list:
            framework_policies = active_policies.filtered(
                lambda p, f=framework: p.regulatory_framework == f
            )
            summary["policies_by_framework"][framework] = len(framework_policies)

        return summary

    def name_get(self):
        """Custom name_get to show additional information."""
        result = []
        for record in self:
            name = record.name
            if record.retention_period_years:
                if record.retention_period_years == 0:
                    name += " (Permanent)"
                else:
                    name += f" ({record.retention_period_years}Y)"
            if record.document_count:
                name += f" [{record.document_count} docs]"
            result.append((record.id, name))
        return result
