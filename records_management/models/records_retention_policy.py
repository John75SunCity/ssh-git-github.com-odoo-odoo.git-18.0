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
    code = fields.Char(string="Code", index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    retention_period = fields.Integer(
        string="Retention Period (Years)", help="Number of years to retain records"
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

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

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
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')
    # Records Retention Policy Management Fields
    approval_status = fields.Selection([('pending', 'Pending'), ('approved', 'Approved'), ('rejected', 'Rejected')], default='pending')
    changed_by = fields.Many2one('res.users', 'Changed By')
    compliance_rate = fields.Float('Compliance Rate %', default=0.0)
    destruction_efficiency_rate = fields.Float('Destruction Efficiency Rate %', default=0.0)
    destruction_method = fields.Selection([('shred', 'Shred'), ('incinerate', 'Incinerate'), ('pulp', 'Pulp'), ('degauss', 'Degauss')], default='shred')
    audit_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')], default='annually')
    compliance_framework = fields.Selection([('gdpr', 'GDPR'), ('hipaa', 'HIPAA'), ('sox', 'SOX'), ('custom', 'Custom')], default='custom')
    destruction_approval_required = fields.Boolean('Destruction Approval Required', default=True)
    legal_hold_override = fields.Boolean('Legal Hold Override', default=False)
    policy_automation_enabled = fields.Boolean('Policy Automation Enabled', default=False)
    policy_enforcement_level = fields.Selection([('advisory', 'Advisory'), ('mandatory', 'Mandatory'), ('strict', 'Strict')], default='mandatory')
    policy_review_cycle = fields.Selection([('annual', 'Annual'), ('biennial', 'Biennial'), ('triennial', 'Triennial')], default='annual')
    regulatory_compliance_verified = fields.Boolean('Regulatory Compliance Verified', default=False)
    retention_calculation_method = fields.Selection([('creation_date', 'Creation Date'), ('last_access', 'Last Access'), ('custom', 'Custom')], default='creation_date')
    retention_extension_allowed = fields.Boolean('Retention Extension Allowed', default=True)
    retention_monitoring_enabled = fields.Boolean('Retention Monitoring Enabled', default=True)
    risk_assessment_completed = fields.Boolean('Risk Assessment Completed', default=False)
    stakeholder_notification_required = fields.Boolean('Stakeholder Notification Required', default=True)
    version_control_enabled = fields.Boolean('Version Control Enabled', default=True)
    action = fields.Selection([('archive', 'Archive'), ('destroy', 'Destroy'), ('review', 'Review')], string='Action')
    applicable_document_type_ids = fields.Many2many('records.document.type', string='Applicable Document Types')
    compliance_officer = fields.Many2one('res.users', string='Compliance Officer')
    compliance_rate = fields.Float('Compliance Rate (%)', default=0.0)
    legal_reviewer = fields.Many2one('res.users', string='Legal Reviewer')
    review_frequency = fields.Selection([('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('yearly', 'Yearly')], string='Review Frequency', default='yearly')
    notification_enabled = fields.Boolean('Notifications Enabled', default=True)
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')


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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
