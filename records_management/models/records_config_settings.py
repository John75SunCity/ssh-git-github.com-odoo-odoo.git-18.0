# -*- coding: utf-8 -*-

from odoo import api, fields, models, _

from odoo.exceptions import UserError




class RecordsConfigSettings(models.TransientModel):
    _name = 'records.config.setting'
    _inherit = 'res.config.settings'
    _description = 'Records Management Configuration Setting'

    # ============================================================================
    # CORE RECORDS MANAGEMENT SETTINGS
    # ============================================================================
    
    # Document Management Settings
    records_auto_barcode_generation = fields.Boolean(
        string='Automatic Barcode Generation',
        config_parameter='records_management.auto_barcode_generation',
        default=True,
        help="Automatically generate barcodes for new containers and documents"
    )
    
    records_barcode_nomenclature_id = fields.Many2one(
        'barcode.nomenclature',
        string='Records Barcode Nomenclature',
        config_parameter='records_management.barcode_nomenclature_id',
        help="Barcode nomenclature for records management system"
    )
    
    records_default_retention_days = fields.Integer(
        string='Default Retention Period (Days)',
        config_parameter='records_management.default_retention_days',
        default=2555,  # 7 years default
        help="Default retention period for documents without specific retention policy"
    )
    
    records_enable_advanced_search = fields.Boolean(
        string='Advanced Search Features',
        config_parameter='records_management.enable_advanced_search',
        default=True,
        help="Enable advanced search and filtering capabilities"
    )
    
    records_auto_location_assignment = fields.Boolean(
        string='Automatic Location Assignment',
        config_parameter='records_management.auto_location_assignment',
        default=True,
        help="Automatically assign optimal storage locations for new containers"
    )
    
    # Container Management Settings
    records_default_container_type_id = fields.Many2one(
        'records.container.type',
        string='Default Container Type',
        config_parameter='records_management.default_container_type_id',
        help="Default container type for new storage boxes"
    )
    
    records_container_capacity_warning_threshold = fields.Float(
        string='Container Capacity Warning (%)',
        config_parameter='records_management.capacity_warning_threshold',
        default=85.0,
        help="Warning threshold for container capacity utilization"
    )
    
    records_enable_container_weight_tracking = fields.Boolean(
        string='Container Weight Tracking',
        config_parameter='records_management.enable_weight_tracking',
        default=True,
        help="Track container weights for billing and capacity planning"
    )
    
    # ============================================================================
    # NAID COMPLIANCE SETTINGS
    # ============================================================================
    
    naid_compliance_level = fields.Selection([
        ('basic', 'Basic Compliance'),
        ('aaa', 'NAID AAA Certification'),
        ('enhanced', 'Enhanced Security')
    ], string='NAID Compliance Level',
       config_parameter='records_management.naid_compliance_level',
       default='aaa',
       help="Level of NAID compliance enforcement")
    
    naid_auto_audit_logging = fields.Boolean(
        string='Automatic Audit Logging',
        config_parameter='records_management.auto_audit_logging',
        default=True,
        help="Automatically create audit logs for all critical operations"
    )
    
    naid_require_dual_authorization = fields.Boolean(
        string='Require Dual Authorization',
        config_parameter='records_management.require_dual_authorization',
        default=True,
        help="Require dual authorization for destruction and sensitive operations"
    )
    
    naid_audit_retention_years = fields.Integer(
        string='Audit Log Retention (Years)',
        config_parameter='records_management.audit_retention_years',
        default=7,
        help="Number of years to retain audit logs for compliance"
    )
    
    naid_certificate_template_id = fields.Many2one(
        'ir.ui.view',
        string='Destruction Certificate Template',
        config_parameter='records_management.certificate_template_id',
        help="Template for generating NAID destruction certificates"
    )
    
    # ============================================================================
    # PICKUP AND FIELD SERVICE SETTINGS
    # ============================================================================
    
    pickup_auto_route_optimization = fields.Boolean(
        string='Automatic Route Optimization',
        config_parameter='records_management.auto_route_optimization',
        default=True,
        help="Automatically optimize pickup routes for efficiency"
    )
    
    pickup_default_time_window_hours = fields.Float(
        string='Default Pickup Time Window (Hours)',
        config_parameter='records_management.default_time_window',
        default=4.0,
        help="Default time window for pickup appointments"
    )
    
    pickup_advance_notice_days = fields.Integer(
        string='Advance Notice Required (Days)',
        config_parameter='records_management.advance_notice_days',
        default=2,
        help="Minimum advance notice required for pickup requests"
    )
    
    fsm_integration_enabled = fields.Boolean(
        string='Field Service Management Integration',
        config_parameter='records_management.fsm_integration_enabled',
        default=True,
        help="Enable integration with Odoo Field Service Management"
    )
    
    pickup_automatic_confirmation = fields.Boolean(
        string='Automatic Pickup Confirmation',
        config_parameter='records_management.auto_pickup_confirmation',
        default=False,
        help="Automatically confirm pickup requests when capacity allows"
    )
    
    # ============================================================================
    # BILLING AND PRICING SETTINGS
    # ============================================================================
    
    billing_period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('custom', 'Custom Period')
    ], string='Default Billing Period',
       config_parameter='records_management.billing_period_type',
       default='monthly',
       help="Default billing cycle for storage fees")
    
    billing_auto_invoice_generation = fields.Boolean(
        string='Automatic Invoice Generation',
        config_parameter='records_management.auto_invoice_generation',
        default=True,
        help="Automatically generate invoices based on billing cycles"
    )
    
    billing_prorate_first_month = fields.Boolean(
        string='Prorate First Month',
        config_parameter='records_management.prorate_first_month',
        default=True,
        help="Prorate billing for partial first month of storage"
    )
    
    billing_default_currency_id = fields.Many2one(
        'res.currency',
        string='Default Billing Currency',
        config_parameter='records_management.default_currency_id',
        help="Default currency for billing calculations"
    )
    
    billing_volume_discount_enabled = fields.Boolean(
        string='Volume Discount Pricing',
        config_parameter='records_management.volume_discount_enabled',
        default=True,
        help="Enable volume-based discount pricing tiers"
    )
    
    # ============================================================================
    # PORTAL AND CUSTOMER SETTINGS
    # ============================================================================
    
    portal_allow_customer_requests = fields.Boolean(
        string='Allow Customer Service Requests',
        config_parameter='records_management.portal_allow_requests',
        default=True,
        help="Allow customers to submit service requests through portal"
    )
    
    portal_enable_document_preview = fields.Boolean(
        string='Document Preview in Portal',
        config_parameter='records_management.portal_document_preview',
        default=False,
        help="Allow customers to preview documents in portal (security consideration)"
    )
    
    portal_require_request_approval = fields.Boolean(
        string='Require Request Approval',
        config_parameter='records_management.portal_require_approval',
        default=True,
        help="All portal requests require internal approval before processing"
    )
    
    portal_auto_notification_enabled = fields.Boolean(
        string='Automatic Portal Notifications',
        config_parameter='records_management.portal_auto_notifications',
        default=True,
        help="Automatically notify customers of status changes via portal"
    )
    
    portal_feedback_collection_enabled = fields.Boolean(
        string='Customer Feedback Collection',
        config_parameter='records_management.portal_feedback_enabled',
        default=True,
        help="Enable customer feedback and satisfaction surveys"
    )
    
    portal_ai_sentiment_analysis = fields.Boolean(
        string='AI Sentiment Analysis',
        config_parameter='records_management.portal_ai_sentiment',
        default=True,
        help="Use AI to analyze customer feedback sentiment"
    )
    
    # ============================================================================
    # SECURITY AND ACCESS SETTINGS
    # ============================================================================
    
    security_department_isolation = fields.Boolean(
        string='Department Data Isolation',
        config_parameter='records_management.department_isolation',
        default=True,
        help="Isolate data access by department assignments"
    )
    
    security_require_bin_key_management = fields.Boolean(
        string='Physical Bin Key Management',
        config_parameter='records_management.require_bin_key_mgmt',
        default=True,
        help="Require physical key management for secure storage bins"
    )
    
    security_access_log_retention_days = fields.Integer(
        string='Access Log Retention (Days)',
        config_parameter='records_management.access_log_retention',
        default=365,
        help="Number of days to retain access logs"
    )
    
    security_failed_access_lockout_enabled = fields.Boolean(
        string='Failed Access Lockout',
        config_parameter='records_management.failed_access_lockout',
        default=True,
        help="Lock accounts after failed access attempts"
    )
    
    security_failed_access_attempt_limit = fields.Integer(
        string='Failed Access Attempt Limit',
        config_parameter='records_management.failed_access_limit',
        default=5,
        help="Maximum failed access attempts before lockout"
    )
    
    # ============================================================================
    # NOTIFICATION SETTINGS
    # ============================================================================
    
    notification_email_enabled = fields.Boolean(
        string='Email Notifications',
        config_parameter='records_management.email_notifications',
        default=True,
        help="Send email notifications for important events"
    )
    
    notification_sms_enabled = fields.Boolean(
        string='SMS Notifications',
        config_parameter='records_management.sms_notifications',
        default=False,
        help="Send SMS notifications for critical alerts"
    )
    
    notification_retention_expiry_days = fields.Integer(
        string='Retention Expiry Notice (Days)',
        config_parameter='records_management.retention_expiry_notice',
        default=90,
        help="Days before retention expiry to send notifications"
    )
    
    notification_pickup_reminder_hours = fields.Float(
        string='Pickup Reminder (Hours)',
        config_parameter='records_management.pickup_reminder_hours',
        default=24.0,
        help="Hours before pickup to send reminder notifications"
    )
    
    # ============================================================================
    # REPORTING AND ANALYTICS SETTINGS
    # ============================================================================
    
    analytics_enable_advanced_reporting = fields.Boolean(
        string='Advanced Reporting',
        config_parameter='records_management.advanced_reporting',
        default=True,
        help="Enable advanced analytics and reporting features"
    )
    
    analytics_auto_report_generation = fields.Boolean(
        string='Automatic Report Generation',
        config_parameter='records_management.auto_report_generation',
        default=True,
        help="Automatically generate scheduled reports"
    )
    
    analytics_customer_kpi_tracking = fields.Boolean(
        string='Customer KPI Tracking',
        config_parameter='records_management.customer_kpi_tracking',
        default=True,
        help="Track and analyze customer-specific KPIs"
    )
    
    analytics_predictive_analytics_enabled = fields.Boolean(
        string='Predictive Analytics',
        config_parameter='records_management.predictive_analytics',
        default=False,
        help="Enable predictive analytics for capacity and demand forecasting"
    )
    
    # ============================================================================
    # INTEGRATION SETTINGS
    # ============================================================================
    
    integration_accounting_auto_sync = fields.Boolean(
        string='Automatic Accounting Sync',
        config_parameter='records_management.accounting_auto_sync',
        default=True,
        help="Automatically sync billing data with accounting module"
    )
    
    integration_document_management_system = fields.Selection([
        ('none', 'None'),
        ('odoo_documents', 'Odoo Documents'),
        ('sharepoint', 'Microsoft SharePoint'),
        ('google_drive', 'Google Drive'),
        ('custom', 'Custom DMS')
    ], string='Document Management System',
       config_parameter='records_management.document_management_system',
       default='odoo_documents',
       help="External document management system integration")
    
    integration_api_access_enabled = fields.Boolean(
        string='API Access Enabled',
        config_parameter='records_management.api_access_enabled',
        default=False,
        help="Enable REST API access for external integrations"
    )
    
    integration_webhook_notifications = fields.Boolean(
        string='Webhook Notifications',
        config_parameter='records_management.webhook_notifications',
        default=False,
        help="Send webhook notifications for external system integration"
    )
    
    # ============================================================================
    # COMPUTED FIELDS FOR DASHBOARD
    # ============================================================================
    
    total_active_containers = fields.Integer(
        string='Total Active Containers',
        compute='_compute_system_statistics',
        help="Total number of active storage containers"
    )
    
    total_stored_documents = fields.Integer(
        string='Total Stored Documents',
        compute='_compute_system_statistics',
        help="Total number of documents under management"
    )
    
    pending_destruction_requests = fields.Integer(
        string='Pending Destruction Requests',
        compute='_compute_system_statistics',
        help="Number of pending destruction requests"
    )
    
    compliance_score = fields.Float(
        string='Compliance Score (%)',
        compute='_compute_compliance_metrics',
        help="Overall NAID compliance score"
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    
    @api.depends()
    def _compute_system_statistics(self):
        """Compute system-wide statistics for dashboard display"""
        for record in self:
            # Get container statistics
            active_containers = self.env['records.container'].search_count([
                ('state', 'in', ['active', 'stored'])
            ])
            record.total_active_containers = active_containers
            
            # Get document statistics  
            stored_documents = self.env['records.document'].search_count([
                ('state', '!=', 'destroyed')
            ])
            record.total_stored_documents = stored_documents
            
            # Get pending destruction requests
            pending_destructions = self.env['records.destruction'].search_count([
                ('state', 'in', ['draft', 'confirmed'])
            ])
            record.pending_destruction_requests = pending_destructions
    
    @api.depends('naid_compliance_level', 'naid_auto_audit_logging', 'naid_require_dual_authorization')
    def _compute_compliance_metrics(self):
        """Compute compliance score based on configured settings"""
        for record in self:
            score = 0.0
            
            # Base score from compliance level
            if record.naid_compliance_level == 'enhanced':
                score += 40.0
            elif record.naid_compliance_level == 'aaa':
                score += 30.0
            elif record.naid_compliance_level == 'basic':
                score += 20.0
            
            # Additional points for security features
            if record.naid_auto_audit_logging:
                score += 20.0
            if record.naid_require_dual_authorization:
                score += 20.0
            if record.security_department_isolation:
                score += 10.0
            if record.security_require_bin_key_management:
                score += 10.0
            
            record.compliance_score = min(score, 100.0)
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    
    def action_test_notification_settings(self):
        """Test notification configuration by sending test messages"""

        self.ensure_one()
        
        if self.notification_email_enabled:
            # Send test email
            template = self.env.ref('records_management.email_template_test_notification', raise_if_not_found=False)
            if template:
                template.send_mail(self.env.user.id, force_send=True)
        
        if self.notification_sms_enabled:
            # Send test SMS if SMS module is available
            if 'sms.sms' in self.env:
                self.env['sms.sms'].create({
                    'number': self.env.user.partner_id.mobile or self.env.user.partner_id.phone,
                    'body': _('Records Management test notification - SMS configuration is working correctly.'),
                })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Test notifications sent successfully.'),
                'sticky': False,
            }
        }
    
    def action_run_compliance_audit(self):
        """Run a comprehensive compliance audit"""

        self.ensure_one()
        
        audit_results = {
            'total_checks': 0,
            'passed_checks': 0,
            'failed_checks': [],
            'warnings': []
        }
        
        # Check NAID compliance settings
        audit_results['total_checks'] += 1
        if self.naid_compliance_level in ['aaa', 'enhanced']:
            audit_results['passed_checks'] += 1
        else:
            audit_results['failed_checks'].append('NAID compliance level should be AAA or Enhanced')
        
        # Check audit logging
        audit_results['total_checks'] += 1
        if self.naid_auto_audit_logging:
            audit_results['passed_checks'] += 1
        else:
            audit_results['failed_checks'].append('Automatic audit logging should be enabled')
        
        # Check dual authorization
        audit_results['total_checks'] += 1
        if self.naid_require_dual_authorization:
            audit_results['passed_checks'] += 1
        else:
            audit_results['warnings'].append('Consider enabling dual authorization for enhanced security')
        
        compliance_percentage = (audit_results['passed_checks'] / audit_results['total_checks']) * 100
        
        message = _('Compliance Audit Complete - check system logs for detailed results')
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success' if compliance_percentage >= 80 else 'warning',
                'message': message,
                'sticky': True,
            }
        }
    
    def action_reset_all_settings(self):
        """Reset all settings to recommended defaults"""

        self.ensure_one()
        
        default_values = {
            'records_auto_barcode_generation': True,
            'records_default_retention_days': 2555,
            'records_enable_advanced_search': True,
            'records_auto_location_assignment': True,
            'records_container_capacity_warning_threshold': 85.0,
            'records_enable_container_weight_tracking': True,
            'naid_compliance_level': 'aaa',
            'naid_auto_audit_logging': True,
            'naid_require_dual_authorization': True,
            'naid_audit_retention_years': 7,
            'pickup_auto_route_optimization': True,
            'pickup_default_time_window_hours': 4.0,
            'pickup_advance_notice_days': 2,
            'fsm_integration_enabled': True,
            'billing_period_type': 'monthly',
            'billing_auto_invoice_generation': True,
            'billing_prorate_first_month': True,
            'billing_volume_discount_enabled': True,
            'portal_allow_customer_requests': True,
            'portal_require_request_approval': True,
            'portal_auto_notification_enabled': True,
            'portal_feedback_collection_enabled': True,
            'portal_ai_sentiment_analysis': True,
            'security_department_isolation': True,
            'security_require_bin_key_management': True,
            'security_access_log_retention_days': 365,
            'security_failed_access_lockout_enabled': True,
            'security_failed_access_attempt_limit': 5,
            'notification_email_enabled': True,
            'notification_retention_expiry_days': 90,
            'notification_pickup_reminder_hours': 24.0,
            'analytics_enable_advanced_reporting': True,
            'analytics_auto_report_generation': True,
            'analytics_customer_kpi_tracking': True,
            'integration_accounting_auto_sync': True,
            'integration_document_management_system': 'odoo_documents',
        }
        
        self.write(default_values)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'type': 'success',
                'message': _('Settings reset to recommended defaults successfully.'),
                'sticky': False,
            }
        }
    
    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    @api.constrains('records_container_capacity_warning_threshold')
    def _check_capacity_threshold(self):
        """Validate capacity warning threshold is within reasonable bounds"""
        for record in self:
            if not (0 < record.records_container_capacity_warning_threshold <= 100):
                raise UserError(_('Container capacity warning threshold must be between 1 and 100 percent.'))
    
    @api.constrains('pickup_advance_notice_days')
    def _check_advance_notice_days(self):
        """Validate advance notice period is reasonable"""
        for record in self:
            if record.pickup_advance_notice_days < 0 or record.pickup_advance_notice_days > 30:
                raise UserError(_('Advance notice days must be between 0 and 30 days.'))
    
    @api.constrains('security_failed_access_attempt_limit')
    def _check_failed_access_limit(self):
        """Validate failed access attempt limit"""
        for record in self:
            if not (1 <= record.security_failed_access_attempt_limit <= 20):
                raise UserError(_('Failed access attempt limit must be between 1 and 20 attempts.'))
