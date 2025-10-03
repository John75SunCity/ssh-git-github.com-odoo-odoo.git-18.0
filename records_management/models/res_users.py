from odoo import api, fields, models, _


class ResUsers(models.Model):
    _inherit = 'res.users'

    records_user_profile = fields.Selection(
        selection=[
            ('records_admin', 'Records Admin'),
            ('records_user', 'Records User'),
            ('portal_company_admin', 'Portal Company Admin'),
            ('portal_department_admin', 'Portal Department Admin'),
            ('portal_user', 'Portal User'),
            ('portal_read_only', 'Portal Read Only'),
        ],
        string='Records Profile',
        help="High-level role abstraction that automatically assigns the correct security groups for the Records Management module (internal + portal tiers).",
        default='records_user',
        tracking=True,
    )

    # Mapping constants (XML IDs) -> kept here for clarity & single-point maintenance
    _RM_INTERNAL_MAP = {
        'records_admin': 'records_management.group_records_admin',
        'records_user': 'records_management.group_records_user',
    }
    _RM_PORTAL_MAP = {
        'portal_company_admin': 'records_management.group_portal_company_admin',
        'portal_department_admin': 'records_management.group_portal_department_admin',
        'portal_user': 'records_management.group_portal_department_user',  # reuse business-functions tier
        'portal_read_only': 'records_management.group_portal_readonly_employee',
    }

    def _rm_all_profile_xmlids(self):  # small helper for cleanup
        return list(self._RM_INTERNAL_MAP.values()) + list(self._RM_PORTAL_MAP.values())

    def _apply_records_user_profile(self):
        """Synchronize groups according to records_user_profile.

        Rules:
        - Internal profiles (records_admin, records_user) must have base.group_user, must NOT have base.group_portal.
        - Portal profiles (portal_*) must have base.group_portal, must NOT have base.group_user.
        - Remove any prior records_management profile groups then add the mapped one. Implied groups chain handles extended rights.
        - Keep any unrelated groups (e.g., accounting) intact.
        """
        base_group_user = self.env.ref('base.group_user')
        base_group_portal = self.env.ref('base.group_portal')

        # Build once
        xmlid_map = {**self._RM_INTERNAL_MAP, **self._RM_PORTAL_MAP}

        for user in self:
            profile = user.records_user_profile
            if not profile:
                continue  # nothing to do

            # Determine target group XML ID
            target_xmlid = xmlid_map.get(profile)
            if not target_xmlid:
                continue

            target_group = self.env.ref(target_xmlid)

            # If already aligned (target group present and mutually exclusive base group correct) skip
            if target_group in user.groups_id:
                if profile in self._RM_INTERNAL_MAP and base_group_user in user.groups_id and base_group_portal not in user.groups_id:
                    continue
                if profile in self._RM_PORTAL_MAP and base_group_portal in user.groups_id and base_group_user not in user.groups_id:
                    continue

            # Remove all existing profile groups for safety (avoid leftover privilege) using unlink from m2m through commands
            # but keep unrelated groups
            new_groups = user.groups_id - self.env['res.groups']  # start with original (copy semantics)
            removable = self.env['res.groups']
            for xmlid in self._rm_all_profile_xmlids():
                try:
                    removable |= self.env.ref(xmlid)
                except Exception:
                    continue
            # filter out removable from current groups
            new_groups = user.groups_id - removable

            # Add target group
            new_groups |= target_group

            # Base group alignment (internal vs portal)
            if profile in self._RM_INTERNAL_MAP:
                if base_group_portal in new_groups:
                    new_groups -= base_group_portal
                new_groups |= base_group_user
            else:  # portal tier
                if base_group_user in new_groups:
                    new_groups -= base_group_user
                new_groups |= base_group_portal

            if set(new_groups.ids) != set(user.groups_id.ids):
                user.groups_id = [(6, 0, new_groups.ids)]

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Post-create apply (need real record with m2m)
        records._apply_records_user_profile()
        return records

    def write(self, vals):
        res = super().write(vals)
        # Only apply if the profile changed or explicitly requested (avoid extra writes)
        if 'records_user_profile' in vals:
            self._apply_records_user_profile()
        return res
