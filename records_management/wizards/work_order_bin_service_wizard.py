# -*- coding: utf-8 -*-
"""
Work Order Bin Service Wizard

Wizard for technicians to record TIP and SWAP bin services on work orders.
Supports barcode scanning workflow for mobile/field service operations.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderBinServiceWizard(models.TransientModel):
    """
    Wizard for recording bin service events (TIP/SWAP) on work orders.
    
    Workflow:
    1. Open wizard from work order (action_open_bin_service_scanner)
    2. Select service mode: TIP or SWAP
    3. Scan bin barcode(s)
    4. System records service event and calculates billing
    """
    _name = 'work.order.bin.service.wizard'
    _description = 'Bin Service Scanner Wizard'

    # ============================================================================
    # CONTEXT FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string="Work Order",
        required=True,
        readonly=True
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        related='work_order_id.partner_id',
        readonly=True
    )

    # ============================================================================
    # SERVICE MODE
    # ============================================================================
    service_mode = fields.Selection([
        ('tip', 'TIP - Empty bin and return same bin'),
        ('swap', 'SWAP - Take full bin, leave empty bin'),
    ], string="Service Type", required=True, default='tip',
       help="TIP: Empty the bin contents and leave same bin.\n"
            "SWAP: Take full bin away, leave different empty bin.")

    # ============================================================================
    # BARCODE INPUTS
    # ============================================================================
    bin_barcode = fields.Char(
        string="Bin Barcode",
        help="Scan or enter the bin barcode"
    )

    # For SWAP mode - need to scan two bins
    old_bin_barcode = fields.Char(
        string="Full Bin (Picking Up)",
        help="Scan the full bin you're taking away"
    )
    new_bin_barcode = fields.Char(
        string="Empty Bin (Leaving)",
        help="Scan the empty bin you're leaving behind"
    )

    # ============================================================================
    # SERVICE LOG (Shows completed services this session)
    # ============================================================================
    service_log = fields.Html(
        string="Service Log",
        compute='_compute_service_log',
        readonly=True
    )

    session_event_ids = fields.Many2many(
        comodel_name='shredding.service.event',
        string="Services This Session",
        readonly=True
    )

    # ============================================================================
    # STATISTICS
    # ============================================================================
    session_tip_count = fields.Integer(
        string="Tips This Session",
        compute='_compute_session_stats'
    )
    session_swap_count = fields.Integer(
        string="Swaps This Session",
        compute='_compute_session_stats'
    )
    session_total_billable = fields.Monetary(
        string="Session Total",
        compute='_compute_session_stats',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('session_event_ids')
    def _compute_session_stats(self):
        for wizard in self:
            events = wizard.session_event_ids
            wizard.session_tip_count = len(events.filtered(lambda e: e.service_type == 'tip'))
            wizard.session_swap_count = len(events.filtered(lambda e: e.service_type == 'swap_out'))
            wizard.session_total_billable = sum(events.filtered('is_billable').mapped('billable_amount'))

    @api.depends('session_event_ids')
    def _compute_service_log(self):
        for wizard in self:
            if not wizard.session_event_ids:
                wizard.service_log = '<p class="text-muted">No services recorded yet. Scan a bin to begin.</p>'
                continue

            log_html = '<table class="table table-sm">'
            log_html += '<thead><tr><th>Time</th><th>Type</th><th>Bin</th><th>Amount</th></tr></thead>'
            log_html += '<tbody>'

            for event in wizard.session_event_ids.sorted('service_date', reverse=True):
                type_badge = 'success' if event.service_type == 'tip' else 'primary' if event.service_type == 'swap_out' else 'secondary'
                type_label = dict(event._fields['service_type'].selection).get(event.service_type, event.service_type)
                amount = '${:.2f}'.format(event.billable_amount) if event.is_billable else '-'

                log_html += '<tr>'
                log_html += '<td>{}</td>'.format(event.service_date.strftime('%H:%M:%S') if event.service_date else '-')
                log_html += '<td><span class="badge badge-{}">{}</span></td>'.format(type_badge, type_label)
                log_html += '<td>{}</td>'.format(event.bin_id.barcode)
                log_html += '<td>{}</td>'.format(amount)
                log_html += '</tr>'

            log_html += '</tbody></table>'
            wizard.service_log = log_html

    # ============================================================================
    # BARCODE PROCESSING
    # ============================================================================
    @api.onchange('bin_barcode')
    def _onchange_bin_barcode(self):
        """Process barcode scan in TIP mode."""
        if self.bin_barcode and self.service_mode == 'tip':
            result = self._process_tip(self.bin_barcode)
            self.bin_barcode = False  # Clear for next scan

            if not result.get('success'):
                return {
                    'warning': {
                        'title': _('Scan Error'),
                        'message': result.get('message', _('Unknown error'))
                    }
                }

    @api.onchange('old_bin_barcode', 'new_bin_barcode')
    def _onchange_swap_barcodes(self):
        """Process barcode scans in SWAP mode."""
        if self.service_mode == 'swap' and self.old_bin_barcode and self.new_bin_barcode:
            result = self._process_swap(self.old_bin_barcode, self.new_bin_barcode)
            self.old_bin_barcode = False  # Clear for next scan
            self.new_bin_barcode = False

            if not result.get('success'):
                return {
                    'warning': {
                        'title': _('Scan Error'),
                        'message': result.get('message', _('Unknown error'))
                    }
                }

    def _process_tip(self, barcode):
        """Process a TIP scan."""
        self.ensure_one()
        result = self.work_order_id.action_tip_bin(barcode)

        if result.get('success') and result.get('event_id'):
            event = self.env['shredding.service.event'].browse(result['event_id'])
            self.session_event_ids = [(4, event.id)]

        return result

    def _process_swap(self, old_barcode, new_barcode):
        """Process a SWAP scan."""
        self.ensure_one()
        result = self.work_order_id.action_swap_bin(old_barcode, new_barcode)

        if result.get('success') and result.get('event_ids'):
            for event_id in result['event_ids']:
                self.session_event_ids = [(4, event_id)]

        return result

    # ============================================================================
    # BUTTON ACTIONS
    # ============================================================================
    def action_record_tip(self):
        """Button action to record a TIP service."""
        self.ensure_one()
        if not self.bin_barcode:
            raise UserError(_("Please scan or enter a bin barcode."))

        result = self._process_tip(self.bin_barcode)
        self.bin_barcode = False

        if not result.get('success'):
            raise UserError(result.get('message', _('Failed to record TIP')))

        # Reopen wizard to continue scanning
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_record_swap(self):
        """Button action to record a SWAP service."""
        self.ensure_one()
        if not self.old_bin_barcode or not self.new_bin_barcode:
            raise UserError(_("Please scan both the full bin (picking up) and empty bin (leaving)."))

        result = self._process_swap(self.old_bin_barcode, self.new_bin_barcode)
        self.old_bin_barcode = False
        self.new_bin_barcode = False

        if not result.get('success'):
            raise UserError(result.get('message', _('Failed to record SWAP')))

        # Reopen wizard to continue scanning
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_done(self):
        """Close the wizard and return to work order."""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    def action_complete_work_order(self):
        """Complete the work order and close wizard."""
        self.ensure_one()
        if self.work_order_id.state == 'in_progress':
            self.work_order_id.action_complete_work()
        return {'type': 'ir.actions.act_window_close'}
