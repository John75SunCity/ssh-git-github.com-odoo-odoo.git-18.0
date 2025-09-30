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
