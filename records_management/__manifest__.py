# Updated file: Added 'survey' dependency for feedback forms (built-in Odoo tool for suggestions/concerns). Included new templates for feedback and centralized views. This enables structured feedback collection (with NAID-compliant logging) and a dashboard for invoices/quotes/certificates/comms, while ensuring granular access via security updates. Enhances portal modernity with clean tabs/cards.

{
    'name': 'Records Management',
    'version': '18.0.6.0.0',  # Comprehensive portal templates with modern UI, multi-select, and enhanced navigation
    'category': 'Document Management',
    'summary': 'Manage physical document boxes, records, shredding, and recycling services',
    'description': """
Records Management System
========================
Advanced system for managing physical document boxes, records, shredding, hard drive destruction, uniform shredding, walk-in services, and paper recycling:

Features:
- Track box locations and contents
- Manage document retention policies
- Link documents to partners and other Odoo records
- Generate reports on document status
- Pickup request management
- Shredding service functionality (documents, hard drives, uniforms)
- Customer inventory tracking
- Paper baling, weighing, and trailer load management
- Auto-invoicing on bale pickup
- Customer portal with certificates, PO updates, and self-quotes
- POS integration for walk-in services
- Modern UI with tractor trailer loading visualization
- Advanced customer portal: Billing updates, self-quotes, inventory management, destruction/service requests with signatures, user imports, temp barcodes for additions, FSM integration
- Compliance: NAID AAA audit trails, timestamps, signatures
- Notifications: Email/SMS for requests
- Customer feedback system with NAID-compliant logging
- Centralized document dashboard for invoices, quotes, certificates, and communications
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'depends': [
        'base',
        'product',
        'stock',
        'mail',
        'web',
        'portal',
        'base_setup',
        'fleet',
        'account',  # For invoicing/billing
        'sale',  # For quotes
        'website',  # For website forms and quoting
        'point_of_sale',  # For walk-ins
        'industry_fsm',  # Added: Field service management for requests
        'sign',  # Added: Electronic signatures for requests/compliance
        'sms',  # Added: SMS notifications
        'hr',  # Added: For user imports and access management
        'barcodes',  # For temp/physical barcode handling
        'web_tour',  # Added: For portal app tours
        'survey',  # Added: For customer feedback forms/suggestions
    ],
    'data': [
        'security/records_management_security.xml',
        'security/ir.model.access.csv',
        'data/ir_sequence_data.xml',
        'data/sequence.xml',
        'data/tag_data.xml',
        'data/products.xml',
        'data/storage_fee.xml',
        'data/scheduled_actions.xml',
        'data/paper_products.xml',
        'data/portal_mail_templates.xml',  # New: Email/SMS templates for notifications
        'data/naid_compliance_data.xml',  # Existing/updated for signatures
        'data/feedback_survey_data.xml',  # New: Default feedback survey form
        'views/records_tag_views.xml',
        'views/records_location_views.xml',
        'views/records_retention_policy_views.xml',
        'views/records_document_type_views.xml',
        'views/records_box_views.xml',
        'views/records_document_views.xml',
        'views/pickup_request.xml',
        'views/shredding_views.xml',
        'views/stock_lot_views.xml',
        'views/res_partner_views.xml',
        'views/customer_inventory_views.xml',
        'views/billing_views.xml',
        'views/departmental_billing_views.xml',
        'views/barcode_views.xml',
        'views/paper_bale_views.xml',
        'views/trailer_load_views.xml',
        'views/pos_config_views.xml',
        'views/portal_request_views.xml',  # New: Views for portal requests (destruction, services)
        'views/fsm_task_views.xml',  # New: FSM integration views
        'views/hr_employee_views.xml',  # Updated for user imports/access
        'views/portal_feedback_views.xml',  # New: Views for feedback management
        'report/records_reports.xml',
        'report/destruction_certificate_report.xml',
        'report/bale_label_report.xml',
        'report/portal_audit_report.xml',  # New: Audit trail reports
        'views/records_management_menus.xml',
        'templates/my_portal_inventory.xml',  # Updated: Enhanced portal templates
        'templates/portal_quote_template.xml',  # New: Quote generation
        'templates/portal_billing_template.xml',  # New: Billing updates
        'templates/portal_inventory_template.xml',  # New: Modern inventory views
        'templates/portal_overview.xml',  # New: Portal overview/tour template
        'templates/portal_feedback_template.xml',  # New: Feedback form
        'templates/portal_centralized_docs.xml',  # New: Centralized views for invoices/quotes/certs/comms
    ],
    'demo': [
        'demo/odoo.xml',
    ],
    'qweb': [],
    'external_dependencies': {
        'python': [],
        'bin': [],
    },
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/scss/records_management.scss',
            'records_management/static/src/js/map_widget.js',
            'records_management/static/src/xml/map_widget.xml',
            'records_management/static/src/js/trailer_visualization.js',
            'records_management/static/src/xml/trailer_visualization.xml',
            'records_management/static/src/js/portal_inventory_highlights.js',  # New: JS for modern inventory UI (highlights, multi-select)
            'records_management/static/src/js/naid_compliance_widget.js',  # Existing
        ],
        'web.assets_frontend': [
            'records_management/static/src/css/portal_tour.css',  # New: CSS for enhanced tour styling
            'records_management/static/src/js/portal_quote_generator.js',  # Existing
            'records_management/static/src/js/portal_user_import.js',  # New: JS for user imports
            'records_management/static/src/js/portal_signature.js',  # New: JS for signatures
            'records_management/static/src/js/portal_inventory_search.js',  # New: JS for advanced search/filters
            'records_management/static/src/js/portal_tour.js',  # New: JS for portal app tour
            'records_management/static/src/js/portal_feedback.js',  # New: JS for feedback submission
            'records_management/static/src/js/portal_docs.js',  # New: JS for centralized document center
        ],
    },
}
