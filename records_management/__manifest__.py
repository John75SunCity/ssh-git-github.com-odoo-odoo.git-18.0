# -*- coding: utf-8 -*-
{
                'name': 'Records Management',
                'version': '18.0.6.0.0',   # Updated version for Odoo 18.0 compatibility fixes
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
        # Core Odoo Dependencies (Required)
        'base',
        'mail',
        'web',
        'portal',
        
        # Product and Inventory Management
        'product',
        'stock',
        'barcodes',
        
        # Accounting and Sales
        'account',  # For invoicing/billing
        'sale',     # For quotes/self-quotes
        
        # Website and E-commerce
        'website',  # For website forms/quoting
        
        # Point of Sale
        'point_of_sale',  # For walk-in services
        
        # Communication
        'sms',  # For SMS notifications
        
        # Electronic Signatures (if available)
        'sign',  # For electronic signatures (NAID compliance)
        
        # Human Resources
        'hr',  # For employee training/access
        
        # Project Management
        'project',  # For project tasks
        'calendar',  # For meeting/event scheduling
        
        # Survey and Feedback
        'survey',  # For customer feedback forms/suggestions
        
        # Additional modules (commented out if not available in Odoo 18.0)
        # 'frontdesk',  # For visitor check-in integration - may not exist in 18.0
        # 'industry_fsm',  # For field service management - may not exist in 18.0
        # 'web_tour',  # For portal app tours - may not exist in 18.0
    ],
    'external_dependencies': {
        'python': [
            'qrcode',      # For QR code generation
            'Pillow',      # For image processing
            'cryptography', # For encryption and security
            'requests',    # For monitoring webhook notifications
            # 'pulp',      # For optimization - uncomment when ready for production
            # 'torch',     # For AI features - optional dependency
        ],
        # Binary dependencies (if any)
        # 'bin': [
        #     'wkhtmltopdf',  # For PDF generation - usually pre-installed
        # ],
    },
    'data': [
        'data/model_records.xml',  # Model records for security rules
        'security/records_management_security.xml',
        'security/ir.model.access.csv',
        'security/new_models_access.xml',
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
        'data/document_retrieval_rates.xml',  # New: Default retrieval rates
        'data/advanced_billing_demo.xml',  # New: Advanced billing demo data
        # Load base menu structure first (parent menus only, no actions)
        'views/records_management_base_menus.xml',
        # Load all action-containing view files
        'views/records_box_views.xml',
        'views/records_tag_views.xml',
        'views/records_location_views.xml',
        'views/records_document_type_views.xml',
        'views/records_document_views.xml',
        'views/pickup_request.xml',
        'views/shredding_views.xml',
        'views/stock_lot_views.xml',
        'views/customer_inventory_views.xml',
        'report/records_reports.xml',  # Contains report actions
        # Load menu items with actions after actions are defined
        'views/records_management_menus.xml',
        'views/records_retention_policy_views.xml',
        # Additional views that depend on base menus
        'views/hard_drive_scan_views.xml',  # New: Hard drive scanning views
        'views/res_partner_views.xml',
        'views/billing_views.xml',
        'views/departmental_billing_views.xml',
        'views/barcode_views.xml',
        'views/paper_bale_views.xml',
        'views/paper_bale_recycling_views.xml',  # New: Paper recycling bale views
        'views/paper_load_shipment_views.xml',  # New: Load shipment views
        'views/pos_config_views.xml',
        'views/visitor_pos_wizard_views.xml',
        'views/portal_request_views.xml',  # New: Views for portal requests
        'views/fsm_task_views.xml',  # New: FSM task views
        'views/portal_feedback_views.xml',  # New: Feedback views
        'views/box_type_converter_views.xml',  # New: Box type conversion wizard
        'views/permanent_flag_wizard_views.xml',  # New: Permanent flag security wizard
        'views/document_retrieval_work_order_views.xml',  # New: Document retrieval work orders
        'views/document_retrieval_rates_views.xml',  # New: Document retrieval rates
        'views/shredding_rates_views.xml',  # New: Shredding rates views
        'views/shredding_inventory_views.xml',  # New: Shredding inventory views
        'views/advanced_billing_views.xml',  # New: Advanced billing views
        'views/bin_key_management_views.xml',  # New: Bin key management views
        'views/partner_bin_key_views.xml',  # New: Partner bin key views
        'views/mobile_bin_key_wizard_views.xml',  # New: Mobile bin key wizard views
        'report/destruction_certificate_report.xml',
        'report/bale_label_report.xml',
        'report/portal_audit_report.xml',  # New: Audit reports for NAID
        'views/departmental_billing_menus.xml',  # Loaded after main menus for proper dependencies
        'views/barcode_menus.xml',  # Loaded after main menus for proper dependencies
        'views/portal_request_menus.xml',  # Loaded after main menus for proper dependencies
        'views/portal_feedback_menus.xml',  # Loaded after main menus for proper dependencies
        'views/paper_recycling_menus.xml',  # New: Paper recycling menus
        'views/document_retrieval_menus.xml',  # New: Document retrieval menus
        'templates/my_portal_inventory.xml',
        'templates/portal_quote_template.xml',  # New: Quote generation
        'templates/portal_billing_template.xml',  # New: Billing updates
        'templates/portal_inventory_template.xml',  # New: Inventory views
        'templates/portal_overview.xml',  # New: Portal overview/tour
        'templates/portal_feedback_template.xml',  # New: Feedback form
        'templates/portal_centralized_docs.xml',  # New: Centralized docs dashboard
        'templates/portal_document_retrieval.xml',  # New: Document retrieval portal
    ],
    'demo': [
        'demo/odoo.xml',
    ],
    'qweb': [],
    'application': True,
    'installable': True,
    'auto_install': False,
    'sequence': 1000,  # Load after all dependencies are loaded
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',  # For any setup that needs to run after other modules
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/scss/records_management.scss',
            'records_management/static/src/js/map_widget.js',
            'records_management/static/src/xml/map_widget.xml',
            'records_management/static/src/js/trailer_visualization.js',
            'records_management/static/src/xml/trailer_visualization.xml',
            'records_management/static/src/js/truck_widget.js',  # Original truck widget
            'records_management/static/src/js/paper_load_truck_widget.js',  # New: Enhanced paper load truck widget
            'records_management/static/src/js/paper_load_progress_field.js',  # New: Field widget for paper loads
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