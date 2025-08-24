from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RmModuleConfigurator(models.Model):
    _name = 'rm.module.configurator'
    _description = 'Records Management Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'category, sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS - Configuration Definition
    # ============================================================================
    name = fields.Char(string="Configuration Name", required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, help="Only active configurations are applied.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, help="Configuration specific to a company. Leave empty for global.")
    
    category = fields.Selection([
        ('ui', 'User Interface'),
        ('workflow', 'Workflow'),
        ('billing', 'Billing'),
        ('compliance', 'Compliance & NAID'),
        ('fsm', 'Field Service'),
        ('portal', 'Customer Portal'),
        ('reporting', 'Reporting'),
        ('security', 'Security'),
        ('system', 'System')
    ], string="Category", required=True, default='system')

    config_type = fields.Selection([
        ('field_visibility', 'Field Visibility'),
        ('feature_toggle', 'Feature Toggle'),
        ('parameter', 'System Parameter'),
        ('domain_rule', 'Domain Rule')
    ], string="Configuration Type", required=True, default='parameter')

    description = fields.Text(string="Description", help="Explain what this configuration does and its impact.")
    config_key = fields.Char(string="Technical Key", required=True, copy=False, help="Unique technical key to identify this configuration in code.")

    # ============================================================================
    # FIELDS - Configuration Value
    # ============================================================================
    value_text = fields.Char(string="Text Value")
    value_boolean = fields.Boolean(string="Boolean Value")
    value_number = fields.Float(string="Number Value")
    value_selection = fields.Char(string="Selection Value")
    
    # ============================================================================
    # FIELDS - Targeting (for UI/Domain rules)
    # ============================================================================
    target_model_id = fields.Many2one('ir.model', string="Target Model", domain="[('model', 'like', 'records_management.')]")
    target_model = fields.Char(related='target_model_id.model', readonly=True, store=True)
    target_field_id = fields.Many2one('ir.model.fields', string="Target Field", domain="[('model_id', '=', target_model_id)]")
    target_field = fields.Char(related='target_field_id.name', readonly=True, store=True)
    
    # For field_visibility
    visible = fields.Boolean(string="Is Visible", default=True)
    required = fields.Boolean(string="Is Required")
    readonly = fields.Boolean(string="Is Read-Only")

    # ============================================================================
    # FIELDS - Auditing
    # ============================================================================
    modified_by_id = fields.Many2one('res.users', string='Last Modified By', readonly=True)
    last_modified = fields.Datetime(string='Last Modified On', readonly=True)
    modification_count = fields.Integer(string="Modification Count", default=0, readonly=True)
    notes = fields.Text(string="Internal Notes")

    _sql_constraints = [
        ('config_key_company_uniq', 'unique(config_key, company_id)', 'The configuration key must be unique per company!')
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals['modified_by_id'] = self.env.user.id
            vals['last_modified'] = fields.Datetime.now()
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track modifications and clear server cache."""
        if any(key.startswith('value_') for key in vals):
            vals['modified_by_id'] = self.env.user.id
            vals['last_modified'] = fields.Datetime.now()
            vals['modification_count'] = self.modification_count + 1
        
        res = super().write(vals)
        # Clear server-side caches to ensure new configuration is loaded
        self.env.registry.clear_caches()
        self.clear_caches()
        return res

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('config_type', 'value_text', 'value_boolean', 'value_number', 'value_selection')
    def _validate_value_type(self):
        """Validate that the correct value field is used for the parameter type."""
        for record in self:
            if record.config_type == 'parameter':
                # Ensure only one value field is set for parameters
                value_fields = [record.value_text, record.value_boolean, record.value_number, record.value_selection]
                if sum(1 for v in value_fields if v) > 1:
                    raise ValidationError(_(
                        "Configuration '%(name)s' is a parameter and must have only one value type (Text, Boolean, Number, or Selection).",
                        name=record.name
                    ))

    @api.constrains('config_type', 'target_model_id', 'target_field_id')
    def _check_target_exists(self):
        """Validate that target model and field are set for UI-related configs."""
        for record in self:
            if record.config_type in ['field_visibility', 'domain_rule']:
                if not record.target_model_id:
                    raise ValidationError(_("A 'Target Model' is required for UI or Domain configurations."))
                if not record.target_field_id and record.config_type == 'field_visibility':
                    raise ValidationError(_("A 'Target Field' is required for Field Visibility configurations."))

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    @api.model
    def get_config_parameter(self, key, default=None):
        """
        High-performance method to get a configuration value.
        This should be the primary way code interacts with this model.
        It uses caching for performance.
        """
        # Caching is automatically handled by Odoo for search method
        config = self.search([('config_key', '=', key), ('active', '=', True)], limit=1)
        if not config:
            return default
        
        if config.value_boolean:
            return config.value_boolean
        if config.value_number is not None:
            return config.value_number
        if config.value_text:
            return config.value_text
        if config.value_selection:
            return config.value_selection
            
        return default

    def action_apply_configuration(self):
        """
        Applies the configuration. For most types, this is done by clearing caches.
        For more complex scenarios, this method can be extended.
        """
        self.ensure_one()
