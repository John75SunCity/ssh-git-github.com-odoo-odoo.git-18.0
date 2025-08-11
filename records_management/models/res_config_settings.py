# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"
    _description = "Res Config Settings"

    # ============================================================================
    # RECORDS MANAGEMENT CONFIGURATION FIELDS
    # ============================================================================
    module_records_management_setting = fields.Boolean(
        string="Enable Records Management Features", 
        config_parameter="records_management.setting",
        help="Enable advanced records management features"
    )
    
    # NAID Compliance Settings
    naid_compliance_enabled = fields.Boolean(
        string="Enable NAID AAA Compliance",
        config_parameter="records_management.naid_compliance_enabled",
        help="Enable NAID AAA compliance features and audit trails"
    )
    
    auto_barcode_generation = fields.Boolean(
        string="Auto-Generate Barcodes",
        config_parameter="records_management.auto_barcode_generation", 
        help="Automatically generate barcodes for new containers"
    )
    
    default_retention_days = fields.Integer(
        string="Default Retention Period (Days)",
        config_parameter="records_management.default_retention_days",
        default=2555,  # 7 years standard
        help="Default retention period in days for new documents"
    )
    
    # Portal Configuration
    portal_customer_access = fields.Boolean(
        string="Enable Customer Portal Access",
        config_parameter="records_management.portal_customer_access",
        help="Allow customers to access records management portal"
    )
    
    portal_feedback_enabled = fields.Boolean(
        string="Enable Customer Feedback System",
        config_parameter="records_management.portal_feedback_enabled", 
        help="Enable AI-powered customer feedback and sentiment analysis"
    )
    
    # Billing Configuration
    auto_billing_enabled = fields.Boolean(
        string="Enable Automatic Billing",
        config_parameter="records_management.auto_billing_enabled",
        help="Automatically generate invoices for records management services"
    )
    
    billing_cycle_days = fields.Integer(
        string="Billing Cycle (Days)",
        config_parameter="records_management.billing_cycle_days",
        default=30,
        help="Number of days between billing cycles"
    )
    
    # Container Management
    container_capacity_alerts = fields.Boolean(
        string="Enable Capacity Alerts",
        config_parameter="records_management.container_capacity_alerts",
        help="Send alerts when locations approach capacity limits"
    )
    
    auto_location_assignment = fields.Boolean(
        string="Auto-Assign Locations",
        config_parameter="records_management.auto_location_assignment",
        help="Automatically assign optimal storage locations for new containers"
    )
    
    # Field Service Integration
    fsm_integration_enabled = fields.Boolean(
        string="Enable Field Service Integration",
        config_parameter="records_management.fsm_integration_enabled",
        help="Integrate with Odoo Field Service Management for pickup/delivery"
    )
    
    auto_route_optimization = fields.Boolean(
        string="Enable Route Optimization",
        config_parameter="records_management.auto_route_optimization",
        help="Automatically optimize pickup and delivery routes"
    )

    # ============================================================================
    # DOCUMENTATION AND NOTES
    # ============================================================================
    notes = fields.Text(
        string="Configuration Notes",
        help="Internal notes about records management configuration"
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('naid_compliance_enabled', 'portal_customer_access')
    def _compute_compliance_status(self):
        """Compute overall compliance status"""
        for record in self:
            if record.naid_compliance_enabled and record.portal_customer_access:
                record.compliance_status = 'full'
            elif record.naid_compliance_enabled:
                record.compliance_status = 'basic'
            else:
                record.compliance_status = 'none'
    
    compliance_status = fields.Selection([
        ('none', 'No Compliance'),
        ('basic', 'Basic Compliance'),
        ('full', 'Full Compliance')
    ], string="Compliance Status", compute="_compute_compliance_status")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_enable_full_compliance(self):
        """Enable full NAID AAA compliance features"""
        self.ensure_one()
        
        self.write({
            'naid_compliance_enabled': True,
            'portal_customer_access': True,
            'auto_barcode_generation': True,
            'container_capacity_alerts': True,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Full Compliance Enabled'),
                'message': _('All NAID AAA compliance features have been enabled'),
                'type': 'success',
                'sticky': True,
            }
        }
    
    def action_configure_billing_defaults(self):
        """Configure default billing settings"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Configure Billing Defaults'),
            'res_model': 'records.billing.config',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_auto_billing': self.auto_billing_enabled,
                'default_billing_cycle_days': self.billing_cycle_days,
            }
        }
    
    def action_test_barcode_generation(self):
        """Test barcode generation system"""
        self.ensure_one()
        
        if not self.auto_barcode_generation:
            raise UserError(_('Please enable auto-barcode generation first'))
        
        # Test barcode generation
        test_barcode = self.env['records.container']._generate_barcode()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcode Generation Test'),
                'message': _('Test barcode generated: %s', test_barcode),
                'type': 'info',
            }
        }
    
    def action_setup_fsm_integration(self):
        """Setup Field Service Management integration"""
        self.ensure_one()
        
        if not self.fsm_integration_enabled:
            raise UserError(_('Please enable FSM integration first'))
        
        # Check if FSM module is installed
        fsm_module = self.env['ir.module.module'].search([
            ('name', '=', 'industry_fsm'),
            ('state', '=', 'installed')
        ])
        
        if not fsm_module:
            raise UserError(_('Field Service Management module is not installed'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Integration Setup'),
            'res_model': 'project.project',
            'view_mode': 'tree,form',
            'domain': [('is_fsm', '=', True)],
            'context': {'create_fsm_project': True}
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('default_retention_days', 'billing_cycle_days')
    def _check_positive_values(self):
        """Ensure positive values for day fields"""
        for record in self:
            if record.default_retention_days <= 0:
                raise ValidationError(_('Default retention days must be positive'))
            if record.billing_cycle_days <= 0:
                raise ValidationError(_('Billing cycle days must be positive'))
    
    @api.constrains('default_retention_days')
    def _check_retention_period(self):
        """Validate retention period is reasonable"""
        for record in self:
            if record.default_retention_days > 36500:  # 100 years
                raise ValidationError(_('Retention period cannot exceed 100 years'))
            if record.default_retention_days < 365:  # 1 year minimum
                raise ValidationError(_('Retention period should be at least 1 year for compliance'))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_records_management_config(self):
        """Get current records management configuration as dictionary"""
        self.ensure_one()
        
        return {
            'naid_compliance': self.naid_compliance_enabled,
            'portal_access': self.portal_customer_access,
            'auto_barcode': self.auto_barcode_generation,
            'retention_days': self.default_retention_days,
            'billing_enabled': self.auto_billing_enabled,
            'billing_cycle': self.billing_cycle_days,
            'fsm_enabled': self.fsm_integration_enabled,
            'route_optimization': self.auto_route_optimization,
        }
    
    @api.model
    def get_default_config_values(self):
        """Get default configuration values for new installations"""
        return {
            'naid_compliance_enabled': True,
            'portal_customer_access': True,
            'auto_barcode_generation': True,
            'default_retention_days': 2555,  # 7 years
            'auto_billing_enabled': False,
            'billing_cycle_days': 30,
            'container_capacity_alerts': True,
            'fsm_integration_enabled': False,
        }
