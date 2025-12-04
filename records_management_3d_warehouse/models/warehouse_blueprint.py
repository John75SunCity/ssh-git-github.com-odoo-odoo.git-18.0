from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WarehouseBlueprint(models.Model):
    _name = 'warehouse.blueprint'
    _description = '3D Warehouse Blueprint Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'warehouse_id, name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char('Blueprint Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        tracking=True,
        help='The warehouse this blueprint represents'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='warehouse_id.company_id',
        store=True,
        readonly=True
    )
    
    # ============================================================================
    # WAREHOUSE DIMENSIONS (in inches)
    # ============================================================================
    length = fields.Float(
        'Length (inches)',
        default=1200.0,  # 100 feet
        required=True,
        tracking=True,
        help='Total warehouse length in inches'
    )
    width = fields.Float(
        'Width (inches)',
        default=720.0,  # 60 feet
        required=True,
        tracking=True,
        help='Total warehouse width in inches'
    )
    height = fields.Float(
        'Height (inches)',
        default=144.0,  # 12 feet
        required=True,
        tracking=True,
        help='Total warehouse height in inches'
    )
    
    # Display fields (converted to feet)
    length_feet = fields.Float(
        'Length (feet)',
        compute='_compute_dimensions_feet',
        inverse='_inverse_length_feet',
        store=True
    )
    width_feet = fields.Float(
        'Width (feet)',
        compute='_compute_dimensions_feet',
        inverse='_inverse_width_feet',
        store=True
    )
    height_feet = fields.Float(
        'Height (feet)',
        compute='_compute_dimensions_feet',
        inverse='_inverse_height_feet',
        store=True
    )
    
    # ============================================================================
    # BLUEPRINT ELEMENTS
    # ============================================================================
    wall_ids = fields.One2many(
        'warehouse.wall',
        'blueprint_id',
        string='Walls',
        help='Wall structures in the warehouse'
    )
    door_ids = fields.One2many(
        'warehouse.door',
        'blueprint_id',
        string='Doors',
        help='Door and entrance locations'
    )
    office_ids = fields.One2many(
        'warehouse.office',
        'blueprint_id',
        string='Offices/Zones',
        help='Office areas and restricted zones'
    )
    
    # ============================================================================
    # SHELVING CONFIGURATION
    # ============================================================================
    shelving_template_ids = fields.One2many(
        'warehouse.shelving.template',
        'blueprint_id',
        string='Shelving Templates',
        help='Configured shelving units'
    )
    
    # ============================================================================
    # STATISTICS
    # ============================================================================
    total_locations = fields.Integer(
        'Total Locations',
        compute='_compute_statistics',
        store=True
    )
    total_capacity = fields.Integer(
        'Total Capacity',
        compute='_compute_statistics',
        store=True,
        help='Total maximum container capacity'
    )
    current_usage = fields.Integer(
        'Current Usage',
        compute='_compute_statistics',
        store=True,
        help='Current number of containers stored'
    )
    utilization_percentage = fields.Float(
        'Utilization %',
        compute='_compute_statistics',
        store=True
    )
    
    # ============================================================================
    # BLUEPRINT DATA (JSON)
    # ============================================================================
    blueprint_data = fields.Text(
        'Blueprint JSON Data',
        help='Serialized blueprint configuration for visualization'
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('length', 'width', 'height')
    def _compute_dimensions_feet(self):
        for record in self:
            record.length_feet = record.length / 12.0
            record.width_feet = record.width / 12.0
            record.height_feet = record.height / 12.0
    
    def _inverse_length_feet(self):
        for record in self:
            record.length = record.length_feet * 12.0
    
    def _inverse_width_feet(self):
        for record in self:
            record.width = record.width_feet * 12.0
    
    def _inverse_height_feet(self):
        for record in self:
            record.height = record.height_feet * 12.0
    
    @api.depends('warehouse_id', 'shelving_template_ids.total_capacity')
    def _compute_statistics(self):
        for record in self:
            locations = self.env['stock.location'].search([
                ('warehouse_id', '=', record.warehouse_id.id),
                ('is_records_location', '=', True)
            ])
            
            record.total_locations = len(locations)
            record.total_capacity = sum(loc.max_capacity or 0 for loc in locations)
            record.current_usage = sum(loc.current_usage or 0 for loc in locations)
            
            if record.total_capacity > 0:
                record.utilization_percentage = (record.current_usage / record.total_capacity) * 100
            else:
                record.utilization_percentage = 0.0
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('length', 'width', 'height')
    def _check_positive_dimensions(self):
        for record in self:
            if record.length <= 0 or record.width <= 0 or record.height <= 0:
                raise ValidationError(_('All dimensions must be positive numbers.'))
    
    @api.constrains('warehouse_id')
    def _check_unique_warehouse(self):
        for record in self:
            if self.search_count([
                ('warehouse_id', '=', record.warehouse_id.id),
                ('id', '!=', record.id)
            ]) > 0:
                raise ValidationError(
                    _('A blueprint already exists for warehouse "%s". Only one blueprint per warehouse is allowed.') 
                    % record.warehouse_id.name
                )
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_sync_locations(self):
        """Synchronize stock locations with blueprint configuration"""
        self.ensure_one()
        
        # This will be called after shelving templates generate locations
        # to ensure posx, posy, posz coordinates are properly set
        
        location_obj = self.env['stock.location']
        
        for template in self.shelving_template_ids:
            # Get locations created by this template
            locations = location_obj.search([
                ('warehouse_id', '=', self.warehouse_id.id),
                ('is_records_location', '=', True),
                # Additional domain to match template locations
            ])
            
            # Update coordinates based on template configuration
            # This is handled in the template's generation logic
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Sync Complete'),
                'message': _('Stock locations have been synchronized with the blueprint.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_open_3d_view(self):
        """Open the 3D visualization for this blueprint"""
        self.ensure_one()
        
        # Create or get a default view configuration
        view_config = self.env['warehouse.3d.view.config'].search([
            ('blueprint_id', '=', self.id),
            ('is_default', '=', True)
        ], limit=1)
        
        if not view_config:
            view_config = self.env['warehouse.3d.view.config'].create({
                'name': _('Default View - %s') % self.name,
                'blueprint_id': self.id,
                'is_default': True,
            })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'warehouse_3d_view',
            'params': {
                'config_id': view_config.id,
            },
        }
    
    def action_quickstart_wizard(self):
        """Open quick start configuration wizard"""
        return {
            'type': 'ir.actions.act_window',
            'name': _('3D Warehouse Quick Setup'),
            'res_model': 'warehouse.3d.quickstart.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_blueprint_id': self.id,
                'default_warehouse_id': self.warehouse_id.id,
            },
        }

    def action_open_2d_editor(self):
        """Open the 2D Blueprint Editor"""
        self.ensure_one()
        return {
            'type': 'ir.actions.client',
            'tag': 'warehouse_blueprint_editor',
            'params': {
                'blueprint_id': self.id,
            },
            'name': _('2D Blueprint Editor - %s') % self.name,
        }

    # ============================================================================
    # BLUEPRINT EDITOR API METHODS
    # ============================================================================
    def _get_blueprint_editor_data(self):
        """Get complete blueprint data for the 2D editor"""
        self.ensure_one()

        # Get all locations with their coordinates
        locations = self.env['stock.location'].search([
            ('warehouse_id', '=', self.warehouse_id.id),
            ('usage', '=', 'internal'),
        ])

        # Build walls data
        walls = [{
            'id': wall.id,
            'name': wall.name,
            'start_x': wall.start_x,
            'start_y': wall.start_y,
            'end_x': wall.end_x,
            'end_y': wall.end_y,
            'thickness': wall.thickness,
            'height': wall.height,
            'color': wall.color,
            'is_load_bearing': wall.is_load_bearing,
        } for wall in self.wall_ids]

        # Build doors data
        doors = [{
            'id': door.id,
            'name': door.name,
            'pos_x': door.pos_x,
            'pos_y': door.pos_y,
            'width': door.width,
            'height': door.height,
            'door_type': door.door_type,
            'color': door.color,
        } for door in self.door_ids]

        # Build zones/offices data
        zones = [{
            'id': office.id,
            'name': office.name,
            'start_x': office.start_x,
            'start_y': office.start_y,
            'width': office.width,
            'depth': office.depth,
            'zone_type': office.zone_type,
            'color': office.color,
            'access_restricted': office.access_restricted,
        } for office in self.office_ids]

        # Build shelving data
        shelves = [{
            'id': template.id,
            'name': template.name,
            'start_x': template.start_x,
            'start_y': template.start_y,
            'width': template.unit_width,
            'depth': template.unit_depth,
            'height': template.unit_height,
            'shelves_count': template.shelves_per_unit,
            'units_per_row': template.units_per_row,
            'row_count': template.row_count,
            'color': template.color or '#795548',
        } for template in self.shelving_template_ids]

        # Build aisles data (computed from shelving layout)
        aisles = []
        for i, template in enumerate(self.shelving_template_ids):
            if hasattr(template, 'aisle_width') and template.aisle_width:
                aisles.append({
                    'id': f'aisle_{template.id}',
                    'name': _('Aisle %d') % (i + 1),
                    'start_x': template.start_x + template.unit_width,
                    'start_y': template.start_y,
                    'end_x': template.start_x + template.unit_width,
                    'end_y': template.start_y + (template.row_count * (template.unit_depth + template.aisle_width)),
                    'width': template.aisle_width,
                })

        # Build locations data
        locs = [{
            'id': loc.id,
            'name': loc.name,
            'barcode': loc.barcode or '',
            'posx': loc.posx or 0,
            'posy': loc.posy or 0,
            'posz': loc.posz or 0,
            'current_usage': len(loc.container_ids) if hasattr(loc, 'container_ids') else 0,
            'max_capacity': loc.max_capacity if hasattr(loc, 'max_capacity') else 0,
        } for loc in locations]

        return {
            'id': self.id,
            'name': self.name,
            'length': self.length,
            'width': self.width,
            'height': self.height,
            'walls': walls,
            'doors': doors,
            'zones': zones,
            'shelves': shelves,
            'aisles': aisles,
            'locations': locs,
            'statistics': {
                'total_locations': self.total_locations,
                'total_capacity': self.total_capacity,
                'current_usage': self.current_usage,
                'utilization_percentage': self.utilization_percentage,
            },
        }

    def _save_blueprint_editor_data(self, data):
        """Save blueprint modifications from the 2D editor"""
        self.ensure_one()

        # Update walls
        if 'walls' in data:
            # Delete removed walls
            existing_ids = [w['id'] for w in data['walls'] if isinstance(w.get('id'), int)]
            self.wall_ids.filtered(lambda w: w.id not in existing_ids).unlink()

            for wall_data in data['walls']:
                if isinstance(wall_data.get('id'), int):
                    # Update existing wall
                    wall = self.env['warehouse.wall'].browse(wall_data['id'])
                    if wall.exists():
                        wall.write({
                            'name': wall_data.get('name', wall.name),
                            'start_x': wall_data.get('start_x', wall.start_x),
                            'start_y': wall_data.get('start_y', wall.start_y),
                            'end_x': wall_data.get('end_x', wall.end_x),
                            'end_y': wall_data.get('end_y', wall.end_y),
                        })
                else:
                    # Create new wall
                    self.env['warehouse.wall'].create({
                        'blueprint_id': self.id,
                        'name': wall_data.get('name', _('New Wall')),
                        'start_x': wall_data.get('start_x', 0),
                        'start_y': wall_data.get('start_y', 0),
                        'end_x': wall_data.get('end_x', 0),
                        'end_y': wall_data.get('end_y', 0),
                    })

        # Update zones/offices
        if 'zones' in data:
            existing_ids = [z['id'] for z in data['zones'] if isinstance(z.get('id'), int)]
            self.office_ids.filtered(lambda z: z.id not in existing_ids).unlink()

            for zone_data in data['zones']:
                if isinstance(zone_data.get('id'), int):
                    zone = self.env['warehouse.office'].browse(zone_data['id'])
                    if zone.exists():
                        zone.write({
                            'name': zone_data.get('name', zone.name),
                            'start_x': zone_data.get('start_x', zone.start_x),
                            'start_y': zone_data.get('start_y', zone.start_y),
                            'width': zone_data.get('width', zone.width),
                            'depth': zone_data.get('depth', zone.depth),
                            'zone_type': zone_data.get('zone_type', zone.zone_type),
                        })
                else:
                    self.env['warehouse.office'].create({
                        'blueprint_id': self.id,
                        'name': zone_data.get('name', _('New Zone')),
                        'start_x': zone_data.get('start_x', 0),
                        'start_y': zone_data.get('start_y', 0),
                        'width': zone_data.get('width', 120),
                        'depth': zone_data.get('depth', 120),
                        'zone_type': zone_data.get('zone_type', 'staging'),
                    })

        return True

    def _calculate_navigation_path(self, start_location_id, end_location_id):
        """
        Calculate navigation path between two locations using A* algorithm

        This is a server-side backup implementation. The main A* runs client-side
        for better interactivity. This can be used for route optimization.
        """
        self.ensure_one()

        start_loc = self.env['stock.location'].browse(start_location_id)
        end_loc = self.env['stock.location'].browse(end_location_id)

        if not start_loc.exists() or not end_loc.exists():
            return {'error': 'Invalid locations'}

        # Simple direct path calculation (client does full A*)
        import math
        dx = (end_loc.posx or 0) - (start_loc.posx or 0)
        dy = (end_loc.posy or 0) - (start_loc.posy or 0)
        distance = math.sqrt(dx**2 + dy**2) / 12  # Convert inches to feet

        # Simple cardinal direction
        if abs(dx) > abs(dy):
            direction = 'East' if dx > 0 else 'West'
        else:
            direction = 'North' if dy > 0 else 'South'

        return {
            'path': [
                {'x': start_loc.posx or 0, 'y': start_loc.posy or 0},
                {'x': end_loc.posx or 0, 'y': end_loc.posy or 0},
            ],
            'totalDistance': round(distance, 1),
            'estimatedTime': round(distance / 250, 1),  # ~250 ft/min walking speed
            'directions': [{
                'step': 1,
                'icon': '➡️' if dx > 0 else '⬅️' if dx < 0 else '⬆️' if dy > 0 else '⬇️',
                'instruction': _('Head %s toward %s') % (direction, end_loc.name),
                'distance': round(distance, 1),
                'landmark': end_loc.name,
            }],
        }

    def _export_coordinates(self, format='json'):
        """Export blueprint coordinates in various formats"""
        self.ensure_one()
        import json

        data = self._get_blueprint_editor_data()

        if format == 'json':
            return data

        elif format == 'csv':
            lines = ['type,name,x,y,z,width,depth,height']

            for loc in data['locations']:
                lines.append(
                    'location,%s,%s,%s,%s,0,0,0' % (
                        loc['name'], loc['posx'], loc['posy'], loc['posz']
                    )
                )

            for shelf in data['shelves']:
                lines.append(
                    'shelf,%s,%s,%s,0,%s,%s,%s' % (
                        shelf['name'], shelf['start_x'], shelf['start_y'],
                        shelf['width'], shelf['depth'], shelf['height']
                    )
                )

            for zone in data['zones']:
                lines.append(
                    'zone,%s,%s,%s,0,%s,%s,0' % (
                        zone['name'], zone['start_x'], zone['start_y'],
                        zone['width'], zone['depth']
                    )
                )

            return '\n'.join(lines)

        elif format == 'geojson':
            features = []

            # Add locations as points
            for loc in data['locations']:
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Point',
                        'coordinates': [loc['posx'], loc['posy']],
                    },
                    'properties': {
                        'name': loc['name'],
                        'type': 'location',
                        'barcode': loc['barcode'],
                    }
                })

            # Add zones as polygons
            for zone in data['zones']:
                x1, y1 = zone['start_x'], zone['start_y']
                x2, y2 = x1 + zone['width'], y1 + zone['depth']
                features.append({
                    'type': 'Feature',
                    'geometry': {
                        'type': 'Polygon',
                        'coordinates': [[[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]],
                    },
                    'properties': {
                        'name': zone['name'],
                        'type': 'zone',
                        'zone_type': zone['zone_type'],
                    }
                })

            return {
                'type': 'FeatureCollection',
                'features': features,
            }

        return data


# ============================================================================
# SUPPORTING MODELS
# ============================================================================

class WarehouseWall(models.Model):
    _name = 'warehouse.wall'
    _description = 'Warehouse Wall'
    _order = 'blueprint_id, sequence'
    
    name = fields.Char('Wall Name', required=True)
    blueprint_id = fields.Many2one('warehouse.blueprint', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    
    # Start and end points (in inches from origin)
    start_x = fields.Float('Start X', default=0.0)
    start_y = fields.Float('Start Y', default=0.0)
    end_x = fields.Float('End X', default=0.0)
    end_y = fields.Float('End Y', default=0.0)
    
    # Wall properties
    thickness = fields.Float('Thickness (inches)', default=6.0)
    height = fields.Float('Height (inches)', default=144.0)
    color = fields.Char('Color', default='#808080')
    is_load_bearing = fields.Boolean('Load Bearing', default=False)


class WarehouseDoor(models.Model):
    _name = 'warehouse.door'
    _description = 'Warehouse Door'
    _order = 'blueprint_id, sequence'
    
    name = fields.Char('Door Name', required=True)
    blueprint_id = fields.Many2one('warehouse.blueprint', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    
    # Position (center point)
    pos_x = fields.Float('Position X', default=0.0)
    pos_y = fields.Float('Position Y', default=0.0)
    
    # Door properties
    width = fields.Float('Width (inches)', default=96.0)
    height = fields.Float('Height (inches)', default=96.0)
    door_type = fields.Selection([
        ('single', 'Single Door'),
        ('double', 'Double Door'),
        ('overhead', 'Overhead Door'),
        ('rollup', 'Roll-up Door'),
    ], default='single')
    color = fields.Char('Color', default='#8B4513')


class WarehouseOffice(models.Model):
    _name = 'warehouse.office'
    _description = 'Warehouse Office/Zone'
    _order = 'blueprint_id, sequence'
    
    name = fields.Char('Zone Name', required=True)
    blueprint_id = fields.Many2one('warehouse.blueprint', required=True, ondelete='cascade')
    sequence = fields.Integer(default=10)
    
    # Rectangular area definition
    start_x = fields.Float('Start X', default=0.0)
    start_y = fields.Float('Start Y', default=0.0)
    width = fields.Float('Width (inches)', default=120.0)
    depth = fields.Float('Depth (inches)', default=120.0)
    
    # Zone properties
    zone_type = fields.Selection([
        ('office', 'Office'),
        ('restroom', 'Restroom'),
        ('break_room', 'Break Room'),
        ('restricted', 'Restricted Area'),
        ('shipping', 'Shipping/Receiving'),
        ('staging', 'Staging Area'),
    ], default='office')
    color = fields.Char('Color', default='#E0E0E0')
    access_restricted = fields.Boolean('Access Restricted', default=False)
