# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Add new fields here, for example:
    # is_records_customer = fields.Boolean(string="Records Customer", default=False)
    is_records_customer = fields.Boolean(string="Records Customer", default=False)
    records_department_users = fields.One2many(
        "res.users", "partner_id", string="Department Users (Records)"
    )
    records_department_id = fields.Many2one(
        "records.department", string="Records Department"
    )

    # Field Label Configuration
    transitory_field_config_id = fields.Many2one(
        "transitory.field.config",
        string="Field Configuration Template",
        help="Default field configuration template for this customer",
    )

    @api.model
    def _grant_dev_permissions(self):
        """
        Grant superuser-like permissions to the 'Mitchell Admin' user
        for development and testing purposes. This method is triggered
        by a data file on module installation/update.
        """
        # Check if we are in a development environment (e.g., on Odoo.sh)
        # You can add more robust checks if needed, like checking a system parameter.
        if self.env.ref("base.user_root").name == "Mitchell Admin":
            admin_user = self.env.ref("base.user_admin", raise_if_not_found=False)
            if admin_user:
                # Add user to all relevant groups to provide broad access
                groups_to_add = [
                    "base.group_system",
                    "records_management.group_records_manager",
                    # Add any other critical groups here
                ]

                for group_xml_id in groups_to_add:
                    group = self.env.ref(group_xml_id, raise_if_not_found=False)
                    if group and admin_user not in group.users:
                        group.users = [(4, admin_user.id)]

                # Activate developer mode for the admin user
                admin_user.write({"in_group_10": True})  # 'base.group_user_dev_mode'
        return True

    # =============================================================================
    # PARTNER ACTION METHODS (Key Management & Records Integration)
    # =============================================================================

    def action_allow_key_issuance(self):
        """Allow key issuance for this partner."""
        self.ensure_one()
        # Find or create key restriction record
        restriction = self.env["partner.bin.key"].search(
            [("partner_id", "=", self.id)], limit=1
        )
        if restriction:
            restriction.write({"key_issuance_allowed": True})
        else:
            self.env["partner.bin.key"].create(
                {
                    "partner_id": self.id,
                    "key_issuance_allowed": True,
                }
            )
        self.message_post(body=_("Key issuance allowed for this partner."))
        return True

    def action_confirm(self):
        """Confirm partner details for records management."""
        self.ensure_one()
        self.write({"is_records_customer": True})
        self.message_post(body=_("Partner confirmed for records management services."))
        return True

    def action_issue_new_key(self):
        """Issue new bin key for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Issue New Key"),
            "res_model": "bin.key.management",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_key_type": "new_issue",
                "default_status": "active",
            },
        }

    def action_report_lost_key(self):
        """Report lost key for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Report Lost Key"),
            "res_model": "bin.key.management",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.id,
                "default_key_type": "lost_report",
                "default_status": "lost",
                "default_notes": "Key reported as lost by customer",
            },
        }

    def action_restrict_key_issuance(self):
        """Restrict key issuance for this partner."""
        self.ensure_one()
        # Find or create key restriction record
        restriction = self.env["partner.bin.key"].search(
            [("partner_id", "=", self.id)], limit=1
        )
        if restriction:
            restriction.write({"key_issuance_allowed": False})
        else:
            self.env["partner.bin.key"].create(
                {
                    "partner_id": self.id,
                    "key_issuance_allowed": False,
                }
            )
        self.message_post(body=_("Key issuance restricted for this partner."))
        return True

    def action_return_key(self):
        """Process key return for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Return Key"),
            "res_model": "bin.key.management",
            "view_mode": "tree",
            "domain": [("partner_id", "=", self.id), ("status", "=", "active")],
            "context": {
                "default_partner_id": self.id,
                "default_key_type": "return",
                "search_default_active": 1,
            },
        }

    def action_view_active_key(self):
        """View active key for this partner."""
        self.ensure_one()
        active_key = self.env["bin.key.management"].search(
            [("partner_id", "=", self.id), ("status", "=", "active")], limit=1
        )

        if not active_key:
            raise UserError(_("No active key found for this partner."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Active Key"),
            "res_model": "bin.key.management",
            "res_id": active_key.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_bin_keys(self):
        """View all bin keys for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Partner Bin Keys"),
            "res_model": "bin.key.management",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "default_partner_id": self.id,
                "search_default_partner_id": self.id,
            },
        }

    def action_view_unlock_services(self):
        """View unlock services for this partner."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Unlock Services"),
            "res_model": "bin.unlock.service",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.id)],
            "context": {
                "default_partner_id": self.id,
                "search_default_partner_id": self.id,
            },
        }
