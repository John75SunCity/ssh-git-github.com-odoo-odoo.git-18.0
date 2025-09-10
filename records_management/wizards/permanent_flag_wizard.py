# -*- coding: utf-8 -*-
from odoo import models, fields, api



class PermanentFlagWizard(models.TransientModel):
    _name = 'records.permanent.flag.wizard'
    _description = 'Records Permanent Flag Wizard'

    # Core fields
    action_type = fields.Selection([
        ('mark', 'Mark as Permanent'),
        ('unmark', 'Remove Permanent Flag')
    ], string='Action', required=True, default='mark')

    document_ids = fields.Many2many(
        'records.document',
        string='Documents',
        required=True
    )

    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count'
    )

    user_password = fields.Char(
        string='Password',
        required=True
    )

    @api.depends('document_ids')
    def _compute_document_count(self):
        for wizard in self:
            wizard.document_count = len(wizard.document_ids)

    # Action method
    def action_confirm(self):
        """Execute the wizard action."""
        self.ensure_one()

        # Here you would implement the logic to mark/unmark documents as permanent
        # For now, just close the wizard
        return {'type': 'ir.actions.act_window_close'}
