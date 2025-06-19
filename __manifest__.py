{
    'name': 'Records Management',
    'version': '1.0',
    'summary': 'Manage records efficiently within Odoo.',
    'description': """
Records Management
==================
A comprehensive module for managing records, integrating with stock and web modules.
Features include custom models, views, demo data, and scheduled actions.
""",
    'author': 'Your Name or Company',
    'website': 'https://yourwebsite.com',
    'category': 'Tools',
    'license': 'LGPL-3',
    'icon': 'records_management/static/description/records_management_icon.png',
    'depends': ['stock', 'web'],
    'data': [
        'views/inventory_template.xml',
        'views/pickup_request.xml',
        'views/my_portal_inventory.xml',
        'views/shredding_views.xml',
        'security/groups.xml',
        'security/ir.model.access.csv',
        'data/products.xml',
        'data/scheduled_actions.xml',
    ],
    'installable': True,
    'application': True,
} # type: ignore