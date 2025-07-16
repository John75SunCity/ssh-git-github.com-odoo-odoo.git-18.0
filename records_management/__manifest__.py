{
    'name': 'Records Management',
    'version': '18.0.3.0.0',  # Bumped for optimizations and additions
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
        'account',  # For invoicing
        'sale',  # For quotes
        'website',  # For quoting via website
        'point_of_sale',  # For walk-in services
        'hr',  # Added: For technician signatures in baling/shredding
        'report_xlsx',  # Added: For exportable reports/dashboards (e.g., load weights)
        #'iot',  # Optional: For scale weighing integration in baling
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
        'data/paper_products.xml',  # Optimized: Add bale/paper types as products
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
        'views/paper_bale_views.xml',  # Optimized: Add OWL for modern bale list
        'views/trailer_load_views.xml',  # Optimized: OWL truck visualization
        'views/pos_config_views.xml',  # Optimized: POS for walk-in shredding
        'report/records_reports.xml',
        'report/destruction_certificate_report.xml',  # Optimized: Add QR for chain-of-custody
        'report/bale_label_report.xml',  # Optimized: Include tech signature/date
        'views/records_management_menus.xml',
        'templates/my_portal_inventory.xml',  # Optimized: Add self-quotes/cert downloads
    ],
    'demo': [
        'demo/odoo.xml',
    ],
    'qweb': [
        'static/src/xml/trailer_visualization.xml',  # Added for OWL QWeb
        'static/src/xml/map_widget.xml',  # Kept/optimized if for location tracking
    ],
    'external_dependencies': {
        'python': ['qrcode'],  # Added: For QR in labels/certs (pip in Dockerfile if needed)
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
            'records_management/static/src/js/trailer_visualization.js',  # Optimized: JS for interactive truck
            'records_management/static/src/js/truck_widget.js',  # New: OWL truck progress widget
        ],
        'web.assets_frontend': [  # For portal
            'records_management/static/src/js/portal_quote_generator.js',
        ],
    },
}
