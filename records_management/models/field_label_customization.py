from odoo import models, fields, api

class FieldLabelCustomization(models.Model):
    _name = 'field.label.customization'
    _description = 'Field Label Customization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, name'

    name = fields.Char('Configuration Name', required=True)
    description = fields.Text('Description')
    model_name = fields.Char('Model Name', required=True)
    field_name = fields.Char('Field Name', required=True)
    original_label = fields.Char('Original Label', required=True)
    custom_label = fields.Char('Custom Label', required=True)
    priority = fields.Integer('Priority', default=1, help="Higher priority configurations override lower ones")
    active = fields.Boolean('Active', default=True)
    
    # Relationship fields
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', help="Apply this configuration to a specific customer")
    department_id = fields.Many2one(comodel_name='records.department', string='Department', help="Apply this configuration to a specific department")
    
    # Scope and statistics
    scope_display = fields.Char('Scope', compute='_compute_scope_display', store=True)
    customized_label_count = fields.Integer('Customized Labels', compute='_compute_customized_label_count', store=True)
    available_fields = fields.Text('Available Fields', compute='_compute_available_fields')

    # Industry-specific container label fields
    label_container_number = fields.Char('Container Number Label', default='Container Number')
    label_item_description = fields.Char('Item Description Label', default='Item Description')
    label_content_description = fields.Char('Content Description Label', default='Content Description')
    label_parent_container = fields.Char('Parent Container Label', default='Parent Container')
    label_folder_type = fields.Char('Item Type Label', default='Item Type')
    label_hierarchy_display = fields.Char('Location Path Label', default='Location Path')
    label_date_from = fields.Char('Date From Label', default='Date From')
    label_date_to = fields.Char('Date To Label', default='Date To')
    label_destruction_date = fields.Char('Destruction Date Label', default='Destruction Date')
    label_sequence_from = fields.Char('Sequence From Label', default='Sequence From')
    label_sequence_to = fields.Char('Sequence To Label', default='Sequence To')
    label_record_type = fields.Char('Record Type Label', default='Record Type')
    label_confidentiality = fields.Char('Confidentiality Label', default='Confidentiality')
    label_filing_system = fields.Char('Filing System Label', default='Filing System')
    label_project_code = fields.Char('Project Code Label', default='Project Code')
    label_client_reference = fields.Char('Client Reference Label', default='Client Reference')
    label_file_count = fields.Char('Number of Files Label', default='Number of Files')
    label_authorized_by = fields.Char('Authorized By Label', default='Authorized By')
    label_created_by_dept = fields.Char('Created By Department Label', default='Created By Department')
    label_special_handling = fields.Char('Special Handling Label', default='Special Handling Instructions')
    label_compliance_notes = fields.Char('Compliance Notes Label', default='Compliance Notes')
    label_weight_estimate = fields.Char('Estimated Weight Label', default='Estimated Weight')
    label_size_estimate = fields.Char('Estimated Size Label', default='Estimated Size')
    
    @api.depends('partner_id', 'department_id')
    def _compute_scope_display(self):
        """Compute the scope display string"""
        for record in self:
            if record.department_id:
                record.scope_display = f"Department: {record.department_id.name}"
            elif record.partner_id:
                record.scope_display = f"Customer: {record.partner_id.name}"
            else:
                record.scope_display = "Global"
    
    @api.depends('label_container_number', 'label_item_description', 'label_content_description', 
                 'label_parent_container', 'label_folder_type', 'label_hierarchy_display',
                 'label_date_from', 'label_date_to', 'label_destruction_date',
                 'label_sequence_from', 'label_sequence_to',
                 'label_record_type', 'label_confidentiality', 'label_filing_system',
                 'label_project_code', 'label_client_reference', 'label_file_count',
                 'label_authorized_by', 'label_created_by_dept',
                 'label_special_handling', 'label_compliance_notes',
                 'label_weight_estimate', 'label_size_estimate')
    def _compute_customized_label_count(self):
        """Count how many labels have been customized from defaults"""
        defaults = {
            'label_container_number': 'Container Number',
            'label_item_description': 'Item Description',
            'label_content_description': 'Content Description',
            'label_parent_container': 'Parent Container',
            'label_folder_type': 'Item Type',
            'label_hierarchy_display': 'Location Path',
            'label_date_from': 'Date From',
            'label_date_to': 'Date To',
            'label_destruction_date': 'Destruction Date',
            'label_sequence_from': 'Sequence From',
            'label_sequence_to': 'Sequence To',
            'label_record_type': 'Record Type',
            'label_confidentiality': 'Confidentiality',
            'label_filing_system': 'Filing System',
            'label_project_code': 'Project Code',
            'label_client_reference': 'Client Reference',
            'label_file_count': 'Number of Files',
            'label_authorized_by': 'Authorized By',
            'label_created_by_dept': 'Created By Department',
            'label_special_handling': 'Special Handling Instructions',
            'label_compliance_notes': 'Compliance Notes',
            'label_weight_estimate': 'Estimated Weight',
            'label_size_estimate': 'Estimated Size',
        }
        for record in self:
            count = 0
            for field_name, default_value in defaults.items():
                if record[field_name] and record[field_name] != default_value:
                    count += 1
            record.customized_label_count = count
    
    @api.depends('model_name')
    def _compute_available_fields(self):
        """Show available fields for the selected model"""
        for record in self:
            if record.model_name and record.model_name in self.env:
                model = self.env[record.model_name]
                fields_list = []
                for fname, field in model._fields.items():
                    fields_list.append(f"{fname}: {field.string}")
                record.available_fields = "\n".join(sorted(fields_list))
            else:
                record.available_fields = "Select a valid model to see available fields"

    # Field name to label field mapping - maps actual model fields to customization fields
    FIELD_LABEL_MAP = {
        # records.container fields
        'name': 'label_container_number',
        'description': 'label_item_description',
        'content_description': 'label_content_description',
        'parent_id': 'label_parent_container',
        'container_type_id': 'label_folder_type',
        'hierarchy_display': 'label_hierarchy_display',
        'content_date_from': 'label_date_from',
        'content_date_to': 'label_date_to',
        'destruction_due_date': 'label_destruction_date',
        'alpha_range_start': 'label_sequence_from',
        'alpha_range_end': 'label_sequence_to',
        'primary_content_type': 'label_record_type',
        'confidentiality_level': 'label_confidentiality',
        'filing_system': 'label_filing_system',
        'project_code': 'label_project_code',
        'customer_reference': 'label_client_reference',
        'file_count': 'label_file_count',
        'authorized_by': 'label_authorized_by',
        'department_id': 'label_created_by_dept',
        'special_handling': 'label_special_handling',
        'compliance_notes': 'label_compliance_notes',
        'weight': 'label_weight_estimate',
        'dimensions': 'label_size_estimate',
    }

    @api.model
    def get_config_for_partner(self, partner_id=None):
        """Get the highest priority configuration for a specific partner or global.
        
        Priority order:
        1. Partner-specific config (highest priority)
        2. Department-specific config
        3. Global config (no partner or department)
        """
        domain = [('active', '=', True)]
        
        if partner_id:
            # Try partner-specific first
            config = self.search(domain + [('partner_id', '=', partner_id)], 
                                order='priority desc', limit=1)
            if config:
                return config
        
        # Try global config
        config = self.search(domain + [('partner_id', '=', False), ('department_id', '=', False)], 
                            order='priority desc', limit=1)
        return config

    @api.model
    def get_custom_label(self, field_name, partner_id=None):
        """Get the custom label for a field based on partner's configuration.
        
        Args:
            field_name: The technical field name (e.g., 'name', 'content_description')
            partner_id: Optional partner ID to get partner-specific labels
            
        Returns:
            Custom label string or None if no customization exists
        """
        config = self.get_config_for_partner(partner_id)
        if not config:
            return None
        
        label_field = self.FIELD_LABEL_MAP.get(field_name)
        if label_field and hasattr(config, label_field):
            return getattr(config, label_field)
        return None

    @api.model
    def get_labels_dict(self, partner_id=None):
        """Get all custom labels as a dictionary for templates/views.
        
        Returns dict mapping field names to their custom labels.
        Only includes fields that have been customized (different from default).
        """
        config = self.get_config_for_partner(partner_id)
        
        # Default labels
        defaults = {
            'name': 'Container Number',
            'description': 'Item Description',
            'content_description': 'Content Description',
            'parent_id': 'Parent Container',
            'container_type_id': 'Item Type',
            'hierarchy_display': 'Location Path',
            'content_date_from': 'Date From',
            'content_date_to': 'Date To',
            'destruction_due_date': 'Destruction Date',
            'alpha_range_start': 'Sequence From',
            'alpha_range_end': 'Sequence To',
            'primary_content_type': 'Record Type',
            'confidentiality_level': 'Confidentiality',
            'filing_system': 'Filing System',
            'project_code': 'Project Code',
            'customer_reference': 'Client Reference',
            'file_count': 'Number of Files',
            'authorized_by': 'Authorized By',
            'department_id': 'Created By Department',
            'special_handling': 'Special Handling Instructions',
            'compliance_notes': 'Compliance Notes',
            'weight': 'Estimated Weight',
            'dimensions': 'Estimated Size',
        }
        
        if not config:
            return defaults
        
        # Override with custom labels
        labels = defaults.copy()
        for field_name, label_field in self.FIELD_LABEL_MAP.items():
            if hasattr(config, label_field):
                custom_value = getattr(config, label_field)
                if custom_value:
                    labels[field_name] = custom_value
        
        return labels

    @api.model
    def get_container_labels(self, partner_id=None):
        """Get all container-related labels for the current configuration.
        
        Backward compatible method - now uses get_labels_dict internally.
        """
        labels = self.get_labels_dict(partner_id)
        
        # Return in the old format for backward compatibility
        return {
            'container_number': labels.get('name', 'Container Number'),
            'item_description': labels.get('description', 'Item Description'),
            'content_description': labels.get('content_description', 'Content Description'),
            'date_from': labels.get('content_date_from', 'Date From'),
            'date_to': labels.get('content_date_to', 'Date To'),
            'record_type': labels.get('primary_content_type', 'Record Type'),
            'confidentiality': labels.get('confidentiality_level', 'Confidentiality'),
            'project_code': labels.get('project_code', 'Project Code'),
            'client_reference': labels.get('customer_reference', 'Client Reference'),
            'authorized_by': labels.get('authorized_by', 'Authorized By'),
            'created_by_dept': labels.get('department_id', 'Created By Department'),
        }

    @api.constrains('model_name', 'field_name', 'priority')
    def _check_unique_priority(self):
        """Ensure no duplicate priorities for the same model/field combination"""
        for record in self:
            duplicate = self.search([
                ('model_name', '=', record.model_name),
                ('field_name', '=', record.field_name),
                ('priority', '=', record.priority),
                ('id', '!=', record.id)
            ])
            if duplicate:
                raise ValueError(f"Priority {record.priority} already exists for {record.model_name}.{record.field_name}")
    
    def action_apply_corporate_preset(self):
        """Apply standard corporate terminology preset"""
        self.ensure_one()
        self.write({
            'label_container_number': 'Box Number',
            'label_item_description': 'Contents',
            'label_content_description': 'Detailed Contents',
            'label_parent_container': 'Parent Box',
            'label_folder_type': 'Document Type',
            'label_hierarchy_display': 'Storage Location',
            'label_date_from': 'Start Date',
            'label_date_to': 'End Date',
            'label_destruction_date': 'Disposal Date',
            'label_sequence_from': 'Starting Number',
            'label_sequence_to': 'Ending Number',
            'label_record_type': 'Document Category',
            'label_confidentiality': 'Classification',
            'label_filing_system': 'Organization System',
            'label_project_code': 'Project ID',
            'label_client_reference': 'Reference Number',
            'label_file_count': 'File Quantity',
            'label_authorized_by': 'Approved By',
            'label_created_by_dept': 'Originating Department',
            'label_special_handling': 'Handling Notes',
            'label_compliance_notes': 'Regulatory Notes',
            'label_weight_estimate': 'Approx. Weight',
            'label_size_estimate': 'Approx. Size',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Corporate Preset Applied',
            'message': 'Standard corporate terminology has been applied',
            'type': 'success',
        }}
    
    def action_apply_legal_preset(self):
        """Apply legal industry terminology preset"""
        self.ensure_one()
        self.write({
            'label_container_number': 'Matter Box',
            'label_item_description': 'Case Materials',
            'label_content_description': 'Document Inventory',
            'label_parent_container': 'Parent Matter',
            'label_folder_type': 'Document Class',
            'label_hierarchy_display': 'Matter Path',
            'label_date_from': 'Earliest Date',
            'label_date_to': 'Latest Date',
            'label_destruction_date': 'Retention Expiry',
            'label_sequence_from': 'First Document',
            'label_sequence_to': 'Last Document',
            'label_record_type': 'Document Type',
            'label_confidentiality': 'Privilege Level',
            'label_filing_system': 'Filing Method',
            'label_project_code': 'Matter Number',
            'label_client_reference': 'Client Matter',
            'label_file_count': 'Document Count',
            'label_authorized_by': 'Responsible Attorney',
            'label_created_by_dept': 'Practice Group',
            'label_special_handling': 'Handling Instructions',
            'label_compliance_notes': 'Retention Notes',
            'label_weight_estimate': 'Estimated Weight',
            'label_size_estimate': 'Volume Estimate',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Legal Preset Applied',
            'message': 'Legal industry terminology has been applied',
            'type': 'success',
        }}
    
    def action_apply_healthcare_preset(self):
        """Apply healthcare industry terminology preset"""
        self.ensure_one()
        self.write({
            'label_container_number': 'Chart Box',
            'label_item_description': 'Medical Records',
            'label_content_description': 'Record Details',
            'label_parent_container': 'Parent Chart',
            'label_folder_type': 'Record Type',
            'label_hierarchy_display': 'Storage Path',
            'label_date_from': 'Service Date From',
            'label_date_to': 'Service Date To',
            'label_destruction_date': 'Purge Date',
            'label_sequence_from': 'First MRN',
            'label_sequence_to': 'Last MRN',
            'label_record_type': 'Chart Type',
            'label_confidentiality': 'HIPAA Level',
            'label_filing_system': 'Filing Protocol',
            'label_project_code': 'Department Code',
            'label_client_reference': 'Patient ID',
            'label_file_count': 'Chart Count',
            'label_authorized_by': 'Supervising Physician',
            'label_created_by_dept': 'Originating Department',
            'label_special_handling': 'PHI Handling',
            'label_compliance_notes': 'HIPAA Compliance',
            'label_weight_estimate': 'Box Weight',
            'label_size_estimate': 'Box Dimensions',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Healthcare Preset Applied',
            'message': 'Healthcare industry terminology has been applied',
            'type': 'success',
        }}
    
    def action_apply_financial_preset(self):
        """Apply financial services terminology preset"""
        self.ensure_one()
        self.write({
            'label_container_number': 'File Box',
            'label_item_description': 'Account Records',
            'label_content_description': 'Transaction Details',
            'label_parent_container': 'Master File',
            'label_folder_type': 'Account Type',
            'label_hierarchy_display': 'File Path',
            'label_date_from': 'Period Start',
            'label_date_to': 'Period End',
            'label_destruction_date': 'Archive Expiry',
            'label_sequence_from': 'Starting Account',
            'label_sequence_to': 'Ending Account',
            'label_record_type': 'Document Category',
            'label_confidentiality': 'Security Level',
            'label_filing_system': 'Filing Structure',
            'label_project_code': 'Branch Code',
            'label_client_reference': 'Account Number',
            'label_file_count': 'Statement Count',
            'label_authorized_by': 'Compliance Officer',
            'label_created_by_dept': 'Business Unit',
            'label_special_handling': 'Audit Requirements',
            'label_compliance_notes': 'Regulatory Compliance',
            'label_weight_estimate': 'Container Weight',
            'label_size_estimate': 'Storage Volume',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Financial Preset Applied',
            'message': 'Financial services terminology has been applied',
            'type': 'success',
        }}
    
    def action_reset_to_defaults(self):
        """Reset all labels to default values"""
        self.ensure_one()
        self.write({
            'label_container_number': 'Container Number',
            'label_item_description': 'Item Description',
            'label_content_description': 'Content Description',
            'label_parent_container': 'Parent Container',
            'label_folder_type': 'Item Type',
            'label_hierarchy_display': 'Location Path',
            'label_date_from': 'Date From',
            'label_date_to': 'Date To',
            'label_destruction_date': 'Destruction Date',
            'label_sequence_from': 'Sequence From',
            'label_sequence_to': 'Sequence To',
            'label_record_type': 'Record Type',
            'label_confidentiality': 'Confidentiality',
            'label_filing_system': 'Filing System',
            'label_project_code': 'Project Code',
            'label_client_reference': 'Client Reference',
            'label_file_count': 'Number of Files',
            'label_authorized_by': 'Authorized By',
            'label_created_by_dept': 'Created By Department',
            'label_special_handling': 'Special Handling Instructions',
            'label_compliance_notes': 'Compliance Notes',
            'label_weight_estimate': 'Estimated Weight',
            'label_size_estimate': 'Estimated Size',
        })
        return {'type': 'ir.actions.client', 'tag': 'display_notification', 'params': {
            'title': 'Reset Complete',
            'message': 'All labels have been reset to default values',
            'type': 'success',
        }}
