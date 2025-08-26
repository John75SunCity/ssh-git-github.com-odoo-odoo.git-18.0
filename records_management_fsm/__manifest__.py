{
    'name': 'Records Management FSM Integration',
    'version': '18.0.1.0.1',
    'category': 'Records Management',
    'summary': 'FSM integration for Records Management',
    'author': 'Your Name',
    'license': 'LGPL-3',
    'depends': ['records_management', 'industry_fsm', 'project'],
    'data': [
        'security/ir.model.access.csv',
        # Add your views, data files here
    ],
    'installable': True,
    'auto_install': False,
}
