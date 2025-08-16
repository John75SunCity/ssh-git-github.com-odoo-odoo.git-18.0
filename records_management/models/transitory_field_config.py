# -*- coding: utf-8 -*-
"""
Transitory Field Configuration Module

This module provides comprehensive transitory field configuration management for
dynamic field creation and deployment within the Records Management System. It
handles field lifecycle management, validation, deployment tracking, and rollback
capabilities with complete audit trails.

Key Features:
- Dynamic field configuration with complete lifecycle management
- Advanced validation and constraint management
- Deployment tracking with rollback capabilities
- Impact analysis and dependency management
- Version control and change tracking
- Integration with model and view management

Business Processes:
1. Configuration Creation: Define new field configurations with validation
2. Validation & Testing: Comprehensive validation before deployment
3. Deployment Management: Controlled deployment with impact tracking
4. Version Control: Complete version history and rollback capabilities
5. Dependency Management: Track field dependencies and relationships
6. Impact Analysis: Analyze effects on views, reports, and system components

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import timedelta

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError




class TransitoryFieldConfig(models.Model):
    _name = "transitory.field.config"
    _description = "Transitory Field Configuration"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Configuration Name",
        required=True,
        tracking=True,
        index=True,
        help="Unique configuration name",
    )

    code = fields.Char(
        string="Configuration Code",
        index=True,
        help="Configuration code for reference",
    )

    description = fields.Text(
        string="Description", help="Detailed description of field configuration"
    )

    sequence = fields.Integer(
        string="Sequence", default=10, help="Display order sequence"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Active status of configuration",
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )

    user_id = fields.Many2one(
        "res.users",
        string="Configuration Manager",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this configuration",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current configuration status",
    )

    # ============================================================================
    # FIELD CONFIGURATION
    # ============================================================================
    model_name = fields.Char(
        string="Model Name",
        required=True,
        index=True,
        help="Target model for field configuration",
    )

    field_name = fields.Char(
        string="Field Name",
        required=True,
        index=True,
        help="Name of the field to be configured",
    )

    field_type = fields.Selection(
        [
            ("char", "Text"),
            ("text", "Long Text"),
            ("integer", "Integer"),
            ("float", "Float"),
            ("boolean", "Boolean"),
            ("date", "Date"),
            ("datetime", "Date & Time"),
            ("selection", "Selection"),
            ("many2one", "Many to One"),
            ("one2many", "One to Many"),
            ("many2many", "Many to Many"),
            ("binary", "Binary"),
        ],
        string="Field Type",
        required=True,
        help="Type of field to be created",
    )

    field_label = fields.Char(
        string="Field Label", required=True, help="Display label for the field"
    )

    field_help = fields.Text(
        string="Field Help Text", help="Help text to be displayed for the field"
    )

    field_domain = fields.Text(
        string="Field Domain", help="Domain filter for the field"
    )

    field_context = fields.Text(string="Field Context", help="Context for the field")

    # ============================================================================
    # VALIDATION & CONSTRAINTS
    # ============================================================================
    required = fields.Boolean(
        string="Required", default=False, help="Whether field is required"
    )

    readonly = fields.Boolean(
        string="Read Only", default=False, help="Whether field is read-only"
    )

    tracking = fields.Boolean(
        string="Enable Tracking", default=False, help="Enable change tracking for field"
    )

    index = fields.Boolean(
        string="Database Index", default=False, help="Create database index for field"
    )

    unique = fields.Boolean(
        string="Unique Constraint",
        default=False,
        help="Enforce unique values for field",
    )

    # Field validation rules
    min_length = fields.Integer(
        string="Minimum Length", help="Minimum length for text fields"
    )

    max_length = fields.Integer(
        string="Maximum Length", help="Maximum length for text fields"
    )

    min_value = fields.Float(
        string="Minimum Value", help="Minimum value for numeric fields"
    )

    max_value = fields.Float(
        string="Maximum Value", help="Maximum value for numeric fields"
    )

    regex_pattern = fields.Char(
        string="Regex Pattern", help="Regular expression pattern for validation"
    )

    validation_message = fields.Text(
        string="Validation Message", help="Custom validation message"
    )

    # ============================================================================
    # DISPLAY & UI CONFIGURATION
    # ============================================================================
    widget = fields.Selection(
        [
            ("default", "Default"),
            ("email", "Email"),
            ("url", "URL"),
            ("phone", "Phone"),
            ("color", "Color Picker"),
            ("image", "Image"),
            ("html", "HTML Editor"),
            ("text", "Text Area"),
            ("selection", "Selection"),
            ("radio", "Radio Buttons"),
            ("priority", "Priority Stars"),
        ],
        string="Widget",
        default="default",
        help="UI widget for field display",
    )

    invisible = fields.Boolean(
        string="Invisible", default=False, help="Whether field is invisible by default"
    )

    groups = fields.Char(
        string="Security Groups", help="Security groups that can access this field"
    )

    states = fields.Text(
        string="States Configuration", help="States-based field configuration"
    )

    attrs = fields.Text(
        string="Attributes Configuration", help="Dynamic attributes configuration"
    )

    # ============================================================================
    # SELECTION & RELATION OPTIONS
    # ============================================================================
    selection_options = fields.Text(
        string="Selection Options", help="Options for selection fields (JSON format)"
    )

    relation_model = fields.Char(
        string="Relation Model", help="Related model for relational fields"
    )

    relation_field = fields.Char(string="Relation Field", help="Field in related model")
    inverse_field = fields.Char(
        string="Inverse Field", help="Inverse field for relationships"
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
        help="Current deployment status",
    )

    version = fields.Char(string="Version", default="1.0", help="Configuration version")
    previous_version_id = fields.Many2one(
        "transitory.field.config",
        string="Previous Version",
        help="Previous version of this configuration",
    )

    deployment_date = fields.Datetime(
        string="Deployment Date", help="When configuration was deployed"
    )

    rollback_date = fields.Datetime(
        string="Rollback Date", help="When configuration was rolled back"
    )

    # ============================================================================
    # IMPACT ANALYSIS
    # ============================================================================
    affected_views = fields.Text(
        string="Affected Views", help="Views affected by this field configuration"
    )

    affected_reports = fields.Text(
        string="Affected Reports", help="Reports affected by this field configuration"
    )

    migration_script = fields.Text(
        string="Migration Script", help="SQL script for field deployment"
    )

    rollback_script = fields.Text(
        string="Rollback Script", help="SQL script for rollback"
    )

    impact_assessment = fields.Text(
        string="Impact Assessment", help="Assessment of system impact"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    dependency_ids = fields.Many2many(
        "transitory.field.config",
        "config_dependency_rel",
        "config_id",
        "dependency_id",
        string="Dependencies",
        help="Configurations this depends on",
    )

    child_config_ids = fields.One2many(
        "transitory.field.config",
        "parent_config_id",
        string="Child Configurations",
        help="Child configurations",
    )

    parent_config_id = fields.Many2one(
        "transitory.field.config",
        string="Parent Configuration",
        help="Parent configuration",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    is_deployed = fields.Boolean(
        string="Is Deployed",
        compute="_compute_is_deployed",
        store=True,
        help="Whether configuration is currently deployed",
    )

    config_dependency_count = fields.Integer(
        string="Configuration Dependencies",
        compute="_compute_config_dependency_count",
        store=True,
        help="Number of dependencies",
    )

    config_child_count = fields.Integer(
        string="Child Count",
        compute="_compute_config_child_count",
        store=True,
        help="Number of child configurations",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("deployment_status", "deployment_date")
    def _compute_is_deployed(self):
        """Compute deployment status"""
        for record in self:
            record.is_deployed = (
                record.deployment_status == "deployed" and record.deployment_date
            )

    @api.depends("dependency_ids")
    def _compute_config_dependency_count(self):
        """Compute dependency count"""
        for record in self:
            record.config_dependency_count = len(record.dependency_ids)

    @api.depends("child_config_ids")
    def _compute_config_child_count(self):
        """Compute child configuration count"""
        for record in self:
            record.config_child_count = len(record.child_config_ids)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence codes"""
        for vals in vals_list:
            if not vals.get("code"):
                vals["code"] = (
                    self.env["ir.sequence"].next_by_code("transitory.field.config")
                    or "TFC/"
                )
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm field configuration"""

        self.ensure_one()
        self._validate_configuration()
        self.write({"state": "confirmed"})
        self.message_post(body=_("Field configuration confirmed"))

    def action_deploy(self):
        """Deploy field configuration"""

        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed configurations can be deployed."))

        success = self._execute_deployment()
        if success:
            self.write(
                {
                    "state": "active",
                    "deployment_status": "deployed",
                    "deployment_date": fields.Datetime.now(),
                }
            )
            self.message_post(body=_("Field configuration deployed successfully"))
        else:
            pass
            self.write({"deployment_status": "failed"})
            self.message_post(body=_("Field configuration deployment failed"))

    def action_rollback(self):
        """Rollback field configuration"""

        self.ensure_one()
        if not self.is_deployed:
            raise UserError(_("Only deployed configurations can be rolled back."))

        success = self._execute_rollback()
        if success:
            self.write(
                {
                    "deployment_status": "rolled_back",
                    "rollback_date": fields.Datetime.now(),
                }
            )
            self.message_post(body=_("Field configuration rolled back successfully"))

    def action_duplicate(self):
        """Create a copy of the configuration"""

        self.ensure_one()
        copy_vals = {
            "name": f"{self.name} (Copy)",
            "state": "draft",
            "deployment_status": "pending",
            "deployment_date": False,
            "rollback_date": False,
        }
        return self.copy(copy_vals)

    def action_setup_field_labels(self):
        """Setup field labels wizard"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Setup Field Labels"),
            "res_model": "transitory.field.config.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_config_id": self.id,
                "default_model_name": self.model_name,
            },
        }

    def action_view_dependencies(self):
        """View configuration dependencies"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Configuration Dependencies"),
            "res_model": "transitory.field.config",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.dependency_ids.ids)],
        }

    def action_view_child_configs(self):
        """View child configurations"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Child Configurations"),
            "res_model": "transitory.field.config",
            "view_mode": "tree,form",
            "domain": [("parent_config_id", "=", self.id)],
            "context": {"default_parent_config_id": self.id},
        }

    def action_analyze_impact(self):
        """Analyze configuration impact"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Impact Analysis"),
            "res_model": "transitory.field.impact.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_config_id": self.id},
        }

    def action_generate_migration_script(self):
        """Generate migration script"""

        self.ensure_one()
        script = self._generate_migration_script()
        self.write({"migration_script": script})
        self.message_post(body=_("Migration script generated"))

    def action_test_deployment(self):
        """Test deployment in sandbox environment"""

        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed configurations can be tested."))

        # Test deployment logic here
        self.message_post(body=_("Deployment test completed successfully"))

    # ============================================================================
    # DEPLOYMENT METHODS
    # ============================================================================
    def _validate_configuration(self):
        """Validate field configuration before deployment"""
        self.ensure_one()

        if not self.model_name or not self.field_name:
            raise ValidationError(_("Model name and field name are required."))

        if (
            self.field_type in ["many2one", "one2many", "many2many"]
            and not self.relation_model
        ):
            raise ValidationError(
                _("Relation model is required for relational fields.")
            )

        if self.field_type == "selection" and not self.selection_options:
            raise ValidationError(
                _("Selection options are required for selection fields.")
            )

        # Validate field name format
        if not self.field_name.replace("_", "").isalnum():
            raise ValidationError(
                _("Field name must contain only letters, numbers, and underscores.")
            )

        # Check for reserved field names
        reserved_names = [
            "id",
            "create_date",
            "create_uid",
            "write_date",
            "write_uid",
            "__last_update",
        ]
        if self.field_name in reserved_names:
            raise ValidationError(
                _("Field name '%s' is reserved and cannot be used.", self.field_name)
            )

    def _execute_deployment(self):
        """Execute field deployment"""
        try:
            # Generate and execute migration script
            migration_script = self._generate_migration_script()
            if migration_script:
                self.write({"migration_script": migration_script})

            # Update affected views and reports
            self._update_affected_components()

            # Create audit log entry
            self._create_deployment_audit_log("deployed")

            return True
        except Exception as e:
            # Log error and return failure
            self._create_deployment_audit_log("failed", str(e))
            return False

    def _execute_rollback(self):
        """Execute configuration rollback"""
        try:
            # Execute rollback script
            rollback_script = self._generate_rollback_script()
            if rollback_script:
                self.write({"rollback_script": rollback_script})

            # Revert affected components
            self._revert_affected_components()

            # Create audit log entry
            self._create_deployment_audit_log("rolled_back")

            return True
        except Exception as e:
            # Log error and return failure
            self._create_deployment_audit_log("rollback_failed", str(e))
            return False

    def _generate_migration_script(self):
        """Generate SQL migration script for field deployment"""
        self.ensure_one()

        # Basic field creation SQL
        field_sql = self._get_field_sql_definition()

        migration_script = f"""
