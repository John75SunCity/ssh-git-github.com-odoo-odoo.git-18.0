from odoo import models, fields, api, _
from odoo.exceptions import UserError


class MobileBinKeyWizard(models.TransientModel):
    _name = 'mobile.bin.key.wizard'
    _description = 'Mobile Bin Key Management Wizard'
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Operation Reference", readonly=True, default=lambda self: _('New Mobile Operation'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Technician', default=lambda self: self.env.user)
    employee_id = fields.Many2one('hr.employee', string='Employee', readonly=True)

    action_type = fields.Selection([
        ('access', 'Standard Access'),
        ('emergency_access', 'Emergency Access'),
        ('quick_lookup', 'Quick Lookup'),
        ('inspect', 'Inspect Bin'),
        ('audit_check', 'Audit Check')
    ], string='Action Type', required=True, default='access')

    priority = fields.Selection([('normal', 'Normal'), ('urgent', 'Urgent')], string='Priority', default='normal')
    mobile_session_id = fields.Char(string='Mobile Session ID')
    device_info = fields.Char(string='Device Info')

    bin_key_id = fields.Many2one('bin.key', string='Bin Key')
    bin_location_id = fields.Many2one('records.location', string='Bin Location')
    bin_number = fields.Char(string='Bin Number')
    key_code = fields.Char(string='Key Code')
    access_level_required = fields.Selection([
        ('standard', 'Standard'),
        ('restricted', 'Restricted'),
        ('confidential', 'Confidential'),
        ('secure_vault', 'Secure Vault')
    ], string='Required Access Level')

    partner_id = fields.Many2one('res.partner', string='Customer')
    operation_reason = fields.Selection([
        ('retrieval', 'Item Retrieval'),
        ('deposit', 'Item Deposit'),
        ('maintenance', 'Maintenance'),
        ('audit', 'Audit'),
        ('emergency', 'Emergency')
    ], string='Reason for Operation')
    operation_description = fields.Text(string='Operation Description')

    authorization_required = fields.Boolean(string='Authorization Required')
    authorized_by_id = fields.Many2one('res.users', string='Authorized By', readonly=True)
    approval_date = fields.Datetime(string='Approval Date', readonly=True)

    operation_start_time = fields.Datetime(string='Operation Start Time', readonly=True)
    operation_end_time = fields.Datetime(string='Operation End Time', readonly=True)
    actual_duration = fields.Float(string='Actual Duration (Hours)', compute='_compute_operation_duration', store=True)

    billable = fields.Boolean(string='Is Billable')
    service_charge = fields.Float(string='Service Charge')

    # UI Control Fields
    show_lookup_results = fields.Boolean(string='Show Lookup Results')
    show_emergency_options = fields.Boolean(string='Show Emergency Options')

    # Lookup Fields
    lookup_query = fields.Char(string='Search Query')
    lookup_results = fields.Text(string='Lookup Results', readonly=True)
    containers_found = fields.Integer(string='Containers Found', readonly=True)
    documents_found = fields.Integer(string='Documents Found', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('auth_pending', 'Pending Authorization'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', readonly=True)
    operation_notes = fields.Text(string='Operation Notes')

    # Compliance
    naid_compliance_check = fields.Boolean(string='NAID Compliance Check')
    audit_trail_created = fields.Boolean(string='Audit Trail Created', readonly=True)
    chain_of_custody_id = fields.Many2one('records.chain.of.custody', string='Chain of Custody Record', readonly=True)

    # ============================================================================
    # COMPUTE & ONCHANGE
    # ============================================================================
    @api.depends('operation_start_time', 'operation_end_time')
    def _compute_operation_duration(self):
        for wizard in self:
            if wizard.operation_start_time and wizard.operation_end_time:
                delta = wizard.operation_end_time - wizard.operation_start_time
                wizard.actual_duration = delta.total_seconds() / 3600.0
            else:
                wizard.actual_duration = 0.0

    @api.onchange('user_id')
    def _onchange_user_id(self):
        if self.user_id and self.user_id.employee_id:
            self.employee_id = self.user_id.employee_id

    @api.onchange('bin_key_id')
    def _onchange_bin_key_id(self):
        if self.bin_key_id:
            self.bin_location_id = self.bin_key_id.location_id
            self.bin_number = self.bin_key_id.bin_number
            self.access_level_required = self.bin_key_id.access_level

    @api.onchange('action_type')
    def _onchange_action_type(self):
        if self.action_type == 'emergency_access':
            self.priority = 'urgent'
            self.authorization_required = True
            self.show_emergency_options = True
        elif self.action_type == 'quick_lookup':
            self.show_lookup_results = True
            self.billable = False
        elif self.action_type in ['inspect', 'audit_check']:
            self.naid_compliance_check = True

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_operation(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Can only start draft operations."))
        if self.authorization_required and not self.authorized_by_id:
            raise UserError(_("Authorization is required before starting this operation."))
        if not self._check_access_permissions():
            raise UserError(_("You do not have sufficient access permissions for this operation."))

        self.write({
            'state': 'in_progress',
            'operation_start_time': fields.Datetime.now()
        })
        self._create_audit_log('operation_started')
        self.message_post(body=_("Mobile operation started by %s.", self.user_id.name))
        return self._return_mobile_interface()

    def action_complete_operation(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Can only complete operations that are in progress."))
        if self.naid_compliance_check and not self.operation_notes:
            raise UserError(_("Operation notes are required for compliance purposes."))

        self.write({
            'state': 'completed',
            'operation_end_time': fields.Datetime.now()
        })

        if self.naid_compliance_check:
            self._create_chain_of_custody_record()
        self._create_audit_log('operation_completed')
        self.message_post(body=_("Mobile operation completed successfully."))

        if self.billable:
            self._create_billing_record()
        return {'type': 'ir.actions.act_window_close'}

    def action_cancel_operation(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self._create_audit_log('operation_cancelled')
        self.message_post(body=_("Mobile operation cancelled."))
        return {'type': 'ir.actions.act_window_close'}

    def action_execute_lookup(self):
        self.ensure_one()
        if not self.lookup_query:
            raise UserError(_("Please enter search criteria for the lookup."))
        results = self._perform_database_lookup()
        self.write({
            'lookup_results': results.get('formatted_results', ''),
            'containers_found': results.get('containers_count', 0),
            'documents_found': results.get('documents_count', 0),
            'show_lookup_results': True
        })
        self._create_audit_log('lookup_performed')
        return self._return_mobile_interface()

    def action_request_authorization(self):
        self.ensure_one()
        self.state = 'auth_pending'
        manager_group = self.env.ref('records_management.group_records_manager', raise_if_not_found=False)
        if not manager_group:
            raise UserError(_("The 'Records Manager' security group could not be found."))

        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Authorization Required: %s", self.name),
            note=_("Mobile operation '%s' by %s requires supervisor authorization.")
            % (self.action_type, self.user_id.name),
            user_id=manager_group.users[0].id if manager_group.users else self.env.ref("base.user_admin").id,
        )
        self.message_post(body=_("Authorization requested from supervisors."))
        return self._return_mobile_interface()

    def action_authorize_operation(self):
        self.ensure_one()
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only supervisors can authorize operations."))
        self.write({
            'authorized_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'state': 'draft'
        })
        self._create_audit_log('operation_authorized')
        self.message_post(body=_("Operation authorized by %s.", self.env.user.name))
        return self._return_mobile_interface()

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _check_access_permissions(self):
        self.ensure_one()
        # This is a simplified placeholder. Real logic would be more robust.
        if self.access_level_required == 'secure_vault':
            return self.env.user.has_group('records_management.group_records_manager')
        return True

    def _perform_database_lookup(self):
        self.ensure_one()
        query = self.lookup_query.strip()
        results = {'containers_count': 0, 'documents_count': 0, 'formatted_results': ''}
        if not query:
            return results

        containers = self.env['records.container'].search([('name', 'ilike', query)], limit=10)
        documents = self.env['records.document'].search([('name', 'ilike', query)], limit=10)
        results['containers_count'] = len(containers)
        results['documents_count'] = len(documents)

        lines = []
        if containers:
            lines.append(_("CONTAINERS FOUND (%d):", len(containers)))
            lines.extend([f"- {c.name} (Location: {c.location_id.name or 'N/A'})" for c in containers])
        if documents:
            lines.append(_("\nDOCUMENTS FOUND (%d):", len(documents)))
            lines.extend([f"- {d.name} (Container: {d.container_id.name or 'N/A'})" for d in documents])

        results['formatted_results'] = '\n'.join(lines) if lines else _("No results found.")
        return results

    def _create_audit_log(self, action):
        self.ensure_one()
        if 'naid.audit.log' in self.env:
            self.env['naid.audit.log'].create({
                'action_type': action,
                'user_id': self.env.user.id,
                'description': _("Mobile bin key operation: %s on bin %s") % (action, self.bin_number or 'N/A'),
                'naid_compliant': self.naid_compliance_check,
            })
            self.audit_trail_created = True

    def _create_chain_of_custody_record(self):
        self.ensure_one()
        if 'records.chain.of.custody' in self.env:
            custody = self.env["records.chain.of.custody"].create(
                {
                    "name": _("Mobile Operation: %s", self.name),
                    "event_type": "mobile_access",
                    "responsible_user_id": self.user_id.id,
                    "location_id": self.bin_location_id.id if self.bin_location_id else False,
                    "description": self.operation_description or "",
                }
            )
            self.chain_of_custody_id = custody.id

    def _create_billing_record(self):
        self.ensure_one()
        if not self.billable or not self.service_charge > 0 or not self.partner_id:
            return
        # Simplified invoice creation. A real implementation would use products.
        self.env["account.move"].create(
            {
                "partner_id": self.partner_id.id,
                "move_type": "out_invoice",
                "invoice_line_ids": [
                    (
                        0,
                        0,
                        {
                            "name": _("Mobile Bin Key Service: %s", self.action_type),
                            "quantity": 1,
                            "price_unit": self.service_charge,
                        },
                    )
                ],
            }
        )

    def _return_mobile_interface(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _("Mobile Bin Key Operation"),
            'res_model': 'mobile.bin.key.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name') or vals.get('name') == _('New Mobile Operation'):
                vals['name'] = self.env['ir.sequence'].next_by_code('mobile.bin.key.wizard') or _('New Mobile Operation')
        return super().create(vals_list)

    def name_get(self):
        result = []
        for wizard in self:
            name = wizard.name
            if wizard.action_type and wizard.state:
                action_label = dict(wizard._fields['action_type'].selection).get(wizard.action_type, '')
                state_label = dict(wizard._fields['state'].selection).get(wizard.state, '')
                name = f"{name} - {action_label} [{state_label}]"
            result.append((wizard.id, name))
        return result
