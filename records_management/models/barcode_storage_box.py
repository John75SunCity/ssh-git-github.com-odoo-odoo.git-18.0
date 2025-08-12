# -*- coding: utf-8 -*-
"""
Barcode Storage Container Module

This module manages barcode storage containers (referred to as "boxes" in UI)
for the Records Management System. Handles container capacity, tracking,
and integration with barcode products.

Important Terminology:
- Code: "container" (precise technical term)
- UI: "box" (user-friendly term)
- Business: Both terms are interchangeable in user-facing contexts

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class BarcodeStorageBox(models.Model):
    _name = "barcode.storage.box"
    _description = "Barcode Storage Container (Box)"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Container Name",
        required=True,
        tracking=True,
        index=True,
        help="Container name (displayed as 'Box Name' to users)"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True
    )
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("full", "Full"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True
    )

    # ============================================================================
    # BARCODE MANAGEMENT
    # ============================================================================
    barcode = fields.Char(string="Box Barcode", required=True, index=True)
    barcode_product_ids = fields.One2many(
        "barcode.product", "storage_box_id", string="Barcode Products"
    )

    # ============================================================================
    # PHYSICAL SPECIFICATIONS
    # ============================================================================
    location_id = fields.Many2one("records.location", string="Storage Location")
    box_type = fields.Selection(
        [
            ("standard", "Standard Box"),
            ("large", "Large Box"),
            ("small", "Small Box"),
            ("custom", "Custom Size"),
        ],
        string="Box Type",
        default="standard",
    )

    capacity = fields.Integer(string="Storage Capacity", default=100)
    current_count = fields.Integer(
        string="Current Count", compute="_compute_current_count", store=True
    )
    available_space = fields.Integer(
        string="Available Space", compute="_compute_available_space", store=True
    )

    # ============================================================================
    # PHYSICAL DIMENSIONS
    # ============================================================================
    length = fields.Float(string="Length (cm)", default=30.0)
    width = fields.Float(string="Width (cm)", default=20.0)
    height = fields.Float(string="Height (cm)", default=15.0)
    weight_empty = fields.Float(string="Empty Weight (kg)", default=0.5)
    weight_current = fields.Float(
        string="Current Weight (kg)", compute="_compute_current_weight", store=True
    )
    volume_cubic_cm = fields.Float(
        string="Volume (cm³)",
        compute="_compute_volume",
        store=True,
        help="Calculated volume in cubic centimeters"
    )

    # ============================================================================
    # STATUS & TRACKING
    # ============================================================================
    is_full = fields.Boolean(string="Is Full", compute="_compute_is_full", store=True)
    last_accessed = fields.Datetime(string="Last Accessed")
    created_date = fields.Date(string="Created Date", default=fields.Date.today)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer")
    department_id = fields.Many2one("records.department", string="Department")

    # Container type integration with Records Management specifications
    container_type = fields.Selection([
        ('type_01', 'TYPE 01: Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02: Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03: Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04: Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06: Pathology Box (0.042 CF)'),
    ], string="Container Type", help="Records Management container classification")

    # ============================================================================
    # NOTES & DOCUMENTATION
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("barcode_product_ids")
    def _compute_current_count(self):
        for box in self:
            box.current_count = len(box.barcode_product_ids)

    @api.depends("capacity", "current_count")
    def _compute_available_space(self):
        for box in self:
            box.available_space = max(0, box.capacity - box.current_count)

    @api.depends("current_count", "capacity")
    def _compute_is_full(self):
        for box in self:
            box.is_full = box.current_count >= box.capacity

    @api.depends("barcode_product_ids", "barcode_product_ids.weight", "weight_empty")
    def _compute_current_weight(self):
        for box in self:
            product_weight = sum(box.barcode_product_ids.mapped("weight") or [0.0])
            box.weight_current = box.weight_empty + product_weight

    @api.depends("length", "width", "height")
    def _compute_volume(self):
        for box in self:
            box.volume_cubic_cm = box.length * box.width * box.height

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_type')
    def _onchange_container_type(self):
        """Update specifications based on container type"""
        if self.container_type:
            specs = self._get_container_specifications()
            spec = specs.get(self.container_type, {})
            if spec:
                # Update capacity based on container type
                self.capacity = spec.get('capacity', 100)
                # Update dimensions if available
                if 'length' in spec:
                    self.length = spec['length']
                if 'width' in spec:
                    self.width = spec['width']
                if 'height' in spec:
                    self.height = spec['height']

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_full(self):
        """Mark storage container as full"""
        self.ensure_one()

        if self.state != "active":
            raise UserError(_("Only active containers can be marked as full"))

        self.write({"state": "full"})
        self.message_post(body=_("Container marked as full"))

    def action_archive_box(self):
        """Archive storage container"""
        self.ensure_one()

        if self.state == "archived":
            raise UserError(_("Container is already archived"))

        self.write({
            "state": "archived",
            "active": False
        })
        self.message_post(body=_("Container archived"))

    def action_activate(self):
        """Activate storage container"""
        self.ensure_one()

        if self.state != "draft":
            raise UserError(_("Only draft containers can be activated"))

        self._validate_container_setup()
        self.write({"state": "active"})
        self.message_post(body=_("Container activated and ready for use"))

    def action_add_barcode_product(self):
        """Open wizard to add barcode product to this container"""
        self.ensure_one()

        if self.state not in ["active", "draft"]:
            raise UserError(_("Cannot add products to %s containers", self.state))

        if self.is_full:
            raise UserError(_("Container is at full capacity"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Add Barcode Product"),
            "res_model": "barcode.product",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_storage_box_id": self.id,
                "default_container_name": self.name,
            },
        }

    def action_view_products(self):
        """View all barcode products in this container"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Products in Container: %s", self.name),
            "res_model": "barcode.product",
            "view_mode": "tree,form",
            "domain": [("storage_box_id", "=", self.id)],
            "context": {"default_storage_box_id": self.id},
        }

    def action_update_capacity_status(self):
        """Check and update container capacity status"""
        self.ensure_one()

        # Refresh computed fields
        self._compute_current_count()
        self._compute_available_space()
        self._compute_is_full()

        if self.is_full and self.state == "active":
            self.action_mark_full()

        message = _("Capacity check completed. Current: %s/%s items",
                   self.current_count, self.capacity)
        self.message_post(body=message)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Capacity Status Updated'),
                'message': message,
                'type': 'success',
            }
        }

    def action_generate_barcode_label(self):
        """Generate printable barcode label for container"""
        self.ensure_one()

        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.container_barcode_label',
            'report_type': 'qweb-pdf',
            'data': {'ids': [self.id]},
            'context': self.env.context,
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _validate_container_setup(self):
        """Validate container setup before activation"""
        if not self.barcode:
            raise ValidationError(_("Container barcode is required"))

        if not self.location_id:
            raise ValidationError(_("Storage location is required"))

        if self.capacity <= 0:
            raise ValidationError(_("Storage capacity must be greater than zero"))

        # Check for duplicate barcodes
        duplicate = self.search([
            ("barcode", "=", self.barcode),
            ("id", "!=", self.id),
            ("active", "=", True)
        ])
        if duplicate:
            raise ValidationError(_("Container barcode %s already exists", self.barcode))

    def get_capacity_percentage(self):
        """Get capacity utilization as percentage"""
        self.ensure_one()

        if self.capacity == 0:
            return 0.0

        return (self.current_count / self.capacity) * 100

    def can_add_products(self, quantity=1):
        """Check if container can accommodate additional products"""
        self.ensure_one()

        if self.state not in ["active", "draft"]:
            return False

        return (self.current_count + quantity) <= self.capacity

    def _get_container_specifications(self):
        """Get container specifications based on business requirements"""
        return {
            'type_01': {
                'capacity': 150,
                'length': 30.5,
                'width': 38.1,
                'height': 25.4,
                'description': 'Standard Box (1.2 CF)'
            },
            'type_02': {
                'capacity': 150,
                'length': 60.9,
                'width': 38.1,
                'height': 25.4,
                'description': 'Legal/Banker Box (2.4 CF)'
            },
            'type_03': {
                'capacity': 50,
                'length': 106.7,
                'width': 15.2,
                'height': 15.2,
                'description': 'Map Box (0.875 CF)'
            },
            'type_04': {
                'capacity': 500,
                'description': 'Odd Size/Temp Box (5.0 CF)'
            },
            'type_06': {
                'capacity': 25,
                'length': 30.5,
                'width': 15.2,
                'height': 25.4,
                'description': 'Pathology Box (0.042 CF)'
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("capacity")
    def _check_capacity(self):
        """Validate storage capacity"""
        for container in self:
            if container.capacity <= 0:
                raise ValidationError(_("Storage capacity must be greater than zero"))

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate physical dimensions"""
        for container in self:
            if container.length <= 0 or container.width <= 0 or container.height <= 0:
                raise ValidationError(_("Container dimensions must be positive values"))

    @api.constrains("barcode")
    def _check_barcode_unique(self):
        """Validate barcode uniqueness"""
        for container in self:
            if container.barcode:
                # Check for duplicates
                duplicate = self.search([
                    ("barcode", "=", container.barcode),
                    ("id", "!=", container.id),
                    ("active", "=", True)
                ])
                if duplicate:
                    raise ValidationError(_("Container barcode %s already exists", container.barcode))

    @api.constrains("current_count", "capacity")
    def _check_capacity_limits(self):
        """Validate capacity limits are not exceeded"""
        for container in self:
            if container.current_count > container.capacity:
                raise ValidationError(_(
                    "Current count (%s) cannot exceed container capacity (%s)",
                    container.current_count,
                    container.capacity
                ))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with capacity information"""
        result = []
        for container in self:
            name = container.name
            if container.barcode:
                name = _("[%s] %s", container.barcode, name)
            
            # Add capacity information
            capacity_info = _("(%s/%s)", container.current_count, container.capacity)
            name = _("%s %s", name, capacity_info)
            
            result.append((container.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default barcode if needed"""
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("barcode.storage.box")
            
            # Auto-generate barcode if not provided
            if not vals.get("barcode"):
                vals["barcode"] = self.env["ir.sequence"].next_by_code("barcode.storage.box.barcode")
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle state changes"""
        result = super().write(vals)
        
        # Update last_accessed when certain fields change
        if any(field in vals for field in ['current_count', 'state']):
            self.write({'last_accessed': fields.Datetime.now()})
        
        return result

    @api.model
    def get_containers_near_capacity(self, threshold_percentage=90):
        """Get containers that are near capacity"""
        containers = self.search([
            ('state', '=', 'active'),
            ('capacity', '>', 0)
        ])
        
        near_capacity = []
        for container in containers:
            if container.get_capacity_percentage() >= threshold_percentage:
                near_capacity.append(container)
        
        return near_capacity

    @api.model
    def get_dashboard_data(self):
        """Get dashboard statistics for containers"""
        total_containers = self.search_count([('active', '=', True)])
        active_containers = self.search_count([('state', '=', 'active')])
        full_containers = self.search_count([('state', '=', 'full')])
        
        return {
            'total_containers': total_containers,
            'active_containers': active_containers,
            'full_containers': full_containers,
            'utilization_rate': (full_containers / total_containers * 100) if total_containers else 0,
        }