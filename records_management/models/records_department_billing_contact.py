# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsDepartmentBillingContact(models.Model):
    """Model for department billing contacts."""
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'department_id, sequence, name'

    # Core fields
    name = fields.Char('Contact Name', required=True, tracking=True)
    sequence = fields.Integer('Sequence', default=10)
    
    # Contact relationships
    customer_id = fields.Many2one('res.partner', string='Customer',
                                  domain="[('is_company', '=', True)]",
                                  help='Customer this contact belongs to')
    billing_contact_id = fields.Many2one('res.partner', string='Billing Contact',
                                         help='Specific billing contact person')
    department_id = fields.Many2one('records.department', string='Department')
    
    # Contact details
    email = fields.Char('Email', tracking=True)
    phone = fields.Char('Phone', tracking=True)
    mobile = fields.Char('Mobile')
    
    # Billing preferences
    contact_type = fields.Selection([
        ('primary', 'Primary Contact'),
        ('billing', 'Billing Contact'), 
        ('technical', 'Technical Contact'),
        ('backup', 'Backup Contact')
    ], string='Contact Type', default='billing', required=True)
    
    # Communication preferences
    receives_invoices = fields.Boolean('Receives Invoices', default=True)
    receives_statements = fields.Boolean('Receives Statements', default=True)
    receives_notifications = fields.Boolean('Receives Notifications', default=True)
    
    # Preferred communication method
    communication_method = fields.Selection([
        ('email', 'Email'),
        ('mail', 'Postal Mail'),
        ('phone', 'Phone'),
        ('portal', 'Customer Portal')
    ], string='Preferred Method', default='email')
    
    # Status and dates
    active = fields.Boolean('Active', default=True, tracking=True)
    start_date = fields.Date('Start Date', default=fields.Date.today)
    end_date = fields.Date('End Date')
    
    # Notes and additional info
    notes = fields.Text('Notes')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        """Validate date constraints"""
        for record in self:
            if record.end_date and record.start_date and record.end_date < record.start_date:
                raise ValidationError(_('End date cannot be earlier than start date'))
    
    @api.onchange('billing_contact_id')
    def _onchange_billing_contact(self):
        """Update contact details when billing contact changes"""
        if self.billing_contact_id:
            self.email = self.billing_contact_id.email
            self.phone = self.billing_contact_id.phone
            self.mobile = self.billing_contact_id.mobile
            if not self.name:
                self.name = self.billing_contact_id.name
