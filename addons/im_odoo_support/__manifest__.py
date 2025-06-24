{
    'name': 'IM Odoo Support',
    'version': '1.0',
    'summary': 'Instant messaging support for Odoo',
    'description': 'This module provides instant messaging support for Odoo users.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Communication',
    'depends': ['mail'],
    'data': [
        'views/im_odoo_support_view.xml',
    ],
    'installable': True,
    'application': False,
}