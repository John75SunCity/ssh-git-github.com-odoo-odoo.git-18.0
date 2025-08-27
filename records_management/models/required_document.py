from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date


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
    is_required = fields.Boolean(string='Required', default=True, tracking=True)
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
    @api.depends('expiration_date')
    def _compute_is_expired(self):
        """Check if the document is expired."""
        today = date.today()
        for doc in self:
            doc.is_expired = doc.expiration_date and doc.expiration_date < today
            if doc.is_expired and doc.state == 'verified':
                doc.state = 'expired'

    @api.depends('res_model', 'res_id')
    def _compute_related_record(self):
        for record in self:
            if record.res_model and record.res_id:
                record.related_record = f"{record.res_model},{record.res_id}"
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

    def action_verify(self):
        """Mark document as verified."""
        self.ensure_one()
        self.write({
            'state': 'verified',
            'verified_by_id': self.env.user.id,
            'verification_date': fields.Datetime.now()
        })
        self.message_post(body=_("Document verified by %s.") % self.env.user.name)

    def action_reject(self):
        """Mark document as rejected."""
        # This would typically open a wizard to ask for a rejection reason.
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Document rejected."))

    def action_reset_to_pending(self):
        """Reset the document back to the pending state."""
        self.ensure_one()
        self.write({
            'state': 'pending',
            'verified_by_id': False,
            'verification_date': False,
        })
        self.message_post(body=_("Document reset to pending."))

    # ============================================================================
    # AUTOMATED ACTIONS (CRON)
    # ============================================================================
    @api.model
    def _cron_check_expirations(self):
        """
        Scheduled action to check for documents that have expired or are expiring soon.
        """
        expired_docs = self.search([('state', '=', 'verified'), ('is_expired', '=', True)])
        if expired_docs:
            expired_docs.write({'state': 'expired'})
            for doc in expired_docs:
                doc.message_post(body=_("This document has expired."))
                # Optionally, create an activity for follow-up
                doc.activity_schedule(
                    'mail.mail_activity_data_todo',
                    summary=_('Expired Document: %s') % doc.name,
                    note=_('Please upload a new version of this required document.'),
                    user_id=doc.create_uid.id # Notify the creator
                )
