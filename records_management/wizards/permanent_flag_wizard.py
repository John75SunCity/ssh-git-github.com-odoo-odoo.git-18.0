# -*- coding: utf-8 -*-
from odoo import models, fields, api


class RecordsPermanentFlagWizard(models.TransientModel):
    _name = 'records.permanent.flag.wizard'
    _description = 'Records Permanent Flag Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Core fields matching view expectations
    operation_type = fields.Selection([
        ('set', 'Set Permanent Flag'),
        ('remove', 'Remove Permanent Flag')
    ], string='Operation Type', required=True, default='set', tracking=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='State', default='draft', tracking=True)

    document_count = fields.Integer(
        string='Document Count',
        compute='_compute_document_count',
        store=True
    )

    container_ids = fields.Many2many(
        'records.container',
        string='Containers',
        help='Containers to apply permanent flag operation'
    )

    document_ids = fields.Many2many(
        'records.document',
        string='Documents',
        help='Documents to apply permanent flag operation'
    )

    reason = fields.Text(
        string='Reason',
        help='Reason for permanent flag operation'
    )

    confirm = fields.Boolean(
        string='Confirm Operation',
        help='Confirm that you want to proceed with this operation'
    )

    @api.depends('document_ids', 'container_ids')
    def _compute_document_count(self):
        for wizard in self:
            doc_count = len(wizard.document_ids)
            # Add documents from containers
            for container in wizard.container_ids:
                doc_count += len(container.document_ids) if hasattr(container, 'document_ids') else 0
            wizard.document_count = doc_count

    def action_apply_changes(self):
        """Execute the permanent flag operation."""
        self.ensure_one()

        if not self.confirm:
            raise models.UserError('Please confirm the operation before proceeding.')

        self.state = 'in_progress'

        # Apply permanent flag to documents
        if self.document_ids:
            if self.operation_type == 'set':
                self.document_ids.write({'permanent_flag': True})
            else:
                self.document_ids.write({'permanent_flag': False})

        # Apply permanent flag to documents in containers
        if self.container_ids:
            for container in self.container_ids:
                if hasattr(container, 'document_ids'):
                    if self.operation_type == 'set':
                        container.document_ids.write({'permanent_flag': True})
                    else:
                        container.document_ids.write({'permanent_flag': False})

        self.state = 'done'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Success',
                'message': f'Permanent flag operation completed for {self.document_count} documents.',
                'type': 'success',
                'sticky': False,
            }
        }
