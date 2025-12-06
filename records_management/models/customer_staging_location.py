# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class CustomerStagingLocation(models.Model):
    """
    Customer Virtual Locations - Hierarchical staging areas for containers awaiting pickup.
    
    Allows customers to organize their containers by physical location before pickup:
    - Company/Department (auto-prefix from partner)
    - Building/Floor
    - Room Number
    
    Example: "City of EP/Records Department/Basement/Room B-006"
    
    Technicians use these locations to know exactly where to find containers during pickup.
    
    STOCK INTEGRATION:
    Each customer staging location auto-creates a corresponding stock.location
    with usage='customer'. This enables:
    - Proper stock moves to/from customer locations
    - Stock Barcode app compatibility
    - Inventory tracking at customer sites
    """
    _name = 'customer.staging.location'
    _description = 'Customer Staging Location (Virtual)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'complete_name asc'
    _parent_name = "parent_id"
    _parent_store = True
    _rec_name = 'complete_name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(
        string="Location Name",
        required=True,
        tracking=True,
        help="Short name for this location level. Examples:\n"
             "- 'Basement' (building level)\n"
             "- 'Room B-006' (room level)\n"
             "- 'Records Department' (department level)"
    )

    complete_name = fields.Char(
        string="Full Location Path",
        compute='_compute_complete_name',
        recursive=True,
        store=True,
        help="Complete hierarchical path. Auto-generated from parent chain.\n"
             "Example: 'City of EP/Records Department/Basement/Room B-006'"
    )

    active = fields.Boolean(
        default=True,
        help="Inactive locations are hidden but not deleted"
    )

    # ============================================================================
    # HIERARCHY
    # ============================================================================
    parent_id = fields.Many2one(
        comodel_name='customer.staging.location',
        string='Parent Location',
        index=True,
        ondelete='cascade',
        domain="[('partner_id', '=', partner_id)]",
        help="Parent location in hierarchy. Leave empty for top-level locations."
    )

    parent_path = fields.Char(
        index=True,
        help="Technical field for hierarchical queries"
    )

    child_ids = fields.One2many(
        comodel_name='customer.staging.location',
        inverse_name='parent_id',
        string='Child Locations'
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True,
        tracking=True,
        domain="[('is_records_customer', '=', True)]",
        default=lambda self: self.env.user.partner_id if self.env.user.partner_id.is_records_customer else False,
        help="The customer company this location belongs to"
    )

    department_id = fields.Many2one(
        comodel_name='records.department',
        string='Department',
        tracking=True,
        domain="[('partner_id', '=', partner_id)]",
        help="Department within customer organization"
    )

    container_ids = fields.One2many(
        comodel_name='records.container',
        inverse_name='customer_staging_location_id',
        string='Containers at This Location',
        help="Containers currently assigned to this staging location"
    )

    # ============================================================================
    # STOCK INTEGRATION
    # ============================================================================
    stock_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Stock Location',
        readonly=True,
        ondelete='restrict',
        help="Auto-created stock.location for inventory tracking. "
             "Usage type is 'customer' for proper stock moves."
    )

    # ============================================================================
    # COUNTS & STATISTICS
    # ============================================================================
    container_count = fields.Integer(
        string='Container Count',
        compute='_compute_container_count',
        help="Number of containers at this location (including child locations)"
    )

    pending_pickup_count = fields.Integer(
        string='Pending Pickup',
        compute='_compute_pending_pickup_count',
        help="Containers awaiting pickup at this location"
    )

    # ============================================================================
    # BARCODE - For location labels customers can print
    # ============================================================================
    barcode = fields.Char(
        string="Location Barcode",
        copy=False,
        index=True,
        help="Unique barcode for this staging location. "
             "Customers can print labels with this barcode to identify their pickup locations."
    )

    # ============================================================================
    # LOCATION DETAILS
    # ============================================================================
    location_type = fields.Selection(
        selection=[
            ('building', 'Building'),
            ('floor', 'Floor'),
            ('room', 'Room'),
            ('area', 'Area'),
            ('other', 'Other')
        ],
        string='Location Type',
        default='other',
        help="Type of location for better organization"
    )

    notes = fields.Text(
        string='Access Notes',
        help="Special instructions for technicians:\n"
             "- Access codes\n"
             "- Parking instructions\n"
             "- Contact person\n"
             "- Special handling notes"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'parent_id.complete_name', 'partner_id.name')
    def _compute_complete_name(self):
        """Build full hierarchical path with customer prefix"""
        for location in self:
            if location.parent_id:
                location.complete_name = '%s/%s' % (location.parent_id.complete_name, location.name)
            elif location.partner_id:
                # Top-level: include customer name
                location.complete_name = '%s/%s' % (location.partner_id.name, location.name)
            else:
                location.complete_name = location.name or ''

    @api.depends('container_ids')
    def _compute_container_count(self):
        """Count containers at this location and all child locations"""
        for location in self:
            # Get all child location IDs recursively
            child_locations = self.search([
                ('id', 'child_of', location.id)
            ])
            location.container_count = self.env['records.container'].search_count([
                ('customer_staging_location_id', 'in', child_locations.ids)
            ])

    @api.depends('container_ids.state')
    def _compute_pending_pickup_count(self):
        """Count containers pending pickup"""
        for location in self:
            child_locations = self.search([
                ('id', 'child_of', location.id)
            ])
            location.pending_pickup_count = self.env['records.container'].search_count([
                ('customer_staging_location_id', 'in', child_locations.ids),
                ('state', '=', 'draft')  # Containers not yet picked up
            ])

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        """Prevent circular parent relationships"""
        if self._has_cycle():
            raise ValidationError(_('You cannot create recursive location hierarchies.'))

    @api.constrains('partner_id', 'parent_id')
    def _check_partner_consistency(self):
        """Ensure parent and child belong to same customer"""
        for location in self:
            if location.parent_id and location.parent_id.partner_id != location.partner_id:
                raise ValidationError(_(
                    'Parent location must belong to the same customer.\n'
                    'Parent: %s\nThis location: %s'
                ) % (location.parent_id.partner_id.name, location.partner_id.name))

    # ============================================================================
    # CRUD METHODS - STOCK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create customer staging locations with corresponding stock.location."""
        locations = super().create(vals_list)
        for location in locations:
            location._create_or_update_stock_location()
        return locations

    def write(self, vals):
        """Update stock.location when name or parent changes."""
        result = super().write(vals)
        if 'name' in vals or 'parent_id' in vals or 'partner_id' in vals:
            for location in self:
                location._create_or_update_stock_location()
        return result

    def _create_or_update_stock_location(self):
        """
        Create or update the corresponding stock.location.
        
        Stock location hierarchy mirrors customer staging location hierarchy.
        All customer locations use usage='customer' for proper stock handling.
        """
        self.ensure_one()
        
        # Get parent stock location
        parent_stock_location = False
        if self.parent_id and self.parent_id.stock_location_id:
            parent_stock_location = self.parent_id.stock_location_id
        else:
            # Top level - use partner's property_stock_customer if set, otherwise Partner Locations
            parent_stock_location = self.env.ref('stock.stock_location_customers', raise_if_not_found=False)
        
        if not parent_stock_location:
            return  # Stock module may not be fully installed
        
        location_vals = {
            'name': self.complete_name or self.name,
            'usage': 'customer',
            'location_id': parent_stock_location.id,
            'company_id': self.env.company.id,
        }
        
        if self.stock_location_id:
            # Update existing (use sudo to bypass stock.location permissions)
            self.stock_location_id.sudo().write(location_vals)
        else:
            # Create new (use sudo - portal users can create staging locations
            # but don't have direct stock.location create permissions)
            stock_location = self.env['stock.location'].sudo().create(location_vals)
            self.sudo().stock_location_id = stock_location.id

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_view_containers(self):
        """View containers at this location"""
        self.ensure_one()
        child_locations = self.search([('id', 'child_of', self.id)])

        return {
            'name': _('Containers at %s') % self.complete_name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'list,form',
            'domain': [('customer_staging_location_id', 'in', child_locations.ids)],
            'context': {'default_customer_staging_location_id': self.id}
        }

    def action_generate_barcode(self):
        """Generate a unique barcode for this staging location."""
        self.ensure_one()
        if not self.barcode:
            # Use sequence or generate based on ID
            sequence = self.env['ir.sequence'].sudo().search([
                ('code', '=', 'customer.staging.location.barcode')
            ], limit=1)
            if sequence:
                self.barcode = sequence.next_by_id()
            else:
                # Fallback: generate from partner code + location type + ID
                partner_code = (self.partner_id.ref or 'CUST')[:4].upper()
                loc_type = (self.location_type or 'LOC')[:3].upper()
                self.barcode = 'SL-%s-%s-%06d' % (partner_code, loc_type, self.id)
        return True

    def action_print_barcode(self):
        """Print barcode label for this staging location."""
        self.ensure_one()
        # Generate barcode if not exists
        if not self.barcode:
            self.action_generate_barcode()
        
        # Return report action for printing
        return self.env.ref('records_management.action_report_staging_location_barcode').report_action(self)

    def name_get(self):
        """Display complete path"""
        return [(location.id, location.complete_name) for location in self]
