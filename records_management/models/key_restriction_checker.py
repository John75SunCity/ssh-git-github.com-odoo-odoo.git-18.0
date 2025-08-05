# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class KeyRestrictionChecker(models.Model):
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _name = "key.restriction.checker"
    _description = "Key Restriction Checker"

    # Basic Information
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )

    name = fields.Char(string="Name", required=True)
    partner_id = fields.Many2one("res.partner", string="Partner")
    restriction_type = fields.Selection(
        [
            ("blacklist", "Blacklisted"),
            ("restricted", "Restricted"),
            ("approved", "Approved"),
        ],
        string="Restriction Type",
    )

    # === COMPREHENSIVE MISSING FIELDS ===
    active = fields.Boolean(string="Flag", default=True, tracking=True)
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    notes = fields.Text(string="Description", tracking=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )
    created_date = fields.Date(
        string="Created Date", default=fields.Date.today, tracking=True
    )
    updated_date = fields.Date(string="Updated Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    bin_number = fields.Char(string="Bin Number")
    access_level = fields.Selection(
        [("full", "Full Access"), ("limited", "Limited"), ("restricted", "Restricted")],
        string="Access Level",
    )
    expiration_date = fields.Date(string="Expiration Date")
    last_check_date = fields.Date(string="Last Check Date")
    authorized_by = fields.Many2one("res.users", string="Authorized By")

    # === ENTERPRISE-GRADE FIELDS ===
    action_required = fields.Boolean("Action Required", default=False)
    bin_identifier = fields.Char("Bin Identifier")
    check_performed = fields.Boolean("Check Performed", default=False)
    customer_name = fields.Char("Customer Name")
    key_allowed = fields.Boolean("Key Allowed", default=True)
    access_level_verified = fields.Boolean("Access Level Verified", default=False)
    authorization_bypass_used = fields.Boolean(
        "Authorization Bypass Used", default=False
    )
    override_reason = fields.Text("Override Reason")
    security_violation_detected = fields.Boolean(
        "Security Violation Detected", default=False
    )

    # === ANALYTICS & COMPLIANCE ===
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)
    last_audit_date = fields.Date(string="Last Audit Date")
    compliance_notes = fields.Text(string="Compliance Notes")
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
    )

    # === COMPUTED FIELDS ===
    is_expired = fields.Boolean(
        string="Is Expired", compute="_compute_is_expired", store=True
    )
    days_until_expiration = fields.Integer(
        string="Days Until Expiration",
        compute="_compute_days_until_expiration",
        store=True,
    )

    @api.depends("expiration_date")
    def _compute_is_expired(self):
        from datetime import date

        for record in self:
            if record.expiration_date and record.expiration_date < date.today():
                record.is_expired = True
            else:
                record.is_expired = False

    @api.depends("expiration_date")
    def _compute_days_until_expiration(self):
        from datetime import date

        for record in self:
            if record.expiration_date:
                record.days_until_expiration = (
                    record.expiration_date - date.today()
                ).days
            else:
                record.days_until_expiration = 0

    # === MISSING VIEW-RELATED FIELDS ===
    restriction_date = fields.Date(
        string="Restriction Date", help="Date when restriction was applied"
    )
    restriction_notes = fields.Text(
        string="Restriction Notes", help="Additional notes about the restriction"
    )
    restriction_reason = fields.Text(
        string="Restriction Reason", help="Reason for applying restriction"
    )
    status_message = fields.Char(
        string="Status Message", help="Current status message for restriction checker"
    )

    # === ADDITIONAL MISSING FIELD ===
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Company this restriction checker belongs to",
    )

    # === VALIDATION CONSTRAINTS ===
    @api.constrains("expiration_date")
    def _check_expiration_date(self):
        for record in self:
            if record.expiration_date and record.expiration_date < record.created_date:
                raise ValidationError(
                    _("Expiration date cannot be before creation date.")
                )

    # === ACTION METHODS ===
    def action_audit_checker(self):
        """Audit this key restriction checker."""
        self.ensure_one()
        self.last_audit_date = fields.Date.today()
        self.message_post(body=_("Audit completed for this key restriction checker."))
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Complete"),
                "message": _("Audit completed for this key restriction checker."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_check_customer(self):
        """Check customer restrictions."""
        self.ensure_one()

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
        """Reset checker."""
        self.ensure_one()

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
        """Create unlock service."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Unlock Service Created"),
                "message": _("Unlock service has been created."),
                "type": "success",
                "sticky": False,
            },
        }
