from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class WarehouseShelvingTemplate(models.Model):
    _name = 'warehouse.shelving.template'
    _description = 'Warehouse Shelving Template'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'blueprint_id, sequence, name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char('Template Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    blueprint_id = fields.Many2one(
        'warehouse.blueprint',
        string='Blueprint',
        tracking=True,
        help='The blueprint this shelving belongs to'
    )
    sequence = fields.Integer(default=10)
    
    # ============================================================================
    # SHELVING DIMENSIONS (in inches)
    # ============================================================================
    shelving_width = fields.Float(
        'Shelf Width (inches)',
        default=48.0,
        required=True,
        tracking=True,
        help='Width of each shelving unit'
    )
    shelving_depth = fields.Float(
        'Shelf Depth (inches)',
        default=24.0,
        required=True,
        tracking=True,
        help='Depth of each shelf'
    )
    shelving_height = fields.Float(
        'Total Height (inches)',
        default=96.0,
        required=True,
        tracking=True,
        help='Total height of shelving unit'
    )
    shelf_count = fields.Integer(
        'Number of Shelves',
        default=5,
        required=True,
        tracking=True,
        help='Number of shelves in the unit'
    )
    
    # ============================================================================
    # CONTAINER TYPE & CAPACITY
    # ============================================================================
    container_type_id = fields.Many2one(
        'product.container.type',
        string='Container Type',
        help='The type of container this shelving is designed for'
    )
    positions_per_shelf = fields.Integer(
        'Positions per Shelf',
        compute='_compute_capacity',
        store=True,
        help='Number of containers that fit on each shelf'
    )
    total_capacity = fields.Integer(
        'Total Capacity',
        compute='_compute_capacity',
        store=True,
        help='Total containers this unit can hold'
    )
    
    # Manual override if needed
    manual_positions_per_shelf = fields.Integer(
        'Manual Positions/Shelf',
        help='Override auto-calculated positions'
    )
    
    # ============================================================================
    # POSITIONING
    # ============================================================================
    start_x = fields.Float(
        'Start Position X (inches)',
        default=0.0,
        help='Starting X coordinate in warehouse'
    )
    start_y = fields.Float(
        'Start Position Y (inches)',
        default=0.0,
        help='Starting Y coordinate in warehouse'
    )
    start_z = fields.Float(
        'Start Position Z (inches)',
        default=0.0,
        help='Starting Z coordinate (height from floor)'
    )
    
    # ============================================================================
    # AISLE CONFIGURATION
    # ============================================================================
    aisle_name = fields.Char(
        'Aisle Name',
        default='A',
        help='Name/letter for this aisle (e.g., A, B, C)'
    )
    rack_prefix = fields.Char(
        'Rack Prefix',
        default='R',
        help='Prefix for rack numbering (e.g., R for R01, R02...)'
    )
    
    # ============================================================================
    # DUPLICATION SETTINGS
    # ============================================================================
    duplicate_count = fields.Integer(
        'Duplicate Count',
        default=1,
        help='Number of identical units to create'
    )
    duplication_direction = fields.Selection([
        ('horizontal_x', 'Horizontal (Along X axis)'),
        ('horizontal_y', 'Horizontal (Along Y axis)'),
        ('vertical', 'Vertical (Stack upward)'),
    ], default='horizontal_y', string='Duplication Direction')
    
    spacing_between = fields.Float(
        'Spacing Between Units (inches)',
        default=36.0,
        help='Space between duplicated units'
    )
    
    # ============================================================================
    # LOCATION GENERATION
    # ============================================================================
    location_ids = fields.Many2many(
        'stock.location',
        string='Generated Locations',
        help='Stock locations created from this template',
        readonly=True
    )
    locations_generated = fields.Boolean(
        'Locations Generated',
        compute='_compute_locations_generated',
        store=True
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('shelving_width', 'container_type_id.width_inches', 'shelf_count', 'manual_positions_per_shelf')
    def _compute_capacity(self):
        for record in self:
            if record.manual_positions_per_shelf:
                record.positions_per_shelf = record.manual_positions_per_shelf
            elif record.container_type_id and record.container_type_id.width_inches:
                # Auto-calculate based on box width + spacing
                box_width = record.container_type_id.width_inches
                spacing = 2.0  # 2 inches between boxes
                available_width = record.shelving_width
                
                positions = int(available_width / (box_width + spacing))
                record.positions_per_shelf = max(1, positions)
            else:
                record.positions_per_shelf = 4  # Default
            
            record.total_capacity = record.positions_per_shelf * record.shelf_count
    
    @api.depends('location_ids')
    def _compute_locations_generated(self):
        for record in self:
            record.locations_generated = bool(record.location_ids)
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('shelving_width', 'shelving_depth', 'shelving_height', 'shelf_count')
    def _check_positive_values(self):
        for record in self:
            if record.shelving_width <= 0 or record.shelving_depth <= 0 or record.shelving_height <= 0:
                raise ValidationError(_('All dimensions must be positive numbers.'))
            if record.shelf_count <= 0:
                raise ValidationError(_('Shelf count must be at least 1.'))
    
    @api.constrains('duplicate_count')
    def _check_duplicate_count(self):
        for record in self:
            if record.duplicate_count < 1:
                raise ValidationError(_('Duplicate count must be at least 1.'))
            if record.duplicate_count > 100:
                raise ValidationError(_('Duplicate count cannot exceed 100. Create multiple templates instead.'))
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_generate_locations(self):
        """Generate stock.location hierarchy from template"""
        self.ensure_one()
        
        if not self.blueprint_id or not self.blueprint_id.warehouse_id:
            raise ValidationError(_('Blueprint and warehouse must be configured before generating locations.'))
        
        location_obj = self.env['stock.location']
        warehouse = self.blueprint_id.warehouse_id
        
        # Find or create parent location for this warehouse
        parent_location = location_obj.search([
            ('warehouse_id', '=', warehouse.id),
            ('usage', '=', 'internal'),
            ('location_id.usage', '=', 'view'),
        ], limit=1)
        
        if not parent_location:
            parent_location = warehouse.lot_stock_id
        
        created_locations = self.env['stock.location']
        
        # Generate for each duplication
        for dup_index in range(self.duplicate_count):
            # Calculate position offset based on duplication
            offset_x = 0.0
            offset_y = 0.0
            offset_z = 0.0
            
            if self.duplication_direction == 'horizontal_x':
                offset_x = dup_index * (self.shelving_width + self.spacing_between)
            elif self.duplication_direction == 'horizontal_y':
                offset_y = dup_index * (self.shelving_depth + self.spacing_between)
            else:  # vertical
                offset_z = dup_index * (self.shelving_height + self.spacing_between)
            
            # Create aisle location (if doesn't exist)
            aisle_name = f"{self.aisle_name}{dup_index + 1:02d}" if self.duplicate_count > 1 else self.aisle_name
            aisle_location = location_obj.search([
                ('name', '=', aisle_name),
                ('location_id', '=', parent_location.id),
            ], limit=1)
            
            if not aisle_location:
                aisle_location = location_obj.create({
                    'name': aisle_name,
                    'location_id': parent_location.id,
                    'usage': 'internal',
                    'is_records_location': True,
                    'aisle': aisle_name,
                    'posx': int(self.start_x + offset_x),
                    'posy': int(self.start_y + offset_y),
                    'posz': int(self.start_z + offset_z),
                })
                created_locations |= aisle_location
            
            # Create racks (vertical columns)
            rack_count = self.duplicate_count if self.duplication_direction == 'horizontal_y' else 1
            
            for rack_index in range(rack_count):
                rack_name = f"{self.rack_prefix}{rack_index + 1:02d}"
                
                # Create rack location
                rack_location = location_obj.create({
                    'name': rack_name,
                    'location_id': aisle_location.id,
                    'usage': 'internal',
                    'is_records_location': True,
                    'aisle': aisle_name,
                    'rack': rack_name,
                    'posx': int(self.start_x + offset_x + (rack_index * self.shelving_width)),
                    'posy': int(self.start_y + offset_y),
                    'posz': int(self.start_z + offset_z),
                })
                created_locations |= rack_location
                
                # Create shelves
                shelf_height = self.shelving_height / self.shelf_count
                
                for shelf_index in range(self.shelf_count):
                    shelf_name = f"S{shelf_index + 1:02d}"
                    shelf_z = int(self.start_z + offset_z + (shelf_index * shelf_height))
                    
                    # Create shelf location
                    shelf_location = location_obj.create({
                        'name': shelf_name,
                        'location_id': rack_location.id,
                        'usage': 'internal',
                        'is_records_location': True,
                        'aisle': aisle_name,
                        'rack': rack_name,
                        'shelf': shelf_name,
                        'posx': int(self.start_x + offset_x + (rack_index * self.shelving_width)),
                        'posy': int(self.start_y + offset_y),
                        'posz': shelf_z,
                        'max_capacity': self.positions_per_shelf,
                    })
                    created_locations |= shelf_location
                    
                    # Create positions on each shelf
                    position_width = self.shelving_width / self.positions_per_shelf
                    
                    for pos_index in range(self.positions_per_shelf):
                        pos_name = f"P{pos_index + 1:02d}"
                        pos_x = int(self.start_x + offset_x + (rack_index * self.shelving_width) + (pos_index * position_width))
                        
                        position_location = location_obj.create({
                            'name': pos_name,
                            'location_id': shelf_location.id,
                            'usage': 'internal',
                            'is_records_location': True,
                            'aisle': aisle_name,
                            'rack': rack_name,
                            'shelf': shelf_name,
                            'position': pos_name,
                            'posx': pos_x,
                            'posy': int(self.start_y + offset_y),
                            'posz': shelf_z,
                            'max_capacity': 1,  # One container per position
                        })
                        created_locations |= position_location
        
        # Link created locations to template
        self.location_ids = [(6, 0, created_locations.ids)]
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Locations Generated'),
                'message': _('%d locations created successfully.') % len(created_locations),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_view_locations(self):
        """View generated locations"""
        self.ensure_one()
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Locations - %s') % self.name,
            'res_model': 'stock.location',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.location_ids.ids)],
            'context': {'create': False},
        }
    
    def action_regenerate_locations(self):
        """Delete and regenerate all locations"""
        self.ensure_one()
        
        # Archive old locations instead of deleting (safer)
        if self.location_ids:
            self.location_ids.write({'active': False})
            self.location_ids = [(5, 0, 0)]
        
        # Regenerate
        return self.action_generate_locations()
