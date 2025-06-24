{
    'name': 'Account Payment',
    'version': '1.0',
    'summary': 'Manage payments in accounting',
    'description': 'This module provides features to manage payments in the accounting system.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Accounting',
    'depends': ['account'],
    'data': [
        'views/account_payment_view.xml',
    ],
    'installable': True,
    'application': False,
}