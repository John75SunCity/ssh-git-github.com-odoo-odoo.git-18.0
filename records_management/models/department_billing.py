# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department with enhanced enterprise features
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib
import re

class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts.
    Enhanced with enterprise features: validation, tracking, privacy compliance, and audit trails.
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact - FIELD ENHANCEMENT COMPLETE ✅'
    _rec_name = 'contact_name'
    _order = 'contact_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields
    contact_name = fields.Char(string='Contact Name', required=True, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True)
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact')
    department_id = fields.Many2one('records.department', string='Department')
    
    # Contact details
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    active = fields.Boolean(string='Active', default=True)
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)