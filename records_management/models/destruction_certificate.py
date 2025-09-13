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
import random
import string
from datetime import date
from odoo import api, fields, models, _
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
    # Computed counter used by stat button in form view (button_box)
    event_count = fields.Integer(string="Events", compute="_compute_event_count", readonly=True)

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
    naid_certificate_number = fields.Char(
        string="NAID Certificate #",
        help="External NAID membership or compliance certificate reference number, if applicable.")
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

    # -------------------------------------------------------------------------
    # PORTAL VISIBILITY (referenced by security/destruction_certificate_security.xml)
    # -------------------------------------------------------------------------
    portal_visible = fields.Boolean(
        string="Portal Visible",
        default=True,
        help="Controls whether this certificate is visible to portal users related to the customer.\n"
             "Security rule destruction_certificate_rule_portal_paid filters on this flag."
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    company_id = fields.Many2one("res.company", related="partner_id.company_id", string="Company", store=True)

    # -------------------------------------------------------------------------
    # COMPUTE METHODS: SIMPLE COUNTS
    # -------------------------------------------------------------------------
    @api.depends("event_ids")
    def _compute_event_count(self):
        for rec in self:
            rec.event_count = len(rec.event_ids)

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
    def _generate_certificate_number(self, work_order):
        """Generate formatted certificate number.

        New Pattern:
            COD/<work order name>/<RANDOM6>
            or COD/<mmddyy>/<RANDOM6> if no work order.

        RANDOM6 = 6-character uppercase alphanumeric, regenerated until unique
        (collision-checked up to a small bounded number of attempts).
        """
        attempts = 0
        max_attempts = 5
        if work_order and work_order.name:
            prefix_token = work_order.name.replace("/", "-")
        else:
            prefix_token = date.today().strftime("%m%d%y")

        while attempts < max_attempts:
            rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
            candidate = f"COD/{prefix_token}/{rand_part}"
            if not self.search_count([("name", "=", candidate)]):
                return candidate
            attempts += 1

        # Fallback (very unlikely) - append attempt counter for traceability
        rand_part = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
        return f"COD/{prefix_token}/{rand_part}-{attempts}"

    @api.model_create_multi
    def create(self, vals_list):
        records_to_name = []
        # Prefetch work orders for performance (collect ids first)
        work_order_map = {}
        work_order_ids = [vals.get("work_order_id") for vals in vals_list if vals.get("work_order_id")]
        if work_order_ids:
            wo_records = self.env["work.order.shredding"].browse(work_order_ids)
            work_order_map = {wo.id: wo for wo in wo_records}

        for vals in vals_list:
            current_name = vals.get("name")
            if not current_name or current_name == _("New"):
                wo = False
                if vals.get("work_order_id"):
                    wo = work_order_map.get(vals["work_order_id"])
                vals["name"] = self._generate_certificate_number(wo)
        records = super().create(vals_list)
        return records

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
        """
        Aggregate destruction events/lines for the PDF report.

        Returns:
            list of dict: [{
                'name': str,
                'date': str|datetime,
                'technician': str,
                'location_type': str,
                'items': str,
                'quantity': float,
                'uom': str,
            }, ...]
        """
        self.ensure_one()
        results = []

        # Try common relation names without assuming schema
        candidate_lines = (
            getattr(self, 'event_ids', False)
            or getattr(self, 'line_ids', False)
            or self.env['destruction.certificate']  # empty recordset sentinel
        )

        if candidate_lines:
            for line in candidate_lines:
                # Safe attribute getters
                name = getattr(line, 'display_name', False) or getattr(line, 'name', '') or ''
                date_val = getattr(line, 'date', False) or self.certificate_date or ''
                tech = ''
                if 'technician_id' in line._fields:
                    tech = line.technician_id.display_name or ''
                elif 'user_id' in line._fields:
                    tech = line.user_id.display_name or ''
                loc = ''
                if 'location_type' in line._fields:
                    loc = line.location_type or ''
                elif 'location_id' in line._fields:
                    loc = line.location_id.display_name or ''
                items = ''
                if 'item_description' in line._fields:
                    items = line.item_description or ''
                elif 'product_id' in line._fields:
                    items = line.product_id.display_name or ''
                qty = 0.0
                if 'quantity' in line._fields:
                    qty = line.quantity or 0.0
                elif 'qty' in line._fields:
                    qty = line.qty or 0.0
                uom = ''
                if 'uom_id' in line._fields and line.uom_id:
                    uom = line.uom_id.display_name
                elif 'product_uom_id' in line._fields and line.product_uom_id:
                    uom = line.product_uom_id.display_name

                results.append({
                    'name': name,
                    'date': date_val,
                    'technician': tech,
                    'location_type': loc,
                    'items': items,
                    'quantity': qty,
                    'uom': uom,
                })

        # Optional: stable ordering (date desc then name)
        def _key(d):
            return (str(d.get('date') or ''), d.get('name') or '')
        results.sort(key=_key)
        return results

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

    def action_revoke_certificate(self):  # referenced by XML button
        """Placeholder: revoke an already issued/delivered certificate.

        Future Behavior (planned):
            - Transition to a 'archived' or dedicated 'revoked' state (if added)
            - Log reason + user in chatter / audit log model
            - Optionally remove / supersede existing attachment
        """
        self.ensure_one()
        # Minimal safe action: move to archived if not already to avoid noop button.
        if self.state not in ("archived",):
            self.write({"state": "archived"})
            self.message_post(body=_("Certificate revoked (archived)."))
        return True

    # -------------------------------------------------------------------------
    # UI ACTIONS (Referenced by Views)
    # -------------------------------------------------------------------------
    def action_send_notification(self):  # referenced by kanban button/menu
        """Simple placeholder notification action.

        Posts a chatter message and triggers a client notification. Future
        enhancement could open a wizard for composing a custom message or
        selecting recipients.
        """
    self.ensure_one()
    # Chatter log entry (use % interpolation per project policy)
    # Simpler static message to satisfy translation lint rules
    self.message_post(body=_("Notification sent for destruction certificate"))
    return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Notification Sent"),
                "message": _("A notification was recorded in the chatter."),
                "sticky": False,
                "type": "success",
            },
        }

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
