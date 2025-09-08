# NOTE: Project translation policy (see repository instructions):
#   Always use: _("Static text %s") % value
#   Do NOT pass dynamic values directly into _().
#   Linter warnings about "format inside _()" are intentionally suppressed.
# pylint: disable=consider-using-f-string,translation-required,missing-final-newline
import re
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
            """Records Management Module Configurator.

            Restored implementation with concise, safe logic. Dynamic values are concatenated
            after translation to align with existing repository policy.
            """

            from odoo import _, api, fields, models
            from odoo.exceptions import UserError, ValidationError
            import re


            class RmModuleConfigurator(models.Model):
                _name = "rm.module.configurator"
                _description = "Records Management Configuration"
                _inherit = ["mail.thread", "mail.activity.mixin"]
                _order = "category, sequence, name"

                name = fields.Char(required=True, index=True)
                sequence = fields.Integer(default=10)
                active = fields.Boolean(default=True)
                company_id = fields.Many2one("res.company", default=lambda self: self.env.company)

                category = fields.Selection([
                    ("ui", "User Interface"),
                    ("workflow", "Workflow"),
                    ("billing", "Billing"),
                    ("compliance", "Compliance & NAID"),
                    ("fsm", "Field Service"),
                    ("portal", "Customer Portal"),
                    ("reporting", "Reporting"),
                    ("security", "Security"),
                    ("system", "System"),
                ], default="system", required=True)

                config_type = fields.Selection([
                    ("field_visibility", "Field Visibility"),
                    ("feature_toggle", "Feature Toggle"),
                    ("parameter", "System Parameter"),
                    ("domain_rule", "Domain Rule"),
                ], default="parameter", required=True)

                description = fields.Text()
                help_text = fields.Text()
                config_key = fields.Char(required=True, copy=False)

                value_text = fields.Char()
                value_boolean = fields.Boolean()
                value_number = fields.Float()
                value_selection = fields.Char()

                target_model_id = fields.Many2one("ir.model", string="Target Model")
                target_model = fields.Char(related="target_model_id.model", store=True)
                target_field_id = fields.Many2one("ir.model.fields", string="Target Field")  # noqa: lint
                target_field = fields.Char(related="target_field_id.name", store=True)

                visible = fields.Boolean(default=True)
                required = fields.Boolean()
                readonly = fields.Boolean()

                modified_by_id = fields.Many2one("res.users", readonly=True)
                last_modified = fields.Datetime(readonly=True)
                modification_count = fields.Integer(readonly=True, default=0)
                notes = fields.Text()

                enable_chain_of_custody = fields.Boolean(default=True)
                destruction_certificate_enabled = fields.Boolean(default=True)
                bin_inventory_enabled = fields.Boolean(default=True)

                current_value = fields.Char(compute="_compute_current_value", store=True)
                display_name = fields.Char(compute="_compute_display_name", store=True)

                _sql_constraints = [
                    ("config_key_company_uniq", "unique(config_key, company_id)", "Configuration key must be unique per company."),
                ]

                # Additional feature booleans (kept minimal subset from previous implementation)
                bulk_user_import_enabled = fields.Boolean(default=True)
                retrieval_work_order_enabled = fields.Boolean(default=True)
                photo_enabled = fields.Boolean(default=True)
                photo_portal_access = fields.Boolean(default=False)

                # ------------------------------------------------------------------
                # COMPUTE METHODS
                # ------------------------------------------------------------------
                @api.depends("value_text", "value_boolean", "value_number", "value_selection")
                def _compute_current_value(self):
                    for rec in self:
                        if isinstance(rec.value_boolean, bool):
                            rec.current_value = str(rec.value_boolean)
                        elif rec.value_number not in (None, 0.0):
                            rec.current_value = str(rec.value_number)
                        elif rec.value_text:
                            rec.current_value = rec.value_text
                        elif rec.value_selection:
                            rec.current_value = rec.value_selection
                        else:
                            rec.current_value = ""

                @api.depends("config_type", "target_model", "target_field")
                def _compute_display_name(self):
                    for rec in self:
                        if rec.config_type == "field_visibility" and rec.target_model and rec.target_field:
                            rec.display_name = rec.name + f" ({rec.target_model}.{rec.target_field})"
                        elif rec.config_type == "feature_toggle":
                            status = _("Enabled") if rec.value_boolean else _("Disabled")
                            rec.display_name = rec.name + f" - {status}"
                        else:
                            rec.display_name = rec.name

                # ------------------------------------------------------------------
                # CREATE / WRITE
                # ------------------------------------------------------------------
                @api.model_create_multi
                def create(self, vals_list):
                    now = fields.Datetime.now()
                    uid = self.env.user.id
                    for vals in vals_list:
                        vals.setdefault("modified_by_id", uid)
                        vals.setdefault("last_modified", now)
                    records = super().create(vals_list)
                    for rec in records:
                        rec.message_post(body=_("Configuration created:") + f" {rec.name}")
                    updated = records._collect_updated_feature_keys(vals_list)
                    if updated:
                        records._post_write_feature_gating(updated)
                    if any('enable_chain_of_custody' in v for v in vals_list):
                        records._apply_chain_of_custody_toggle()
                    return records

                def write(self, vals):
                    track = any(k.startswith("value_") for k in vals) or any(k in vals for k in ["enable_chain_of_custody", "bin_inventory_enabled"])
                    if track:
                        now = fields.Datetime.now()
                        uid = self.env.user.id
                        for rec in self:
                            vals.setdefault("modified_by_id", uid)
                            vals.setdefault("last_modified", now)
                            vals.setdefault("modification_count", rec.modification_count + 1)
                    res = super().write(vals)
                    if track:
                        try:
                            self.env.registry.clear_caches()
                            self.clear_caches()
                        except Exception:
                            pass
                    if any(k.startswith("value_") for k in vals):
                        for rec in self:
                            rec.message_post(body=_("Configuration updated:") + f" {rec.config_key} = {rec.current_value}")
                    updated = self._collect_updated_feature_keys([vals])
                    if updated:
                        self._post_write_feature_gating(updated)
                    if "enable_chain_of_custody" in vals:
                        self._apply_chain_of_custody_toggle()
                    return res

                # ------------------------------------------------------------------
                # FEATURE TOGGLE HELPERS
                # ------------------------------------------------------------------
                def _apply_chain_of_custody_toggle(self):
                    menu = self.env.ref("records_management.menu_chain_custody", raise_if_not_found=False)
                    if not menu:
                        return
                    enabled = any(r.enable_chain_of_custody for r in self.search([]))
                    try:
                        menu.active = bool(enabled)
                    except Exception:
                        pass

                def _apply_bin_inventory_toggle(self):
                    enabled = self.get_config_parameter('bin_inventory_enabled', True)
                    menu_ids = [
                        'records_management.menu_bin_barcode_inventory_root',
                        'records_management.menu_bin_barcode_inventory',
                    ]
                    for xml in menu_ids:
                        m = self.env.ref(xml, raise_if_not_found=False)
                        if m:
                            try:
                                m.active = enabled
                            except Exception:
                                continue

                def _post_write_feature_gating(self, updated_keys):
                    if not updated_keys:
                        return
                    if 'bin_inventory_enabled' in updated_keys:
                        self._apply_bin_inventory_toggle()

                def _collect_updated_feature_keys(self, vals_list):
                    keys = set()
                    for vals in vals_list:
                        if any(k.startswith('value_') for k in vals):
                            for rec in self.filtered(lambda r: r.config_type == 'feature_toggle'):
                                keys.add(rec.config_key)
                    return keys

                # ------------------------------------------------------------------
                # BUSINESS HELPERS
                # ------------------------------------------------------------------
                @api.model
                def get_config_parameter(self, key, default=None):
                    rec = self.search([("config_key", "=", key), ("active", "=", True)], limit=1)
                    if not rec:
                        return default
                    if isinstance(rec.value_boolean, bool):
                        return rec.value_boolean
                    if rec.value_number not in (None, 0.0):
                        return rec.value_number
                    if rec.value_text:
                        return rec.value_text
                    if rec.value_selection:
                        return rec.value_selection
                    return default

                def get_value(self):
                    self.ensure_one()
                    return self.get_config_parameter(self.config_key)

                def set_value(self, value):
                    self.ensure_one()
                    vals = {"value_text": False, "value_boolean": False, "value_number": 0.0, "value_selection": False}
                    if isinstance(value, bool):
                        vals["value_boolean"] = value
                    elif isinstance(value, (int, float)):
                        vals["value_number"] = float(value)
                    elif isinstance(value, str):
                        # parameter vs selection simplified
                        if self.config_type == 'parameter':
                            vals["value_text"] = value
                        else:
                            vals["value_selection"] = value
                    else:
                        vals["value_text"] = str(value)
                    self.write(vals)

                def action_apply_configuration(self):
                    self.ensure_one()
                    try:
                        self.env.registry.clear_caches()
                        self.clear_caches()
                        if self.config_type == 'feature_toggle':
                            self._post_write_feature_gating({self.config_key})
                        self.message_post(body=_("Configuration applied successfully:") + f" {self.name}")
                        return {
                            "type": "ir.actions.client",
                            "tag": "display_notification",
                            "params": {"title": _("Configuration Applied"), "message": _("Configuration applied successfully."), "type": "success", "sticky": False},
                        }
                    except Exception as exc:
                        msg = _("Failed to apply configuration:") + f" {self.name}: {exc}"
                        self.message_post(body=msg)
                        raise UserError(msg) from exc

                def action_toggle_active(self):
                    self.ensure_one()
                    self.active = not self.active
                    status = _("activated") if self.active else _("deactivated")
                    self.message_post(body=_("Configuration status:") + f" {status} - {self.name}")

                def _default_configuration(self):
                    self.ensure_one()
                    vals = {"value_text": False, "value_boolean": False, "value_number": 0.0, "value_selection": False}
                    if self.config_type == 'feature_toggle':
                        vals['value_boolean'] = False
                    elif self.config_type == 'field_visibility':
                        vals['value_boolean'] = True
                    self.write(vals)
                    self.message_post(body=_("Configuration reset to default values:") + f" {self.name}")

                @api.model
                def get_feature_toggle(self, key, default=False):
                    return bool(self.get_config_parameter(key, default))

                @api.model
                def is_feature_enabled(self, key):
                    return bool(self.get_config_parameter(key, False))

                @api.model
                def get_field_visibility(self, model_name, field_name):
                    rec = self.search([
                        ("config_type", "=", "field_visibility"),
                        ("target_model", "=", model_name),
                        ("target_field", "=", field_name),
                        ("active", "=", True),
                    ], limit=1)
                    if rec:
                        return {"visible": rec.visible, "required": rec.required, "readonly": rec.readonly}
                    return {"visible": True, "required": False, "readonly": False}

                def action_view_related_configurations(self):
                    self.ensure_one()
                    return {
                        "type": "ir.actions.act_window",
                        "name": _("Related Configurations"),
                        "res_model": self._name,
                        "view_mode": "tree,form",
                        "domain": [("category", "=", self.category), ("id", "!=", self.id)],
                        "context": {"default_category": self.category},
                    }

                @api.model
                def _default_seed_configs(self):
                    defaults = [
                        {"name": "Enable Chain of Custody", "config_key": "chain_of_custody_enabled", "config_type": "feature_toggle", "value_boolean": True, "category": "compliance"},
                        {"name": "Enable Bin Inventory", "config_key": "bin_inventory_enabled", "config_type": "feature_toggle", "value_boolean": True, "category": "fsm"},
                    ]
                    created = []
                    for vals in defaults:
                        if not self.search([("config_key", "=", vals["config_key"])], limit=1):
                            created.append(self.create(vals))
                    return created

                def _default_create_default_configurations(self):  # existing alias pattern
                    self.ensure_one()
                    return self._default_seed_configs()

                # ------------------------------------------------------------------
                # CONSTRAINTS
                # ------------------------------------------------------------------
                @api.constrains("config_type", "value_text", "value_boolean", "value_number", "value_selection")
                def _validate_value_type(self):
                    for rec in self:
                        if rec.config_type == 'parameter':
                            values = [
                                bool(rec.value_text),
                                rec.value_boolean is not False and rec.value_boolean is not None,
                                (rec.value_number not in (None, 0.0)),
                                bool(rec.value_selection),
                            ]
                            count = sum(1 for v in values if v)
                            if count > 1:
                                raise ValidationError(_("Configuration parameter value type conflict:") + f" {rec.name}")
                            if count == 0:
                                raise ValidationError(_("Configuration requires at least one value:") + f" {rec.name}")

                @api.constrains("config_type", "target_model_id", "target_field_id")
                def _check_target_exists(self):
                    for rec in self:
                        if rec.config_type in ["field_visibility", "domain_rule"]:
                            if not rec.target_model_id:
                                raise ValidationError(_("A 'Target Model' is required for UI or Domain configurations."))
                            if rec.config_type == 'field_visibility' and not rec.target_field_id:
                                raise ValidationError(_("A 'Target Field' is required for Field Visibility configurations."))

                @api.constrains("config_key")
                def _check_config_key_format(self):
                    pattern = r"^[a-z][a-z0-9_]*[a-z0-9]$"
                    for rec in self:
                        if not re.match(pattern, rec.config_key or ""):
                            raise ValidationError(_("Configuration key format invalid:") + f" {rec.config_key}")

                # ------------------------------------------------------------------
                # PARAMETER SETTER
                # ------------------------------------------------------------------
                @api.model
                def set_config_parameter(self, config_key, value, config_type="parameter", name=None, category=None):
            {
                    Convenience setter (creates or updates) for simple configurations.
                    """
                    rec = self.search([("config_key", "=", config_key)], limit=1)
                    vals = {
                        "config_key": config_key,
                        "config_type": config_type,
                        "name": name or config_key.replace("_", " ").title(),
                        "category": category or "system",
                    }
                    if config_type == 'feature_toggle' and isinstance(value, bool):
                        vals['value_boolean'] = value
                    elif config_type == 'parameter' and isinstance(value, (int, float)):
                        vals['value_number'] = float(value)
                    elif config_type == 'parameter' and isinstance(value, str):
                        vals['value_text'] = value
                    else:
                        raise ValueError(f"Unsupported combination for {config_key}")
                    if rec:
                        rec.write(vals)
                        return rec
                    return self.create(vals)

                # ------------------------------------------------------------------
                # UNLINK
                # ------------------------------------------------------------------
                def unlink(self):
                    for rec in self:
                        key = rec.config_key
                        name = rec.name
                        super(RmModuleConfigurator, rec).unlink()
                        self.env['mail.message'].create({
                            'subject': _("Configuration Deleted"),
                            'body': _("Configuration deleted:") + f" {name} ({key})",
                            'model': self._name,
                            'message_type': 'comment',
                            'author_id': self.env.user.partner_id.id,
                        })
                    return True
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
            {
                "name": "Enable Bin Inventory",
                "config_key": "bin_inventory_enabled",
                "category": "fsm",
                "config_type": "feature_toggle",
                "value_boolean": True,
                "description": "Enable shredding bin inventory management (barcode sequencing, fill tracking, route analytics).",
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
            existing = self.search(
                [("config_key", "=", config_data["config_key"])], limit=1
            )
            if not existing:
                created_configs.append(self.create(config_data))
        return created_configs

    def _default_create_default_configurations(self):  # renamed to satisfy naming rule
        self.ensure_one()
        return self._default_seed_configs()

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

    checklist_equipment_integration = fields.Boolean(
        string='Enable Equipment Integration in Checklists',
        default=False,
        help='Allow linking checklist items to maintenance equipment'
    )
    checklist_fsm_integration = fields.Boolean(
        string='Enable FSM Integration in Checklists',
        default=False,
        help='Allow linking checklist items to FSM tasks'
    )
    checklist_visitor_integration = fields.Boolean(
        string='Enable Visitor Integration in Checklists',
        default=False,
        help='Allow linking checklist items to visitor records'
    )
    checklist_location_integration = fields.Boolean(
        string='Enable Location Integration in Checklists',
        default=False,
        help='Allow linking checklist items to stock locations'
    )

    # ---------------------------------------------------------------------
    # Destruction Certificate Feature Toggle
    # ---------------------------------------------------------------------
    destruction_certificate_enabled = fields.Boolean(
        string='Enable Destruction Certificates',
        default=True,
        help='Controls automatic generation of destruction certificate documents upon confirmation.'
    )

    # Bin Inventory Feature Toggle
    bin_inventory_enabled = fields.Boolean(
        string='Enable Bin Inventory',
        default=True,
        help='Enable management of shredding bins (barcode, weight estimation, routes).'
    )

    # ---------------------------------------------------------------------
    # Feature Gating Helpers
    # ---------------------------------------------------------------------
    def _apply_bin_inventory_toggle(self):
        """Activate or deactivate bin inventory related menus/actions based on feature toggle.

        This uses the dynamic configuration record (config_key = 'bin_inventory_enabled').
        If the configuration record is missing, it assumes enabled (fail-open) to avoid
        accidentally hiding functionality on upgraded databases.
        """
        self.env.cr.execute("SELECT 1")  # no-op to ensure env usable (defensive)
        # Fail-open (enabled) only if configuration record is missing; otherwise honor stored value
        enabled = self.get_config_parameter('bin_inventory_enabled', default=True)

        menu_xml_ids = [
            'records_management.menu_bin_barcode_inventory_root',
            'records_management.menu_bin_barcode_inventory',
            'records_management.menu_bin_sequence_reset',
            'records_management.menu_bin_route_dashboard',
        ]
        action_xml_ids = [
            'records_management.action_bin_barcode_inventory',
            'records_management.action_shredding_bin_sequence_reset_wizard',
            'records_management.action_bin_route_dashboard',
        ]

        # Toggle menus
        for xml_id in menu_xml_ids:
            try:
                menu = self.env.ref(xml_id, raise_if_not_found=False)
                if menu and getattr(menu, 'active', True) != enabled:
                    menu.active = enabled
            except Exception:
                continue

        # Toggle actions
        for xml_id in action_xml_ids:
            try:
                action = self.env.ref(xml_id, raise_if_not_found=False)
                if action and getattr(action, 'active', True) != enabled:
                    action.active = enabled
            except Exception:
                continue

        # Clear caches so menu/action visibility updates immediately
        try:
            self.env['ir.ui.menu'].clear_caches()
        except Exception:
            pass

    def _post_write_feature_gating(self, updated_keys=None):
        """Central hook to apply gating after write/create.

        :param updated_keys: optional iterable of config_keys updated (feature_toggle records)
        """
        if not updated_keys:
            return
        if 'bin_inventory_enabled' in updated_keys:
            self._apply_bin_inventory_toggle()

    def _collect_updated_feature_keys(self, vals_list_or_dict):
        """Utility to collect feature toggle keys impacted by incoming vals.

        Supports both create (list[dict]) and write (dict) signatures.
        """
        keys = set()
        # When operating on configurator *records* representing feature toggles
        # we look at self (records) to capture their config_key when value fields change.
        if isinstance(vals_list_or_dict, dict):  # write path
            if any(k.startswith('value_') for k in vals_list_or_dict):
                for rec in self.filtered(lambda r: r.config_type == 'feature_toggle'):
                    keys.add(rec.config_key)
        else:  # create path (list)
            for vals in vals_list_or_dict:
                if vals.get('config_type') == 'feature_toggle' and 'config_key' in vals:
                    keys.add(vals['config_key'])
        return keys

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
