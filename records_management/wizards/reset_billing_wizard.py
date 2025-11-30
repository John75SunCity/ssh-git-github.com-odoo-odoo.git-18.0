# -*- coding: utf-8 -*-
"""
Reset Billing Wizard

Wizard for resetting billing status on work orders so they can be re-billed.
Useful when invoices were created by mistake or need to be regenerated.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ResetBillingWizard(models.TransientModel):
    """
    Wizard for resetting billing status on work orders.
    
    Allows users to:
    - Select specific work orders to reset
    - Preview which work orders will be affected
    - Optionally delete associated draft invoices
    """
    _name = 'reset.billing.wizard'
    _description = 'Reset Billing Status Wizard'

    # ============================================================================
    # CONFIGURATION
    # ============================================================================
    work_order_type = fields.Selection([
        ('retrieval', 'Retrieval Work Orders'),
        ('shredding', 'Shredding Work Orders'),
        ('all', 'All Work Order Types'),
    ], string='Work Order Type', default='all', required=True)

    delete_draft_invoices = fields.Boolean(
        string='Delete Draft Invoices',
        default=False,
        help='If checked, draft invoices linked to these work orders will be deleted. '
             'Posted invoices will NOT be deleted - only unlinked.'
    )

    # ============================================================================
    # WORK ORDER SELECTIONS
    # ============================================================================
    retrieval_order_ids = fields.Many2many(
        comodel_name='work.order.retrieval',
        relation='reset_billing_wizard_retrieval_rel',
        column1='wizard_id',
        column2='order_id',
        string='Retrieval Work Orders',
        domain=[('invoice_id', '!=', False)]
    )

    shredding_order_ids = fields.Many2many(
        comodel_name='work.order.shredding',
        relation='reset_billing_wizard_shredding_rel',
        column1='wizard_id',
        column2='order_id',
        string='Shredding Work Orders',
        domain=[('invoice_id', '!=', False)]
    )

    # ============================================================================
    # PREVIEW / SUMMARY
    # ============================================================================
    preview_html = fields.Html(
        string='Preview',
        compute='_compute_preview',
        readonly=True
    )

    total_orders = fields.Integer(
        string='Total Orders to Reset',
        compute='_compute_totals'
    )

    total_invoices = fields.Integer(
        string='Linked Invoices',
        compute='_compute_totals'
    )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model
    def default_get(self, fields_list):
        """Pre-populate with selected work orders from context"""
        res = super().default_get(fields_list)

        # Check if called from work order retrieval tree view
        active_model = self.env.context.get('active_model')
        active_ids = self.env.context.get('active_ids', [])

        if active_model == 'work.order.retrieval' and active_ids:
            res['retrieval_order_ids'] = [(6, 0, active_ids)]
            res['work_order_type'] = 'retrieval'
        elif active_model == 'work.order.shredding' and active_ids:
            res['shredding_order_ids'] = [(6, 0, active_ids)]
            res['work_order_type'] = 'shredding'

        return res

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('retrieval_order_ids', 'shredding_order_ids')
    def _compute_totals(self):
        """Compute summary totals"""
        for wizard in self:
            wizard.total_orders = len(wizard.retrieval_order_ids) + len(wizard.shredding_order_ids)

            # Count unique invoices
            invoice_ids = set()
            for order in wizard.retrieval_order_ids:
                if order.invoice_id:
                    invoice_ids.add(order.invoice_id.id)
            for order in wizard.shredding_order_ids:
                if order.invoice_id:
                    invoice_ids.add(order.invoice_id.id)

            wizard.total_invoices = len(invoice_ids)

    @api.depends('retrieval_order_ids', 'shredding_order_ids', 'delete_draft_invoices')
    def _compute_preview(self):
        """Generate HTML preview of reset operation"""
        for wizard in self:
            html = '<div class="alert alert-info">'
            html += f'<strong>Summary:</strong> {wizard.total_orders} work order(s) will be reset for re-billing.'
            html += '</div>'

            if wizard.total_orders == 0:
                html += '<div class="alert alert-warning">No work orders selected. Select work orders with linked invoices to reset.</div>'
                wizard.preview_html = html
                continue

            html += '<div class="table-responsive">'
            html += '<table class="table table-sm table-bordered">'
            html += '<thead class="table-light"><tr>'
            html += '<th>Work Order</th><th>Type</th><th>Customer</th><th>Invoice</th><th>Invoice Status</th>'
            html += '</tr></thead><tbody>'

            for order in wizard.retrieval_order_ids:
                invoice_name = order.invoice_id.name if order.invoice_id else '-'
                invoice_state = order.invoice_id.state if order.invoice_id else '-'
                state_badge = 'success' if invoice_state == 'draft' else 'warning'
                html += f'<tr><td>{order.name}</td><td>Retrieval</td><td>{order.partner_id.name}</td>'
                html += f'<td>{invoice_name}</td><td><span class="badge bg-{state_badge}">{invoice_state}</span></td></tr>'

            for order in wizard.shredding_order_ids:
                invoice_name = order.invoice_id.name if order.invoice_id else '-'
                invoice_state = order.invoice_id.state if order.invoice_id else '-'
                state_badge = 'success' if invoice_state == 'draft' else 'warning'
                html += f'<tr><td>{order.name}</td><td>Shredding</td><td>{order.partner_id.name}</td>'
                html += f'<td>{invoice_name}</td><td><span class="badge bg-{state_badge}">{invoice_state}</span></td></tr>'

            html += '</tbody></table></div>'

            if wizard.delete_draft_invoices:
                html += '<div class="alert alert-warning mt-2">'
                html += '<i class="fa fa-exclamation-triangle"></i> '
                html += '<strong>Warning:</strong> Draft invoices will be deleted. Posted invoices will only be unlinked.'
                html += '</div>'

            wizard.preview_html = html

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_reset_billing(self):
        """Reset billing status on selected work orders"""
        self.ensure_one()

        if not self.retrieval_order_ids and not self.shredding_order_ids:
            raise UserError(_("Please select at least one work order to reset."))

        reset_count = 0
        deleted_invoices = 0
        unlinked_invoices = 0

        # Collect all invoices to process
        invoices_to_delete = self.env['account.move']
        invoices_to_unlink = self.env['account.move']

        all_orders = list(self.retrieval_order_ids) + list(self.shredding_order_ids)

        for order in all_orders:
            if order.invoice_id:
                invoice = order.invoice_id

                if self.delete_draft_invoices and invoice.state == 'draft':
                    invoices_to_delete |= invoice
                else:
                    invoices_to_unlink |= invoice

                # Reset the work order
                order.write({
                    'invoice_id': False,
                    'billing_period_id': False,
                    'pending_consolidated_billing': False,
                })
                reset_count += 1

        # Delete draft invoices
        if invoices_to_delete:
            deleted_invoices = len(invoices_to_delete)
            invoices_to_delete.unlink()

        unlinked_invoices = len(invoices_to_unlink)

        # Return notification
        message = _("Successfully reset %d work order(s) for re-billing.") % reset_count
        if deleted_invoices:
            message += _(" Deleted %d draft invoice(s).") % deleted_invoices
        if unlinked_invoices:
            message += _(" Unlinked from %d posted invoice(s).") % unlinked_invoices

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Billing Reset Complete'),
                'message': message,
                'type': 'success',
                'sticky': False,
                'next': {'type': 'ir.actions.act_window_close'},
            }
        }

    def action_load_all_billed(self):
        """Load all currently billed work orders based on type selection"""
        self.ensure_one()

        if self.work_order_type in ('retrieval', 'all'):
            billed_retrievals = self.env['work.order.retrieval'].search([
                ('invoice_id', '!=', False)
            ])
            self.retrieval_order_ids = [(6, 0, billed_retrievals.ids)]

        if self.work_order_type in ('shredding', 'all'):
            billed_shredding = self.env['work.order.shredding'].search([
                ('invoice_id', '!=', False)
            ])
            self.shredding_order_ids = [(6, 0, billed_shredding.ids)]

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'reset.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
