from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Warehouse3DQuickstartWizard(models.TransientModel):
    _name = 'warehouse.3d.quickstart.wizard'
    _description = '3D Warehouse Quick Setup Wizard'
    
    # ============================================================================
    # STEP 1: BASIC INFO
    # ============================================================================
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        required=True,
        help='Select the warehouse to configure'
    )
    blueprint_name = fields.Char(
        'Blueprint Name',
        default='Main Warehouse 3D',
        required=True
    )
    
    # ============================================================================
    # STEP 2: WAREHOUSE DIMENSIONS
    # ============================================================================
    length_feet = fields.Float('Length (feet)', default=100.0, required=True)
    width_feet = fields.Float('Width (feet)', default=60.0, required=True)
    height_feet = fields.Float('Height (feet)', default=12.0, required=True)
    
    # ============================================================================
    # STEP 3: LAYOUT TEMPLATE
    # ============================================================================
    use_template = fields.Selection([
        ('custom', 'Custom Design (Manual)'),
        ('simple_rows', 'Simple Layout (2 aisles, 10 racks each)'),
        ('medium_density', 'Medium Density (4 aisles, 15 racks each)'),
        ('high_density', 'High Density (6 aisles, 20 racks each)'),
    ], default='simple_rows', required=True, string='Layout Template')
    
    # ============================================================================
    # STEP 4: SHELVING CONFIGURATION
    # ============================================================================
    container_type_id = fields.Many2one(
        'product.container.type',
        string='Primary Container Type',
        help='The main type of container this warehouse will store'
    )
    
    shelving_width = fields.Float('Shelf Width (inches)', default=48.0)
    shelving_depth = fields.Float('Shelf Depth (inches)', default=24.0)
    shelving_height = fields.Float('Total Height (inches)', default=96.0)
    shelf_count = fields.Integer('Shelves per Unit', default=5)
    
    # Auto-populated based on template
    aisle_count = fields.Integer(
        'Number of Aisles',
        compute='_compute_template_defaults',
        store=True,
        readonly=False
    )
    racks_per_aisle = fields.Integer(
        'Racks per Aisle',
        compute='_compute_template_defaults',
        store=True,
        readonly=False
    )
    
    # ============================================================================
    # STEP 5: OPTIONS
    # ============================================================================
    create_sample_data = fields.Boolean(
        'Create Sample Data',
        default=False,
        help='Generate sample walls, doors, and office areas'
    )
    auto_generate_locations = fields.Boolean(
        'Auto-Generate Locations',
        default=True,
        help='Automatically create stock.location records'
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('use_template')
    def _compute_template_defaults(self):
        templates = {
            'simple_rows': {'aisles': 2, 'racks': 10},
            'medium_density': {'aisles': 4, 'racks': 15},
            'high_density': {'aisles': 6, 'racks': 20},
            'custom': {'aisles': 1, 'racks': 1},
        }
        
        for record in self:
            template = templates.get(record.use_template, templates['custom'])
            record.aisle_count = template['aisles']
            record.racks_per_aisle = template['racks']
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_generate_warehouse(self):
        """Generate the complete warehouse configuration"""
        self.ensure_one()
        
        # Check if blueprint already exists
        existing = self.env['warehouse.blueprint'].search([
            ('warehouse_id', '=', self.warehouse_id.id)
        ])
        
        if existing:
            raise ValidationError(
                _('A blueprint already exists for warehouse "%s". Please delete it first or use the existing one.')
                % self.warehouse_id.name
            )
        
        # Create blueprint
        blueprint = self.env['warehouse.blueprint'].create({
            'name': self.blueprint_name,
            'warehouse_id': self.warehouse_id.id,
            'length': self.length_feet * 12,  # Convert to inches
            'width': self.width_feet * 12,
            'height': self.height_feet * 12,
        })
        
        # Create sample warehouse structure if requested
        if self.create_sample_data:
            self._create_sample_structure(blueprint)
        
        # Create shelving templates based on layout
        if self.use_template != 'custom':
            self._create_shelving_from_template(blueprint)
        
        # Create default view configuration
        view_config = self.env['warehouse.3d.view.config'].create({
            'name': _('Default View - %s') % blueprint.name,
            'blueprint_id': blueprint.id,
            'is_default': True,
            'view_mode': 'capacity',
            'show_grid': True,
            'show_legend': True,
            'show_warehouse_structure': True,
        })
        
        # Return to blueprint form
        return {
            'type': 'ir.actions.act_window',
            'name': _('3D Warehouse Blueprint'),
            'res_model': 'warehouse.blueprint',
            'res_id': blueprint.id,
            'view_mode': 'form',
            'target': 'current',
        }
    
    def _create_sample_structure(self, blueprint):
        """Create sample walls, doors, and offices"""
        wall_obj = self.env['warehouse.wall']
        door_obj = self.env['warehouse.door']
        office_obj = self.env['warehouse.office']
        
        length = blueprint.length
        width = blueprint.width
        height = blueprint.height
        
        # Create perimeter walls
        walls = [
            {'name': 'North Wall', 'start_x': 0, 'start_y': 0, 'end_x': length, 'end_y': 0},
            {'name': 'South Wall', 'start_x': 0, 'start_y': width, 'end_x': length, 'end_y': width},
            {'name': 'East Wall', 'start_x': length, 'start_y': 0, 'end_x': length, 'end_y': width},
            {'name': 'West Wall', 'start_x': 0, 'start_y': 0, 'end_x': 0, 'end_y': width},
        ]
        
        for wall_data in walls:
            wall_obj.create({
                'blueprint_id': blueprint.id,
                'name': wall_data['name'],
                'start_x': wall_data['start_x'],
                'start_y': wall_data['start_y'],
                'end_x': wall_data['end_x'],
                'end_y': wall_data['end_y'],
                'thickness': 6.0,
                'height': height,
            })
        
        # Create main entrance door
        door_obj.create({
            'blueprint_id': blueprint.id,
            'name': 'Main Entrance',
            'pos_x': length / 2,
            'pos_y': 0,
            'width': 96.0,
            'height': 96.0,
            'door_type': 'double',
        })
        
        # Create office area in corner
        office_obj.create({
            'blueprint_id': blueprint.id,
            'name': 'Office',
            'start_x': 0,
            'start_y': 0,
            'width': 240.0,  # 20 feet
            'depth': 240.0,
            'zone_type': 'office',
        })
        
        # Create shipping/receiving area
        office_obj.create({
            'blueprint_id': blueprint.id,
            'name': 'Shipping/Receiving',
            'start_x': length - 360,  # 30 feet from end
            'start_y': 0,
            'width': 360.0,
            'depth': 240.0,
            'zone_type': 'shipping',
        })
    
    def _create_shelving_from_template(self, blueprint):
        """Create shelving templates based on selected layout"""
        template_obj = self.env['warehouse.shelving.template']
        
        # Calculate spacing
        usable_width = blueprint.width - 480  # 40 feet for aisles/walkways
        aisle_spacing = usable_width / max(self.aisle_count, 1)
        
        # Start position (after office area)
        start_x = 300.0  # 25 feet from wall
        start_y = 300.0  # 25 feet from front
        
        for aisle_index in range(self.aisle_count):
            aisle_letter = chr(65 + aisle_index)  # A, B, C, etc.
            
            template = template_obj.create({
                'name': f'Aisle {aisle_letter} - Standard Shelving',
                'blueprint_id': blueprint.id,
                'shelving_width': self.shelving_width,
                'shelving_depth': self.shelving_depth,
                'shelving_height': self.shelving_height,
                'shelf_count': self.shelf_count,
                'container_type_id': self.container_type_id.id if self.container_type_id else False,
                'start_x': start_x,
                'start_y': start_y + (aisle_index * aisle_spacing),
                'start_z': 0.0,
                'aisle_name': aisle_letter,
                'duplicate_count': self.racks_per_aisle,
                'duplication_direction': 'horizontal_x',
                'spacing_between': 72.0,  # 6 feet between racks
                'sequence': aisle_index * 10,
            })
            
            # Auto-generate locations if requested
            if self.auto_generate_locations:
                template.action_generate_locations()
        
        return True
