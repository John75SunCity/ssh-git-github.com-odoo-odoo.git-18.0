# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RecordDisposition(models.Model):
    """
    Record Disposition - How records are handled at end of retention period
    
    From O'Neil Stratus documentation:
    "Descriptive term from a controlled list that describes how a record series 
    is to be handled at the end of its retention period."
    
    Typical values:
    - Shred
    - Incinerate
    - Recycle
    - Transfer Ownership
    - Archive (Permanent Storage)
    - Review for Retention Extension
    """
    _name = 'record.disposition'
    _description = 'Record Disposition Method'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Disposition Method',
        required=True,
        help='How records should be handled at end of retention (Shred, Incinerate, Recycle, Transfer, etc.)'
    )
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help='Short code for this disposition method (e.g., SHRD, INCN, RCYL, XFER)'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of this disposition method and when to use it'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order in lists and forms'
    )
    active = fields.Boolean(
        default=True,
        help='Inactive dispositions are hidden but retain historical data'
    )
    is_destructive = fields.Boolean(
        string='Is Destructive',
        default=True,
        help='Check if this disposition involves destruction (Shred, Incinerate). '
             'Uncheck for non-destructive actions (Transfer, Archive).'
    )
    requires_certificate = fields.Boolean(
        string='Requires Certificate',
        default=False,
        help='Check if this disposition requires a certificate of destruction/transfer'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Disposition code must be unique!'),
    ]
