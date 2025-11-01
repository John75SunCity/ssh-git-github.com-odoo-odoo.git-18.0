from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TransitoryFieldConfig(models.Model):
    _name = 'transitory.field.config'
    _description = 'Transitory Field Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Field Label", required=True, tracking=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", tracking=True)
    department_id = fields.Many2one(comodel_name='records.department', string="Department", tracking=True)
    field_label_config_id = fields.Many2one(comodel_name='field.label.customization', string="Field Label Configuration")
    
    # Configuration Preset
    config_preset = fields.Selection([
        ('minimal', 'Minimal'),
        ('standard', 'Standard'),
        ('comprehensive', 'Comprehensive'),
        ('custom', 'Custom')
    ], string="Configuration Preset", default='standard')
    
    # Field Visibility Flags
    show_container_number = fields.Boolean(string="Show Container Number", default=True)
    show_description = fields.Boolean(string="Show Description", default=True)
    show_content_description = fields.Boolean(string="Show Content Description", default=True)
    show_date_ranges = fields.Boolean(string="Show Date Ranges", default=True)
    show_sequence_ranges = fields.Boolean(string="Show Sequence Ranges", default=False)
    show_destruction_date = fields.Boolean(string="Show Destruction Date", default=True)
    show_record_type = fields.Boolean(string="Show Record Type", default=True)
    show_confidentiality = fields.Boolean(string="Show Confidentiality", default=True)
    show_project_code = fields.Boolean(string="Show Project Code", default=False)
    show_client_reference = fields.Boolean(string="Show Client Reference", default=False)
    show_file_count = fields.Boolean(string="Show File Count", default=False)
    show_filing_system = fields.Boolean(string="Show Filing System", default=False)
    show_created_by_dept = fields.Boolean(string="Show Created By Department", default=False)
    show_authorized_by = fields.Boolean(string="Show Authorized By", default=False)
    show_special_handling = fields.Boolean(string="Show Special Handling", default=False)
    show_compliance_notes = fields.Boolean(string="Show Compliance Notes", default=False)
    show_weight_estimate = fields.Boolean(string="Show Weight Estimate", default=False)
    show_size_estimate = fields.Boolean(string="Show Size Estimate", default=False)
    
    # Required Field Flags
    require_container_number = fields.Boolean(string="Require Container Number", default=False)
    require_description = fields.Boolean(string="Require Description", default=True)
    require_content_description = fields.Boolean(string="Require Content Description", default=False)
    require_date_from = fields.Boolean(string="Require Date From", default=False)
    require_date_to = fields.Boolean(string="Require Date To", default=False)
    require_destruction_date = fields.Boolean(string="Require Destruction Date", default=False)
    require_record_type = fields.Boolean(string="Require Record Type", default=False)
    require_confidentiality = fields.Boolean(string="Require Confidentiality", default=False)
    require_project_code = fields.Boolean(string="Require Project Code", default=False)
    require_client_reference = fields.Boolean(string="Require Client Reference", default=False)
    require_sequence_from = fields.Boolean(string="Require Sequence From", default=False)
    require_sequence_to = fields.Boolean(string="Require Sequence To", default=False)
    
    # Computed Fields
    visible_field_count = fields.Integer(string="Visible Fields", compute='_compute_field_counts', store=True)
    required_field_count = fields.Integer(string="Required Fields", compute='_compute_field_counts', store=True)
    
    model_id = fields.Many2one(comodel_name='ir.model', string="Model", required=True, ondelete='cascade',
                               help="The model to add the new field to.")
    field_name = fields.Char(string="Technical Name", required=True, tracking=True,
                             help="The technical name of the field (e.g., x_custom_field).")
    field_type = fields.Selection([
        ('char', 'Char'),
        ('text', 'Text'),
        ('integer', 'Integer'),
        ('float', 'Float'),
        ('boolean', 'Boolean'),
        ('date', 'Date'),
        ('datetime', 'Datetime'),
        ('selection', 'Selection'),
        ('many2one', 'Many2one'),
    ], string="Field Type", required=True, default='char')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('deployed', 'Deployed'),
        ('error', 'Error'),
        ('archived', 'Archived')
    ], string="Status", default='draft', required=True, tracking=True, copy=False)

    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string="Help Text (Tooltip)")
    required = fields.Boolean(string="Required")
    readonly = fields.Boolean(string="Read-Only")
    tracking = fields.Boolean(string="Track Changes", default=True)
    
    # Relational Fields
    relation_model_id = fields.Many2one(comodel_name='ir.model', string="Relation Model",
                                        help="For Many2one fields, specify the target model.")
    
    # Selection Field
    selection_options = fields.Text(string="Selection Options", 
                                    help="For Selection fields, provide options as a Python list of tuples, e.g., [('key1', 'Value1'), ('key2', 'Value2')]")

    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('show_container_number', 'show_description', 'show_content_description', 
                 'show_date_ranges', 'show_sequence_ranges', 'show_destruction_date',
                 'show_record_type', 'show_confidentiality', 'show_project_code',
                 'show_client_reference', 'show_file_count', 'show_filing_system',
                 'show_created_by_dept', 'show_authorized_by', 'show_special_handling',
                 'show_compliance_notes', 'show_weight_estimate', 'show_size_estimate',
                 'require_container_number', 'require_description', 'require_content_description',
                 'require_date_from', 'require_date_to', 'require_destruction_date',
                 'require_record_type', 'require_confidentiality', 'require_project_code',
                 'require_client_reference', 'require_sequence_from', 'require_sequence_to')
    def _compute_field_counts(self):
        """Compute the number of visible and required fields."""
        for record in self:
            visible_fields = [
                record.show_container_number, record.show_description, record.show_content_description,
                record.show_date_ranges, record.show_sequence_ranges, record.show_destruction_date,
                record.show_record_type, record.show_confidentiality, record.show_project_code,
                record.show_client_reference, record.show_file_count, record.show_filing_system,
                record.show_created_by_dept, record.show_authorized_by, record.show_special_handling,
                record.show_compliance_notes, record.show_weight_estimate, record.show_size_estimate
            ]
            required_fields = [
                record.require_container_number, record.require_description, record.require_content_description,
                record.require_date_from, record.require_date_to, record.require_destruction_date,
                record.require_record_type, record.require_confidentiality, record.require_project_code,
                record.require_client_reference, record.require_sequence_from, record.require_sequence_to
            ]
            record.visible_field_count = sum(visible_fields)
            record.required_field_count = sum(required_fields)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('field_name')
    def _check_field_name_format(self):
        """Validate field name format to ensure it's a valid Python identifier."""
        for record in self:
            if not record.field_name.isidentifier() or record.field_name.startswith('_'):
                raise ValidationError(_("The technical field name '%s' is not valid. It must be a valid Python identifier and not start with an underscore.") % record.field_name)

    @api.constrains('field_type', 'relation_model_id')
    def _check_relation_model(self):
        """Ensure relation model is set for relational fields."""
        for record in self:
            if record.field_type == 'many2one' and not record.relation_model_id:
                raise ValidationError(_("A 'Relation Model' is required for Many2one fields."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_deploy(self):
        """Placeholder for deployment logic."""
        self.ensure_one()
        # In a real implementation, this would dynamically create an ir.model.fields record
        # and potentially alter database tables and views. This is a highly complex operation.
        self.message_post(body=_("Deployment action triggered. (This is a placeholder)."))
        self.write({'state': 'deployed'})

    def action_rollback(self):
        """Placeholder for rollback logic."""
        self.ensure_one()
        # This would involve removing the ir.model.fields record, and handling data migration.
        self.message_post(body=_("Rollback action triggered. (This is a placeholder)."))
        self.write({'state': 'draft'})

    def action_archive(self):
        """Archive the configuration."""
        self.ensure_one()
        self.write({'active': False, 'state': 'archived'})

    def action_setup_field_labels(self):
        """Open wizard to setup custom field labels."""
        self.ensure_one()
        # Return action to open field label customization wizard
        return {
            'type': 'ir.actions.act_window',
            'name': _('Customize Field Labels'),
            'res_model': 'field.label.customization',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id if hasattr(self, 'partner_id') else False,
                'default_department_id': self.department_id.id if hasattr(self, 'department_id') else False,
            }
        }
