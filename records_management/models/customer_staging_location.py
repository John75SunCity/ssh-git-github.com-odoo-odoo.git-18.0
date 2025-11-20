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
            'view_mode': 'tree,form',
            'domain': [('customer_staging_location_id', 'in', child_locations.ids)],
            'context': {'default_customer_staging_location_id': self.id}
        }

    def name_get(self):
        """Display complete path"""
        return [(location.id, location.complete_name) for location in self]
