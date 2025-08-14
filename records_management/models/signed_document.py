# -*- coding: utf-8 -*-
"""
Signed Document Management Module

This module handles digitally signed documents in the Records Management System,
providing comprehensive e-signature tracking, verification, and audit trails
with complete NAID compliance integration.
"""
import re
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SignedDocument(models.Model):
    _name = "signed.document"
    _description = "Signed Document"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "signature_date desc, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Document Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the signed document",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        help="Company associated with this signed document",
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this signed document",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Active status of the signed document",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    request_id = fields.Many2one(
        "portal.request",
        string="Portal Request",
        required=True,
        ondelete="cascade",
        tracking=True,
        help="Portal request that generated this signed document",
    )

    # ============================================================================
    # DOCUMENT CLASSIFICATION
    # ============================================================================
    document_type = fields.Selection(
        [
            ("destruction_request", "Destruction Request"),
            ("service_agreement", "Service Agreement"),
            ("certificate", "Certificate"),
            ("authorization", "Authorization"),
            ("pickup_authorization", "Pickup Authorization"),
            ("chain_of_custody", "Chain of Custody"),
            ("naid_certificate", "NAID Certificate"),
        ],
        string="Document Type",
        required=True,
        tracking=True,
        help="Type of signed document",
    )

    # ============================================================================
    # SIGNATURE INFORMATION
    # ============================================================================
    signature_date = fields.Datetime(
        string="Signature Date",
        tracking=True,
        index=True,
        help="Date and time when document was signed",
    )
    signatory_name = fields.Char(
        string="Signatory Name",
        tracking=True,
        help="Full name of the person who signed",
    )
    signatory_email = fields.Char(
        string="Signatory Email",
        tracking=True,
        help="Email address of the signatory",
    )
    signatory_title = fields.Char(
        string="Signatory Title",
        tracking=True,
        help="Job title or position of the signatory",
    )
    signatory_ip_address = fields.Char(
        string="Signatory IP Address",
        help="IP address from which document was signed",
    )

    # ============================================================================
    # DOCUMENT STORAGE
    # ============================================================================
    pdf_document = fields.Binary(
        string="PDF Document",
        attachment=True,
        help="Signed PDF document file",
    )
    pdf_filename = fields.Char(
        string="PDF Filename",
        help="Original filename of the PDF document",
    )
    original_document = fields.Binary(
        string="Original Document",
        attachment=True,
        help="Original unsigned document for comparison",
    )
    original_filename = fields.Char(
        string="Original Filename",
        help="Filename of the original document",
    )

    # ============================================================================
    # WORKFLOW MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_signature", "Pending Signature"),
            ("signed", "Signed"),
            ("verified", "Verified"),
            ("archived", "Archived"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
        help="Current status of the signed document",
    )

    # ============================================================================
    # SECURITY AND VERIFICATION
    # ============================================================================
    signature_hash = fields.Char(
        string="Signature Hash",
        help="Cryptographic hash of the signature for verification",
    )
    document_hash = fields.Char(
        string="Document Hash",
        help="Hash of the complete signed document",
    )
    verification_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("valid", "Valid"),
            ("invalid", "Invalid"),
            ("expired", "Expired"),
        ],
        string="Verification Status",
        default="pending",
        tracking=True,
        help="Status of signature verification",
    )
    verification_date = fields.Datetime(
        string="Verification Date",
        help="Date when signature was last verified",
    )
    verified_by_id = fields.Many2one(
        "res.users",
        string="Verified By",
        help="User who verified the signature",
    )

    # ============================================================================
    # LEGAL AND COMPLIANCE
    # ============================================================================
    legal_validity_period = fields.Integer(
        string="Legal Validity Period (Days)",
        default=2555,  # 7 years default
        help="Number of days the signature remains legally valid",
    )
    expiry_date = fields.Date(
        string="Signature Expiry Date",
        compute="_compute_expiry_date",
        store=True,
        help="Date when signature expires",
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes related to legal compliance and requirements",
    )

    # ============================================================================
    # NAID COMPLIANCE INTEGRATION
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether this signature meets NAID requirements",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for this signed document",
    )
    is_expired = fields.Boolean(
        string="Is Expired",
        compute="_compute_is_expired",
        help="Whether the signature has expired",
    )
    signature_age_days = fields.Integer(
        string="Signature Age (Days)",
        compute="_compute_signature_age_days",
        help="Number of days since signature",
    )

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    notes = fields.Text(
        string="Notes",
        help="Additional notes or comments about the signed document",
    )
    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes not visible to customers",
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "signatory_name", "signature_date")
    def _compute_display_name(self):
        """Compute display name with signature info"""
        for record in self:
            if record.signatory_name and record.signature_date:
                record.display_name = _(
                    "%s - Signed by %s", record.name, record.signatory_name
                )
            elif record.signatory_name:
                record.display_name = _("%s - %s", record.name, record.signatory_name)
            else:
                record.display_name = record.name or _("New Signed Document")

    @api.depends("signature_date", "legal_validity_period")
    def _compute_expiry_date(self):
        """Compute signature expiry date"""
        for record in self:
            if record.signature_date and record.legal_validity_period > 0:
                expiry_datetime = record.signature_date + timedelta(
                    days=record.legal_validity_period
                )
                record.expiry_date = expiry_datetime.date()
            else:
                record.expiry_date = False

    @api.depends("expiry_date")
    def _compute_is_expired(self):
        """Check if signature has expired"""
        today = fields.Date.today()
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < today

    @api.depends("signature_date")
    def _compute_signature_age_days(self):
        """Compute age of signature in days"""
        today = fields.Date.today()
        for record in self:
            if record.signature_date:
                delta = today - record.signature_date.date()
                record.signature_age_days = delta.days
            else:
                record.signature_age_days = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_request_signature(self):
        """Request signature from signatory"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft documents can be sent for signature"))

        self.write({"state": "pending_signature"})
        self.message_post(body=_("Document sent for signature"))
        self._create_audit_log("signature_requested")

    def action_mark_signed(self):
        """Mark document as signed"""
        self.ensure_one()
        if self.state != "pending_signature":
            raise UserError(_("Only pending documents can be marked as signed"))

        if not self.signatory_name:
            raise UserError(_("Please specify the signatory name"))

        self.write({"state": "signed", "signature_date": fields.Datetime.now()})
        self.message_post(body=_("Document signed by %s", self.signatory_name))
        self._create_audit_log("document_signed")

    def action_verify_signature(self):
        """Verify document signature"""
        self.ensure_one()
        if self.state != "signed":
            raise UserError(_("Only signed documents can be verified"))

        verification_result = self._perform_signature_verification()

        if verification_result:
            self.write(
                {
                    "state": "verified",
                    "verification_status": "valid",
                    "verification_date": fields.Datetime.now(),
                    "verified_by_id": self.env.user.id,
                }
            )
            self.message_post(body=_("Signature verified successfully"))
        else:
            self.write(
                {
                    "verification_status": "invalid",
                    "verification_date": fields.Datetime.now(),
                    "verified_by_id": self.env.user.id,
                }
            )
            self.message_post(body=_("Signature verification failed"))

        self._create_audit_log("signature_verified")

    def action_archive_document(self):
        """Archive the signed document"""
        self.ensure_one()
        if self.state not in ["signed", "verified"]:
            raise UserError(_("Only signed or verified documents can be archived"))

        self.write({"state": "archived"})
        self.message_post(body=_("Document archived"))
        self._create_audit_log("document_archived")

    def action_reject_signature(self):
        """Reject the signature"""
        self.ensure_one()
        if self.state not in ["pending_signature", "signed"]:
            raise UserError(_("Cannot reject document in current state"))

        self.write({"state": "rejected", "verification_status": "invalid"})
        self.message_post(body=_("Document signature rejected"))
        self._create_audit_log("signature_rejected")

    def action_download_signed_document(self):
        """Download the signed PDF document"""
        self.ensure_one()
        if not self.pdf_document:
            raise UserError(_("No signed document available for download"))

        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s/%s/pdf_document?download=true&filename=%s"
            % (self._name, self.id, self.pdf_filename or "signed_document.pdf"),
            "target": "self",
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _perform_signature_verification(self):
        """Perform actual signature verification"""
        # Placeholder for signature verification logic
        return True

    def _create_audit_log(self, action):
        """Create audit log entry"""
        self.env["signed.document.audit"].create(
            {
                "document_id": self.id,
                "action": action,
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now(),
                "ip_address": self.env.context.get("request_ip"),
                "details": _("Action: %s performed on document %s", action, self.name),
            }
        )

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains("signature_date")
    def _check_signature_date(self):
        """Validate signature date is not in the future"""
        for record in self:
            if record.signature_date and record.signature_date > fields.Datetime.now():
                raise ValidationError(_("Signature date cannot be in the future"))

    @api.constrains("signatory_email")
    def _check_signatory_email(self):
        """Validate signatory email format"""
        for record in self:
            if record.signatory_email and not re.match(
                r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                record.signatory_email,
            ):
                raise ValidationError(_("Please enter a valid email address"))

    @api.constrains("legal_validity_period")
    def _check_validity_period(self):
        """Validate legal validity period"""
        for record in self:
            if record.legal_validity_period <= 0:
                raise ValidationError(
                    _("Legal validity period must be greater than zero")
                )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence and audit logs"""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("signed.document") or _("New")
                )

        documents = super().create(vals_list)

        for document in documents:
            document._create_audit_log("document_created")

        return documents

    def write(self, vals):
        """Override write to track changes"""
        res = super().write(vals)
        if "state" in vals:
            for record in self:
                record._create_audit_log("state_changed")
        return res

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    @api.model
    def get_expiring_signatures(self, days_ahead=30):
        """Get signatures expiring within specified days"""
        expiry_date_limit = fields.Date.today() + timedelta(days=days_ahead)
        return self.search(
            [
                ("state", "in", ["signed", "verified"]),
                ("expiry_date", "<=", expiry_date_limit),
                ("expiry_date", ">=", fields.Date.today()),
            ]
        )

    @api.model
    def cleanup_expired_signatures(self):
        """Archive expired signatures"""
        expired = self.search(
            [("state", "in", ["signed", "verified"]), ("is_expired", "=", True)]
        )
        for doc in expired:
            doc.message_post(body=_("Signature expired - document archived"))
            doc.write({"state": "archived"})
