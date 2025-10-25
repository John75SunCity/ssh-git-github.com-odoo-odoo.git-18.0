# -*- coding: utf-8 -*-
"""
System Flowchart Configuration Wizard

This wizard helps users configure and understand the interactive system flowchart,
providing guided setup for search parameters, access visualization, and export options.

Key Features:
- Guided flowchart configuration
- Pre-defined search scenarios
- Help and tutorial system
- Export configuration management
- User preference management

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

import json
from odoo import models, fields, api, _

from odoo.exceptions import ValidationError




class SystemFlowchartWizard(models.TransientModel):
    _name = "system.flowchart.wizard"
    _description = "System Flowchart Configuration Wizard"

    # ============================================================================
    # WIZARD STEP FIELDS
    # ============================================================================
    step = fields.Selection(
        [
            ("welcome", "Welcome"),
            ("configure", "Configure"),
            ("preview", "Preview"),
            ("complete", "Complete"),
        ],
        string="Wizard Step",
        default="welcome",
        required=True,
    )

    # ============================================================================
    # CONFIGURATION FIELDS
    # ============================================================================
    search_scenario = fields.Selection(
        [
            ("overview", "System Overview"),
            ("user_access", "User Access Analysis"),
            ("company_structure", "Company Structure"),
            ("model_relationships", "Model Relationships"),
            ("compliance_audit", "Compliance Audit View"),
            ("custom", "Custom Configuration"),
        ],
        string="Search Scenario",
        default="overview",
        help="Pre-configured scenarios for common use cases",
    )

    target_user = fields.Many2one(
        "res.users",
        string="Target User",
        help="Focus on specific user's access rights",
    )

    target_company = fields.Many2one(
        "res.company",
        string="Target Company",
        help="Focus on specific company structure",
    )

    show_models = fields.Boolean(
        string="Show Models",
        default=True,
        help="Include model relationships in diagram",
    )

    show_users = fields.Boolean(
        string="Show Users",
        default=True,
        help="Include user information in diagram",
    )

    show_access_rights = fields.Boolean(
        string="Show Access Rights",
        default=True,
        help="Include access control visualization",
    )

    show_companies = fields.Boolean(
        string="Show Companies",
        default=True,
        help="Include company and department structure",
    )

    layout_style = fields.Selection(
        [
            ("hierarchical", "Hierarchical Layout"),
            ("network", "Network Layout"),
            ("circular", "Circular Layout"),
            ("force_directed", "Force-Directed Layout"),
        ],
        string="Layout Style",
        default="hierarchical",
        help="Visual layout style for the diagram",
    )

    color_scheme = fields.Selection(
        [
            ("default", "Default Colors"),
            ("high_contrast", "High Contrast"),
            ("colorblind_safe", "Colorblind Safe"),
            ("corporate", "Corporate Theme"),
        ],
        string="Color Scheme",
        default="default",
        help="Color scheme for better accessibility",
    )

    export_format = fields.Selection(
        [
            ("png", "PNG Image"),
            ("svg", "SVG Vector"),
            ("pdf", "PDF Document"),
            ("json", "JSON Data"),
        ],
        string="Export Format",
        default="png",
        help="Preferred export format",
    )

    # ============================================================================
    # HELP AND TUTORIAL FIELDS
    # ============================================================================
    show_tutorial = fields.Boolean(
        string="Show Tutorial",
        default=True,
        help="Show tutorial overlay on first visit",
    )

    tutorial_step = fields.Integer(
        string="Tutorial Step",
        default=1,
        help="Current tutorial step",
    )

    # ============================================================================
    # GENERATED CONFIG FIELDS
    # ============================================================================
    generated_config = fields.Text(
        string="Generated Configuration",
        compute="_compute_generated_config",
        store=False,
        help="Auto-generated configuration JSON",
    )

    preview_data = fields.Text(
        string="Preview Data",
        compute="_compute_preview_data",
        store=False,
        help="Preview of diagram data",
    )

    config_valid = fields.Boolean(
        string="Configuration Valid",
        compute="_compute_config_valid",
        store=False,
        help="Indicates if the current configuration is valid",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends(
        "search_scenario",
        "layout_style",
        "color_scheme",
        "show_models",
        "show_users",
        "show_access_rights",
        "show_companies",
    )
    def _compute_generated_config(self):
        """Generate configuration based on wizard selections"""
        for record in self:
            config = {
                "scenario": record.search_scenario,
                "layout": {
                    "style": record.layout_style,
                    "hierarchical": {
                        "enabled": record.layout_style == "hierarchical",
                        "direction": (
                            "UD" if record.layout_style == "hierarchical" else "LR"
                        ),
                    },
                    "physics": {
                        "enabled": record.layout_style in ["network", "force_directed"],
                    },
                },
                "filters": {
                    "show_models": record.show_models,
                    "show_users": record.show_users,
                    "show_access_rights": record.show_access_rights,
                    "show_companies": record.show_companies,
                },
                "styling": {
                    "color_scheme": record.color_scheme,
                    "export_format": record.export_format,
                },
                "tutorial": {
                    "show_tutorial": record.show_tutorial,
                    "tutorial_step": record.tutorial_step,
                },
            }

            # Add target-specific configurations
            if record.target_user:
                config["target_user_id"] = record.target_user.id
            if record.target_company:
                config["target_company_id"] = record.target_company.id

            record.generated_config = json.dumps(config, indent=2)

    @api.depends("search_scenario", "target_user", "target_company")
    def _compute_preview_data(self):
        """Generate preview description based on selections"""
        for record in self:
            preview = []

            if record.search_scenario == "overview":
                preview.append("• Complete system architecture overview")
                preview.append("• All major components and relationships")
                preview.append("• Color-coded access indicators")

            elif record.search_scenario == "user_access":
                if record.target_user:
                    preview.append(f"• Focus on user: {record.target_user.name}")
                    preview.append("• User's access rights visualization")
                    preview.append("• Connected models and permissions")
                else:
                    preview.append("• All users and their access rights")
                    preview.append("• Group memberships and permissions")
                    preview.append("• Portal vs internal user distinction")

            elif record.search_scenario == "company_structure":
                if record.target_company:
                    preview.append(f"• Focus on company: {record.target_company.name}")
                    preview.append("• Department structure and assignments")
                    preview.append("• User-department relationships")
                else:
                    preview.append("• All company structures")
                    preview.append("• Department hierarchies")
                    preview.append("• Multi-company relationships")

            elif record.search_scenario == "model_relationships":
                preview.append("• Core Records Management models")
                preview.append("• Field relationships and dependencies")
                preview.append("• Data flow visualization")

            elif record.search_scenario == "compliance_audit":
                preview.append("• NAID compliance framework")
                preview.append("• Audit trail connections")
                preview.append("• Security and access compliance")

            else:  # custom
                preview.append("• Custom configuration based on your selections")

            record.preview_data = "\n".join(preview)

    @api.depends('search_scenario', 'layout_style', 'color_scheme')
    def _compute_config_valid(self):
        """Check if current configuration is valid"""
        for record in self:
            # Basic validation - all required fields have values
            config_valid = bool(
                record.search_scenario and
                record.layout_style and
                record.color_scheme
            )

            # Additional scenario-specific validation
            if record.search_scenario == 'user_access' and not record.target_user:
                # User access scenario should have a target user for best results
                pass  # Not required, but recommended

            if record.search_scenario == 'company_structure' and not record.target_company:
                # Company structure scenario should have a target company for best results
                pass  # Not required, but recommended

            record.config_valid = config_valid

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_next_step(self):
        """Move to next wizard step"""

        self.ensure_one()

        if self.step == "welcome":
            self.step = "configure"
        elif self.step == "configure":
            self.step = "preview"
        elif self.step == "preview":
            self.step = "complete"
        else:
            return self.action_open_flowchart()

        return {
            "type": "ir.actions.act_window",
            "res_model": "system.flowchart.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_previous_step(self):
        """Move to previous wizard step"""

        self.ensure_one()

        if self.step == "complete":
            self.step = "preview"
        elif self.step == "preview":
            self.step = "configure"
        elif self.step == "configure":
            self.step = "welcome"

        return {
            "type": "ir.actions.act_window",
            "res_model": "system.flowchart.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_open_flowchart(self):
        """Open the system flowchart with configured parameters"""

        self.ensure_one()

        # Map search scenarios to valid search_type values
        search_type_mapping = {
            'overview': 'all',
            'user_access': 'access',
            'company_structure': 'company',
            'model_relationships': 'relationships',
            'compliance_audit': 'all',
            'custom': 'all',
        }

        # Create system diagram data record with configuration
        diagram_data = {
            "name": f"System Flowchart - {self.search_scenario.replace('_', ' ').title()}",
            "search_type": search_type_mapping.get(self.search_scenario, 'all'),
            "show_access_only": self.search_scenario == "user_access",
        }

        if self.target_user:
            diagram_data["search_query"] = self.target_user.name

        if self.target_company:
            diagram_data["search_query"] = self.target_company.name

        diagram = self.env["system.diagram.data"].create(diagram_data)

        # Get the form view with diagram preview
        form_view = self.env.ref('records_management.system_diagram_data_view_form')

        return {
            "type": "ir.actions.act_window",
            "name": "System Architecture Flowchart",
            "res_model": "system.diagram.data",
            "res_id": diagram.id,
            "view_mode": "form",
            "view_id": form_view.id,
            "target": "current",
            "context": {
                "wizard_config": self.generated_config,
                "show_tutorial": self.show_tutorial,
                "tutorial_step": self.tutorial_step,
            },
        }

    def action_reset_wizard(self):
        """Reset wizard to default values"""

        self.ensure_one()

        self.write(
            {
                "step": "welcome",
                "search_scenario": "overview",
                "target_user": False,
                "target_company": False,
                "show_models": True,
                "show_users": True,
                "show_access_rights": True,
                "show_companies": True,
                "layout_style": "hierarchical",
                "color_scheme": "default",
                "export_format": "png",
                "show_tutorial": True,
                "tutorial_step": 1,
            }
        )

        return {
            "type": "ir.actions.act_window",
            "res_model": "system.flowchart.wizard",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_apply_scenario(self):
        """Apply selected scenario configuration"""

        self.ensure_one()

        # Configure based on scenario
        if self.search_scenario == "user_access":
            self.show_access_rights = True
            self.show_users = True
            self.show_models = False
            self.show_companies = False

        elif self.search_scenario == "company_structure":
            self.show_companies = True
            self.show_users = True
            self.show_models = False
            self.show_access_rights = False

        elif self.search_scenario == "model_relationships":
            self.show_models = True
            self.show_users = False
            self.show_companies = False
            self.show_access_rights = False

        elif self.search_scenario == "compliance_audit":
            self.show_access_rights = True
            self.show_models = True
            self.show_users = True
            self.show_companies = True
            self.color_scheme = "high_contrast"

        else:  # overview
            self.show_models = True
            self.show_users = True
            self.show_access_rights = True
            self.show_companies = True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("tutorial_step")
    def _check_tutorial_step(self):
        """Validate tutorial step range"""
        for record in self:
            if record.tutorial_step < 1 or record.tutorial_step > 10:
                raise ValidationError(_("Tutorial step must be between 1 and 10."))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_scenario_description(self, scenario):
        """Get description for a scenario"""
        descriptions = {
            "overview": "Complete system architecture with all components and relationships",
            "user_access": "Focus on user access rights and permissions with color-coded indicators",
            "company_structure": "Company and department hierarchies with user assignments",
            "model_relationships": "Core data models and their field relationships",
            "compliance_audit": "NAID compliance framework and audit trail visualization",
            "custom": "Custom configuration based on your specific requirements",
        }
        return descriptions.get(scenario, "Custom configuration")

    def get_color_scheme_preview(self, scheme):
        """Get color preview for scheme"""
        schemes = {
            "default": "Standard blue/green/orange color palette",
            "high_contrast": "High contrast black/white/yellow for better visibility",
            "colorblind_safe": "Colorblind-friendly palette with distinct patterns",
            "corporate": "Professional grey/blue corporate theme",
        }
        return schemes.get(scheme, "Standard color scheme")

    @api.model
    def get_tutorial_content(self, step):
        """Get tutorial content for specific step"""
        content = {
            1: {
                "title": "Welcome to System Flowchart",
                "content": "This interactive diagram shows your Records Management System architecture, relationships, and access controls.",
                "action": "Click nodes to see details, drag to navigate, and use the mouse wheel to zoom.",
            },
            2: {
                "title": "Search Functionality",
                "content": "Use the search bar to find specific users, companies, or models. Results are highlighted in the diagram.",
                "action": "Try searching for your username to see your access rights.",
            },
            3: {
                "title": "Access Visualization",
                "content": "Green connections show granted access, red shows denied access. This helps audit security permissions.",
                "action": "Look for the color-coded lines connecting users to system components.",
            },
            4: {
                "title": "Export Options",
                "content": "Export the diagram as PNG, SVG, or PDF for documentation and compliance reporting.",
                "action": "Click the export button to download the current view.",
            },
        }
        return content.get(step, {})

    @api.model
    def create_quick_scenario(self, scenario_name, user_id=None, company_id=None):
        """Create wizard with quick scenario setup"""
        wizard = self.create(
            {
                "search_scenario": scenario_name,
                "target_user": user_id,
                "target_company": company_id,
                "step": "preview",
            }
        )
        wizard.action_apply_scenario()
        return wizard
