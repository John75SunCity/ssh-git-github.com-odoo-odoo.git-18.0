# -*- coding: utf-8 -*-
from odoo import models, fields, api

class NaidDestructionRecord(models.Model):
    _name = "naid.destruction.record"
    _description = "NAID Destruction Record"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Record Number", required=True, tracking=True, index=True),
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    user_id = fields.Many2one(
        "res.users",
        default=lambda self: self.env.user,
        string="Created By",
        tracking=True,
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # DESTRUCTION DETAILS
    # ============================================================================
    destruction_date = fields.Date(string="Destruction Date", required=True)
    certificate_id = fields.Many2one("naid.certificate", string="Certificate")
    items_destroyed = fields.Integer(string="Items Destroyed")
    method = fields.Selection(
        [
            ("shredding", "Shredding"),
            ("incineration", "Incineration"),
            ("pulverization", "Pulverization"),
        ],
        string="Destruction Method",
        required=True,
    responsible_user_id = fields.Many2one("res.users", string="Destruction Manager")
    notes = fields.Text(string="Notes")
    state = fields.Selection(
        [("draft", "Draft"), ("completed", "Completed"), ("certified", "Certified")],
        default="draft",
    ))
