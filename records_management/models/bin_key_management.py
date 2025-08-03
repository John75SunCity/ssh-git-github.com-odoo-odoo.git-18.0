# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BinKeyManagement(models.Model):
    _name = "bin.key.management"
    _description = "Bin Key Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # Relationship to Partner Bin Key
    partner_bin_key_id = fields.Many2one(
        "partner.bin.key",
        string="Partner Bin Key",
        help="Link to the partner bin key record",
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

    def action_create_invoice(self):
        """Create invoice for key services."""
        self.ensure_one()
        if not self.user_id:
            raise UserError(_("Cannot create invoice without assigned user."))

        # Create activity to track invoice creation
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Invoice created for key service: %s") % self.name,
            note=_("Invoice has been generated for key management services."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Invoice creation initiated for key service: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_move_type": "out_invoice",
                "default_partner_id": (
                    self.user_id.partner_id.id if self.user_id.partner_id else False
                ),
                "default_ref": self.name,
            },
        }

    def action_mark_completed(self):
        """Mark key service as completed."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot complete archived key service."))

        # Update state to completed (using 'active' as completed state)
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nService completed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create completion activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Key service completed: %s") % self.name,
            note=_("Key management service has been successfully completed."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Key service marked as completed: %s") % self.name,
            message_type="notification",
        )

        return {"type": "ir.actions.act_window_close"}

    def action_mark_lost(self):
        """Mark key as lost and require replacement."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot mark archived key as lost."))

        # Update state to inactive (lost)
        self.write(
            {
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nKey marked as lost on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create urgent activity for key replacement
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("URGENT: Key lost - Replacement required: %s") % self.name,
            note=_(
                "Key has been reported lost and requires immediate replacement for security."
            ),
            user_id=self.user_id.id,
            date_deadline=fields.Date.today(),
        )

        self.message_post(
            body=_("Key marked as lost - Security replacement required: %s")
            % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Key Replacement Form"),
            "res_model": "bin.key.management",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": _("Replacement for: %s") % self.name,
                "default_user_id": self.user_id.id,
                "default_notes": _("Replacement key for lost key: %s") % self.name,
            },
        }
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    bin_number = fields.Char(string='Bin Number')
    access_level = fields.Selection([('full', 'Full Access'), ('limited', 'Limited'), ('restricted', 'Restricted')], string='Access Level')
    expiration_date = fields.Date(string='Expiration Date')
    last_check_date = fields.Date(string='Last Check Date')
    authorized_by = fields.Many2one('res.users', string='Authorized By')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')


    def action_replace_key(self):
        """Create replacement key and update records."""
        self.ensure_one()

        # Archive current key
        self.write(
            {
                "state": "archived",
                "active": False,
                "notes": (self.notes or "")
                + _("\nKey replaced on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create replacement key
        replacement_vals = {
            "name": _("Replacement for: %s") % self.name,
            "description": _("Replacement key for: %s")
            % (self.description or self.name),
            "user_id": self.user_id.id,
            "company_id": self.company_id.id,
            "state": "draft",
            "notes": _("Replacement key created for: %s") % self.name,
        }

        replacement_key = self.create(replacement_vals)

        # Create activity for key handover
        replacement_key.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("New replacement key ready: %s") % replacement_key.name,
            note=_("Replacement key has been created and is ready for distribution."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Key replacement completed. New key: %s") % replacement_key.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Replacement Key"),
            "res_model": "bin.key.management",
            "res_id": replacement_key.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_return_key(self):
        """Process key return and update availability."""
        self.ensure_one()
        if self.state == "archived":
            raise UserError(_("Cannot return archived key."))

        # Mark key as returned (inactive but available for reassignment)
        self.write(
            {
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nKey returned on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create activity for key processing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Key returned: %s") % self.name,
            note=_("Key has been returned and is available for reassignment."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Key returned and available for reassignment: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Key Returned"),
                "message": _(
                    "Key %s has been successfully returned and is available for reassignment."
                )
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_unlock_services(self):
        """View all unlock services related to this key."""
        self.ensure_one()

        # Create activity to track service viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Unlock services reviewed for: %s") % self.name,
            note=_("Unlock services and access history has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Unlock Services for: %s") % self.name,
            "res_model": "bin.key.management",
            "view_mode": "tree,form",
            "domain": [("user_id", "=", self.user_id.id), ("state", "!=", "archived")],
            "context": {
                "default_user_id": self.user_id.id,
                "search_default_user_id": self.user_id.id,
            },
            "target": "current",
        }

    def create(self, vals):
        """Override create to set default values."""
        if not vals.get("name"):
            vals["name"] = _("New Record")
        return super().create(vals)
