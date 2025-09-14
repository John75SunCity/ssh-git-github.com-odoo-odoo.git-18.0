from odoo import models, fields, api


class FieldLabelConfig(models.Model):
    _name = 'field.label.config'
    _description = 'Field Label Configuration'
    _rec_name = 'name'

    name = fields.Char(
        string="Configuration Name",
        required=True,
        help="Name of this field label configuration"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Partner",
        help="Partner this configuration applies to"
    )

    description = fields.Text(
        string="Description",
        help="Description of this configuration"
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

    active = fields.Boolean(string="Active", default=True)

    required_field_count = fields.Integer(
        string="Required Field Count",
        compute='_compute_field_stats',
        help="Number of required fields in configuration"
    )
    visible_field_count = fields.Integer(
        string="Visible Field Count",
        compute='_compute_field_stats',
        help="Number of visible fields in configuration"
    )
    customized_label_count = fields.Integer(
        string="Customized Label Count",
        compute='_compute_field_stats',
        help="Number of customized labels"
    )

    @api.depends(
        'require_client_reference', 'require_confidentiality', 'require_container_number',
        'require_content_description', 'require_date_from', 'require_date_to',
        'require_description', 'require_destruction_date', 'require_project_code',
        'require_record_type', 'require_sequence_from', 'require_sequence_to',
        'show_authorized_by', 'show_client_reference', 'show_compliance_notes',
        'show_confidentiality', 'show_container_number', 'show_content_description',
        'show_created_by_dept', 'show_date_ranges', 'show_description',
        'show_destruction_date', 'show_file_count', 'show_filing_system',
        'show_project_code', 'show_record_type', 'show_sequence_ranges',
        'show_size_estimate', 'show_special_handling', 'show_weight_estimate',
        'label_authorized_by', 'label_client_reference', 'label_compliance_notes',
        'label_confidentiality', 'label_container_number', 'label_content_description',
        'label_created_by_dept', 'label_date_from', 'label_date_to',
        'label_destruction_date', 'label_file_count', 'label_filing_system',
        'label_folder_type', 'label_hierarchy_display', 'label_item_description',
        'label_parent_container', 'label_project_code', 'label_record_type',
        'label_sequence_from', 'label_sequence_to', 'label_size_estimate',
        'label_special_handling', 'label_weight_estimate'
    )
    def _compute_field_stats(self):
        """Compute field configuration statistics"""
        for config in self:
            # Count required fields
            required_fields = [
                config.require_client_reference,
                config.require_confidentiality,
                config.require_container_number,
                config.require_content_description,
                config.require_date_from,
                config.require_date_to,
                config.require_description,
                config.require_destruction_date,
                config.require_project_code,
                config.require_record_type,
                config.require_sequence_from,
                config.require_sequence_to
            ]
            config.required_field_count = sum(1 for req in required_fields if req)

            # Count visible fields
            visible_fields = [
                config.show_authorized_by,
                config.show_client_reference,
                config.show_compliance_notes,
                config.show_confidentiality,
                config.show_container_number,
                config.show_content_description,
                config.show_created_by_dept,
                config.show_date_ranges,
                config.show_description,
                config.show_destruction_date,
                config.show_file_count,
                config.show_filing_system,
                config.show_project_code,
                config.show_record_type,
                config.show_sequence_ranges,
                config.show_size_estimate,
                config.show_special_handling,
                config.show_weight_estimate
            ]
            config.visible_field_count = sum(1 for vis in visible_fields if vis)

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
                current_value = getattr(config, field_name)
                if current_value and current_value != default_value:
                    customized_count += 1
            config.customized_label_count = customized_count
