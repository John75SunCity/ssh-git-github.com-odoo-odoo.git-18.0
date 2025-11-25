from odoo import http
from odoo.http import request
import json


class Warehouse3DDataController(http.Controller):
    
    @http.route('/warehouse/3d/data', type='json', auth='user')
    def get_3d_data(self, config_id, **kw):
        """
        Get 3D visualization data for the warehouse
        
        Args:
            config_id: ID of warehouse.3d.view.config record
        
        Returns:
            dict: Complete 3D visualization data
        """
        config = request.env['warehouse.3d.view.config'].browse(config_id)
        
        if not config.exists():
            return {'error': 'Configuration not found'}
        
        return config.get_3d_visualization_data()
    
    @http.route('/warehouse/3d/container/<int:container_id>', type='json', auth='user')
    def get_container_details(self, container_id, **kw):
        """Get detailed information for a specific container"""
        container = request.env['records.container'].browse(container_id)
        
        if not container.exists():
            return {'error': 'Container not found'}
        
        return {
            'id': container.id,
            'name': container.name,
            'barcode': container.barcode,
            'temp_barcode': container.temp_barcode,
            'customer': {
                'id': container.partner_id.id,
                'name': container.partner_id.name,
            },
            'type': {
                'id': container.container_type_id.id,
                'name': container.container_type_id.name,
                'dimensions': container.container_type_id.dimensions_display,
            } if container.container_type_id else None,
            'location': {
                'id': container.location_id.id,
                'name': container.location_id.name,
                'coordinates': container.location_id.full_coordinates,
            } if container.location_id else None,
            'financial': {
                'monthly_fee': container.monthly_storage_fee,
                'setup_fee': container.setup_fee,
                'total_billed': container.total_billed_amount,
            },
            'metadata': {
                'age_days': container.storage_duration_days,
                'created_date': container.create_date.isoformat() if container.create_date else None,
                'file_folders_count': len(container.file_folder_ids),
                'has_fsm_orders': bool(container.fsm_order_ids),
                'fsm_count': len(container.fsm_order_ids),
                'security_level': container.location_id.security_level if container.location_id else None,
            },
            'status': {
                'state': container.state,
                'active': container.active,
            },
        }
    
    @http.route('/warehouse/3d/export', type='http', auth='user')
    def export_visualization(self, config_id, format='png', **kw):
        """Export 3D visualization as image"""
        # This will be handled client-side using canvas.toDataURL()
        # This endpoint could generate server-side exports if needed
        pass
