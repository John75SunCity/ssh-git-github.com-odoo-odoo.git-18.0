{
    'name': 'Records Management',
    'version': '18.0.2.0.0',  # Bumped for comprehensive improvements
    'category': 'Industry',
    'summary': 'Enterprise DMS for Shredding, Destruction, and Recycling',
    'description': """
Enterprise Records Management System
==================================
Track document shredding, HDD/uniform destruction, POS walk-ins, paper baling, loads, invoices, and sales.

🏭 **Industry Features:**
• Physical document box tracking with QR codes
• HDD, uniform, and document destruction services  
• Paper baling with weight tracking and trailer visualization
• Auto-invoicing with market rate integration
• POS integration for walk-in shredding services

📊 **Modern UI & Analytics:**
• Interactive truck loading progress (OWL-powered SVG)
• Real-time dashboards and pivot reports
• QR code chain-of-custody tracking
• Customer portal with self-service quotes

🔒 **Compliance & Security:**
• ISO 15489-1:2016 records management standards
• NAID AAA shredding compliance
• GDPR/CCPA data protection features
• Complete audit trails and destruction certificates

⚡ **Advanced Integrations:**
• Stock/Inventory management
• Account/Invoicing automation  
• Sales quote generation
• Fleet/Vehicle tracking
• HR technician signatures
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'depends': [
        # Essential Core (always installed)
        'base',
        'product', 
        'stock',
        'mail',
        'web',
        'portal',
        
        # Business Critical (per review recommendations)
        'account',         # For auto-invoicing and financial integration
        'sale',           # For quotes and sales orders
        'hr',             # For technician signatures & NAID employee screening
        
        # NAID AAA Compliance Requirements
        'barcodes',       # For chain of custody scanning
        
        # Modern Features (uncomment as needed)
        'website',        # For customer portal and self-quotes  
        'point_of_sale',  # For walk-in services
        # 'fleet',        # For vehicle tracking
        # 'iot',          # For scale integration & facility security
        # 'quality',      # For quality control
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
        'data/naid_compliance_data.xml',  # New: NAID compliance sequences and policies
        'security/naid_security.xml',  # New: NAID compliance security groups
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
        'views/naid_compliance_views.xml',  # New: NAID AAA compliance views
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
