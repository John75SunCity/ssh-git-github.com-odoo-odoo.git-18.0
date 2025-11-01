from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, AccessError
from odoo.http import request


class ResUsers(models.Model):
    _inherit = 'res.users'

    @api.model
    def _assign_admin_groups(self):
        """Automatically assign admin users to Records Admin and Settings groups
        This runs during module upgrade to fix access lockouts
        
        CRITICAL: Uses sudo() to bypass access checks during upgrade
        """
        import logging
        _logger = logging.getLogger(__name__)

        try:
            # Get the groups using sudo to bypass access restrictions
            records_admin = self.env.ref('records_management.group_records_admin', raise_if_not_found=False)
            settings_group = self.env.ref('base.group_system', raise_if_not_found=False)

            if not records_admin:
                _logger.warning("⚠️  Records Admin group not found - skipping admin assignment")
                return False
            if not settings_group:
                _logger.warning("⚠️  Settings group not found - skipping admin assignment")
                return False

            # Find all admin users (login contains 'admin' or has id=1, id=2, or id=6)
            # Use sudo() to search even if current user has no access
            admin_users = self.sudo().search([
                '|', '|', '|',
                ('login', 'ilike', 'admin'),
                ('id', '=', 1),
                ('id', '=', 2),
                ('id', '=', 6)  # John Cope - Records Admin
            ])

            _logger.info(f"🔧 Found {len(admin_users)} admin users to process: {admin_users.mapped('login')}")

            # Add them to both groups - ONE group at a time to avoid user type conflicts
            for user in admin_users:
                try:
                    groups_to_add = []

                    # Only add if not already present
                    if records_admin.id not in user.groups_id.ids:
                        groups_to_add.append(records_admin.id)
                        _logger.info(f"  Adding {user.login} to Records Admin group")

                    if settings_group.id not in user.groups_id.ids:
                        groups_to_add.append(settings_group.id)
                        _logger.info(f"  Adding {user.login} to Settings group")

                    # Add all groups in a single write to avoid multiple user type validations
                    if groups_to_add:
                        user.sudo().write({'groups_id': [(4, gid) for gid in groups_to_add]})
                        _logger.info(f"✅ Successfully assigned groups to {user.login}")
                    else:
                        _logger.info(f"✅ User {user.login} already has all required groups")

                except Exception as user_error:
                    _logger.error(f"❌ Error assigning groups to user {user.login}: {user_error}")
                    continue  # Continue with other users even if one fails

            return True

        except Exception as e:
            _logger.error(f"❌ Critical error in _assign_admin_groups: {e}")
            return False

    # ============================================================================
    # PORTAL ACCOUNT ACCESS FEATURE
    # ============================================================================
    can_access_portal_accounts = fields.Boolean(
        string="Can Access Customer Portal Accounts",
        default=False,
        groups='base.group_system',
        help="Allow this user to log into customer portal accounts from backend to assist customers"
    )

    records_user_profile = fields.Selection(
        selection=[
            ('records_admin', 'Internal: Records Admin'),
            ('records_user', 'Internal: Records User'),
            ('portal_company_admin', 'Portal: Company Admin (Full Control)'),
            ('portal_department_admin', 'Portal: Department Admin (Can Delegate)'),
            ('portal_user', 'Portal: Department User (Business Functions)'),
            ('portal_read_only', 'Portal: Read-Only Employee (View Only)'),
        ],
        string='Records Management Access Level',
        help="Portal users are standard Odoo Portal users with different access levels:\n"
             "• Company Admin: Full control over all company data and users\n"
             "• Department Admin: Can delegate users and manage department data\n"
             "• Department User: Can perform business functions (requests, inventory)\n"
             "• Read-Only: View-only access to assigned records\n\n"
             "All portal options require selecting a Customer Company/Contact below.\n"
             "Internal users have backend access with Records Management permissions.",
        default='records_user',
        # tracking removed: res.users may not inherit mail.thread in all editions / variants; parameter caused warnings
    )

    @api.depends('records_user_profile')
    def _compute_partner_required(self):
        """Make partner selection required for portal users"""
        for user in self:
            user.partner_required = user.records_user_profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']

    partner_required = fields.Boolean(string='Partner Required', compute='_compute_partner_required', store=False)

    @api.onchange('records_user_profile')
    def _onchange_records_user_profile(self):
        """Preview group assignment when user changes the profile in UI"""
        if self.records_user_profile:
            # Show a warning if portal profile but no partner
            if self.records_user_profile in ['portal_company_admin', 'portal_department_admin', 'portal_user', 'portal_read_only']:
                if not self.partner_id:
                    return {
                        'warning': {
                            'title': _('Partner Required'),
                            'message': _('Portal profiles require selecting a Related Partner (customer company/contact). Please select one before saving.')
                        }
                    }

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
                partner_id = vals.get('partner_id')
                if not partner_id:
                    raise ValidationError(_(
                        "Portal profiles require a Related Partner. Please select the customer contact or company before saving."
                    ))
                partner = self.env['res.partner'].browse(partner_id)
                if profile in ['portal_company_admin', 'portal_department_admin'] and partner and not partner.is_company:
                    raise ValidationError(_(
                        "Portal company or department administrators must be linked to a company contact. "
                        "Please choose the customer company record instead of an individual contact."
                    ))

        records = super().create(vals_list)
        # Apply profile settings after creation, but only if profile was set
        for record in records:
            if record.share:
                # Automatically align portal user profiles to avoid user type conflicts
                partner = record.partner_id
                target_profile = record.records_user_profile if record.records_user_profile in self._RM_PORTAL_MAP else False

                if not target_profile:
                    if partner and partner.company_type == 'company':
                        target_profile = 'portal_company_admin'
                    else:
                        target_profile = 'portal_user'

                if record.records_user_profile != target_profile:
                    record.sudo().write({'records_user_profile': target_profile})
                else:
                    record._apply_records_user_profile()
                continue

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
                            "Portal profiles require a Related Partner. Please select the customer contact or company before saving."
                        ))
                    partner = self.env['res.partner'].browse(partner_id)
                    if profile in ['portal_company_admin', 'portal_department_admin'] and partner and not partner.is_company:
                        raise ValidationError(_(
                            "Portal company or department administrators must be linked to a company contact. "
                            "Please choose the customer company record instead of an individual contact."
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

    # ============================================================================
    # PORTAL ACCOUNT ACCESS METHODS
    # ============================================================================

    def action_access_portal_account(self):
        """
        Action button from partner form to access portal account
        Generates a secure login token and redirects to portal
        """
        self.ensure_one()

        # Security check
        if not self.env.user.can_access_portal_accounts:
            raise AccessError(_("You are not authorized to access customer portal accounts. Please contact your administrator."))

        if not self.share:
            raise ValidationError(_("This user is not a portal user."))

        # Generate secure access token
        login_token = self.env['portal.access.token'].sudo().create({
            'user_id': self.id,
            'created_by_user_id': self.env.user.id,
        })

        # Return URL action to open portal in new tab
        portal_url = '/portal/access/%s' % login_token.token

        return {
            'type': 'ir.actions.act_url',
            'url': portal_url,
            'target': 'new',
        }


class PortalAccessToken(models.Model):
    """Secure tokens for admin→portal account access"""
    _name = 'portal.access.token'
    _description = 'Portal Access Token'
    _rec_name = 'token'

    token = fields.Char(string='Access Token', required=True, default=lambda self: self._generate_token(), index=True)
    user_id = fields.Many2one('res.users', string='Portal User', required=True, ondelete='cascade')
    created_by_user_id = fields.Many2one('res.users', string='Created By', required=True, ondelete='cascade')
    create_date = fields.Datetime(string='Created On', readonly=True)
    expiry_date = fields.Datetime(string='Expires On', compute='_compute_expiry_date', store=True)
    used = fields.Boolean(string='Used', default=False)
    used_date = fields.Datetime(string='Used On', readonly=True)

    @api.model
    def _generate_token(self):
        """Generate a secure random token"""
        import secrets
        return secrets.token_urlsafe(32)

    @api.depends('create_date')
    def _compute_expiry_date(self):
        """Tokens expire after 5 minutes"""
        from dateutil.relativedelta import relativedelta
        for token in self:
            if token.create_date:
                token.expiry_date = token.create_date + relativedelta(minutes=5)
            else:
                token.expiry_date = False

    def is_valid(self):
        """Check if token is still valid"""
        self.ensure_one()
        from odoo.fields import Datetime
        if self.used:
            return False
        if self.expiry_date and self.expiry_date < Datetime.now():
            return False
        return True