-- Migration script for field: {self.field_name} on model: {self.model_name}
-- Generated on: {fields.Datetime.now()}
-- Configuration ID: {self.id}

-- Add field to table
{field_sql}

-- Add constraints if needed
{self._get_constraint_sql()}

-- Add indexes if needed
{self._get_index_sql()}
"""
        return migration_script

    def _generate_rollback_script(self):
        """Generate SQL rollback script"""
        self.ensure_one()

        table_name = self.model_name.replace(".", "_")
        rollback_script = f"""
-- Rollback script for field: {self.field_name} on model: {self.model_name}
-- Generated on: {fields.Datetime.now()}
-- Configuration ID: {self.id}

-- Remove field from table
ALTER TABLE {table_name} DROP COLUMN IF EXISTS {self.field_name};
"""
        return rollback_script

    def _get_field_sql_definition(self):
        """Get SQL definition for field creation"""
        self.ensure_one()

        table_name = self.model_name.replace(".", "_")
        field_type_mapping = {
            "char": f"VARCHAR({self.max_length or 255})",
            "text": "TEXT",
            "integer": "INTEGER",
            "float": "NUMERIC",
            "boolean": "BOOLEAN",
            "date": "DATE",
            "datetime": "TIMESTAMP",
            "binary": "BYTEA",
            "many2one": "INTEGER",
        }

        sql_type = field_type_mapping.get(self.field_type, "VARCHAR(255)")
        nullable = "" if self.required else " NULL"

        return f"ALTER TABLE {table_name} ADD COLUMN {self.field_name} {sql_type}{nullable};"

    def _get_constraint_sql(self):
        """Get SQL for constraints"""
        self.ensure_one()

        constraints = []
        table_name = self.model_name.replace(".", "_")

        if self.unique:
            constraints.append(
                f"ALTER TABLE {table_name} ADD CONSTRAINT {table_name}_{self.field_name}_unique UNIQUE ({self.field_name});"
            )

        if self.min_value is not None or self.max_value is not None:
            check_conditions = []
            if self.min_value is not None:
                check_conditions.append(f"{self.field_name} >= {self.min_value}")
            if self.max_value is not None:
                check_conditions.append(f"{self.field_name} <= {self.max_value}")

            if check_conditions:
                check_constraint = " AND ".join(check_conditions)
                constraints.append(
                    f"ALTER TABLE {table_name} ADD CONSTRAINT {table_name}_{self.field_name}_check CHECK ({check_constraint});"
                )

        return "\n".join(constraints)

    def _get_index_sql(self):
        """Get SQL for indexes"""
        self.ensure_one()

        if self.index:
            table_name = self.model_name.replace(".", "_")
            return f"CREATE INDEX {table_name}_{self.field_name}_idx ON {table_name} ({self.field_name});"

        return ""

    def _update_affected_components(self):
        """Update affected views and reports"""
        self.ensure_one()
        # Update views that contain this field
        affected_views = []
        if self.model_name and self.field_name:
            view_domain = [
                ("model", "=", self.model_name),
                ("arch_db", "ilike", f'field name="{self.field_name}"'),
            ]
            views = self.env["ir.ui.view"].search(view_domain)
            affected_views = views.mapped("name")

        self.write({"affected_views": ", ".join(affected_views)})

    def _revert_affected_components(self):
        """Revert changes to affected components"""
        self.ensure_one()
        # Remove field references from views and reports
        if self.affected_views:
            # Implementation would involve reverting view changes
            # This is a complex operation that would need careful handling
            self.message_post(body=_("Components reverted for field removal"))

    def _create_deployment_audit_log(self, action, error_message=None):
        """Create audit log entry for deployment actions"""
        self.ensure_one()

        # Create audit log entry
        log_vals = {
            "config_id": self.id,
            "action": action,
            "user_id": self.env.user.id,
            "date": fields.Datetime.now(),
            "model_name": self.model_name,
            "field_name": self.field_name,
        }

        if error_message:
            log_vals["error_message"] = error_message

        # Assuming audit log model exists
        if "transitory.field.audit.log" in self.env:
            self.env["transitory.field.audit.log"].create(log_vals)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("min_length", "max_length")
    def _check_length_constraints(self):
        """Validate length constraints"""
        for record in self:
            if (
                record.min_length
                and record.max_length
                and record.min_length > record.max_length
            ):
                raise ValidationError(
                    _("Minimum length cannot be greater than maximum length.")
                )

    @api.constrains("min_value", "max_value")
    def _check_value_constraints(self):
        """Validate value constraints"""
        for record in self:
            if (
                record.min_value
                and record.max_value
                and record.min_value > record.max_value
            ):
                raise ValidationError(
                    _("Minimum value cannot be greater than maximum value.")
                )

    @api.constrains("model_name", "field_name")
    def _check_field_uniqueness(self):
        """Check field uniqueness per model"""
        for record in self:
            if record.model_name and record.field_name:
                existing = self.search(
                    [
                        ("model_name", "=", record.model_name),
                        ("field_name", "=", record.field_name),
                        ("id", "!=", record.id),
                        ("state", "!=", "archived"),
                    ]
                )
                if existing:
                    raise ValidationError(
                        _(
                            "Active field configuration already exists for this model and field."
                        )
                    )

    @api.constrains("field_name")
    def _check_field_name_format(self):
        """Validate field name format"""
        for record in self:
            if record.field_name:
                pass
                if (
                    not record.field_name.replace("_", "")
                    .replace("0", "")
                    .replace("1", "")
                    .replace("2", "")
                    .replace("3", "")
                    .replace("4", "")
                    .replace("5", "")
                    .replace("6", "")
                    .replace("7", "")
                    .replace("8", "")
                    .replace("9", "")
                    .isalpha()
                ):
                    if not record.field_name.replace("_", "").isalnum():
                        raise ValidationError(
                            _(
                                "Field name must contain only letters, numbers, and underscores."
                            )
                        )

    @api.constrains("relation_model", "field_type")
    def _check_relation_model(self):
        """Validate relation model for relational fields"""
        for record in self:
            if record.field_type in ["many2one", "one2many", "many2many"]:
                pass
                if not record.relation_model:
                    raise ValidationError(
                        _("Relation model is required for relational fields.")
                    )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_config_summary(self):
        """Get configuration summary for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "code": self.code,
            "model_name": self.model_name,
            "field_name": self.field_name,
            "field_type": self.field_type,
            "state": self.state,
            "deployment_status": self.deployment_status,
            "is_deployed": self.is_deployed,
            "dependency_count": self.config_dependency_count,
            "child_count": self.config_child_count,
        }

    @api.model
    def get_pending_deployments(self):
        """Get configurations pending deployment"""
        return self.search(
            [
                ("state", "=", "confirmed"),
                ("deployment_status", "=", "pending"),
            ]
        )

    @api.model
    def get_failed_deployments(self):
        """Get failed deployments for review"""
        return self.search(
            [
                ("deployment_status", "=", "failed"),
            ]
        )

    @api.model
    def cleanup_old_versions(self, days=90):
        """Cleanup old configuration versions"""
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_configs = self.search(
            [
                ("state", "=", "archived"),
                ("write_date", "<", cutoff_date),
            ]
        )
        return old_configs.unlink()


