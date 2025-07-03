{
    'name': 'Records Management',
    'version': '18.0.1.0.0',
    'category': 'Industries',
    'summary': 'Manages document boxes, storage, and retrieval processes',
    'author': 'Odoo Inc.',
    'website': 'https://www.odoo.com',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'stock',
        'mail',
        'portal',
        'board',
        'product',
        'contacts',
        'sale_management',
        'fleet'
    ],
    'data': [
        'security/groups.xml',
        'security/ir_rule.xml',
        'security/ir.model.access.csv',
        'security/security.xml',
        'data/ir_sequence_data.xml',  # Keep only one sequence file
        'data/products.xml',
        'data/dependencies_check.xml',
        'data/scheduled_actions.xml',
        'views/pickup_request.xml',
        'views/shredding_views.xml',
        'views/stock_lot_views.xml',
        'views/customer_inventory_views.xml',
        'report/customer_inventory_report.xml',
        'templates/my_portal_inventory.xml',
    ],
    'demo': [
        'demo/odoo.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
