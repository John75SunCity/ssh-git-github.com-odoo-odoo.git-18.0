# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = "res.partner"

    # Add new fields here, for example:
    # is_records_customer = fields.Boolean(string="Records Customer", default=False)
    is_records_customer = fields.Boolean(string="Records Customer", default=False)

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
