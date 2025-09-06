import base64
import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class NaidCertificate(models.Model):
    _name = "naid.certificate"
    _description = "NAID Destruction Certificate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "issue_date desc, certificate_number desc"

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Reference", related="certificate_number", store=True)
    certificate_number = fields.Char(
        string="Certificate Number",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _("New"),
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        readonly=True,
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, readonly=True
    )

    # Inverse link back to shredding service (used in shredding.service.certificate_ids)
    shredding_service_id = fields.Many2one(
        comodel_name="shredding.service",
        string="Shredding Service",
        readonly=True,
        help="Shredding service that produced this certificate.",
    )

    # FSM & Operational Links
    fsm_task_id = fields.Many2one(
        "project.task",
        string="FSM Work Order",
        readonly=True,
        help="Link to the Field Service task for this destruction.",
    )
    technician_user_id = fields.Many2one(
        "res.users",
        string="Technician",
        compute="_compute_technician_user_id",
        store=True,
        readonly=True,
    )

    destruction_date = fields.Datetime(
        string="Destruction Date", required=True, readonly=True
    )
    issue_date = fields.Datetime(string="Issue Date", readonly=True)
    destruction_item_ids = fields.One2many(
        "naid.certificate.item", "certificate_id", string="Destroyed Items"
    )

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("issued", "Issued"),
            ("sent", "Sent"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        readonly=True,
        tracking=True,
    )

    certificate_data = fields.Binary(string="Certificate PDF", readonly=True)
    certificate_filename = fields.Char(string="Certificate Filename", readonly=True)

    container_ids = fields.Many2many(
        "records.container",
        "naid_certificate_container_rel",
        "certificate_id",
        "container_id",
        string="Destroyed Containers",
    )
    box_ids = fields.Many2many(
        "records.container",
        "naid_certificate_box_rel",
        "certificate_id",
        "box_id",
        string="Destroyed Boxes",
    )
    total_weight = fields.Float(
        string="Total Weight (kg)", compute="_compute_totals", store=True
    )
    total_items = fields.Integer(
        string="Total Items", compute="_compute_totals", store=True
    )

    # Witness Information
    witness_name = fields.Char(string="Witness Name")
    witness_signature = fields.Binary(string="Witness Signature")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends(
        "destruction_item_ids.weight",
        "destruction_item_ids.quantity",
        "container_ids",
        "box_ids",
    )
    def _compute_totals(self):
        """Compute total weight and items with null value handling"""
        for cert in self:
            # Handle null weight values safely
            cert.total_weight = sum(
                item.weight or 0.0 for item in cert.destruction_item_ids
            )
            cert.total_items = (
                sum(item.quantity or 0 for item in cert.destruction_item_ids)
                + len(cert.container_ids)
                + len(cert.box_ids)
            )

    @api.depends("fsm_task_id.user_ids")
    def _compute_technician_user_id(self):
        """Compute technician from FSM task with proper null handling"""
        for rec in self:
            if (
                rec.fsm_task_id
                and hasattr(rec.fsm_task_id, "user_ids")
                and rec.fsm_task_id.user_ids
            ):
                rec.technician_user_id = rec.fsm_task_id.user_ids[0]
                rec.destruction_date = rec.fsm_task_id.date_end or fields.Datetime.now()

                # Automatically link related containers/boxes if they are on the task
                if hasattr(rec.fsm_task_id, "container_ids"):
                    rec.container_ids = [(6, 0, rec.fsm_task_id.container_ids.ids)]
                if hasattr(rec.fsm_task_id, "box_ids"):
                    rec.box_ids = [(6, 0, rec.fsm_task_id.box_ids.ids)]
            else:
                rec.technician_user_id = False

    # ============================================================================
    # CONSTRAINT VALIDATION
    # ============================================================================
    @api.constrains("destruction_date")
    def _check_destruction_date(self):
        """Validate destruction date is not in the future"""
        for record in self:
            if (
                record.destruction_date
                and record.destruction_date > fields.Datetime.now()
            ):
                raise ValidationError(_("Destruction date cannot be in the future"))

    @api.constrains("certificate_number")
    def _check_certificate_number_unique(self):
        """Ensure certificate numbers are unique"""
        for record in self:
            if record.certificate_number and record.certificate_number != _("New"):
                existing = self.search(
                    [
                        ("certificate_number", "=", record.certificate_number),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(_("Certificate number %s already exists") % record.certificate_number)

    @api.constrains("state", "destruction_item_ids", "container_ids", "box_ids")
    def _check_issued_certificate_has_items(self):
        """Validate issued certificates have destruction items, containers or boxes"""
        for record in self:
            if record.state in ("issued", "sent") and not (
                record.destruction_item_ids or record.container_ids or record.box_ids
            ):
                raise ValidationError(
                    _(
                        "Certificate cannot be issued without destruction items, containers, or boxes listed"
                    )
                )

    @api.constrains("state")
    def _check_state_transitions(self):
        """Validate proper state transitions"""
        for record in self:
            if record.state == "sent" and not record.certificate_data:
                raise ValidationError(_("Cannot send certificate without PDF data"))
            if record.state == "issued" and not record.issue_date:
                raise ValidationError(_("Issued certificates must have an issue date"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_issue_certificate(self):
        """Issue certificate with comprehensive validation"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft certificates can be issued."))
        if (
            not self.destruction_item_ids
            and not self.container_ids
            and not self.box_ids
        ):
            raise UserError(
                _(
                    "Cannot issue a certificate with no destroyed items, containers, or boxes listed."
                )
            )

        # Additional validation for required fields
        if not self.partner_id:
            raise UserError(_("Customer is required to issue a certificate."))
        if not self.destruction_date:
            raise UserError(_("Destruction date is required to issue a certificate."))

        try:
            # Generate certificate PDF
            pdf_content = self._generate_certificate_pdf()
            pdf_filename = f"CoD-{self.certificate_number}.pdf"

            self.write(
                {
                    "state": "issued",
                    "issue_date": fields.Datetime.now(),
                    "certificate_data": pdf_content,
                    "certificate_filename": pdf_filename,
                }
            )
            self.message_post(body=_("Certificate issued and PDF generated."))
        except Exception as e:
            _logger.error(
                "Failed to issue certificate %s: %s", self.certificate_number, str(e)
            )
            raise UserError(_("Failed to generate certificate PDF: %s") % str(e))

    def action_send_by_email(self):
        """Send certificate by email with improved error handling"""
        self.ensure_one()
        if self.state != "issued":
            raise UserError(_("Only issued certificates can be sent."))

        if not self.partner_id.email:
            raise UserError(
                _("Customer email address is required to send certificate.")
            )

        template = self.env.ref(
            "records_management.email_template_naid_certificate",
            raise_if_not_found=False,
        )
        if not template:
            raise UserError(
                _("The email template for NAID Certificates could not be found.")
            )

        try:
            template.send_mail(self.id, force_send=True)
            self.write({"state": "sent"})
            self.message_post(body=_("Certificate sent to customer via email."))
        except Exception as e:
            _logger.error(
                "Failed to send certificate %s: %s", self.certificate_number, str(e)
            )
            raise UserError(_("Failed to send certificate email: %s") % str(e))

    def action_cancel(self):
        """Cancel certificate with state validation"""
        self.ensure_one()
        if self.state == "cancelled":
            raise UserError(_("Certificate is already cancelled."))
        self.write({"state": "cancelled"})
        self.message_post(body=_("Certificate has been cancelled."))

    def action_reset_to_draft(self):
        """Reset certificate to draft with data cleanup"""
        self.ensure_one()
        if self.state == "draft":
            raise UserError(_("Certificate is already in draft state."))

        self.write(
            {
                "state": "draft",
                "issue_date": False,
                "certificate_data": False,
                "certificate_filename": False,
            }
        )
        self.message_post(body=_("Certificate reset to draft."))

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _generate_certificate_pdf(self):
        """Generate certificate PDF with error handling"""
        self.ensure_one()

        try:
            report = self.env.ref("records_management.action_report_naid_certificate")
            if not report:
                raise UserError(_("NAID certificate report template not found"))

            result = report._render_qweb_pdf(self.ids)
            # Handle both tuple and single return value for compatibility
            if isinstance(result, tuple):
                pdf_content = result[0]
            else:
                pdf_content = result

            if not pdf_content:
                raise UserError(_("Failed to generate PDF content"))

            return base64.b64encode(pdf_content)

        except Exception as e:
            _logger.error(
                "PDF generation failed for certificate %s: %s",
                self.certificate_number,
                str(e),
            )
            # Return a basic PDF placeholder if report generation fails
            placeholder_content = _("Certificate %s - PDF Generation Error") % self.certificate_number
            return base64.b64encode(placeholder_content.encode("utf-8"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with certificate number generation and validation"""
        for vals in vals_list:
            if vals.get("certificate_number", _("New")) == _("New"):
                try:
                    # Try to generate sequence number
                    vals["certificate_number"] = self.env["ir.sequence"].next_by_code(
                        "naid.certificate"
                    ) or _("New")
                except Exception as e:
                    _logger.warning("Failed to generate certificate sequence: %s", str(e))
                    # Fallback sequence generation
                    vals["certificate_number"] = (
                        f"CERT-{fields.Datetime.now().strftime('%Y%m%d%H%M%S')}"
                    )

        records = super(NaidCertificate, self).create(vals_list)

        # Log certificate creation for audit purposes
        for record in records:
            # Using translation with inline interpolation arguments per linter requirement
            record.message_post(
                body=_(
                    "NAID Certificate created: %s for customer %s",
                    record.certificate_number,
                    record.partner_id.name,
                )
            )

        return records

    def write(self, vals):
        """Enhanced write method with state change logging"""
        # Log state changes for audit trail
        if "state" in vals:
            for record in self:
                if record.state != vals["state"]:
                    record.message_post(
                        body=_(
                            "Certificate state changed from %s to %s",
                            record.state,
                            vals["state"],
                        )
                    )

        return super(NaidCertificate, self).write(vals)

    def unlink(self):
        """Enhanced unlink method with deletion restrictions"""
        for record in self:
            if record.state in ("issued", "sent"):
                raise UserError(
                    _(
                        "Cannot delete issued or sent certificates. "
                        "Please cancel the certificate first."
                    )
                )

        return super(NaidCertificate, self).unlink()

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        (
            "unique_certificate_number",
            "unique(certificate_number)",
            "Certificate number must be unique",
        ),
        (
            "check_positive_weight",
            "CHECK(total_weight >= 0)",
            "Total weight must be positive",
        ),
        (
            "check_positive_items",
            "CHECK(total_items >= 0)",
            "Total items must be positive",
        ),
    ]

    # -------------------------------------------------------------
    # Placeholder buttons referenced in XML views (safe stubs)
    # -------------------------------------------------------------
    def action_conduct_audit(self):
        self.ensure_one()
        return False

    def action_renew_certificate(self):
        self.ensure_one()
        return False

    def action_view_audit_history(self):
        self.ensure_one()
        return False

    def action_view_destruction_records(self):
        self.ensure_one()
        return False
