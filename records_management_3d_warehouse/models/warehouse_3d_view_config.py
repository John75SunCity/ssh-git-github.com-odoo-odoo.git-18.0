from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import json


class Warehouse3DViewConfig(models.Model):
    _name = 'warehouse.3d.view.config'
    _description = '3D Warehouse View Configuration'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'blueprint_id, sequence, name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char('View Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    blueprint_id = fields.Many2one(
        'warehouse.blueprint',
        string='Blueprint',
        required=True,
        tracking=True
    )
    sequence = fields.Integer(default=10)
    is_default = fields.Boolean(
        'Default View',
        help='Default view for this blueprint'
    )
    
    # ============================================================================
    # VISUALIZATION MODE
    # ============================================================================
    view_mode = fields.Selection([
        ('capacity', '📦 Capacity Utilization'),
        ('revenue', '💰 Revenue per Container'),
        ('customer', '👤 By Customer'),
        ('age_fifo', '⏳ Container Age (Oldest First - FIFO)'),
        ('age_lifo', '🆕 Container Age (Newest First - LIFO)'),
        ('fsm_orders', '🔧 Active FSM Work Orders'),
        ('metadata', '📋 Container Metadata'),
        ('security', '🔒 Security Levels'),
        ('temperature', '🌡️ Climate Control'),
        ('file_folders', '📁 Contains File Folders'),
    ], default='capacity', required=True, tracking=True)
    
    # ============================================================================
    # COLOR SCHEME
    # ============================================================================
    color_scheme = fields.Selection([
        ('heatmap_red_green', 'Heat Map: Red (Empty) → Green (Full)'),
        ('heatmap_blue_red', 'Heat Map: Blue (Low) → Red (High)'),
        ('gradient_age', 'Gradient: Gray (Old) → Yellow (New)'),
        ('rainbow_customer', 'Rainbow by Customer'),
        ('status_categorical', 'Categorical by Status'),
        ('custom', 'Custom Colors'),
    ], default='heatmap_red_green', tracking=True)
    
    # ============================================================================
    # TIME FILTERING (Time Travel Feature)
    # ============================================================================
    enable_time_filter = fields.Boolean(
        'Enable Time Filter',
        default=False,
        help='Filter containers by date range'
    )
    snapshot_date = fields.Datetime(
        'Snapshot Date',
        help='View warehouse state as of this specific date/time'
    )
    date_from = fields.Date('From Date')
    date_to = fields.Date('To Date')
    
    # ============================================================================
    # FILTERS
    # ============================================================================
    customer_ids = fields.Many2many(
        'res.partner',
        string='Filter by Customers',
        domain="[('is_records_customer', '=', True)]"
    )
    location_ids = fields.Many2many(
        'stock.location',
        string='Filter by Locations'
    )
    container_type_ids = fields.Many2many(
        'product.container.type',
        string='Filter by Container Types'
    )
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], string='Security Level Filter')
    
    show_empty_locations = fields.Boolean(
        'Show Empty Locations',
        default=False,
        help='Display locations with no containers'
    )
    
    # ============================================================================
    # FSM INTEGRATION
    # ============================================================================
    fsm_order_id = fields.Many2one(
        'project.task',
        string='FSM Work Order',
        domain="[('is_fsm', '=', True)]",
        help='Highlight containers in this work order'
    )
    
    # ============================================================================
    # DISPLAY SETTINGS
    # ============================================================================
    show_grid = fields.Boolean('Show Grid', default=True)
    show_legend = fields.Boolean('Show Legend', default=True)
    show_tooltips = fields.Boolean('Show Tooltips', default=True)
    show_warehouse_structure = fields.Boolean(
        'Show Warehouse Structure',
        default=True,
        help='Display walls, doors, and offices'
    )
    
    # Camera settings
    camera_horizontal = fields.Float('Camera Horizontal', default=-0.35)
    camera_vertical = fields.Float('Camera Vertical', default=0.22)
    camera_distance = fields.Float('Camera Distance', default=1.8)
    
    # ============================================================================
    # STATISTICS (Computed from current filters)
    # ============================================================================
    total_containers = fields.Integer(
        'Total Containers',
        compute='_compute_statistics'
    )
    total_revenue = fields.Monetary(
        'Total Revenue',
        compute='_compute_statistics',
        currency_field='currency_id'
    )
    currency_id = fields.Many2one(
        'res.currency',
        related='blueprint_id.company_id.currency_id'
    )
    average_age_days = fields.Float(
        'Average Age (Days)',
        compute='_compute_statistics'
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('blueprint_id', 'customer_ids', 'container_type_ids', 'date_from', 'date_to')
    def _compute_statistics(self):
        for record in self:
            containers = record._get_filtered_containers()
            
            record.total_containers = len(containers)
            record.total_revenue = sum(c.monthly_storage_fee or 0 for c in containers)
            
            if containers:
                total_days = sum(c.storage_duration_days or 0 for c in containers)
                record.average_age_days = total_days / len(containers)
            else:
                record.average_age_days = 0.0
    
    def _get_filtered_containers(self):
        """Get containers based on current filters"""
        domain = [('active', '=', True)]
        
        # Warehouse filter
        if self.blueprint_id and self.blueprint_id.warehouse_id:
            location_ids = self.env['stock.location'].search([
                ('warehouse_id', '=', self.blueprint_id.warehouse_id.id),
                ('is_records_location', '=', True)
            ]).ids
            domain.append(('location_id', 'in', location_ids))
        
        # Customer filter
        if self.customer_ids:
            domain.append(('partner_id', 'in', self.customer_ids.ids))
        
        # Container type filter
        if self.container_type_ids:
            domain.append(('container_type_id', 'in', self.container_type_ids.ids))
        
        # Date range filter
        if self.date_from:
            domain.append(('create_date', '>=', self.date_from))
        if self.date_to:
            domain.append(('create_date', '<=', self.date_to))
        
        return self.env['records.container'].search(domain)
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('blueprint_id', 'is_default')
    def _check_single_default(self):
        for record in self:
            if record.is_default:
                other_defaults = self.search([
                    ('blueprint_id', '=', record.blueprint_id.id),
                    ('is_default', '=', True),
                    ('id', '!=', record.id)
                ])
                if other_defaults:
                    raise ValidationError(
                        _('Only one default view is allowed per blueprint.')
                    )
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_open_3d_view(self):
        """Open the 3D visualization"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'warehouse_3d_view',
            'params': {
                'config_id': self.id,
            },
        }
    
    def get_3d_visualization_data(self):
        """Get data for 3D visualization (called from controller)"""
        self.ensure_one()
        
        blueprint = self.blueprint_id
        warehouse = blueprint.warehouse_id
        
        # Get all locations in this warehouse
        locations = self.env['stock.location'].search([
            ('warehouse_id', '=', warehouse.id),
            ('is_records_location', '=', True),
            ('usage', '=', 'internal'),
        ])
        
        if not self.show_empty_locations:
            locations = locations.filtered(lambda l: l.container_count > 0)
        
        # Apply location filter
        if self.location_ids:
            locations = locations.filtered(lambda l: l.id in self.location_ids.ids)
        
        # Build data points
        data_points = []
        max_value = 0.0
        
        for loc in locations:
            containers = loc.container_ids
            
            # Apply filters
            if self.customer_ids:
                containers = containers.filtered(lambda c: c.partner_id.id in self.customer_ids.ids)
            if self.container_type_ids:
                containers = containers.filtered(lambda c: c.container_type_id.id in self.container_type_ids.ids)
            
            if not containers and not self.show_empty_locations:
                continue
            
            # Calculate value based on view mode
            value = self._calculate_view_value(loc, containers)
            max_value = max(max_value, value)
            
            # Build data point
            point = {
                'id': loc.id,
                'name': loc.name,
                'x': loc.posx or 0,
                'y': loc.posy or 0,
                'z': loc.posz or 0,
                'coordinates': loc.full_coordinates or loc.name,
                'container_count': len(containers),
                'container_ids': containers.ids,
                'capacity': loc.max_capacity or 0,
                'utilization': loc.utilization_percentage or 0,
                'value': value,
                'containers_data': self._get_containers_metadata(containers),
            }
            
            data_points.append(point)
        
        # Calculate colors for all points
        for point in data_points:
            point['color'] = self._calculate_color(point['value'], max_value)
        
        # Build blueprint structure
        blueprint_data = {
            'length': blueprint.length,
            'width': blueprint.width,
            'height': blueprint.height,
            'walls': [self._wall_to_dict(w) for w in blueprint.wall_ids] if self.show_warehouse_structure else [],
            'doors': [self._door_to_dict(d) for d in blueprint.door_ids] if self.show_warehouse_structure else [],
            'offices': [self._office_to_dict(o) for o in blueprint.office_ids] if self.show_warehouse_structure else [],
        }
        
        return {
            'blueprint': blueprint_data,
            'data_points': data_points,
            'view_mode': self.view_mode,
            'color_scheme': self.color_scheme,
            'max_value': max_value,
            'settings': {
                'show_grid': self.show_grid,
                'show_legend': self.show_legend,
                'show_tooltips': self.show_tooltips,
                'camera_horizontal': self.camera_horizontal,
                'camera_vertical': self.camera_vertical,
                'camera_distance': self.camera_distance,
            },
            'legend': self._generate_legend(),
        }
    
    def _calculate_view_value(self, location, containers):
        """Calculate numeric value for visualization based on view mode"""
        if self.view_mode == 'capacity':
            return location.utilization_percentage or 0
        
        elif self.view_mode == 'revenue':
            return sum(c.monthly_storage_fee or 0 for c in containers)
        
        elif self.view_mode == 'customer':
            # Return customer ID for color mapping
            if containers:
                return containers[0].partner_id.id
            return 0
        
        elif self.view_mode in ('age_fifo', 'age_lifo'):
            if containers:
                ages = [c.storage_duration_days or 0 for c in containers]
                return sum(ages) / len(ages)  # Average age
            return 0
        
        elif self.view_mode == 'fsm_orders':
            # Count containers with FSM orders
            fsm_count = len(containers.filtered(lambda c: c.fsm_order_ids))
            return fsm_count
        
        elif self.view_mode == 'metadata':
            # Count metadata items (file folders, documents, etc.)
            metadata_count = sum(len(c.file_folder_ids) for c in containers)
            return metadata_count
        
        elif self.view_mode == 'security':
            # Return numeric security level
            security_map = {'public': 1, 'internal': 2, 'confidential': 3, 'restricted': 4}
            return security_map.get(location.security_level, 0)
        
        elif self.view_mode == 'temperature':
            return 1 if location.temperature_controlled else 0
        
        elif self.view_mode == 'file_folders':
            return sum(len(c.file_folder_ids) for c in containers)
        
        return 0
    
    def _calculate_color(self, value, max_value):
        """Calculate color based on value and color scheme"""
        if self.color_scheme == 'heatmap_red_green':
            # Red (low) → Green (high)
            if max_value == 0:
                return '#808080'
            ratio = value / max_value
            r = int((1 - ratio) * 255)
            g = int(ratio * 255)
            return f'#{r:02x}{g:02x}00'
        
        elif self.color_scheme == 'heatmap_blue_red':
            # Blue (low) → Red (high)
            if max_value == 0:
                return '#808080'
            ratio = value / max_value
            r = int(ratio * 255)
            b = int((1 - ratio) * 255)
            return f'#{r:02x}00{b:02x}'
        
        elif self.color_scheme == 'gradient_age':
            # Gray (old) → Yellow (new)
            if max_value == 0:
                return '#808080'
            ratio = value / max_value
            yellow = int(ratio * 255)
            return f'#{yellow:02x}{yellow:02x}00'
        
        elif self.color_scheme == 'rainbow_customer':
            # Consistent color per customer using golden angle
            hue = (value * 137.508) % 360
            return self._hsl_to_hex(hue, 70, 50)
        
        return '#0066CC'  # Default blue
    
    def _hsl_to_hex(self, h, s, l):
        """Convert HSL to HEX color"""
        # Simplified conversion
        import colorsys
        r, g, b = colorsys.hls_to_rgb(h/360, l/100, s/100)
        return f'#{int(r*255):02x}{int(g*255):02x}{int(b*255):02x}'
    
    def _get_containers_metadata(self, containers):
        """Get metadata for containers"""
        data = []
        for container in containers:
            data.append({
                'id': container.id,
                'name': container.name,
                'barcode': container.barcode,
                'customer': container.partner_id.name,
                'customer_id': container.partner_id.id,
                'type': container.container_type_id.name if container.container_type_id else 'N/A',
                'monthly_fee': container.monthly_storage_fee or 0,
                'age_days': container.storage_duration_days or 0,
                'has_fsm': bool(container.fsm_order_ids),
                'has_files': bool(container.file_folder_ids),
                'file_count': len(container.file_folder_ids),
                'security_level': container.location_id.security_level or 'internal',
            })
        return data
    
    def _wall_to_dict(self, wall):
        return {
            'name': wall.name,
            'start_x': wall.start_x,
            'start_y': wall.start_y,
            'end_x': wall.end_x,
            'end_y': wall.end_y,
            'thickness': wall.thickness,
            'height': wall.height,
            'color': wall.color,
        }
    
    def _door_to_dict(self, door):
        return {
            'name': door.name,
            'x': door.pos_x,
            'y': door.pos_y,
            'width': door.width,
            'height': door.height,
            'type': door.door_type,
            'color': door.color,
        }
    
    def _office_to_dict(self, office):
        return {
            'name': office.name,
            'x': office.start_x,
            'y': office.start_y,
            'width': office.width,
            'depth': office.depth,
            'type': office.zone_type,
            'color': office.color,
            'restricted': office.access_restricted,
        }
    
    def _generate_legend(self):
        """Generate legend data for the view"""
        legend = {
            'title': dict(self._fields['view_mode'].selection).get(self.view_mode),
            'items': [],
        }
        
        if self.view_mode == 'capacity':
            legend['items'] = [
                {'label': '0-25% Full', 'color': '#FF0000'},
                {'label': '25-50% Full', 'color': '#FF8800'},
                {'label': '50-75% Full', 'color': '#FFFF00'},
                {'label': '75-100% Full', 'color': '#00FF00'},
            ]
        elif self.view_mode == 'revenue':
            legend['items'] = [
                {'label': 'Low Revenue', 'color': '#0000FF'},
                {'label': 'Medium Revenue', 'color': '#8800FF'},
                {'label': 'High Revenue', 'color': '#FF0000'},
            ]
        
        return legend
