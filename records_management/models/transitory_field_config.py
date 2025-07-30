# -*- coding: utf-8 -*-
"""
Transitory Items Field Configuration
Admin control over which fields are visible/required for customers
"""

from odoo import models, fields, api, _


class TransitoryFieldConfig(models.Model):
    """
    Configuration for transitory items fields per customer
    Allows admins to control which fields customers see and which are required
    """

    _name = "transitory.field.config"
    _description = "Transitory Items Field Configuration"
    _rec_name = "customer_id"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Configuration Name", compute="_compute_name", store=True)
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        domain=[("is_company", "=", True)],
        help="Customer this configuration applies to",
    )
    department_id = fields.Many2one(
        "records.department", string="Department", help="Specific department (optional)"
    )
    active = fields.Boolean(default=True)

    # Field label customization integration
    field_label_config_id = fields.Many2one(
        "field.label.customization",
        string="Field Label Configuration",
        help="Custom field labels for this customer/department",
    )

    # ==========================================
    # FIELD VISIBILITY CONTROLS
    # ==========================================
    # Core identification
    show_container_number = fields.Boolean(string="Show Container Number", default=True)
    show_description = fields.Boolean(string="Show Item Description", default=True)
    show_content_description = fields.Boolean(
        string="Show Content Description", default=True
    )

    # Business fields
    show_date_ranges = fields.Boolean(string="Show Date Ranges", default=True)
    show_sequence_ranges = fields.Boolean(string="Show Sequence Ranges", default=True)
    show_destruction_date = fields.Boolean(
        string="Show Destruction Date", default=False
    )
    show_record_type = fields.Boolean(string="Show Record Type", default=True)
    show_confidentiality = fields.Boolean(
        string="Show Confidentiality Level", default=False
    )
    show_project_code = fields.Boolean(string="Show Project Code", default=False)
    show_client_reference = fields.Boolean(
        string="Show Client Reference", default=False
    )
    show_file_count = fields.Boolean(string="Show File Count", default=False)
    show_filing_system = fields.Boolean(string="Show Filing System", default=False)
    show_created_by_dept = fields.Boolean(
        string="Show Created By Department", default=False
    )
    show_authorized_by = fields.Boolean(string="Show Authorized By", default=False)
    show_special_handling = fields.Boolean(
        string="Show Special Handling", default=False
    )
    show_compliance_notes = fields.Boolean(
        string="Show Compliance Notes", default=False
    )
    show_weight_estimate = fields.Boolean(string="Show Weight Estimate", default=False)
    show_size_estimate = fields.Boolean(string="Show Size Estimate", default=False)

    # ==========================================
    # FIELD REQUIREMENT CONTROLS
    # ==========================================
    require_container_number = fields.Boolean(
        string="Require Container Number", default=True
    )
    require_description = fields.Boolean(
        string="Require Item Description", default=True
    )
    require_content_description = fields.Boolean(
        string="Require Content Description", default=False
    )
    require_date_from = fields.Boolean(string="Require Date From", default=False)
    require_date_to = fields.Boolean(string="Require Date To", default=False)
    require_sequence_from = fields.Boolean(
        string="Require Sequence From", default=False
    )
    require_sequence_to = fields.Boolean(string="Require Sequence To", default=False)
    require_destruction_date = fields.Boolean(
        string="Require Destruction Date", default=False
    )
    require_record_type = fields.Boolean(string="Require Record Type", default=False)
    require_confidentiality = fields.Boolean(
        string="Require Confidentiality Level", default=False
    )
    require_project_code = fields.Boolean(string="Require Project Code", default=False)
    require_client_reference = fields.Boolean(
        string="Require Client Reference", default=False
    )

    # ==========================================
    # PRESET CONFIGURATIONS
    # ==========================================
    config_preset = fields.Selection(
        [
            ("minimal", "Minimal (Container #, Description only)"),
            ("basic", "Basic (Container #, Description, Date Ranges)"),
            ("standard", "Standard (Common business fields)"),
            ("comprehensive", "Comprehensive (All fields)"),
            ("custom", "Custom Configuration"),
        ],
        string="Configuration Preset",
        default="basic",
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    visible_field_count = fields.Integer(
        string="Visible Fields", compute="_compute_field_counts"
    )
    required_field_count = fields.Integer(
        string="Required Fields", compute="_compute_field_counts"
    )

    @api.depends("customer_id", "department_id")
    def _compute_name(self):
        """Generate name based on customer/department"""
        for record in self:
            if record.department_id:
                record.name = f"{record.customer_id.name} - {record.department_id.name}"
            elif record.customer_id:
                record.name = f"{record.customer_id.name} - Field Configuration"
            else:
                record.name = "Field Configuration"

    @api.depends(
        "show_container_number",
        "show_description", 
        "show_content_description",
        "show_date_ranges",
        "show_sequence_ranges",
        "show_destruction_date",
        "show_record_type",
        "show_confidentiality",
        "show_project_code",
        "show_client_reference",
        "show_file_count",
        "show_filing_system",
        "show_created_by_dept",
        "show_authorized_by",
        "show_special_handling",
        "show_compliance_notes", 
        "show_weight_estimate",
        "show_size_estimate",
        "require_container_number",
        "require_description",
        "require_content_description",
        "require_date_from",
        "require_date_to",
        "require_sequence_from",
        "require_sequence_to",
        "require_destruction_date",
        "require_record_type",
        "require_confidentiality",
        "require_project_code",
        "require_client_reference",
    )
    def _compute_field_counts(self):
        """Count visible and required fields"""
        for record in self:
            # Count visible fields
            visible_fields = [
                record.show_container_number,
                record.show_description,
                record.show_content_description,
                record.show_date_ranges,
                record.show_sequence_ranges,
                record.show_destruction_date,
                record.show_record_type,
                record.show_confidentiality,
                record.show_project_code,
                record.show_client_reference,
                record.show_file_count,
                record.show_filing_system,
                record.show_created_by_dept,
                record.show_authorized_by,
                record.show_special_handling,
                record.show_compliance_notes,
                record.show_weight_estimate,
                record.show_size_estimate,
            ]
            record.visible_field_count = sum(bool(field) for field in visible_fields)

            # Count required fields
            required_fields = [
                record.require_container_number,
                record.require_description,
                record.require_content_description,
                record.require_date_from,
                record.require_date_to,
                record.require_sequence_from,
                record.require_sequence_to,
                record.require_destruction_date,
                record.require_record_type,
                record.require_confidentiality,
                record.require_project_code,
                record.require_client_reference,
            ]
            record.required_field_count = sum(bool(field) for field in required_fields)

    # ==========================================
    # PRESET APPLICATION METHODS
    # ==========================================
    @api.onchange("config_preset")
    def _onchange_config_preset(self):
        """Apply preset configuration"""
        if self.config_preset == "minimal":
            self._apply_minimal_preset()
        elif self.config_preset == "basic":
            self._apply_basic_preset()
        elif self.config_preset == "standard":
            self._apply_standard_preset()
        elif self.config_preset == "comprehensive":
            self._apply_comprehensive_preset()

    def _apply_minimal_preset(self):
        """Minimal configuration: Container number and description only"""
        # Show only essential fields
        self.update(
            {
                "show_container_number": True,
                "show_description": True,
                "show_content_description": False,
                "show_date_ranges": False,
                "show_sequence_ranges": False,
                "show_destruction_date": False,
                "show_record_type": False,
                "show_confidentiality": False,
                "show_project_code": False,
                "show_client_reference": False,
                "show_file_count": False,
                "show_filing_system": False,
                "show_created_by_dept": False,
                "show_authorized_by": False,
                "show_special_handling": False,
                "show_compliance_notes": False,
                "show_weight_estimate": False,
                "show_size_estimate": False,
                # Requirements
                "require_container_number": True,
                "require_description": True,
                "require_content_description": False,
                "require_date_from": False,
                "require_date_to": False,
            }
        )

    def _apply_basic_preset(self):
        """Basic configuration: Container number, description, date ranges"""
        self.update(
            {
                "show_container_number": True,
                "show_description": True,
                "show_content_description": True,
                "show_date_ranges": True,
                "show_sequence_ranges": True,
                "show_destruction_date": False,
                "show_record_type": True,
                "show_confidentiality": False,
                "show_project_code": False,
                "show_client_reference": False,
                "show_file_count": False,
                "show_filing_system": False,
                "show_created_by_dept": False,
                "show_authorized_by": False,
                "show_special_handling": False,
                "show_compliance_notes": False,
                "show_weight_estimate": False,
                "show_size_estimate": False,
                # Requirements
                "require_container_number": True,
                "require_description": True,
                "require_content_description": False,
                "require_date_from": False,
                "require_date_to": False,
            }
        )

    def _apply_standard_preset(self):
        """Standard configuration: Common business fields"""
        self.update(
            {
                "show_container_number": True,
                "show_description": True,
                "show_content_description": True,
                "show_date_ranges": True,
                "show_sequence_ranges": True,
                "show_destruction_date": True,
                "show_record_type": True,
                "show_confidentiality": True,
                "show_project_code": True,
                "show_client_reference": True,
                "show_file_count": True,
                "show_filing_system": True,
                "show_created_by_dept": True,
                "show_authorized_by": False,
                "show_special_handling": False,
                "show_compliance_notes": False,
                "show_weight_estimate": False,
                "show_size_estimate": False,
                # Requirements
                "require_container_number": True,
                "require_description": True,
                "require_content_description": True,
                "require_date_from": True,
                "require_date_to": True,
            }
        )

    def _apply_comprehensive_preset(self):
        """Comprehensive configuration: All fields visible"""
        # Set all show_ fields to True
        show_fields = [field for field in self._fields if field.startswith("show_")]
        for field in show_fields:
            setattr(self, field, True)

        # Set reasonable requirements
        self.update(
            {
                "require_container_number": True,
                "require_description": True,
                "require_content_description": True,
                "require_record_type": True,
            }
        )

    # ==========================================
    # UTILITY METHODS
    # ==========================================
    @api.model
    def get_config_for_customer(self, customer_id, department_id=None):
        """Get field configuration for a specific customer/department"""
        domain = [("customer_id", "=", customer_id)]
        if department_id:
            domain.append(("department_id", "=", department_id))

        config = self.search(domain, limit=1)
        if not config:
            # Try without department filter
            config = self.search([("customer_id", "=", customer_id)], limit=1)

        if not config:
            # Create default config
            config = self.create(
                {
                    "customer_id": customer_id,
                    "department_id": department_id,
                    "config_preset": "basic",
                }
            )
            config._apply_basic_preset()

        return config

    def get_field_config_dict(self):
        """Returns the field configuration as a dictionary"""
        self.ensure_one()
        return {
            "visible_fields": {
                "container_number": self.show_container_number,
                "description": self.show_description,
                "content_description": self.show_content_description,
                "date_ranges": self.show_date_ranges,
                "sequence_ranges": self.show_sequence_ranges,
                "destruction_date": self.show_destruction_date,
                "record_type": self.show_record_type,
                "confidentiality": self.show_confidentiality,
                "project_code": self.show_project_code,
                "client_reference": self.show_client_reference,
                "file_count": self.show_file_count,
                "filing_system": self.show_filing_system,
                "created_by_dept": self.show_created_by_dept,
                "authorized_by": self.show_authorized_by,
                "special_handling": self.show_special_handling,
                "compliance_notes": self.show_compliance_notes,
                "weight_estimate": self.show_weight_estimate,
                "size_estimate": self.show_size_estimate,
            },
            "required_fields": {
                "container_number": self.require_container_number,
                "description": self.require_description,
                "content_description": self.require_content_description,
                "date_from": self.require_date_from,
                "date_to": self.require_date_to,
                "sequence_from": self.require_sequence_from,
                "sequence_to": self.require_sequence_to,
                "destruction_date": self.require_destruction_date,
                "record_type": self.require_record_type,
                "confidentiality": self.require_confidentiality,
                "project_code": self.require_project_code,
                "client_reference": self.require_client_reference,
            },
        }

    def get_field_labels(self):
        """Get custom field labels for this configuration"""
        self.ensure_one()

        # Get labels from field label customization system
        labels = self.env["field.label.customization"].get_labels_for_context(
            customer_id=self.customer_id.id,
            department_id=self.department_id.id if self.department_id else None,
        )

        return labels

    def action_setup_field_labels(self):
        """Setup custom field labels for this configuration"""
        self.ensure_one()

        if not self.field_label_config_id:
            # Create new label configuration
            config_name = f"Labels for {self.customer_id.name}"
            if self.department_id:
                config_name += f" - {self.department_id.name}"

            label_config = self.env["field.label.customization"].create(
                {
                    "name": config_name,
                    "customer_id": self.customer_id.id,
                    "department_id": (
                        self.department_id.id if self.department_id else False
                    ),
                    "priority": (
                        30 if self.department_id else 20
                    ),  # Department gets higher priority
                    "description": f"Custom field labels for {config_name}",
                }
            )
            self.field_label_config_id = label_config.id

        return {
            "type": "ir.actions.act_window",
            "name": "Customize Field Labels",
            "view_mode": "form",
            "res_model": "field.label.customization",
            "res_id": self.field_label_config_id.id,
            "target": "new",
        }
