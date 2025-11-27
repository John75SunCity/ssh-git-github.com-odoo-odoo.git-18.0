from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class StockLocation(models.Model):
    """
    Extend stock.location to add Records Management specific features.
    
    ARCHITECTURE DECISION:
    ====================
    Instead of maintaining a separate records.location model, we extend
    Odoo's native stock.location to add records management capabilities.
    
    BENEFITS:
    - Locations visible in both Inventory and Records Management modules
    - Automatic integration with stock.quant (inventory on-hand)
    - Stock moves automatically track location changes
    - Barcode scanning works out of the box
    - Inventory reports show correct locations
    - Portal users can use same locations as internal users
    
    YOUR 100+ TEST LOCATIONS:
    - Migrate from records.location to stock.location
    - Or create corresponding stock.location for each records.location
    - Then visible in Inventory → Configuration → Locations
    
    USAGE FILTER:
    stock.location has a 'usage' field:
    - 'internal': Warehouse locations (your records storage)
    - 'customer': Customer locations (where containers come from)
    - 'transit': In-transit locations
    - 'inventory': Inventory adjustments
    - 'production': Manufacturing
    - 'view': Virtual locations (parent categories)
    
    For records management, you'll mainly use:
    - usage='internal' for your warehouse shelves/aisles
    - usage='customer' for customer site locations
    """

    _inherit = 'stock.location'

    # ============================================================================
    # RECORDS MANAGEMENT SPECIFIC FIELDS
    # ============================================================================
    is_records_location = fields.Boolean(
        string="Records Management Location",
        default=False,
        help="Identifies this as a records management storage location with "
             "enhanced security, compliance, and capacity tracking features."
    )

    # ============================================================================
    # PHYSICAL COORDINATES (for precise shelf/rack positioning)
    # ============================================================================
    building = fields.Char(string="Building")
    floor = fields.Char(string="Floor")
    zone = fields.Char(string="Zone")
    aisle = fields.Char(string="Aisle")
    rack = fields.Char(string="Rack")
    shelf = fields.Char(string="Shelf")
    position = fields.Char(string="Position")

    full_coordinates = fields.Char(
        string="Full Coordinates",
        compute='_compute_full_coordinates',
        store=True,
        help="Complete hierarchical address: Building/Floor/Zone/Aisle/Rack/Shelf/Position"
    )

    # ============================================================================
    # CAPACITY MANAGEMENT
    # ============================================================================
    max_capacity = fields.Integer(
        string="Maximum Capacity",
        default=0,
        help="Maximum number of containers this location can hold"
    )

    current_usage = fields.Integer(
        string="Current Usage",
        compute='_compute_current_usage',
        store=True,
        help="Number of containers currently stored in this location"
    )

    utilization_percentage = fields.Float(
        string="Utilization %",
        compute='_compute_utilization',
        store=True,
        help="Percentage of capacity currently utilized"
    )

    available_spaces = fields.Integer(
        string="Available Spaces",
        compute='_compute_available_spaces',
        store=True
    )

    is_at_capacity = fields.Boolean(
        string="At Capacity",
        compute='_compute_is_at_capacity',
        store=True
    )

    # ============================================================================
    # SECURITY & COMPLIANCE
    # ============================================================================
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], string='Security Level', default='internal',
       help="Security classification for this location")

    access_controlled = fields.Boolean(
        string="Access Controlled",
        default=False,
        help="Requires special access authorization"
    )

    temperature_controlled = fields.Boolean(
        string="Temperature Controlled",
        default=False,
        help="Climate-controlled environment"
    )

    humidity_controlled = fields.Boolean(
        string="Humidity Controlled",
        default=False
    )

    fire_suppression_system = fields.Boolean(
        string="Fire Suppression",
        default=False,
        help="Has automated fire suppression system"
    )

    last_inspection_date = fields.Date(
        string="Last Inspection"
    )
    
    next_inspection_date = fields.Date(
        string="Next Inspection"
    )
    
    # ============================================================================
    # LIFECYCLE STATE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Under Maintenance'),
        ('full', 'Full'),
        ('inactive', 'Inactive'),
    ], string='Status', default='draft')
    
    # ============================================================================
    # RELATIONSHIPS (leverage stock.location hierarchy)
    # ============================================================================
    # Note: stock.location already has:
    # - location_id (parent location)
    # - child_ids (child locations)
    # - company_id
    
    # One2many reverse relationship for containers stored at this location
    container_ids = fields.One2many(
        comodel_name='records.container',
        inverse_name='location_id',
        string='Containers',
        help='Containers currently stored at this location'
    )
    # - usage (internal/customer/transit/etc.)
    
    quant_ids = fields.One2many(
        'stock.quant',
        'location_id',
        string="Inventory On Hand",
        help="All inventory currently at this location"
    )
    
    # Computed field for container count (used in views)
    records_container_count = fields.Integer(
        string="Records Containers",
        compute='_compute_records_container_count',
        store=False,
        help="Number of records containers at this location"
    )
    
    # Computed field for file count (used in views)
    records_file_count = fields.Integer(
        string="File Folders",
        compute='_compute_records_file_count',
        store=False,
        help="Number of file folders at this location"
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('building', 'floor', 'zone', 'aisle', 'rack', 'shelf', 'position')
    def _compute_full_coordinates(self):
        """Build full hierarchical coordinate string"""
        for location in self:
            parts = [
                location.building,
                location.floor,
                location.zone,
                location.aisle,
                location.rack,
                location.shelf,
                location.position,
            ]
            location.full_coordinates = ' / '.join(filter(None, parts))
    
    @api.depends('container_ids')
    def _compute_records_container_count(self):
        """Count records containers at this location"""
        for location in self:
            location.records_container_count = len(location.container_ids)
    
    @api.depends('quant_ids')
    def _compute_records_file_count(self):
        """Count file folders at this location"""
        RecordsFile = self.env['records.file']
        for location in self:
            location.records_file_count = RecordsFile.search_count([
                ('location_id', '=', location.id)
            ])
    
    @api.depends('quant_ids', 'quant_ids.quantity')
    def _compute_current_usage(self):
        """Count containers currently in this location"""
        for location in self:
            # Count records containers (stock.quant with is_records_container=True)
            location.current_usage = len(location.quant_ids.filtered('is_records_container'))
    
    @api.depends('current_usage', 'max_capacity')
    def _compute_utilization(self):
        """Calculate utilization percentage"""
        for location in self:
            if location.max_capacity > 0:
                location.utilization_percentage = (location.current_usage / location.max_capacity) * 100
            else:
                location.utilization_percentage = 0.0
    
    @api.depends('max_capacity', 'current_usage')
    def _compute_available_spaces(self):
        """Calculate available capacity"""
        for location in self:
            location.available_spaces = max(0, location.max_capacity - location.current_usage)
    
    @api.depends('available_spaces')
    def _compute_is_at_capacity(self):
        """Check if location is full"""
        for location in self:
            location.is_at_capacity = location.available_spaces <= 0
    
    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def action_view_containers(self):
        """View all records.container records at this location"""
        self.ensure_one()
        return {
            'name': _('Records Containers at %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {
                'default_location_id': self.id,
                'search_default_location_id': self.id,
            },
        }
    
    def action_view_files(self):
        """View all records.file records at this location (files in containers at this location)"""
        self.ensure_one()
        return {
            'name': _('File Folders at %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.file',
            'view_mode': 'tree,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {
                'default_location_id': self.id,
                'search_default_location_id': self.id,
            },
        }
    
    def action_view_inventory(self):
        """View all inventory (stock.quant) at this location"""
        self.ensure_one()
        return {
            'name': _('Inventory at %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.quant',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id},
        }
    
    def action_activate(self):
        """Activate location for use"""
        self.write({'state': 'active'})
        self.message_post(body=_('Location activated by %s') % self.env.user.name)
    
    def action_mark_maintenance(self):
        """Mark location as under maintenance"""
        self.write({'state': 'maintenance'})
        self.message_post(body=_('Location marked for maintenance by %s') % self.env.user.name)
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        """Validate max capacity is non-negative"""
        for location in self:
            if location.max_capacity < 0:
                raise ValidationError(_('Maximum capacity cannot be negative'))
    
    @api.constrains('location_id')
    def _check_location_recursion(self):
        """Prevent circular parent relationships"""
        if self._has_cycle():
            raise ValidationError(_('Error! You cannot create recursive locations.'))
