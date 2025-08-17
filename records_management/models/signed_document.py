from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class SignedDocument(models.Model):
    _name = 'signed.document'
    _description = 'Signed Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'signature_date desc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean()
    request_id = fields.Many2one()
    document_type = fields.Selection()
    signature_date = fields.Datetime()
    signatory_name = fields.Char()
    signatory_email = fields.Char()
    signatory_title = fields.Char()
    signatory_ip_address = fields.Char()
    pdf_document = fields.Binary()
    pdf_filename = fields.Char()
    original_document = fields.Binary()
    original_filename = fields.Char()
    state = fields.Selection()
    signature_hash = fields.Char()
    document_hash = fields.Char()
    verification_status = fields.Selection()
    verification_date = fields.Datetime()
    verified_by_id = fields.Many2one()
    legal_validity_period = fields.Integer()
    expiry_date = fields.Date()
    compliance_notes = fields.Text()
    naid_compliant = fields.Boolean()
    display_name = fields.Char()
    is_expired = fields.Boolean()
    signature_age_days = fields.Integer()
    notes = fields.Text()
    internal_notes = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    today = fields.Date()
    expiry_date_limit = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name with signature info"""
            for record in self:
                if record.signatory_name and record.signature_date:
                    record.display_name = _()
                        "%s - Signed by %s", record.name, record.signatory_name

                elif record.signatory_name:
                    record.display_name = _("%s - %s", record.name, record.signatory_name)
                else:
                    record.display_name = record.name or _("New Signed Document")


    def _compute_expiry_date(self):
            """Compute signature expiry date"""
            for record in self:
                if record.signature_date and record.legal_validity_period > 0:
                    expiry_datetime = record.signature_date + timedelta()
                        days=record.legal_validity_period

                    record.expiry_date = expiry_datetime.date()
                else:
                    record.expiry_date = False


    def _compute_is_expired(self):
            """Check if signature has expired""":

    def _compute_signature_age_days(self):
            """Compute age of signature in days"""

    def action_request_signature(self):
            """Request signature from signatory"""
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft documents can be sent for signature")):
            self.write({"state": "pending_signature"})
            self.message_post(body=_("Document sent for signature")):
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
                self.write()
                    {}
                        "state": "verified",
                        "verification_status": "valid",
                        "verification_date": fields.Datetime.now(),
                        "verified_by_id": self.env.user.id,


                self.message_post(body=_("Signature verified successfully"))
            else:
                self.write()
                    {}
                        "verification_status": "invalid",
                        "verification_date": fields.Datetime.now(),
                        "verified_by_id": self.env.user.id,


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
                raise UserError(_("No signed document available for download")):
            return {}
                "type": "ir.actions.act_url",
                "url": "/web/content/%s/%s/pdf_document?download=true&filename=%s"
                % (self._name, self.id, self.pdf_filename or "signed_document.pdf"),
                "target": "self",


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def _perform_signature_verification(self):
            """Perform actual signature verification"""
            # Placeholder for signature verification logic:
            return True


    def _create_audit_log(self, action):
            """Create audit log entry"""
            self.env["signed.document.audit").create(]
                {}
                    "document_id": self.id,
                    "action": action,
                    "user_id": self.env.user.id,
                    "timestamp": fields.Datetime.now(),
                    "ip_address": self.env.context.get("request_ip"),
                    "details": _("Action: %s performed on document %s", action, self.name),



        # ============================================================================
            # CONSTRAINT METHODS
        # ============================================================================

    def _check_signature_date(self):
            """Validate signature date is not in the future"""
            for record in self:
                if record.signature_date and record.signature_date > fields.Datetime.now():
                    raise ValidationError(_("Signature date cannot be in the future"))


    def _check_signatory_email(self):
            """Validate signatory email format"""
            for record in self:
                if record.signatory_email and not re.match(:)
                    r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$",
                    record.signatory_email,

                    raise ValidationError(_("Please enter a valid email address"))


    def _check_validity_period(self):
            """Validate legal validity period"""
            for record in self:
                if record.legal_validity_period <= 0:
                    raise ValidationError()
                        _("Legal validity period must be greater than zero")


        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to generate sequence and audit logs"""
            for vals in vals_list:
                if not vals.get("name") or vals["name"] == "/":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("signed.document") or _("New")


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

    def get_expiring_signatures(self, days_ahead=30):
            """Get signatures expiring within specified days"""

    def cleanup_expired_signatures(self):
            """Archive expired signatures"""
            expired = self.search()
                [("state", "in", ["signed", "verified"]), ("is_expired", "=", True)]

            for doc in expired:
                doc.message_post(body=_("Signature expired - document archived"))
                doc.write({"state": "archived"})
