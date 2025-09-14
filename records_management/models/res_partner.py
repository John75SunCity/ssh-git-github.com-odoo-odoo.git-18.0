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

    negotiated_rates_count = fields.Integer(
        string="Negotiated Rates Count",
        compute='_compute_negotiated_rates_count',
        help="Number of negotiated rates for this customer"
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

    # ============================================================================
    # TRANSITORY FIELD CONFIGURATION FIELDS
    # ============================================================================
    transitory_field_config_id = fields.Many2one(
        'transitory.field.config',
        string="Transitory Field Configuration",
        help="Configuration for transitory fields display"
    )
    field_label_config_id = fields.Many2one(
        'field.label.config',
        string="Field Label Configuration",
        help="Configuration for field labels"
    )
    allow_transitory_items = fields.Boolean(
        string="Allow Transitory Items",
        default=False,
        help="Whether this partner can have transitory items"
    )
    max_transitory_items = fields.Integer(
        string="Max Transitory Items",
        default=0,
        help="Maximum number of transitory items allowed"
    )
    active_transitory_items = fields.Integer(
        string="Active Transitory Items",
        compute='_compute_transitory_stats',
        help="Number of currently active transitory items"
    )
    total_transitory_items = fields.Integer(
        string="Total Transitory Items",
        compute='_compute_transitory_stats',
        help="Total number of transitory items ever created"
    )
    customized_label_count = fields.Integer(
        string="Customized Label Count",
        compute='_compute_transitory_stats',
        help="Number of customized labels"
    )
    required_field_count = fields.Integer(
        string="Required Field Count",
        compute='_compute_transitory_stats',
        help="Number of required fields in configuration"
    )
    visible_field_count = fields.Integer(
        string="Visible Field Count",
        compute='_compute_transitory_stats',
        help="Number of visible fields in configuration"
    )

    # Field requirement flags
    require_client_reference = fields.Boolean(string="Require Client Reference", default=False)
    require_confidentiality = fields.Boolean(string="Require Confidentiality", default=False)
    require_container_number = fields.Boolean(string="Require Container Number", default=False)
    require_content_description = fields.Boolean(string="Require Content Description", default=False)
    require_date_from = fields.Boolean(string="Require Date From", default=False)
    require_date_to = fields.Boolean(string="Require Date To", default=False)
    require_description = fields.Boolean(string="Require Description", default=False)
    require_destruction_date = fields.Boolean(string="Require Destruction Date", default=False)
    require_project_code = fields.Boolean(string="Require Project Code", default=False)
    require_record_type = fields.Boolean(string="Require Record Type", default=False)
    require_sequence_from = fields.Boolean(string="Require Sequence From", default=False)
    require_sequence_to = fields.Boolean(string="Require Sequence To", default=False)

    # Field display flags
    show_authorized_by = fields.Boolean(string="Show Authorized By", default=True)
    show_client_reference = fields.Boolean(string="Show Client Reference", default=True)
    show_compliance_notes = fields.Boolean(string="Show Compliance Notes", default=True)
    show_confidentiality = fields.Boolean(string="Show Confidentiality", default=True)
    show_container_number = fields.Boolean(string="Show Container Number", default=True)
    show_content_description = fields.Boolean(string="Show Content Description", default=True)
    show_created_by_dept = fields.Boolean(string="Show Created By Dept", default=True)
    show_date_ranges = fields.Boolean(string="Show Date Ranges", default=True)
    show_description = fields.Boolean(string="Show Description", default=True)
    show_destruction_date = fields.Boolean(string="Show Destruction Date", default=True)
    show_file_count = fields.Boolean(string="Show File Count", default=True)
    show_filing_system = fields.Boolean(string="Show Filing System", default=True)
    show_project_code = fields.Boolean(string="Show Project Code", default=True)
    show_record_type = fields.Boolean(string="Show Record Type", default=True)
    show_sequence_ranges = fields.Boolean(string="Show Sequence Ranges", default=True)
    show_size_estimate = fields.Boolean(string="Show Size Estimate", default=True)
    show_special_handling = fields.Boolean(string="Show Special Handling", default=True)
    show_weight_estimate = fields.Boolean(string="Show Weight Estimate", default=True)

    # Field labels (customizable)
    label_authorized_by = fields.Char(string="Label: Authorized By", default="Authorized By")
    label_client_reference = fields.Char(string="Label: Client Reference", default="Client Reference")
    label_compliance_notes = fields.Char(string="Label: Compliance Notes", default="Compliance Notes")
    label_confidentiality = fields.Char(string="Label: Confidentiality", default="Confidentiality")
    label_container_number = fields.Char(string="Label: Container Number", default="Container Number")
    label_content_description = fields.Char(string="Label: Content Description", default="Content Description")
    label_created_by_dept = fields.Char(string="Label: Created By Dept", default="Created By Department")
    label_date_from = fields.Char(string="Label: Date From", default="Date From")
    label_date_to = fields.Char(string="Label: Date To", default="Date To")
    label_destruction_date = fields.Char(string="Label: Destruction Date", default="Destruction Date")
    label_file_count = fields.Char(string="Label: File Count", default="File Count")
    label_filing_system = fields.Char(string="Label: Filing System", default="Filing System")
    label_folder_type = fields.Char(string="Label: Folder Type", default="Folder Type")
    label_hierarchy_display = fields.Char(string="Label: Hierarchy Display", default="Hierarchy Display")
    label_item_description = fields.Char(string="Label: Item Description", default="Item Description")
    label_parent_container = fields.Char(string="Label: Parent Container", default="Parent Container")
    label_project_code = fields.Char(string="Label: Project Code", default="Project Code")
    label_record_type = fields.Char(string="Label: Record Type", default="Record Type")
    label_sequence_from = fields.Char(string="Label: Sequence From", default="Sequence From")
    label_sequence_to = fields.Char(string="Label: Sequence To", default="Sequence To")
    label_size_estimate = fields.Char(string="Label: Size Estimate", default="Size Estimate")
    label_special_handling = fields.Char(string="Label: Special Handling", default="Special Handling")
    label_weight_estimate = fields.Char(string="Label: Weight Estimate", default="Weight Estimate")

    # Additional fields from various views
    total_records_containers = fields.Integer(
        string="Total Records Containers",
        compute='_compute_records_stats',
        help="Total number of records containers"
    )
    key_restriction_status = fields.Selection([
        ('none', 'No Restrictions'),
        ('temporary', 'Temporary Restriction'),
        ('permanent', 'Permanent Restriction')
    ], string="Key Restriction Status", default='none')
    key_issuance_allowed = fields.Boolean(
        string="Key Issuance Allowed",
        default=True,
        help="Whether key issuance is allowed for this partner"
    )
    key_restriction_reason = fields.Text(
        string="Key Restriction Reason",
        help="Reason for key restriction if applicable"
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
            partner.total_records_containers = partner.container_count  # Same as container_count

    def _compute_negotiated_rates_count(self):
        """Compute the count of negotiated rates for the partner."""
        if not self.env['customer.negotiated.rate']._table_exists():
            for partner in self:
                partner.negotiated_rates_count = 0
            return

        rates_data = self.env['customer.negotiated.rate']._read_group(
            [('partner_id', 'in', self.ids)],
            ['partner_id'],
            ['__count']
        )
        rates_map = {item['partner_id'][0]: item['__count'] for item in rates_data}

        for partner in self:
            partner.negotiated_rates_count = rates_map.get(partner.id, 0)

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

    def _compute_transitory_stats(self):
        """Compute transitory field configuration statistics"""
        for partner in self:
            # Initialize default values
            partner.active_transitory_items = 0
            partner.total_transitory_items = 0
            partner.customized_label_count = 0
            partner.required_field_count = 0
            partner.visible_field_count = 0

            # Count required fields
            required_fields = [
                partner.require_client_reference,
                partner.require_confidentiality,
                partner.require_container_number,
                partner.require_content_description,
                partner.require_date_from,
                partner.require_date_to,
                partner.require_description,
                partner.require_destruction_date,
                partner.require_project_code,
                partner.require_record_type,
                partner.require_sequence_from,
                partner.require_sequence_to
            ]
            partner.required_field_count = sum(1 for req in required_fields if req)

            # Count visible fields
            visible_fields = [
                partner.show_authorized_by,
                partner.show_client_reference,
                partner.show_compliance_notes,
                partner.show_confidentiality,
                partner.show_container_number,
                partner.show_content_description,
                partner.show_created_by_dept,
                partner.show_date_ranges,
                partner.show_description,
                partner.show_destruction_date,
                partner.show_file_count,
                partner.show_filing_system,
                partner.show_project_code,
                partner.show_record_type,
                partner.show_sequence_ranges,
                partner.show_size_estimate,
                partner.show_special_handling,
                partner.show_weight_estimate
            ]
            partner.visible_field_count = sum(1 for vis in visible_fields if vis)

            # Count customized labels (non-default values)
            default_labels = {
                'label_authorized_by': 'Authorized By',
                'label_client_reference': 'Client Reference',
                'label_compliance_notes': 'Compliance Notes',
                'label_confidentiality': 'Confidentiality',
                'label_container_number': 'Container Number',
                'label_content_description': 'Content Description',
                'label_created_by_dept': 'Created By Department',
                'label_date_from': 'Date From',
                'label_date_to': 'Date To',
                'label_destruction_date': 'Destruction Date',
                'label_file_count': 'File Count',
                'label_filing_system': 'Filing System',
                'label_folder_type': 'Folder Type',
                'label_hierarchy_display': 'Hierarchy Display',
                'label_item_description': 'Item Description',
                'label_parent_container': 'Parent Container',
                'label_project_code': 'Project Code',
                'label_record_type': 'Record Type',
                'label_sequence_from': 'Sequence From',
                'label_sequence_to': 'Sequence To',
                'label_size_estimate': 'Size Estimate',
                'label_special_handling': 'Special Handling',
                'label_weight_estimate': 'Weight Estimate'
            }

            customized_count = 0
            for field_name, default_value in default_labels.items():
                if hasattr(partner, field_name):
                    current_value = getattr(partner, field_name)
                    if current_value and current_value != default_value:
                        customized_count += 1
            partner.customized_label_count = customized_count

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

    def action_view_negotiated_rates(self):
        """Opens the tree view of negotiated rates related to this partner."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Negotiated Rates'),
            'res_model': 'customer.negotiated.rate',
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
