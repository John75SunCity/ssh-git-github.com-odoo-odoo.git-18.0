from datetime import date
from odoo import _, api, fields, models
from odoo.exceptions import UserError


class RequiredDocument(models.Model):
    _name = 'required.document'
    _description = 'Required Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Document Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # Generic relation to link this to any model (e.g., res.partner, records.destruction)
    res_model = fields.Char(string="Related Model", readonly=True, index=True)
    res_id = fields.Integer(string="Related Record ID", readonly=True, index=True)
    related_record = fields.Reference(selection='_selection_related_models', string="Related To", compute='_compute_related_record', readonly=True)

    # ============================================================================
    # DOCUMENT DETAILS & LIFECYCLE
    # ============================================================================
    document_type_id = fields.Many2one('records.document.type', string="Document Type", tracking=True)
    is_required = fields.Boolean(string='Required', default=True)
    state = fields.Selection([
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('verified', 'Verified'),
        ('expired', 'Expired'),
        ('rejected', 'Rejected'),
    ], string="Status", default='pending', required=True, tracking=True)

    expiration_date = fields.Date(string='Expiration Date', tracking=True)
    is_expired = fields.Boolean(string="Is Expired", compute='_compute_is_expired', store=True)

    # ============================================================================
    # ATTACHMENT & VERIFICATION
    # ============================================================================
    document_file = fields.Binary(string='Document File', attachment=True)
    document_filename = fields.Char(string='Document Filename')
    verified_by_id = fields.Many2one('res.users', string="Verified By", readonly=True, tracking=True)
    verification_date = fields.Datetime(string='Verification Date', readonly=True, tracking=True)
    notes = fields.Text(string='Notes')

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    def _sanitize_related_reference(self, value):
        """Defensive helper: always return (model, id) tuple or False."""
        if isinstance(value, tuple) and len(value) == 2:
            return value
        if isinstance(value, str) and ',' in value:
            model_part, id_part = value.split(',', 1)
            try:
                return (model_part.strip(), int(id_part.strip()))
            except ValueError:
                return False
        return False

    @api.depends('expiration_date')
    def _compute_is_expired(self):
        """Compute helper marking documents as expired in memory (state change handled elsewhere)."""
        today = date.today()
        for doc in self:
            doc.is_expired = bool(doc.expiration_date and doc.expiration_date < today)
            if doc.is_expired and doc.state == 'verified':
                # State transition deferred to scheduled job for batch consistency
                pass

    @api.depends('res_model', 'res_id')
    def _compute_related_record(self):
        """Ensure Reference field gets a tuple, never a raw string."""
        for record in self:
            if record.res_model and record.res_id:
                record.related_record = (record.res_model, record.res_id)
            else:
                record.related_record = False

    @api.model
    def _selection_related_models(self):
        """Provide a selection of models that can have required documents."""
        return [
            ('res.partner', 'Customer'),
            ('res.users', 'User'),
            ('records.destruction', 'Destruction Order'),
            ('maintenance.equipment', 'Equipment'),
        ]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        """Mark document as submitted for verification."""
        self.ensure_one()
        if not self.document_file:
            raise UserError(_("You must upload a document file before submitting."))
        self.write({'state': 'submitted'})
        self.message_post(body=_("Document submitted for verification."))
        return True

    def action_verify(self):
        """Mark document as verified."""
        self.ensure_one()
        self.write({
            'state': 'verified',
            'verified_by_id': self.env.user.id,
            'verification_date': fields.Datetime.now()
        })
        # Project translation policy: interpolate after _()
        self.message_post(body=_("Document verified by %s.") % self.env.user.name)
        return True

    def action_reject(self):
        """Mark document as rejected."""
        # This would typically open a wizard to ask for a rejection reason.
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Document rejected."))
        return True

    def action_reset_to_pending(self):
        """Reset the document back to the pending state."""
        self.ensure_one()
        self.write({
            'state': 'pending',
            'verified_by_id': False,
            'verification_date': False,
        })
        self.message_post(body=_("Document reset to pending."))
        return True

    # ============================================================================
    # AUTOMATED ACTIONS (CRON)
    # ============================================================================
    @api.model
    def _check_expirations(self):
        """
        Scheduled expiration enforcement (called by ir.cron 'ir_cron_required_document_expiration').

        Purpose:
            Batch-process verified required documents whose expiration_date is in the past.

        Logic:
            1. Recompute (normal dependency flow ensures is_expired is up to date).
            2. Search all documents still in state 'verified' and flagged is_expired.
            3. Transition them to state 'expired'.
            4. Post a chatter note and schedule a follow-up activity for the creator.

        Side Effects:
            - Updates 'state' to 'expired'.
            - Creates mail.message entries (audit trail).
            - Schedules mail.activity todos for renewal.

        Idempotency:
            Safe to run multiple times; already expired documents are not reprocessed.

        Returns:
            None
        """
        expired_docs = self.search([('state', '=', 'verified'), ('is_expired', '=', True)])
        if not expired_docs:
            return
        expired_docs.write({'state': 'expired'})
        for doc in expired_docs:
            doc.message_post(body=_("This document has expired."))
            doc.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Expired Document: %s") % doc.name,
                note=_("Please upload a new version of this required document."),
                user_id=doc.create_uid.id,
            )
