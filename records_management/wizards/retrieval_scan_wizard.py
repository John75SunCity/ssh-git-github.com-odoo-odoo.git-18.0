# -*- coding: utf-8 -*-
"""
Retrieval Scan Wizard

Provides a mobile-friendly interface for scanning containers during
the retrieval/picking process. Shows pick list and allows barcode scanning.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RetrievalScanWizard(models.TransientModel):
    """Wizard for scanning containers during retrieval work order execution."""
    _name = 'retrieval.scan.wizard'
    _description = 'Retrieval Container Scanner'

    work_order_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string='Work Order',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='work_order_id.partner_id',
        readonly=True
    )
    
    # Scanning interface
    barcode_input = fields.Char(
        string='Scan Barcode',
        help='Scan or enter container barcode'
    )
    
    # Status display
    last_scan_result = fields.Char(string='Last Scan', readonly=True)
    last_scan_success = fields.Boolean(string='Last Scan OK', readonly=True)
    
    # Statistics
    total_items = fields.Integer(
        string='Total Items',
        compute='_compute_stats'
    )
    scanned_items = fields.Integer(
        string='Scanned',
        compute='_compute_stats'
    )
    remaining_items = fields.Integer(
        string='Remaining',
        compute='_compute_stats'
    )
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_stats'
    )
    
    # Pick list items
    item_ids = fields.One2many(
        related='work_order_id.retrieval_item_ids',
        string='Items to Pick',
        readonly=True
    )

    @api.depends('work_order_id.retrieval_item_ids', 'work_order_id.retrieval_item_ids.retrieved')
    def _compute_stats(self):
        """Compute scanning statistics."""
        for wizard in self:
            items = wizard.work_order_id.retrieval_item_ids
            wizard.total_items = len(items)
            wizard.scanned_items = len(items.filtered('retrieved'))
            wizard.remaining_items = wizard.total_items - wizard.scanned_items
            wizard.progress_percentage = (wizard.scanned_items / wizard.total_items * 100) if wizard.total_items else 0

    def action_process_scan(self):
        """Process the scanned barcode."""
        self.ensure_one()
        
        if not self.barcode_input:
            return self._refresh_wizard()
        
        barcode = self.barcode_input.strip()
        
        # Call the work order's scan method
        result = self.work_order_id.action_scan_container(barcode)
        
        # Update wizard status
        self.last_scan_result = result.get('message', '')
        self.last_scan_success = result.get('success', False)
        self.barcode_input = ''  # Clear for next scan
        
        # Check if all items are scanned
        if self.remaining_items == 0:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Pick Complete!'),
                    'message': _('All %d containers have been scanned.') % self.total_items,
                    'type': 'success',
                    'sticky': False,
                    'next': {'type': 'ir.actions.act_window_close'},
                }
            }
        
        return self._refresh_wizard()

    def _refresh_wizard(self):
        """Refresh the wizard to update statistics."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_complete_picking(self):
        """Complete the picking process and close wizard."""
        self.ensure_one()
        
        if self.remaining_items > 0:
            raise UserError(_(
                'There are still %d items to scan. '
                'Please scan all items or cancel to exit.'
            ) % self.remaining_items)
        
        # Update work order progress
        self.work_order_id.completed_boxes = self.scanned_items
        
        return {'type': 'ir.actions.act_window_close'}

    def action_mark_all_scanned(self):
        """Mark all remaining items as scanned (supervisor override)."""
        self.ensure_one()
        
        for item in self.work_order_id.retrieval_item_ids.filtered(lambda l: not l.retrieved):
            item.write({
                'retrieved': True,
                'retrieval_time': fields.Datetime.now(),
                'notes': _('Manually marked as retrieved (supervisor override)')
            })
        
        self.work_order_id.completed_boxes = len(self.work_order_id.retrieval_item_ids)
        self.work_order_id.message_post(body=_('All items marked as retrieved via supervisor override.'))
        
        return {'type': 'ir.actions.act_window_close'}
