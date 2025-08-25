# -*- coding: utf-8 -*-
"""
Department Billing Contact Module

Manages specific billing contacts associated with a customer's department,
ensuring invoices and billing communications are sent to the correct person.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsDepartmentBillingContact(models.Model):
    _name = 'records.department.billing.contact'
    _description = 'Department Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'department_id, sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string='Contact Name', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', required=True, ondelete='cascade', tracking=True)
    partner_id = fields.Many2one(related='department_id.partner_id', string='Customer', store=True, readonly=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Determines the order of contacts, lower is higher priority.")

    # ============================================================================
    # CONTACT INFORMATION
    # ============================================================================
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    contact_type = fields.Selection([
        ('primary', 'Primary Billing Contact'),
        ('secondary', 'Secondary Contact'),
        ('accounts_payable', 'Accounts Payable'),
        ('other', 'Other')
    ], string='Contact Type', default='primary', required=True, tracking=True)

    # ============================================================================
    # NOTES
    # ============================================================================
    notes = fields.Text(string='Notes')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('email')
    def _check_email(self):
        """Validate email format."""
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError(_("Please enter a valid email address."))

    @api.constrains('department_id', 'contact_type')
    def _check_unique_primary_contact(self):
        """Ensure only one primary billing contact per department."""
        for record in self:
            if record.contact_type == 'primary':
                domain = [
                    ('department_id', '=', record.department_id.id),
                    ('contact_type', '=', 'primary'),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("A primary billing contact already exists for this department."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_send_test_email(self):
        """Sends a test email to the contact to verify the address."""
        self.ensure_one()
        if not self.email:
            raise UserError(_("This contact does not have an email address."))

        mail_template = self.env.ref('mail.mail_template_data_notification_email_default', raise_if_not_found=False)
        if not mail_template:
            raise UserError(_("The default email template could not be found. Please contact an administrator."))

        mail_body = _("""
            <p>Hello %s,</p>
            <p>This is a test email from your Records Management provider to confirm that your contact information is correct in our system.</p>
            <p>No action is required on your part.</p>
            <p>Thank you,<br/>%s</p>
        """) % (self.name, self.company_id.name)

        mail_template.with_context(
            body_html=mail_body,
            subject=_("Test Email from %s") % self.company_id.name
        ).send_mail(self.id, force_send=True)

        self.message_post(body=_("Test email sent to %s.") % self.email)
