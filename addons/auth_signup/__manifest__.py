{
    'name': 'Auth Signup',
    'version': '1.0',
    'summary': 'User signup and authentication',
    'description': 'This module allows users to sign up and authenticate on the platform.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Authentication',
    'depends': ['base'],
    'data': [
        'views/auth_signup_view.xml',
    ],
    'installable': True,
    'application': False,
}