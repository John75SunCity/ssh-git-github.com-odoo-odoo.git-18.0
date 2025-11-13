from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsLocation(models.Model):
    """
    Represents a physical or logical storage location for records containers.

    This model manages hierarchical locations, such as buildings, floors, and shelves,
    and tracks their capacity, utilization, and compliance with security and environmental
    standards. It also provides tools for managing child locations and associated containers.

    Key Features:
    - Hierarchical structure with parent/child relationships.
    - Capacity management and utilization tracking.
    - Full address and coordinate-based identification.
    - Security and compliance features (e.g., security level, inspection dates).
    - Lifecycle management with states (Draft, Active, Maintenance, etc.).
    - Integration with records containers for storage and tracking.

    Fields:
    - Core Fields: `name`, `display_name`, `code`, `active`, `company_id`, `user_id`, `sequence`.
    - Hierarchy: `parent_location_id`, `child_location_ids`, `child_count`.
    - Address: `street`, `city`, `state_id`, `zip`, `country_id`, `full_address`.
    - Coordinates: `building`, `floor`, `zone`, `aisle`, `rack`, `shelf`, `position`, `full_coordinates`.
    - Capacity: `max_capacity`, `utilization_percentage`, `available_spaces`, `is_at_capacity`.
    - Status: `state`.
    - Security: `security_level`, `temperature_controlled`, `humidity_controlled`, `fire_suppression_system`.

    Constraints:
    - Prevents recursive location hierarchies.
    - Ensures `max_capacity` is non-negative.

    Methods:
    - Compute Methods: `_compute_display_name`, `_compute_full_address`, `_compute_full_coordinates`, etc.
    - Action Methods: `action_view_containers`, `action_view_child_locations`, `action_activate`, `action_deactivate`.
    - Overrides: `create`, `unlink`.

    Usage:
    - Use this model to define and manage storage locations for records containers.
    - Supports hierarchical organization and compliance tracking.
    """

    _name = 'records.location'
    _inherit = ['stock.location', 'mail.thread', 'mail.activity.mixin']  # Multiple inheritance
    _description = 'Records Storage Location'
    _order = 'complete_name'  # Use stock.location's hierarchical name

    # ============================================================================
    # RECORDS-SPECIFIC FIELDS (Everything else inherited from stock.location)
    # ============================================================================
    # Note: name, active, company_id, location_id (parent), child_ids inherited from stock.location

    # Records-specific location code (supplements stock.location.barcode)
    code = fields.Char(
        string="Location Code",
        copy=False,
        readonly=True,
        default=lambda self: "New",
        tracking=True,
        help="Records-specific location code (supplements Odoo barcode)"
    )

    # Responsible user for this location
    user_id = fields.Many2one(
        comodel_name='res.users',
        string="Responsible",
        default=lambda self: self.env.user,
        tracking=True
    )

    # Records Management description (separate from stock.location.comment)
    description = fields.Text(
        string="Description",
        tracking=True,
        help="Location description and special instructions for records management. "
             "Use this for access notes, handling instructions, or compliance details."
    )

    # Container relationship (records-specific)
    container_ids = fields.One2many(
        'records.container',
        'location_id',
        string="Containers"
    )
    container_count = fields.Integer(
        string="Container Count",
        compute='_compute_container_count',
        store=True
    )

    # Location grouping for records management
    group_id = fields.Many2one(
        comodel_name='location.group',
        string='Location Group'
    )

    # Note: We use stock.location's native 'usage' field instead of creating our own
    # 'location_type' to avoid duplication and leverage Odoo's standard location types
    # (internal, view, customer, vendor, inventory, production, transit)

    # Storage capacity tracking (Records Management specific)
    storage_capacity = fields.Integer(
        string='Storage Capacity',
        compute='_compute_storage_capacity',
        store=True,
        help='Maximum number of containers this location can hold'
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

    # ============================================================================
    # CAPACITY & UTILIZATION (Records-specific tracking)
    # ============================================================================
    max_capacity = fields.Integer(
        string="Maximum Capacity (Containers)",
        tracking=True,
        help="The total number of containers this location can hold"
    )
    utilization_percentage = fields.Float(
        string="Utilization (%)",
        compute='_compute_utilization_percentage',
        store=True,
        aggregator="avg"
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

    # ============================================================================
    # STATUS & LIFECYCLE (Records-specific states)
    # Note: Supplements stock.location usage field (view, internal, customer, supplier, etc.)
    # ============================================================================
    location_state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('full', 'Full'),
        ('inactive', 'Inactive'),
    ], string="Location Status", default='draft', required=True, tracking=True,
    help="Records-specific location status (supplements Odoo usage field)")

    # ============================================================================
    # SECURITY & COMPLIANCE (security_level inherited from stock_location.py extension)
    # ============================================================================
    # Note: security_level, temperature_controlled, humidity_controlled,
    # fire_suppression_system, last_inspection_date already added to stock.location
    # via stock_location.py - no need to redefine here

    next_inspection_date = fields.Date(string="Next Inspection Date", tracking=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Generate records-specific location code
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('records.location') or _('New')

            # Set default usage to 'internal' for warehouse locations
            if 'usage' not in vals:
                vals['usage'] = 'internal'

        return super().create(vals_list)

    def unlink(self):
        for loc in self:
            if loc.container_ids:
                raise UserError(_("You cannot delete a location that contains containers. Please move them first."))
            # Note: child_ids is inherited from stock.location (was child_location_ids)
            if loc.child_ids:
                raise UserError(_("You cannot delete a location that has child locations. Please remove or re-parent them first."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    # Note: display_name inherited from stock.location (uses complete_name)
    # Note: full_address removed - use stock.location.partner_id.contact_address instead

    @api.depends('building', 'floor', 'zone', 'aisle', 'rack', 'shelf', 'position')
    def _compute_full_coordinates(self):
        for record in self:
            parts = [record.building, record.floor, record.zone, record.aisle, record.rack, record.shelf, record.position]
            record.full_coordinates = ' > '.join(filter(None, parts))

    # Note: child_count removed - use len(child_ids) directly (inherited from stock.location)

    @api.depends('container_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends('max_capacity')
    def _compute_storage_capacity(self):
        """Compute storage capacity from max_capacity field"""
        for record in self:
            record.storage_capacity = record.max_capacity or 0

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

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('location_id')  # parent field in stock.location
    def _check_location_hierarchy(self):
        """Prevent recursive location hierarchies"""
        # Manual cycle check since _has_cycle may not work with inherited fields
        for record in self:
            if not record.location_id:
                continue
            visited = set()
            current = record
            while current.location_id:
                if current.location_id.id in visited:
                    raise ValidationError(_('You cannot create recursive locations.'))
                visited.add(current.id)
                current = current.location_id
                if current == record:
                    raise ValidationError(_('You cannot create recursive locations.'))

    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        for record in self:
            if record.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers'),
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id}
        }

    def action_view_child_locations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Locations'),
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': [('location_id', '=', self.id)],  # parent field in stock.location
            'context': {'default_location_id': self.id}  # parent field in stock.location
        }

    def action_activate(self):
        """Activate location for use"""
        # Update both active flag and location_state
        self.write({'active': True, 'location_state': 'active'})

    def action_deactivate(self):
        """Deactivate location"""
        # Update both active flag and location_state
        self.write({'active': False, 'location_state': 'inactive'})

    # =========================================================================
    # DEFAULT VIEW FALLBACK (Test Support)
    # =========================================================================
    def _get_default_tree_view(self):  # Odoo core still asks for 'tree' in some test helpers
        """Provide a minimal fallback list (tree) view structure for automated tests.

        Odoo 19 uses <list/> arch tag, but internal test utilities may still request
        a default 'tree' view for x2many placeholders when no explicit list view is
        preloaded. Returning a valid list arch prevents UserError during base tests.
        """
        from lxml import etree
        arch = etree.fromstring(
            "<list string='Records Locations'>"
            "<field name='display_name'/>"
            "<field name='state'/>"
            "<field name='container_count'/>"
            "<field name='utilization_percentage'/>"
            "</list>"
        )
        return arch

    # =========================================================================
    # UPGRADE SAFEGUARD: Prevent MissingError during parent_path computation
    # =========================================================================
    @api.depends('location_id')
    def _compute_warehouse_id(self):
        """
        Override stock.location._compute_warehouse_id with safe version.
        
        During module upgrade, stock.location may have broken parent_path values
        that reference deleted locations. The stock module's search with 'parent_of'
        operator tries to traverse parent_path and fails with MissingError.
        
        This override catches that error and gracefully handles it by setting
        warehouse_id to False, allowing the upgrade to complete. Odoo will
        recompute warehouse_id correctly after upgrade.
        """
        for location in self:
            try:
                # Try the parent class computation
                super(RecordsLocation, location)._compute_warehouse_id()
            except Exception:
                # If it fails (MissingError, AttributeError, etc.), set to False
                # Odoo will recompute this after the upgrade completes
                location.warehouse_id = False
