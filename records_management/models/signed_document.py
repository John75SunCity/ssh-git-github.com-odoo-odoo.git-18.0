import re
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class SignedDocument(models.Model):
    _name = 'signed.document'
    _description = 'Signed Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'signature_date desc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Document Name", required=True, copy=False, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    partner_id = fields.Many2one('res.partner', string="Customer", related='request_id.partner_id', store=True, readonly=True)
    active = fields.Boolean(default=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    # ============================================================================
    # RELATIONSHIP & DOCUMENT DETAILS
    # ============================================================================
    request_id = fields.Many2one('portal.request', string="Related Request", ondelete='cascade')
    document_type = fields.Selection([
        ('destruction_certificate', 'Destruction Certificate'),
        ('service_agreement', 'Service Agreement'),
        ('pickup_confirmation', 'Pickup Confirmation'),
        ('other', 'Other')
    ], string="Document Type", required=True, default='other')
    
    pdf_document = fields.Binary(string="Signed PDF", attachment=True, required=True)
    pdf_filename = fields.Char(string="PDF Filename")
    original_document = fields.Binary(string="Original Document", attachment=True)
    original_filename = fields.Char(string="Original Filename")

    # ============================================================================
    # STATE & SIGNATURE DETAILS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_signature', 'Pending Signature'),
        ('signed', 'Signed'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
        ('archived', 'Archived')
    ], string="Status", default='draft', required=True, tracking=True)
    
    signature_date = fields.Datetime(string="Signature Date", readonly=True)
    signatory_name = fields.Char(string="Signatory Name", tracking=True)
    signatory_email = fields.Char(string="Signatory Email", tracking=True)
    signatory_title = fields.Char(string="Signatory Title")
    signatory_ip_address = fields.Char(string="Signatory IP Address", readonly=True)

    # ============================================================================
    # HASHING & VERIFICATION
    # ============================================================================
    signature_hash = fields.Char(string="Signature Hash", readonly=True, copy=False)
    document_hash = fields.Char(string="Document Hash", readonly=True, copy=False)
    verification_status = fields.Selection([
        ('not_verified', 'Not Verified'),
        ('valid', 'Valid'),
        ('invalid', 'Invalid')
    ], string="Verification Status", default='not_verified', tracking=True)
    verification_date = fields.Datetime(string="Verification Date", readonly=True)
    verified_by_id = fields.Many2one('res.users', string="Verified By", readonly=True)

    # ============================================================================
    # LEGAL & COMPLIANCE
    # ============================================================================
    legal_validity_period = fields.Integer(string="Validity Period (Days)", default=365)
    expiry_date = fields.Date(string="Expiry Date", compute='_compute_expiry_date', store=True)
    is_expired = fields.Boolean(string="Is Expired", compute='_compute_is_expired', store=True)
    signature_age_days = fields.Integer(string="Signature Age (Days)", compute='_compute_signature_age_days', store=True)
    compliance_notes = fields.Text(string="Compliance Notes")
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)
    notes = fields.Text(string="Notes")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'signatory_name', 'signature_date')
    def _compute_display_name(self):
        for record in self:
            if record.signatory_name and record.signature_date:
                record.display_name = _("%s - Signed by %s") % (record.name, record.signatory_name)
            elif record.signatory_name:
                record.display_name = _("%s - %s") % (record.name, record.signatory_name)
            else:
                record.display_name = record.name or _("New Signed Document")

    @api.depends('signature_date', 'legal_validity_period')
    def _compute_expiry_date(self):
        for record in self:
            if record.signature_date and record.legal_validity_period > 0:
                expiry_datetime = record.signature_date + timedelta(days=record.legal_validity_period)
                record.expiry_date = expiry_datetime.date()
            else:
                record.expiry_date = False

    @api.depends('expiry_date')
    def _compute_is_expired(self):
        for record in self:
            record.is_expired = record.expiry_date and record.expiry_date < fields.Date.today()

    @api.depends('signature_date')
    def _compute_signature_age_days(self):
        for record in self:
            if record.signature_date:
                age = fields.Datetime.now() - record.signature_date
                record.signature_age_days = age.days
            else:
                record.signature_age_days = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_request_signature(self):
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft documents can be sent for signature."))
        self.write({"state": "pending_signature"})
        self.message_post(body=_("Document sent for signature."))
        self._create_audit_log("signature_requested")

    def action_mark_signed(self):
        self.ensure_one()
        if self.state != "pending_signature":
            raise UserError(_("Only pending documents can be marked as signed."))
        if not self.signatory_name:
            raise UserError(_("Please specify the signatory name."))
        self.write({"state": "signed", "signature_date": fields.Datetime.now()})
        self.message_post(body=_("Document signed by %s") % self.signatory_name)
        self._create_audit_log("document_signed")

    def action_verify_signature(self):
        self.ensure_one()
        if self.state != "signed":
            raise UserError(_("Only signed documents can be verified."))
        
        verification_result = self._perform_signature_verification()
        
        if verification_result:
            self.write({
                "state": "verified",
                "verification_status": "valid",
                "verification_date": fields.Datetime.now(),
                "verified_by_id": self.env.user.id,
            })
            self.message_post(body=_("Signature verified successfully."))
        else:
            self.write({
                "verification_status": "invalid",
                "verification_date": fields.Datetime.now(),
                "verified_by_id": self.env.user.id,
            })
            self.message_post(body=_("Signature verification failed."))
        self._create_audit_log("signature_verified")

    def action_archive_document(self):
        self.ensure_one()
        if self.state not in ["signed", "verified"]:
            raise UserError(_("Only signed or verified documents can be archived."))
        self.write({"state": "archived", "active": False})
        self.message_post(body=_("Document archived."))
        self._create_audit_log("document_archived")

    def action_reject_signature(self):
        self.ensure_one()
        if self.state not in ["pending_signature", "signed"]:
            raise UserError(_("Cannot reject document in current state."))
        self.write({"state": "rejected", "verification_status": "invalid"})
        self.message_post(body=_("Document signature rejected."))
        self._create_audit_log("signature_rejected")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _perform_signature_verification(self):
        """Perform actual signature verification. Placeholder for now."""
        return True

    def _create_audit_log(self, action, details=None):
        """Create an audit log entry using the dedicated audit model."""
        for record in self:
            before_state = self.env.context.get('old_state')
            self.env['signed.document.audit'].log_action(
                document_id=record.id,
                action=action,
                details=details,
                before_state=before_state,
                after_state=record.state if before_state else None
            )

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains('signature_date')
    def _check_signature_date(self):
        for record in self:
            if record.signature_date and record.signature_date > fields.Datetime.now():
                raise ValidationError(_("Signature date cannot be in the future."))

    @api.constrains('signatory_email')
    def _check_signatory_email(self):
        for record in self:
            if record.signatory_email and not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", record.signatory_email):
                raise ValidationError(_("Please enter a valid email address for the signatory."))

    @api.constrains('legal_validity_period')
    def _check_validity_period(self):
        for record in self:
            if record.legal_validity_period < 0:
                raise ValidationError(_("Legal validity period cannot be negative."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('signed.document') or _('New')
        
        documents = super().create(vals_list)
        documents._create_audit_log("document_created")
        return documents

    def write(self, vals):
        old_states = {rec: rec.state for rec in self} if 'state' in vals else {}
        res = super().write(vals)
        if "state" in vals:
            for record in self:
                details = _('State changed from %s to %s', old_states.get(record, 'N/A'), record.state)
                self.with_context(old_state=old_states.get(record))._create_audit_log(
                    "state_changed",
                    details=details
                )
        return res
