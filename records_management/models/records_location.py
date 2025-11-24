from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class StockLocationRecordsExtension(models.Model):
    """
    Extends stock.location with Records Management fields.
    
    This adds records-specific functionality to Odoo's standard stock locations
    without creating a separate location model. All inventory locations are now
    automatically available in Records Management.
    
    Usage:
    1. In Inventory → Configuration → Locations: Check "Is Records Location"
    2. Those locations will appear in Records Management → Storage Locations
    3. No data duplication - one unified location system
    """
    
    _inherit = 'stock.location'
    
    # Flag to identify records management locations
    is_records_location = fields.Boolean(
        string="Is Records Location",
        default=False,
        help="Check this box to use this location in Records Management"
    )
    
    # Records Management description (separate from stock comment)
    records_description = fields.Text(
        string="Records Management Notes",
        help="Special instructions for records handling, access, or compliance"
    )
    
    # Location group (for grouping locations)
    group_id = fields.Many2one(
        'location.group',
        string="Location Group",
        help="Group this location belongs to for organizational purposes"
    )
    
    # Detailed warehouse coordinates (supplements stock.location.name)
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
        help="Formatted warehouse coordinates (Building > Floor > Zone > Aisle > Rack > Shelf > Position)"
    )
    
    # Capacity & Utilization
    max_capacity = fields.Integer(
        string="Maximum Capacity (Containers)",
        help="The total number of containers this location can hold"
    )
    utilization_percentage = fields.Float(
        string="Utilization (%)",
        compute='_compute_utilization_percentage',
        store=True
    )
    available_spaces = fields.Integer(
        string="Available Spaces",
        compute='_compute_available_spaces',
        store=True
    )
    is_at_capacity = fields.Boolean(
        string="Is At Capacity",
        compute='_compute_is_at_capacity',
        store=True
    )
    
    # Status & Lifecycle
    location_state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('full', 'Full'),
        ('inactive', 'Inactive'),
    ], string="Location Status", default='draft', required=True,
       help="Records-specific location status (supplements Odoo usage field)")
    
    # Inspection tracking
    next_inspection_date = fields.Date(string="Next Inspection Date")
    
    # Container relationship
    container_ids = fields.One2many(
        'records.container',
        'location_id',
        string="Containers",
        domain=[('state', '!=', 'destroyed')]
    )
    
    container_count = fields.Integer(
        string="Container Count",
        compute='_compute_container_count',
        store=True
    )
    
    # Compute methods
    @api.depends('building', 'floor', 'zone', 'aisle', 'rack', 'shelf', 'position')
    def _compute_full_coordinates(self):
        for record in self:
            parts = [record.building, record.floor, record.zone, record.aisle, 
                    record.rack, record.shelf, record.position]
            record.full_coordinates = ' > '.join(filter(None, parts))
    
    @api.depends('container_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.container_ids)
    
    @api.depends('container_count', 'max_capacity')
    def _compute_utilization_percentage(self):
        for record in self:
            if record.max_capacity > 0:
                record.utilization_percentage = (record.container_count / record.max_capacity) * 100.0
            else:
                record.utilization_percentage = 0.0
    
    @api.depends('container_count', 'max_capacity')
    def _compute_available_spaces(self):
        for record in self:
            record.available_spaces = max(0, record.max_capacity - record.container_count)
    
    @api.depends('available_spaces')
    def _compute_is_at_capacity(self):
        for record in self:
            record.is_at_capacity = record.available_spaces <= 0
    
    # Constraints
    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        for record in self:
            if record.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative."))
    
    # Action methods
    def action_view_containers(self):
        """View containers at this location"""
        self.ensure_one()
        return {
            'name': _('Containers at %s') % self.display_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'list,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id}
        }
    
    def action_activate(self):
        """Activate location for use"""
        self.write({'active': True, 'location_state': 'active'})
    
    def action_deactivate(self):
        """Deactivate location"""
        self.write({'active': False, 'location_state': 'inactive'})
