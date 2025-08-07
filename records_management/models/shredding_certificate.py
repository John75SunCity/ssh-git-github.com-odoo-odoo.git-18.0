# -*- coding: utf-8 -*-

from odoo import models, fields, api

class ShreddingCertificate(models.Model):
    _name = "shredding.certificate"
    _description = "Shredding Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Certificate Number", required=True, tracking=True, index=True
    )
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("delivered", "Delivered"),
            ("archived", "Archived"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CERTIFICATE DETAILS
    # ============================================================================
    certificate_date = fields.Date(
        string="Certificate Date", default=fields.Date.today, required=True
    )
    destruction_date = fields.Date(string="Destruction Date", required=True)
    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("pulverization", "Pulverization"),
            ("incineration", "Incineration"),
            ("degaussing", "Degaussing"),
        ],
        string="Destruction Method",
        required=True,
    )

    # ============================================================================
    # CUSTOMER & SERVICE INFO
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer", required=True)
    witness_name = fields.Char(string="Witness Name")
    witness_title = fields.Char(string="Witness Title")
    total_weight = fields.Float(
        string="Total Weight Destroyed (lbs)", digits="Stock Weight", default=0.0
    )
    total_containers = fields.Integer(string="Total Containers", default=0)

    # ============================================================================
    # COMPLIANCE & CERTIFICATION
    # ============================================================================
    naid_level = fields.Selection(
        [("aaa", "NAID AAA"), ("aa", "NAID AA"), ("a", "NAID A")],
        string="NAID Certification Level",
        default="aaa",
    )

    certification_statement = fields.Text(
        string="Certification Statement",
        default="This is to certify that the documents/materials described above have been destroyed in accordance with NAID standards.",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    service_ids = fields.One2many(
        "shredding.service", "certificate_id", string="Shredding Services"
    )
    service_count = fields.Integer(
        string="Service Count", compute="_compute_service_count", store=True
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)        "mail.followers", "res_id", string="Followers"
    )