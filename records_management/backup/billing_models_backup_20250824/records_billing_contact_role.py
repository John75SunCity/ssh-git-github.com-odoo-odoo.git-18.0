# -*- coding: utf-8 -*-
"""
Model for Records Billing Contact Role.

Defines roles for billing contacts (e.g. Primary Billing, Accounts Payable).
Follows Odoo RM module standards: single model per file, mail integration, unique key, sequence, and description.
"""

from odoo import models, fields

class RecordsBillingContactRole(models.Model):
    """Role definition for billing contacts (single model per file)."""
    _name = 'records.billing.contact.role'
    _description = 'Records Billing Contact Role'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(string='Role Name', required=True, tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, help="Order for display and selection.")
    key = fields.Char(
        string='Technical Key',
        help="Unique technical key for programmatic use (e.g. 'primary_billing').",
        copy=False,
        tracking=True
    )
    description = fields.Text(string='Description', tracking=True)

    _sql_constraints = [
        ('key_uniq', 'unique(key)', 'The technical key must be unique.'),
    ]
