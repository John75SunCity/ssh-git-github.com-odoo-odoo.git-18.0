# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsLocation(models.Model):
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Location Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Location Code", required=True, index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # PHYSICAL LOCATION DETAILS
    # ============================================================================

    # Building Information
    building = fields.Char(string="Building", tracking=True)
    floor = fields.Char(string="Floor", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    aisle = fields.Char(string="Aisle", tracking=True)
    rack = fields.Char(string="Rack", tracking=True)
    shelf = fields.Char(string="Shelf", tracking=True)
    position = fields.Char(string="Position", tracking=True)

    # Address Information
    street = fields.Char(string="Street")
    street2 = fields.Char(string="Street 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    zip = fields.Char(string="ZIP Code")
    country_id = fields.Many2one("res.country", string="Country")

    # Computed Location Fields
    full_address = fields.Char(
        string="Full Address",
        compute="_compute_full_address",
        store=True,
    )
    location_path = fields.Char(
        string="Location Path",
        compute="_compute_location_path",
        store=True,
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )

    # ============================================================================
    # LOCATION CLASSIFICATION
    # ============================================================================

    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("vault", "Vault"),
            ("cold_storage", "Cold Storage"),
            ("archive", "Archive"),
            ("staging", "Staging Area"),
            ("shipping", "Shipping/Receiving"),
            ("destruction", "Destruction Area"),
            ("quarantine", "Quarantine"),
            ("temporary", "Temporary Storage"),
        ],
        string="Location Type",
        required=True,
        tracking=True,
    )

    # Security Classifications
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
            ("secret", "Secret"),
            ("top_secret", "Top Secret"),
        ],
        string="Access Level",
        default="restricted",
        tracking=True,
    )

    security_level = fields.Selection(
        [
            ("level_1", "Level 1 - Basic"),
            ("level_2", "Level 2 - Standard"),
            ("level_3", "Level 3 - High"),
            ("level_4", "Level 4 - Maximum"),
        ],
        string="Security Level",
        default="level_2",
        tracking=True,
    )

    # ============================================================================
    # ACCESS CONTROL
    # ============================================================================

    # Physical Access Requirements
    access_card_required = fields.Boolean(
        string="Access Card Required",
        default=True,
        tracking=True,
    )
    biometric_access = fields.Boolean(
        string="Biometric Access Required",
        default=False,
        tracking=True,
    )
    escort_required = fields.Boolean(
        string="Escort Required",
        default=False,
        tracking=True,
    )

    # Access Control Lists
    authorized_user_ids = fields.Many2many(
        "res.users",
        "location_authorized_users_rel",
        string="Authorized Users",
    )
    authorized_group_ids = fields.Many2many(
        "res.groups",
        string="Authorized Groups",
    )

    # ============================================================================
    # CAPACITY & USAGE TRACKING
    # ============================================================================

    # Capacity Management
    total_capacity = fields.Float(
        string="Total Capacity (Cubic Ft)",
        digits=(10, 2),
        tracking=True,
    )
    current_usage = fields.Float(
        string="Current Usage (Cubic Ft)",
        compute="_compute_usage_metrics",
        store=True,
        digits=(10, 2),
    )
    available_capacity = fields.Float(
        string="Available Capacity",
        compute="_compute_usage_metrics",
        store=True,
        digits=(10, 2),
    )
    usage_percentage = fields.Float(
        string="Usage Percentage",
        compute="_compute_usage_metrics",
        store=True,
        digits=(5, 2),
    )

    # Weight Tracking
    max_weight_capacity = fields.Float(
        string="Max Weight Capacity (lbs)",
        digits=(10, 2),
    )
    current_weight = fields.Float(
        string="Current Weight (lbs)",
        compute="_compute_weight_metrics",
        store=True,
        digits=(10, 2),
    )
    available_weight = fields.Float(
        string="Available Weight Capacity",
        compute="_compute_weight_metrics",
        store=True,
        digits=(10, 2),
    )

    # Item Counts
    box_count = fields.Integer(
        string="Box Count",
        compute="_compute_item_counts",
        store=True,
    )
    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_item_counts",
        store=True,
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_item_counts",
        store=True,
    )

    # ============================================================================
    # ENVIRONMENTAL CONDITIONS
    # ============================================================================

    # Climate Control
    climate_controlled = fields.Boolean(
        string="Climate Controlled",
        default=False,
        tracking=True,
    )
    temperature_min = fields.Float(
        string="Min Temperature (°F)",
        digits=(5, 2),
    )
    temperature_max = fields.Float(
        string="Max Temperature (°F)",
        digits=(5, 2),
    )
    target_temperature = fields.Float(
        string="Target Temperature (°F)",
        digits=(5, 2),
    )
    humidity_min = fields.Float(
        string="Min Humidity (%)",
        digits=(5, 2),
    )
    humidity_max = fields.Float(
        string="Max Humidity (%)",
        digits=(5, 2),
    )
    target_humidity = fields.Float(
        string="Target Humidity (%)",
        digits=(5, 2),
    )

    # Environmental Features
    fire_suppression = fields.Boolean(string="Fire Suppression System", default=False)
    flood_protection = fields.Boolean(string="Flood Protection", default=False)
    pest_control = fields.Boolean(string="Pest Control", default=False)
    earthquake_resistant = fields.Boolean(string="Earthquake Resistant", default=False)

    # ============================================================================
    # STATUS & OPERATIONAL STATE
    # ============================================================================

    # Operational Status
    status = fields.Selection(
        [
            ("available", "Available"),
            ("occupied", "Occupied"),
            ("full", "Full"),
            ("maintenance", "Under Maintenance"),
            ("restricted", "Restricted"),
            ("decommissioned", "Decommissioned"),
        ],
        string="Status",
        default="available",
        tracking=True,
    )

    # Maintenance Information
    last_inspection_date = fields.Date(string="Last Inspection")
    next_inspection_date = fields.Date(string="Next Inspection")
    maintenance_notes = fields.Text(string="Maintenance Notes")
    inspection_frequency = fields.Integer(
        string="Inspection Frequency (Days)",
        default=90,
    )

    # ============================================================================
    # OPERATIONAL FEATURES
    # ============================================================================

    # Location Features
    has_loading_dock = fields.Boolean(string="Has Loading Dock", default=False)
    has_elevator_access = fields.Boolean(string="Elevator Access", default=False)
    wheelchair_accessible = fields.Boolean(
        string="Wheelchair Accessible", default=False
    )
    has_backup_power = fields.Boolean(string="Backup Power", default=False)
    has_security_cameras = fields.Boolean(string="Security Cameras", default=False)

    # Operational Hours
    operating_hours_start = fields.Float(string="Operating Hours Start", default=8.0)
    operating_hours_end = fields.Float(string="Operating Hours End", default=17.0)
    after_hours_access = fields.Boolean(string="After Hours Access", default=False)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Parent/Child Relationships
    parent_location_id = fields.Many2one(
        "records.location",
        string="Parent Location",
        index=True,
    )
    child_location_ids = fields.One2many(
        "records.location",
        "parent_location_id",
        string="Child Locations",
    )

    # Related Records
    container_ids = fields.One2many(
        "records.container",
        "location_id",
        string="Containers",
    )
    document_ids = fields.One2many(
        "records.document",
        "location_id",
        string="Documents",
    )

    # Service References
    pickup_request_ids = fields.One2many(
        "pickup.request",
        "location_id",
        string="Pickup Requests",
    )
    work_order_ids = fields.One2many(
        "document.retrieval.work.order",
        "location_id",
        string="Document Retrieval Work Orders",
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("name", "code", "building", "floor", "zone")
    def _compute_display_name(self):
        """Compute display name for location"""
        for record in self:
            parts = [record.name]
            if record.code:
                parts.append(f"[{record.code}]")
            if record.building:
                parts.append(record.building)
            if record.floor:
                parts.append(f"Floor {record.floor}")
            record.display_name = " - ".join(parts)

    @api.depends("street", "street2", "city", "state_id", "zip", "country_id")
    def _compute_full_address(self):
        """Compute full address string"""
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
            record.full_address = ", ".join(address_parts)

    @api.depends("building", "floor", "zone", "aisle", "rack", "shelf", "position")
    def _compute_location_path(self):
        """Compute hierarchical location path"""
        for record in self:
            path_parts = []
            for field in [
                "building",
                "floor",
                "zone",
                "aisle",
                "rack",
                "shelf",
                "position",
            ]:
                value = getattr(record, field)
                if value:
                    path_parts.append(f"{field.title()}: {value}")
            record.location_path = " / ".join(path_parts)

    @api.depends("container_ids", "total_capacity")
    def _compute_usage_metrics(self):
        """Compute capacity usage metrics"""
        for record in self:
            current_usage = 0.0

            # Calculate usage from containers
            for container in record.container_ids:
                if hasattr(container, "volume") and container.volume:
                    current_usage += container.volume

            record.current_usage = current_usage

            if record.total_capacity:
                record.available_capacity = record.total_capacity - current_usage
                record.usage_percentage = (current_usage / record.total_capacity) * 100
            else:
                record.available_capacity = 0.0
                record.usage_percentage = 0.0

    @api.depends("container_ids", "max_weight_capacity")
    def _compute_weight_metrics(self):
        """Compute weight metrics"""
        for record in self:
            current_weight = 0.0

            # Calculate weight from containers
            for container in record.container_ids:
                if hasattr(container, "weight") and container.weight:
                    current_weight += container.weight

            record.current_weight = current_weight

            if record.max_weight_capacity:
                record.available_weight = record.max_weight_capacity - current_weight
            else:
                record.available_weight = 0.0

    @api.depends("container_ids", "document_ids")
    def _compute_item_counts(self):
        """Compute item counts"""
        for record in self:
            record.box_count = len(
                record.container_ids
            )  # Keep box_count name for customer-facing UI
            record.container_count = len(record.container_ids)
            record.document_count = len(record.document_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_activate(self):
        """Activate location for use"""
        self.ensure_one()
        if self.status == "decommissioned":
            raise UserError(_("Cannot activate a decommissioned location"))

        self.write(
            {
                "active": True,
                "status": "available",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Location Activated"),
                "message": _("Location has been activated successfully."),
                "type": "success",
            },
        }

    def action_set_maintenance(self):
        """Set location to maintenance mode"""
        self.ensure_one()
        self.write(
            {
                "status": "maintenance",
                "last_inspection_date": fields.Date.today(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Maintenance Mode"),
                "message": _("Location set to maintenance mode."),
                "type": "warning",
            },
        }

    def action_mark_full(self):
        """Mark location as full"""
        self.ensure_one()
        self.write({"status": "full"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Location Full"),
                "message": _("Location marked as full."),
                "type": "info",
            },
        }

    def action_view_contents(self):
        """View all contents of this location"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Location Contents"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("location_id", "=", self.id)],
            "context": {"default_location_id": self.id},
        }

    def action_location_report(self):
        """Generate location utilization report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_report",
            "report_type": "qweb-pdf",
            "data": {"location_id": self.id},
            "context": self.env.context,
        }

    def action_schedule_inspection(self):
        """Schedule next inspection"""
        self.ensure_one()
        next_date = fields.Date.today() + fields.timedelta(
            days=self.inspection_frequency
        )

        self.write({"next_inspection_date": next_date})

        # Create calendar event for inspection
        self.env["calendar.event"].create(
            {
                "name": f"Location Inspection - {self.name}",
                "start": next_date,
                "allday": True,
                "user_id": self.user_id.id,
                "description": f"Scheduled inspection for location {self.name}",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Inspection Scheduled"),
                "message": _("Next inspection scheduled for %s") % next_date,
                "type": "success",
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("total_capacity", "current_usage")
    def _check_capacity_limits(self):
        """Ensure capacity limits are respected"""
        for record in self:
            if record.total_capacity and record.current_usage > record.total_capacity:
                raise ValidationError(
                    _("Current usage cannot exceed total capacity for location %s")
                    % record.name
                )

    @api.constrains("temperature_min", "temperature_max")
    def _check_temperature_ranges(self):
        """Validate temperature ranges"""
        for record in self:
            if record.temperature_min and record.temperature_max:
                if record.temperature_min >= record.temperature_max:
                    raise ValidationError(
                        _("Minimum temperature must be less than maximum temperature")
                    )

    @api.constrains("humidity_min", "humidity_max")
    def _check_humidity_ranges(self):
        """Validate humidity ranges"""
        for record in self:
            if record.humidity_min and record.humidity_max:
                if record.humidity_min >= record.humidity_max:
                    raise ValidationError(
                        _("Minimum humidity must be less than maximum humidity")
                    )
                if record.humidity_min < 0 or record.humidity_max > 100:
                    raise ValidationError(
                        _("Humidity values must be between 0 and 100")
                    )

    @api.constrains("parent_location_id")
    def _check_parent_recursion(self):
        """Prevent recursive parent relationships"""
        if not self._check_recursion():
            raise ValidationError(_("You cannot create recursive location hierarchies"))

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================

    @api.onchange("climate_controlled")
    def _onchange_climate_controlled(self):
        """Set default temperature/humidity when climate control enabled"""
        if self.climate_controlled:
            if not self.target_temperature:
                self.target_temperature = 70.0
            if not self.target_humidity:
                self.target_humidity = 45.0
        else:
            self.target_temperature = False
            self.target_humidity = False

    @api.onchange("location_type")
    def _onchange_location_type(self):
        """Set defaults based on location type"""
        if self.location_type == "vault":
            self.security_level = "level_4"
            self.biometric_access = True
            self.fire_suppression = True
        elif self.location_type == "cold_storage":
            self.climate_controlled = True
            self.target_temperature = 32.0

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("code"):
            vals["code"] = (
                self.env["ir.sequence"].next_by_code("records.location") or "LOC"
            )

        # Set next inspection date if not provided
        if not vals.get("next_inspection_date") and vals.get("inspection_frequency"):
            vals["next_inspection_date"] = fields.Date.today() + fields.timedelta(
                days=vals["inspection_frequency"]
            )

        return super().create(vals)

    def write(self, vals):
        """Override write to track changes"""
        if "status" in vals:
            for record in self:
                old_status = dict(record._fields["status"].selection).get(record.status)
                new_status = dict(record._fields["status"].selection).get(
                    vals["status"]
                )
                record.message_post(
                    body=_("Location status changed from %s to %s")
                    % (old_status, new_status)
                )

        return super().write(vals)

    def name_get(self):
        """Custom name_get to show location hierarchy"""
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            if record.parent_location_id:
                name = f"{record.parent_location_id.name} / {name}"
            result.append((record.id, name))
        return result
