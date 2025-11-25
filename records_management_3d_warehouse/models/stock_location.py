from odoo import models, fields, api


class StockLocation(models.Model):
    _inherit = 'stock.location'
    
    # These fields already exist in records_management, but we add helpers
    
    # Computed full hierarchical coordinates
    @api.depends('building', 'floor', 'zone', 'aisle', 'rack', 'shelf', 'position')
    def _compute_full_coordinates(self):
        """Override to ensure proper coordinate computation"""
        for record in self:
            parts = []
            if record.building:
                parts.append(record.building)
            if record.floor:
                parts.append(record.floor)
            if record.zone:
                parts.append(record.zone)
            if record.aisle:
                parts.append(record.aisle)
            if record.rack:
                parts.append(record.rack)
            if record.shelf:
                parts.append(record.shelf)
            if record.position:
                parts.append(record.position)
            
            record.full_coordinates = ' / '.join(parts) if parts else record.name
    
    def action_open_in_3d_view(self):
        """Open 3D view focused on this location"""
        self.ensure_one()
        
        # Find blueprint for this warehouse
        blueprint = self.env['warehouse.blueprint'].search([
            ('warehouse_id', '=', self.warehouse_id.id)
        ], limit=1)
        
        if not blueprint:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'No Blueprint',
                    'message': 'No 3D blueprint configured for this warehouse.',
                    'type': 'warning',
                    'sticky': False,
                }
            }
        
        # Get or create view config
        view_config = self.env['warehouse.3d.view.config'].search([
            ('blueprint_id', '=', blueprint.id),
            ('is_default', '=', True)
        ], limit=1)
        
        if not view_config:
            view_config = self.env['warehouse.3d.view.config'].create({
                'name': f'Default View - {blueprint.name}',
                'blueprint_id': blueprint.id,
                'is_default': True,
            })
        
        # Set location filter to highlight this location
        view_config.write({
            'location_ids': [(6, 0, [self.id])],
        })
        
        return view_config.action_open_3d_view()
