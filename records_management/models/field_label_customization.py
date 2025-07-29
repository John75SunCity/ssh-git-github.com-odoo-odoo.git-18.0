# -*- coding: utf-8 -*-
"""
Field Label Customization System
Allows different admin levels to customize field names/labels for their users
"""

from odoo import models, fields, api, _


class FieldLabelCustomization(models.Model):
    """
    Customizable field labels for different customer/department contexts
    Allows admins to rename fields to match their organization's terminology
    """

    _name = "field.label.customization"
    _description = "Field Label Customization"
    _order = "priority desc, customer_id, department_id"

    # ==========================================
    # CORE IDENTIFICATION
    # ==========================================
    name = fields.Char(
        string="Configuration Name",
        required=True,
        help="Name for this label configuration",
    )

    # Hierarchy: Global > Customer > Department
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain=[("is_company", "=", True)],
        help="Customer this applies to (leave blank for global)",
    )
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        help="Specific department (leave blank for customer-wide)",
    )

    priority = fields.Integer(
        string="Priority",
        default=10,
        help="Higher priority overrides lower (Department=30, Customer=20, Global=10)",
    )

    active = fields.Boolean(default=True)
    description = fields.Text(
        string="Description", help="Description of this customization set"
    )

    # ==========================================
    # CUSTOMIZABLE FIELD LABELS
    # ==========================================

    # Core identification fields
    label_container_number = fields.Char(
        string="Container Number Label",
        default="Container Number",
        help="Custom label for container number field",
    )
    label_item_description = fields.Char(
        string="Item Description Label",
        default="Item Description",
        help="Custom label for item description",
    )
    label_content_description = fields.Char(
        string="Content Description Label",
        default="Content Description",
        help="Custom label for content description",
    )

    # Date and sequence fields
    label_date_from = fields.Char(
        string="Date From Label",
        default="Date From",
        help="Custom label for start date",
    )
    label_date_to = fields.Char(
        string="Date To Label", default="Date To", help="Custom label for end date"
    )
    label_sequence_from = fields.Char(
        string="Sequence From Label",
        default="Sequence From",
        help="Custom label for sequence start",
    )
    label_sequence_to = fields.Char(
        string="Sequence To Label",
        default="Sequence To",
        help="Custom label for sequence end",
    )

    # Business fields
    label_destruction_date = fields.Char(
        string="Destruction Date Label",
        default="Destruction Date",
        help="Custom label for destruction date",
    )
    label_record_type = fields.Char(
        string="Record Type Label",
        default="Record Type",
        help="Custom label for record type",
    )
    label_confidentiality = fields.Char(
        string="Confidentiality Label",
        default="Confidentiality Level",
        help="Custom label for confidentiality",
    )
    label_project_code = fields.Char(
        string="Project Code Label",
        default="Project Code",
        help="Custom label for project code",
    )
    label_client_reference = fields.Char(
        string="Client Reference Label",
        default="Client Reference",
        help="Custom label for client reference",
    )
    label_file_count = fields.Char(
        string="File Count Label",
        default="Number of Files",
        help="Custom label for file count",
    )
    label_filing_system = fields.Char(
        string="Filing System Label",
        default="Filing System",
        help="Custom label for filing system",
    )
    label_created_by_dept = fields.Char(
        string="Created By Dept Label",
        default="Created By Department",
        help="Custom label for creating department",
    )
    label_authorized_by = fields.Char(
        string="Authorized By Label",
        default="Authorized By",
        help="Custom label for authorization",
    )
    label_special_handling = fields.Char(
        string="Special Handling Label",
        default="Special Handling Instructions",
        help="Custom label for special handling",
    )
    label_compliance_notes = fields.Char(
        string="Compliance Notes Label",
        default="Compliance Notes",
        help="Custom label for compliance notes",
    )
    label_weight_estimate = fields.Char(
        string="Weight Estimate Label",
        default="Estimated Weight",
        help="Custom label for weight estimate",
    )
    label_size_estimate = fields.Char(
        string="Size Estimate Label",
        default="Estimated Size",
        help="Custom label for size estimate",
    )

    # Hierarchical folder fields
    label_parent_container = fields.Char(
        string="Parent Container Label",
        default="Parent Container",
        help="Custom label for parent container reference",
    )
    label_folder_type = fields.Char(
        string="Folder Type Label",
        default="Item Type",
        help="Custom label for folder/item type",
    )
    label_hierarchy_display = fields.Char(
        string="Hierarchy Display Label",
        default="Location Path",
        help="Custom label for hierarchy path display",
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    customized_label_count = fields.Integer(
        string="Customized Labels",
        compute="_compute_customized_count",
        help="Number of labels that have been customized",
    )

    scope_display = fields.Char(
        string="Scope",
        compute="_compute_scope_display",
        help="Display scope: Global, Customer, or Department",
    )

    @api.depends(
        "label_container_number",
        "label_item_description",
        "label_content_description",
        "label_date_from",
        "label_date_to",
        "label_sequence_from",
        "label_sequence_to",
        "label_destruction_date",
        "label_record_type",
        "label_confidentiality",
        "label_project_code",
        "label_client_reference",
        "label_file_count",
    )
    def _compute_customized_count(self):
        """Count how many labels have been customized from defaults"""
        default_labels = {
            "label_container_number": "Container Number",
            "label_item_description": "Item Description",
            "label_content_description": "Content Description",
            "label_date_from": "Date From",
            "label_date_to": "Date To",
            "label_sequence_from": "Sequence From",
            "label_sequence_to": "Sequence To",
            "label_destruction_date": "Destruction Date",
            "label_record_type": "Record Type",
            "label_confidentiality": "Confidentiality Level",
            "label_project_code": "Project Code",
            "label_client_reference": "Client Reference",
            "label_file_count": "Number of Files",
            "label_filing_system": "Filing System",
            "label_created_by_dept": "Created By Department",
            "label_authorized_by": "Authorized By",
            "label_special_handling": "Special Handling Instructions",
            "label_compliance_notes": "Compliance Notes",
            "label_weight_estimate": "Estimated Weight",
            "label_size_estimate": "Estimated Size",
            "label_parent_container": "Parent Container",
            "label_folder_type": "Item Type",
            "label_hierarchy_display": "Location Path",
        }

        for record in self:
            customized = 0
            for field_name, default_value in default_labels.items():
                current_value = getattr(record, field_name)
                if current_value and current_value != default_value:
                    customized += 1
            record.customized_label_count = customized

    @api.depends("customer_id", "department_id")
    def _compute_scope_display(self):
        """Display the scope of this customization"""
        for record in self:
            if record.department_id:
                record.scope_display = f"Department: {record.department_id.name}"
            elif record.customer_id:
                record.scope_display = f"Customer: {record.customer_id.name}"
            else:
                record.scope_display = "Global (All Customers)"

    # ==========================================
    # LABEL RESOLUTION METHODS
    # ==========================================
    @api.model
    def get_labels_for_context(self, customer_id=None, department_id=None):
        """
        Get field labels for a specific context (customer/department)
        Returns a dictionary with field names and their custom labels
        """
        # Build search domain based on hierarchy
        domain = [("active", "=", True)]

        # Find all applicable configurations in order of priority
        configs = []

        # 1. Department-specific (highest priority)
        if department_id:
            dept_configs = self.search(
                domain + [("department_id", "=", department_id)], order="priority desc"
            )
            configs.extend(dept_configs)

        # 2. Customer-specific
        if customer_id:
            customer_configs = self.search(
                domain
                + [("customer_id", "=", customer_id), ("department_id", "=", False)],
                order="priority desc",
            )
            configs.extend(customer_configs)

        # 3. Global configurations (lowest priority)
        global_configs = self.search(
            domain + [("customer_id", "=", False), ("department_id", "=", False)],
            order="priority desc",
        )
        configs.extend(global_configs)

        # Start with default labels
        labels = {
            "container_number": "Container Number",
            "item_description": "Item Description",
            "content_description": "Content Description",
            "date_from": "Date From",
            "date_to": "Date To",
            "sequence_from": "Sequence From",
            "sequence_to": "Sequence To",
            "destruction_date": "Destruction Date",
            "record_type": "Record Type",
            "confidentiality": "Confidentiality Level",
            "project_code": "Project Code",
            "client_reference": "Client Reference",
            "file_count": "Number of Files",
            "filing_system": "Filing System",
            "created_by_dept": "Created By Department",
            "authorized_by": "Authorized By",
            "special_handling": "Special Handling Instructions",
            "compliance_notes": "Compliance Notes",
            "weight_estimate": "Estimated Weight",
            "size_estimate": "Estimated Size",
            "parent_container": "Parent Container",
            "folder_type": "Item Type",
            "hierarchy_display": "Location Path",
        }

        # Apply customizations in reverse order (global first, then customer, then department)
        for config in reversed(configs):
            for field_key in labels.keys():
                label_field = f"label_{field_key}"
                if hasattr(config, label_field):
                    custom_label = getattr(config, label_field)
                    if custom_label:
                        labels[field_key] = custom_label

        return labels

    @api.model
    def get_label_for_field(self, field_name, customer_id=None, department_id=None):
        """Get custom label for a specific field in context"""
        labels = self.get_labels_for_context(customer_id, department_id)
        return labels.get(field_name, field_name.replace("_", " ").title())

    # ==========================================
    # PRESET METHODS
    # ==========================================
    def action_apply_corporate_preset(self):
        """Apply corporate terminology preset"""
        self.ensure_one()
        self.write(
            {
                "label_container_number": "File Container ID",
                "label_item_description": "Document Category",
                "label_content_description": "Document Contents",
                "label_date_from": "Period Start",
                "label_date_to": "Period End",
                "label_record_type": "Document Classification",
                "label_confidentiality": "Security Level",
                "label_project_code": "Cost Center",
                "label_client_reference": "Matter Number",
                "label_authorized_by": "Department Head",
                "label_created_by_dept": "Originating Department",
            }
        )

    def action_apply_legal_preset(self):
        """Apply legal terminology preset"""
        self.ensure_one()
        self.write(
            {
                "label_container_number": "Matter Container",
                "label_item_description": "Case Documents",
                "label_content_description": "File Contents",
                "label_date_from": "Case Start Date",
                "label_date_to": "Case End Date",
                "label_record_type": "Document Type",
                "label_confidentiality": "Attorney-Client Privilege",
                "label_project_code": "Matter Code",
                "label_client_reference": "Client Matter Number",
                "label_authorized_by": "Supervising Attorney",
                "label_destruction_date": "Retention Expiry",
            }
        )

    def action_apply_healthcare_preset(self):
        """Apply healthcare terminology preset"""
        self.ensure_one()
        self.write(
            {
                "label_container_number": "Medical Records Container",
                "label_item_description": "Patient Records",
                "label_content_description": "Medical File Contents",
                "label_date_from": "Treatment Start",
                "label_date_to": "Treatment End",
                "label_record_type": "Record Category",
                "label_confidentiality": "HIPAA Classification",
                "label_project_code": "Department Code",
                "label_client_reference": "Patient ID",
                "label_authorized_by": "Chief Medical Officer",
                "label_special_handling": "HIPAA Special Instructions",
            }
        )

    def action_apply_financial_preset(self):
        """Apply financial services terminology preset"""
        self.ensure_one()
        self.write(
            {
                "label_container_number": "Account File Container",
                "label_item_description": "Financial Records",
                "label_content_description": "Account Documentation",
                "label_date_from": "Account Period Start",
                "label_date_to": "Account Period End",
                "label_record_type": "Financial Document Type",
                "label_confidentiality": "Regulatory Classification",
                "label_project_code": "Account Number",
                "label_client_reference": "Customer Account",
                "label_authorized_by": "Branch Manager",
                "label_compliance_notes": "Regulatory Notes",
            }
        )

    # ==========================================
    # UTILITY METHODS
    # ==========================================
    def action_reset_to_defaults(self):
        """Reset all labels to default values"""
        self.ensure_one()
        default_values = {
            "label_container_number": "Container Number",
            "label_item_description": "Item Description",
            "label_content_description": "Content Description",
            "label_date_from": "Date From",
            "label_date_to": "Date To",
            "label_sequence_from": "Sequence From",
            "label_sequence_to": "Sequence To",
            "label_destruction_date": "Destruction Date",
            "label_record_type": "Record Type",
            "label_confidentiality": "Confidentiality Level",
            "label_project_code": "Project Code",
            "label_client_reference": "Client Reference",
            "label_file_count": "Number of Files",
            "label_filing_system": "Filing System",
            "label_created_by_dept": "Created By Department",
            "label_authorized_by": "Authorized By",
            "label_special_handling": "Special Handling Instructions",
            "label_compliance_notes": "Compliance Notes",
            "label_weight_estimate": "Estimated Weight",
            "label_size_estimate": "Estimated Size",
            "label_parent_container": "Parent Container",
            "label_folder_type": "Item Type",
            "label_hierarchy_display": "Location Path",
        }
        self.write(default_values)

    @api.model
    def create_default_configurations(self):
        """Create default global configurations for common industry types"""
        # Check if we already have configurations
        if self.search_count([]) > 0:
            return

        # Create global corporate configuration
        corporate = self.create(
            {
                "name": "Corporate Standard",
                "description": "Standard corporate terminology",
                "priority": 5,
            }
        )
        corporate.action_apply_corporate_preset()

        # Create global legal configuration
        legal = self.create(
            {
                "name": "Legal Standard",
                "description": "Legal industry terminology",
                "priority": 5,
            }
        )
        legal.action_apply_legal_preset()
