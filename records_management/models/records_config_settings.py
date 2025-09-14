from odoo import models, fields

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ============================================================================
    # General Settings
    # ============================================================================
    module_records_management = fields.Boolean(string="Activate Records Management Features")

    # ============================================================================
    # Barcode & Container Settings
    # ============================================================================
    records_auto_barcode_generation = fields.Boolean(
        string="Auto-generate Barcodes",
        config_parameter='records_management.auto_barcode_generation',
        help="Automatically generate a unique barcode when a new container is created."
    )
    records_barcode_nomenclature_id = fields.Many2one(
        'barcode.nomenclature',
        string="Barcode Nomenclature",
        config_parameter='records_management.barcode_nomenclature_id',
        help="The barcode format to use for generation."
    )
    records_default_container_type_id = fields.Many2one(
        'product.container.type',
        string="Default Container Type",
        config_parameter='records_management.default_container_type_id',
        help="Default container type for new records."
    )

    # ============================================================================
    # NAID Compliance Settings
    # ============================================================================
    naid_auto_audit_logging = fields.Boolean(
        string="Enable NAID Audit Logging",
        config_parameter='records_management.naid_auto_audit_logging',
        help="Automatically log all critical events for NAID compliance."
    )
    naid_require_dual_authorization = fields.Boolean(
        string="Require Dual Authorization for Destruction",
        config_parameter='records_management.naid_require_dual_authorization',
        help="Requires a second user to approve destruction orders."
    )
    naid_certificate_template_id = fields.Many2one(
        'mail.template',
        string="Destruction Certificate Template",
        config_parameter='records_management.naid_certificate_template_id',
        domain="[('model', '=', 'project.task')]"
    )

    # ============================================================================
    # Billing Settings
    # ============================================================================
    billing_auto_invoice_generation = fields.Boolean(
        string="Automate Recurring Invoicing",
        config_parameter='records_management.billing_auto_invoice_generation',
        help="Enable the scheduled action to automatically generate monthly storage invoices."
    )
    billing_prorate_first_month = fields.Boolean(
        string="Prorate First Month's Billing",
        config_parameter='records_management.billing_prorate_first_month',
        help="Calculate the first invoice based on the number of days remaining in the month."
    )

    # ============================================================================
    # Customer Portal Settings
    # ============================================================================
    portal_allow_customer_requests = fields.Boolean(
        string="Allow Portal Service Requests",
        config_parameter='records_management.portal_allow_customer_requests',
        help="Allow customers to submit pickup, retrieval, and destruction requests via the portal."
    )
    portal_require_request_approval = fields.Boolean(
        string="Require Approval for Portal Requests",
        config_parameter='records_management.portal_require_request_approval',
        help="All customer requests must be approved by a manager before being processed."
    )
    portal_ai_sentiment_analysis = fields.Boolean(
        string="Enable AI Sentiment Analysis for Feedback",
        config_parameter='records_management.portal_ai_sentiment_analysis',
        help="Automatically analyze customer feedback for sentiment (positive, negative, neutral)."
    )

    # ============================================================================
    # FSM Integration
    # ============================================================================
    fsm_integration_enabled = fields.Boolean(
        string="Enable Field Service (FSM) Integration",
        config_parameter='records_management.fsm_integration_enabled',
        help="Automatically create FSM tasks for pickup and destruction requests."
    )

    # =========================================================================
    # Advanced Records Features (Previously Referenced – Now Defined)
    # =========================================================================
    records_enable_advanced_search = fields.Boolean(
        string="Enable Advanced Search",
        config_parameter='records_management.enable_advanced_search',
        help="Enable advanced multi-criteria search features in the records portal/backend."
    )
    records_auto_location_assignment = fields.Boolean(
        string="Auto-Assign Storage Location",
        config_parameter='records_management.auto_location_assignment',
        help="Automatically assign an optimal storage location for newly created containers."
    )
    records_enable_container_weight_tracking = fields.Boolean(
        string="Track Container Weights",
        config_parameter='records_management.enable_container_weight_tracking',
        help="Enable weight capture and monitoring for containers (useful for capacity analytics)."
    )
    records_default_retention_days = fields.Integer(
        string="Default Retention (Days)",
        config_parameter='records_management.default_retention_days',
        help="Default retention period applied when a document type has no specific rule configured."
    )
    records_container_capacity_warning_threshold = fields.Integer(
        string="Capacity Warning Threshold (%)",
        config_parameter='records_management.container_capacity_warning_threshold',
        help="Trigger warning indicators when average container utilization exceeds this percentage.",
        default=85
    )

    # =========================================================================
    # Pickup & Logistics Settings
    # =========================================================================
    pickup_auto_route_optimization = fields.Boolean(
        string="Auto Route Optimization",
        config_parameter='records_management.pickup_auto_route_optimization',
        help="Automatically optimize pickup and delivery routes for approved requests."
    )

    # =========================================================================
    # Billing Enhancements
    # =========================================================================
    billing_period_type = fields.Selection(
        selection=[('monthly', 'Monthly'), ('quarterly', 'Quarterly'), ('annually', 'Annually')],
        string="Billing Period Type",
        config_parameter='records_management.billing_period_type',
        help="Defines the aggregation period used for recurring billing cycles.",
        default='monthly'
    )

    # =========================================================================
    # Analytics & Intelligence Settings
    # =========================================================================
    analytics_predictive_analytics_enabled = fields.Boolean(
        string="Enable Predictive Analytics",
        config_parameter='records_management.analytics_predictive_analytics_enabled',
        help="Enable predictive modeling for volume trends, destruction forecasting, and workload planning."
    )

    # =========================================================================
    # Accounting / External Integration Settings
    # =========================================================================
    integration_accounting_auto_sync = fields.Boolean(
        string="Auto-Sync Accounting",
        config_parameter='records_management.integration_accounting_auto_sync',
        help="Automatically synchronize billing data with the connected accounting system."
    )

    # =========================================================================
    # Additional NAID Compliance Settings
    # =========================================================================
    naid_audit_retention_years = fields.Integer(
        string="NAID Audit Retention (Years)",
        config_parameter='records_management.naid_audit_retention_years',
        help="Number of years to retain NAID audit logs.",
        default=5
    )
    naid_compliance_level = fields.Selection(
        selection_add=[('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')],
        string="NAID Compliance Level",
        config_parameter='records_management.naid_compliance_level',
        help="Target NAID compliance certification level.",
        default='aaa'
    )

    # =========================================================================
    # Enhanced Billing Settings
    # =========================================================================
    billing_volume_discount_enabled = fields.Boolean(
        string="Enable Volume Discounts",
        config_parameter='records_management.billing_volume_discount_enabled',
        help="Apply volume-based discounts for large customers."
    )
    billing_default_currency_id = fields.Many2one(
        'res.currency',
        string="Default Billing Currency",
        config_parameter='records_management.billing_default_currency_id',
        help="Default currency for billing and invoicing."
    )

    # =========================================================================
    # Pickup & Logistics Enhanced Settings
    # =========================================================================
    pickup_default_time_window_hours = fields.Integer(
        string="Default Pickup Window (Hours)",
        config_parameter='records_management.pickup_default_time_window_hours',
        help="Default time window for pickup appointments.",
        default=4
    )
    pickup_automatic_confirmation = fields.Boolean(
        string="Auto-Confirm Pickup Requests",
        config_parameter='records_management.pickup_automatic_confirmation',
        help="Automatically confirm pickup requests without manual approval."
    )
    pickup_advance_notice_days = fields.Integer(
        string="Pickup Advance Notice (Days)",
        config_parameter='records_management.pickup_advance_notice_days',
        help="Minimum days notice required for pickup requests.",
        default=1
    )

    # =========================================================================
    # Portal Enhanced Settings
    # =========================================================================
    portal_auto_notification_enabled = fields.Boolean(
        string="Auto Portal Notifications",
        config_parameter='records_management.portal_auto_notification_enabled',
        help="Automatically notify customers of status changes via portal."
    )
    portal_enable_document_preview = fields.Boolean(
        string="Enable Document Preview",
        config_parameter='records_management.portal_enable_document_preview',
        help="Allow customers to preview documents in the portal."
    )
    portal_feedback_collection_enabled = fields.Boolean(
        string="Enable Feedback Collection",
        config_parameter='records_management.portal_feedback_collection_enabled',
        help="Enable customer feedback collection in portal."
    )

    # =========================================================================
    # Notification Settings
    # =========================================================================
    notification_email_enabled = fields.Boolean(
        string="Enable Email Notifications",
        config_parameter='records_management.notification_email_enabled',
        help="Send email notifications for important events.",
        default=True
    )
    notification_sms_enabled = fields.Boolean(
        string="Enable SMS Notifications",
        config_parameter='records_management.notification_sms_enabled',
        help="Send SMS notifications for urgent events."
    )
    notification_pickup_reminder_hours = fields.Integer(
        string="Pickup Reminder (Hours Before)",
        config_parameter='records_management.notification_pickup_reminder_hours',
        help="Send pickup reminders this many hours before scheduled pickup.",
        default=24
    )
    notification_retention_expiry_days = fields.Integer(
        string="Retention Expiry Notice (Days Before)",
        config_parameter='records_management.notification_retention_expiry_days',
        help="Send retention expiry notices this many days before expiration.",
        default=30
    )

    # =========================================================================
    # Security Settings
    # =========================================================================
    security_department_isolation = fields.Boolean(
        string="Enable Department Data Isolation",
        config_parameter='records_management.security_department_isolation',
        help="Restrict data access based on department assignments."
    )
    security_require_bin_key_management = fields.Boolean(
        string="Require Bin Key Management",
        config_parameter='records_management.security_require_bin_key_management',
        help="Require bin keys for accessing physical storage."
    )
    security_failed_access_lockout_enabled = fields.Boolean(
        string="Enable Failed Access Lockout",
        config_parameter='records_management.security_failed_access_lockout_enabled',
        help="Lock accounts after repeated failed access attempts."
    )
    security_failed_access_attempt_limit = fields.Integer(
        string="Failed Access Attempt Limit",
        config_parameter='records_management.security_failed_access_attempt_limit',
        help="Number of failed attempts before account lockout.",
        default=5
    )

    # =========================================================================
    # Integration Settings
    # =========================================================================
    integration_api_access_enabled = fields.Boolean(
        string="Enable API Access",
        config_parameter='records_management.integration_api_access_enabled',
        help="Enable external API access for integrations."
    )
    integration_document_management_system = fields.Char(
        string="External DMS Integration",
        config_parameter='records_management.integration_document_management_system',
        help="Connected external document management system."
    )
    integration_webhook_notifications = fields.Boolean(
        string="Enable Webhook Notifications",
        config_parameter='records_management.integration_webhook_notifications',
        help="Send webhook notifications to external systems."
    )

    # =========================================================================
    # Analytics Settings
    # =========================================================================
    analytics_enable_advanced_reporting = fields.Boolean(
        string="Enable Advanced Reporting",
        config_parameter='records_management.analytics_enable_advanced_reporting',
        help="Enable advanced analytics and reporting features."
    )
    analytics_auto_report_generation = fields.Boolean(
        string="Auto-Generate Reports",
        config_parameter='records_management.analytics_auto_report_generation',
        help="Automatically generate scheduled reports."
    )
    analytics_customer_kpi_tracking = fields.Boolean(
        string="Enable Customer KPI Tracking",
        config_parameter='records_management.analytics_customer_kpi_tracking',
        help="Track and analyze customer-specific KPIs."
    )

    # =========================================================================
    # KPI / Dashboard Metrics (Computed, Non-Stored)
    # =========================================================================
    total_active_containers = fields.Integer(
        string="Active Containers",
        compute='_compute_records_kpis'
    )
    total_stored_documents = fields.Integer(
        string="Stored Documents",
        compute='_compute_records_kpis'
    )
    pending_destruction_requests = fields.Integer(
        string="Pending Destruction Requests",
        compute='_compute_records_kpis'
    )
    compliance_score = fields.Float(
        string="Compliance Score",
        compute='_compute_records_kpis',
        help="Overall NAID compliance score as a percentage."
    )

    def _compute_records_kpis(self):
        """Compute lightweight KPI values for display in the settings dashboard.
        These are transient values – no store=True to keep computation cheap and current.
        Safe fallbacks are used if underlying models are unavailable during early init.
        """
        Container = self.env.get('records.container')
        Document = self.env.get('records.document')
        PortalRequest = self.env.get('portal.request')  # destruction requests flow through this model
        NAIDAuditLog = self.env.get('naid.audit.log')

        # Pre-compute safe domains based on actual existing fields to avoid AttributeErrors during early init
        container_domain = []
        if Container:
            # Apply active flag if present
            if 'active' in Container._fields:
                container_domain.append(('active', '=', True))
            # If state selection exists, exclude final 'destroyed' state to align with KPI label "Active Containers"
            if 'state' in Container._fields and 'destroyed' in dict(Container._fields['state'].selection):
                container_domain.append(('state', '!=', 'destroyed'))

        # Stored documents: target documents physically in storage; fall back to active docs if state not available
        document_domain = []
        if Document:
            if 'active' in Document._fields:
                document_domain.append(('active', '=', True))
            if 'state' in Document._fields:
                state_field = Document._fields['state']
                selection_values = dict(state_field.selection).keys()  # selection keys list-like
                # Prefer counting only true storage states if present
                storage_states = [s for s in ['in_storage', 'archived'] if s in selection_values]
                if storage_states:
                    document_domain.append(('state', 'in', storage_states))

        # Destruction requests: count submitted/approved/in_progress destruction-type requests that are not completed/cancelled/rejected
        destruction_domain = []
        if PortalRequest:
            if 'request_type' in PortalRequest._fields:
                destruction_domain.append(('request_type', '=', 'destruction'))
            if 'state' in PortalRequest._fields:
                # Actual states per model definition
                pending_states = [s for s in ['submitted', 'approved', 'in_progress']]
                # Only include those present in selection to avoid invalid domain values
                selection_values = dict(PortalRequest._fields['state'].selection).keys()
                pending_states = [s for s in pending_states if s in selection_values]
                if pending_states:
                    destruction_domain.append(('state', 'in', pending_states))

        for rec in self:
            try:
                rec.total_active_containers = Container.search_count(container_domain) if Container else 0
            except Exception:
                rec.total_active_containers = 0
            try:
                rec.total_stored_documents = Document.search_count(document_domain) if Document else 0
            except Exception:
                rec.total_stored_documents = 0
            try:
                if PortalRequest and (destruction_domain or PortalRequest):
                    # If we built a domain, use it; else zero (avoid inflating with all request types)
                    rec.pending_destruction_requests = (
                        PortalRequest.search_count(destruction_domain) if destruction_domain else 0
                    )
                else:
                    rec.pending_destruction_requests = 0
            except Exception:
                rec.pending_destruction_requests = 0

            # Calculate compliance score based on NAID audit logs and system configuration
            try:
                if NAIDAuditLog:
                    # Simple compliance calculation based on audit trail completeness
                    total_auditable_events = NAIDAuditLog.search_count([])
                    compliant_events = NAIDAuditLog.search_count([('compliance_status', '=', 'compliant')])
                    if total_auditable_events > 0:
                        rec.compliance_score = (compliant_events / total_auditable_events) * 100
                    else:
                        rec.compliance_score = 95.0  # Default high score for new systems
                else:
                    rec.compliance_score = 95.0  # Default when audit model not available
            except Exception:
                rec.compliance_score = 95.0  # Safe default
