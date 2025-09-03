from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RmModuleConfigurator(models.Model):
    """
    This model manages the configuration settings for the Records Management module.

    It provides a centralized way to define, store, and manage various configuration options
    such as feature toggles, field visibility rules, system parameters, and domain rules.
    Each configuration can be categorized, targeted to specific models or fields, and
    associated with a company for multi-company environments.

    Key Features:
    - Supports multiple configuration types: field visibility, feature toggles, parameters, and domain rules.
    - Allows targeting of specific models and fields for UI-related configurations.
    - Tracks modifications with auditing fields (e.g., last modified, modified by, modification count).
    - Enforces constraints to ensure data integrity, such as unique configuration keys per company
      and valid value types for parameters.
    - Provides a high-performance method (`get_config_parameter`) to retrieve configuration values
      with caching for optimal performance.
    - Includes functionality to apply configurations by clearing server-side caches.

    Fields:
    - Configuration Definition: Includes fields like `name`, `category`, `config_type`, and `config_key`.
    - Configuration Value: Supports multiple value types (text, boolean, number, selection).
    - Targeting: Allows specifying target models and fields for UI/domain rules.
    - Auditing: Tracks who modified the configuration and when, along with internal notes.

    Constraints:
    - Ensures only one value type is set for parameters.
    - Validates that target models and fields are set for UI-related configurations.

    Example Use Case:
    - A feature toggle to enable or disable a specific functionality in the customer portal.
    - A field visibility rule to hide or make a field read-only based on user roles.

    Methods:
    - `create`: Overrides the create method to initialize auditing fields.
    - `write`: Overrides the write method to track modifications and clear caches.
    - `get_config_parameter`: Retrieves a configuration value efficiently.
    - `action_apply_configuration`: Applies the configuration by clearing caches.

    SQL Constraints:
    - Ensures the uniqueness of configuration keys per company.

    This model is critical for ensuring the flexibility and extendability of the Records Management module.
    """

    _name = "rm.module.configurator"
    _description = "Records Management Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "category, sequence, name"
    _rec_name = "name"

    # ============================================================================
    # FIELDS - Configuration Definition
    # ============================================================================
    name = fields.Char(string="Configuration Name", required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(
        default=True, help="Only active configurations are applied."
    )
    company_id = fields.Many2one(
        comodel_name="res.company",
        string="Company",
        default=lambda self: self.env.company,
        help="Configuration specific to a company. Leave empty for global.",
    )

    category = fields.Selection(
        [
            ("ui", "User Interface"),
            ("workflow", "Workflow"),
            ("billing", "Billing"),
            ("compliance", "Compliance & NAID"),
            ("fsm", "Field Service"),
            ("portal", "Customer Portal"),
            ("reporting", "Reporting"),
            ("security", "Security"),
            ("system", "System"),
        ],
        string="Category",
        required=True,
        default="system",
    )

    config_type = fields.Selection(
        [
            ("field_visibility", "Field Visibility"),
            ("feature_toggle", "Feature Toggle"),
            ("parameter", "System Parameter"),
            ("domain_rule", "Domain Rule"),
        ],
        string="Configuration Type",
        required=True,
        default="parameter",
    )

    description = fields.Text(
        string="Description",
        help="Explain what this configuration does and its impact.",
    )
    help_text = fields.Text(
        string="Help Text", help="Additional help text for this configuration option."
    )
    config_key = fields.Char(
        string="Technical Key",
        required=True,
        copy=False,
        help="Unique technical key to identify this configuration in code.",
    )

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
    target_model_id = fields.Many2one(
        comodel_name="ir.model",
        string="Target Model",
        domain="[('model', 'like', 'records_management.')]",
    )
    target_model = fields.Char(
        related="target_model_id.model", readonly=True, store=True
    )
    target_field_id = fields.Many2one(
        comodel_name="ir.model.fields",
        string="Target Field",
        domain="[('model_id', '=', target_model_id)]",
    )
    target_field = fields.Char(
        related="target_field_id.name", readonly=True, store=True
    )

    # For field_visibility
    visible = fields.Boolean(string="Is Visible", default=True)
    required = fields.Boolean(string="Is Required")
    readonly = fields.Boolean(string="Is Read-Only")

    # ============================================================================
    # FIELDS - Auditing
    # ============================================================================
    modified_by_id = fields.Many2one(
        comodel_name="res.users", string="Last Modified By", readonly=True
    )
    last_modified = fields.Datetime(string="Last Modified On", readonly=True)
    modification_count = fields.Integer(
        string="Modification Count", default=0, readonly=True
    )
    notes = fields.Text(string="Internal Notes")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("value_text", "value_boolean", "value_number", "value_selection")
    def _compute_current_value(self):
        """Compute the current effective value based on type."""
        for record in self:
            if record.value_boolean is not False:  # Check explicitly for False
                record.current_value = str(record.value_boolean)
            elif record.value_number is not False and record.value_number != 0.0:
                record.current_value = str(record.value_number)
            elif record.value_text:
                record.current_value = record.value_text
            elif record.value_selection:
                record.current_value = record.value_selection
            else:
                record.current_value = ""

    current_value = fields.Char(
        string="Current Value", compute="_compute_current_value", store=True
    )

    @api.depends("config_type", "target_model", "target_field")
    def _compute_display_name(self):
        """Compute a descriptive display name."""
        for record in self:
            if (
                record.config_type == "field_visibility"
                and record.target_model
                and record.target_field
            ):
                record.display_name = _("%(name)s (%(model)s.%(field)s)") % {
                    "name": record.name,
                    "model": record.target_model,
                    "field": record.target_field,
                }
            elif record.config_type == "feature_toggle":
                status = _("Enabled") if record.value_boolean else _("Disabled")
                record.display_name = _("%(name)s - %(status)s") % {
                    "name": record.name,
                    "status": status,
                }
            else:
                record.display_name = record.name

    display_name = fields.Char(compute="_compute_display_name", store=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        (
            "config_key_company_uniq",
            "unique(config_key, company_id)",
            "The configuration key must be unique per company!",
        )
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            vals["modified_by_id"] = self.env.user.id
            vals["last_modified"] = fields.Datetime.now()

        records = super().create(vals_list)

        # Log creation in chatter
        for record in records:
            record.message_post(body=_("Configuration created: %s", record.name))

        return records

    def write(self, vals):
        """Override write to track modifications and clear server cache."""
        # Track modifications for value changes
        if any(key.startswith("value_") for key in vals):
            for record in self:
                vals["modified_by_id"] = self.env.user.id
                vals["last_modified"] = fields.Datetime.now()
                vals["modification_count"] = record.modification_count + 1

        res = super().write(vals)

        # Clear server-side caches to ensure new configuration is loaded
        try:
            self.env.registry.clear_caches()
            self.clear_caches()
        except Exception:
            # Graceful fallback if cache clearing fails
            pass

        # Log significant changes in chatter
        if any(key.startswith("value_") for key in vals):
            for record in self:
                record.message_post(
                    body=_("Configuration updated: %s = %s")
                    % (record.config_key, record.current_value)
                )

        return res

    def unlink(self):
        """Override unlink to log deletion."""
        for record in self:
            config_key = record.config_key
            config_name = record.name

        result = super().unlink()

        # Log deletion (can't use message_post after deletion)
        self.env["mail.message"].create(
            {
                "subject": _("Configuration Deleted"),
                "body": _("Configuration deleted: %s (%s)") % (config_name, config_key),
                "model": self._name,
                "message_type": "comment",
                "author_id": self.env.user.partner_id.id,
            }
        )

        return result

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains(
        "config_type", "value_text", "value_boolean", "value_number", "value_selection"
    )
    def _validate_value_type(self):
        """Validate that the correct value field is used for the parameter type."""
        for record in self:
            if record.config_type == "parameter":
                # Count non-empty/non-false values
                value_count = 0
                if record.value_text:
                    value_count += 1
                if record.value_boolean is not False:  # Explicit check for False
                    value_count += 1
                if record.value_number != 0.0:  # Check if not default 0.0
                    value_count += 1
                if record.value_selection:
                    value_count += 1

                if value_count > 1:
                    raise ValidationError(
                        _(
                            "Configuration '%s' is a parameter and must have only one value type (Text, Boolean, Number, or Selection)."
                        )
                        % record.name
                    )

                if value_count == 0:
                    raise ValidationError(
                        _("Configuration '%s' must have at least one value set.")
                        % record.name
                    )

    @api.constrains("config_type", "target_model_id", "target_field_id")
    def _check_target_exists(self):
        """Validate that target model and field are set for UI-related configs."""
        for record in self:
            if record.config_type in ["field_visibility", "domain_rule"]:
                if not record.target_model_id:
                    raise ValidationError(
                        _(
                            "A 'Target Model' is required for UI or Domain configurations."
                        )
                    )
                if (
                    not record.target_field_id
                    and record.config_type == "field_visibility"
                ):
                    raise ValidationError(
                        _(
                            "A 'Target Field' is required for Field Visibility configurations."
                        )
                    )

    @api.constrains("config_key")
    def _check_config_key_format(self):
        """Validate that config_key follows proper naming convention."""
        import re

        for record in self:
            if not re.match(r"^[a-z][a-z0-9_]*[a-z0-9]$", record.config_key):
                raise ValidationError(
                    _(
                        "Configuration key '%s' must start with a lowercase letter, contain only lowercase letters, numbers, and underscores, and end with a letter or number."
                    )
                    % record.config_key
                )

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
        try:
            # Caching is automatically handled by Odoo for search method
            config = self.search(
                [("config_key", "=", key), ("active", "=", True)], limit=1
            )

            if not config:
                return default

            # Return the appropriate value based on type
            if config.value_boolean is not False:  # Explicit check for False
                return config.value_boolean
            if config.value_number != 0.0:  # Check if not default 0.0
                return config.value_number
            if config.value_text:
                return config.value_text
            if config.value_selection:
                return config.value_selection

            return default

        except Exception:
            # Return default value if any error occurs
            return default

    def get_value(self):
        """Get the configuration value for this record."""
        self.ensure_one()
        return self.get_config_parameter(self.config_key)

    def set_value(self, value):
        """Set the configuration value for this record."""
        self.ensure_one()

        # Determine the appropriate field based on value type
        vals = {
            "value_text": False,
            "value_boolean": False,
            "value_number": 0.0,
            "value_selection": False,
        }

        if isinstance(value, bool):
            vals["value_boolean"] = value
        elif isinstance(value, (int, float)):
            vals["value_number"] = float(value)
        elif isinstance(value, str):
            if self.config_type == "parameter":
                vals["value_text"] = value
            else:
                vals["value_selection"] = value
        else:
            vals["value_text"] = str(value) if value is not None else False

        self.write(vals)

    def action_apply_configuration(self):
        """
        Applies the configuration. For most types, this is done by clearing caches.
        For more complex scenarios, this method can be extended.
        """
        self.ensure_one()

        try:
            # Clear various caches to ensure configuration takes effect
            self.env.registry.clear_caches()
            self.clear_caches()

            # For field visibility configurations, we might need to clear view caches
            if self.config_type == "field_visibility":
                self.env["ir.ui.view"].clear_caches()

            # For feature toggles, clear menu caches
            elif self.config_type == "feature_toggle":
                self.env["ir.ui.menu"].clear_caches()

            # Log the application
            self.message_post(
                body=_("Configuration applied successfully: %s", self.name)
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Configuration Applied"),
                    "message": _("Configuration '%s' has been applied successfully.")
                    % self.name,
                    "type": "success",
                    "sticky": False,
                },
            }

        except Exception as exc:
            error_msg = _("Failed to apply configuration '%s': %s") % (
                self.name,
                str(exc),
            )
            self.message_post(body=error_msg)
            raise UserError(error_msg) from exc

    def action_toggle_active(self):
        """Toggle the active state of the configuration."""
        for record in self:
            record.active = not record.active
            status = _("activated") if record.active else _("deactivated")
            record.message_post(body=_("Configuration %s: %s") % (status, record.name))

    def _default_configuration(self):
        """Reset configuration values to default for this record."""
        self.ensure_one()

        vals = {
            "value_text": False,
            "value_boolean": False,
            "value_number": 0.0,
            "value_selection": False,
        }

        # Set default based on config type
        if self.config_type == "feature_toggle":
            vals["value_boolean"] = False
        elif self.config_type == "field_visibility":
            vals["value_boolean"] = True  # Default to visible

        self.write(vals)
        self.message_post(
            body=_("Configuration reset to default values: %s", self.name)
        )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_feature_toggle(self, key, default=False):
        """Convenience method specifically for feature toggles."""
        return self.get_config_parameter(key, default)

    @api.model
    def is_feature_enabled(self, key):
        """Check if a feature is enabled."""
        return bool(self.get_config_parameter(key, False))

    @api.model
    def get_field_visibility(self, model_name, field_name):
        """Get field visibility configuration for a specific model.field."""
        config = self.search(
            [
                ("config_type", "=", "field_visibility"),
                ("target_model", "=", model_name),
                ("target_field", "=", field_name),
                ("active", "=", True),
            ],
            limit=1,
        )

        if config:
            return {
                "visible": config.visible,
                "required": config.required,
                "readonly": config.readonly,
            }

        # Default values if no configuration found
        return {
            "visible": True,
            "required": False,
            "readonly": False,
        }

    def action_view_related_configurations(self):
        """View configurations in the same category."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Related Configurations"),
            "res_model": "rm.module.configurator",
            "view_mode": "tree,form",
            "domain": [("category", "=", self.category), ("id", "!=", self.id)],
            "context": {
                "default_category": self.category,
                "search_default_group_by_config_type": 1,
            },
        }

    @api.model
    def create_default_configurations(self):
        """Create default configurations for the Records Management module."""
        default_configs = [
            # ============================================================================
            # PORTAL CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Customer Portal",
                "config_key": "portal_enabled",
                "category": "portal",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable or disable the customer portal functionality.",
            },
            {
                "name": "Enable Portal Feedback System",
                "config_key": "portal_feedback_enabled",
                "category": "portal",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable customer feedback collection in the portal.",
            },
            {
                "name": "Enable Portal Request Management",
                "config_key": "portal_request_enabled",
                "category": "portal",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable portal request submission and management.",
            },
            # ============================================================================
            # COMPLIANCE & NAID CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable NAID Compliance",
                "config_key": "naid_compliance_enabled",
                "category": "compliance",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable NAID AAA compliance features and audit logging.",
            },
            {
                "name": "Enable NAID Audit Logging",
                "config_key": "naid_audit_enabled",
                "category": "compliance",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable comprehensive audit logging for NAID compliance.",
            },
            {
                "name": "Enable Chain of Custody",
                "config_key": "chain_of_custody_enabled",
                "category": "compliance",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable chain of custody tracking for documents.",
            },
            {
                "name": "Default Retention Period",
                "config_key": "default_retention_years",
                "category": "compliance",
                "config_type": "parameter",
                "value_number": 7.0,
                "description": "Default retention period in years for documents.",
            },
            # ============================================================================
            # FSM CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable FSM Integration",
                "config_key": "fsm_integration_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable Field Service Management integration.",
            },
            {
                "name": "Enable FSM Notifications",
                "config_key": "fsm_notifications_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable notifications for FSM operations.",
            },
            {
                "name": "Enable Pickup Routes",
                "config_key": "pickup_routes_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable pickup route optimization and management.",
            },
            # ============================================================================
            # BILLING CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Advanced Billing",
                "config_key": "advanced_billing_enabled",
                "category": "billing",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable advanced billing features and configurations.",
            },
            {
                "name": "Enable Customer Inventory Reports",
                "config_key": "customer_inventory_reports_enabled",
                "category": "billing",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable customer inventory reporting features.",
            },
            {
                "name": "Enable Billing Periods",
                "config_key": "billing_periods_enabled",
                "category": "billing",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable billing period management.",
            },
            # ============================================================================
            # CORE RECORDS CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Records Containers",
                "config_key": "records_containers_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable records container management functionality.",
            },
            {
                "name": "Enable Records Documents",
                "config_key": "records_documents_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable records document management functionality.",
            },
            {
                "name": "Enable Records Locations",
                "config_key": "records_locations_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable records location management functionality.",
            },
            {
                "name": "Enable Shredding Services",
                "config_key": "shredding_services_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable shredding service management.",
            },
            {
                "name": "Enable Paper Model Bales",
                "config_key": "paper_model_bale_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable paper model bale management and tracking.",
            },
            {
                "name": "Enable Digital Scanning",
                "config_key": "digital_scanning_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable digital scanning and document digitization features.",
            },
            {
                "name": "Show Total Scan Size",
                "config_key": "total_scan_size_visible",
                "category": "ui",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Show total file size of all digital scans for documents.",
            },
            # ============================================================================
            # ENHANCED FEATURES CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Workflow Visualization",
                "config_key": "workflow_visualization_enabled",
                "category": "workflow",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable workflow visualization and process flow diagrams.",
            },
            {
                "name": "Enable Enhanced FSM Integration",
                "config_key": "enhanced_fsm_integration_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable enhanced field service management integration with fallback support.",
            },
            {
                "name": "Enable Mobile FSM Integration",
                "config_key": "mobile_fsm_integration_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable mobile-optimized FSM integration with offline capabilities.",
            },
            {
                "name": "Enable Mobile Dashboard",
                "config_key": "mobile_dashboard_enabled",
                "category": "ui",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable mobile dashboard for field service operations.",
            },
            {
                "name": "Enable Biometric Authentication",
                "config_key": "biometric_auth_enabled",
                "category": "security",
                "config_type": "feature_toggle",
                "value_boolean": False,
                "description": "Enable biometric authentication for mobile devices.",
            },
            {
                "name": "Enable GPS Tracking",
                "config_key": "gps_tracking_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable GPS tracking for field service operations.",
            },
            {
                "name": "Enable Offline Mode",
                "config_key": "offline_mode_enabled",
                "category": "system",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable offline mode for mobile field service operations.",
            },
            # ============================================================================
            # SYSTEM PARAMETERS
            # ============================================================================
            {
                "name": "Mobile Sync Interval",
                "config_key": "mobile_sync_interval_minutes",
                "category": "system",
                "config_type": "parameter",
                "value_number": 15.0,
                "description": "Interval in minutes for mobile data synchronization.",
            },
            {
                "name": "Max Offline Days",
                "config_key": "max_offline_days",
                "category": "system",
                "config_type": "parameter",
                "value_number": 7.0,
                "description": "Maximum number of days data can remain offline before requiring sync.",
            },
            {
                "name": "Default Container Capacity",
                "config_key": "default_container_capacity",
                "category": "system",
                "config_type": "parameter",
                "value_number": 100.0,
                "description": "Default capacity for new records containers.",
            },
            # ============================================================================
            # UI CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Push Notifications",
                "config_key": "push_notifications_enabled",
                "category": "ui",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable push notifications for mobile devices.",
            },
            {
                "name": "Enable Voice Commands",
                "config_key": "voice_commands_enabled",
                "category": "ui",
                "config_type": "feature_toggle",
                "value_boolean": False,
                "description": "Enable voice command functionality for mobile operations.",
            },
            {
                "name": "Enable Barcode Scanning",
                "config_key": "barcode_scanning_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable barcode scanning for field service operations.",
            },
            {
                "name": "Enable NFC Scanning",
                "config_key": "nfc_scanning_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": False,
                "description": "Enable NFC scanning for field service operations.",
            },
            # ============================================================================
            # REPORTING CONFIGURATIONS
            # ============================================================================
            {
                "name": "Enable Advanced Reporting",
                "config_key": "advanced_reporting_enabled",
                "category": "reporting",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable advanced reporting and analytics features.",
            },
            {
                "name": "Enable Compliance Reports",
                "config_key": "compliance_reports_enabled",
                "category": "reporting",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable NAID compliance reporting features.",
            },
        ]

        created_configs = []
        for config_data in default_configs:
            # Check if configuration already exists
            existing = self.search(
                [("config_key", "=", config_data["config_key"])], limit=1
            )
            if not existing:
                created_configs.append(self.create(config_data))

        return created_configs

    bulk_user_import_enabled = fields.Boolean(
        string="Enable Bulk User Import", default=True, help="Enable or disable bulk user import functionality."
    )
    retrieval_work_order_enabled = fields.Boolean(string="Enable Retrieval Work Orders", default=True)

    photo_enabled = fields.Boolean(
        string="Enable Photo Documentation", default=True, help="Allow technicians to capture and manage photos"
    )
    photo_portal_access = fields.Boolean(
        string="Portal Photo Access", default=False, help="Allow customers to view linked photos"
    )

    @api.model
    def set_config_parameter(self, config_key, value, config_type="parameter", name=None, category=None):
        """
        Sets a configuration parameter by key. Updates existing record or creates a new one.

        :param config_key: Unique key for the config parameter (e.g., 'naid.compliance.enabled')
        :param value: The value to set (boolean, int, str, etc.)
        :param config_type: Type of config ('feature_toggle', 'parameter', etc.)
        :param name: Human-readable name (optional, defaults to config_key)
        :param category: Category for grouping (optional)
        :return: The config record (created or updated)
        """
        # Search for existing config by key
        existing = self.search([("config_key", "=", config_key)], limit=1)

        # Prepare values based on type
        vals = {
            "config_key": config_key,
            "config_type": config_type,
            "name": name or config_key.replace(".", " ").title(),
            "category": category or "general",
        }

        # Set the appropriate value field based on type
        if config_type == "feature_toggle" and isinstance(value, bool):
            vals["value_boolean"] = value
        elif config_type == "parameter" and isinstance(value, (int, float)):
            vals["value_number"] = value
        elif config_type == "parameter" and isinstance(value, str):
            vals["value_text"] = value
        else:
            raise ValueError(f"Unsupported config_type '{config_type}' or value type for key '{config_key}'")

        if existing:
            existing.write(vals)
            return existing
        else:
            return self.create(vals)
