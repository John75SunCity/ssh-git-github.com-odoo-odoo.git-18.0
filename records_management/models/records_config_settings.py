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

    def _compute_records_kpis(self):
        """Compute lightweight KPI values for display in the settings dashboard.
        These are transient values – no store=True to keep computation cheap and current.
        Safe fallbacks are used if underlying models are unavailable during early init.
        """
        Container = self.env.get('records.container')
        Document = self.env.get('records.document')
        PortalRequest = self.env.get('portal.request')  # destruction requests flow through this model

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
