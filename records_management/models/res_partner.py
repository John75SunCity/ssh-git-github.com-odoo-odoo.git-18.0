from odoo import models, fields, api, _
from odoo.exceptions import UserError, AccessError


class Company(models.Model):
    _inherit = 'res.company'

    # Records Management configurations
    records_management_enabled = fields.Boolean(
        string="Enable Records Management",
        default=True,
        help="Enable Records Management features for this company"
    )
    naid_member_id = fields.Char(
        string="NAID Member ID",
        help="Official NAID membership identifier for destruction certificates"
    )


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_customer = fields.Boolean(
        string="Is a Records Management Customer",
        default=False,
        help="Check this box if this partner is a customer of the records management services."
    )

    department_ids = fields.One2many(
        'records.department',
        'partner_id',
        string="Departments"
    )

    department_count = fields.Integer(
        string="Department Count",
        compute='_compute_department_count',
        store=True
    )

    container_count = fields.Integer(
        string="Container Count",
        compute='_compute_records_stats',
    )

    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_records_stats',
    )

    destruction_address_id = fields.Many2one(comodel_name='res.partner', string='Destruction Address')

    # =========================================================================
    # BIN KEY & UNLOCK SERVICE FIELDS (used by mobile_bin_key_wizard_views.xml)
    # =========================================================================
    has_bin_key = fields.Boolean(
        string="Has Active Bin Key",
        compute='_compute_bin_key_stats',
        store=True,
        help="Indicates whether this partner currently holds at least one active (assigned) bin key."
    )
    is_emergency_key_contact = fields.Boolean(
        string="Emergency Key Contact",
        help="Flag contact as an emergency key contact (manually managed)."
    )
    active_bin_key_count = fields.Integer(
        string="Active Bin Key Count",
        compute='_compute_bin_key_stats',
        store=True
    )
    key_issue_date = fields.Date(
        string="Most Recent Key Issue Date",
        compute='_compute_bin_key_stats',
        store=True,
        help="Date when the most recent key was issued to this partner."
    )
    total_bin_keys_issued = fields.Integer(
        string="Total Bin Keys Issued",
        compute='_compute_bin_key_stats',
        store=True
    )
    bin_key_history_ids = fields.One2many(
        'bin.key.history',
        'partner_id',
        string="Bin Key History",
        help="Historical key assignment events related to this partner."
    )

    unlock_service_history_ids = fields.One2many(
        'bin.unlock.service',
        'partner_id',
        string="Unlock Services",
        help="Unlock / service events performed for this partner (merged model)."
    )
    unlock_service_count = fields.Integer(
        string="Unlock Service Count",
        compute='_compute_unlock_service_stats',
        store=True
    )
    total_unlock_charges = fields.Monetary(
        string="Total Unlock Charges",
        compute='_compute_unlock_service_stats',
        store=True,
        currency_field='company_currency_id',
        help="Sum of billable unlock service costs for this partner."
    )
    company_currency_id = fields.Many2one(
        'res.currency',
        related='company_id.currency_id',
        string='Company Currency',
        readonly=True
    )

    # =========================================================================
    # KEY RESTRICTION – PARTNER-LEVEL SUMMARY FIELDS (used by partner views)
    # =========================================================================
    key_issuance_allowed = fields.Boolean(
        string="Key Issuance Allowed",
        compute='_compute_key_restriction_fields',
        search='_search_key_issuance_allowed',
        help="Indicates if this partner is allowed to be issued physical bin keys (derived from active restrictions)."
    )
    key_restriction_status = fields.Selection(
        [
            ('allowed', 'Allowed'),
            ('restricted', 'Restricted'),
        ],
        string='Key Restriction Status',
        compute='_compute_key_restriction_fields',
        search='_search_key_restriction_status',
        help="Convenience badge mapping based on key issuance policy."
    )
    key_restriction_reason = fields.Text(
        string='Restriction Reason',
        compute='_compute_key_restriction_fields',
        help="Reason captured on the most recent key restriction record."
    )
    key_restriction_date = fields.Date(
        string='Restriction Date',
        compute='_compute_key_restriction_fields',
        search='_search_key_restriction_date'
    )
    key_restriction_approved_by = fields.Many2one(
        comodel_name='res.users',
        string='Approved By',
        compute='_compute_key_restriction_fields'
    )
    key_restriction_notes = fields.Text(
        string='Restriction Notes',
        compute='_compute_key_restriction_fields'
    )
    key_restriction_history_ids = fields.One2many(
        comodel_name='res.partner.key.restriction',
        inverse_name='partner_id',
        string='Key Restriction History'
    )
    key_restriction_history_count = fields.Integer(
        string='Restriction History Count',
        compute='_compute_key_restriction_history_count'
    )
    restricted_unlock_count = fields.Integer(
        string='Restricted Unlock Count',
        compute='_compute_restricted_unlock_count',
        help="Number of unlock services performed while customer was restricted."
    )
    # Recent restriction helper (avoid Python expressions in search filter domains)
    recently_restricted = fields.Boolean(
        string='Recently Restricted (30d)',
        compute='_compute_recently_restricted',
        store=True,
        help="Indicates partner has an effective key restriction whose effective date is within the last 30 days. Stored for fast filtering; updated whenever restriction fields recompute."
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('department_ids')
    def _compute_department_count(self):
        """Computes the number of departments associated with this partner."""
        for partner in self:
            partner.department_count = len(partner.department_ids)

    def _compute_records_stats(self):
        """Compute container_count & document_count in batch.

        Previous implementation misused _read_group (passing ['__count'] as the groupby
        parameter) which resulted in low-level tuple structures and a runtime TypeError
        when treating each item as a dict. We now use the public read_group API with
        proper arguments (domain, fields, groupby) and robustly extract the partner id.
        """
        if not self:
            return

        # read_group automatically supplies '__count' for each grouped row
        container_rows = self.env['records.container'].read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['partner_id']
        )
        document_rows = self.env['records.document'].read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['partner_id']
        )

        def build_map(rows):
            result = {}
            for row in rows or []:
                # row['partner_id'] is usually (id, display_name) for m2o group
                raw = row.get('partner_id')
                if not raw:
                    continue
                pid = raw[0] if isinstance(raw, (list, tuple)) else raw
                result[pid] = row.get('__count', 0)
            return result

        container_map = build_map(container_rows)
        document_map = build_map(document_rows)

        for partner in self:
            partner.container_count = container_map.get(partner.id, 0)
            partner.document_count = document_map.get(partner.id, 0)

    # =========================================================================
    # COMPUTE: BIN KEY STATS
    # =========================================================================
    @api.depends('bin_key_history_ids.event_date', 'bin_key_history_ids.event_type')
    def _compute_bin_key_stats(self):
        """Aggregate bin key related statistics in batch for performance.

        Logic:
          - Active keys: bin.key records where key_holder_id == partner AND state = 'assigned'.
          - Most recent issue date: max(issue_date) across active/assigned keys.
          - Total issued: count of bin.key.history events with event_type in ('assign','create') for partner.
        """
        if not self.exists():
            return
        # Active key counts & latest issue date
        # Correct _read_group usage: groupby fields list, then aggregated specs list
        keys_data = self.env['bin.key']._read_group(
            [('key_holder_id', 'in', self.ids), ('state', '=', 'assigned')],
            ['key_holder_id'],
            ['issue_date:max']
        )
        active_count_map = {d['key_holder_id'][0]: d['__count'] for d in keys_data}
        # Returned dictionary uses aggregated field base name for :max (issue_date)
        latest_issue_map = {d['key_holder_id'][0]: d.get('issue_date') for d in keys_data}

        # Total issued from history
        history_data = self.env['bin.key.history']._read_group(
            [('partner_id', 'in', self.ids), ('event_type', 'in', ['assign', 'create'])],
            ['partner_id'],
            ['__count']
        )
        total_issued_map = {d['partner_id'][0]: d['__count'] for d in history_data}

        for partner in self:
            active_count = active_count_map.get(partner.id, 0)
            partner.active_bin_key_count = active_count
            partner.has_bin_key = bool(active_count)
            partner.key_issue_date = latest_issue_map.get(partner.id)
            partner.total_bin_keys_issued = total_issued_map.get(partner.id, 0)

    @api.depends(
        'unlock_service_history_ids.state',
        'unlock_service_history_ids.total_cost',
        'unlock_service_history_ids.partner_id'
    )
    def _compute_unlock_service_stats(self):
        """Compute unlock service counters and monetary totals.

        Counts only completed or invoiced services as historical events contributing to totals.
        """
        if not self.exists():
            return
        # Aggregate unified unlock service records
        services = self.env['bin.unlock.service']._read_group(
            [('partner_id', 'in', self.ids), ('state', 'in', ['completed', 'invoiced'])],
            ['partner_id'],
            ['__count', 'total_cost:sum']
        )
        svc_count_map = {d['partner_id'][0]: d['__count'] for d in services}
        svc_cost_map = {d['partner_id'][0]: d.get('total_cost', 0.0) for d in services}
        for partner in self:
            partner.unlock_service_count = svc_count_map.get(partner.id, 0)
            partner.total_unlock_charges = svc_cost_map.get(partner.id, 0.0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_departments(self):
        """Opens the tree view of departments related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Departments'),
            'res_model': 'records.department',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
                'default_company_id': self.company_id.id or self.env.company.id,
            }
        }

    def action_view_containers(self):
        """Opens the tree view of containers related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers'),
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    def action_view_documents(self):
        """Opens the tree view of documents related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Documents'),
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {'default_partner_id': self.id}
        }

    # --------------------------------------------------------------
    # NEW: Bin Key / Unlock Service action handlers (used in views)
    # --------------------------------------------------------------
    def action_view_bin_keys(self):
        """Open bin.key records for this contact as key holder.

        Provides a simple list/form view for active and historical keys.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bin Keys'),
            'res_model': 'bin.key',
            'view_mode': 'tree,form',
            'domain': [('key_holder_id', '=', self.id)],
            'context': {
                'default_key_holder_id': self.id,
                'search_default_assigned': 1,
            }
        }

    def action_view_unlock_services(self):
        """Open unified bin.unlock.service records for this partner/contact."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Services'),
            'res_model': 'bin.unlock.service',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            }
        }

    # --------------------------------------------------------------
    # Missing Button Action: Issue New Bin Key (stub implementation)
    # --------------------------------------------------------------
    def action_issue_new_key(self):
        """Wizard entry point for issuing a new bin key to this contact.

        This stub returns an act_window opening the mobile.bin.key.wizard
        pre-configured for issuing a new key. It mirrors the existing quick
        access server action but ensures the view button resolves properly.
        Future enhancements may:
          - Pre-populate additional defaults (e.g., default_issue_location)
          - Enforce security or eligibility checks
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Issue Bin Key'),
            'res_model': 'mobile.bin.key.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_action_type': 'issue_new',
                'default_contact_id': self.id,
                'default_customer_company_id': self.parent_id.id if self.parent_id else (self.company_id.partner_id.id if self.company_id and self.company_id.partner_id else False),
            }
        }

    # --------------------------------------------------------------
    # Additional Bin Key Actions referenced by partner form buttons
    # --------------------------------------------------------------
    def action_view_active_key(self):
        """Open the currently assigned (active) key for this contact.

        Behaviour:
          - If no active key: raise a friendly error.
          - If exactly one active key: open its form view directly.
          - If multiple active keys (rare but supported): open list filtered to assigned.
        """
        self.ensure_one()
        assigned_keys = self.env['bin.key'].search([
            ('key_holder_id', '=', self.id),
            ('state', '=', 'assigned')
        ])
        if not assigned_keys:
            raise UserError(_("No active (assigned) bin key found for this contact."))
        if len(assigned_keys) == 1:
            key = assigned_keys[0]
            return {
                'type': 'ir.actions.act_window',
                'name': _('Active Bin Key'),
                'res_model': 'bin.key',
                'res_id': key.id,
                'view_mode': 'form',
                'target': 'current',
            }
        # Multiple keys: fallback to list view
        return {
            'type': 'ir.actions.act_window',
            'name': _('Active Bin Keys'),
            'res_model': 'bin.key',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', assigned_keys.ids)],
            'context': {
                'search_default_assigned': 1,
                'default_key_holder_id': self.id,
            }
        }

    def action_return_key(self):
        """Partner-level helper to process key return.

        Logic mirrors action_view_active_key to select the key. We do NOT
        directly change state here to avoid unintended side-effects. Instead:
          - If single assigned key: invoke its action_return_key() method.
          - If multiple: open filtered list so user can choose which key to return.
        """
        self.ensure_one()
        assigned_keys = self.env['bin.key'].search([
            ('key_holder_id', '=', self.id),
            ('state', '=', 'assigned')
        ])
        if not assigned_keys:
            raise UserError(_("No assigned key to return for this contact."))
        if len(assigned_keys) == 1:
            # Delegate to key model method (ensures history + chatter logging)
            assigned_keys.action_return_key()
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Bin Key Returned'),
                    'message': _('The active bin key has been marked as returned.'),
                    'sticky': False,
                    'type': 'success'
                }
            }
        # Multiple keys: open list for manual selection / action
        return {
            'type': 'ir.actions.act_window',
            'name': _('Return Bin Key'),
            'res_model': 'bin.key',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', assigned_keys.ids)],
            'context': {
                'search_default_assigned': 1,
                'default_key_holder_id': self.id,
            }
        }

    def action_report_lost_key(self):
        """Partner-level helper to mark an active key as lost.

        Behaviour parallels return logic. If a single key is active we call
        action_mark_lost on it (which opens replacement wizard). If multiple
        keys are active we present the list for user selection.
        """
        self.ensure_one()
        assigned_keys = self.env['bin.key'].search([
            ('key_holder_id', '=', self.id),
            ('state', '=', 'assigned')
        ])
        if not assigned_keys:
            raise UserError(_("No active key to mark as lost for this contact."))
        if len(assigned_keys) == 1:
            return assigned_keys.action_mark_lost()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark Key as Lost'),
            'res_model': 'bin.key',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', assigned_keys.ids)],
            'context': {
                'search_default_assigned': 1,
                'default_key_holder_id': self.id,
                'bin_key_mark_lost_mode': True,
            }
        }

    # =========================================================================
    # COMPUTES: KEY RESTRICTIONS
    # =========================================================================
    def _get_latest_key_restriction_by_partner(self):
        """Return a dict partner_id -> latest res.partner.key.restriction (by effective_date desc, id desc).

        We consider records in any state but prefer an 'active' restriction when present.
        """
        result = {}
        if not self:
            return result
        # Fetch all restrictions for these partners ordered by effective_date desc, id desc
        restrictions = self.env['res.partner.key.restriction'].sudo().search(
            [('partner_id', 'in', self.ids)], order='effective_date desc, id desc'
        )
        for restr in restrictions:
            pid = restr.partner_id.id
            if pid not in result:
                result[pid] = restr
            else:
                # Prefer active over any other state
                if result[pid].state != 'active' and restr.state == 'active':
                    result[pid] = restr
        return result

    def _compute_key_restriction_fields(self):
        latest_map = self._get_latest_key_restriction_by_partner()
        for partner in self:
            restr = latest_map.get(partner.id)
            # Default: allowed when no restriction exists
            allowed = True
            status = 'allowed'
            reason = False
            date_val = False
            approved_by = False
            notes = False
            if restr:
                # If an active restriction exists and its flag is False, partner is restricted
                allowed = bool(restr.key_issuance_allowed)
                status = 'allowed' if allowed else 'restricted'
                reason = restr.restriction_reason
                date_val = restr.effective_date
                approved_by = restr.user_id
                notes = restr.notes
            partner.key_issuance_allowed = allowed
            partner.key_restriction_status = status
            partner.key_restriction_reason = reason
            partner.key_restriction_date = date_val
            partner.key_restriction_approved_by = approved_by
            partner.key_restriction_notes = notes

    def _compute_key_restriction_history_count(self):
        counts = self.env['res.partner.key.restriction']._read_group(
            [('partner_id', 'in', self.ids)], ['partner_id'], ['__count']
        )
        count_map = {d['partner_id'][0]: d['__count'] for d in counts}
        for partner in self:
            partner.key_restriction_history_count = count_map.get(partner.id, 0)

    def _compute_restricted_unlock_count(self):
        if not self:
            return
        try:
            # Determine restricted partners using same logic as key issuance search helper
            restricted_partner_ids = set(self.env['res.partner.key.restriction'].sudo().search([
                ('key_issuance_allowed', '=', False),
                ('partner_id', 'in', self.ids),
                ('state', 'in', ['active', 'draft'])
            ]).mapped('partner_id').ids)

            if restricted_partner_ids:
                rows = self.env['bin.unlock.service']._read_group(
                    [('partner_id', 'in', list(restricted_partner_ids))],
                    ['partner_id'], ['__count']
                )
                cnt_map = {r['partner_id'][0]: r['__count'] for r in rows}
            else:
                cnt_map = {}
        except AccessError:
            # Defensive fallback: if ACL load order or test harness context prevents
            # reading bin.unlock.service, suppress the AccessError and treat as zero.
            cnt_map = {}
        for partner in self:
            partner.restricted_unlock_count = cnt_map.get(partner.id, 0)

    @api.depends('key_restriction_date', 'key_issuance_allowed')
    def _compute_recently_restricted(self):
        """A partner is 'recently restricted' if:
        - key_issuance_allowed is False, and
        - key_restriction_date is set and within the last 30 days (inclusive)

        This replaces dynamic Python expressions in XML domains which are not
        evaluated client-side (caused clickbot test failure)."""
        from datetime import date, timedelta
        today = date.today()
        threshold = today - timedelta(days=30)
        for partner in self:
            recent = False
            if not partner.key_issuance_allowed and partner.key_restriction_date:
                try:
                    if partner.key_restriction_date >= threshold:
                        recent = True
                except Exception:
                    # Defensive: if date comparison fails, leave recent False
                    recent = False
            partner.recently_restricted = recent

    # =========================================================================
    # SEARCH HELPERS for computed (non-stored) fields used in domains
    # =========================================================================
    def _search_key_issuance_allowed(self, operator, value):
        # Build set of restricted partners: active restriction with key_issuance_allowed = False
        restricted_partners = self.env['res.partner.key.restriction'].sudo().search([
            ('key_issuance_allowed', '=', False),
            ('partner_id', '!=', False),
            ('state', 'in', ['active', 'draft'])
        ]).mapped('partner_id').ids
        if operator in ('=', '=='):
            if value:
                return [('id', 'not in', restricted_partners)]
            return [('id', 'in', restricted_partners)]
        if operator in ('!=', '<>'):
            if value:
                return [('id', 'in', restricted_partners)]
            return [('id', 'not in', restricted_partners)]
        # Fallback conservative domain
        return [('id', '!=', 0)]

    def _search_key_restriction_status(self, operator, value):
        # Map status to boolean value of allowed
        if isinstance(value, str):
            value = value.lower()
        if operator in ('=', '=='):
            if value == 'allowed':
                return self._search_key_issuance_allowed('=', True)
            if value == 'restricted':
                return self._search_key_issuance_allowed('=', False)
        if operator in ('!=', '<>'):
            if value == 'allowed':
                return self._search_key_issuance_allowed('=', False)
            if value == 'restricted':
                return self._search_key_issuance_allowed('=', True)
        return [('id', '!=', 0)]

    def _search_key_restriction_date(self, operator, value):
        # Partners that have a restriction with effective_date OP value
        restrs = self.env['res.partner.key.restriction'].sudo().search([
            ('effective_date', operator, value)
        ])
        return [('id', 'in', restrs.mapped('partner_id').ids)]

    # =========================================================================
    # ACTIONS: UI Buttons in partner view for key restrictions
    # =========================================================================
    def action_restrict_key_issuance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Key Restriction'),
            'res_model': 'key.restriction.management.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_action': 'restrict',
            }
        }

    def action_allow_key_issuance(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Allow Key Issuance'),
            'res_model': 'key.restriction.management.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.id,
                'default_action': 'allow',
            }
        }

    def action_view_key_history(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Key Restriction History'),
            'res_model': 'res.partner.key.restriction',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.id)],
            'context': {
                'default_partner_id': self.id,
            }
        }

    def action_go_to_portal_account(self):
        """
        Action to access customer's portal account
        Available to users with 'can_access_portal_accounts' permission
        """
        self.ensure_one()
        
        # Security check
        if not self.env.user.can_access_portal_accounts:
            raise AccessError(_("You are not authorized to access customer portal accounts. Please contact your administrator."))
        
        # Find portal user for this partner
        portal_user = self.env['res.users'].search([
            ('partner_id', '=', self.id),
            ('share', '=', True)  # Portal users have share=True
        ], limit=1)
        
        if not portal_user:
            raise UserError(_(
                "No portal user found for %s.\n\n"
                "Please create a portal user first:\n"
                "1. Go to Settings > Users & Companies > Users\n"
                "2. Create a new user\n"
                "3. Select this customer as 'Related Partner'\n"
                "4. Grant portal access"
            ) % self.name)
        
        # Use the action from res.users
        return portal_user.action_access_portal_account()
