{
    'name': 'Records Management',
    'version': '18.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Manage boxes and records',
    'description': """
Records Management
=================
This module allows managing boxes and records for document archiving.
    """,
    'author': 'John75SunCity',
    'depends': ['base', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/records_management_views.xml',
        'data/products.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}