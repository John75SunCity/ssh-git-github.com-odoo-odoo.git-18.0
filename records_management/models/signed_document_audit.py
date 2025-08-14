# -*- coding: utf-8 -*-
"""
Signed Document Audit Trail Model
"""
from odoo import fields, models


class SignedDocumentAudit(models.Model):
    """Audit trail for signed documents"""

    _name = "signed.document.audit"
    _description = "Signed Document Audit Trail"
    _order = "timestamp desc"
    _rec_name = "action"


    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        tracking=True,
        index=True,
        default=lambda self: _('New'),
        help='Unique identifier for this record'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Set to false to hide this record'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True,
        help='Company this record belongs to'
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add auto-numbering"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('signed.document.audit') or _('New')
        return super().create(vals_list)
    document_id = fields.Many2one(
        "signed.document",
        string="Signed Document",
        required=True,
        ondelete="cascade",
    )
    action = fields.Char(
        string="Action",
        required=True,
        help="Action performed on the document",
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        required=True,
        help="User who performed the action",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
    )
    timestamp = fields.Datetime(
        string="Timestamp",
        required=True,
        help="When the action was performed",
    )
    ip_address = fields.Char(
        string="IP Address",
        help="IP address from which action was performed",
    )
    details = fields.Text(
        string="Details",
        help="Detailed information about the action",
    )
