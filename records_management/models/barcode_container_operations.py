# -*- coding: utf-8 -*-
"""
Barcode-Based Container Operations

This module enables barcode-triggered workflows for container management.
Integrates with Odoo's Barcode app to process containers through scanning.

Key Features:
- Barcode-triggered status changes (temp → storage, etc.)
- Internal transfer automation
- Stock quant creation via barcode operations
- UI button → barcode value mapping
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerBarcodeOperations(models.Model):
    """
    Extends records.container with barcode operation support.
    
    Instead of direct stock.quant creation (which has product type field issues),
    this uses Odoo's Barcode app infrastructure to handle inventory operations.
    """
    _inherit = 'records.container'
    
    # Barcode operation tracking
    last_barcode_operation = fields.Char(
        string='Last Barcode Operation',
        readonly=True,
        help='Tracks the last barcode operation performed on this container'
    )
    
    last_barcode_operation_date = fields.Datetime(
        string='Last Barcode Scan',
        readonly=True,
        help='Timestamp of last barcode operation'
    )
    
    barcode_operation_count = fields.Integer(
        string='Barcode Operations',
        compute='_compute_barcode_operation_count',
        help='Total number of barcode operations performed'
    )
    
    pending_transfer_id = fields.Many2one(
        'stock.picking',
        string='Pending Transfer',
        help='Active stock transfer waiting for validation'
    )
    
    @api.depends('last_barcode_operation')
    def _compute_barcode_operation_count(self):
        """Count barcode operations from audit logs"""
        for record in self:
            count = self.env['naid.audit.log'].search_count([
                ('container_id', '=', record.id),
                ('action', 'like', 'barcode_%')
            ])
            record.barcode_operation_count = count
    
    def action_barcode_convert_to_storage(self):
        """
        Convert temp container to storage container via barcode operation.
        
        This method is called when:
        1. User clicks "Store Container" button (emits WH/STOCK/NEW-IN barcode)
        2. User scans container barcode
        3. Barcode app processes the transfer
        
        The button essentially "emits" the barcode value, triggering the
        barcode nomenclature rule which creates the internal transfer.
        """
        self.ensure_one()
        
        if self.state != 'temp':
            raise UserError(_('Only temporary containers can be converted to storage.'))
        
        # Create internal transfer using barcode operation
        transfer = self._create_barcode_transfer(
            operation_type='convert_to_storage',
            source_location_barcode='TEMP/INTAKE',
            dest_location_barcode='WH/STOCK/NEW-IN',
            notes='Convert temp container to storage via barcode operation'
        )
        
        # Log the operation
        self._log_barcode_operation(
            operation='barcode_convert_storage',
            barcode='WH/STOCK/NEW-IN',
            transfer_id=transfer.id
        )
        
        # Update container state
        self.write({
            'state': 'active',
            'container_type': 'storage',
            'last_barcode_operation': 'Convert to Storage',
            'last_barcode_operation_date': fields.Datetime.now(),
            'pending_transfer_id': transfer.id,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Barcode Transfer'),
            'res_model': 'stock.picking',
            'res_id': transfer.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def action_barcode_mark_for_pickup(self):
        """Mark container for customer pickup via barcode operation"""
        self.ensure_one()
        
        transfer = self._create_barcode_transfer(
            operation_type='mark_pickup',
            source_location_barcode=self.location_id.barcode or 'WH/STOCK',
            dest_location_barcode='WH/STOCK/PICKUP',
            notes='Mark container for pickup'
        )
        
        self._log_barcode_operation('barcode_mark_pickup', 'WH/STOCK/PICKUP', transfer.id)
        
        self.write({
            'pickup_ready': True,
            'last_barcode_operation': 'Marked for Pickup',
            'last_barcode_operation_date': fields.Datetime.now(),
            'pending_transfer_id': transfer.id,
        })
        
        return self._open_barcode_transfer(transfer)
    
    def action_barcode_queue_for_shredding(self):
        """Queue container for destruction via barcode operation"""
        self.ensure_one()
        
        if self.state not in ['active', 'retention_expired']:
            raise UserError(_('Only active or retention-expired containers can be queued for shredding.'))
        
        transfer = self._create_barcode_transfer(
            operation_type='queue_shredding',
            source_location_barcode=self.location_id.barcode or 'WH/STOCK',
            dest_location_barcode='WH/SHRED/QUEUE',
            notes='Queue container for destruction'
        )
        
        self._log_barcode_operation('barcode_queue_shred', 'WH/SHRED/QUEUE', transfer.id)
        
        self.write({
            'state': 'pending_destruction',
            'last_barcode_operation': 'Queued for Shredding',
            'last_barcode_operation_date': fields.Datetime.now(),
            'pending_transfer_id': transfer.id,
        })
        
        return self._open_barcode_transfer(transfer)
    
    def action_barcode_complete_shredding(self):
        """
        Complete destruction process via barcode operation.
        
        UPDATED: Now uses new 'destroyed' state and billing automation.
        Legacy method maintained for backward compatibility.
        """
        self.ensure_one()
        
        if self.state not in ('in', 'out', 'pending_destruction'):
            raise UserError(_('Container must be in storage, out with customer, or pending destruction state.'))
        
        # Use new destruction workflow
        return self.action_barcode_destroy()
    
    def action_barcode_add_to_inventory(self):
        """
        Add container to inventory via barcode operation.
        
        This is the key method that replaces direct stock.quant creation.
        Instead of manually creating product records with problematic fields,
        we let Odoo's Barcode app handle it through internal transfers.
        """
        self.ensure_one()
        
        # Get or create stock location
        stock_location = self._get_or_create_stock_location()
        
        # Create inventory adjustment transfer
        transfer = self.env['stock.picking'].create({
            'picking_type_id': self._get_inventory_adjustment_type().id,
            'location_id': self.env.ref('stock.stock_location_locations').id,
            'location_dest_id': stock_location.id,
            'origin': _('Barcode Inventory - %s') % self.barcode,
            'move_ids': [(0, 0, {
                'name': _('Add Container to Inventory'),
                'product_id': self._get_container_product().id,
                'product_uom_qty': 1,
                'product_uom': self.env.ref('uom.product_uom_unit').id,
                'location_id': self.env.ref('stock.stock_location_locations').id,
                'location_dest_id': stock_location.id,
            })],
        })
        
        self._log_barcode_operation('barcode_add_inventory', 'INV/ADD/STOCK', transfer.id)
        
        self.write({
            'last_barcode_operation': 'Added to Inventory',
            'last_barcode_operation_date': fields.Datetime.now(),
            'pending_transfer_id': transfer.id,
        })
        
        # Auto-validate the transfer (inventory adjustments are immediate)
        transfer.action_confirm()
        transfer.action_assign()
        for move in transfer.move_ids:
            move.quantity_done = move.product_uom_qty
        transfer.button_validate()
        
        return self._open_barcode_transfer(transfer)

    def action_barcode_transfer_location(self):
        """
        Transfer container to a different stock location via barcode operation.
        
        This method is called from batch operations wizard when 'transfer' type is selected.
        Uses the target_location_id from the wizard context.
        """
        self.ensure_one()
        
        # Get target location from context (set by batch wizard)
        target_location_id = self.env.context.get('target_location_id')
        if not target_location_id:
            # If no context, use current location (no-op for safety)
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Transfer Skipped'),
                    'message': _('No target location specified for container %s') % (self.barcode or self.name),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        target_location = self.env['stock.location'].browse(target_location_id)
        if not target_location.exists():
            raise UserError(_('Target location not found.'))
        
        # Create internal transfer
        transfer = self._create_barcode_transfer(
            operation_type='transfer_location',
            source_location_barcode=self.location_id.barcode or 'WH/STOCK',
            dest_location_barcode=target_location.barcode or target_location.complete_name,
            notes=_('Transfer container to %s') % target_location.display_name
        )
        
        self._log_barcode_operation('barcode_transfer', target_location.barcode or 'WH/TRANSFER', transfer.id)
        
        self.write({
            'location_id': target_location.id,
            'last_barcode_operation': _('Transferred to %s') % target_location.display_name,
            'last_barcode_operation_date': fields.Datetime.now(),
            'pending_transfer_id': transfer.id,
        })
        
        return self._open_barcode_transfer(transfer)
    
    def action_barcode_destroy(self):
        """
        Mark container as destroyed and create destruction charges.
        
        Destruction Workflow:
        1. Technician scans containers on destruction work order
        2. Clicks "Verified and Destroyed" button (calls this method)
        3. System: Sets state='destroyed', active=False
        4. Creates invoice charges: removal fee + shredding fee
        5. Closes work order if all items processed
        6. Creates NAID audit log
        
        Billing: Removal fee + Shredding fee (2 line items)
        """
        self.ensure_one()
        
        # Validation
        if self.state not in ('in', 'out'):
            raise UserError(_("Can only destroy containers that are 'In Storage' or 'Out with Customer'. Current state: %s") % dict(self._fields['state'].selection).get(self.state))
        
        # Perform destruction
        self.write({
            'state': 'destroyed',
            'active': False,
            'destruction_date': fields.Date.today(),
            'last_barcode_operation': 'Verified and Destroyed',
            'last_barcode_operation_date': fields.Datetime.now(),
        })
        
        # Create destruction charges (removal + shredding fees)
        self._create_destruction_charges()
        
        # Check and close work order if all items complete
        self._check_and_close_destruction_work_order()
        
        # Audit log
        self.env['naid.audit.log'].sudo().create({
            'name': _('Destruction: %s') % self.name,
            'action_type': 'container_destroyed',
            'container_id': self.id,
            'description': _('Container %s destroyed via barcode workflow. Customer: %s. Charges created.') % (self.barcode or self.name, self.partner_id.name),
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Container Destroyed'),
                'message': _('Container %s marked as destroyed. Destruction charges created.') % (self.barcode or self.name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_barcode_perm_out(self):
        """
        Mark container as permanent removal and create removal charges.
        
        Perm-Out Workflow:
        1. Customer discontinues service, takes items back permanently
        2. Technician scans containers on perm-out work order
        3. Clicks "Verified and Returned" button (calls this method)
        4. System: Sets state='perm_out', active=False
        5. Creates invoice charge: removal fee ONLY (no shredding)
        6. Closes work order if all items processed
        7. Creates NAID audit log
        
        Billing: Removal fee only (1 line item)
        """
        self.ensure_one()
        
        # Validation
        if self.state not in ('in', 'out'):
            raise UserError(_("Can only perm-out containers that are 'In Storage' or 'Out with Customer'. Current state: %s") % dict(self._fields['state'].selection).get(self.state))
        
        # Perform perm-out
        self.write({
            'state': 'perm_out',
            'active': False,
            'last_barcode_operation': 'Verified and Returned (Perm-Out)',
            'last_barcode_operation_date': fields.Datetime.now(),
        })
        
        # Create removal charges (NO shredding fee)
        self._create_removal_charges()
        
        # Check and close work order if all items complete
        self._check_and_close_perm_out_work_order()
        
        # Audit log
        self.env['naid.audit.log'].sudo().create({
            'name': _('Perm-Out: %s') % self.name,
            'action_type': 'container_perm_out',
            'container_id': self.id,
            'description': _('Container %s permanently removed and returned to customer %s. Removal charges created.') % (self.barcode or self.name, self.partner_id.name),
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Container Returned'),
                'message': _('Container %s permanently removed. Removal charges created.') % (self.barcode or self.name),
                'type': 'success',
                'sticky': False,
            }
        }
    
    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    
    def _create_barcode_transfer(self, operation_type, source_location_barcode, 
                                   dest_location_barcode, notes=''):
        """
        Create internal transfer triggered by barcode operation.
        
        This is the core method that enables barcode-driven workflows.
        The barcode nomenclature rules define what happens when specific
        location barcodes are scanned.
        """
        # Find or create locations based on barcode patterns
        source_location = self._get_location_by_barcode(source_location_barcode)
        dest_location = self._get_location_by_barcode(dest_location_barcode)
        
        # Get internal transfer operation type
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'internal'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not picking_type:
            raise UserError(_('Internal transfer operation type not found. Please configure warehouse.'))
        
        # Create the transfer
        transfer = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'origin': _('Barcode Operation - %s') % self.barcode,
            'note': notes,
            'partner_id': self.partner_id.id,
            'container_id': self.id,  # Link to container
        })
        
        # Add container as "product" to transfer
        # This uses Odoo's product infrastructure without manually creating products
        product = self._get_container_product()
        
        transfer.move_ids = [(0, 0, {
            'name': _('Container %s - %s') % (self.barcode, operation_type),
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom': self.env.ref('uom.product_uom_unit').id,
            'location_id': source_location.id,
            'location_dest_id': dest_location.id,
            'picking_id': transfer.id,
        })]
        
        return transfer
    
    def _get_location_by_barcode(self, barcode_pattern):
        """
        Find or create stock location based on barcode pattern.
        
        Barcode patterns like 'WH/STOCK/NEW-IN' are used to identify
        specific workflow destinations.
        """
        location = self.env['stock.location'].search([
            ('barcode', '=', barcode_pattern),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not location:
            # Create location if it doesn't exist
            # Parse barcode pattern for location hierarchy
            parts = barcode_pattern.split('/')
            location_name = parts[-1].replace('-', ' ').title()
            
            # Find parent location
            parent = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
            
            location = self.env['stock.location'].create({
                'name': location_name,
                'barcode': barcode_pattern,
                'usage': 'internal',
                'location_id': parent.id if parent else False,
                'company_id': self.company_id.id,
            })
        
        return location
    
    def _get_container_product(self):
        """
        Get or create generic container product for inventory tracking.
        
        This method intentionally does NOT set detailed_type or type fields,
        letting Odoo use defaults to avoid field compatibility issues.
        """
        product = self.env['product.product'].search([
            ('default_code', '=', 'CONTAINER-GENERIC'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Records Container (Generic)',
                'default_code': 'CONTAINER-GENERIC',
                'type': 'storable',  # Odoo 18: 'storable' for inventory tracking
                'tracking': 'none',
                'company_id': self.company_id.id,
                # Intentionally NOT setting detailed_type - let Odoo defaults handle it
            })
        
        return product
    
    def _get_inventory_adjustment_type(self):
        """Get inventory adjustment operation type"""
        adjustment_type = self.env['stock.picking.type'].search([
            ('code', '=', 'incoming'),
            ('warehouse_id.company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not adjustment_type:
            raise UserError(_('Inventory adjustment operation type not found.'))
        
        return adjustment_type
    
    def _get_or_create_stock_location(self):
        """Get or create default stock location for containers"""
        location = self.env['stock.location'].search([
            ('name', '=', 'Records Storage'),
            ('usage', '=', 'internal'),
            ('company_id', '=', self.company_id.id),
        ], limit=1)
        
        if not location:
            parent = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)
            location = self.env['stock.location'].create({
                'name': 'Records Storage',
                'usage': 'internal',
                'location_id': parent.id if parent else False,
                'company_id': self.company_id.id,
            })
        
        return location
    
    def _log_barcode_operation(self, operation, barcode, transfer_id=None):
        """Log barcode operation to audit trail"""
        self.env['naid.audit.log'].create({
            'container_id': self.id,
            'action': operation,
            'description': _('Barcode operation: %s (Barcode: %s)') % (operation, barcode),
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
            'transfer_id': transfer_id,
        })
    
    def _open_barcode_transfer(self, transfer):
        """Open transfer in Barcode app view"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('Barcode Transfer - %s') % transfer.name,
            'res_model': 'stock.picking',
            'res_id': transfer.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'barcode_view': True,
                'default_immediate_transfer': True,
            }
        }
    
    def action_view_barcode_operations(self):
        """View all barcode operations for this container"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Barcode Operations - %s') % self.barcode,
            'res_model': 'naid.audit.log',
            'view_mode': 'tree,form',
            'domain': [
                ('container_id', '=', self.id),
                ('action', 'like', 'barcode_%'),
            ],
            'context': {'default_container_id': self.id},
        }
