# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FieldLabelCustomization(models.Model):
    _name = "field.label.customization"
    _description = "Field Label Customization"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(
        string="Description", help="Description of this field label customization set"
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    priority = fields.Integer(
        string="Priority",
        default=50,
        help="Priority level (1-100, lower numbers = higher priority)",
    )

    # ============================================================================
    # CUSTOMIZATION SPECIFICATIONS
    # ============================================================================
    model_name = fields.Char(string="Model Name", required=True)
    field_name = fields.Char(string="Field Name", required=True)
    original_label = fields.Char(string="Original Label")
    custom_label = fields.Char(string="Custom Label", required=True)

    # Label configuration
    label_template = fields.Selection(
        [
            ("standard", "Standard"),
            ("verbose", "Verbose"),
            ("abbreviated", "Abbreviated"),
            ("technical", "Technical"),
        ],
        string="Label Template",
        default="standard",
    )

    label_language = fields.Selection(
        [("en", "English"), ("es", "Spanish"), ("fr", "French")],
        string="Language",
        default="en",
    )

    label_size = fields.Selection(
        [("small", "Small"), ("medium", "Medium"), ("large", "Large")],
        string="Label Size",
        default="medium",
    )

    # ============================================================================
    # SCOPE AND APPLICATION
    # ============================================================================
    scope = fields.Selection(
        [
            ("global", "Global"),
            ("company", "Company"),
            ("user", "User Specific"),
            ("department", "Department"),
        ],
        string="Scope",
        default="company",
    )

    department_ids = fields.Many2many("hr.department", string="Departments")
    user_ids = fields.Many2many("res.users", string="Specific Users")

    # ============================================================================
    # COMPLIANCE AND INDUSTRY
    # ============================================================================
    industry_type = fields.Selection(
        [
            ("healthcare", "Healthcare"),
            ("finance", "Finance"),
            ("legal", "Legal"),
            ("manufacturing", "Manufacturing"),
            ("education", "Education"),
            ("government", "Government"),
            ("generic", "Generic"),
        ],
        string="Industry Type",
        default="generic",
    )

    compliance_framework = fields.Selection(
        [
            ("hipaa", "HIPAA"),
            ("gdpr", "GDPR"),
            ("sox", "SOX"),
            ("iso27001", "ISO 27001"),
            ("naid", "NAID AAA"),
            ("custom", "Custom"),
        ],
        string="Compliance Framework",
    )

    security_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Security Classification",
        default="internal",
    )

    # ============================================================================
    # CONTAINER/INVENTORY FIELD LABELS (Customer Customizable)
    # ============================================================================
    label_container_number = fields.Char(
        string="Container Number Label",
        default="Container Number",
        help="Custom label for container/box number field",
    )
    label_item_description = fields.Char(
        string="Item Description Label",
        default="Item Description",
        help="Custom label for item description field",
    )
    label_content_description = fields.Char(
        string="Content Description Label",
        default="Content Description",
        help="Custom label for content description field",
    )
    label_date_from = fields.Char(
        string="Date From Label",
        default="Date From",
        help="Custom label for start date field",
    )
    label_date_to = fields.Char(
        string="Date To Label",
        default="Date To",
        help="Custom label for end date field",
    )
    label_record_type = fields.Char(
        string="Record Type Label",
        default="Record Type",
        help="Custom label for record type classification field",
    )
    label_confidentiality = fields.Char(
        string="Confidentiality Label",
        default="Confidentiality",
        help="Custom label for confidentiality/security level field",
    )
    label_project_code = fields.Char(
        string="Project Code Label",
        default="Project Code",
        help="Custom label for project/cost center code field",
    )
    label_client_reference = fields.Char(
        string="Client Reference Label",
        default="Client Reference",
        help="Custom label for client reference/matter number field",
    )
    label_authorized_by = fields.Char(
        string="Authorized By Label",
        default="Authorized By",
        help="Custom label for authorization/approval field",
    )
    label_created_by_dept = fields.Char(
        string="Created By Department Label",
        default="Created By Department",
        help="Custom label for originating department field",
    )

    # ============================================================================
    # DEPLOYMENT & VERSIONING
    # ============================================================================
    deployment_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("deployed", "Deployed"),
            ("failed", "Failed"),
            ("rolled_back", "Rolled Back"),
        ],
        string="Deployment Status",
        default="pending",
        tracking=True,
    )

    version = fields.Char(string="Version", default="1.0")
    deployment_date = fields.Datetime(string="Deployment Date")
    rollback_date = fields.Datetime(string="Rollback Date")

    # ============================================================================
    # VALIDATION & TESTING
    # ============================================================================
    validation_rules = fields.Text(string="Validation Rules")
    test_results = fields.Text(string="Test Results")
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By")
    approval_date = fields.Datetime(string="Approval Date")

    # ============================================================================
    # BATCH-GENERATED FIELDS (From Ultimate Batch Fixer)
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    department_id = fields.Many2one("hr.department", string="Department", tracking=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail framework fields
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    @api.depends("deployment_status", "deployment_date")
    def _compute_is_deployed(self):
        for record in self:
            record.is_deployed = (
                record.deployment_status == "deployed" and record.deployment_date
            )

    @api.depends("model_name", "field_name", "custom_label")
    def _compute_full_customization_name(self):
        for record in self:
            if record.model_name and record.field_name:
                record.full_customization_name = _("%s.%s: %s", 
                    record.model_name, record.field_name, record.custom_label or "Custom Label"
                )
            else:
                record.full_customization_name = _("Incomplete Configuration")
                record.full_customization_name = record.name

    @api.depends("model_name")
    def _compute_available_fields(self):
        """Compute available fields for the selected model"""
        for record in self:
            if record.model_name and record._is_records_management_model(
                record.model_name
            ):
                try:
                    model = self.env[record.model_name]
                    fields_list = []
                    for field_name, field in model._fields.items():
                        if not field_name.startswith("_") and field_name not in [
                            "id",
                            "create_date",
                            "write_date",
                            "create_uid",
                            "write_uid",
                        ]:
                            fields_list.append(
                                f"{field_name} ({field.string or field_name})"
                            )
                    record.available_fields = "\n".join(sorted(fields_list))
                except Exception:
                    record.available_fields = "Invalid model selected"
            else:
            pass
            pass
                record.available_fields = (
                    "No model selected or model not in records_management"
                )

    is_deployed = fields.Boolean(compute="_compute_is_deployed", string="Is Deployed")
    full_customization_name = fields.Char(
        compute="_compute_full_customization_name", string="Full Customization Name"
    )
    available_fields = fields.Text(
        compute="_compute_available_fields",
        string="Available Fields",
        help="List of fields available for customization in the selected model",
    )

    # ============================================================================
    label_box_number = fields.Char(string='Box Number Label', default='Box Number')
    # HELPER METHODS
    # ============================================================================
    @api.model
    def _get_records_management_models(self):
        """Get all models that belong to records_management module"""
        records_models = []
        for model_name in self.env.registry:
            try:
                model = self.env[model_name]
                # Check if model belongs to records_management module
                if hasattr(model, "_module") and model._module == "records_management":
                    records_models.append(model_name)
                elif model_name.startswith(
                    ("records.", "naid.", "customer.", "portal.")
                ):
            pass
                    # Additional check for records management related models
                    records_models.append(model_name)
            except Exception:
                continue
        return sorted(records_models)

    def _is_records_management_model(self, model_name):
        """Check if a model belongs to records_management module"""
        try:
            if model_name not in self.env.registry:
                return False

            model = self.env[model_name]
            # Check if model belongs to records_management module
            if hasattr(model, "_module") and model._module == "records_management":
                return True

            # Additional check for records management related models by naming convention
            if model_name.startswith(
                ("records.", "naid.", "customer.", "portal.", "field.label")
            ):
                return True

            return False
        except Exception:
            return False

    def _is_protected_search_field(self, model_name, field_name):
        """Check if a field is protected from customization (critical for search functionality)"""
        # Define protected fields by model
        protected_fields = {
            "records.container": {
                # Core search functionality fields
                "alpha_range_start",
                "alpha_range_end",
                "alpha_range_display",
                "content_date_from",
                "content_date_to",
                "content_date_range_display",
                "primary_content_type",
                "search_keywords",
                "customer_sequence_start",
                "customer_sequence_end",
                # Core identification fields
                "name",
                "barcode",
                "container_number",
                # Critical search database fields
                "partner_id",
                "location_id",
                "state",
            },
            "records.document": {
                # Document search fields
                "name",
                "document_name",
                "barcode",
                "partner_id",
                "container_id",
                "document_type_id",
                # Content classification for search
                "content_description",
                "keywords",
            },
            "records.location": {
                # Location search fields
                "name",
                "barcode",
                "location_code",
                "warehouse_id",
                "parent_location_id",
            },
            # Add other models with search-critical fields
            "portal.request": {
                "name",
                "partner_id",
                "state",
                "request_type",
            },
        }

        return field_name in protected_fields.get(model_name, set())

    @api.model
    def get_model_field_options(self):
        """Return available models and their fields for selection"""
        result = {}
        for model_name in self._get_records_management_models():
            try:
                model = self.env[model_name]
                fields_info = {}
                for field_name, field in model._fields.items():
                    if not field_name.startswith("_") and field_name not in [
                        "id",
                        "create_date",
                        "write_date",
                        "create_uid",
                        "write_uid",
                    ]:
                        fields_info[field_name] = {
                            "string": field.string or field_name,
                            "type": field.type,
                            "help": field.help or "",
                        }
                result[model_name] = {
                    "description": getattr(model, "_description", model_name),
                    "fields": fields_info,
                }
            except Exception:
                continue
        return result

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("model_name")
    def _check_model_in_records_management(self):
        """Ensure the model belongs to records_management module"""
        for record in self:
            if record.model_name:
                if not record._is_records_management_model(record.model_name):
                    available_models = record._get_records_management_models()
                    raise ValidationError(
                        _(
                            "Model '%s' is not part of the records_management module.\n"
                            "Available models:\n%s"
                        )
                        % (
                            record.model_name,
                            "\n".join(
                                available_models[:10] + ["..."]
                                if len(available_models) > 10
                                else available_models
                            ),
                        )
                    )

    @api.constrains("model_name", "field_name")
    def _check_field_exists(self):
        for record in self:
            if record.model_name and record.field_name:
                # First check if model is in records_management
                if not record._is_records_management_model(record.model_name):
                    raise ValidationError(
                        _("Model '%s' is not part of the records_management module.", record.model_name)
                    )

                # Check if field is protected from customization
                if record._is_protected_search_field(
                    record.model_name, record.field_name
                ):
                    raise ValidationError(
                        _(
                            "Field '%s' in model '%s' is protected and cannot be customized. "
                            "This field is critical for the intelligent search functionality."
                        )
                        % (record.field_name, record.model_name)
                    )

                # Then validate that the field exists
                try:
                    if record.model_name not in self.env.registry:
                        raise ValidationError(
                            _("Model '%s' does not exist.", record.model_name)
                        )

                    model = self.env[record.model_name]
                    if record.field_name not in model._fields:
                        # Get available fields for helpful error message
                        available_fields = [
                            f
                            for f in model._fields.keys()
                            if not f.startswith("_")
                            and f
                            not in [
                                "id",
                                "create_date",
                                "write_date",
                                "create_uid",
                                "write_uid",
                            ]
                        ]
                        raise ValidationError(
                            _(
                                "Field '%s' does not exist in model '%s'.\n"
                                "Available fields:\n%s"
                            )
                            % (
                                record.field_name,
                                record.model_name,
                                "\n".join(
                                    sorted(available_fields)[:20] + ["..."]
                                    if len(available_fields) > 20
                                    else sorted(available_fields)
                                ),
                            )
                        )
                except Exception:
                    raise ValidationError(
                        _("Model '%s' does not exist.", record.model_name)
                    )

    @api.constrains("custom_label")
    def _check_custom_label_length(self):
        for record in self:
            if record.custom_label and len(record.custom_label) > 100:
                raise ValidationError(_("Custom label cannot exceed 100 characters."))

    @api.onchange("model_name")
    def _onchange_model_name(self):
        """Clear field_name when model changes and show available fields"""
        if self.model_name:
            self.field_name = False
            if not self._is_records_management_model(self.model_name):
                return {
                    "warning": {
                        "title": _("Invalid Model"),
                        "message": _(
                            "The selected model is not part of the records_management module. "
                            "Please select a valid records_management model."
                        ),
                    }
                }

    @api.onchange("field_name")
    def _onchange_field_name(self):
        """Auto-populate original_label when field is selected"""
        if self.model_name and self.field_name:
            try:
                model = self.env[self.model_name]
                if self.field_name in model._fields:
                    field = model._fields[self.field_name]
                    self.original_label = field.string or self.field_name
                    if not self.custom_label:
                        self.custom_label = self.original_label
            except Exception:
                pass

    # ============================================================================
    # BATCH-GENERATED ACTION METHODS (Ultimate Batch Fixer)
    # ============================================================================
    def action_apply_corporate_preset(self):
        """Apply Corporate Preset - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Corporate Preset"),
            "res_model": "field.label.customization",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_apply_financial_preset(self):
        """Apply Financial Preset - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Financial Preset"),
            "res_model": "field.label.customization",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_apply_healthcare_preset(self):
        """Apply Healthcare Preset - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Healthcare Preset"),
            "res_model": "field.label.customization",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_apply_legal_preset(self):
        """Apply Legal Preset - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Legal Preset"),
            "res_model": "field.label.customization",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_reset_to_defaults(self):
        """Reset To Defaults - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Reset To Defaults"),
            "res_model": "field.label.customization",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
