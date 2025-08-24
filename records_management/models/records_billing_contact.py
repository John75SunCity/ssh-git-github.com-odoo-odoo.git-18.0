# -*- coding: utf-8 -*-
"""
Records Billing Contact Module

Manages specific contact persons for billing purposes associated with a customer.
This allows for directing invoices and billing communications to the correct
individual, such as an Accounts Payable representative.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsBillingContact(models.Model):
    """
    Represents a specific contact for billing-related matters for a customer.
    """
    _name = 'records.billing.contact'
    _description = 'Records Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'partner_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & RELATIONSHIPS
    # ============================================================================
    name = fields.Char(string='Contact Name', required=True, tracking=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        ondelete='cascade',
        help="The customer this billing contact is associated with."
    )
    billing_profile_id = fields.Many2one('customer.billing.profile', string="Billing Profile")
    profile_id = fields.Many2one('records.billing.profile', string="Billing Profile")
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='partner_id.company_id',
        store=True
    )
    active = fields.Boolean(string='Active', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10)

    # ============================================================================
    # CONTACT DETAILS
    # ============================================================================
    contact_type = fields.Selection([
        ('billing', 'Billing'),
        ('technical', 'Technical'),
        ('primary', 'Primary'),
        ('other', 'Other')
    ], string='Contact Type', default='billing', required=True, tracking=True)
    email = fields.Char(string='Email', tracking=True)
    phone = fields.Char(string='Phone', tracking=True)
    job_title = fields.Char(string='Job Title', tracking=True)


    # ============================================================================
    # CONFIGURATION & NOTES
    # ============================================================================
    send_invoices = fields.Boolean(
        string='Receive Invoices',
        default=True,
        help="If checked, this contact will be included in invoice communications."
    )
    send_statements = fields.Boolean(
        string='Receive Statements',
        default=True,
        help="If checked, this contact will receive account statements."
    )
    notes = fields.Text(string='Internal Notes')

    # === AUDIT: MISSING FIELDS ===
    primary_contact = fields.Char(string='Primary Contact')
    receive_service_invoices = fields.Char(string='Receive Service Invoices')
    receive_statements = fields.Char(string='Receive Statements')
    receive_storage_invoices = fields.Char(string='Receive Storage Invoices')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'contact_type')
    def _compute_display_name(self):
        """Generate a descriptive display name."""
        for record in self:
            partner_name = record.partner_id.name or ''
            contact_type_display = dict(self._fields['contact_type'].selection).get(record.contact_type, '')
            record.display_name = f"{partner_name} - {record.name} ({contact_type_display})"

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('email')
    def _check_email_validity(self):
        """Validate the email format."""
        for record in self:
            if record.email and '@' not in record.email:
                raise ValidationError(_("The email address '%s' is not valid.", record.email))

    @api.constrains('partner_id', 'contact_type')
    def _check_primary_contact_uniqueness(self):
        """Ensure only one primary contact per customer."""
        for record in self:
            if record.contact_type == 'primary':
                domain = [
                    ('partner_id', '=', record.partner_id.id),
                    ('contact_type', '=', 'primary'),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("A primary contact already exists for this customer."))

