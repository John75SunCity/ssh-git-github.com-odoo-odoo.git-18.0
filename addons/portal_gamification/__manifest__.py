{
    'name': 'Portal Gamification',
    'version': '1.0',
    'summary': 'Gamify your portal experience',
    'description': 'This module adds gamification features to the portal.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Portal',
    'depends': ['portal', 'gamification'],
    'data': [
        'views/portal_gamification_view.xml',
    ],
    'installable': True,
    'application': False,
}