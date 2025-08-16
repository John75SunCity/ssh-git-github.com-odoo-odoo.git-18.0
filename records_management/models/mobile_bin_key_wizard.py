# -*- coding: utf-8 -*-

Mobile Bin Key Management Wizard

Mobile wizard for field service technicians to manage bin access, perform:
    pass
quick lookups, and execute bin-related operations with comprehensive audit
trails and NAID compliance integration.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MobileBinKeyWizard(models.TransientModel):

        Mobile Bin Key Management Wizard
    
    Provides mobile-friendly interface for field technicians to perform:
        bin access operations, conduct quick lookups, and manage physical
    key access with complete audit trail integration.


    _name = "mobile.bin.key.wizard"
    _description = "Mobile Bin Key Management Wizard"
    _order = "create_date desc"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Wizard Reference",
        required=True,
        ,
    default=lambda self: _("New Mobile Operation"),
        help="Reference for this mobile operation":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Technician",
        default=lambda self: self.env.user,
        required=True,
        help="Field technician performing the operation"
    

    employee_id = fields.Many2one(
        "hr.employee",
        string="Employee",
        help="Employee record for the technician":
    

        # ============================================================================
    # OPERATION CONFIGURATION
        # ============================================================================
    ,
    action_type = fields.Selection([))
        ('unlock', 'Unlock Bin'),
        ('lock', 'Lock Bin'),
        ('inspect', 'Inspect Contents'),
        ('relocate', 'Relocate Bin'),
        ('service', 'Service Request'),
        ('quick_lookup', 'Quick Lookup'),
        ('emergency_access', 'Emergency Access'),
        ('audit_check', 'Audit Check')
    
        help="Type of operation to perform"

    priority = fields.Selection([))
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    

    mobile_session_id = fields.Char(
        string="Mobile Session ID",
        help="Unique session identifier for mobile app integration":
    

    device_info = fields.Char(
        string="Device Information",
        help="Mobile device information for audit trail":
    

        # ============================================================================
    # BIN AND KEY INFORMATION
        # ============================================================================
    bin_key_id = fields.Many2one(
        "bin.key",
        string="Bin Key",
        help="Primary bin key for the operation":
    

    bin_location_id = fields.Many2one(
        "records.location",
        string="Bin Location",
        help="Location of the bin being accessed"
    

    bin_number = fields.Char(
        string="Bin Number",
        help="Physical bin identifier"
    

    key_code = fields.Char(
        string="Key Code",
        help="Physical key code or electronic access code"
    

    ,
    access_level_required = fields.Selection([))
        ('standard', 'Standard Access'),
        ('restricted', 'Restricted Access'),
        ('confidential', 'Confidential Access'),
        ('secure_vault', 'Secure Vault Access')
    

        # ============================================================================
    # CUSTOMER AND CONTACT INFORMATION
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        help="Customer associated with the bin access"
    

    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        help="Primary customer contact for this operation":
    

    emergency_contact_id = fields.Many2one(
        "res.partner",
        string="Emergency Contact",
        help="Emergency contact for urgent situations":
    

    contact_name = fields.Char(
        string="Contact Name",
        help="Name of the person requesting access"
    

    contact_phone = fields.Char(
        string="Contact Phone",
        help="Phone number for verification":
    

    contact_email = fields.Char(
        string="Contact Email",
        help="Email address for notifications":
    

        # ============================================================================
    # OPERATION DETAILS
        # ============================================================================
    ,
    operation_reason = fields.Selection([))
        ('document_retrieval', 'Document Retrieval'),
        ('container_inspection', 'Container Inspection'),
        ('emergency_access', 'Emergency Access'),
        ('routine_maintenance', 'Routine Maintenance'),
        ('audit_compliance', 'Audit Compliance'),
        ('customer_request', 'Customer Request')
    
    operation_description = fields.Text(
        string="Operation Description",
        help="Detailed description of the operation being performed"
    

    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling or access instructions"
    

    estimated_duration = fields.Float(
        ,
    string="Estimated Duration (Hours)",
        digits=(4, 2),
        help="Expected time to complete the operation"
    

        # ============================================================================
    # AUTHORIZATION AND APPROVAL
        # ============================================================================
    authorization_required = fields.Boolean(
        string="Authorization Required",
        default=False,
        help="Whether supervisor authorization is required"
    

    authorized_by_id = fields.Many2one(
        "res.users",
        string="Authorized By",
        help="Supervisor who authorized the operation"
    

    authorization_code = fields.Char(
        string="Authorization Code",
        help="Verification code for authorized access":
    

    approval_date = fields.Datetime(
        string="Approval Date",
        help="Date and time when operation was approved"
    

        # ============================================================================
    # OPERATION TRACKING
        # ============================================================================
    operation_start_time = fields.Datetime(
        string="Operation Start Time",
        help="When the operation actually started"
    

    operation_end_time = fields.Datetime(
        string="Operation End Time",
        help="When the operation was completed"
    

    items_accessed = fields.Text(
        string="Items Accessed",
        help="List of documents or containers accessed"
    

    items_retrieved = fields.Text(
        string="Items Retrieved",
        help="List of items physically retrieved"
    

    bin_condition_notes = fields.Text(
        string="Bin Condition Notes",
        help="Observations about bin condition during access"
    

        # ============================================================================
    # BILLING AND CHARGES
        # ============================================================================
    billable = fields.Boolean(
        string="Billable Operation",
        default=False,
        help="Whether this operation should be billed to customer"
    

    service_charge = fields.Float(
        string="Service Charge",
        digits='Product Price',
        help="Cost for the service operation":
    

    emergency_charge = fields.Float(
        string="Emergency Charge",
        digits='Product Price',
        help="Additional charge for emergency access":
    

    billing_notes = fields.Text(
        string="Billing Notes",
        help="Notes for billing department":
    

        # ============================================================================
    # MOBILE INTERFACE CONTROLS
        # ============================================================================
    show_contact_creation = fields.Boolean(
        string="Show Contact Creation",
        default=False,
        help="Display contact creation form in mobile interface"
    

    show_key_assignment = fields.Boolean(
        string="Show Key Assignment",
        default=False,
        help="Display key assignment options"
    

    show_lookup_results = fields.Boolean(
        string="Show Lookup Results",
        default=False,
        help="Display lookup results section"
    

    show_emergency_options = fields.Boolean(
        string="Show Emergency Options",
        default=False,
        help="Display emergency access options"
    

    ,
    mobile_view_mode = fields.Selection([))
        ('simple', 'Simple View'),
        ('detailed', 'Detailed View'),
        ('expert', 'Expert Mode')
    

        # ============================================================================
    # PHOTO AND DOCUMENTATION
        # ============================================================================
    photo_ids = fields.One2many(
        "mobile.bin.photo",
        "wizard_id",
        string="Photos",
        help="Photos taken during the operation"
    

    signature_image = fields.Binary(
        string="Digital Signature",
        help="Digital signature for operation confirmation":
    

    documentation_required = fields.Boolean(
        string="Documentation Required",
        default=False,
        help="Whether additional documentation is required"
    

        # ============================================================================
    # COMPLIANCE AND AUDIT
        # ============================================================================
    naid_compliance_check = fields.Boolean(
        string="NAID Compliance Check",
        default=True,
        help="Whether NAID compliance verification is required"
    

    audit_trail_created = fields.Boolean(
        string="Audit Trail Created",
        default=False,
        readonly=True,
        help="Whether audit trail has been created"
    

    chain_of_custody_id = fields.Many2one(
        "records.chain.of.custody",
        string="Chain of Custody",
        help="Chain of custody record for this operation":
    

    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes regarding compliance requirements"
    

        # ============================================================================
    # LOOKUP AND SEARCH RESULTS
        # ============================================================================
    lookup_query = fields.Char(
        string="Lookup Query",
        help="Search terms or criteria for quick lookup":
    

    lookup_results = fields.Text(
        string="Lookup Results",
        readonly=True,
        help="Results from database lookup operations"
    

    containers_found = fields.Integer(
        string="Containers Found",
        readonly=True,
        help="Number of containers matching lookup criteria"
    

    documents_found = fields.Integer(
        string="Documents Found",
        readonly=True,
        help="Number of documents matching lookup criteria"
    

        # ============================================================================
    # STATUS AND WORKFLOW
        # ============================================================================
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled')
    

    operation_status = fields.Selection([))
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('executing', 'Executing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('partial', 'Partial Success')
    

        # ============================================================================
    # NOTES AND OBSERVATIONS
        # ============================================================================
    operation_notes = fields.Text(
        string="Operation Notes",
        help="Detailed notes about the operation"
    

    technician_notes = fields.Text(
        string="Technician Notes",
        help="Notes from the field technician"
    

    customer_feedback = fields.Text(
        string="Customer Feedback",
        help="Feedback from customer about the service"
    

    issue_encountered = fields.Text(
        string="Issues Encountered",
        ,
    help="Any problems or issues during the operation"
    

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('operation_start_time', 'operation_end_time')
    def _compute_operation_duration(self):
        """Calculate actual operation duration"""
        for wizard in self:
            if wizard.operation_start_time and wizard.operation_end_time:
                delta = wizard.operation_end_time - wizard.operation_start_time
                wizard.actual_duration = delta.total_seconds() / 3600.0
            else:
                wizard.actual_duration = 0.0

    actual_duration = fields.Float(
        ,
    string="Actual Duration (Hours)",
        compute='_compute_operation_duration',
        store=True,
        digits=(4, 2),
        help="Actual time spent on the operation"
    

        # ============================================================================
    # ONCHANGE METHODS
        # ============================================================================
    @api.onchange('user_id')
    def _onchange_user_id(self):
        """Update employee when user changes"""
        if self.user_id and self.user_id.employee_id:
            self.employee_id = self.user_id.employee_id

    @api.onchange('bin_key_id')
    def _onchange_bin_key_id(self):
        """Update related fields when bin key changes"""
        if self.bin_key_id:
            self.bin_location_id = self.bin_key_id.location_id
            self.bin_number = self.bin_key_id.bin_number
            self.access_level_required = self.bin_key_id.access_level

    @api.onchange('action_type')
    def _onchange_action_type(self):
        """Update fields based on action type"""
        if self.action_type == 'emergency_access':
            self.priority = 'urgent'
            self.authorization_required = True
            self.show_emergency_options = True
        elif self.action_type == 'quick_lookup':
            self.show_lookup_results = True
            self.billable = False
        elif self.action_type in ['inspect', 'audit_check'):
            self.documentation_required = True
            self.naid_compliance_check = True

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update contact information when partner changes"""
        if self.partner_id:
            # Set default contact information from partner
            self.contact_name = self.partner_id.name
            self.contact_phone = self.partner_id.phone
            self.contact_email = self.partner_id.email

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_start_operation(self):
        """Start the mobile operation"""
        self.ensure_one()
        
        if self.state != 'draft':
            raise UserError(_("Can only start draft operations"))

        # Validate authorization if required:
        if self.authorization_required and not self.authorized_by_id:
            raise UserError(_("Authorization required before starting operation"))

        # Check access permissions
        if not self._check_access_permissions():
            raise UserError(_("Insufficient access permissions for this operation")):
        self.write({)}
            'state': 'in_progress',
            'operation_status': 'executing',
            'operation_start_time': fields.Datetime.now()
        

        self._create_audit_log('operation_started')
        self.message_post(body=_("Mobile operation started by %s", self.user_id.name))

        return self._return_mobile_interface()

    def action_complete_operation(self):
        """Complete the mobile operation"""
        self.ensure_one()
        
        if self.state != 'in_progress':
            raise UserError(_("Can only complete operations in progress"))

        # Validate required fields
        if self.documentation_required and not self.operation_notes:
            raise UserError(_("Operation notes required for this type of operation")):
        self.write({)}
            'state': 'completed',
            'operation_status': 'success',
            'operation_end_time': fields.Datetime.now()
        

        # Create chain of custody record if needed:
        if self.naid_compliance_check:
            self._create_chain_of_custody_record()

        self._create_audit_log('operation_completed')
        self.message_post(body=_("Mobile operation completed successfully"))

        # Generate billing record if billable:
        if self.billable:
            self._create_billing_record()

        return {'type': 'ir.actions.act_window_close'}

    def action_cancel_operation(self):
        """Cancel the mobile operation"""
        self.ensure_one()
        
        self.write({)}
            'state': 'cancelled',
            'operation_status': 'failed'
        

        self._create_audit_log('operation_cancelled')
        self.message_post(body=_("Mobile operation cancelled"))

        return {'type': 'ir.actions.act_window_close'}

    def action_execute_lookup(self):
        """Execute quick lookup operation"""
        self.ensure_one()
        
        if not self.lookup_query:
            raise UserError(_("Please enter search criteria for lookup")):
        # Perform database lookup
        results = self._perform_database_lookup()
        
        self.write({)}
            'lookup_results': results.get('formatted_results', ''),
            'containers_found': results.get('containers_count', 0),
            'documents_found': results.get('documents_count', 0),
            'show_lookup_results': True
        

        self._create_audit_log('lookup_performed')
        
        return {}
            'type': 'ir.actions.act_window',
            'res_model': 'mobile.bin.key.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, show_lookup_results=True)
        

    def action_request_authorization(self):
        """Request supervisor authorization"""
        self.ensure_one()
        
        # Create activity for supervisor:
        supervisor_group = self.env.ref('records_management.group_records_manager')
        supervisors = self.env['res.users'].search([)]
            ('groups_id', 'in', supervisor_group.id)
        

        for supervisor in supervisors:
            self.activity_schedule()
                'mail.mail_activity_data_todo',
                user_id=supervisor.id,
                summary=_("Authorization Required: %s", self.name),
                note=_("Mobile operation requires supervisor authorization:\n")
                        "Operation: %s\n"
                        "Technician: %s\n"
                        "Reason: %s", 
                        self.action_type, self.user_id.name, self.operation_reason
            

        self.message_post(body=_("Authorization requested from supervisors"))
        
        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'message': _("Authorization request sent to supervisors"),
                'type': 'success'
            
        

    def action_authorize_operation(self):
        """Authorize the operation (supervisor action)"""
        self.ensure_one()
        
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only supervisors can authorize operations"))

        self.write({)}
            'authorized_by_id': self.env.user.id,
            'approval_date': fields.Datetime.now(),
            'authorization_required': False
        

        self._create_audit_log('operation_authorized')
        self.message_post(body=_("Operation authorized by %s", self.env.user.name))

        return self._return_mobile_interface()

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('operation_start_time', 'operation_end_time')
    def _check_operation_times(self):
        """Validate operation time sequence"""
        for wizard in self:
            if (wizard.operation_start_time and wizard.operation_end_time and:)
                wizard.operation_start_time > wizard.operation_end_time
                raise ValidationError(_())
                    "Operation start time cannot be after end time"
                

    @api.constrains('service_charge', 'emergency_charge')
    def _check_charges(self):
        """Validate charge amounts"""
        for wizard in self:
            if wizard.service_charge and wizard.service_charge < 0:
                raise ValidationError(_("Service charge cannot be negative"))
            if wizard.emergency_charge and wizard.emergency_charge < 0:
                raise ValidationError(_("Emergency charge cannot be negative"))

    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def _check_access_permissions(self):
        """Check if user has permission for the requested access level""":
        self.ensure_one()
        
        user_groups = self.env.user.groups_id.mapped('name')
        
        access_requirements = {}
            'standard': ['Records User'],
            'restricted': ['Records User', 'Records Manager'],
            'confidential': ['Records Manager'],
            'secure_vault': ['Records Manager', 'Compliance Officer']
        
        
        required_groups = access_requirements.get(self.access_level_required, [])
        return any(group in user_groups for group in required_groups):
    def _perform_database_lookup(self):
        """Perform database lookup based on query"""
        self.ensure_one()
        
        query = self.lookup_query.strip()
        results = {'containers_count': 0, 'documents_count': 0, 'formatted_results': ''}
        
        if not query:
            return results

        # Search containers
        containers = self.env['records.container'].search([)]
            '|', '|',
            ('name', 'ilike', query),
            ('barcode', 'ilike', query),
            ('description', 'ilike', query)
        
        
        # Search documents
        documents = self.env['records.document'].search([)]
            '|', '|',
            ('name', 'ilike', query),
            ('document_number', 'ilike', query),
            ('description', 'ilike', query)
        

        results['containers_count'] = len(containers)
        results['documents_count'] = len(documents)
        
        # Format results
        formatted_lines = []
        if containers:
            formatted_lines.append(_("CONTAINERS FOUND (%d):", len(containers)))
            for container in containers[:10]:  # Limit to first 10
                formatted_lines.append(_("- %s (Location: %s)", 
                                        container.name, 
                                        container.location_id.name or 'Unknown'
        
        if documents:
            formatted_lines.append(_("\nDOCUMENTS FOUND (%d):", len(documents)))
            for document in documents[:10]:  # Limit to first 10
                formatted_lines.append(_("- %s (Container: %s)", 
                                        document.name, 
                                        document.container_id.name or 'Unknown'

        results['formatted_results'] = '\n'.join(formatted_lines)
        return results

    def _create_audit_log(self, action_type):
        """Create NAID compliance audit log"""
        self.ensure_one()
        
        if 'naid.audit.log' in self.env:
            audit_vals = {}
                'action_type': action_type,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'description': _("Mobile bin key operation: %s", action_type),
                'mobile_wizard_id': self.id,
                'bin_key_id': self.bin_key_id.id if self.bin_key_id else False,:
                'location_id': self.bin_location_id.id if self.bin_location_id else False,:
                'naid_compliant': self.naid_compliance_check,
            
            self.env['naid.audit.log'].create(audit_vals)
            self.audit_trail_created = True

    def _create_chain_of_custody_record(self):
        """Create chain of custody record for NAID compliance""":
        self.ensure_one()
        
        if 'records.chain.of.custody' in self.env:
            custody_vals = {}
                'name': _("Mobile Operation: %s", self.name),
                'event_type': 'mobile_access',
                'responsible_user_id': self.user_id.id,
                'event_date': fields.Datetime.now(),
                'location_id': self.bin_location_id.id if self.bin_location_id else False,:
                'description': self.operation_description or '',
                'mobile_wizard_id': self.id,
            
            custody_record = self.env['records.chain.of.custody'].create(custody_vals)
            self.chain_of_custody_id = custody_record.id

    def _create_billing_record(self):
        """Create billing record for billable operations""":
        self.ensure_one()
        
        if not self.billable or not (self.service_charge or self.emergency_charge):
            return

        total_charge = (self.service_charge or 0.0) + (self.emergency_charge or 0.0)
        
        if 'account.move' in self.env and self.partner_id:
            # Create invoice line for the service:
            invoice_vals = {}
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_line_ids': [(0, 0, {)]}
                    'name': _("Mobile Bin Key Service: %s", self.action_type),
                    'quantity': 1,
                    'price_unit': total_charge,
                    'account_id': self.env['account.account'].search([)]
                        ('user_type_id.name', '=', 'Income')
                    
                
            
            invoice = self.env['account.move'].create(invoice_vals)
            self.message_post(body=_("Billing record created: %s", invoice.name))

    def _return_mobile_interface(self):
        """Return appropriate mobile interface view"""
        self.ensure_one()
        
        return {}
            'type': 'ir.actions.act_window',
            'name': _("Mobile Bin Key Operation"),
            'res_model': 'mobile.bin.key.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': dict(self.env.context, 
                            mobile_interface=True,
                            view_mode=self.mobile_view_mode
        

    # ============================================================================
        # MOBILE INTERFACE METHODS
    # ============================================================================
    def get_mobile_dashboard_data(self):
        """Get dashboard data for mobile interface""":
        self.ensure_one()
        
        return {}
            'operation_status': self.operation_status,
            'current_location': self.bin_location_id.name if self.bin_location_id else '',:
            'operation_duration': self.actual_duration,
            'containers_found': self.containers_found,
            'documents_found': self.documents_found,
            'authorization_status': 'authorized' if not self.authorization_required else 'pending',:
            'billing_estimate': (self.service_charge or 0.0) + (self.emergency_charge or 0.0)
        

    @api.model
    def create_from_mobile_request(self, mobile_data):
        """Create wizard from mobile app request"""
        vals = {}
            'name': mobile_data.get('operation_name', _('Mobile Operation')),
            'action_type': mobile_data.get('action_type', 'quick_lookup'),
            'mobile_session_id': mobile_data.get('session_id'),
            'device_info': mobile_data.get('device_info'),
            'lookup_query': mobile_data.get('search_query'),
            'operation_reason': mobile_data.get('reason'),
            'priority': mobile_data.get('priority', 'normal'),
        
        
        return self.create(vals)

    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name and mobile settings"""
        for vals in vals_list:
            if not vals.get('name') or vals['name'] == _('New Mobile Operation'):
                sequence = self.env['ir.sequence'].next_by_code('mobile.bin.key.wizard')
                vals['name'] = sequence or _('Mobile Op %s', fields.Datetime.now().strftime('%Y%m%d-%H%M'))

        return super().create(vals_list)

    def name_get(self):
        """Custom name display for mobile operations""":
        result = []
        for wizard in self:
            name = wizard.name
            if wizard.action_type and wizard.state:
                action_label = dict(wizard._fields['action_type'].selection)[wizard.action_type]
                state_label = dict(wizard._fields['state'].selection)[wizard.state]
                name = _("%s - %s [%s]", name, action_label, state_label)
            result.append((wizard.id, name))
        return result

)))))))))))))))))))))))))))))))))))))))))))))))))