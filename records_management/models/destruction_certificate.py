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
import logging
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
    event_ids = fields.One2many(
        comodel_name="destruction.event",
        inverse_name="certificate_id",
        string="Destruction Events",
        help="Individual destruction events that roll up into this certificate",
    )

    # ============================================================================
    # SERVICE TRACKING
    # ============================================================================
    fsm_task_id = fields.Many2one(comodel_name="project.task", string="FSM Task", readonly=True)
    shredding_team_id = fields.Many2one(comodel_name="shredding.team", string="Shredding Team")
    work_order_id = fields.Many2one(comodel_name="work.order.shredding", string="Work Order")
    invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Customer Invoice",
        help="Invoice linked to this destruction service. When it reaches Paid state the certificate document will be generated automatically (if not already).",
        tracking=True,
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

    def generate_certificate_document(self, force=False):
        """Generate and attach the PDF certificate via QWeb report.

        Behavior:
          - Skips if feature disabled.
          - Skips if existing attachment is already a PDF (unless force=True).
          - Uses action_report_destruction_certificate to render.
          - Stores as ir.attachment and links certificate_attachment_id.
          - Provides graceful fallback with a text placeholder if report missing or fails.
        """
        self.ensure_one()
        if not self._is_certificate_feature_enabled():
            return False
        # Skip regeneration if we already have a PDF unless forced
        if (
            self.certificate_attachment_id
            and self.certificate_attachment_id.mimetype == "application/pdf"
            and not force
        ):
            return self.certificate_attachment_id

        logger = logging.getLogger(__name__)
        pdf_bytes = False
        report = self.env.ref(
            "records_management.action_report_destruction_certificate", raise_if_not_found=False
        )
        if report:
            try:
                result = report._render_qweb_pdf(self.ids)
                if isinstance(result, tuple):
                    pdf_bytes = result[0]
                else:
                    pdf_bytes = result
            except Exception as exc:  # noqa: BLE001 broad but logged
                logger.error("Failed rendering destruction certificate PDF %s: %s", self.name, exc)
        else:
            logger.warning("Destruction certificate report action not found for %s", self.name)

        if pdf_bytes:
            datas = base64.b64encode(pdf_bytes)
            mimetype = "application/pdf"
            filename = f"DestructionCertificate-{self.name}.pdf"
        else:
            # Fallback placeholder text when PDF generation not available
            content = (
                "Destruction Certificate\n"
                f"Number: {self.name}\n"
                f"Date: {self.certificate_date}\n"
                f"Customer: {self.partner_id.display_name}\n"
                f"State: {self.state}\n"
                "(PDF generation unavailable)\n"
            )
            datas = base64.b64encode(content.encode("utf-8"))
            mimetype = "text/plain"
            filename = f"DestructionCertificate-{self.name}.txt"

        # If existing attachment mismatched (e.g., old text) replace it
        if self.certificate_attachment_id and (force or self.certificate_attachment_id.mimetype != mimetype):
            self.certificate_attachment_id.unlink()

        attachment = self.env["ir.attachment"].create(
            {
                "name": filename,
                "datas": datas,
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": mimetype,
            }
        )
        self.certificate_attachment_id = attachment.id
        return attachment

    # -------------------------------------------------------------------------
    # REPORT SUPPORT HELPERS (aggregation for QWeb template)
    # -------------------------------------------------------------------------
    def _get_aggregated_events(self):
        """Return simplified dict list of linked events for easier QWeb iteration.

        Avoids heavy recordset logic in template and provides consistent ordering.
        """
        self.ensure_one()
        events = self.event_ids.sorted(lambda e: (e.date or '', e.name or ''))
        data = []
        for ev in events:
            data.append(
                {
                    "name": ev.name,
                    "date": ev.date,
                    "technician": ev.technician_id.display_name,
                    "location_type": ev.location_type,
                    "items": ev.shredded_items,
                    "quantity": ev.quantity,
                    "uom": ev.unit_of_measure,
                }
            )
        return data

    def _signature_block_context(self):
        """Return context dict for signature placeholders in report.

        Provides names only (no binary sign images yet). Future enhancement could
        embed sign.request integration or attachment lookups.
        """
        self.ensure_one()
        return {
            "compliance_officer": self.compliance_officer_id and self.compliance_officer_id.display_name or "",
            "witness": self.witness_id and self.witness_id.display_name or "",
            "operator": self.operator_certification_id
            and self.operator_certification_id.operator_id.display_name
            or "",
        }

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

    def action_force_regenerate_certificate(self):
        """Force re-generation of the certificate document.

        Always regenerates (even if PDF already exists) provided the feature toggle is enabled.
        Posts a chatter message with the outcome.
        """
        self.ensure_one()
        attachment = self.generate_certificate_document(force=True)
        if attachment:
            self.message_post(body=_("Destruction certificate document regenerated."), attachment_ids=[attachment.id])
        return True

    def action_print_certificate(self):  # UI button helper
        """Return the QWeb report action for this destruction certificate.

        Ensures the document exists (generating if feature enabled and missing)
        then returns the standard report action so the user can download/print.
        Fallback: if report action missing, regenerate placeholder attachment
        and open it in attachment preview.
        """
        self.ensure_one()
        # Ensure we have (at least) a generated document if feature enabled
        if not self.certificate_attachment_id and self._is_certificate_feature_enabled():
            self.generate_certificate_document()
        report = self.env.ref("records_management.action_report_destruction_certificate", raise_if_not_found=False)
        if report:
            return report.report_action(self)
        # Fallback: open the attachment (may be placeholder) if exists
        if self.certificate_attachment_id:
            return {
                "type": "ir.actions.act_url",
                "url": f"/web/content/{self.certificate_attachment_id.id}?download=true",
                "target": "self",
            }
        return False

    # -------------------------------------------------------------------------
    # COMPUTE METHODS
    # -------------------------------------------------------------------------
    @api.depends("invoice_id.payment_state")
    def _auto_generate_on_invoice_paid(self):
        """When the linked invoice becomes paid, ensure certificate document exists.

        This replaces prior portal visibility gating. Keeps portal access simple
        and shifts gating to document existence timing.
        """
        for rec in self:
            inv = rec.invoice_id
            if (
                inv
                and inv.payment_state == "paid"
                and not rec.certificate_attachment_id
                and rec._is_certificate_feature_enabled()
            ):
                # Generate the document (placeholder now; later real PDF)
                rec.generate_certificate_document()
