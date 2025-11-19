# -*- coding: utf-8 -*-
"""
Batch Barcode Operations Wizard

Allows processing multiple containers with a single barcode operation.
Users select containers and choose an operation - the wizard emits the
appropriate barcode value for all selected containers.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BatchBarcodeOperations(models.TransientModel):
    """
    Wizard for batch processing containers via barcode operations.
    
    This extends the single-button concept to multiple containers:
    - Select multiple containers
    - Click one button (e.g., "Store All")
    - System emits barcode value for each container
    - All transfers processed in batch
    """
    _name = 'batch.barcode.operations'
    _description = 'Batch Barcode Operations for Containers'
    
    operation_type = fields.Selection([
        ('convert_storage', 'Convert to Storage'),
        ('mark_pickup', 'Mark for Pickup'),
        ('queue_shred', 'Queue for Destruction'),
        ('complete_shred', 'Complete Destruction'),
        ('add_inventory', 'Add to Inventory'),
        ('transfer', 'Transfer to Location'),
    ], string='Operation', required=True, default='convert_storage')
    
    container_ids = fields.Many2many(
        'records.container',
        string='Containers',
        required=True,
        default=lambda self: self._default_containers()
    )
    
    container_count = fields.Integer(
        string='Number of Containers',
        compute='_compute_container_count'
    )
    
    target_location_id = fields.Many2one(
        'stock.location',
        string='Target Location',
        help='Destination location for transfer operations'
    )
    
    operation_display = fields.Char(
        string='Operation Description',
        compute='_compute_operation_display'
    )
    
    barcode_value = fields.Char(
        string='Barcode Value',
        compute='_compute_barcode_value',
        help='The barcode value that will be emitted for this operation'
    )
    
    def _default_containers(self):
        """Get containers from context (selected in tree view)"""
        return self.env.context.get('active_ids', [])
    
    @api.depends('container_ids')
    def _compute_container_count(self):
        for wizard in self:
            wizard.container_count = len(wizard.container_ids)
    
    @api.depends('operation_type')
    def _compute_operation_display(self):
        operation_map = {
            'convert_storage': 'Convert temporary containers to storage containers',
            'mark_pickup': 'Mark containers ready for customer pickup',
            'queue_shred': 'Queue containers for destruction',
            'complete_shred': 'Mark destruction as complete',
            'add_inventory': 'Add containers to inventory tracking',
            'transfer': 'Transfer containers to specified location',
        }
        for wizard in self:
            wizard.operation_display = operation_map.get(wizard.operation_type, '')
    
    @api.depends('operation_type', 'target_location_id')
    def _compute_barcode_value(self):
        barcode_map = {
            'convert_storage': 'WH/STOCK/NEW-IN',
            'mark_pickup': 'WH/STOCK/PICKUP',
            'queue_shred': 'WH/SHRED/QUEUE',
            'complete_shred': 'WH/SHRED/COMPLETE',
            'add_inventory': 'INV/ADD/STOCK',
            'transfer': 'WH/MAIN/TRANSFER',
        }
        for wizard in self:
            wizard.barcode_value = barcode_map.get(wizard.operation_type, 'UNKNOWN')
            if wizard.operation_type == 'transfer' and wizard.target_location_id:
                wizard.barcode_value = wizard.target_location_id.barcode or 'WH/MAIN/TRANSFER'
    
    def action_process_batch(self):
        """
        Process all selected containers with the chosen barcode operation.
        Optimized with batch processing and proper error handling.
        """
        self.ensure_one()
        
        if not self.container_ids:
            raise UserError(_('No containers selected for batch operation.'))
        
        # Map operation type to container method
        operation_methods = {
            'convert_storage': 'action_barcode_convert_to_storage',
            'mark_pickup': 'action_barcode_mark_for_pickup',
            'queue_shred': 'action_barcode_queue_for_shredding',
            'complete_shred': 'action_barcode_complete_shredding',
            'add_inventory': 'action_barcode_add_to_inventory',
        }
        
        method_name = operation_methods.get(self.operation_type)
        if not method_name:
            raise UserError(_('Invalid operation type selected.'))
        
        # Process containers with error handling per operation
        processed = []
        failed = []
        
        # Use self.env.cr.savepoint() for transactional safety
        for container in self.container_ids:
            try:
                # Use savepoint to rollback individual container failures
                with self.env.cr.savepoint():
                    method = getattr(container, method_name)
                    method()
                    processed.append(container.barcode)
            except Exception as e:
                failed.append({
                    'barcode': container.barcode,
                    'error': str(e)
                })
        
        # Show results with notification instead of raising error
        if failed:
            message = _('Batch operation completed with errors:\n\n')
            message += _('Processed: %d containers\n') % len(processed)
            message += _('Failed: %d containers\n\n') % len(failed)
            message += _('Failed containers:\n')
            for fail in failed:
                message += _('- %s: %s\n') % (fail['barcode'], fail['error'])
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Batch Operation Results'),
                    'message': message,
                    'type': 'warning',
                    'sticky': True,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success!'),
                    'message': _('Successfully processed %d containers via barcode operation: %s') % (
                        len(processed),
                        self.barcode_value
                    ),
                    'type': 'success',
                }
            }
