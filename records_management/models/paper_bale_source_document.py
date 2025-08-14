# -*- coding: utf-8 -*-
from odoo import models, fields

class PaperBaleSourceDocument(models.Model):
    _name = "paper.bale.source.document"
    _description = "Paper Bale Source Document"
    _rec_name = "document_reference"


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
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.source.document') or _('New')
        return super().create(vals_list)
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
