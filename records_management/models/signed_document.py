# -*- coding: utf-8 -*-

from odoo import models, fields, api

class SignedDocument(models.Model):
    _name = "signed.document"
    _description = "Signed Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core Fields
    name = fields.Char(string="Document Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Required Inverse Field
    request_id = fields.Many2one(
        "portal.request", string="Portal Request", required=True, ondelete="cascade"
    )

    # Business Fields
    document_type = fields.Selection(
        [
            ("destruction_request", "Destruction Request"),
            ("service_agreement", "Service Agreement"),
            ("certificate", "Certificate"),
            ("authorization", "Authorization"),
        ],
        string="Document Type",
        required=True,
        tracking=True,
    )

    signature_date = fields.Datetime(string="Signature Date", tracking=True)
    signatory_name = fields.Char(string="Signatory Name", tracking=True)
    signatory_email = fields.Char(string="Signatory Email")
    signatory_title = fields.Char(string="Signatory Title")

    # Document Fields
    pdf_document = fields.Binary(string="PDF Document")
    pdf_filename = fields.Char(string="PDF Filename")

    # Workflow Fields
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("signed", "Signed"),
            ("verified", "Verified"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    # Legal Fields
    signature_hash = fields.Char(string="Signature Hash")
    verification_status = fields.Selection(
        [("pending", "Pending"), ("valid", "Valid"), ("invalid", "Invalid")],
        default="pending",
        tracking=True,
    )

    # Notes
    notes = fields.Text(string="Notes")

    @api.depends("signature_date", "signatory_name")
    def _compute_display_name(self):
        """Compute display name with signature info"""
        for record in self:
            if record.signatory_name and record.signature_date:
                record.display_name = f"{record.name} - {record.signatory_name}"
            else:
                record.display_name = record.name

    def action_mark_signed(self):

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )
        """Mark document as signed"""
        self.ensure_one()
        self.write({"state": "signed", "signature_date": fields.Datetime.now()})

    def action_verify_signature(self):
        """Verify document signature"""
        self.ensure_one()
        # Add signature verification logic here
        self.write({"state": "verified", "verification_status": "valid"})
