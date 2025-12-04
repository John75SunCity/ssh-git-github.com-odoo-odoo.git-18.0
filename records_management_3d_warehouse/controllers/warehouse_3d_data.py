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

    # Blueprint Editor API Routes
    @http.route('/warehouse/blueprint/<int:blueprint_id>/data', type='json', auth='user')
    def get_blueprint_data(self, blueprint_id, **kw):
        """
        Get complete blueprint data for 2D editor

        Returns:
            dict: Blueprint dimensions, walls, zones, shelves, aisles, locations
        """
        blueprint = request.env['warehouse.blueprint'].browse(blueprint_id)

        if not blueprint.exists():
            return {'error': 'Blueprint not found'}

        return blueprint._get_blueprint_editor_data()

    @http.route('/warehouse/blueprint/<int:blueprint_id>/save', type='json', auth='user')
    def save_blueprint_data(self, blueprint_id, data, **kw):
        """
        Save blueprint modifications from 2D editor

        Args:
            blueprint_id: ID of warehouse.blueprint record
            data: dict containing walls, zones, shelves, aisles to update

        Returns:
            dict: Success status and any warnings
        """
        blueprint = request.env['warehouse.blueprint'].browse(blueprint_id)

        if not blueprint.exists():
            return {'error': 'Blueprint not found'}

        try:
            blueprint._save_blueprint_editor_data(data)
            return {'success': True}
        except Exception as e:
            return {'error': str(e)}

    @http.route('/warehouse/blueprint/<int:blueprint_id>/navigate', type='json', auth='user')
    def get_navigation_path(self, blueprint_id, start_location_id, end_location_id, **kw):
        """
        Calculate navigation path between two locations using A* algorithm

        Args:
            blueprint_id: ID of warehouse.blueprint record
            start_location_id: Starting stock.location ID
            end_location_id: Destination stock.location ID

        Returns:
            dict: Path coordinates, turn-by-turn directions, distance, estimated time
        """
        blueprint = request.env['warehouse.blueprint'].browse(blueprint_id)

        if not blueprint.exists():
            return {'error': 'Blueprint not found'}

        return blueprint._calculate_navigation_path(start_location_id, end_location_id)

    @http.route('/warehouse/blueprint/<int:blueprint_id>/export', type='json', auth='user')
    def export_blueprint_coordinates(self, blueprint_id, format='json', **kw):
        """
        Export blueprint coordinates for 3D integration

        Args:
            blueprint_id: ID of warehouse.blueprint record
            format: Export format (json, csv, geojson)

        Returns:
            dict/str: Exported data in requested format
        """
        blueprint = request.env['warehouse.blueprint'].browse(blueprint_id)

        if not blueprint.exists():
            return {'error': 'Blueprint not found'}

        return blueprint._export_coordinates(format)

    @http.route('/warehouse/blueprint/<int:blueprint_id>/locations', type='json', auth='user')
    def get_blueprint_locations(self, blueprint_id, **kw):
        """
        Get all locations for a blueprint for navigation endpoints

        Returns:
            list: List of locations with id, name, barcode, coordinates
        """
        blueprint = request.env['warehouse.blueprint'].browse(blueprint_id)

        if not blueprint.exists():
            return {'error': 'Blueprint not found'}

        # Get all locations associated with this blueprint's warehouse
        locations = request.env['stock.location'].search([
            ('warehouse_blueprint_id', '=', blueprint_id),
            ('usage', '=', 'internal'),
        ])

        return [{
            'id': loc.id,
            'name': loc.name,
            'barcode': loc.barcode or '',
            'posx': loc.posx or 0,
            'posy': loc.posy or 0,
            'posz': loc.posz or 0,
            'current_usage': len(loc.container_ids) if hasattr(loc, 'container_ids') else 0,
            'max_capacity': loc.max_capacity if hasattr(loc, 'max_capacity') else 0,
        } for loc in locations]
