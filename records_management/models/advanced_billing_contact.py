# -*- coding: utf-8 -*-
"""
Advanced Billing Contact Model

Defines the advanced.billing.contact model for managing billing contacts associated with advanced billing profiles.
Supports contact preferences, communication options, and ensures only one primary contact per billing profile.
Integrates with Odoo's mail and activity mixins for full tracking and workflow support.
"""

from odoo import api, fields, models
from odoo.exceptions import ValidationError


class AdvancedBillingContact(models.Model):
    """
    Advanced Billing Contact

    Represents a contact for an advanced billing profile, including preferences for invoice receipt,
    communication methods, and primary contact designation. Ensures integrity of primary contact assignment
    and provides utility methods for contact management.
    """

    _name = 'advanced.billing.contact'
    _description = 'Advanced Billing Contact'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string='Contact Name', required=True, tracking=True)
    email = fields.Char(string='Email', required=True, tracking=True)
    phone = fields.Char(string='Phone', tracking=True)

    # Billing profile relationship
    billing_profile_id = fields.Many2one('advanced.billing.profile', string='Billing Profile',
                                        required=True, ondelete='cascade')
    partner_id = fields.Many2one(related='billing_profile_id.partner_id', string='Customer',
                                store=True, readonly=True, comodel_name='res.partner')

    # Contact preferences
    receive_storage_invoices = fields.Boolean(string='Receive Storage Invoices',
                                             default=True, tracking=True)
    receive_service_invoices = fields.Boolean(string='Receive Service Invoices',
                                             default=True, tracking=True)
    receive_statements = fields.Boolean(string='Receive Statements',
                                       default=True, tracking=True)
    receive_reminders = fields.Boolean(string='Receive Payment Reminders',
                                      default=True, tracking=True)

    # Contact role and priority
    primary_contact = fields.Boolean(string='Primary Contact', default=False, tracking=True)
    contact_type = fields.Selection([
        ('billing', 'Billing Contact'),
        ('accounting', 'Accounting Contact'),
        ('executive', 'Executive Contact'),
        ('technical', 'Technical Contact'),
        ('other', 'Other')
    ], string='Contact Type', default='billing', tracking=True)

    sequence = fields.Integer(string='Sequence', default=10,
                             help='Order of contact priority')
    active = fields.Boolean(default=True, tracking=True)

    # Communication preferences
    preferred_communication = fields.Selection([
        ('email', 'Email'),
        ('phone', 'Phone'),
        ('both', 'Email and Phone'),
        ('portal', 'Customer Portal')
    ], string='Preferred Communication', default='email')

    language = fields.Selection(selection='_get_languages', string='Language',
                               help='Language for communications')
    timezone = fields.Selection(selection='_tz_get', string='Timezone')

    # Status and metadata
    company_id = fields.Many2one(related='billing_profile_id.company_id', store=True, readonly=True, comodel_name='res.company')
    last_contact_date = fields.Datetime(string='Last Contact Date', readonly=True)
    notes = fields.Text(string='Notes')

    @api.model
    def _get_languages(self):
        """Get available languages for selection"""
        langs = self.env["res.lang"].get_installed()
        return [(lang["code"], lang["name"]) for lang in langs]

    @api.model
    def _tz_get(self):
        """Get available timezones for selection"""
        return [(tz, tz) for tz in self.env["res.partner"]._tz_get()]

    @api.constrains('primary_contact')
    def _check_primary_contact(self):
        """Ensure only one primary contact per billing profile"""
        for contact in self:
            if contact.primary_contact:
                other_primaries = self.search([
                    ('billing_profile_id', '=', contact.billing_profile_id.id),
                    ('primary_contact', '=', True),
                    ('id', '!=', contact.id)
                ])
                if other_primaries:
                    raise ValidationError(
                        "There can only be one primary contact per billing profile."
                    )

    @api.model_create_multi
    def create(self, vals_list):
        """Auto-set primary contact if none exists"""
        contacts = super().create(vals_list)
        for contact in contacts:
            # Defensive check: ensure field exists before accessing
            if (
                hasattr(contact.billing_profile_id, "primary_contact_id")
                and not contact.billing_profile_id.primary_contact_id
            ):
                contact.billing_profile_id.primary_contact_id = contact.id
                contact.primary_contact = True
        return contacts

    def write(self, vals):
        if "primary_contact" in vals and vals["primary_contact"]:
            for contact in self:
                # Ensure only one primary per profile
                contact_id = contact.id
                other_contacts = contact.billing_profile_id.contact_ids.filtered(lambda c, cid=contact_id: c.id != cid)
                other_contacts.write({"primary_contact": False})
        return super().write(vals)

    def action_set_primary(self):
        """Set this contact as primary"""
        self.ensure_one()
        self.primary_contact = True
        # Ensure others are not primary
        self.billing_profile_id.contact_ids.filtered(lambda c: c.id != self.id).write({"primary_contact": False})

    def action_contact_now(self):
        """Record contact attempt"""
        self.ensure_one()
        self.last_contact_date = fields.Datetime.now()
