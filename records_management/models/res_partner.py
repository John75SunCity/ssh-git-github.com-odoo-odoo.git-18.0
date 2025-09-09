from odoo import models, fields, api, _
from odoo.exceptions import UserError


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

    destruction_address_id = fields.Many2one('res.partner', string='Destruction Address')

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
        'unlock.service.history',
        'partner_id',
        string="Unlock Service History",
        help="Past unlock / service events performed for this partner."
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

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('department_ids')
    def _compute_department_count(self):
        """Computes the number of departments associated with this partner."""
        for partner in self:
            partner.department_count = len(partner.department_ids)

    def _compute_records_stats(self):
        """Computes the count of containers and documents for the partner.

        This method is optimized for batch computation using _read_group for efficiency,
        avoiding per-record searches and improving performance.
        """
        container_data = self.env['records.container']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )
        document_data = self.env['records.document']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )

        container_map = {item['partner_id'][0]: item['__count'] for item in container_data}
        document_map = {item['partner_id'][0]: item['__count'] for item in document_data}

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
        'unlock_service_history_ids.cost',
        'unlock_service_history_ids.partner_id'
    )
    def _compute_unlock_service_stats(self):
        """Compute unlock service counters and monetary totals.

        Counts only completed or invoiced services as historical events contributing to totals.
        """
        if not self.exists():
            return
        services = self.env['unlock.service.history']._read_group(
            [('partner_id', 'in', self.ids), ('state', 'in', ['completed', 'invoiced'])],
            ['partner_id'],
            ['__count', 'cost:sum']
        )
        svc_count_map = {d['partner_id'][0]: d['__count'] for d in services}
        svc_cost_map = {d['partner_id'][0]: d.get('cost', 0.0) for d in services}
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
        """Open unlock.service.history records for this partner/contact."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Unlock Services'),
            'res_model': 'unlock.service.history',
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
