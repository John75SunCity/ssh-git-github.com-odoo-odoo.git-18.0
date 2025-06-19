{
    'name': 'Records Management',
    'version': '1.0',
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
}