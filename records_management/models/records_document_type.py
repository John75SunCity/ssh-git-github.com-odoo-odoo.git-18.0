# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDocumentType(models.Model):
    _name = "records.document.type"
    _description = "Records Document Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

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

    # New Fields for Compliance and Analytics
    approval_date = fields.Date(
        "Approval Date", tracking=True, help="Date of last approval."
    )
    approval_required = fields.Boolean(
        "Approval Required",
        default=False,
        tracking=True,
        help="Is approval required for this document type?",
    )
    approved_by = fields.Many2one(
        "res.users",
        "Approved By",
        tracking=True,
        help="User who approved this document type.",
    )
    audit_readiness_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        "Audit Readiness Level",
        tracking=True,
        help="Level of audit readiness.",
    )
    audit_required = fields.Boolean(
        "Audit Required",
        default=False,
        tracking=True,
        help="Is an audit required for this document type?",
    )
    auto_classification_potential = fields.Float(
        "Auto-Classification Potential",
        digits=(3, 2),
        tracking=True,
        help="Potential for auto-classification.",
    )
    classification_accuracy_score = fields.Float(
        "Classification Accuracy Score",
        tracking=True,
        help="Accuracy score of classification.",
    )
    compliance_notes = fields.Text(
        "Compliance Notes", tracking=True, help="Notes on compliance."
    )
    compliance_risk_assessment = fields.Text(
        "Compliance Risk Assessment",
        tracking=True,
        help="Assessment of compliance risk.",
    )
    compliance_status = fields.Selection(
        [
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("under_review", "Under Review"),
        ],
        "Compliance Status",
        tracking=True,
        help="Current compliance status.",
    )
    document_count = fields.Integer(
        "Document Count",
        compute="_compute_document_count",
        store=True,
        help="Number of documents of this type.",
    )
    document_type_utilization = fields.Float(
        "Document Type Utilization",
        compute="_compute_document_type_utilization",
        store=True,
        help="Utilization of this document type.",
    )
    growth_trend_indicator = fields.Selection(
        [("up", "Up"), ("down", "Down"), ("stable", "Stable")],
        "Growth Trend",
        tracking=True,
        help="Growth trend of this document type.",
    )
    regulatory_compliance_score = fields.Float(
        "Regulatory Compliance Score",
        tracking=True,
        help="Score for regulatory compliance.",
    )
    regulatory_requirement = fields.Text(
        "Regulatory Requirement",
        tracking=True,
        help="Regulatory requirements for this document type.",
    )
    retention_compliance = fields.Float(
        "Retention Compliance",
        tracking=True,
        help="Compliance with retention policies.",
    )
    risk_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High")],
        "Risk Level",
        tracking=True,
        help="Risk level associated with this document type.",
    )
    seasonal_pattern_score = fields.Float(
        "Seasonal Pattern Score", tracking=True, help="Score for seasonal patterns."
    )
    security_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        "Security Classification",
        tracking=True,
        help="Security classification of the document type.",
    )
    type_complexity_rating = fields.Integer(
        "Type Complexity Rating",
        tracking=True,
        help="Rating of the complexity of this document type.",
    )

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    def _compute_document_count(self):
        """Computes the number of documents for this type."""
        for record in self:
            record.document_count = self.env["records.document"].search_count(
                [("document_type_id", "=", record.id)]
            )

    @api.depends("document_count", "document_type_utilization")
    def _compute_document_type_utilization(self):
        """Computes the utilization of this document type across all documents."""
        for record in self:
            total_docs = self.env["records.document"].search_count([])
            if total_docs > 0:
                record.document_type_utilization = (
                    record.document_count / total_docs
                ) * 100
            else:
                record.document_type_utilization = 0.0

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    def action_view_type_documents(self):
        """View all documents of this type."""
        self.ensure_one()

        # Create activity to track document viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Documents viewed for type: %s") % self.name,
            note=_("All documents of this type have been reviewed and analyzed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Documents of Type: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_type_id", "=", self.id)],
            "context": {
                "default_document_type_id": self.id,
                "search_default_document_type_id": self.id,
                "search_default_group_by_state": True,
            },
        }

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
