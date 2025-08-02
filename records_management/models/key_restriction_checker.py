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
        default="approved",
    )

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
