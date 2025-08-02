# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PosConfig(models.Model):
    _inherit = "pos.config"
    _description = "Pos Config"
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
        "res.users", string="Responsible User", default=lambda self: self.env.user
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

    def action_close_session(self):
        """Close current POS session."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active POS configurations can close sessions."))

        # Update notes with session closure
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nSession closed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create session closure activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("POS session closed: %s") % self.name,
            note=_("POS session has been properly closed with balance reconciliation."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("POS session closed: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Close Session"),
            "res_model": "pos.session",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("config_id", "=", self.id), ("state", "=", "opened")],
            "context": {
                "default_config_id": self.id,
                "search_default_config_id": self.id,
            },
        }

    def action_force_close_session(self):
        """Force close POS session with administrative override."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(
                _("Cannot force close session for archived POS configuration.")
            )

        # Update notes with forced closure
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nSession force closed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create urgent activity for force closure
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("POS session force closed: %s") % self.name,
            note=_(
                "POS session was force closed - requires review and balance verification."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today(),
        )

        self.message_post(
            body=_("POS session force closed - requires balance review: %s")
            % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Session Force Closed"),
                "message": _(
                    "POS session %s has been force closed. Please review balance discrepancies."
                )
                % self.name,
                "type": "warning",
                "sticky": True,
            },
        }

    def action_open_session(self):
        """Open new POS session."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active POS configurations can open sessions."))

        # Update notes with session opening
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nNew session opened on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create session opening activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("POS session opened: %s") % self.name,
            note=_("New POS session has been opened and is ready for transactions."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("New POS session opened: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Open Session"),
            "res_model": "pos.session",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_config_id": self.id,
                "default_user_id": self.user_id.id,
            },
        }

    def action_view_orders(self):
        """View all orders for this POS configuration."""
        self.ensure_one()

        # Create activity to track order viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("POS orders reviewed: %s") % self.name,
            note=_("POS orders and transaction history has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("POS Orders for: %s") % self.name,
            "res_model": "pos.order",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("config_id", "=", self.id)],
            "context": {
                "default_config_id": self.id,
                "search_default_config_id": self.id,
                "search_default_today": True,
            },
        }

    def action_view_sales_report(self):
        """View sales report for this POS configuration."""
        self.ensure_one()

        # Create activity for sales report review
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Sales report generated: %s") % self.name,
            note=_("Sales report has been generated and reviewed for analysis."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Sales report accessed for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Sales Report for: %s") % self.name,
            "res_model": "report.pos.order",
            "view_mode": "graph,pivot,tree",
            "target": "current",
            "domain": [("config_id", "=", self.id)],
            "context": {
                "default_config_id": self.id,
                "search_default_config_id": self.id,
                "search_default_today": True,
                "group_by": ["date_order"],
            },
        }

    def action_view_sessions(self):
        """View all sessions for this POS configuration."""
        self.ensure_one()

        # Create activity to track session viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("POS sessions reviewed: %s") % self.name,
            note=_("POS sessions and daily operations have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("POS Sessions for: %s") % self.name,
            "res_model": "pos.session",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("config_id", "=", self.id)],
            "context": {
                "default_config_id": self.id,
                "search_default_config_id": self.id,
                "search_default_recent": True,
            },
        }

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
