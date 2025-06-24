{
    'name': 'Website Project',
    'version': '1.0',
    'summary': 'Integrate projects with your website',
    'description': 'This module integrates project management features with your website.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Website/Website',
    'depends': ['website', 'project'],
    'data': [
        'views/website_project_view.xml',
    ],
    'installable': True,
    'application': False,
}