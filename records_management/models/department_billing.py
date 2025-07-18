# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department
"""

from odoo import models, fields, api


class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _rec_name = 'contact_name'

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade'
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True
    )
    
    contact_name = fields.Char(
        string='Contact Name',
        required=True
    )
    
    email = fields.Char(
        string='Email',
        required=True
    )
    
    phone = fields.Char(string='Phone')
    
    is_primary = fields.Boolean(
        string='Primary Contact',
        default=False
    )
    
    active = fields.Boolean(default=True)


class ResPartnerDepartmentBilling(models.Model):
    """
    Model for partner department billing assignments
    """
    _name = 'res.partner.department.billing'
    _description = 'Partner Department Billing'
    _rec_name = 'department_id'

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade'
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True
    )
    
    billing_contact_id = fields.Many2one(
        'res.partner',
        string='Billing Contact',
        domain="[('parent_id', '=', partner_id)]"
    )
    
    billing_method = fields.Selection([
        ('inherit', 'Inherit from Customer'),
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail'),
    ], string='Billing Method', default='inherit')
    
    active = fields.Boolean(default=True)
