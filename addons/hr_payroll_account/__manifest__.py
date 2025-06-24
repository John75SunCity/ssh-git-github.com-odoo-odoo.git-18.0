{
    'name': 'HR Payroll Account',
    'version': '1.0',
    'summary': 'Integrate payroll with accounting',
    'description': 'This module integrates payroll management with the accounting system.',
    'author': 'Odoo S.A.',
    'website': 'https://www.odoo.com',
    'category': 'Human Resources',
    'depends': ['hr_payroll', 'account'],
    'data': [
        'views/hr_payroll_account_view.xml',
    ],
    'installable': True,
    'application': False,
}