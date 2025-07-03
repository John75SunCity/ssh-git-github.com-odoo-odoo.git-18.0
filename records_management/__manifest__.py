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
    ],
    'data': [
        'security/records_management_security.xml',
        'security/ir.model.access.csv',
        'data/products.xml',
        'data/sequence.xml',
        'views/records_box_views.xml',
        'views/records_document_views.xml',
        'views/records_location_views.xml',
        'views/res_partner_views.xml',
        'views/records_management_menus.xml',
        'reports/records_reports.xml',
    ],
    'demo': [
        'data/demo_data.xml',
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
    'assets': {
        'web.assets_backend': [
            'records_management/static/src/scss/records_management.scss',
        ],
    },
}