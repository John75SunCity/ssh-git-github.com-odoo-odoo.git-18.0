# -*- coding: utf-8 -*-
"""
NAID Compliance Alert Model

Model for managing compliance alerts for NAID compliance management.
"""

from odoo import _, api, fields, models




class NaidComplianceAlert(models.Model):
    """Compliance alerts for NAID compliance management"""

    _name = "naid.compliance.alert"
    _description = "NAID Compliance Alert"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "alert_date desc, severity desc"
    _rec_name = "title"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Alert Reference",
        required=True,
        tracking=True,
        index=True,
        default="New Alert",
    )

    title = fields.Char(string="Alert Title", required=True, tracking=True,),

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # ALERT RELATIONSHIPS
    # ============================================================================

    compliance_id = fields.Many2one(
        "naid.compliance",
        string="Compliance Record",
        required=True,
        ondelete="cascade",
        tracking=True,
    )

    # ============================================================================
    # ALERT DETAILS
    # ============================================================================

    alert_date = fields.Datetime(
        string="Alert Date", required=True, default=fields.Datetime.now, tracking=True,)

    alert_type = fields.Selection(
        [
            ("certificate_expiry", "Certificate Expiry"),
            ("audit_due", "Audit Due"),
            ("non_compliance", "Non-Compliance Issue"),
            ("security_breach", "Security Breach"),
            ("equipment_failure", "Equipment Failure"),
            ("documentation_missing", "Documentation Missing"),
            ("training_overdue", "Training Overdue"),
            ("risk_escalation", "Risk Escalation"),
        ],
        string="Alert Type",
        required=True,
        tracking=True,
    )

    severity = fields.Selection(
        [("info", "Information"), ("warning", "Warning"), ("critical", "Critical")],
        string="Severity",
        required=True,
        default="warning",
        tracking=True,
    )

    description = fields.Text(string="Alert Description")

    # ============================================================================
    # STATUS MANAGEMENT
    # ============================================================================

    status = fields.Selection(
        [
            ("active", "Active"),
            ("acknowledged", "Acknowledged"),
            ("resolved", "Resolved"),
            ("dismissed", "Dismissed"),
        ],
        string="Status",
        required=True,
        default="active",
        tracking=True,
    )

    resolved_date = fields.Datetime(string="Resolved Date"),

    resolved_by_id = fields.Many2one("res.users", string="Resolved By"),

    resolution_notes = fields.Text(string="Resolution Notes")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        auto_join=True,
        groups="base.group_user",
    )

    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )

    message_ids = fields.One2many(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_acknowledge(self):
        """Acknowledge alert"""

        self.ensure_one()
        self.write({"status": "acknowledged"})
        self.message_post(body=_("Alert acknowledged by %s", self.env.user.name))

    def action_resolve(self):
        """Resolve alert"""

        self.ensure_one()
        self.write(
            {
                "status": "resolved",
                "resolved_date": fields.Datetime.now(),
                "resolved_by": self.env.user.id,
            }
        }
        self.message_post(body=_("Alert resolved by %s", self.env.user.name))

    def action_dismiss(self):
        """Dismiss alert"""

        self.ensure_one()
        self.write({"status": "dismissed"})
        self.message_post(body=_("Alert dismissed by %s", self.env.user.name))
