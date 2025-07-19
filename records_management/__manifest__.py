# -*- coding: utf-8 -*-
{
    'name': 'Records Management',
            'version': '18.0.2.49.16',  # FIX: Fix view inheritance structure for billing period enhanced view
    'category': 'Document Management',
    'summary': 'Manage physical document boxes, records, shredding, recycling, and visitor-POS integration for walk-ins',
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
- Customer portal with certificates, PO updates, self-quotes, and visit history
- POS integration for walk-in services
- Frontdesk visitor check-in linked to POS for auditing (e.g., NAID compliance) and walk-in shred transactions
- Wizard for easy POS linking from visitors
- Secure certificate downloads via portal controller
- Modern UI with tractor trailer loading visualization
- NAID AAA best practices: Audit trails, signatures, chain-of-custody (2025: verifiable destruction with particle size/crushing logs)
- ISO 27001:2022: Data integrity/encryption (A.8.24 for attachments; transition by Oct 31, 2025)
- Innovative: PuLP optimization for fees/loads, AI sentiment on feedback (extend with torch for OCR tagging)
- Resources: odoo.com/documentation/18.0/developer/howtos.html, suncityshred.com, oneilsoftware.com
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
        'sale',  # For quotes/self-quotes
        'website',  # For website forms/quoting
        'point_of_sale',  # For walk-in services
        'frontdesk',  # For visitor check-in integration
        'sms',  # For POS SMS receipts/notifications
        'industry_fsm',  # For field service management (shredding/pickups)
        'sign',  # For electronic signatures (NAID compliance)
        'hr',  # For employee training/access
        'barcodes',  # For temp inventory/barcode handling
        'web_tour',  # For portal app tours
        'survey',  # For customer feedback forms/suggestions
    ],
    'external_dependencies': {
        'python': [
            'qrcode',
            'Pillow',
            'cryptography',
            # 'pulp',  # Commented out for development - uncomment when ready for production
        ],
    },
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
        'data/naid_compliance_data.xml',  # New: NAID data for audits/signatures
        'data/feedback_survey_data.xml',  # New: Default feedback survey
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
        'views/frontdesk_visitor_views.xml',
        'views/visitor_pos_wizard_views.xml',
        'views/portal_request_views.xml',  # New: Views for portal requests
        'views/fsm_task_views.xml',  # New: FSM task views
        'views/hr_employee_views.xml',  # New: HR views for training
        'views/portal_feedback_views.xml',  # New: Feedback views
        'report/records_reports.xml',
        'report/destruction_certificate_report.xml',
        'report/bale_label_report.xml',
        'report/portal_audit_report.xml',  # New: Audit reports for NAID
        'views/records_management_menus.xml',
        'templates/my_portal_inventory.xml',
        'templates/portal_quote_template.xml',  # New: Quote generation
        'templates/portal_billing_template.xml',  # New: Billing updates
        'templates/portal_inventory_template.xml',  # New: Inventory views
        'templates/portal_overview.xml',  # New: Portal overview/tour
        'templates/portal_feedback_template.xml',  # New: Feedback form
        'templates/portal_centralized_docs.xml',  # New: Centralized docs dashboard
    ],
    'demo': [
        'demo/odoo.xml',
    ],
    'qweb': [],
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
            'records_management/static/src/js/portal_inventory_highlights.js',  # New: JS for inventory highlights
            'records_management/static/src/js/naid_compliance_widget.js',  # New: Compliance widgets
        ],
        'web.assets_frontend': [
            'records_management/static/src/css/portal_tour.css',  # New: CSS for tours
            'records_management/static/src/js/portal_quote_generator.js',  # New: Quote JS
            'records_management/static/src/js/portal_user_import.js',  # New: User imports
            'records_management/static/src/js/portal_signature.js',  # New: Signature JS
            'records_management/static/src/js/portal_inventory_search.js',  # New: Search/filters
            'records_management/static/src/js/portal_tour.js',  # New: Tour JS
            'records_management/static/src/js/portal_feedback.js',  # New: Feedback submission
            'records_management/static/src/js/portal_docs.js',  # New: Docs dashboard JS
        ],
    },
}