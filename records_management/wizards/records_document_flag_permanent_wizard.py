from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsDocumentFlagPermanentWizard(models.TransientModel):
    _name = 'records.document.flag.permanent.wizard'
    _description = 'Flag Document as Permanent Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    document_id = fields.Many2one(
        comodel_name='records.document',
        string='Document',
        required=True,
        readonly=True
    )
    document_name = fields.Char(
        related='document_id.name',
        string='Document Name',
        readonly=True
    )
    document_reference = fields.Char(
        related='document_id.reference',
        string='Document Reference',
        readonly=True
    )
    current_state = fields.Selection(
        related='document_id.state',
        string='Current State',
        readonly=True
    )
    permanent_reason = fields.Text(
        string='Reason for Permanent Flag',
        required=True,
        help='Provide a detailed reason why this document should be flagged as permanent and exempt from destruction policies.'
    )
    confirm_action = fields.Boolean(
        string='I confirm this document should be permanent',
        help='Check this box to confirm you want to flag this document as permanent'
    )

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('permanent_reason')
    def _check_permanent_reason(self):
        """Ensure permanent reason is provided and meaningful"""
        for wizard in self:
            if not wizard.permanent_reason or len(wizard.permanent_reason.strip()) < 10:
                raise ValidationError(_("Please provide a detailed reason (at least 10 characters) for flagging this document as permanent."))

    @api.constrains('confirm_action')
    def _check_confirmation(self):
        """Ensure user has confirmed the action"""
        for wizard in self:
            if not wizard.confirm_action:
                raise ValidationError(_("Please confirm that you want to flag this document as permanent."))

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_flag_permanent(self):
        """Flag the document as permanent with the provided reason"""
        self.ensure_one()

        # Validate document exists and is not already permanent
        if not self.document_id:
            raise ValidationError(_("No document selected."))

        if self.document_id.is_permanent:
            raise ValidationError(_("Document '%s' is already flagged as permanent.") % self.document_id.name)

        # Check if document is in a state that allows permanent flagging
        if self.document_id.state in ('destroyed',):
            raise ValidationError(_("Cannot flag a destroyed document as permanent."))

        # Update the document
        self.document_id.write({
            'is_permanent': True,
            'permanent_reason': self.permanent_reason,
            'permanent_user_id': self.env.user.id,
            'permanent_date': fields.Datetime.now(),
        })

        # Log the action in chatter
        self.document_id.message_post(
            body=_("Document flagged as PERMANENT by %s.<br/><strong>Reason:</strong> %s") % (
                self.env.user.name,
                self.permanent_reason
            ),
            subject=_("Document Flagged as Permanent"),
            message_type='notification'
        )

        # Create audit log entry
        if hasattr(self.env, 'naid.audit.log'):
            self.env["naid.audit.log"].sudo().create(
                {
                    "document_id": self.document_id.id,
                    "event_type": "permanent_flag",
                    "event_description": _(
                        "Document flagged as permanent: %s",
                        self.permanent_reason,
                    ),
                    "user_id": self.env.user.id,
                    "event_date": fields.Datetime.now(),
                }
            )

        # Return success notification
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Document '%s' has been flagged as permanent and is now exempt from destruction policies.") % self.document_id.name,
                'sticky': False,
                'type': 'success',
            }
        }

    def action_cancel(self):
        """Cancel the wizard without making changes"""
        return {'type': 'ir.actions.act_window_close'}
