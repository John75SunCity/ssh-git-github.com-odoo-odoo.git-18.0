# -*- coding: utf-8 -*-
{
    'name': 'Records Management - Minimal Version',
    'version': '18.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Minimal Records Management System',
    'description': """
        Minimal Records Management System - Testing Version
        This is a stripped-down version to get basic loading working.
    """,
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'web'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/menu_views.xml',
    ],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
    'sequence': 100,
}
