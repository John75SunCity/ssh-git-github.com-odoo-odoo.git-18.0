{
    'name': 'Records Management - FSM',
    'version': '18.0.1.0.0',
    'summary': 'Field Service Management for Records Management',
    'description': """
        This module provides the integration between the Records Management and Field Service Management (FSM) applications.
    """,
    'category': 'Services/Field Service',
    'author': 'John75SunCity',
    'website': 'https://github.com/John75SunCity',
    'license': 'LGPL-3',
    'depends': [
        'records_management',
        'industry_fsm',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/fsm_task_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': True,
}
