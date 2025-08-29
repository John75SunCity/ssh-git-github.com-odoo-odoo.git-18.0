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
