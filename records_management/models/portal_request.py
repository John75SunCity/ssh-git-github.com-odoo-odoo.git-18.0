# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalRequest(models.Model):
    _name = "portal.request"
    _description = "Portal Request"
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
    # PORTAL REQUEST ACTION METHODS
    # =============================================================================

    def action_approve_request(self):
        """Approve the portal request."""
        self.ensure_one()
        if self.state == "draft":
            self.write({"state": "active"})
            self.message_post(body=_("Request approved and activated."))
        return True

    def action_complete_request(self):
        """Mark request as complete."""
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Request marked as complete."))
        return True

    def action_contact_customer(self):
        """Contact customer about this request."""
        self.ensure_one()
        # Return action to open compose message wizard
        return {
            "type": "ir.actions.act_window",
            "name": _("Contact Customer"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "portal.request",
                "default_res_id": self.id,
                "default_use_template": False,
                "default_composition_mode": "comment",
            },
        }

    def action_customer_history(self):
        """View customer history for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer History"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id)],
            "context": {"search_default_user_id": self.user_id.id},
        }

    def action_download(self):
        """Download request data."""
        self.ensure_one()
        # Return action to download as PDF or export
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.portal_request_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_escalate(self):
        """Escalate the request to management."""
        self.ensure_one()
        # Create activity for manager
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Escalated Request: %s") % self.name,
            note=_(
                "This request has been escalated and requires management attention."
            ),
            user_id=(
                self.env.ref("base.group_system").users[0].id
                if self.env.ref("base.group_system").users
                else self.env.user.id
            ),
        )
        self.message_post(body=_("Request escalated to management."))
        return True

    def action_process_request(self):
        """Process the request."""
        self.ensure_one()
        if self.state == "draft":
            self.write({"state": "active"})
        self.message_post(body=_("Request processing started."))
        return True

    def action_send_notification(self):
        """Send notification about request status."""
        self.ensure_one()
        # Send email notification
        template = self.env.ref(
            "records_management.portal_request_notification_template",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)
        self.message_post(body=_("Notification sent to stakeholders."))
        return True

    def action_view_attachments(self):
        """View attachments for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Attachments"),
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "domain": [("res_model", "=", "portal.request"), ("res_id", "=", self.id)],
            "context": {
                "default_res_model": "portal.request",
                "default_res_id": self.id,
            },
        }

    def action_view_communications(self):
        """View all communications for this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Communications"),
            "res_model": "mail.message",
            "view_mode": "tree,form",
            "domain": [("model", "=", "portal.request"), ("res_id", "=", self.id)],
            "context": {"search_default_model": "portal.request"},
        }

    def action_view_details(self):
        """View detailed information about this request."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Details"),
            "res_model": "portal.request",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_related_requests(self):
        """View related requests from same user."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Requests"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id), ("id", "!=", self.id)],
            "context": {"search_default_user_id": self.user_id.id},
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
