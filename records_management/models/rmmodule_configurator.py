# -*- coding: utf-8 -*-

Records Management System Configuration Module

This module provides comprehensive field visibility and feature configuration
for the Records Management System. Administrators can control which fields:
    pass
and features are available throughout the system without modifying code.

Key Features
- Field visibility control for all major models:
- Feature toggle system for optional functionality:
- Company-specific configuration with inheritance
- Real-time configuration changes without system restart
- Audit trail of configuration changes
- Default configurations for new installations:
Business Benefits
- Simplified user interface by hiding unused fields
- Streamlined workflows for specific business needs:
- Easy adaptation to different customer requirements
- Professional system customization without technical knowledge
- Compliance with varying regulatory requirements

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


import json

from odoo import models, fields, api, _

from odoo.exceptions import ValidationError




class RMModuleConfigurator(models.Model):
    _name = "rm.module.configurator"
    _description = "Records Management Module Configurator"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "category, name"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Configuration Name",
        required=True,
        tracking=True,
        help="Name of the configuration item"
    

    ,
    category = fields.Selection([))
        ('shredding', 'Shredding & Destruction'),
        ('document', 'Document Management'),
        ('container', 'Container Management'),
        ('billing', 'Billing & Finance'),
        ('portal', 'Customer Portal'),
        ('compliance', 'NAID Compliance'),
        ('location', 'Location Management'),
        ('retention', 'Retention Policies'),
        ('reporting', 'Reports & Analytics'),
        ('security', 'Security & Access'),
    

    description = fields.Text(
        string="Description",
        help="Description of what this configuration controls"
    

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    

    user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    

    active = fields.Boolean(
        string='Active',
        default=True,
        help="Whether this configuration is active"
    

        # ============================================================================
    # CONFIGURATION TYPE
        # ============================================================================
    ,
    config_type = fields.Selection([))
        ('field_visibility', 'Field Visibility'),
        ('feature_toggle', 'Feature Toggle'),
        ('selection_values', 'Selection Field Values'),
        ('validation_rule', 'Validation Rules'),
        ('default_value', 'Default Values'),
    

        # ============================================================================
    # TARGET CONFIGURATION
        # ============================================================================
    target_model = fields.Char(
        string="Target Model",
        ,
    help="Technical name of the model (e.g., 'shredding.certificate')"
    

    target_field = fields.Char(
        string="Target Field",
        ,
    help="Technical name of the field (e.g., 'destruction_method')"
    

    target_view_type = fields.Selection([))
        ('form', 'Form View'),
        ('tree', 'List View'),
        ('search', 'Search View'),
        ('all', 'All Views'),
    

        # ============================================================================
    # VISIBILITY CONTROL
        # ============================================================================
    visible = fields.Boolean(
        string="Visible",
        default=True,
        tracking=True,
        help="Whether the field/feature should be visible to users"
    

    required = fields.Boolean(
        string="Required",
        default=False,
        ,
    help="Whether the field should be required (if visible)":
    

    readonly = fields.Boolean(
        string="Read Only",
        default=False,
        help="Whether the field should be read-only"
    

        # ============================================================================
    # SELECTION VALUES CONFIGURATION
        # ============================================================================
    available_selection_values = fields.Text(
        string="Available Selection Values",
        help="JSON format of available selection values"
    

        # ============================================================================
    # CONDITIONS
        # ============================================================================
    condition_field = fields.Char(
        string="Condition Field",
        help="Field to check for conditional visibility":
    

    ,
    condition_operator = fields.Selection([)),
        ('=', 'Equals'),
        ('!=', 'Not Equals'),
        ('in', 'In List'),
        ('not in', 'Not In List'),
    

    condition_value = fields.Char(
        string="Condition Value",
        help="Value to compare against"
    

        # ============================================================================
    # AUDIT FIELDS
        # ============================================================================
    last_modified = fields.Datetime(
        string="Last Modified",
        default=fields.Datetime.now,
        readonly=True
    

    modified_by_id = fields.Many2one(
        'res.users',
        string="Modified By",
        readonly=True
    

    notes = fields.Text(
        string="Configuration Notes",
        help="Additional notes about this configuration"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    
    ,
    action_activate_config = fields.Char(string='Action Activate Config'),
    action_deactivate_config = fields.Char(string='Action Deactivate Config'),
    action_reset_to_default = fields.Char(string='Action Reset To Default'),
    action_view_related_configs = fields.Char(string='Action View Related Configs'),
    affects_ui = fields.Char(string='Affects Ui'),
    affects_workflow = fields.Char(string='Affects Workflow'),
    analytics = fields.Char(string='Analytics'),
    boolean_value = fields.Char(string='Boolean Value'),
    button_box = fields.Char(string='Button Box'),
    config_key = fields.Char(string='Config Key'),
    configuration_notes = fields.Char(string='Configuration Notes'),
    conflicts_with_configs = fields.Char(string='Conflicts With Configs'),
    context = fields.Char(string='Context'),
    create_date = fields.Date(string='Create Date'),
    default_boolean = fields.Char(string='Default Boolean'),
    default_numeric = fields.Char(string='Default Numeric'),
    default_selection = fields.Char(string='Default Selection'),
    default_text = fields.Char(string='Default Text'),
    department_id = fields.Many2one('department',,
    string='Department Id'),
    dependencies = fields.Char(string='Dependencies'),
    depends_on_configs = fields.Char(string='Depends On Configs'),
    documentation = fields.Char(string='Documentation'),
    domain = fields.Char(string='Domain'),
    filter_active = fields.Boolean(string='Filter Active',,
    default=False),
    filter_billing = fields.Char(string='Filter Billing'),
    filter_compliance = fields.Char(string='Filter Compliance'),
    filter_disabled = fields.Char(string='Filter Disabled'),
    filter_enabled = fields.Char(string='Filter Enabled'),
    filter_features = fields.Char(string='Filter Features'),
    filter_high_priority = fields.Selection([), string='Filter High Priority')  # TODO: Define selection options
    filter_inactive = fields.Boolean(string='Filter Inactive',,
    default=False),
    filter_integrations = fields.Char(string='Filter Integrations'),
    filter_mobile = fields.Char(string='Filter Mobile'),
    filter_my_company = fields.Char(string='Filter My Company'),
    filter_my_configs = fields.Char(string='Filter My Configs'),
    filter_recent = fields.Char(string='Filter Recent'),
    filter_recently_modified = fields.Char(string='Filter Recently Modified'),
    filter_reporting = fields.Char(string='Filter Reporting'),
    filter_security = fields.Char(string='Filter Security'),
    filter_system = fields.Char(string='Filter System'),
    filter_ui = fields.Char(string='Filter Ui'),
    group_by_category = fields.Char(string='Group By Category'),
    group_by_company = fields.Char(string='Group By Company'),
    group_by_create_date = fields.Date(string='Group By Create Date'),
    group_by_priority = fields.Selection([), string='Group By Priority')  # TODO: Define selection options
    group_by_status = fields.Selection([), string='Group By Status')  # TODO: Define selection options
    group_by_type = fields.Selection([), string='Group By Type')  # TODO: Define selection options
    group_by_user = fields.Char(string='Group By User'),
    help = fields.Char(string='Help'),
    help_text = fields.Char(string='Help Text'),
    is_system_config = fields.Char(string='Is System Config'),
    last_user_id = fields.Many2one('last.user',,
    string='Last User Id'),
    max_value = fields.Char(string='Max Value'),
    memory_usage_kb = fields.Char(string='Memory Usage Kb'),
    min_value = fields.Char(string='Min Value'),
    modification_count = fields.Integer(string='Modification Count', compute='_compute_modification_count',,
    store=True),
    numeric_value = fields.Char(string='Numeric Value'),
    performance_impact = fields.Char(string='Performance Impact'),
    related_configs_count = fields.Integer(string='Related Configs Count', compute='_compute_related_configs_count',,
    store=True),
    requires_restart = fields.Char(string='Requires Restart'),
    res_model = fields.Char(string='Res Model'),
    search_view_id = fields.Many2one('search.view',,
    string='Search View Id'),
    selection = fields.Char(string='Selection'),
    selection_options = fields.Char(string='Selection Options'),
    selection_value = fields.Char(string='Selection Value'),
    text_value = fields.Char(string='Text Value'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    values = fields.Char(string='Values'),
    view_id = fields.Many2one('view',,
    string='View Id'),
    view_mode = fields.Char(string='View Mode'),
    web_ribbon = fields.Char(string='Web Ribbon')

    @api.depends('modification_ids')
    def _compute_modification_count(self):
        for record in self:
            record.modification_count = len(record.modification_ids)

    @api.depends('related_configs_ids')
    def _compute_related_configs_count(self):
        for record in self:
            record.related_configs_count = len(record.related_configs_ids)

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('target_model', 'target_field')
    def _check_target_exists(self):
        """Validate that target model and field exist"""
        for record in self:
            if record.target_model:
                if record.target_model not in self.env:
                    raise ValidationError()
                        _("Model '%s' does not exist", record.target_model)
                    

                if record.target_field:
                    model = self.env[record.target_model)
                    if record.target_field not in model._fields:
                        raise ValidationError()
                            _("Field '%s' does not exist in model '%s'",
                                record.target_field, record.target_model
                        

    # ============================================================================
        # WRITE METHOD OVERRIDE
    # ============================================================================
    def write(self, vals):
        """Override write to track modifications"""
        if vals:
            vals.update({)}
                'last_modified': fields.Datetime.now(),
                'modified_by_id': self.env.user.id,
            
        result = super().write(vals)

        # Log configuration change
        for record in self:
            record.message_post()
                body=_("Configuration updated by %s", self.env.user.name)
            

        return result

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_field_visibility(self, model_name, field_name, view_type='all'):
        """Get field visibility configuration"""
        config = self.search([)]
            ('target_model', '=', model_name),
            ('target_field', '=', field_name),
            ('config_type', '=', 'field_visibility'),
            ('target_view_type', 'in', [view_type, 'all']),
            ('active', '=', True),
        

        if config:
            return {}
                'visible': config.visible,
                'required': config.required,
                'readonly': config.readonly,
            

        # Default: all fields visible
        return {}
            'visible': True,
            'required': False,
            'readonly': False,
        

    @api.model
    def get_available_selection_values(self, model_name, field_name):
        """Get available selection values for a field""":
        config = self.search([)]
            ('target_model', '=', model_name),
            ('target_field', '=', field_name),
            ('config_type', '=', 'selection_values'),
            ('active', '=', True),
        

        if config and config.available_selection_values:
            try:
                return json.loads(config.available_selection_values)
            except (json.JSONDecodeError, TypeError)
                pass

        return None

    @api.model
    def is_feature_enabled(self, feature_name):
        """Check if a feature is enabled""":
        config = self.search([)]
            ('name', '=', feature_name),
            ('config_type', '=', 'feature_toggle'),
            ('active', '=', True),
        

        return config.visible if config else True:
    # ============================================================================
        # CONFIGURATION MANAGEMENT METHODS
    # ============================================================================
    @api.model
    def setup_default_configurations(self):
        """Create default configurations for the system""":
        default_configs = self._get_system_default_configurations()

        for config_data in default_configs:
            existing = self.search([)]
                ('name', '=', config_data['name']),
                ('target_model', '=', config_data.get('target_model')),
                ('target_field', '=', config_data.get('target_field')),
            

            if not existing:
                self.create(config_data)

    def _get_system_default_configurations(self):
        """Get default configuration data"""
        return []
            # Shredding Certificate Configurations
            {}
                'name': 'Destruction Method - Standard Options',
                'category': 'shredding',
                'config_type': 'selection_values',
                'target_model': 'shredding.certificate',
                'target_field': 'destruction_method',
                'description': 'Available destruction methods for NAID compliance',:
                'available_selection_values': '["cross_cut", "strip_cut", "pulverization", "incineration", "disintegration", "acid_bath"]',
                'visible': True,
            
            {}
                'name': 'Witness Information Required',
                'category': 'shredding',
                'config_type': 'field_visibility',
                'target_model': 'shredding.certificate',
                'target_field': 'witness_required',
                'description': 'Control witness information requirements',
                'visible': True,
                'required': True,
            
            {}
                'name': 'Temperature Logging',
                'category': 'shredding',
                'config_type': 'field_visibility',
                'target_model': 'shredding.certificate',
                'target_field': 'temperature_log',
                'description': 'Show temperature logging for incineration',:
                'visible': True,
                'condition_field': 'destruction_method',
                'condition_operator': '=',
                'condition_value': 'incineration',
            

            # Container Management
            {}
                'name': 'Container Type Restrictions',
                'category': 'container',
                'config_type': 'selection_values',
                'target_model': 'records.container',
                'target_field': 'container_type',
                'description': 'Available container types for business operations',:
                'available_selection_values': '["type_01", "type_02", "type_03", "type_04", "type_06"]',
                'visible': True,
            

            # Billing Configurations
            {}
                'name': 'prepaid_billing_enabled',
                'category': 'billing',
                'config_type': 'feature_toggle',
                'description': 'Enable prepaid billing functionality',
                'visible': True,
            

            # Portal Configurations
            {}
                'name': 'customer_feedback_enabled',
                'category': 'portal',
                'config_type': 'feature_toggle',
                'description': 'Enable customer feedback and satisfaction tracking',
                'visible': True,
            

            # Compliance Configurations
            {}
                'name': 'NAID Compliance Level Options',
                'category': 'compliance',
                'config_type': 'selection_values',
                'target_model': 'shredding.certificate',
                'target_field': 'naid_level',
                'description': 'Available NAID compliance levels',
                'available_selection_values': '["aaa", "aa", "a"]',
                'visible': True,
            
        

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_apply_configuration(self):
        """Apply configuration changes"""

        self.ensure_one()

        # Trigger cache clear for field visibility:
        self.env.registry.clear_cache()

        # Log the application
        self.message_post()
            body=_("Configuration applied by %s", self.env.user.name)
        

        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'title': _('Configuration Applied'),
                'message': _('Configuration changes have been applied successfully'),
                'type': 'success',
            
        

    def action_restore_defaults(self):
        """Reset configuration to default values"""

        self.ensure_one()

        default_values = {}
            'visible': True,
            'required': False,
            'readonly': False,
        

        self.write(default_values)

        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'title': _('Reset to Default'),
                'message': _('Configuration has been reset to default values'),
                'type': 'info',
            
        


class RecordsConfigurationWizard(models.TransientModel):
    """Wizard for bulk configuration management""":
    _name = 'records.configuration.wizard'
    _description = 'Configuration Management Wizard'

    category = fields.Selection([))
        ('shredding', 'Shredding & Destruction'),
        ('document', 'Document Management'),
        ('container', 'Container Management'),
        ('billing', 'Billing & Finance'),
        ('portal', 'Customer Portal'),
        ('compliance', 'NAID Compliance'),
        ('location', 'Location Management'),
        ('retention', 'Retention Policies'),
        ('reporting', 'Reports & Analytics'),
        ('security', 'Security & Access'),
    

    action_type = fields.Selection([))
        ('show_all', 'Show All Fields'),
        ('hide_all', 'Hide All Fields'),
        ('reset_defaults', 'Reset to Defaults'),
        ('create_missing', 'Create Missing Configurations'),
    

    def action_execute(self):
        """Execute the bulk configuration action"""

        self.ensure_one()
        configs = self.env['rm.module.configurator'].search([)]
            ('category', '=', self.category)
        

        message = _('No action performed')

        if self.action_type == 'show_all':
            configs.write({'visible': True})
            message = _('All fields in %s category are now visible', self.category)

        elif self.action_type == 'hide_all':
            configs.write({'visible': False})
            message = _('All fields in %s category are now hidden', self.category)

        elif self.action_type == 'reset_defaults':
            configs.write({)}
                'visible': True,
                'required': False,
                'readonly': False,
            
            message = _('All configurations in %s category reset to defaults', self.category)

        elif self.action_type == 'create_missing':
            self.env['rm.module.configurator'].setup_default_configurations()
            message = _('Missing configurations created for %s category', self.category):
        return {}
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {}
                'title': _('Bulk Action Completed'),
                'message': message,
                'type': 'success',
            
        
))))))))