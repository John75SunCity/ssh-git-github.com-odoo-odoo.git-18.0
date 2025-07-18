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
    _description = 'Department Billing Contact'
    _rec_name = 'contact_name'
    _order = 'contact_name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True,
        index=True
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
        tracking=True,
        help='Only one primary contact allowed per department'
    )
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    hashed_email = fields.Char(
        compute='_compute_hashed_email',
        store=True,
        help='SHA256 hashed email for privacy compliance (ISO 27001/GDPR)'
    )
    
    # Computed fields for enhanced functionality
    total_departments = fields.Integer(
        compute='_compute_contact_stats',
        string='Total Departments'
    )
    
    last_billing_date = fields.Date(
        compute='_compute_billing_stats',
        string='Last Billing Date'
    )

    @api.depends('email')
    def _compute_hashed_email(self):
        """Compute SHA256 hash of email for privacy compliance"""
        for rec in self:
            rec.hashed_email = hashlib.sha256(rec.email.encode()).hexdigest() if rec.email else False

    @api.depends('customer_id')
    def _compute_contact_stats(self):
        """Compute statistics about contact's departments"""
        for rec in self:
            if rec.customer_id:
                rec.total_departments = len(rec.customer_id.department_ids)
            else:
                rec.total_departments = 0

    def _compute_billing_stats(self):
        """Compute billing-related statistics"""
        for rec in self:
            # Find latest invoice for this contact's customer/department
            invoices = self.env['account.move'].search([
                ('partner_id', '=', rec.customer_id.id),
                ('move_type', '=', 'out_invoice'),
                ('state', '=', 'posted')
            ], order='invoice_date desc', limit=1)
            rec.last_billing_date = invoices.invoice_date if invoices else False

    @api.constrains('email')
    def _check_email_format(self):
        """Validate email format"""
        for rec in self:
            if rec.email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', rec.email):
                raise ValidationError(_("Please enter a valid email address for %s") % rec.contact_name)

    @api.constrains('is_primary', 'department_id')
    def _check_primary_unique(self):
        """Ensure only one primary contact per department"""
        for rec in self:
            if rec.is_primary and self.search_count([
                ('department_id', '=', rec.department_id.id),
                ('is_primary', '=', True),
                ('id', '!=', rec.id)
            ]):
                raise ValidationError(_("Only one primary contact allowed per department: %s") % rec.department_id.name)

    def action_make_primary(self):
        """Action to make this contact primary for the department"""
        # Remove primary status from other contacts in same department
        other_primaries = self.search([
            ('department_id', '=', self.department_id.id),
            ('is_primary', '=', True),
            ('id', '!=', self.id)
        ])
        other_primaries.write({'is_primary': False})
        # Set this contact as primary
        self.is_primary = True
        return True

class ResPartnerDepartmentBilling(models.Model):
    """
    Model for partner department billing assignments.
    Enhanced with enterprise features: tracking, validation, and computed fields.
    """
    _name = 'res.partner.department.billing'
    _description = 'Partner Department Billing'
    _rec_name = 'department_id'
    _order = 'department_id'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    partner_id = fields.Many2one(
        'res.partner',
        string='Partner',
        required=True,
        ondelete='cascade',
        tracking=True,
        index=True
    )
    
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        required=True,
        tracking=True,
        index=True
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
    
    active = fields.Boolean(
        default=True,
        tracking=True
    )
    
    # Enhanced computed fields
    monthly_storage_fee = fields.Float(
        compute='_compute_billing_totals',
        string='Monthly Storage Fee',
        store=True
    )
    
    total_boxes = fields.Integer(
        compute='_compute_billing_totals',
        string='Total Boxes',
        store=True
    )
    
    last_invoice_date = fields.Date(
        compute='_compute_billing_totals',
        string='Last Invoice Date',
        store=True
    )

    @api.depends('customer_id', 'department_id', 'department_id.box_ids', 'department_id.box_ids.state')
    def _compute_billing_totals(self):
        """Compute billing totals from department"""
        for rec in self:
            if rec.department_id:
                # Calculate directly from source data instead of computed fields
                active_boxes = rec.department_id.box_ids.filtered(lambda b: b.state == 'active')
                rec.total_boxes = len(active_boxes)
                rec.monthly_storage_fee = len(active_boxes) * 10.0  # $10 per box per month
                
                # Find latest invoice for this partner/department
                invoices = self.env['account.move'].search([
                    ('partner_id', '=', rec.customer_id.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted')
                ], order='invoice_date desc', limit=1)
                rec.last_invoice_date = invoices.invoice_date if invoices else False
            else:
                rec.monthly_storage_fee = 0.0
                rec.total_boxes = 0
                rec.last_invoice_date = False

    @api.constrains('customer_id', 'department_id')
    def _check_department_belongs_to_partner(self):
        """Ensure department belongs to the selected partner"""
        for rec in self:
            if rec.department_id and rec.department_id.partner_id != rec.customer_id:
                raise ValidationError(_("Department '%s' does not belong to partner '%s'") % 
                                    (rec.department_id.name, rec.customer_id.name))

    def action_generate_invoice(self):
        """Action to generate invoice for this department billing"""
        if not self.monthly_storage_fee:
            raise ValidationError(_("No storage fee configured for department %s") % self.department_id.name)
        
        # Create invoice logic here
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'name': f'Storage Fee - {self.department_id.name}',
                'quantity': 1,
                'price_unit': self.monthly_storage_fee,
            })]
        }
        invoice = self.env['account.move'].create(invoice_vals)
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }
