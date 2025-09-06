# -*- coding: utf-8 -*-
"""
Destruction Certificate Module

Manages certificates of destruction for completed shredding/destruction services.
Provides legal documentation and compliance tracking for destruction activities.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import base64
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
    fsm_task_id = fields.Many2one(comodel_name="project.task", string="FSM Task", readonly=True)
    shredding_team_id = fields.Many2one(comodel_name="shredding.team", string="Shredding Team")
    work_order_id = fields.Many2one(comodel_name="work.order.shredding", string="Work Order")
    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Customer Invoice",
        help="Invoice generated for this destruction service (must be in Posted + Paid state for portal visibility)",
        tracking=True,
    )

    portal_visible = fields.Boolean(
        string="Portal Visible",
        compute="_compute_portal_visible",
        store=False,
        help="Derived flag: certificate only visible to portal user once invoice is paid (if an invoice exists).",
    )

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    certificate_attachment_id = fields.Many2one(
        comodel_name="ir.attachment",
        string="Certificate Document",
        readonly=True,
        help="Generated PDF certificate attached upon confirmation when the feature toggle is enabled.",
    )
    # Batch 4 Relabel: Disambiguate generic 'Notes' label
    notes = fields.Text(string="Certificate Notes")

    # ============================================================================
    # COMPLIANCE
    # ============================================================================
    naid_certificate_id = fields.Many2one("naid.certificate", string="NAID Certificate")
    compliance_officer_id = fields.Many2one("res.users", string="Compliance Officer")
    witness_id = fields.Many2one("res.partner", string="Witness")
    operator_certification_id = fields.Many2one("naid.operator.certification", string="Operator Certification")

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
    destruction_confirmed = fields.Boolean(
        string="Destruction Confirmed",
        help="Internal flag set when destruction outcome has been validated (triggers issuance).",
        tracking=True,
        default=False,
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

    def _is_certificate_feature_enabled(self):
        """Check configurator toggle for destruction certificate generation.

        Falls back to True if configurator not found to avoid blocking core workflow.
        """
        return bool(
            self.env["rm.module.configurator"].sudo().get_config_parameter(
                "destruction_certificate_enabled", True
            )
        )

    def generate_certificate_document(self):
        """Generate and attach PDF certificate (placeholder implementation).

        Actual PDF QWeb report will be implemented separately. For now, create
        a lightweight text attachment to validate workflow and attachment linkage.
        Skips generation if feature toggle disabled or already attached.
        """
        self.ensure_one()
        if not self._is_certificate_feature_enabled():
            return False
        if self.certificate_attachment_id:
            return self.certificate_attachment_id
        content = (
            "Destruction Certificate\n"
            f"Number: {self.name}\n"
            f"Date: {self.certificate_date}\n"
            f"Customer: {self.partner_id.display_name}\n"
            f"State: {self.state}\n"
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": f"DestructionCertificate-{self.name}.txt",
                "datas": base64.b64encode(content.encode("utf-8")),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "text/plain",
            }
        )
        self.certificate_attachment_id = attachment.id
        return attachment

    # -------------------------------------------------------------------------
    # Enhanced issuance workflow
    # -------------------------------------------------------------------------
    def action_confirm_destruction(self):
        """Confirm destruction results, auto-issue certificate, generate document, and link invoice if available.

        Flow:
          1. Mark destruction_confirmed
          2. Transition state -> issued (if still draft)
          3. Generate certificate document (placeholder)
          4. (Optional future) Auto-create invoice if not provided
        """
        self.ensure_one()
        updates = {}
        if not self.destruction_confirmed:
            updates["destruction_confirmed"] = True
        if self.state == "draft":
            updates["state"] = "issued"
        if updates:
            self.write(updates)
        # Generate document (placeholder) if feature enabled
        self.generate_certificate_document()
        return True

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends("invoice_id.payment_state")
    def _compute_portal_visible(self):
        for rec in self:
            # If there's an invoice: require it to be posted & paid; else hide until an invoice is linked
            inv = rec.invoice_id
            rec.portal_visible = bool(inv and inv.payment_state in ("paid", "in_payment"))
