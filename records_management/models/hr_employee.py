# -*- coding: utf-8 -*-
"""
HR Employee Extension (Simplified)
"""

from odoo import models, fields, api, _


class HrEmployee(models.Model):
    """
    HR Employee Extension for Records Management (Simplified to avoid field conflicts)
    """
    
    _inherit = 'hr.employee'
    
    # Minimal records management fields to avoid conflicts
    records_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator')
    ], string='Records Access Level', default='none')
    
    destruction_authorized = fields.Boolean(
        string='Authorized for Destruction',
        help='Employee is authorized to approve document destruction',
        default=False
    )
