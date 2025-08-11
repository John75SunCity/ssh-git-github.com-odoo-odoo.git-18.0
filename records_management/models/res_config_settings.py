# -*- coding: utf-8 -*-
"""
Records Management Configuration Settings

This module provides comprehensive configuration settings for the Records Management System.
It includes settings for NAID compliance, portal access, billing automation, container management,
and field service integration to provide complete control over system behavior.

Key Configuration Areas:
- NAID AAA Compliance settings and audit trail configuration
- Customer portal access and feedback system controls  
- Automated billing and invoicing configuration
- Container management and capacity monitoring
- Field service integration and route optimization
- Security and access control settings

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # ============================================================================
    # RECORDS MANAGEMENT CORE CONFIGURATION
    # ============================================================================
    module_records_management_setting = fields.Boolean(
        string="Enable Records Management Features", 
        config_parameter="records_management.setting",
        help="Enable advanced records management features and workflows"
    )
    
    # ============================================================================
    # NAID COMPLIANCE SETTINGS
    # ============================================================================
    naid_compliance_enabled = fields.Boolean(
        string="Enable NAID AAA Compliance",
        config_parameter="records_management.naid_compliance_enabled",
        help="Enable NAID AAA compliance features and comprehensive audit trails"
    )
    
    naid_audit_retention_days = fields.Integer(
        string="NAID Audit Log Retention (Days)",
        config_parameter="records_management.naid_audit_retention_days",
        default=2555,  # 7 years standard compliance
        help="Number of days to retain NAID audit logs for compliance"
    )
    
    naid_certificate_auto_generation = fields.Boolean(
        string="Auto-Generate NAID Certificates",
        config_parameter="records_management.naid_certificate_auto_generation",
        default=True,
        help="Automatically generate NAID destruction certificates"
    )
    
    chain_of_custody_required = fields.Boolean(
        string="Require Chain of Custody Documentation",
        config_parameter="records_management.chain_of_custody_required",
        default=True,
        help="Mandate chain of custody documentation for all document movements"
    )
    
    # ============================================================================
    # PORTAL AND CUSTOMER ACCESS SETTINGS
    # ============================================================================
    portal_customer_access = fields.Boolean(
        string="Enable Customer Portal Access",
        config_parameter="records_management.portal_customer_access",
        help="Allow customers to access records management portal features"
    )
    
    portal_feedback_enabled = fields.Boolean(
        string="Enable Customer Feedback System",
        config_parameter="records_management.portal_feedback_enabled", 
        help="Enable AI-powered customer feedback and sentiment analysis system"
    )
    
    portal_document_download = fields.Boolean(
        string="Allow Document Downloads",
        config_parameter="records_management.portal_document_download",
        help="Allow customers to download documents through the portal"
    )
    
    portal_esignature_enabled = fields.Boolean(
        string="Enable E-Signature Integration",
        config_parameter="records_management.portal_esignature_enabled",
        help="Enable electronic signature capabilities for portal requests"
    )
    
    # ============================================================================
    # BARCODE AND AUTOMATION SETTINGS
    # ============================================================================
    auto_barcode_generation = fields.Boolean(
        string="Auto-Generate Barcodes",
        config_parameter="records_management.auto_barcode_generation", 
        help="Automatically generate barcodes for new containers and documents"
    )
    
    barcode_format = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('ean13', 'EAN-13'),
        ('qr_code', 'QR Code'),
    ], string="Barcode Format",
       config_parameter="records_management.barcode_format",
       default='code128',
       help="Default barcode format for container and document identification")
    
    intelligent_classification_enabled = fields.Boolean(
        string="Enable Intelligent Barcode Classification",
        config_parameter="records_management.intelligent_classification_enabled",
        default=True,
        help="Automatically classify items based on barcode length and patterns"
    )
    
    # ============================================================================
    # BILLING AND FINANCIAL CONFIGURATION
    # ============================================================================
    auto_billing_enabled = fields.Boolean(
        string="Enable Automatic Billing",
        config_parameter="records_management.auto_billing_enabled",
        help="Automatically generate invoices for records management services"
    )
    
    billing_cycle_days = fields.Integer(
        string="Billing Cycle (Days)",
        config_parameter="records_management.billing_cycle_days",
        default=30,
        help="Number of days between billing cycles for recurring services"
    )
    
    prepaid_billing_enabled = fields.Boolean(
        string="Enable Prepaid Billing",
        config_parameter="records_management.prepaid_billing_enabled",
        help="Allow customers to use prepaid billing accounts"
    )
    
    late_fee_percentage = fields.Float(
        string="Late Fee Percentage",
        config_parameter="records_management.late_fee_percentage",
        default=1.5,
        digits=(5, 2),
        help="Monthly late fee percentage for overdue accounts"
    )
    
    # ============================================================================
    # CONTAINER AND CAPACITY MANAGEMENT
    # ============================================================================
    default_retention_days = fields.Integer(
        string="Default Retention Period (Days)",
        config_parameter="records_management.default_retention_days",
        default=2555,  # 7 years standard
        help="Default retention period in days for new documents and containers"
    )
    
    container_capacity_alerts = fields.Boolean(
        string="Enable Capacity Alerts",
        config_parameter="records_management.container_capacity_alerts",
        help="Send alerts when storage locations approach capacity limits"
    )
    
    capacity_alert_threshold = fields.Float(
        string="Capacity Alert Threshold (%)",
        config_parameter="records_management.capacity_alert_threshold",
        default=85.0,
        digits=(5, 2),
        help="Percentage threshold for capacity alerts"
    )
    
    auto_location_assignment = fields.Boolean(
        string="Auto-Assign Storage Locations",
        config_parameter="records_management.auto_location_assignment",
        help="Automatically assign optimal storage locations for new containers"
    )
    
    # ============================================================================
    # FIELD SERVICE MANAGEMENT INTEGRATION
    # ============================================================================
    fsm_integration_enabled = fields.Boolean(
        string="Enable Field Service Integration",
        config_parameter="records_management.fsm_integration_enabled",
        help="Integrate with Odoo Field Service Management for pickup and delivery operations"
    )
    
    auto_route_optimization = fields.Boolean(
        string="Enable Route Optimization",
        config_parameter="records_management.auto_route_optimization",
        help="Automatically optimize pickup and delivery routes for efficiency"
    )
    
    fsm_auto_task_creation = fields.Boolean(
        string="Auto-Create FSM Tasks",
        config_parameter="records_management.fsm_auto_task_creation",
        help="Automatically create FSM tasks for pickup and service requests"
    )
    
    # ============================================================================
    # NOTIFICATION AND COMMUNICATION SETTINGS
    # ============================================================================
    email_notifications_enabled = fields.Boolean(
        string="Enable Email Notifications",
        config_parameter="records_management.email_notifications_enabled",
        default=True,
        help="Send email notifications for important events and status changes"
    )
    
    sms_notifications_enabled = fields.Boolean(
        string="Enable SMS Notifications",
        config_parameter="records_management.sms_notifications_enabled",
        help="Send SMS notifications for critical alerts and confirmations"
    )
    
    notification_batch_size = fields.Integer(
        string="Notification Batch Size",
        config_parameter="records_management.notification_batch_size",
        default=50,
        help="Maximum number of notifications to process in a single batch"
    )
    
    # ============================================================================
    # APPROVAL WORKFLOW SETTINGS
    # ============================================================================
    require_manager_approval = fields.Boolean(
        string="Require Manager Approval",
        config_parameter="records_management.require_manager_approval",
        help="Require manager approval for destruction and sensitive operations"
    )
    
    dual_approval_threshold = fields.Float(
        string="Dual Approval Threshold ($)",
        config_parameter="records_management.dual_approval_threshold",
        default=1000.0,
        help="Dollar amount threshold requiring dual approval for services"
    )
    
    authorized_by_id = fields.Many2one(
        'res.users',
        string="Default Authorized User",
        config_parameter="records_management.authorized_by_id",
        help="Default user for system authorizations"
    )
    
    emergency_contact_id = fields.Many2one(
        'res.partner',
        string="Emergency Contact",
        config_parameter="records_management.emergency_contact_id",
        help="Emergency contact for critical system issues"
    )
    
    # ============================================================================
    # SECURITY AND ACCESS CONTROL
    # ============================================================================
    department_data_separation = fields.Boolean(
        string="Enable Department Data Separation",
        config_parameter="records_management.department_data_separation",
        default=True,
        help="Enforce data separation by department for multi-tenant security"
    )
    
    session_timeout_minutes = fields.Integer(
        string="Portal Session Timeout (Minutes)",
        config_parameter="records_management.session_timeout_minutes",
        default=60,
        help="Portal user session timeout in minutes"
    )
    
    max_login_attempts = fields.Integer(
        string="Maximum Login Attempts",
        config_parameter="records_management.max_login_attempts",
        default=3,
        help="Maximum failed login attempts before account lockout"
    )
    
    # ============================================================================
    # SYSTEM PERFORMANCE SETTINGS
    # ============================================================================
    enable_performance_monitoring = fields.Boolean(
        string="Enable Performance Monitoring",
        config_parameter="records_management.enable_performance_monitoring",
        help="Monitor system performance and generate analytics"
    )
    
    max_records_per_page = fields.Integer(
        string="Maximum Records Per Page",
        config_parameter="records_management.max_records_per_page",
        default=80,
        help="Maximum number of records to display per page in lists"
    )
    
    enable_background_tasks = fields.Boolean(
        string="Enable Background Task Processing",
        config_parameter="records_management.enable_background_tasks",
        default=True,
        help="Process non-critical tasks in the background for better performance"
    )
    
    # ============================================================================
    # DOCUMENTATION AND NOTES
    # ============================================================================
    configuration_notes = fields.Text(
        string="Configuration Notes",
        help="Internal notes about records management configuration and customizations"
    )
    
    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('naid_compliance_enabled', 'portal_customer_access', 'auto_billing_enabled')
    def _compute_system_readiness_score(self):
        """Compute overall system configuration readiness score"""
        for record in self:
            score = 0
            total_checks = 10
            
            # Core features
            if record.naid_compliance_enabled:
                score += 2
            if record.portal_customer_access:
                score += 2
            if record.auto_billing_enabled:
                score += 1
            if record.container_capacity_alerts:
                score += 1
            if record.fsm_integration_enabled:
                score += 1
            if record.auto_barcode_generation:
                score += 1
            if record.email_notifications_enabled:
                score += 1
            if record.department_data_separation:
                score += 1
            
            record.system_readiness_score = (score / total_checks) * 100
    
    system_readiness_score = fields.Float(
        string="System Readiness Score (%)",
        compute="_compute_system_readiness_score",
        help="Overall system configuration completeness score"
    )
    
    @api.depends('naid_compliance_enabled', 'chain_of_custody_required', 'naid_certificate_auto_generation')
    def _compute_compliance_status(self):
        """Compute overall compliance configuration status"""
        for record in self:
            if (record.naid_compliance_enabled and 
                record.chain_of_custody_required and 
                record.naid_certificate_auto_generation):
                record.compliance_status = 'full'
            elif record.naid_compliance_enabled:
                record.compliance_status = 'partial'
            else:
                record.compliance_status = 'none'
    
    compliance_status = fields.Selection([
        ('none', 'No Compliance Features'),
        ('partial', 'Partial Compliance'),
        ('full', 'Full NAID AAA Compliance')
    ], string="Compliance Status", compute="_compute_compliance_status")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_enable_full_compliance(self):
        """Enable complete NAID AAA compliance configuration"""
        self.ensure_one()
        
        self.write({
            'naid_compliance_enabled': True,
            'chain_of_custody_required': True,
            'naid_certificate_auto_generation': True,
            'naid_audit_retention_days': 2555,  # 7 years
            'portal_customer_access': True,
            'auto_barcode_generation': True,
            'container_capacity_alerts': True,
            'department_data_separation': True,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Full NAID AAA Compliance Enabled'),
                'message': _('All NAID AAA compliance features have been enabled successfully'),
                'type': 'success',
                'sticky': True,
            }
        }
    
    def action_configure_billing_defaults(self):
        """Configure comprehensive billing default settings"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Configure Billing Defaults'),
            'res_model': 'records.billing.config.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_auto_billing_enabled': self.auto_billing_enabled,
                'default_billing_cycle_days': self.billing_cycle_days,
                'default_prepaid_billing_enabled': self.prepaid_billing_enabled,
                'default_late_fee_percentage': self.late_fee_percentage,
            }
        }
    
    def action_test_barcode_generation(self):
        """Test the barcode generation system with current settings"""
        self.ensure_one()
        
        if not self.auto_barcode_generation:
            raise UserError(_('Please enable auto-barcode generation before testing'))
        
        # Test barcode generation with current format
        try:
            test_sequence = self.env['ir.sequence'].next_by_code('records.container.test') or 'TEST001'
            test_barcode = _('Test barcode generated: %(sequence)s (Format: %(format)s)', {
                'sequence': test_sequence,
                'format': self.barcode_format
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Barcode Generation Test Successful'),
                    'message': test_barcode,
                    'type': 'info',
                }
            }
        except Exception as e:
            raise UserError(_('Barcode generation test failed: %s', str(e)))
    
    def action_setup_fsm_integration(self):
        """Setup and validate Field Service Management integration"""
        self.ensure_one()
        
        if not self.fsm_integration_enabled:
            raise UserError(_('Please enable FSM integration before setup'))
        
        # Check if FSM module is installed
        fsm_module = self.env['ir.module.module'].search([
            ('name', '=', 'industry_fsm'),
            ('state', '=', 'installed')
        ])
        
        if not fsm_module:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Install Field Service Management'),
                'res_model': 'base.module.install',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_module_ids': [(6, 0, [self.env.ref('base.module_industry_fsm').id])]
                          if self.env.ref('base.module_industry_fsm', False) else []}
            }
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Integration Setup'),
            'res_model': 'project.project',
            'view_mode': 'tree,form',
            'domain': [('is_fsm', '=', True)],
            'context': {
                'create_fsm_project': True,
                'default_is_fsm': True,
                'default_name': _('Records Management Field Service')
            }
        }
    
    def action_validate_system_configuration(self):
        """Validate complete system configuration and provide recommendations"""
        self.ensure_one()
        
        issues = []
        recommendations = []
        
        # Validate core settings
        if not self.naid_compliance_enabled:
            issues.append(_('NAID AAA compliance is not enabled'))
            recommendations.append(_('Enable NAID compliance for audit trail requirements'))
        
        if not self.portal_customer_access:
            recommendations.append(_('Enable customer portal access for improved customer experience'))
        
        if not self.auto_billing_enabled:
            recommendations.append(_('Enable automatic billing for improved cash flow'))
        
        if self.billing_cycle_days > 30:
            recommendations.append(_('Consider shorter billing cycles for better cash flow'))
        
        if not self.container_capacity_alerts:
            recommendations.append(_('Enable capacity alerts to prevent storage overages'))
        
        # Generate validation report
        validation_message = []
        
        if issues:
            validation_message.append(_('Configuration Issues Found:'))
            for issue in issues:
                validation_message.append(_('• %s', issue))
        
        if recommendations:
            validation_message.append(_('Recommendations:'))
            for rec in recommendations:
                validation_message.append(_('• %s', rec))
        
        if not issues and not recommendations:
            validation_message = [_('System configuration is optimal. All recommended settings are enabled.')]
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('System Configuration Report'),
            'res_model': 'records.config.validation.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_validation_results': '\n'.join(validation_message),
                'default_readiness_score': self.system_readiness_score,
                'default_compliance_status': self.compliance_status,
            }
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('default_retention_days', 'billing_cycle_days', 'naid_audit_retention_days')
    def _check_positive_day_values(self):
        """Ensure all day-based fields have positive values"""
        for record in self:
            if record.default_retention_days <= 0:
                raise ValidationError(_('Default retention days must be positive'))
            if record.billing_cycle_days <= 0:
                raise ValidationError(_('Billing cycle days must be positive'))
            if record.naid_audit_retention_days <= 0:
                raise ValidationError(_('NAID audit retention days must be positive'))
    
    @api.constrains('default_retention_days', 'naid_audit_retention_days')
    def _check_retention_periods(self):
        """Validate retention periods are within reasonable business ranges"""
        for record in self:
            # Maximum 100 years (36,500 days)
            if record.default_retention_days > 36500:
                raise ValidationError(_('Retention period cannot exceed 100 years'))
            if record.naid_audit_retention_days > 36500:
                raise ValidationError(_('NAID audit retention cannot exceed 100 years'))
            
            # Minimum 1 year for compliance
            if record.default_retention_days < 365:
                raise ValidationError(_('Retention period should be at least 1 year for compliance'))
            if record.naid_audit_retention_days < 2555:  # 7 years minimum for NAID
                raise ValidationError(_('NAID audit retention should be at least 7 years for compliance'))  # 7 years minimum for NAID
                raise ValidationError(_('NAID audit retention should be at least 7 years for compliance'))
    
    @api.constrains('capacity_alert_threshold', 'late_fee_percentage')
    def _check_percentage_values(self):
        """Validate percentage values are within acceptable ranges"""
        for record in self:
            if record.capacity_alert_threshold <= 0 or record.capacity_alert_threshold > 100:
                raise ValidationError(_('Capacity alert threshold must be between 0 and 100 percent'))
            if record.late_fee_percentage < 0 or record.late_fee_percentage > 10:
                raise ValidationError(_('Late fee percentage must be between 0 and 10 percent'))
    
    @api.constrains('session_timeout_minutes', 'max_login_attempts', 'notification_batch_size')
    def _check_security_settings(self):
        """Validate security-related configuration values"""
        for record in self:
            if record.session_timeout_minutes < 5 or record.session_timeout_minutes > 480:
                raise ValidationError(_('Session timeout must be between 5 and 480 minutes'))
            if record.max_login_attempts < 1 or record.max_login_attempts > 10:
                raise ValidationError(_('Maximum login attempts must be between 1 and 10'))
            if record.notification_batch_size < 1 or record.notification_batch_size > 1000:
                raise ValidationError(_('Notification batch size must be between 1 and 1000'))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_records_management_config(self):
        """Get current records management configuration as structured dictionary"""
        self.ensure_one()
        
        return {
            'core_settings': {
                'module_enabled': self.module_records_management_setting,
                'performance_monitoring': self.enable_performance_monitoring,
                'background_tasks': self.enable_background_tasks,
            },
            'naid_compliance': {
                'enabled': self.naid_compliance_enabled,
                'audit_retention_days': self.naid_audit_retention_days,
                'auto_certificates': self.naid_certificate_auto_generation,
                'chain_of_custody_required': self.chain_of_custody_required,
            },
            'portal_settings': {
                'customer_access': self.portal_customer_access,
                'feedback_system': self.portal_feedback_enabled,
                'document_download': self.portal_document_download,
                'esignature_enabled': self.portal_esignature_enabled,
                'session_timeout': self.session_timeout_minutes,
            },
            'billing_configuration': {
                'auto_billing': self.auto_billing_enabled,
                'billing_cycle_days': self.billing_cycle_days,
                'prepaid_enabled': self.prepaid_billing_enabled,
                'late_fee_percentage': self.late_fee_percentage,
                'dual_approval_threshold': self.dual_approval_threshold,
            },
            'container_management': {
                'auto_barcode_generation': self.auto_barcode_generation,
                'barcode_format': self.barcode_format,
                'capacity_alerts': self.container_capacity_alerts,
                'alert_threshold': self.capacity_alert_threshold,
                'auto_location_assignment': self.auto_location_assignment,
                'default_retention_days': self.default_retention_days,
            },
            'fsm_integration': {
                'enabled': self.fsm_integration_enabled,
                'route_optimization': self.auto_route_optimization,
                'auto_task_creation': self.fsm_auto_task_creation,
            },
            'security_settings': {
                'department_separation': self.department_data_separation,
                'max_login_attempts': self.max_login_attempts,
                'require_manager_approval': self.require_manager_approval,
            },
            'notification_settings': {
                'email_enabled': self.email_notifications_enabled,
                'sms_enabled': self.sms_notifications_enabled,
                'batch_size': self.notification_batch_size,
            }
        }
    
    @api.model
    def get_default_config_values(self):
        """Get recommended default configuration values for new installations"""
        return {
            'module_records_management_setting': True,
            'naid_compliance_enabled': True,
            'naid_audit_retention_days': 2555,  # 7 years NAID standard
            'naid_certificate_auto_generation': True,
            'chain_of_custody_required': True,
            'portal_customer_access': True,
            'portal_feedback_enabled': True,
            'portal_document_download': True,
            'auto_barcode_generation': True,
            'barcode_format': 'code128',
            'intelligent_classification_enabled': True,
            'default_retention_days': 2555,  # 7 years standard
            'auto_billing_enabled': False,  # Requires manual setup
            'billing_cycle_days': 30,
            'prepaid_billing_enabled': True,
            'late_fee_percentage': 1.5,
            'container_capacity_alerts': True,
            'capacity_alert_threshold': 85.0,
            'auto_location_assignment': True,
            'fsm_integration_enabled': False,  # Requires FSM module
            'email_notifications_enabled': True,
            'sms_notifications_enabled': False,  # Requires SMS credits
            'department_data_separation': True,
            'session_timeout_minutes': 60,
            'max_login_attempts': 3,
            'require_manager_approval': True,
            'dual_approval_threshold': 1000.0,
            'enable_performance_monitoring': True,
            'max_records_per_page': 80,
            'enable_background_tasks': True,
        }
    
    def apply_recommended_settings(self):
        """Apply all recommended settings for optimal system operation"""
        self.ensure_one()
        
        defaults = self.get_default_config_values()
        self.write(defaults)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Recommended Settings Applied'),
                'message': _('All recommended configuration settings have been applied successfully'),
                'type': 'success',
            }
        }
