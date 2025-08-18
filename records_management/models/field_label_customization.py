from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FieldLabelCustomization(models.Model):
    _name = 'field.label.customization'
    _description = 'Field Label Customization'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'model_name, field_name'
    _rec_name = 'full_customization_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True, tracking=True, help="A descriptive name for this customization rule.")
    description = fields.Text(string="Description", help="Explain the purpose of this label change.")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, help="Only active customizations will be applied.")
    
    model_id = fields.Many2one('ir.model', string='Model', required=True, ondelete='cascade',
                               domain=[('model', 'like', 'records.%')], help="The model to customize.")
    field_id = fields.Many2one('ir.model.fields', string='Field', required=True, ondelete='cascade',
                               domain="[('model_id', '=', model_id)]", help="The field to customize.")
    
    original_label = fields.Char(string='Original Label', related='field_id.field_description', readonly=True)
    custom_label = fields.Char(string='Custom Label', required=True, tracking=True)
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True)

    full_customization_name = fields.Char(string="Full Name", compute='_compute_full_customization_name', store=True)

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('model_id.model', 'field_id.name', 'custom_label')
    def _compute_full_customization_name(self):
        for record in self:
            if record.model_id and record.field_id:
                record.full_customization_name = _(
                    "[%s] %s -> %s",
                    record.model_id.model,
                    record.field_id.name,
                    record.custom_label
                )
            else:
                record.full_customization_name = record.name or _("New Customization")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('model_id', 'field_id')
    def _check_field_exists(self):
        for record in self:
            if record.model_id and record.field_id:
                if record.field_id.model_id != record.model_id:
                    raise ValidationError(_("The selected field does not belong to the selected model."))

    @api.constrains('custom_label')
    def _check_custom_label_length(self):
        for record in self:
            if record.custom_label and len(record.custom_label) > 100:
                raise ValidationError(_("Custom label cannot exceed 100 characters."))

    _sql_constraints = [
        ('unique_model_field', 'unique(model_id, field_id, company_id)', 
         'A customization for this field already exists for this company.')
    ]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activates the customization rule."""
        self.write({'state': 'active'})
        self.message_post(body=_("Customization activated."))

    def action_archive(self):
        """Archives the customization rule."""
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Customization archived."))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    @api.model
    def get_custom_labels(self, model_name):
        """
        Method to be called by other models to get all active customizations.
        Returns a dictionary mapping field names to their custom labels.
        """
        customizations = self.search([
            ('model_id.model', '=', model_name),
            ('state', '=', 'active'),
            ('company_id', 'in', [self.env.company.id, False])
        ])
        return {cust.field_id.name: cust.custom_label for cust in customizations}
