# -*- coding: utf-8 -*-
"""
Destruction Certificate Module

Manages certificates of destruction for completed shredding/destruction services.
Provides legal documentation and compliance tracking for destruction activities.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class DestructionCertificate(models.Model):
    _name = "destruction.certificate"
    _description = "Destruction Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"
    _order = "certificate_date desc, name"

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string="Certificate Number", required=True, copy=False, default=lambda self: _("New"))
    certificate_date = fields.Date(
        string="Certificate Date", required=True, default=fields.Date.context_today, tracking=True
    )
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)

    # ============================================================================
    # DESTRUCTION DETAILS
    # ============================================================================
    destruction_type = fields.Selection(
        [
            ("on_site", "Mobile Shredding"),
            ("off_site", "Off-Site Destruction"),
            ("media_destruction", "Media Destruction"),
            ("hard_drive", "Hard Drive Destruction"),
            ("specialized", "Specialized Destruction"),
        ],
        string="Destruction Type",
        required=True,
        tracking=True,
    )

    weight_processed = fields.Float(string="Weight Processed (kg)", tracking=True)
    containers_processed = fields.Integer(string="Containers Processed", tracking=True)

    # ============================================================================
    # SERVICE TRACKING
    # ============================================================================
    fsm_task_id = fields.Many2one("project.task", string="FSM Task", readonly=True)
    shredding_team_id = fields.Many2one("shredding.team", string="Shredding Team")
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    certificate_attachment_id = fields.Many2one("ir.attachment", string="Certificate Document", readonly=True)
    notes = fields.Text(string="Notes")

    # ============================================================================
    # COMPLIANCE
    # ============================================================================
    naid_certificate_id = fields.Many2one("naid.certificate", string="NAID Certificate")
    compliance_officer_id = fields.Many2one("res.users", string="Compliance Officer")
    witness_id = fields.Many2one("res.partner", string="Witness")

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [("draft", "Draft"), ("issued", "Issued"), ("delivered", "Delivered"), ("archived", "Archived")],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    company_id = fields.Many2one("res.company", related="partner_id.company_id", string="Company", store=True)

    # ============================================================================
    # CONSTRAINTS & VALIDATIONS
    # ============================================================================
    @api.constrains("weight_processed")
    def _check_weight_processed(self):
        for record in self:
            if record.weight_processed and record.weight_processed < 0:
                raise ValidationError(_("Weight processed cannot be negative."))

    @api.constrains("containers_processed")
    def _check_containers_processed(self):
        for record in self:
            if record.containers_processed and record.containers_processed < 0:
                raise ValidationError(_("Containers processed cannot be negative."))

    # ============================================================================
    # NAME GENERATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("destruction.certificate") or _("New")
        return super().create(vals_list)

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_issue_certificate(self):
        """Mark certificate as issued"""
        self.ensure_one()
        self.write({"state": "issued"})

    def action_deliver_certificate(self):
        """Mark certificate as delivered to customer"""
        self.ensure_one()
        self.write({"state": "delivered"})

    def action_archive_certificate(self):
        """Archive the certificate"""
        self.ensure_one()
        self.write({"state": "archived"})

    def generate_certificate_document(self):
        """Generate PDF certificate document"""
        self.ensure_one()
        # Implementation for PDF generation would go here
        # This is a placeholder for the actual implementation
        pass
