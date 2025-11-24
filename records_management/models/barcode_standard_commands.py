# -*- coding: utf-8 -*-
"""
Odoo Standard Barcode Commands Implementation

Implements Odoo's standard barcode commands for Records Management:
- O-BTN.validate - Validate/confirm current operation
- O-BTN.discard - Cancel/discard current operation  
- O-BTN.cancel - Cancel operation (alias for discard)
- O-CMD.MAIN-MENU - Return to barcode main menu
- O-CMD.PRINT - Print picking/movement slip
- O-CMD.PACKING - Print delivery/packing slip
- O-BTN.scrap - Scrap/destroy items (maps to shredding)
- O-CMD.RETURN - Return items (maps to retrieval)

These commands follow Odoo's stock_barcode module patterns.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsContainerBarcodeCommands(models.Model):
    """Extends records.container with Odoo standard barcode commands"""
    _inherit = 'records.container'
    
    # ============================================================================
    # STANDARD ODOO BARCODE COMMANDS
    # ============================================================================
    
    def action_validate_barcode_operation(self):
        """
        Standard Odoo VALIDATE command (O-BTN.validate)
        
        Validates and confirms pending stock transfer operations.
        Called when user scans O-BTN.validate barcode or clicks Validate button.
        
        Returns:
            dict: Success notification or error message
        """
        self.ensure_one()
        
        if not self.pending_transfer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Pending Operation'),
                    'message': _('There is no pending transfer to validate for this container.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        transfer = self.pending_transfer_id
        
        try:
            # Validate the transfer
            if transfer.state == 'draft':
                transfer.action_confirm()
            
            if transfer.state == 'confirmed':
                transfer.action_assign()
            
            # Set quantities done
            for move in transfer.move_ids:
                if move.state not in ['done', 'cancel']:
                    move.quantity_done = move.product_uom_qty
            
            # Validate the transfer
            if transfer.state not in ['done', 'cancel']:
                transfer.button_validate()
            
            # Log the validation
            self.env['naid.audit.log'].sudo().create({
                'name': _('Transfer Validated: %s') % transfer.name,
                'container_id': self.id,
                'action_type': 'container_updated',
                'action': 'barcode_validate',
                'description': _('Transfer validated via barcode command: %s') % transfer.name,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
            })
            
            # Clear pending transfer
            self.write({
                'last_barcode_operation': 'Transfer Validated',
                'last_barcode_operation_date': fields.Datetime.now(),
                'pending_transfer_id': False,
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Transfer Validated'),
                    'message': _('Stock movement %s completed successfully') % transfer.name,
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Validation Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_discard_barcode_operation(self):
        """
        Standard Odoo DISCARD command (O-BTN.discard / O-BTN.cancel)
        
        Cancels pending stock transfer operations.
        Called when user scans O-BTN.discard or O-BTN.cancel barcode.
        
        Returns:
            dict: Action to close current window or show notification
        """
        self.ensure_one()
        
        if not self.pending_transfer_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Pending Operation'),
                    'message': _('There is no pending transfer to discard for this container.'),
                    'type': 'info',
                    'sticky': False,
                }
            }
        
        transfer = self.pending_transfer_id
        transfer_name = transfer.name
        
        # Cancel the transfer
        try:
            if transfer.state not in ['done', 'cancel']:
                transfer.action_cancel()
            
            # Log the cancellation
            self.env['naid.audit.log'].sudo().create({
                'name': _('Transfer Discarded: %s') % transfer_name,
                'container_id': self.id,
                'action_type': 'container_updated',
                'action': 'barcode_discard',
                'description': _('Transfer discarded via barcode command: %s') % transfer_name,
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
            })
            
            # Clear pending transfer
            self.write({
                'last_barcode_operation': 'Operation Discarded',
                'last_barcode_operation_date': fields.Datetime.now(),
                'pending_transfer_id': False,
            })
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Operation Discarded'),
                    'message': _('Transfer %s has been cancelled') % transfer_name,
                    'type': 'info',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Discard Failed'),
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    def action_print_picking_operation(self):
        """
        Standard Odoo PRINT command (O-CMD.PRINT)
        
        Prints the current picking/movement slip.
        If no pending transfer, prints container movement history.
        
        Returns:
            dict: Report action to print document
        """
        self.ensure_one()
        
        if self.pending_transfer_id:
            # Print the pending stock picking
            return self.env.ref('stock.action_report_picking').report_action(self.pending_transfer_id)
        else:
            # Print container movement history report
            # Note: This report template needs to be created separately
            report_ref = self.env.ref('records_management.report_container_movement_history', raise_if_not_found=False)
            if report_ref:
                return report_ref.report_action(self)
            else:
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Report Not Available'),
                        'message': _('Container movement history report is not configured.'),
                        'type': 'warning',
                        'sticky': False,
                    }
                }
    
    def action_print_delivery_slip(self):
        """
        Standard Odoo PACKING command (O-CMD.PACKING)
        
        Prints delivery/packing slip for retrieval or pickup.
        
        Returns:
            dict: Report action to print delivery document
        """
        self.ensure_one()
        
        # Find active retrieval request for this container
        retrieval = self.env['portal.request'].search([
            ('container_ids', 'in', self.id),
            ('request_type', '=', 'retrieval'),
            ('state', 'in', ['pending', 'approved', 'in_progress'])
        ], limit=1)
        
        if retrieval:
            # Print retrieval delivery slip
            report_ref = self.env.ref('records_management.report_retrieval_delivery_slip', raise_if_not_found=False)
            if report_ref:
                return report_ref.report_action(retrieval)
        
        # Fallback: print basic delivery slip
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('No Active Retrieval'),
                'message': _('No active retrieval request found for this container.'),
                'type': 'warning',
                'sticky': False,
            }
        }
    
    def action_barcode_scrap(self):
        """
        Standard Odoo SCRAP command (O-BTN.scrap)
        
        Maps to existing shredding workflow:
        - If container is pending_destruction → Complete shredding
        - Otherwise → Queue for shredding
        
        Returns:
            dict: Action from shredding method
        """
        self.ensure_one()
        
        if self.state == 'pending_destruction':
            # Complete the destruction process
            return self.action_barcode_complete_shredding()
        else:
            # Queue for destruction
            return self.action_barcode_queue_for_shredding()
    
    def action_barcode_return(self):
        """
        Standard Odoo RETURN command (O-CMD.RETURN)
        
        Creates automatic retrieval request for this container.
        Maps to existing retrieval workflow.
        
        Returns:
            dict: Action to open new retrieval request
        """
        self.ensure_one()
        
        # Check if there's already an active retrieval
        existing_retrieval = self.env['portal.request'].search([
            ('container_ids', 'in', self.id),
            ('request_type', '=', 'retrieval'),
            ('state', 'not in', ['completed', 'cancelled'])
        ], limit=1)
        
        if existing_retrieval:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Existing Retrieval Request'),
                'res_model': 'portal.request',
                'res_id': existing_retrieval.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Create new retrieval request
        retrieval = self.env['portal.request'].sudo().create({
            'name': _('Barcode Retrieval: %s') % self.name,
            'request_type': 'retrieval',
            'container_ids': [(4, self.id)],
            'partner_id': self.partner_id.id,
            'description': _('Automatic retrieval request created via barcode scan (O-CMD.RETURN)'),
            'user_id': self.env.user.id,
        })
        
        # Log the operation
        self.env['naid.audit.log'].sudo().create({
            'name': _('Retrieval Request: %s') % retrieval.name,
            'container_id': self.id,
            'action_type': 'container_move_requested',  # Required Selection field
            'action': 'barcode_return',  # Optional legacy field
            'description': _('Retrieval request created via barcode command: %s') % retrieval.name,
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
        
        self.write({
            'last_barcode_operation': 'Retrieval Requested',
            'last_barcode_operation_date': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('New Retrieval Request'),
            'res_model': 'portal.request',
            'res_id': retrieval.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    # ============================================================================
    # ENHANCED BARCODE SCANNING - INTEGRATES STANDARD COMMANDS
    # ============================================================================
    
    def on_barcode_scanned(self, barcode):
        """
        Enhanced barcode scanning with standard Odoo command support.
        
        Handles both standard Odoo commands and container lookups.
        
        Standard Commands Supported:
        - O-BTN.validate - Validate pending transfer
        - O-BTN.discard / O-BTN.cancel - Cancel pending transfer
        - O-CMD.PRINT - Print picking slip
        - O-CMD.PACKING - Print delivery slip
        - O-BTN.scrap - Queue/complete shredding
        - O-CMD.RETURN - Create retrieval request
        - O-CMD.MAIN-MENU - Return to barcode menu (handled by controller)
        
        Args:
            barcode (str): Scanned barcode value
            
        Returns:
            dict: Action to execute based on barcode
        """
        self.ensure_one()
        
        # Handle standard Odoo commands
        if barcode == 'O-BTN.validate':
            return self.action_validate_barcode_operation()
        
        if barcode in ['O-BTN.discard', 'O-BTN.cancel']:
            return self.action_discard_barcode_operation()
        
        if barcode == 'O-CMD.PRINT':
            return self.action_print_picking_operation()
        
        if barcode == 'O-CMD.PACKING':
            return self.action_print_delivery_slip()
        
        if barcode == 'O-BTN.scrap':
            return self.action_barcode_scrap()
        
        if barcode == 'O-CMD.RETURN':
            return self.action_barcode_return()
        
        if barcode == 'O-CMD.MAIN-MENU':
            # Redirect to barcode main menu (handled by controller)
            return {
                'type': 'ir.actions.act_url',
                'url': '/my/barcode/main',
                'target': 'self',
            }
        
        # If not a standard command, proceed with normal container lookup
        # Search by physical barcode first
        container = self.env['records.container'].search([
            ('barcode', '=', barcode)
        ], limit=1)
        
        if not container:
            # Fallback to temp barcode
            container = self.env['records.container'].search([
                ('temp_barcode', '=', barcode)
            ], limit=1)
        
        if not container:
            raise UserError(_('No container found with barcode: %s') % barcode)
        
        # Log the scan
        self.env['naid.audit.log'].sudo().create({
            'name': _('Barcode Scan: %s') % barcode,
            'container_id': container.id,
            'action_type': 'access',
            'action': 'barcode_scan',
            'description': _('Container scanned: %s') % barcode,
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
        
        container.write({
            'last_barcode_operation': 'Container Scanned',
            'last_barcode_operation_date': fields.Datetime.now(),
        })
        
        # Open container form view
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'res_id': container.id,
            'view_mode': 'form',
            'target': 'current',
        }
