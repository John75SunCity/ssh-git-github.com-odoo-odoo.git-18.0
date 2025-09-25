"""Records Management Configurator model (clean consolidated version).

This file was previously corrupted by an embedded duplicate class definition and
trailing JSON/seed data fragments inside the model body, which produced a
NameError at module load time (top-level `self.write`). The implementation below
restores a single, valid model definition focused on: parameters, feature
toggles, field visibility, and basic gating helpers (chain of custody & bin
inventory). Extra stray seed lists were removed; a minimal seeding helper is
retained for required defaults. Translation policy: concatenate dynamic values
after the `_()` call.
"""

from odoo import _, api, fields, models  # noqa: E402 (kept order per local style)
from odoo.exceptions import UserError, ValidationError
import re  # placed after odoo imports previously; retained but allowed


class RmModuleConfigurator(models.Model):
    _name = "rm.module.configurator"
    _description = "Records Management Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "category, sequence, name"

    # ------------------------------------------------------------------
    # CORE FIELDS
    # ------------------------------------------------------------------
    name = fields.Char(required=True, index=True)
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True, help="Only active configurations are applied.")
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
    target_field_id = fields.Many2one("ir.model.fields", string="Target Field")
    target_field = fields.Char(related="target_field_id.name", store=True)

    visible = fields.Boolean(default=True)
    required = fields.Boolean()
    readonly = fields.Boolean()

    modified_by_id = fields.Many2one("res.users", readonly=True)
    last_modified = fields.Datetime(readonly=True)
    modification_count = fields.Integer(readonly=True, default=0)
    notes = fields.Text()

    # Feature toggles (subset + explicit chain/bin controls)
    enable_chain_of_custody = fields.Boolean(default=True)
    bin_inventory_enabled = fields.Boolean(default=True)
    destruction_certificate_enabled = fields.Boolean(default=True)
    # New: Global FSM feature enable (controls visibility of FSM integration menus/views)
    enable_fsm_features = fields.Boolean(default=True, help="Master switch for Records Management FSM integration UI components.")
    # New visualization & portal/advanced search toggles
    enable_flowchart_visualization = fields.Boolean(
        default=True,
        help="Master switch controlling availability of the System Flowchart custom view (system_flowchart). Disable to hide heavy visualization assets.",
    )
    enable_portal_diagram = fields.Boolean(
        default=True,
        help="Controls availability of the Customer Portal Organization Diagram view (customer_portal_diagram).",
    )
    enable_intelligent_search = fields.Boolean(
        default=True,
        help="Enables intelligent container/file search widgets (container_search, file_search) in backend forms.",
    )

    # Additional referenced toggles kept (avoid view breakage)
    bulk_user_import_enabled = fields.Boolean(default=True)
    retrieval_work_order_enabled = fields.Boolean(default=True)
    photo_enabled = fields.Boolean(default=True)
    photo_portal_access = fields.Boolean(default=False)

    current_value = fields.Char(compute="_compute_current_value", store=True)
    display_name = fields.Char(compute="_compute_display_name", store=True)

    _sql_constraints = [
        ("config_key_company_uniq", "unique(config_key, company_id)", "Configuration key must be unique per company."),
    ]

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
    # CREATE / WRITE OVERRIDES
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
            records.action_apply_chain_of_custody_toggle()
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
            self.action_apply_chain_of_custody_toggle()
        return res

    # ------------------------------------------------------------------
    # FEATURE TOGGLE HELPERS
    # ------------------------------------------------------------------
    def action_apply_chain_of_custody_toggle(self):
        """Apply chain of custody toggle functionality"""
        self.ensure_one()
        menu = self.env.ref("records_management.menu_chain_custody", raise_if_not_found=False)
        if not menu:
            return
        enabled = any(r.enable_chain_of_custody for r in self.search([]))
        try:
            menu.active = bool(enabled)
        except Exception:
            pass

    def action_apply_bin_inventory_toggle(self):
        """Apply bin inventory toggle functionality"""
        self.ensure_one()
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
            self.action_apply_bin_inventory_toggle()
        if 'enable_fsm_features' in updated_keys:
            self.action_apply_fsm_visibility_toggle()

    def _collect_updated_feature_keys(self, vals_list):
        keys = set()
        for vals in vals_list:
            if any(k.startswith('value_') for k in vals):
                for rec in self.filtered(lambda r: r.config_type == 'feature_toggle'):
                    keys.add(rec.config_key)
            # direct boolean feature toggles tracked explicitly
            for direct in ['bin_inventory_enabled', 'enable_fsm_features', 'enable_flowchart_visualization', 'enable_portal_diagram', 'enable_intelligent_search']:
                if direct in vals:
                    keys.add(direct)
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
            {"name": "Enable FSM Features", "config_key": "enable_fsm_features", "config_type": "feature_toggle", "value_boolean": True, "category": "fsm"},
            # UI / Theming
            {"name": "Theme Color", "config_key": "rm_theme_color", "config_type": "parameter", "value_text": "#875A7B", "category": "ui", "description": "Primary browser UI theme-color meta value (hex). Overrides default if present."},
        ]
        created = []
        for vals in defaults:
            if not self.search([("config_key", "=", vals["config_key"])], limit=1):
                created.append(self.create(vals))
        return created

    # ------------------------------------------------------------------
    # FSM VISIBILITY TOGGLE
    # ------------------------------------------------------------------
    def action_apply_fsm_visibility_toggle(self):
        """Activate/deactivate FSM integration menus and (optionally) views.

        We only toggle menus here to avoid costly view arch rewrites. Field- or action-level
        conditional logic can key off this configurator via self.env['rm.module.configurator'].
        """
        self.ensure_one()
        enabled = self.get_config_parameter('enable_fsm_features', True)
        xml_ids = [
            'records_management_fsm.menu_fleet_fsm_integration_root',
            'records_management_fsm.menu_fsm_notification_manager',
        ]
        for xmlid in xml_ids:
            menu = self.env.ref(xmlid, raise_if_not_found=False)
            if menu:
                try:
                    menu.active = bool(enabled)
                except Exception:
                    continue

    def _default_create_default_configurations(self):  # alias (backwards compatibility)
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
        # Accept dot-separated namespaces (e.g., "naid.compliance.enabled").
        # Each segment must start with a letter, may contain letters, digits, or underscores,
        # and must not end with an underscore. Single-letter segments are allowed.
        segment = r"[a-z](?:[a-z0-9_]*[a-z0-9])?"
        pattern = rf"^(?:{segment})(?:\.(?:{segment}))*$"
        for rec in self:
            key = (rec.config_key or "").strip()
            if not key or not re.match(pattern, key):
                raise ValidationError(_("Configuration key format invalid:") + f" {rec.config_key}")

    # ------------------------------------------------------------------
    # PARAMETER SETTER (Public Helper)
    # ------------------------------------------------------------------
    @api.model
    def set_config_parameter(self, config_key, value, config_type="parameter", name=None, category=None):
        existing = self.search([("config_key", "=", config_key)], limit=1)
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
        if existing:
            existing.write(vals)
            return existing
        return self.create(vals)

    # ------------------------------------------------------------------
    # UNLINK OVERRIDE
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
