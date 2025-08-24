# -*- coding: utf-8 -*-
{
    'name': 'Records Management FSM Integration',
    'version': '18.0.1.0.0',
    'category': 'Field Service',
    'summary': 'Field Service Management Integration for Records Management',
    'description': """
Records Management FSM Integration
=================================

This module provides Field Service Management integration for the Records Management System including:
- FSM task management for records services
- Route optimization for pickups and deliveries
- Technician assignment and scheduling
- Mobile task completion workflows
- Customer notification management

Key Features:
- FSM task extensions for records services
- Route management and optimization
- Task scheduling and assignment
- Mobile-friendly interfaces
- Automated notifications
- Service completion tracking
    """,
    'author': 'Records Management System',
    'website': '',
    'depends': [
        'base',
        'mail',
        'industry_fsm',
        'records_management',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}