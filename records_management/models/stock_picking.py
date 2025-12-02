from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    is_records_management = fields.Boolean(
        string="Is a Records Management Picking",
        compute='_compute_is_records_management',
        store=True,
        help="Indicates if this picking is related to records management operations."
    )
    portal_request_id = fields.Many2one(
        'portal.request',
        string="Related Service Request",
        copy=False,
        readonly=True,
        help="The customer service request that generated this picking."
    )
    destruction_order_id = fields.Many2one(
        'records.destruction',
        string="Destruction Order",
        copy=False,
        readonly=True,
        help="The destruction order associated with this picking."
    )
    shred_job_id = fields.Many2one(
        'project.task',
        string="Shredding Job",
        domain="[('is_shred_job', '=', True)]",
        copy=False,
        help="Field Service job for on-site or off-site shredding."
    )
    
    # Container scanning fields
    scanned_container_id = fields.Many2one(
        'records.container',
        string="Scanned Container",
        help="Last scanned records container"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('picking_type_id.code', 'portal_request_id', 'destruction_order_id')
    def _compute_is_records_management(self):
        """
        Determine if the picking is part of the records management workflow.
        This can be based on the operation type or if it's linked to a RM document.
        """
        for picking in self:
            is_rm = False
            if picking.picking_type_id.code in ('incoming', 'outgoing', 'internal'):
                if picking.portal_request_id or picking.destruction_order_id:
                    is_rm = True
            picking.is_records_management = is_rm

    # ============================================================================
    # BARCODE SCANNING - Container Integration
    # ============================================================================
    def _get_stock_barcode_data(self):
        """
        Override to include records.container barcodes in barcode data.
        This allows the stock barcode app to recognize container barcodes.
        """
        # Call parent method if it exists (stock_barcode enterprise module)
        if hasattr(super(), '_get_stock_barcode_data'):
            data = super()._get_stock_barcode_data()
        else:
            data = {}
        
        # Add container barcodes to the data
        containers = self.env['records.container'].search([
            ('barcode', '!=', False)
        ])
        data['records.container'] = containers.read(['id', 'name', 'barcode', 'display_name', 'location_id'])
        
        return data
    
    def on_barcode_scanned(self, barcode):
        """
        Handle barcode scanning in picking operations.
        Extends standard behavior to recognize records.container barcodes.
        
        Args:
            barcode: The scanned barcode string
            
        Returns:
            dict: Action or notification
        """
        self.ensure_one()
        
        # First, check if this is a records container barcode
        container = self.env['records.container'].search([
            '|',
            ('barcode', '=', barcode),
            ('temp_barcode', '=', barcode)
        ], limit=1)
        
        if container:
            # Found a container - handle it
            self.scanned_container_id = container.id
            
            # If container has a linked product, try to add it to the picking
            if container.product_id:
                # Check if this product is in the picking
                move = self.move_ids.filtered(
                    lambda m: m.product_id == container.product_id and m.state not in ('done', 'cancel')
                )
                if move:
                    # Increment quantity on the move line
                    move_line = move[0].move_line_ids[:1]
                    if move_line:
                        move_line.quantity += 1
                    return {
                        'type': 'ir.actions.client',
                        'tag': 'display_notification',
                        'params': {
                            'title': _('Container Scanned'),
                            'message': _('Container %s added to picking') % container.display_name,
                            'type': 'success',
                            'sticky': False,
                        }
                    }
            
            # Container found but no matching product in picking
            # Open the container form for reference
            return {
                'type': 'ir.actions.act_window',
                'name': _('Container: %s') % container.display_name,
                'res_model': 'records.container',
                'res_id': container.id,
                'view_mode': 'form',
                'target': 'new',
            }
        
        # Not a container barcode - let parent handle it
        if hasattr(super(), 'on_barcode_scanned'):
            return super().on_barcode_scanned(barcode)
        
        # If no parent method, return warning
        return {
            'warning': {
                'title': _('Unknown Barcode'),
                'message': _('Barcode %s not found in products, locations, packages, or containers.') % barcode,
            }
        }

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_related_request(self):
        """
        Action to open the related portal request form view.
        """
        self.ensure_one()
        if not self.portal_request_id:
            raise UserError(_("This picking is not linked to a service request."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'portal.request',
            'view_mode': 'form',
            'res_id': self.portal_request_id.id,
            'target': 'current',
        }
