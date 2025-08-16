# -*- coding: utf-8 -*-
import uuid

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsLocation(models.Model):
    """Records Storage Location Management
    
    Comprehensive location management system with capacity tracking,
    security controls, and operational status monitoring for Records Management operations.
    """
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Location Name",
        required=True,
        tracking=True,
        index=True
    )
    
    code = fields.Char(
        string="Location Code",
        required=True,
        index=True,
        tracking=True
    )
    
    description = fields.Text(
        string="Description"
    )
    
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        tracking=True
    )
    
    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True
    )
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    
    user_id = fields.Many2one(
        "res.users",
        string="Location Manager",
        default=lambda self: self.env.user,
        tracking=True
    )
    
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    # ============================================================================
    # PHYSICAL LOCATION DETAILS
    # ============================================================================
    building = fields.Char(
        string="Building",
        tracking=True
    )
    
    floor = fields.Char(
        string="Floor",
        tracking=True
    )
    
    zone = fields.Char(
        string="Zone",
        tracking=True
    )
    
    aisle = fields.Char(
        string="Aisle",
        tracking=True
    )
    
    rack = fields.Char(
        string="Rack",
        tracking=True
    )
    
    shelf = fields.Char(
        string="Shelf",
        tracking=True
    )
    
    position = fields.Char(
        string="Position",
        tracking=True
    )

    # Address Information
    street = fields.Char(
        string="Street"
    )
    
    street2 = fields.Char(
        string="Street 2"
    )
    
    city = fields.Char(
        string="City"
    )
    
    state_id = fields.Many2one(
        "res.country.state",
        string="State/Province"
    )
    
    zip = fields.Char(
        string="ZIP Code"
    )
    
    country_id = fields.Many2one(
        "res.country",
        string="Country"
    )
    
    full_address = fields.Text(
        string="Full Address",
        compute="_compute_full_address",
        store=True,
        help="Complete formatted address"
    )

    # ============================================================================
    # CAPACITY & SPECIFICATIONS
    # ============================================================================
    location_type = fields.Selection([
        ("warehouse", "Warehouse"),
        ("office", "Office"),
        ("vault", "Vault"),
        ("archive", "Archive"),
        ("temporary", "Temporary"),
        ("offsite", "Off-site"),
    ], string="Location Type",
       required=True,
       default="warehouse",
       tracking=True)
    
    storage_capacity = fields.Integer(
        string="Storage Capacity (boxes)",
        default=1000
    )
    
    max_capacity = fields.Integer(
        string="Maximum Capacity",
        default=1000
    )
    
    current_utilization = fields.Integer(
        string="Current Utilization",
        compute="_compute_current_utilization"
    )
    
    available_spaces = fields.Integer(
        string="Available Spaces",
        compute="_compute_available_spaces"
    )
    
    available_space = fields.Integer(
        string="Available Space",
        compute="_compute_available_space"
    )
    
    utilization_percentage = fields.Float(
        string="Utilization %",
        compute="_compute_utilization_percentage",
        digits=(5, 2)
    )
    
    box_count = fields.Integer(
        string="Box Count",
        compute="_compute_box_count",
        help="Number of boxes at this location"
    )

    # Physical constraints
    max_weight_capacity = fields.Float(
        string="Max Weight Capacity (lbs)",
        digits=(12, 2)
    )
    
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled",
        default=False
    )
    
    humidity_controlled = fields.Boolean(
        string="Humidity Controlled",
        default=False
    )
    
    fire_suppression = fields.Boolean(
        string="Fire Suppression",
        default=False
    )
    
    security_level = fields.Selection([
        ("standard", "Standard"),
        ("high", "High"),
        ("maximum", "Maximum")
    ], string="Security Level",
       default="standard",
       tracking=True)

    # ============================================================================
    # ACCESS & SECURITY
    # ============================================================================
    access_restrictions = fields.Text(
        string="Access Restrictions"
    )
    
    authorized_user_ids = fields.Many2many(
        "res.users",
        string="Authorized Users"
    )
    
    requires_escort = fields.Boolean(
        string="Requires Escort",
        default=False
    )
    
    security_camera = fields.Boolean(
        string="Security Camera",
        default=False
    )
    
    access_card_required = fields.Boolean(
        string="Access Card Required",
        default=False
    )

    # ============================================================================
    # OPERATIONAL STATUS
    # ============================================================================
    operational_status = fields.Selection([
        ("active", "Active"),
        ("maintenance", "Under Maintenance"),
        ("inactive", "Inactive"),
        ("full", "At Capacity"),
    ], string="Operational Status",
       default="active",
       tracking=True)
    
    availability_schedule = fields.Text(
        string="Availability Schedule"
    )
    
    last_inspection_date = fields.Date(
        string="Last Inspection Date"
    )
    
    next_inspection_date = fields.Date(
        string="Next Inspection Date"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    container_ids = fields.One2many(
        "records.container",
        "location_id",
        string="Records Containers"
    )
    
    box_ids = fields.One2many(
        "records.container",
        "location_id",
        string="Stored Boxes"
    )
    
    parent_location_id = fields.Many2one(
        "records.location",
        string="Parent Location"
    )
    
    child_location_ids = fields.One2many(
        "records.location",
        "parent_location_id",
        string="Child Locations"
    )

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status',
       default='draft',
       tracking=True,
       required=True,
       index=True,
       help='Current status of the record')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    child_count = fields.Integer(
        compute="_compute_child_count",
        string="Child Count"
    )
    
    is_available = fields.Boolean(
        compute="_compute_is_available",
        string="Available for Storage"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[("res_model", "=", "records.location")]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers"
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[("model", "=", "records.location")]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("street", "street2", "city", "state_id", "zip", "country_id")
    def _compute_full_address(self):
        """Compute full formatted address"""
        for record in self:
            address_parts = []
            if record.street:
                address_parts.append(record.street)
            if record.street2:
                address_parts.append(record.street2)
            if record.city:
                address_parts.append(record.city)
            if record.state_id:
                address_parts.append(record.state_id.name)
            if record.zip:
                address_parts.append(record.zip)
            if record.country_id:
                address_parts.append(record.country_id.name)
            record.full_address = ", ".join(address_parts) if address_parts else ""

    @api.depends("container_ids")
    def _compute_current_utilization(self):
        """Compute current utilization based on container count"""
        for record in self:
            record.current_utilization = len(record.container_ids)

    @api.depends("box_ids")
    def _compute_box_count(self):
        """Compute the number of boxes at this location"""
        for record in self:
            record.box_count = len(record.box_ids)

    @api.depends("max_capacity", "box_count")
    def _compute_available_space(self):
        """Compute available space based on maximum capacity and current box count"""
        for record in self:
            record.available_space = max(0, record.max_capacity - record.box_count)

    @api.depends("storage_capacity", "current_utilization")
    def _compute_available_spaces(self):
        """Compute available spaces based on storage capacity and utilization"""
        for record in self:
            if record.storage_capacity > 0:
                record.available_spaces = max(
                    0, record.storage_capacity - record.current_utilization
                )
            else:
                record.available_spaces = 0

    @api.depends("current_utilization", "storage_capacity")
    def _compute_utilization_percentage(self):
        """Compute utilization percentage"""
        for record in self:
            if record.storage_capacity > 0:
                record.utilization_percentage = (
                    record.current_utilization / record.storage_capacity * 100.0
                )
            else:
                record.utilization_percentage = 0.0

    @api.depends("child_location_ids")
    def _compute_child_count(self):
        """Compute count of child locations"""
        for record in self:
            record.child_count = len(record.child_location_ids)

    @api.depends("operational_status", "storage_capacity", "current_utilization")
    def _compute_is_available(self):
        """Compute if location is available for new storage"""
        for record in self:
            record.is_available = (
                record.operational_status == "active"
                and record.current_utilization < record.storage_capacity
            )

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create locations with auto-generated codes if needed"""
        if not vals_list:
            return self.env[self._name]
            
        for vals in vals_list:
            if not vals.get("code"):
                seq_code = self.env["ir.sequence"].next_by_code("records.location")
                if seq_code:
                    vals["code"] = seq_code
                else:
                    vals["code"] = "LOC/%s" % uuid.uuid4().hex[:8]
        
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        """View containers at this location"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Records Containers"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("location_id", "=", self.id)],
            "context": {"default_location_id": self.id},
        }

    def action_location_report(self):
        """Generate location utilization and capacity report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_utilization_report",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }

    def action_maintenance_mode(self):
        """Set location to maintenance mode"""
        self.ensure_one()
        self.write({"operational_status": "maintenance"})
        self.message_post(
            body=_("Location %s set to maintenance mode", self.name),
            message_type="notification",
        )

    def action_activate_location(self):
        """Activate location"""
        for record in self:
            record.write({
                "state": "active",
                "operational_status": "active"
            })
            record.message_post(body=_("Location activated"))

    def action_deactivate_location(self):
        """Deactivate location"""
        for record in self:
            if record.current_utilization > 0:
                raise UserError(_("Cannot deactivate location with stored containers"))
            
            record.write({
                "state": "inactive",
                "operational_status": "inactive"
            })
            record.message_post(body=_("Location deactivated"))

    def action_reserve_space(self):
        """Open form to reserve space at this location"""
        self.ensure_one()
        if not self.is_available:
            raise UserError(_("Location is not available for reservations"))
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Reserve Space"),
            "res_model": "records.location.reservation",
            "view_mode": "form",
            "target": "new",
            "context": {"default_location_id": self.id},
        }

    def action_schedule_inspection(self):
        """Schedule location inspection"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Inspection"),
            "res_model": "records.location.inspection",
            "view_mode": "form",
            "target": "new",
            "context": {"default_location_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_full_location_path(self):
        """Return full hierarchical path of location"""
        self.ensure_one()
        path = [self.name]
        current = self.parent_location_id
        while current:
            path.insert(0, current.name)
            current = current.parent_location_id
        return " > ".join(path)

    def get_available_capacity(self):
        """Return available storage capacity"""
        self.ensure_one()
        return max(0, self.storage_capacity - self.current_utilization)

    def get_location_coordinates(self):
        """Get detailed location coordinates"""
        self.ensure_one()
        coordinates = []
        
        if self.building:
            coordinates.append(_("Building: %s", self.building))
        if self.floor:
            coordinates.append(_("Floor: %s", self.floor))
        if self.zone:
            coordinates.append(_("Zone: %s", self.zone))
        if self.aisle:
            coordinates.append(_("Aisle: %s", self.aisle))
        if self.rack:
            coordinates.append(_("Rack: %s", self.rack))
        if self.shelf:
            coordinates.append(_("Shelf: %s", self.shelf))
        if self.position:
            coordinates.append(_("Position: %s", self.position))
        
        return ", ".join(coordinates)

    def get_security_info(self):
        """Get comprehensive security information"""
        self.ensure_one()
        security_features = []
        
        security_features.append(_("Security Level: %s", dict(self._fields['security_level'].selection)[self.security_level]))
        
        if self.security_camera:
            security_features.append(_("Security Camera: Yes"))
        if self.access_card_required:
            security_features.append(_("Access Card Required: Yes"))
        if self.requires_escort:
            security_features.append(_("Escort Required: Yes"))
        if self.fire_suppression:
            security_features.append(_("Fire Suppression: Yes"))
        if self.temperature_controlled:
            security_features.append(_("Temperature Controlled: Yes"))
        if self.humidity_controlled:
            security_features.append(_("Humidity Controlled: Yes"))
        
        return security_features

    def check_capacity_availability(self, required_spaces):
        """Check if location has sufficient capacity for required spaces"""
        self.ensure_one()
        available = self.get_available_capacity()
        return available >= required_spaces

    @api.model
    def find_available_locations(self, required_capacity=1, location_type=None, security_level=None):
        """Find locations with available capacity matching criteria"""
        domain = [
            ('is_available', '=', True),
            ('available_spaces', '>=', required_capacity),
            ('operational_status', '=', 'active')
        ]
        
        if location_type:
            domain.append(('location_type', '=', location_type))
        
        if security_level:
            domain.append(('security_level', '=', security_level))
        
        return self.search(domain, order='utilization_percentage asc')

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("storage_capacity", "max_capacity")
    def _check_storage_capacity(self):
        """Validate storage capacity constraints"""
        for record in self:
            if record.storage_capacity < 0:
                raise ValidationError(_("Storage capacity cannot be negative"))
            if record.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative"))
            if record.storage_capacity > record.max_capacity:
                raise ValidationError(_("Storage capacity cannot exceed maximum capacity"))

    @api.constrains("parent_location_id")
    def _check_parent_location(self):
        """Validate parent location hierarchy"""
        for record in self:
            if record.parent_location_id:
                if record.parent_location_id == record:
                    raise ValidationError(_("A location cannot be its own parent"))
                
                # Check for circular reference
                current = record.parent_location_id
                visited = {record.id}
                while current:
                    if current.id in visited:
                        raise ValidationError(
                            _("Circular reference detected in location hierarchy")
                        )
                    visited.add(current.id)
                    current = current.parent_location_id

    @api.constrains("code")
    def _check_code_uniqueness(self):
        """Ensure location code uniqueness"""
        for record in self:
            if record.code:
                existing = self.search([
                    ("code", "=", record.code),
                    ("id", "!=", record.id)
                ], limit=1)
                if existing:
                    raise ValidationError(_("Location code must be unique"))

    @api.constrains("max_weight_capacity")
    def _check_weight_capacity(self):
        """Validate weight capacity constraints"""
        for record in self:
            if record.max_weight_capacity and record.max_weight_capacity < 0:
                raise ValidationError(_("Maximum weight capacity cannot be negative"))

    @api.constrains("utilization_percentage")
    def _check_utilization_percentage(self):
        """Validate utilization percentage is within bounds"""
        for record in self:
            if record.utilization_percentage < 0 or record.utilization_percentage > 100:
                raise ValidationError(_("Utilization percentage must be between 0 and 100"))

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def update_operational_status(self):
        """Update operational status based on utilization"""
        for record in self:
            if record.utilization_percentage >= 100:
                record.operational_status = 'full'
            elif record.utilization_percentage >= 95:
                # Near capacity warning
                record.message_post(
                    body=_("Location %s is near capacity (%s%%)", 
                          record.name, record.utilization_percentage),
                    message_type="notification"
                )

    def schedule_maintenance(self, maintenance_date, description=None):
        """Schedule maintenance for this location"""
        self.ensure_one()
        
        if self.current_utilization > 0:
            # Create notification for containers that need relocation
            self.message_post(
                body=_("Maintenance scheduled for %s. %s containers need relocation.", 
                      maintenance_date, self.current_utilization),
                message_type="notification"
            )
        
        self.write({
            'operational_status': 'maintenance',
            'next_inspection_date': maintenance_date
        })
        
        if description:
            self.message_post(body=_("Maintenance scheduled: %s", description))

    def get_capacity_forecast(self, days_ahead=30):
        """Forecast capacity utilization for planning purposes"""
        self.ensure_one()
        
        # Simple capacity forecasting based on recent trends
        # This could be enhanced with more sophisticated algorithms
        current_utilization = self.current_utilization
        capacity = self.storage_capacity
        
        if capacity == 0:
            return {'error': _('No storage capacity defined')}
        
        # Calculate trend based on recent container additions
        recent_additions = self.env['records.container'].search_count([
            ('location_id', '=', self.id),
            ('create_date', '>=', fields.Datetime.now() - 
             fields.Datetime.timedelta(days=30))
        ])
        
        daily_growth_rate = recent_additions / 30 if recent_additions else 0
        projected_utilization = current_utilization + (daily_growth_rate * days_ahead)
        projected_percentage = (projected_utilization / capacity) * 100
        
        return {
            'current_utilization': current_utilization,
            'projected_utilization': min(projected_utilization, capacity),
            'projected_percentage': min(projected_percentage, 100),
            'days_to_capacity': (capacity - current_utilization) / daily_growth_rate if daily_growth_rate > 0 else None,
            'recommendation': self._get_capacity_recommendation(projected_percentage)
        }

    def _get_capacity_recommendation(self, projected_percentage):
        """Get recommendation based on projected capacity"""
        if projected_percentage >= 95:
            return _('URGENT: Location will reach capacity soon. Consider expansion or relocation.')
        elif projected_percentage >= 80:
            return _('WARNING: Location utilization will be high. Monitor closely.')
        elif projected_percentage >= 60:
            return _('NORMAL: Utilization is within acceptable range.')
        else:
            return _('GOOD: Location has ample available capacity.')
    @api.depends('box_count', 'max_capacity')
    def _compute_utilization(self):
        """Calculate current utilization percentage"""
        for record in self:
            if record.max_capacity and record.max_capacity > 0:
                record.current_utilization = (record.box_count / record.max_capacity) * 100
            else:
                record.current_utilization = 0.0
