# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalFeedback(models.Model):
    _name = "portal.feedback"
    _description = "Portal Feedback"
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

    # =============================================================================
    # PORTAL FEEDBACK ACTION METHODS
    # =============================================================================

    def action_close(self):
        """Close the feedback ticket."""
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Feedback ticket closed."))
        return True

    def action_escalate(self):
        """Escalate feedback to management."""
        self.ensure_one()
        # Create escalation activity for manager
        manager_group = self.env.ref("records_management.group_records_manager")
        manager_users = manager_group.users

        if manager_users:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Escalated Feedback: %s") % self.name,
                note=_(
                    "This feedback has been escalated and requires management attention.\n\nFeedback Details:\n%s"
                )
                % self.description,
                user_id=manager_users[0].id,
            )

        self.message_post(body=_("Feedback escalated to management."))
        return True

    def action_mark_reviewed(self):
        """Mark feedback as reviewed."""
        self.ensure_one()
        self.write({"state": "active"})  # Using active as "reviewed" state
        self.message_post(body=_("Feedback marked as reviewed."))
        return True

    def action_reopen(self):
        """Reopen closed feedback."""
        self.ensure_one()
        if self.state != "inactive":
            raise UserError(_("Only closed feedback can be reopened."))

        self.write({"state": "draft"})
        self.message_post(body=_("Feedback reopened for further review."))
        return True

    def action_respond(self):
        """Respond to customer feedback."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Respond to Feedback"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "portal.feedback",
                "default_res_id": self.id,
                "default_use_template": False,
                "default_composition_mode": "comment",
                "default_subject": f"Response to: {self.name}",
            },
        }

    def action_view_customer_history(self):
        """View feedback history for this customer."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Feedback History"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id), ("id", "!=", self.id)],
            "context": {
                "search_default_user_id": self.user_id.id,
                "group_by": "date_created",
            },
        }

    def action_view_improvement_actions(self):
        """View improvement actions related to this feedback."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Improvement Actions"),
            "res_model": "survey.improvement.action",
            "view_mode": "tree,form",
            "domain": [("feedback_id", "=", self.id)],
            "context": {
                "default_feedback_id": self.id,
                "default_name": f"Improvement for: {self.name}",
            },
        }

    def action_view_related_tickets(self):
        """View related feedback tickets."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Tickets"),
            "res_model": "portal.feedback",
            "view_mode": "tree,form",
            "domain": [
                "|",
                ("user_id", "=", self.user_id.id),
                ("description", "ilike", self.name.split()[0] if self.name else ""),
            ],
            "context": {
                "search_default_user_id": self.user_id.id,
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
