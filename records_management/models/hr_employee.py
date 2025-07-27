# -*- coding: utf-8 -*-
"""
HR Employee Extension
"""

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    """
    HR Employee Extension for Records Management
    Extends the core HR Employee model with records-specific fields
    """
    
    _inherit = 'hr.employee'  # Inherit from existing model, don't create new one
    
    # Records Management specific fields
    records_department_id = fields.Many2one(
        'rec.dept', 
        string='Records Department',
        help='Department for records management access control'
    )
    naid_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator')
    ], string='NAID Access Level', default='none')
    
    destruction_authorized = fields.Boolean(
        string='Authorized for Destruction',
        help='Employee is authorized to approve document destruction'
    )
    
    # Security clearance for sensitive documents
    security_clearance = fields.Selection([
        ('public', 'Public'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('secret', 'Secret')
    ], string='Security Clearance', default='public')
