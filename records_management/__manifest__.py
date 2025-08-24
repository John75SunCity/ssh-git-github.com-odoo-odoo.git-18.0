# -*- coding: utf-8 -*-
{
    'name': 'Records Management System',
    'version': '18.0.1.0.0',
    'category': 'Document Management',
    'summary': 'Comprehensive Records Management System with NAID Compliance',
    'description': """
Records Management System
========================

This module provides comprehensive records management functionality including:
- Container and box management
- Document tracking and retention
- NAID AAA compliance features
- Customer portal integration
- Billing and pricing management
- Audit logging and reporting

Key Features:
- Records container lifecycle management
- Destruction and retention policies
- Customer billing profiles
- Document retrieval workflows
- Security and access controls
- Compliance reporting
    """,
    'author': 'Records Management System',
    'website': '',
    'depends': [
        'base',
        'mail',
        'portal',
        'account',
        'contacts',
        'sale',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'auto_install': False,
    'license': 'LGPL-3',
}