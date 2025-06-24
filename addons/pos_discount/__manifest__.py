{
    'name': 'Point of Sale Discount',
    'version': '1.0',
    'summary': 'Manage discounts in the Point of Sale',
    'description': 'This module allows you to manage discounts directly in the Point of Sale interface.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Sales/Point of Sale',
    'depends': ['point_of_sale'],
    'data': [
        'views/pos_discount_view.xml',
    ],
    'installable': True,
    'application': False,
}