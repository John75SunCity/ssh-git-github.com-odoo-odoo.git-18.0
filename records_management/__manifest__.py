{
    'name': 'Records Management',
    'version': '18.0.2.0.0',  # Bumped version for improvements
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
        'account',  # Added for invoicing
        'sale',  # Added for quotes
        'website',  # Added for potential quoting via website
        'point_of_sale',  # Added for walk-in services
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
        'data/paper_products.xml',  # New: Products for bales, trailers
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
        'views/paper_bale_views.xml',  # New: Bale management views
        'views/trailer_load_views.xml',  # New: Trailer load views with visualization
        'views/pos_config_views.xml',  # New: POS integration views
        'report/records_reports.xml',
        'report/destruction_certificate_report.xml',  # New: Certificate report
        'report/bale_label_report.xml',  # New: Bale label report
        'views/records_management_menus.xml',
        'templates/my_portal_inventory.xml',  # Enhanced with new features
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
            'records_management/static/src/js/trailer_visualization.js',  # New: JS for tractor trailer visualization
            'records_management/static/src/xml/trailer_visualization.xml',  # New: QWeb for visualization
        ],
        'web.assets_frontend': [  # Added for portal enhancements
            'records_management/static/src/js/portal_quote_generator.js',
        ],
    },
}
