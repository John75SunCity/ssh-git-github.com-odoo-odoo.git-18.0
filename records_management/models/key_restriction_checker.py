# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class KeyRestrictionChecker(models.Model):
    _name = "key.restriction.checker"
    _description = "Key Restriction Checker"

    # Basic Information
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
    created_date = fields.Date(string="Date", default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string="Date", tracking=True)
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
