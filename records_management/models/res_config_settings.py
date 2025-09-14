from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ============================================================================
    # DASHBOARD/OVERVIEW FIELDS (Computed readonly fields)
    # ============================================================================
    total_active_containers = fields.Integer(
        string="Total Active Containers",
        compute='_compute_dashboard_stats',
        readonly=True,
        help="Current number of active containers in storage"
    )

    total_stored_documents = fields.Integer(
        string="Total Stored Documents",
        compute='_compute_dashboard_stats',
        readonly=True,
        help="Current number of documents in storage"
    )

    pending_destruction_requests = fields.Integer(
        string="Pending Destruction Requests",
        compute='_compute_dashboard_stats',
        readonly=True,
        help="Number of destruction requests awaiting processing"
    )

    compliance_score = fields.Float(
        string="Compliance Score",
        compute='_compute_dashboard_stats',
        readonly=True,
        help="Overall NAID compliance score percentage"
    )

    # ============================================================================
    # RECORDS MANAGEMENT SETTINGS
    # ============================================================================
    records_auto_barcode_generation = fields.Boolean(
        string="Auto Barcode Generation",
        config_parameter='records_management.auto_barcode_generation',
        help="Automatically generate barcodes for new containers and documents"
    )

    records_enable_advanced_search = fields.Boolean(
        string="Enable Advanced Search",
        config_parameter='records_management.enable_advanced_search',
        help="Enable advanced search and filtering capabilities"
    )

    records_auto_location_assignment = fields.Boolean(
        string="Auto Location Assignment",
        config_parameter='records_management.auto_location_assignment',
        help="Automatically assign optimal storage locations for new containers"
    )

    records_enable_container_weight_tracking = fields.Boolean(
        string="Container Weight Tracking",
        config_parameter='records_management.enable_container_weight_tracking',
        help="Track container weights for billing and capacity planning"
    )

    records_barcode_nomenclature_id = fields.Many2one(
        'barcode.nomenclature',
        string="Barcode Nomenclature",
        config_parameter='records_management.barcode_nomenclature_id',
        help="Barcode nomenclature for records management system"
    )

    records_default_retention_days = fields.Integer(
        string="Default Retention (Days)",
        config_parameter='records_management.default_retention_days',
        default=2555,  # 7 years
        help="Default retention period for documents without specific policy"
    )

    records_default_container_type_id = fields.Many2one(
        'records.container.type',
        string="Default Container Type",
        config_parameter='records_management.default_container_type_id',
        help="Default container type for new storage boxes"
    )

    records_container_capacity_warning_threshold = fields.Float(
        string="Capacity Warning (%)",
        config_parameter='records_management.container_capacity_warning_threshold',
        default=85.0,
        help="Warning threshold for container capacity utilization"
    )

    # ============================================================================
    # NAID COMPLIANCE & SECURITY SETTINGS
    # ============================================================================
    naid_compliance_level = fields.Selection([
        ('basic', 'Basic'),
        ('aaa', 'AAA Standard'),
        ('enhanced', 'Enhanced AAA')
    ], string="Compliance Level",
        config_parameter='records_management.naid_compliance_level',
        default='aaa',
        help="Level of NAID compliance enforcement"
    )

    naid_auto_audit_logging = fields.Boolean(
        string="Auto Audit Logging",
        config_parameter='records_management.naid_auto_audit_logging',
        default=True,
        help="Automatically create audit logs for all critical operations"
    )

    naid_require_dual_authorization = fields.Boolean(
        string="Require Dual Authorization",
        config_parameter='records_management.naid_require_dual_authorization',
        help="Require dual authorization for destruction and sensitive operations"
    )

    security_department_isolation = fields.Boolean(
        string="Department Isolation",
        config_parameter='records_management.security_department_isolation',
        help="Isolate data access by department assignments"
    )

    security_require_bin_key_management = fields.Boolean(
        string="Bin Key Management",
        config_parameter='records_management.security_require_bin_key_management',
        help="Require physical key management for secure storage bins"
    )

    naid_audit_retention_years = fields.Integer(
        string="Audit Retention (Years)",
        config_parameter='records_management.naid_audit_retention_years',
        default=10,
        help="Number of years to retain audit logs for compliance"
    )

    security_failed_access_lockout_enabled = fields.Boolean(
        string="Failed Access Lockout",
        config_parameter='records_management.security_failed_access_lockout_enabled',
        help="Lock accounts after failed access attempts"
    )

    security_failed_access_attempt_limit = fields.Integer(
        string="Failed Access Limit",
        config_parameter='records_management.security_failed_access_attempt_limit',
        default=5,
        help="Maximum failed access attempts before lockout"
    )

    # ============================================================================
    # PICKUP & FIELD SERVICE SETTINGS
    # ============================================================================
    pickup_auto_route_optimization = fields.Boolean(
        string="Auto Route Optimization",
        config_parameter='records_management.pickup_auto_route_optimization',
        help="Automatically optimize pickup routes for efficiency"
    )

    fsm_integration_enabled = fields.Boolean(
        string="FSM Integration",
        config_parameter='records_management.fsm_integration_enabled',
        help="Enable integration with Odoo Field Service Management"
    )

    pickup_automatic_confirmation = fields.Boolean(
        string="Automatic Confirmation",
        config_parameter='records_management.pickup_automatic_confirmation',
        help="Automatically confirm pickup requests when capacity allows"
    )

    pickup_default_time_window_hours = fields.Float(
        string="Time Window (Hours)",
        config_parameter='records_management.pickup_default_time_window_hours',
        default=4.0,
        help="Default time window for pickup appointments"
    )

    pickup_advance_notice_days = fields.Integer(
        string="Advance Notice (Days)",
        config_parameter='records_management.pickup_advance_notice_days',
        default=2,
        help="Minimum advance notice required for pickup requests"
    )

    # ============================================================================
    # BILLING & PRICING SETTINGS
    # ============================================================================
    billing_period_type = fields.Selection([
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string="Billing Period",
        config_parameter='records_management.billing_period_type',
        default='monthly',
        help="Default billing cycle for storage fees"
    )

    billing_auto_invoice_generation = fields.Boolean(
        string="Auto Invoice Generation",
        config_parameter='records_management.billing_auto_invoice_generation',
        help="Automatically generate invoices based on billing cycles"
    )

    billing_prorate_first_month = fields.Boolean(
        string="Prorate First Month",
        config_parameter='records_management.billing_prorate_first_month',
        help="Prorate billing for partial first month of storage"
    )

    billing_volume_discount_enabled = fields.Boolean(
        string="Volume Discount",
        config_parameter='records_management.billing_volume_discount_enabled',
        help="Enable volume-based discount pricing tiers"
    )

    billing_default_currency_id = fields.Many2one(
        'res.currency',
        string="Default Currency",
        config_parameter='records_management.billing_default_currency_id',
        help="Default currency for billing calculations"
    )

    # ============================================================================
    # CUSTOMER PORTAL SETTINGS
    # ============================================================================
    portal_allow_customer_requests = fields.Boolean(
        string="Allow Customer Requests",
        config_parameter='records_management.portal_allow_customer_requests',
        help="Allow customers to submit service requests through portal"
    )

    portal_enable_document_preview = fields.Boolean(
        string="Document Preview",
        config_parameter='records_management.portal_enable_document_preview',
        help="Allow customers to preview documents in portal (security consideration)"
    )

    portal_require_request_approval = fields.Boolean(
        string="Require Request Approval",
        config_parameter='records_management.portal_require_request_approval',
        help="All portal requests require internal approval before processing"
    )

    portal_auto_notification_enabled = fields.Boolean(
        string="Auto Notifications",
        config_parameter='records_management.portal_auto_notification_enabled',
        help="Automatically notify customers of status changes via portal"
    )

    portal_feedback_collection_enabled = fields.Boolean(
        string="Feedback Collection",
        config_parameter='records_management.portal_feedback_collection_enabled',
        help="Enable customer feedback and satisfaction surveys"
    )

    portal_ai_sentiment_analysis = fields.Boolean(
        string="AI Sentiment Analysis",
        config_parameter='records_management.portal_ai_sentiment_analysis',
        help="Use AI to analyze customer feedback sentiment"
    )

    # ============================================================================
    # NOTIFICATION SETTINGS
    # ============================================================================
    notification_email_enabled = fields.Boolean(
        string="Email Notifications",
        config_parameter='records_management.notification_email_enabled',
        default=True,
        help="Send email notifications for important events"
    )

    notification_sms_enabled = fields.Boolean(
        string="SMS Notifications",
        config_parameter='records_management.notification_sms_enabled',
        help="Send SMS notifications for critical alerts"
    )

    notification_retention_expiry_days = fields.Integer(
        string="Retention Expiry Notice (Days)",
        config_parameter='records_management.notification_retention_expiry_days',
        default=30,
        help="Days before retention expiry to send notifications"
    )

    notification_pickup_reminder_hours = fields.Integer(
        string="Pickup Reminder (Hours)",
        config_parameter='records_management.notification_pickup_reminder_hours',
        default=24,
        help="Hours before pickup to send reminder notifications"
    )

    # ============================================================================
    # ANALYTICS & REPORTING SETTINGS
    # ============================================================================
    analytics_enable_advanced_reporting = fields.Boolean(
        string="Advanced Reporting",
        config_parameter='records_management.analytics_enable_advanced_reporting',
        help="Enable advanced analytics and reporting features"
    )

    analytics_auto_report_generation = fields.Boolean(
        string="Auto Report Generation",
        config_parameter='records_management.analytics_auto_report_generation',
        help="Automatically generate scheduled reports"
    )

    analytics_customer_kpi_tracking = fields.Boolean(
        string="Customer KPI Tracking",
        config_parameter='records_management.analytics_customer_kpi_tracking',
        help="Track and analyze customer-specific KPIs"
    )

    analytics_predictive_analytics_enabled = fields.Boolean(
        string="Predictive Analytics",
        config_parameter='records_management.analytics_predictive_analytics_enabled',
        help="Enable predictive analytics for capacity and demand forecasting"
    )

    # ============================================================================
    # SYSTEM INTEGRATION SETTINGS
    # ============================================================================
    integration_accounting_auto_sync = fields.Boolean(
        string="Accounting Auto Sync",
        config_parameter='records_management.integration_accounting_auto_sync',
        help="Automatically sync billing data with accounting module"
    )

    integration_document_management_system = fields.Selection([
        ('internal', 'Internal Only'),
        ('sharepoint', 'SharePoint'),
        ('drive', 'Google Drive'),
        ('dropbox', 'Dropbox'),
        ('custom', 'Custom Integration')
    ], string="Document Management System",
        config_parameter='records_management.integration_document_management_system',
        default='internal',
        help="External document management system integration"
    )

    integration_api_access_enabled = fields.Boolean(
        string="API Access",
        config_parameter='records_management.integration_api_access_enabled',
        help="Enable REST API access for external integrations"
    )

    integration_webhook_notifications = fields.Boolean(
        string="Webhook Notifications",
        config_parameter='records_management.integration_webhook_notifications',
        help="Send webhook notifications for external system integration"
    )

    # ============================================================================
    # LEGACY FIELDS (keeping for backward compatibility)
    # ============================================================================
    naid_compliance_enabled = fields.Boolean(
        string="Enable NAID Compliance",
        config_parameter='records_management.naid_compliance_enabled',
        help="Enables full NAID AAA compliance tracking and reporting."
    )

    naid_audit_retention_days = fields.Integer(
        string="NAID Audit Retention (Days)",
        config_parameter='records_management.naid_audit_retention_days',
        help="Number of days to retain NAID audit logs."
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends()
    def _compute_dashboard_stats(self):
        """Compute dashboard statistics"""
        for record in self:
            # Get active containers count
            container_count = self.env['records.container'].search_count([
                ('state', '!=', 'destroyed')
            ])

            # Get stored documents count (approximate)
            document_count = self.env['records.document'].search_count([]) if self.env['records.document']._table_exists() else 0

            # Get pending destruction requests
            destruction_count = 0
            if self.env['destruction.request']._table_exists():
                destruction_count = self.env['destruction.request'].search_count([
                    ('state', 'in', ['draft', 'pending', 'approved'])
                ])

            # Calculate compliance score (simplified)
            compliance_score = 95.0  # Default high score

            record.total_active_containers = container_count
            record.total_stored_documents = document_count
            record.pending_destruction_requests = destruction_count
            record.compliance_score = compliance_score

    # ============================================================================
    # METHODS - Bridge between res.config.settings and rm.module.configurator
    # ============================================================================
    @api.model
    def get_values(self):
        """Read values from rm.module.configurator and ir.config_parameter"""
        res = super(ResConfigSettings, self).get_values()
        Config = self.env['rm.module.configurator']

        # Get values from the custom configurator
        res.update({
            'naid_compliance_enabled': Config.get_config_parameter('naid.compliance.enabled', default=False),
            'naid_audit_retention_days': Config.get_config_parameter('naid.audit.retention_days', default=3650),
        })
        return res

    def set_values(self):
        """Save values to rm.module.configurator"""
        super(ResConfigSettings, self).set_values()
        Config = self.env['rm.module.configurator']

        # Use the new set_config_parameter method for better reusability
        Config.set_config_parameter(
            'naid.compliance.enabled',
            self.naid_compliance_enabled,
            config_type='feature_toggle',
            name='Enable NAID Compliance',
            category='compliance'
        )

        Config.set_config_parameter(
            "naid.audit.retention_days",
            self.naid_audit_retention_days,
            config_type="parameter",
            name="NAID Audit Retention (Days)",
            category="compliance",
        )
