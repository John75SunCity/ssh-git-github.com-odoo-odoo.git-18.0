# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class NAIDAuditVerificationWizard(models.TransientModel):
    _name = 'naid.audit.verification.wizard'
    _description = 'NAID Audit Verification Wizard'

    audit_requirement_id = fields.Many2one(
        comodel_name='naid.audit.requirement',
        string='Audit Requirement',
        required=True,
        readonly=True
    )

    checklist_category = fields.Selection(
        related='audit_requirement_id.checklist_category',
        string='Category',
        readonly=True
    )

    verification_notes = fields.Text(
        string='Verification Notes',
        required=True,
        help='Detailed notes about the verification process and findings'
    )

    verification_result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional Pass')
    ], string='Verification Result', required=True, default='pass')

    corrective_actions = fields.Text(
        string='Corrective Actions Required',
        help='If failed or conditional, describe required corrective actions'
    )

    follow_up_date = fields.Date(
        string='Follow-up Date',
        help='Date for follow-up verification if conditional or failed'
    )

    digital_signature = fields.Binary(
        string='Digital Signature',
        help='Digital signature for verification'
    )

    signature_name = fields.Char(
        string='Signature Name',
        help='Name of person providing signature'
    )

    @api.onchange('verification_result')
    def _onchange_verification_result(self):
        if self.verification_result in ['fail', 'conditional']:
            if not self.corrective_actions:
                self.corrective_actions = "Please specify corrective actions required."
        else:
            self.corrective_actions = False
            self.follow_up_date = False

    def action_verify(self):
        """Complete the verification process"""
        self.ensure_one()
        if not self.verification_notes:
            raise ValidationError(_("Verification notes are required."))

        # Update the requirement
        self.audit_requirement_id.write({
            'last_verified_by_id': self.env.user.id,
            'last_verified_date': fields.Datetime.now(),
            'last_audit_date': fields.Date.today(),
            'verification_notes': self.verification_notes,
            'status': 'completed' if self.verification_result == 'pass' else 'pending'
        })

        # Prepare audit log entry
        audit_log_vals = {
            'requirement_id': self.audit_requirement_id.id,
            'audit_date': fields.Date.today(),
            'auditor_id': self.env.user.id,
            'result': self.verification_result,
            'notes': self.verification_notes,
            'checklist_category': self.checklist_category,
        }
        if self.corrective_actions:
            audit_log_vals['corrective_actions'] = self.corrective_actions
        if self.follow_up_date:
            audit_log_vals['follow_up_date'] = self.follow_up_date
        if self.digital_signature:
            audit_log_vals['digital_signature'] = self.digital_signature
            audit_log_vals['signature_name'] = self.signature_name

        self.env['naid.audit.log'].create(audit_log_vals)
        return {'type': 'ir.actions.act_window_close'}
