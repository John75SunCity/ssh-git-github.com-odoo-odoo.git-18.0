# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PaperBaleSourceDocument(models.Model):
    _name = "paper.bale.source.document"
    _description = "Paper Bale Source Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Core Fields
    name = fields.Char(string="Document Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Required Inverse Field
    bale_id = fields.Many2one(
        "paper.bale", string="Paper Bale", required=True, ondelete="cascade"
    )

    # Business Fields
    document_type = fields.Char(string="Document Type", tracking=True)
    source_location = fields.Char(string="Source Location")
    document_weight = fields.Float(string="Document Weight (lbs)")
    collection_date = fields.Date(string="Collection Date")

    # Workflow Fields
    state = fields.Selection(
        [("draft", "Draft"), ("processed", "Processed"), ("baled", "Baled")],
        default="draft",
        tracking=True,
    )

    # Notes
    notes = fields.Text(string="Notes")

    @api.depends("document_weight")
    def _compute_document_count(self):
        """Compute document count for related paper bale"""
        for record in self:
            if record.bale_id:
                record.bale_id._compute_document_count()

    def action_mark_processed(self):
        """Mark document as processed"""
        self.ensure_one()
        self.write({"state": "processed"})

    def action_mark_baled(self):
        """Mark document as baled"""
        self.ensure_one()
        self.write({"state": "baled"})
