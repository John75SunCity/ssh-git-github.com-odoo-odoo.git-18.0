# -*- coding: utf-8 -*-
"""
Barcode Storage Box Management Module

Manages physical storage containers (boxes) that hold barcode products.
This model tracks capacity, dimensions, location, and integrates with
the Records Management system's business rules for container types.

Author: Records Management System
Version: 19.0.0.1
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BarcodeStorageBox(models.Model):
    """
    Barcode Storage Container (Box)

    Represents a physical box used to store items, each identified by a
    barcode. It tracks physical attributes, capacity, and contents.
    """
    _name = 'barcode.storage.box'
    _description = 'Barcode Storage Container (Box)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Box Name',
        required=True,
        copy=False,
        index=True,
        default=lambda self: _('New')
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('full', 'Full'),
        ('in_transit', 'In Transit'),
        ('archived', 'Archived')
    ], string='Status', default='draft', required=True, tracking=True)
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        tracking=True,
        help="The customer who owns the contents of this box."
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        help="The specific department associated with this box, for access control."
    )

    # ============================================================================
    # BARCODE & LOCATION
    # ============================================================================
    barcode = fields.Char(
        string='Box Barcode',
        required=True,
        copy=False,
        help="Unique barcode identifying this storage box."
    )
    location_id = fields.Many2one(
        'records.location',
        string='Current Location',
        tracking=True,
        help="The physical location where the box is stored."
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS (Based on Business Rules)
    # ============================================================================
    container_type = fields.Selection([
        ('type_01', 'Standard Box (1.2 CF)'),
        ('type_02', 'Legal/Banker Box (2.4 CF)'),
        ('type_03', 'Map Box (0.875 CF)'),
        ('type_04', 'Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'Pathology Box (0.042 CF)')
    ], string='Container Type', required=True, default='type_01', tracking=True)

    length = fields.Float(string='Length (in)', help="Length in inches")
    width = fields.Float(string='Width (in)', help="Width in inches")
    height = fields.Float(string='Height (in)', help="Height in inches")
    volume_cf = fields.Float(
        string='Volume (Cubic Feet)',
        digits=(12, 3),
        help="Calculated volume based on the container type."
    )
    weight_empty = fields.Float(string='Empty Weight (lbs)')
    weight_current = fields.Float(
        string='Current Weight (lbs)',
        compute='_compute_current_weight',
        store=True,
        help="Total weight including contents."
    )

    # ============================================================================
    # CAPACITY & CONTENTS
    # ============================================================================
    barcode_product_ids = fields.One2many(
        'barcode.product',
        'container_id', # Assuming barcode.product has a 'container_id' field
        string='Box Contents'
    )
    capacity = fields.Integer(
        string='Storage Capacity',
        default=100,
        help="Maximum number of items this box can hold."
    )
    current_count = fields.Integer(
        string='Item Count',
        compute='_compute_capacity_status',
        store=True
    )
    available_space = fields.Integer(
        string='Available Space',
        compute='_compute_capacity_status',
        store=True
    )
    is_full = fields.Boolean(
        string='Is Full',
        compute='_compute_capacity_status',
        store=True
    )

    # ============================================================================
    # TRACKING & DOCUMENTATION
    # ============================================================================
    last_accessed = fields.Datetime(string='Last Accessed', readonly=True)
    created_date = fields.Date(
        string='Created Date',
        default=fields.Date.today,
        readonly=True
    )
    description = fields.Text(string='Description')
    notes = fields.Text(string='Internal Notes')

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'barcode')
    def _compute_display_name(self):
        """Create a descriptive display name."""
        for record in self:
            if record.name and record.barcode:
                record.display_name = f"{record.name} [{record.barcode}]"
            else:
                record.display_name = record.name or record.barcode or _('New Box')

    @api.depends('barcode_product_ids', 'capacity')
    def _compute_capacity_status(self):
        """Compute item count, available space, and full status."""
        for box in self:
            item_count = len(box.barcode_product_ids)
            box.current_count = item_count
            box.available_space = max(0, box.capacity - item_count)
            box.is_full = item_count >= box.capacity
            if box.is_full and box.state == 'active':
                box.state = 'full'

    @api.depends('weight_empty', 'barcode_product_ids.weight_lbs')
    def _compute_current_weight(self):
        """Compute the current total weight of the box."""
        for box in self:
            product_weight = sum(box.barcode_product_ids.mapped("weight_lbs"))
            box.weight_current = box.weight_empty + product_weight

    @api.onchange('container_type')
    def _onchange_container_type(self):
        """Update specifications based on the selected container type."""
        specs = self._get_container_specifications().get(self.container_type)
        if specs:
            self.volume_cf = specs.get('volume', 0.0)
            self.weight_empty = specs.get('weight', 0.0) / 2 # Assuming empty weight is half of average
            dims = specs.get('dims', '0x0x0').replace('"', '').split('x')
            if len(dims) == 3:
                self.length = float(dims[0].strip())
                self.width = float(dims[1].strip())
                self.height = float(dims[2].strip())

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_archive_box(self):
        """Archive the storage container and its contents."""
        self.ensure_one()
        self.barcode_product_ids.action_archive()
        self.write({'active': False, 'state': 'archived'})
        self.message_post(body=_("Box and its contents have been archived."))

    def action_activate(self):
        """Activate the storage container."""
        self.ensure_one()
        self.write({'active': True, 'state': 'active'})
        self.message_post(body=_("Box has been activated."))

    def action_view_products(self):
        """Return an action to view all barcode products in this container."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Contents of %s', self.name),
            'res_model': 'barcode.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.barcode_product_ids.ids)],
            'context': {'default_container_id': self.id}
        }

    # ============================================================================
    # BUSINESS LOGIC & VALIDATION
    # ============================================================================
    @api.model
    def _get_container_specifications(self):
        """Central method for container specifications based on business rules."""
        return {
            'type_01': {'volume': 1.2, 'weight': 35, 'dims': '12" x 15" x 10"'},
            'type_02': {'volume': 2.4, 'weight': 65, 'dims': '24" x 15" x 10"'},
            'type_03': {'volume': 0.875, 'weight': 35, 'dims': '42" x 6" x 6"'},
            'type_04': {'volume': 5.0, 'weight': 75, 'dims': 'Variable'},
            'type_06': {'volume': 0.042, 'weight': 40, 'dims': '12" x 6" x 10"'},
        }

    @api.constrains('barcode')
    def _check_barcode_uniqueness(self):
        """Ensure barcode is unique."""
        for record in self:
            if self.search_count([('barcode', '=', record.barcode), ('id', '!=', record.id)]) > 0:
                raise ValidationError(_("A box with barcode '%s' already exists.", record.barcode))

    @api.constrains('capacity')
    def _check_capacity(self):
        """Validate that capacity is a positive number."""
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_("Storage capacity cannot be negative."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name and barcode from a sequence."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('barcode.storage.box') or _('New')
            if not vals.get('barcode'):
                vals['barcode'] = self.env['ir.sequence'].next_by_code('barcode.storage.box.barcode') or vals['name']
        return super().create(vals_list)

    def write(self, vals):
        """Override write to update last_accessed timestamp."""
        if 'barcode_product_ids' in vals or 'location_id' in vals:
            vals['last_accessed'] = fields.Datetime.now()
        return super().write(vals)
