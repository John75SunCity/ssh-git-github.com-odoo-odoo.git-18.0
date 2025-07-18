# -*- coding: utf-8 -*-
"""
Department Billing Contact Models
Support for multiple billing contacts per department
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import hashlib  # For potential hashing of sensitive contact info (ISO 27001 privacy)

class RecordsDepartmentBillingContact(models.Model):
    """
    Model for department-specific billing contacts.
    This enables multi-contact management per department, ensuring NAID AAA compliance for auditable billing communications 
    (e.g., traceable invoice deliveries). ISO 15489 standards for data integrity are supported via tracking and hashing.
    """
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _rec_name = 'contact_name'
    _order = 'contact_name'  # Added for user-friendly sorting in lists

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True,  # Added for audit trails (NAID AAA requirement)
        index=True  # For faster searches in large datasets
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True
    )
    
    contact_name = fields.Char(
        string='Contact Name',
        required=True,
        tracking=True
    )
    
    email = fields.Char(
        string='Email',
        required=True,
        tracking=True
    )
    
    phone = fields.Char(
        string='Phone',
        tracking=True
    )
    
    is_primary = fields.Boolean(
        string='Primary Contact',
        default=False,
        tracking=True
    )
    
    active = fields.Boolean(default=True, tracking=True)
    
    hashed_email = fields.Char(
        compute='_compute_hashed_email',
        store=True,
        help='Hashed for privacy compliance (ISO 27001/GDPR)'
    )

    @api.depends('email')
    def _compute_hashed_email(self):
        for rec in self:
            rec.hashed_email = hashlib.sha256(rec.email.encode()).hexdigest() if rec.email else False

    @api.constrains('is_primary')
    def _check_primary_unique(self):
        """Ensure only one primary per department (clean data integrity)."""
        for rec in self:
            if rec.is_primary and self.search_count([
                ('department_id', '=', rec.department_id.id),
                ('is_primary', '=', True),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError(_("Only one primary contact per department."))

class ResPartnerDepartmentBilling(models.Model):
    """
    Model for partner department billing assignments.
    Links departments to billing prefs/contacts, supporting hybrid methods for multi-dept customers.
    NAID AAA: Ensures auditable billing trails; ISO 15489: Structured for verifiable processes.
    """
    _name = 'res.partner.department.billing'
    _description = 'Partner Department Billing'
    _rec_name = 'department_id'
    _order = 'department_id'  # Added for sorted views

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        tracking=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True
    )
    
    billing_contact_id = fields.Many2one(
        'res.partner',
        string='Billing Contact',
        domain="[('parent_id', '=', partner_id)]",
        tracking=True
    )
    
    billing_method = fields.Selection([
        ('inherit', 'Inherit from Customer'),
        ('email', 'Email'),
        ('portal', 'Customer Portal'),
        ('mail', 'Postal Mail'),
    ], string='Billing Method', default='inherit', tracking=True)
    
    active = fields.Boolean(default=True, tracking=True)
