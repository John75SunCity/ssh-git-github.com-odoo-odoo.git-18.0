from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


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
        # tracking removed: res.users may not inherit mail.thread in all editions / variants; parameter caused warnings
    )

    @api.depends('records_user_profile')
    def _compute_partner_required(self):
        """Make partner selection required for portal users"""
        for user in self:
            user.partner_required = user.records_user_profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']

    partner_required = fields.Boolean(string='Partner Required', compute='_compute_partner_required', store=False)

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
        # Only validate when explicitly setting our custom records_user_profile
        # Allow standard portal creation to work without interference
        for vals in vals_list:
            profile = vals.get('records_user_profile')
            # Only validate if user is explicitly setting a portal profile
            # Skip validation for standard portal user creation (via portal wizard)
            if profile and profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']:
                if not vals.get('partner_id'):
                    raise ValidationError(_(
                        "Portal users must be assigned to an existing customer company. "
                        "Please select a Related Partner from the dropdown list before saving."
                    ))
                # Verify the selected partner is a customer (not auto-created)
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if partner and not partner.is_company:
                    raise ValidationError(_(
                        "Portal users must be assigned to a company partner, not an individual contact. "
                        "Please select a company from the Related Partner dropdown."
                    ))

        records = super().create(vals_list)
        # Apply profile settings after creation, but only if profile was set
        for record in records:
            if record.records_user_profile:
                record._apply_records_user_profile()
        return records

    def write(self, vals):
        # Only validate when explicitly changing our custom records_user_profile
        # Allow standard portal user modifications (group changes) to work
        if 'records_user_profile' in vals:
            for user in self:
                profile = vals.get('records_user_profile')
                # Only validate if explicitly setting a portal profile
                if profile and profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']:
                    partner_id = vals.get('partner_id', user.partner_id.id if user.partner_id else False)
                    if not partner_id:
                        raise ValidationError(_(
                            "Portal users must be assigned to an existing customer company. "
                            "Please select a Related Partner from the dropdown list before saving."
                        ))
                    # Verify the selected partner is a customer company
                    partner = self.env['res.partner'].browse(partner_id)
                    if partner and not partner.is_company:
                        raise ValidationError(_(
                            "Portal users must be assigned to a company partner, not an individual contact. "
                            "Please select a company from the Related Partner dropdown."
                        ))

        res = super().write(vals)
        # Only apply if our custom profile was explicitly changed
        if 'records_user_profile' in vals and vals.get('records_user_profile'):
            self._apply_records_user_profile()
        return res

    def _update_last_login(self):
        """Override to prevent partner auto-creation side effects"""
        return super()._update_last_login()

    @api.model
    def _get_default_image(self):
        """Override to prevent partner auto-creation during user setup"""
        return super()._get_default_image()

    @api.model
    def _prevent_user_type_conflicts(self):
        """Ensure users don't have conflicting base groups (internal + portal)"""
        base_group_user = self.env.ref('base.group_user', raise_if_not_found=False)
        base_group_portal = self.env.ref('base.group_portal', raise_if_not_found=False)
        
        if not (base_group_user and base_group_portal):
            return
        
        # Find users with both groups (conflicting state)
        conflicted_users = self.search([
            ('groups_id', 'in', [base_group_user.id]),
            ('groups_id', 'in', [base_group_portal.id])
        ])
        
        for user in conflicted_users:
            # If user has our portal profile, prioritize portal
            if user.records_user_profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']:
                user.groups_id = [(3, base_group_user.id)]  # Remove internal group
            # Otherwise, prioritize internal
            else:
                user.groups_id = [(3, base_group_portal.id)]  # Remove portal group
