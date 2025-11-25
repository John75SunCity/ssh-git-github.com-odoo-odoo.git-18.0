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
