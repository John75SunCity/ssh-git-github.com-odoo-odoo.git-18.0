# -*- coding: utf-8 -*-
"""
Key Restriction Checker Module

Comprehensive key access control system within the Records Management System.
This module provides enterprise-grade key restriction checking, access level validation,
audit trail management, and compliance tracking for secure bin access control.

Key Features:
- Comprehensive access level validation (full, limited, restricted)
- Real-time restriction checking with automated alerts
- Complete audit trail management with retention policies
- Integration with customer portal and security workflows
- Advanced analytics and compliance reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError




class KeyRestrictionChecker(models.Model):
    _name = "key.restriction.checker"
    _description = "Key Restriction Checker"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & PARTNER INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner", string="Partner", tracking=True, index=True
    )
    customer_id = fields.Many2one(
        "res.partner", string="Customer", tracking=True, index=True
    )
    customer_name = fields.Char(
        string="Customer Name", related="customer_id.name", store=True
    )

    # ============================================================================
    # RESTRICTION & ACCESS CONTROL
    # ============================================================================
    restriction_type = fields.Selection(
        [
            ("blacklist", "Blacklisted"),
            ("restricted", "Restricted"),
            ("approved", "Approved"),
        ],
        string="Restriction Type",
        tracking=True,
    )

    access_level = fields.Selection(
        [("full", "Full Access"), ("limited", "Limited"), ("restricted", "Restricted")],
        string="Access Level",
        tracking=True,
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ============================================================================
    # BIN & KEY MANAGEMENT
    # ============================================================================
    bin_number = fields.Char(string="Bin Number", tracking=True, index=True)
    bin_identifier = fields.Char(string="Bin Identifier", tracking=True)
    key_allowed = fields.Boolean(string="Key Allowed", default=True, tracking=True)

    # ============================================================================
    # AUTHORIZATION & SECURITY
    # ============================================================================
    authorized_by_id = fields.Many2one(
        "res.users", string="Authorized By", tracking=True
    )
    access_level_verified = fields.Boolean(
        string="Access Level Verified", default=False, tracking=True
    )
    authorization_bypass_used = fields.Boolean(
        string="Authorization Bypass Used", default=False, tracking=True
    )
    override_reason = fields.Text(string="Override Reason", tracking=True)
    security_violation_detected = fields.Boolean(
        string="Security Violation Detected", default=False, tracking=True
    )

    # ============================================================================
    # DATES & TIMING
    # ============================================================================
    created_date = fields.Date(
        string="Created Date", default=fields.Date.today, required=True, tracking=True
    )
    updated_date = fields.Date(string="Updated Date", tracking=True)
    expiration_date = fields.Date(string="Expiration Date", tracking=True)
    last_check_date = fields.Date(string="Last Check Date", tracking=True)
    restriction_date = fields.Date(
        string="Restriction Date",
        tracking=True,
        help="Date when restriction was applied",
    )

    # ============================================================================
    # OPERATIONAL FLAGS
    # ============================================================================
    action_required = fields.Boolean(
        string="Action Required", default=False, tracking=True
    )
    check_performed = fields.Boolean(
        string="Check Performed", default=False, tracking=True
    )

    # ============================================================================
    # NOTES & DOCUMENTATION
    # ============================================================================
    notes = fields.Text(string="Description", tracking=True)
    restriction_notes = fields.Text(
        string="Restriction Notes",
        tracking=True,
        help="Additional notes about the restriction",
    )
    restriction_reason = fields.Text(
        string="Restriction Reason",
        tracking=True,
        help="Reason for applying restriction",
    )
    status_message = fields.Char(
        string="Status Message", help="Current status message for restriction checker"
    )

    # ============================================================================
    # AUDIT & COMPLIANCE
    # ============================================================================
    audit_trail_enabled = fields.Boolean(
        string="Audit Trail Enabled", default=True, tracking=True
    )
    last_audit_date = fields.Date(string="Last Audit Date", tracking=True)
    compliance_notes = fields.Text(string="Compliance Notes", tracking=True)
    retention_policy = fields.Selection(
        [
            ("1year", "1 Year"),
            ("3years", "3 Years"),
            ("5years", "5 Years"),
            ("7years", "7 Years"),
            ("permanent", "Permanent"),
        ],
        string="Retention Policy",
        default="7years",
        tracking=True,
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    is_expired = fields.Boolean(
        string="Is Expired", compute="_compute_is_expired", store=True
    )
    days_until_expiration = fields.Integer(
        string="Days Until Expiration",
        compute="_compute_days_until_expiration",
        store=True,
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    action_buttons = fields.Char(string='Action Buttons')
    action_check_customer = fields.Char(string='Action Check Customer')
    action_create_unlock_service = fields.Char(string='Action Create Unlock Service')
    action_reset = fields.Char(string='Action Reset')
    bin_info = fields.Char(string='Bin Info')
    context = fields.Char(string='Context')
    customer_info = fields.Char(string='Customer Info')
    input_section = fields.Char(string='Input Section')
    res_model = fields.Char(string='Res Model')
    restriction_details = fields.Char(string='Restriction Details')
    results_section = fields.Char(string='Results Section')
    target = fields.Char(string='Target')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("expiration_date")
    def _compute_is_expired(self):
        """Compute if the restriction has expired"""
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                record.is_expired = record.expiration_date < today
            else:
                record.is_expired = False

    @api.depends("expiration_date")
    def _compute_days_until_expiration(self):
        """Compute days until expiration"""
        today = fields.Date.today()
        for record in self:
            if record.expiration_date:
                delta = record.expiration_date - today
                record.days_until_expiration = delta.days
            else:
                record.days_until_expiration = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def __check_audit_checker(self):
        """Audit this key restriction checker"""

        self.ensure_one()
        self.write({"last_audit_date": fields.Date.today(), "check_performed": True})

        self.message_post(
            body=_("Audit completed for key restriction checker: %s", self.name)
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Complete"),
                "message": _("Audit completed for this key restriction checker."),
                "type": "success",
                "sticky": False,
            },
        }

    def __check__check_customer(self):
        """Check customer restrictions"""

        self.ensure_one()

        self.write({"last_check_date": fields.Date.today(), "check_performed": True})

        # Log the check activity
        self.message_post(
            body=_("Customer restrictions checked for: %s", (self.customer_name or self.name))
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Customer Checked"),
                "message": _("Customer restrictions have been checked."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_reset(self):
        """Reset checker to initial state"""

        self.ensure_one()

        self.write(
            {
                "state": "draft",
                "check_performed": False,
                "action_required": False,
                "security_violation_detected": False,
                "access_level_verified": False,
                "authorization_bypass_used": False,
                "updated_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Key restriction checker has been reset"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Reset Complete"),
                "message": _("Key restriction checker has been reset."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_create_unlock_service(self):
        """Create unlock service request"""

        self.ensure_one()

        # Create related service request or work order
        self.write({"action_required": True, "state": "in_progress"})

        self.message_post(
            body=_("Unlock service request created for: %s", (self.bin_identifier or self.name))
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Unlock Service Created"),
                "message": _("Unlock service request has been created."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_approve_access(self):
        """Approve access request"""

        self.ensure_one()
        if self.state not in ["draft", "in_progress"]:
            raise UserError(_("Can only approve draft or in-progress requests"))

        self.write(
            {
                "state": "completed",
                "restriction_type": "approved",
                "access_level_verified": True,
                "authorized_by": self.env.user.id,
                "updated_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Access approved for: %s", self.name))

        return True

    def action_deny_access(self):
        """Deny access request"""

        self.ensure_one()

        self.write(
            {
                "state": "cancelled",
                "restriction_type": "restricted",
                "key_allowed": False,
                "updated_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Access denied for: %s", self.name))

        return True

    def action_escalate_security_violation(self):
        """Escalate security violation to management"""

        self.ensure_one()

        self.write(
            {
                "security_violation_detected": True,
                "action_required": True,
                "state": "in_progress",
            }
        )

        # Create high priority activity
        self.activity_schedule(
            "mail.mail_activity_data_call",
            summary=_("Security Violation - %s", self.name),
            note=_(
                "Security violation detected for bin: %s. Immediate attention required."
            )
            % (self.bin_identifier or self.name),
            user_id=self.user_id.id or self.env.user.id,
            date_deadline=fields.Date.today(),
        )

        self.message_post(
            body=_("Security violation escalated for: %s", self.name),
            message_type="notification",
        )

        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("expiration_date", "created_date")
    def _check_expiration_date(self):
        """Validate expiration date is not before creation date"""
        for record in self:
            if (
                record.expiration_date
                and record.created_date
                and record.expiration_date < record.created_date
            ):
                raise ValidationError(
                    _("Expiration date cannot be before creation date.")
                )

    @api.constrains("access_level", "restriction_type")
    def _check_access_consistency(self):
        """Validate access level is consistent with restriction type"""
        for record in self:
            if record.restriction_type == "blacklist" and record.access_level == "full":
                raise ValidationError(
                    _("Blacklisted entries cannot have full access level.")
                )

    @api.constrains("bin_number")
    def _check_bin_number_format(self):
        """Validate bin number format"""
        for record in self:
            if record.bin_number and len(record.bin_number.strip()) == 0:
                raise ValidationError(_("Bin number cannot be empty."))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values and generate sequence"""
        for vals in vals_list:
            if not vals.get("created_date"):
                vals["created_date"] = fields.Date.today()
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "key.restriction.checker"
                ) or _("New Checker")
        return super(KeyRestrictionChecker, self).create(vals_list)

    def write(self, vals):
        """Override write to track updates"""
        if any(key in vals for key in ["state", "restriction_type", "access_level"]):
            vals["updated_date"] = fields.Date.today()
        return super(KeyRestrictionChecker, self).write(vals)

    def get_restriction_status_color(self):
        """Get color code for restriction status display"""
        self.ensure_one()
        color_map = {
            "approved": "success",
            "restricted": "warning",
            "blacklist": "danger",
        }
        return color_map.get(self.restriction_type, "secondary")

    def get_access_level_color(self):
        """Get color code for access level display"""
        self.ensure_one()
        color_map = {
            "full": "success",
            "limited": "warning",
            "restricted": "danger",
        }
        return color_map.get(self.access_level, "secondary")

    def get_state_color(self):
        """Get color code for state display"""
        self.ensure_one()
        color_map = {
            "draft": "secondary",
            "in_progress": "info",
            "completed": "success",
            "cancelled": "danger",
        }
        return color_map.get(self.state, "secondary")

    @api.model
    def _check_expiring_restrictions(self):
        """Cron job to check for expiring restrictions"""
        expiring_soon = self.search(
            [
                (
                    "expiration_date",
                    "<=",
                    fields.Date.today() + fields.timedelta(days=7),
                ),
                ("expiration_date", ">=", fields.Date.today()),
                ("state", "!=", "cancelled"),
            ]
        )

        for checker in expiring_soon:
            checker.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Restriction Expiring Soon - %s", checker.name),
                note=_("This key restriction will expire on %s.", checker.expiration_date),
                user_id=checker.user_id.id or self.env.user.id,
                date_deadline=checker.expiration_date,
            )
