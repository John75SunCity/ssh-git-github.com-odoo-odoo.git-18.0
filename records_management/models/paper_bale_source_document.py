# -*- coding: utf-8 -*-
from odoo import models, fields

class PaperBaleSourceDocument(models.Model):
    _name = "paper.bale.source.document"
    _description = "Paper Bale Source Document"
    _rec_name = "document_reference"

    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    )
    document_reference = fields.Char(
        string="Document Reference", required=True
    )
    document_type = fields.Char(string="Document Type")
    customer_id = fields.Many2one("res.partner", string="Customer")
    estimated_weight = fields.Float(string="Estimated Weight")
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
    )
    destruction_required = fields.Boolean(
        string="Destruction Required", default=False
    )
    notes = fields.Text(string="Notes")
