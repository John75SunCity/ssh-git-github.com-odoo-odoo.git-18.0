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
        'contacts'
    ],
    'data': [
        'security/groups.xml', 
        'security/ir.model.access.csv',
        'security/security.xml',
        'views/customer_invetory_views.xml',
        'views/pickup_request_views.xml',
        'views/shredding_service_views.xml',
        'views/inventory_template.xml',
        'data/ir_sequence_data.xml',
        'data/mail_template_data.xml',
        'data/product_data.xml',
        'data/dependencies_check.xml',
        'sales_management',
    ],
    'demo': [
        'demo/odoo.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
}
