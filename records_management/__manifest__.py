{
    'name': 'Records Management',
    'version': '18.0.6.1.0',  # Updated for fixes/enhancements
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
        'base', 'product', 'stock', 'mail', 'web', 'portal', 'base_setup', 'fleet',
        'account', 'sale', 'website', 'point_of_sale', 'industry_fsm', 'sign',
        'sms', 'hr', 'barcodes', 'web_tour', 'survey',
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
        'data/portal_mail_templates.xml',
        'data/naid_compliance_data.xml',
        'data/feedback_survey_data.xml',
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
        'views/portal_request_views.xml',
        'views/fsm_task_views.xml',
        'views/hr_employee_views.xml',
        'views/portal_feedback_views.xml',
        'report/records_reports.xml',
        'report/destruction_certificate_report.xml',
        'report/bale_label_report.xml',
        'report/portal_audit_report.xml',
        'views/records_management_menus.xml',
        'templates/my_portal_inventory.xml',
        'templates/portal_quote_template.xml',
        'templates/portal_billing_template.xml',
        'templates/portal_inventory_template.xml',
        'templates/portal_overview.xml',
        'templates/portal_feedback_template.xml',
        'templates/portal_centralized_docs.xml',
    ],
    'demo': ['demo/odoo.xml'],
    'qweb': [],
    'external_dependencies': {'python': ['pulp']},  # For optimization
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
            'records_management/static/src/js/portal_inventory_highlights.js',
            'records_management/static/src/js/naid_compliance_widget.js',
        ],
        'web.assets_frontend': [
            'records_management/static/src/css/portal_tour.css',
            'records_management/static/src/js/portal_quote_generator.js',
            'records_management/static/src/js/portal_user_import.js',
            'records_management/static/src/js/portal_signature.js',
            'records_management/static/src/js/portal_inventory_search.js',
            'records_management/static/src/js/portal_tour.js',
            'records_management/static/src/js/portal_feedback.js',
            'records_management/static/src/js/portal_docs.js',
        ],
    },
}