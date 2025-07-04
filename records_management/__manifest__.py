{
    'name': 'Records Management',
    'version': '18.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Manage physical document boxes and records',
    'description': """
Records Management System
========================
Advanced system for managing physical document boxes and their contents:
- Track box locations and contents
- Manage document retention policies
- Link documents to partners and other Odoo records
- Generate reports on document status
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'depends': [
        'base',
        'product',
        'stock',
        'mail',
        'web',
        'sale',  # Added for scheduled actions that create sale orders
    ],
    'data': [
        'security/records_management_security.xml',
        'data/tag_data.xml',
        'security/ir.model.access.csv',
        'data/dependencies_check.xml',
        'data/products.xml',
        'data/storage_fee.xml',
        'data/sequence.xml',
        'data/scheduled_actions.xml',
        'views/records_tag_views.xml',
        'views/records_box_views.xml',
        'views/records_document_views.xml',
        'views/records_location_views.xml',
        'views/records_document_type_views.xml',
        'views/records_retention_policy_views.xml',
        'views/res_partner_views.xml',
        'views/records_management_menus.xml',
        'reports/records_reports.xml',
    ],
    'demo': [
        'demo/odoo.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/scss/records_management.scss',
            'records_management/static/src/js/map_widget.js',
            'records_management/static/src/xml/map_widget.xml',
        ],
    },
}