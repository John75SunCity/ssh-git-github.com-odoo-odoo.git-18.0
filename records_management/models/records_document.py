# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsDocument(models.Model):
    _name = "records.document"
    _description = "Records Document"
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
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )

    # Customer Relationships
    customer_inventory_id = fields.Many2one(
        "customer.inventory", string="Customer Inventory"
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

    def action_audit_trail(self):
        """View audit trail for this document."""
        self.ensure_one()

        # Create audit trail activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Audit trail reviewed: %s") % self.name,
            note=_("Document audit trail and chain of custody has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Audit Trail: %s") % self.name,
            "res_model": "mail.message",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("model", "=", "records.document"), ("res_id", "=", self.id)],
            "context": {
                "search_default_model": "records.document",
                "search_default_res_id": self.id,
            },
        }

    def action_download(self):
        """Download document file."""
        self.ensure_one()

        # Create download activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Document downloaded: %s") % self.name,
            note=_("Document file has been downloaded and accessed."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document downloaded: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/records.document/%s/attachment_file/%s?download=true"
            % (self.id, self.name),
            "target": "new",
        }

    def action_mark_permanent(self):
        """Mark document as permanent retention."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot mark archived document as permanent."))

        # Update notes with permanent marking
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nMarked as permanent on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create permanent marking activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document marked permanent: %s") % self.name,
            note=_(
                "Document has been marked for permanent retention and cannot be destroyed."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document marked for permanent retention: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Retention"),
                "message": _("Document %s has been marked for permanent retention.")
                % self.name,
                "type": "info",
                "sticky": True,
            },
        }

    def action_scan_document(self):
        """Initiate document scanning process."""
        self.ensure_one()

        # Create scanning activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document scanning initiated: %s") % self.name,
            note=_("Document scanning process has been initiated and is in progress."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Document scanning initiated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Document"),
            "res_model": "document.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_scan_type": "digital",
            },
        }

    def action_schedule_destruction(self):
        """Schedule document for destruction."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot schedule archived document for destruction."))

        # Update notes with destruction scheduling
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nScheduled for destruction on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create destruction scheduling activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Document scheduled for destruction: %s") % self.name,
            note=_(
                "Document has been scheduled for destruction according to retention policy."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today() + fields.timedelta(days=30),
        )

        self.message_post(
            body=_("Document scheduled for destruction: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Destruction"),
            "res_model": "destruction.schedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_id": self.id,
                "default_destruction_date": fields.Date.today()
                + fields.timedelta(days=30),
            },
        }

    def action_unmark_permanent(self):
        """Remove permanent retention marking from document."""
        self.ensure_one()

        # Update notes with permanent unmarking
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nPermanent marking removed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        )

        # Create unmarking activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Permanent marking removed: %s") % self.name,
            note=_("Permanent retention marking has been removed from document."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Permanent retention marking removed: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Marking Removed"),
                "message": _(
                    "Permanent retention marking has been removed from document %s."
                )
                % self.name,
                "type": "warning",
                "sticky": False,
            },
        }

    def action_view_chain_of_custody(self):
        """View chain of custody for this document."""
        self.ensure_one()

        # Create chain of custody viewing activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Chain of custody reviewed: %s") % self.name,
            note=_("Document chain of custody and handling history has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody: %s") % self.name,
            "res_model": "document.custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("document_id", "=", self.id)],
            "context": {
                "default_document_id": self.id,
                "search_default_document_id": self.id,
                "search_default_group_by_date": True,
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
