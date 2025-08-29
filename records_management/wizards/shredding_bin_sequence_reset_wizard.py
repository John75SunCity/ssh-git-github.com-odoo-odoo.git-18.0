# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class ShreddingBinSequenceResetWizard(models.TransientModel):
    _name = 'shredding.bin.sequence.reset.wizard'
    _description = 'Shredding Bin Sequence Reset Wizard'

    bin_size = fields.Selection([
        ('23', '23 Gallon Bin'),
        ('32_console', '32 Gallon Console'),
        ('32_bin', '32 Gallon Bin'),
        ('64', '64 Gallon Bin'),
        ('96', '96 Gallon Bin'),
    ], string='Bin Size', required=True)

    new_sequence_number = fields.Integer(
        string='New Starting Number',
        required=True,
        default=1,
        help="The next barcode will start from this number"
    )

    reset_reason = fields.Text(
        string='Reason for Reset',
        required=True,
        help="Please provide a reason for resetting the sequence (e.g., misprint, reorganization)"
    )

    current_sequence_number = fields.Integer(
        string='Current Next Number',
        readonly=True,
        compute='_compute_current_sequence'
    )

    sequence_code_mapping = {
        '23': 'shredding.bin.23gallon',
        '32_console': 'shredding.console.32gallon',
        '32_bin': 'shredding.bin.32gallon',
        '64': 'shredding.bin.64gallon',
        '96': 'shredding.bin.96gallon',
    }

    @api.depends('bin_size')
    def _compute_current_sequence(self):
        for record in self:
            if record.bin_size:
                sequence_code = record.sequence_code_mapping.get(record.bin_size)
                if sequence_code:
                    sequence = self.env['ir.sequence'].search([
                        ('code', '=', sequence_code)
                    ], limit=1)
                    record.current_sequence_number = sequence.number_next if sequence else 0
                else:
                    record.current_sequence_number = 0
            else:
                record.current_sequence_number = 0

    def action_reset_sequence(self):
        """Reset the sequence to the specified number with audit logging"""
        self.ensure_one()

        if not self.reset_reason.strip():
            raise UserError(_("Please provide a reason for the sequence reset."))

        if self.new_sequence_number < 1:
            raise UserError(_("Sequence number must be at least 1."))

        sequence_code = self.sequence_code_mapping.get(self.bin_size)
        if not sequence_code:
            raise UserError(_("Invalid bin size selected."))

        # Find the sequence
        sequence = self.env['ir.sequence'].search([
            ('code', '=', sequence_code)
        ], limit=1)

        if not sequence:
            raise UserError(_("Sequence not found for bin size %s") % dict(self._fields['bin_size'].selection)[self.bin_size])

        # Store old value for audit
        old_number = sequence.number_next

        # Update sequence
        sequence.write({
            'number_next': self.new_sequence_number
        })

        # Create audit log
        self.env['naid.audit.log'].create({
            'action': 'sequence_reset',
            'description': _("Bin sequence reset for %s from %s to %s. Reason: %s") % (
                dict(self._fields['bin_size'].selection)[self.bin_size],
                old_number,
                self.new_sequence_number,
                self.reset_reason
            ),
            'user_id': self.env.user.id,
            'date': fields.Datetime.now(),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Sequence Reset Complete"),
                'message': _("Bin sequence for %s has been reset to %s") % (
                    dict(self._fields['bin_size'].selection)[self.bin_size],
                    self.new_sequence_number
                ),
                'type': 'success',
                'sticky': False,
            }
        }
