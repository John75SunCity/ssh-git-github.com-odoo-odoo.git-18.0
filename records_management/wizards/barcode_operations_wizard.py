# -*- coding: utf-8 -*-
"""
Barcode Operations Wizard

Universal barcode scanning interface for Records Management operations.
Uses Odoo's native barcodes.barcode_events_mixin for real-time barcode handling.

Supports:
- Container lookup and operations
- Work order scanning
- Bin service operations
- File/document scanning

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BarcodeOperationsWizard(models.TransientModel):
    """
    Universal barcode scanning wizard for Records Management.
    
    Inherits from barcodes.barcode_events_mixin to enable real-time
    barcode scanning via the barcode_handler widget.
    """
    _name = 'barcode.operations.wizard'
    _description = 'Barcode Operations Scanner'
    _inherit = ['barcodes.barcode_events_mixin']

    # Operation Mode Selection
    operation_mode = fields.Selection([
        ('lookup', 'Container Lookup'),
        ('retrieval', 'Retrieval Scan'),
        ('shredding', 'Shredding/Destruction'),
        ('bin', 'Bin Service'),
        ('file', 'File/Document'),
        ('location', 'Location Scan'),
    ], string='Operation', default='lookup', required=True)

    # Context Fields
    work_order_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string='Retrieval Work Order',
        help='Active retrieval work order for scanning'
    )
    shredding_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string='Shredding Work Order',
        help='Active shredding work order for bin scanning'
    )
    
    # Results
    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Found Container',
        readonly=True
    )
    bin_id = fields.Many2one(
        comodel_name='shredding.bin',
        string='Found Bin',
        readonly=True
    )
    document_id = fields.Many2one(
        comodel_name='records.document',
        string='Found Document',
        readonly=True
    )
    location_id = fields.Many2one(
        comodel_name='records.location',
        string='Found Location',
        readonly=True
    )

    # Status Display
    last_barcode = fields.Char(string='Last Scanned', readonly=True)
    scan_result = fields.Text(string='Result', readonly=True)
    scan_success = fields.Boolean(string='Success', readonly=True)
    scan_count = fields.Integer(string='Scans This Session', default=0)

    # Standard Odoo Commands Status
    pending_operation = fields.Selection([
        ('none', 'None'),
        ('validate', 'Pending Validate'),
        ('scrap', 'Pending Destruction'),
        ('return', 'Pending Retrieval'),
    ], string='Pending Action', default='none')

    def on_barcode_scanned(self, barcode):
        """
        Handle barcode scanning events from Odoo's barcode infrastructure.
        
        This method is automatically called when a barcode is scanned
        via the barcode_handler widget or hardware scanner.
        
        Supports standard Odoo barcode commands:
        - O-BTN.validate: Validate pending operation
        - O-BTN.cancel / O-BTN.discard: Cancel operation
        - O-CMD.PRINT: Print labels
        - O-BTN.scrap: Queue for destruction
        - O-CMD.RETURN: Create retrieval request
        - O-CMD.MAIN-MENU: Return to main menu
        """
        self.ensure_one()
        self.last_barcode = barcode
        self.scan_count += 1

        # Handle standard Odoo commands first
        result = self._handle_standard_commands(barcode)
        if result:
            return result

        # Route to appropriate handler based on operation mode
        handlers = {
            'lookup': self._handle_container_lookup,
            'retrieval': self._handle_retrieval_scan,
            'shredding': self._handle_shredding_scan,
            'bin': self._handle_bin_scan,
            'file': self._handle_file_scan,
            'location': self._handle_location_scan,
        }
        
        handler = handlers.get(self.operation_mode, self._handle_container_lookup)
        return handler(barcode)

    def _handle_standard_commands(self, barcode):
        """Process standard Odoo barcode commands."""
        # Validate operation
        if barcode == 'O-BTN.validate':
            return self._execute_validate()
        
        # Cancel/Discard
        if barcode in ['O-BTN.cancel', 'O-BTN.discard']:
            return self._execute_cancel()
        
        # Print command
        if barcode == 'O-CMD.PRINT':
            return self._execute_print()
        
        # Scrap/Destruction
        if barcode == 'O-BTN.scrap':
            self.pending_operation = 'scrap'
            self.scan_result = _('Destruction queued. Scan container barcode to confirm.')
            self.scan_success = True
            return None
        
        # Return/Retrieval
        if barcode == 'O-CMD.RETURN':
            self.pending_operation = 'return'
            self.scan_result = _('Retrieval mode. Scan container barcode to create request.')
            self.scan_success = True
            return None
        
        # Main menu
        if barcode == 'O-CMD.MAIN-MENU':
            return {'type': 'ir.actions.act_window_close'}
        
        return None

    def _handle_container_lookup(self, barcode):
        """Lookup container by barcode."""
        Container = self.env['records.container']
        
        # Search by physical barcode
        container = Container.search([
            ('barcode', '=', barcode),
            '|', ('company_id', '=', False),
            ('company_id', '=', self.env.company.id)
        ], limit=1)
        
        # Fallback to temp barcode
        if not container:
            container = Container.search([
                ('temp_barcode', '=', barcode),
                '|', ('company_id', '=', False),
                ('company_id', '=', self.env.company.id)
            ], limit=1)
        
        if not container:
            self.scan_success = False
            self.scan_result = _('No container found: %s') % barcode
            self.container_id = False
            return None
        
        # Handle pending operations
        if self.pending_operation == 'scrap':
            return self._queue_destruction(container)
        elif self.pending_operation == 'return':
            return self._create_retrieval(container)
        
        # Standard lookup - update wizard and optionally open container
        self.container_id = container.id
        self.scan_success = True
        self.scan_result = _('Found: %s\nCustomer: %s\nLocation: %s\nState: %s') % (
            container.name,
            container.partner_id.name or _('N/A'),
            container.location_id.name if container.location_id else _('N/A'),
            container.state or _('N/A')
        )
        
        # Post audit log
        container.message_post(
            body=_('Container scanned via Barcode Operations Wizard'),
            message_type='notification'
        )
        
        return None

    def _handle_retrieval_scan(self, barcode):
        """Handle scanning for retrieval work orders."""
        if not self.work_order_id:
            self.scan_success = False
            self.scan_result = _('No retrieval work order selected. Please set a work order first.')
            return None
        
        # Delegate to work order's scan method
        result = self.work_order_id.action_scan_container(barcode)
        self.scan_success = result.get('success', False)
        self.scan_result = result.get('message', '')
        
        return None

    def _handle_shredding_scan(self, barcode):
        """Handle scanning for shredding/destruction operations."""
        Container = self.env['records.container']
        
        container = Container.search([
            '|', ('barcode', '=', barcode),
            ('temp_barcode', '=', barcode)
        ], limit=1)
        
        if not container:
            self.scan_success = False
            self.scan_result = _('Container not found: %s') % barcode
            return None
        
        # Check if container can be destroyed
        if container.state == 'destroyed':
            self.scan_success = False
            self.scan_result = _('Container %s is already destroyed') % container.name
            return None
        
        # Add to shredding work order if one is active
        if self.shredding_order_id:
            self.shredding_order_id.write({
                'container_ids': [(4, container.id)]
            })
            self.scan_success = True
            self.scan_result = _('Container %s added to shredding order') % container.name
        else:
            # Queue for destruction
            container.write({'queued_for_destruction': True})
            self.scan_success = True
            self.scan_result = _('Container %s queued for destruction') % container.name
        
        self.container_id = container.id
        return None

    def _handle_bin_scan(self, barcode):
        """Handle bin barcode scanning."""
        Bin = self.env.get('shredding.bin')
        
        if not Bin:
            self.scan_success = False
            self.scan_result = _('Bin model not available')
            return None
        
        bin_record = Bin.search([('barcode', '=', barcode)], limit=1)
        
        if not bin_record:
            self.scan_success = False
            self.scan_result = _('Bin not found: %s') % barcode
            return None
        
        self.bin_id = bin_record.id
        self.scan_success = True
        self.scan_result = _('Found Bin: %s\nCustomer: %s\nService Type: %s') % (
            bin_record.name,
            bin_record.partner_id.name if hasattr(bin_record, 'partner_id') else _('N/A'),
            bin_record.service_type if hasattr(bin_record, 'service_type') else _('N/A')
        )
        
        return None

    def _handle_file_scan(self, barcode):
        """Handle file/document barcode scanning."""
        Document = self.env.get('records.document')
        
        if not Document:
            self.scan_success = False
            self.scan_result = _('Document model not available')
            return None
        
        document = Document.search([('barcode', '=', barcode)], limit=1)
        
        if not document:
            self.scan_success = False
            self.scan_result = _('Document not found: %s') % barcode
            return None
        
        self.document_id = document.id
        self.scan_success = True
        self.scan_result = _('Found Document: %s\nContainer: %s') % (
            document.name,
            document.container_id.name if hasattr(document, 'container_id') and document.container_id else _('N/A')
        )
        
        return None

    def _handle_location_scan(self, barcode):
        """Handle location barcode scanning."""
        Location = self.env['records.location']
        
        location = Location.search([('barcode', '=', barcode)], limit=1)
        
        if not location:
            self.scan_success = False
            self.scan_result = _('Location not found: %s') % barcode
            return None
        
        self.location_id = location.id
        self.scan_success = True
        self.scan_result = _('Found Location: %s\nFull Path: %s\nCapacity: %s') % (
            location.name,
            location.complete_name if hasattr(location, 'complete_name') else location.name,
            location.capacity if hasattr(location, 'capacity') else _('N/A')
        )
        
        return None

    def _queue_destruction(self, container):
        """Queue container for destruction."""
        container.write({'queued_for_destruction': True})
        self.pending_operation = 'none'
        self.container_id = container.id
        self.scan_success = True
        self.scan_result = _('Container %s queued for destruction') % container.name
        
        # Log audit
        self.env['naid.audit.log'].sudo().create({
            'name': _('Destruction Queued: %s') % container.name,
            'container_id': container.id,
            'action_type': 'destruction_requested',
            'description': _('Container queued for destruction via barcode scan'),
            'user_id': self.env.user.id,
            'timestamp': fields.Datetime.now(),
        })
        
        return None

    def _create_retrieval(self, container):
        """Create retrieval request for container."""
        PortalRequest = self.env.get('portal.request')
        
        if not PortalRequest:
            self.scan_success = False
            self.scan_result = _('Portal request model not available')
            return None
        
        retrieval = PortalRequest.sudo().create({
            'name': _('Barcode Retrieval: %s') % container.name,
            'request_type': 'retrieval',
            'container_ids': [(4, container.id)],
            'partner_id': container.partner_id.id,
            'description': _('Retrieval request created via barcode scan'),
            'user_id': self.env.user.id,
        })
        
        self.pending_operation = 'none'
        self.container_id = container.id
        self.scan_success = True
        self.scan_result = _('Retrieval request created: %s') % retrieval.name
        
        return None

    def _execute_validate(self):
        """Execute pending validation."""
        if self.container_id:
            self.scan_success = True
            self.scan_result = _('Validated: %s') % self.container_id.name
        else:
            self.scan_success = False
            self.scan_result = _('No container to validate. Scan a container first.')
        return None

    def _execute_cancel(self):
        """Cancel pending operation."""
        self.pending_operation = 'none'
        self.container_id = False
        self.scan_success = True
        self.scan_result = _('Operation cancelled')
        return None

    def _execute_print(self):
        """Execute print command."""
        if self.container_id:
            # Return print action
            return self.container_id.action_print_barcode_label()
        
        self.scan_success = False
        self.scan_result = _('No container selected for printing')
        return None

    # =========================================================================
    # Action Buttons
    # =========================================================================
    
    def action_open_container(self):
        """Open the found container in form view."""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_('No container found. Scan a barcode first.'))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container: %s') % self.container_id.name,
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_reset(self):
        """Reset the scanner for a new session."""
        self.write({
            'container_id': False,
            'bin_id': False,
            'document_id': False,
            'location_id': False,
            'last_barcode': False,
            'scan_result': False,
            'scan_success': False,
            'scan_count': 0,
            'pending_operation': 'none',
        })
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_change_mode(self):
        """Refresh wizard after mode change."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
