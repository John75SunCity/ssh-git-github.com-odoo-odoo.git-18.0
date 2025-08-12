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