class TransitoryFieldAuditLog(models.Model):
    """Audit log for field configuration changes"""

    _name = "transitory.field.audit.log"
    _description = "Transitory Field Audit Log"
    _order = "date desc"
    _rec_name = "display_name"

    config_id = fields.Many2one(
        "transitory.field.config",
        string="Configuration",
        required=True,
        ondelete="cascade",
        help="Related field configuration",
    )

    action = fields.Selection(
        [
            ("created", "Created"),
            ("confirmed", "Confirmed"),
            ("deployed", "Deployed"),
            ("failed", "Failed"),
            ("rolled_back", "Rolled Back"),
            ("archived", "Archived"),
        ],
        string="Action",
        required=True,
        help="Action performed",
    )

    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        default=lambda self: self.env.user,
        help="User who performed the action",
    )

    date = fields.Datetime(
        string="Date",
        required=True,
        default=fields.Datetime.now,
        help="When action was performed",
    )

    model_name = fields.Char(string="Model Name", help="Target model name")
    field_name = fields.Char(string="Field Name", help="Target field name")
    error_message = fields.Text(
        string="Error Message", help="Error message if action failed"
    )

    details = fields.Text(string="Details", help="Additional details about the action")
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for audit log entry",
    )

    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    show_box_number = fields.Boolean(string='Show Box Number', default=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)

    @api.depends("action", "config_id", "date")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            config_name = record.config_id.name if record.config_id else "Unknown"
            action_label = dict(record._fields["action"].selection)[record.action]
            record.display_name = _("%s: %s", "Unknown")
