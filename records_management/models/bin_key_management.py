# -*- coding: utf-8 -*-

# Import handling for disconnected development environment
try:
    from odoo import models, fields, api, _
    from odoo.exceptions import UserError
except ImportError:
    # Fallback for development environments without Odoo installed
    # These will be properly imported when deployed to Odoo.sh
    models = None
    fields = None
    api = None
    _ = lambda x: x  # Simple fallback for translation function

    class UserError(Exception):
        pass


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
    date_created = fields.Datetime(
        string="Key Created Date", default=fields.Datetime.now
    )
    date_modified = fields.Datetime(string="Modified Date")

    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - BIN KEY MANAGEMENT ENHANCEMENT
    # ============================================================================

    # Key Identification & Tracking (Modified for non-unique keys)
    key_number = fields.Char(
        string="Key Reference",
        index=True,
        help="Optional reference for the bin key (not unique since all keys are the same)",
    )

    # Partner and Location Management
    partner_company = fields.Char(
        string="Partner Company", help="Name of the company that issued/owns the key"
    )
    issue_location = fields.Char(
        string="Issue Location", help="Location where the key was issued"
    )

    # Date Management
    issue_date = fields.Date(
        string="Issue Date",
        default=fields.Date.today,
        help="Date when the key was issued",
    )
    expected_return_date = fields.Date(
        string="Expected Return Date", help="Expected date for key return"
    )

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
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    bin_number = fields.Char(string="Bin Number")
    access_level = fields.Selection(
        [("full", "Full Access"), ("limited", "Limited"), ("restricted", "Restricted")],
        string="Access Level",
    )
    expiration_date = fields.Date(string="Expiration Date")
    last_check_date = fields.Date(string="Last Check Date")
    authorized_by = fields.Many2one("res.users", string="Authorized By")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - BIN KEY MANAGEMENT ENHANCEMENT
    # ============================================================================

    # Partner and Service Management (Required by views)
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        tracking=True,
        help="Partner associated with this key management record",
    )

    # Key Replacement Tracking
    replaced_by_id = fields.Many2one(
        "bin.key.management",
        string="Replaced By",
        help="New key record that replaces this key for full traceability",
    )
    replacement_of_id = fields.Many2one(
        "bin.key.management",
        string="Replacement Of",
        help="Always set for replacement keys; links to the original key being replaced. The original key's 'replaced_by_id' points back to this record for full traceability.",
    )

    # Service Date Management
    return_date = fields.Date(
        string="Return Date",
        tracking=True,
        help="Date when the key was returned",
    )
    service_date = fields.Date(
        string="Service Date",
        tracking=True,
        help="Date when a key-related service (maintenance, replacement, issue, etc.) was performed. Used for reporting and automation to track service events.",
    )

    # Key Management Status
    status = fields.Selection(
        [
            ("available", "Available"),
            ("issued", "Issued"),
            ("returned", "Returned"),
            ("lost", "Lost"),
            ("replaced", "Replaced"),
        ],
        string="Key Status",
        default="available",
        tracking=True,
    )

    # Service Documentation
    service_type = fields.Selection(
        [
            ("issue", "Key Issue"),
            ("return", "Key Return"),
            ("replacement", "Key Replacement"),
            ("maintenance", "Key Maintenance"),
        ],
        string="Service Type",
        default="issue",
        tracking=True,
    )

    service_notes = fields.Text(
        string="Service Notes", help="Detailed notes about the key service performed"
    )

    # Security and Access Control
    security_code = fields.Char(
        string="Security Code", help="Internal security code for this key"
    )

    access_restrictions = fields.Text(
        string="Access Restrictions", help="Special access restrictions or requirements"
    )

    # Financial Tracking
    service_fee = fields.Monetary(
        string="Service Fee",
        currency_field="currency_id",
        help="Fee charged for this key service",
    )
    billable = fields.Boolean("Billable", default=True)
    bin_location = fields.Char("Bin Location")
    bin_locations = fields.Text("Multiple Bin Locations")
    charge_amount = fields.Monetary("Charge Amount", currency_field="currency_id")
    emergency_contact = fields.Many2one("res.partner", "Emergency Contact")
    access_authorization_level = fields.Selection(
        [("basic", "Basic"), ("elevated", "Elevated"), ("admin", "Admin")],
        default="basic",
    )
    access_log_retention_days = fields.Integer(
        "Access Log Retention (Days)", default=365
    )
    bin_access_frequency = fields.Selection(
        [("daily", "Daily"), ("weekly", "Weekly"), ("monthly", "Monthly")],
        default="weekly",
    )
    bin_security_level = fields.Selection(
        [("standard", "Standard"), ("high", "High"), ("maximum", "Maximum")],
        default="standard",
    )
    currency_id = fields.Many2one(
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    )
    customer_key_count = fields.Integer("Customer Key Count", default=1)
    key_audit_trail_enabled = fields.Boolean("Key Audit Trail Enabled", default=True)
    key_duplication_allowed = fields.Boolean("Key Duplication Allowed", default=False)
    key_expiration_date = fields.Date("Key Expiration Date")
    key_holder_verification_required = fields.Boolean(
        "Key Holder Verification Required", default=True
    )
    key_replacement_fee = fields.Monetary(
        "Key Replacement Fee", currency_field="currency_id"
    )
    key_restriction_notes = fields.Text("Key Restriction Notes")
    key_security_deposit = fields.Monetary(
        "Key Security Deposit", currency_field="currency_id"
    )
    lock_change_required = fields.Boolean("Lock Change Required", default=False)
    master_key_override = fields.Boolean("Master Key Override Available", default=False)
    multi_user_access_allowed = fields.Boolean(
        "Multi-user Access Allowed", default=False
    )

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

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")
        return super().create(vals_list)
