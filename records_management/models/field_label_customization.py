from odoo import models, fields, api

class FieldLabelCustomization(models.Model):
    _name = 'field.label.customization'
    _description = 'Field Label Customization'
    _order = 'priority desc, name'

    name = fields.Char('Configuration Name', required=True)
    description = fields.Text('Description')
    model_name = fields.Char('Model Name', required=True)
    field_name = fields.Char('Field Name', required=True)
    original_label = fields.Char('Original Label', required=True)
    custom_label = fields.Char('Custom Label', required=True)
    priority = fields.Integer('Priority', default=1, help="Higher priority configurations override lower ones")

    # Industry-specific container label fields
    label_container_number = fields.Char('Container Number Label', default='Container Number')
    label_item_description = fields.Char('Item Description Label', default='Item Description')
    label_content_description = fields.Char('Content Description Label', default='Content Description')
    label_date_from = fields.Char('Date From Label', default='Date From')
    label_date_to = fields.Char('Date To Label', default='Date To')
    label_record_type = fields.Char('Record Type Label', default='Record Type')
    label_confidentiality = fields.Char('Confidentiality Label', default='Confidentiality')
    label_project_code = fields.Char('Project Code Label', default='Project Code')
    label_client_reference = fields.Char('Client Reference Label', default='Client Reference')
    label_authorized_by = fields.Char('Authorized By Label', default='Authorized By')
    label_created_by_dept = fields.Char('Created By Department Label', default='Created By Department')

    @api.model
    def get_custom_label(self, model_name, field_name, original_label):
        """Get the highest priority custom label for a field"""
        customization = self.search([
            ('model_name', '=', model_name),
            ('field_name', '=', field_name)
        ], order='priority desc', limit=1)

        if customization:
            return customization.custom_label
        return original_label

    @api.model
    def get_container_labels(self):
        """Get all container-related labels for the current configuration"""
        # Get the highest priority configuration
        config = self.search([], order='priority desc', limit=1)

        if config:
            return {
                'container_number': config.label_container_number,
                'item_description': config.label_item_description,
                'content_description': config.label_content_description,
                'date_from': config.label_date_from,
                'date_to': config.label_date_to,
                'record_type': config.label_record_type,
                'confidentiality': config.label_confidentiality,
                'project_code': config.label_project_code,
                'client_reference': config.label_client_reference,
                'authorized_by': config.label_authorized_by,
                'created_by_dept': config.label_created_by_dept,
            }

        # Return defaults if no configuration exists
        return {
            'container_number': 'Container Number',
            'item_description': 'Item Description',
            'content_description': 'Content Description',
            'date_from': 'Date From',
            'date_to': 'Date To',
            'record_type': 'Record Type',
            'confidentiality': 'Confidentiality',
            'project_code': 'Project Code',
            'client_reference': 'Client Reference',
            'authorized_by': 'Authorized By',
            'created_by_dept': 'Created By Department',
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
