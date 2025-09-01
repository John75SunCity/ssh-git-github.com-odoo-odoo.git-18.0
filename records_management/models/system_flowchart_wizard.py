# -*- coding: utf-8 -*-
from odoo import models, fields, api


class SystemFlowchartWizard(models.TransientModel):
    """Wizard for configuring and generating system architecture flowcharts"""

    _name = 'system.flowchart.wizard'
    _description = 'System Flowchart Configuration Wizard'

    # Basic fields
    name = fields.Char(string='Session ID', readonly=True, default=lambda self: self._default_name())
    step = fields.Selection([
        ('welcome', 'Welcome'),
        ('configure', 'Configure'),
        ('preview', 'Preview'),
        ('complete', 'Complete')
    ], string='Current Step', default='welcome', required=True)

    # Configuration fields
    search_scenario = fields.Selection([
        ('system_overview', 'System Overview'),
        ('user_access', 'User Access Analysis'),
        ('company_structure', 'Company Structure'),
        ('model_relationships', 'Model Relationships'),
        ('compliance_audit', 'Compliance Audit View'),
        ('custom', 'Custom Configuration')
    ], string='Analysis Scenario', default='system_overview')

    layout_style = fields.Selection([
        ('hierarchical', 'Hierarchical'),
        ('circular', 'Circular'),
        ('force_directed', 'Force Directed'),
        ('grid', 'Grid')
    ], string='Layout Style', default='hierarchical')

    color_scheme = fields.Selection([
        ('professional', 'Professional'),
        ('colorblind_friendly', 'Colorblind Friendly'),
        ('high_contrast', 'High Contrast'),
        ('custom', 'Custom')
    ], string='Color Scheme', default='professional')

    zoom_level = fields.Float(string='Zoom Level', default=1.0)

    # Target fields
    target_user_id = fields.Many2one('res.users', string='Target User')
    target_company_id = fields.Many2one('res.company', string='Target Company')
    target_model_id = fields.Many2one('ir.model', string='Target Model')

    # Export settings
    export_format = fields.Selection([
        ('png', 'PNG'),
        ('svg', 'SVG'),
        ('pdf', 'PDF'),
        ('html', 'Interactive HTML'),
        ('json', 'JSON Data')
    ], string='Export Format', default='png')

    export_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('ultra', 'Ultra')
    ], string='Export Quality', default='high')

    include_metadata = fields.Boolean(string='Include Metadata', default=True)
    export_timestamp = fields.Boolean(string='Include Timestamp', default=True)

    # Performance settings
    performance_mode = fields.Boolean(string='Performance Mode', default=False)
    max_nodes = fields.Integer(string='Max Nodes', default=1000)
    cache_results = fields.Boolean(string='Cache Results', default=True)

    # Display components
    show_models = fields.Boolean(string='Show Models', default=True)
    show_users = fields.Boolean(string='Show Users', default=True)
    show_access_rights = fields.Boolean(string='Show Access Rights', default=True)
    show_companies = fields.Boolean(string='Show Companies', default=True)
    show_departments = fields.Boolean(string='Show Departments', default=True)
    show_relationships = fields.Boolean(string='Show Relationships', default=True)
    show_computed_fields = fields.Boolean(string='Show Computed Fields', default=False)
    show_workflows = fields.Boolean(string='Show Workflows', default=True)
    show_security_rules = fields.Boolean(string='Show Security Rules', default=False)
    show_audit_trails = fields.Boolean(string='Show Audit Trails', default=True)

    # Visualization options
    node_size = fields.Selection([
        ('small', 'Small'),
        ('medium', 'Medium'),
        ('large', 'Large')
    ], string='Node Size', default='medium')

    edge_style = fields.Selection([
        ('straight', 'Straight'),
        ('curved', 'Curved'),
        ('orthogonal', 'Orthogonal')
    ], string='Edge Style', default='curved')

    label_position = fields.Selection([
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('left', 'Left'),
        ('right', 'Right'),
        ('center', 'Center')
    ], string='Label Position', default='bottom')

    animation_enabled = fields.Boolean(string='Enable Animation', default=True)

    # Tutorial settings
    show_tutorial = fields.Boolean(string='Show Tutorial', default=True)
    tutorial_step = fields.Integer(string='Tutorial Step', default=1)
    tutorial_auto_advance = fields.Boolean(string='Auto Advance Tutorial', default=True)
    tutorial_highlights = fields.Boolean(string='Tutorial Highlights', default=True)
    tutorial_auto_start = fields.Boolean(string='Auto Start Tutorial', default=True)

    # Help options
    show_tooltips = fields.Boolean(string='Show Tooltips', default=True)
    show_context_help = fields.Boolean(string='Show Context Help', default=True)
    help_position = fields.Selection([
        ('top', 'Top'),
        ('bottom', 'Bottom'),
        ('floating', 'Floating')
    ], string='Help Position', default='floating')

    # Preview and validation
    preview_data = fields.Text(string='Preview Data', readonly=True)
    config_valid = fields.Boolean(string='Configuration Valid', compute='_compute_config_valid', store=True)
    generated_config = fields.Text(string='Generated Configuration', readonly=True)

    # Statistics (computed)
    total_models = fields.Integer(string='Total Models', compute='_compute_statistics', store=False)
    total_users = fields.Integer(string='Total Users', compute='_compute_statistics', store=False)
    total_companies = fields.Integer(string='Total Companies', compute='_compute_statistics', store=False)
    total_relationships = fields.Integer(string='Total Relationships', compute='_compute_statistics', store=False)
    enabled_components_count = fields.Integer(string='Enabled Components', compute='_compute_enabled_components', store=False)
    estimated_load_time = fields.Float(string='Estimated Load Time (s)', compute='_compute_load_time', store=False)

    # RM Module Configurator integration
    rm_configurator_enabled = fields.Boolean(string='RM Configurator Enabled', compute='_compute_rm_configurator_enabled', store=False)

    @api.model
    def _default_name(self):
        """Generate a default session ID"""
        return self.env['ir.sequence'].next_by_code('system.flowchart.wizard') or 'FLOWCHART-001'

    @api.depends('search_scenario', 'layout_style', 'export_format', 'performance_mode')
    def _compute_config_valid(self):
        """Validate configuration"""
        for record in self:
            record.config_valid = bool(record.search_scenario and record.layout_style and record.export_format)

    @api.depends('show_models', 'show_users', 'show_access_rights', 'show_companies',
                 'show_departments', 'show_relationships', 'show_computed_fields',
                 'show_workflows', 'show_security_rules', 'show_audit_trails')
    def _compute_enabled_components(self):
        """Count enabled display components"""
        for record in self:
            components = [
                record.show_models, record.show_users, record.show_access_rights,
                record.show_companies, record.show_departments, record.show_relationships,
                record.show_computed_fields, record.show_workflows,
                record.show_security_rules, record.show_audit_trails
            ]
            record.enabled_components_count = sum(1 for c in components if c)

    def _compute_statistics(self):
        """Compute system statistics"""
        for record in self:
            # These would be computed based on actual system data
            record.total_models = 25  # Placeholder
            record.total_users = self.env['res.users'].search_count([('active', '=', True)])
            record.total_companies = self.env['res.company'].search_count([])
            record.total_relationships = 150  # Placeholder

    def _compute_load_time(self):
        """Estimate load time based on configuration"""
        for record in self:
            base_time = 2.0
            if record.performance_mode:
                base_time *= 0.7
            if record.enabled_components_count > 5:
                base_time *= 1.5
            record.estimated_load_time = base_time

    def _compute_rm_configurator_enabled(self):
        """Check if RM Module Configurator is enabled"""
        for record in self:
            # This would check the RM Module Configurator settings
            record.rm_configurator_enabled = True  # Placeholder

    # Wizard actions
    def action_next_step(self):
        """Move to next step"""
        self.ensure_one()
        step_sequence = ['welcome', 'configure', 'preview', 'complete']
        current_index = step_sequence.index(self.step)
        if current_index < len(step_sequence) - 1:
            self.step = step_sequence[current_index + 1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_previous_step(self):
        """Move to previous step"""
        self.ensure_one()
        step_sequence = ['welcome', 'configure', 'preview', 'complete']
        current_index = step_sequence.index(self.step)
        if current_index > 0:
            self.step = step_sequence[current_index - 1]
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_open_flowchart(self):
        """Open the generated flowchart"""
        self.ensure_one()
        # This would open the actual flowchart view
        return {
            'type': 'ir.actions.act_window',
            'name': 'System Flowchart',
            'res_model': 'ir.ui.view',
            'view_mode': 'form',
            'target': 'current',
            'context': {'flowchart_config': self._get_config_data()}
        }

    def action_apply_scenario(self):
        """Apply a predefined scenario configuration"""
        self.ensure_one()
        # This would load preset configurations
        pass

    def action_save_configuration(self):
        """Save current configuration"""
        self.ensure_one()
        # This would save the configuration for later use
        pass

    def action_reset_wizard(self):
        """Reset wizard to initial state"""
        self.ensure_one()
        self.step = 'welcome'
        return self.action_next_step()

    def _get_config_data(self):
        """Get configuration data for flowchart generation"""
        self.ensure_one()
        return {
            'scenario': self.search_scenario,
            'layout': self.layout_style,
            'colors': self.color_scheme,
            'components': {
                'models': self.show_models,
                'users': self.show_users,
                'access_rights': self.show_access_rights,
                'companies': self.show_companies,
                'departments': self.show_departments,
                'relationships': self.show_relationships,
                'workflows': self.show_workflows,
                'audit_trails': self.show_audit_trails,
            }
        }
