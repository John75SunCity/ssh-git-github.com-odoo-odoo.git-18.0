# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsLocation(models.Model):
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Location Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Location Code", required=True, index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)

    # Location Hierarchy
    building = fields.Char(string="Building", tracking=True)
    floor = fields.Char(string="Floor", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    aisle = fields.Char(string="Aisle", tracking=True)
    rack = fields.Char(string="Rack", tracking=True)
    shelf = fields.Char(string="Shelf", tracking=True)
    position = fields.Char(string="Position", tracking=True)

    # Location Classification
    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("storage_facility", "Storage Facility"),
            ("vault", "Security Vault"),
            ("climate_storage", "Climate Controlled Storage"),
            ("archive", "Archive"),
            ("offsite", "Offsite Storage"),
            ("mobile", "Mobile Storage"),
        ],
        string="Location Type",
        required=True,
        tracking=True,
    )

    # Security and Access Control
    access_level = fields.Selection(
        [
            ("public", "Public Access"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
            ("top_secret", "Top Secret"),
            ("biometric", "Biometric Access"),
        ],
        string="Access Level",
        default="restricted",
        required=True,
        tracking=True,
    )
    security_level = fields.Selection(
        [
            ("basic", "Basic Security"),
            ("enhanced", "Enhanced Security"),
            ("maximum", "Maximum Security"),
            ("high_security", "High Security Vault"),
        ],
        string="Security Level",
        default="basic",
        required=True,
        tracking=True,
    )
    access_card_required = fields.Boolean(
        string="Access Card Required",
        default=True,
        tracking=True,
    )
    biometric_access = fields.Boolean(
        string="Biometric Access",
        default=False,
        tracking=True,
    )
    escort_required = fields.Boolean(
        string="Escort Required",
        default=False,
        tracking=True,
    )

    # Physical Specifications
    total_capacity = fields.Float(
        string="Total Capacity (cubic feet)",
        required=True,
        tracking=True,
        help="Total storage capacity in cubic feet",
    )
    current_usage = fields.Float(
        string="Current Usage (cubic feet)",
        compute="_compute_usage_metrics",
        store=True,
        help="Currently used storage space",
    )
    available_capacity = fields.Float(
        string="Available Capacity (cubic feet)",
        compute="_compute_usage_metrics",
        store=True,
        help="Available storage space",
    )
    utilization_percentage = fields.Float(
        string="Utilization %",
        compute="_compute_usage_metrics",
        store=True,
        digits=(5, 2),
        help="Percentage of capacity currently used",
    )
    max_weight_capacity = fields.Float(
        string="Max Weight Capacity (lbs)",
        tracking=True,
        help="Maximum weight capacity in pounds",
    )
    max_capacity = fields.Char(
        string="Max Capacity", help="Maximum storage capacity description"
    )
    current_weight = fields.Float(
        string="Current Weight (lbs)",
        compute="_compute_weight_metrics",
        store=True,
        help="Current total weight of stored items",
    )

    # Environmental Controls
    climate_controlled = fields.Boolean(
        string="Climate Controlled",
        default=False,
        tracking=True,
    )
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled",
        default=False,
        tracking=True,
    )
    humidity_controlled = fields.Boolean(
        string="Humidity Controlled",
        default=False,
        tracking=True,
    )
    target_temperature = fields.Float(
        string="Target Temperature (°F)",
        default=70.0,
        tracking=True,
    )
    target_humidity = fields.Float(
        string="Target Humidity (%)",
        default=45.0,
        tracking=True,
    )
    climate_monitoring_enabled = fields.Boolean(
        string="Climate Monitoring Enabled",
        default=False,
        tracking=True,
    )

    # Safety and Protection
    fire_suppression_system = fields.Selection(
        [
            ("none", "None"),
            ("sprinkler", "Sprinkler System"),
            ("gas", "Gas Suppression"),
            ("foam", "Foam System"),
            ("dry_chemical", "Dry Chemical"),
        ],
        string="Fire Suppression System",
        default="sprinkler",
        tracking=True,
    )
    fireproof_rating = fields.Selection(
        [
            ("none", "Not Fireproof"),
            ("30min", "30 Minutes"),
            ("1hour", "1 Hour"),
            ("2hour", "2 Hours"),
            ("4hour", "4 Hours"),
        ],
        string="Fireproof Rating",
        default="none",
        tracking=True,
    )
    flood_protection = fields.Boolean(
        string="Flood Protection",
        default=False,
        tracking=True,
    )
    earthquake_resistant = fields.Boolean(
        string="Earthquake Resistant",
        default=False,
        tracking=True,
    )

    # Status and State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("maintenance", "Under Maintenance"),
            ("full", "Full Capacity"),
            ("restricted", "Access Restricted"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True)

    # Company and User Management
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    responsible_user_id = fields.Many2one(
        "res.users",
        string="Location Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )
    backup_manager_id = fields.Many2one(
        "res.users",
        string="Backup Manager",
        tracking=True,
    )

    # Warehouse Integration
    warehouse_id = fields.Many2one(
        "stock.warehouse",
        string="Warehouse",
        tracking=True,
    )

    # Related Records and Counts
    container_ids = fields.One2many(
        "records.container", "location_id", string="Containers"
    )
    document_ids = fields.One2many(
        "records.document", "location_id", string="Documents"
    )

    # Computed Counts
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

    # Location Services and Features
    pickup_service_available = fields.Boolean(
        string="Pickup Service Available",
        default=True,
        tracking=True,
    )
    delivery_service_available = fields.Boolean(
        string="Delivery Service Available",
        default=True,
        tracking=True,
    )
    scanning_services = fields.Boolean(
        string="On-site Scanning Services",
        default=False,
        tracking=True,
    )
    shredding_services = fields.Boolean(
        string="On-site Shredding Services",
        default=False,
        tracking=True,
    )

    # Operational Information
    operating_hours = fields.Text(
        string="Operating Hours", help="Location operating hours and availability"
    )
    access_instructions = fields.Text(
        string="Access Instructions", help="Instructions for accessing this location"
    )
    emergency_procedures = fields.Text(
        string="Emergency Access Procedures",
        help="Emergency access and evacuation procedures",
    )
    special_handling_notes = fields.Text(
        string="Special Handling Notes", help="Special handling requirements or notes"
    )

    # Compliance and Certification
    location_certification = fields.Char(
        string="Location Certification",
        tracking=True,
        help="Certification or compliance standards met",
    )
    last_inspection_date = fields.Date(
        string="Last Inspection Date",
        tracking=True,
    )
    next_inspection_date = fields.Date(
        string="Next Inspection Date",
        tracking=True,
    )
    naid_certified = fields.Boolean(
        string="NAID Certified",
        default=False,
        tracking=True,
    )
    iso_certified = fields.Boolean(
        string="ISO Certified",
        default=False,
        tracking=True,
    )

    # Financial Information
    monthly_cost = fields.Monetary(
        string="Monthly Cost",
        currency_field="currency_id",
        tracking=True,
        help="Monthly cost for this location",
    )
    cost_per_cubic_foot = fields.Monetary(
        string="Cost per Cubic Foot",
        currency_field="currency_id",
        tracking=True,
        help="Monthly cost per cubic foot of storage",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Timestamps
    created_date = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
    )
    updated_date = fields.Datetime(
        string="Last Updated",
        readonly=True,
    )
    commissioned_date = fields.Date(
        string="Commissioned Date",
        tracking=True,
        help="Date when location was put into service",
    )

    # GPS and Physical Address
    street = fields.Char(string="Street Address")
    street2 = fields.Char(string="Street Address 2")
    city = fields.Char(string="City")
    state_id = fields.Many2one("res.country.state", string="State")
    zip_code = fields.Char(string="ZIP Code")
    country_id = fields.Many2one("res.country", string="Country")
    latitude = fields.Float(string="Latitude", digits=(10, 7))
    longitude = fields.Float(string="Longitude", digits=(10, 7))

    # === MISSING FIELDS FOR RECORDS.LOCATION ===

    # Framework Integration Fields (required by mail.thread)
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("res_model", "=", self._name)],
    )

    # Space Management Fields
    available_spaces = fields.Integer(
        string="Available Spaces",
        compute="_compute_space_metrics",
        store=True,
        help="Number of available storage spaces",
    )

    available_utilization = fields.Float(
        string="Available Utilization (%)",
        compute="_compute_space_metrics",
        store=True,
        digits=(5, 2),
        help="Percentage of available space utilization",
    )

    box_count = fields.Integer(
        string="Box Count",
        compute="_compute_container_metrics",
        store=True,
        help="Total number of boxes stored in this location",
    )

    capacity = fields.Float(
        string="Storage Capacity", help="Maximum storage capacity of the location"
    )

    current_utilization = fields.Float(
        string="Current Utilization (%)",
        compute="_compute_utilization_metrics",
        store=True,
        digits=(5, 2),
        help="Current space utilization percentage",
    )

    # Additional Location Management
    location_manager = fields.Many2one(
        "res.users",
        string="Location Manager",
        help="Person responsible for managing this location",
    )

    last_inspection_date = fields.Date(
        string="Last Inspection Date",
        tracking=True,
        help="Date of last location inspection",
    )

    next_inspection_date = fields.Date(
        string="Next Inspection Date",
        compute="_compute_next_inspection_date",
        store=True,
        help="Computed next inspection date",
    )

    # Display and Computed Fields
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )
    full_address = fields.Char(
        string="Full Address",
        compute="_compute_full_address",
        store=True,
    )
    location_path = fields.Char(
        string="Location Path",
        compute="_compute_location_path",
        store=True,
        help="Full hierarchical path of the location",
    )

    # Enhanced State Management and Compute Methods

    @api.depends("name", "code", "building", "zone")
    def _compute_display_name(self):
        """Compute display name with location details."""
        for record in self:
            parts = [record.name]
            if record.code:
                parts.append(f"[{record.code}]")
            if record.building:
                parts.append(f"- {record.building}")
            if record.zone:
                parts.append(f"Zone {record.zone}")
            record.display_name = " ".join(parts)

    @api.depends("street", "street2", "city", "state_id", "zip_code", "country_id")
    def _compute_full_address(self):
        """Compute full address."""
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
            if record.zip_code:
                address_parts.append(record.zip_code)
            if record.country_id:
                address_parts.append(record.country_id.name)
            record.full_address = ", ".join(address_parts)

    @api.depends("building", "floor", "zone", "aisle", "rack", "shelf", "position")
    def _compute_location_path(self):
        """Compute hierarchical location path."""
        for record in self:
            path_parts = []
            if record.building:
                path_parts.append(f"Building: {record.building}")
            if record.floor:
                path_parts.append(f"Floor: {record.floor}")
            if record.zone:
                path_parts.append(f"Zone: {record.zone}")
            if record.aisle:
                path_parts.append(f"Aisle: {record.aisle}")
            if record.rack:
                path_parts.append(f"Rack: {record.rack}")
            if record.shelf:
                path_parts.append(f"Shelf: {record.shelf}")
            if record.position:
                path_parts.append(f"Position: {record.position}")
            record.location_path = " > ".join(path_parts)

    @api.depends("container_ids", "document_ids", "total_capacity")
    def _compute_usage_metrics(self):
        """Compute usage and capacity metrics."""
        for record in self:
            # Calculate current usage from containers and documents
            total_used = 0.0

            # Add container volumes (primary inventory tracking)
            for container in record.container_ids:
                if hasattr(container, "volume") and container.volume:
                    total_used += container.volume
                else:
                    # Standard container estimate: 1 cubic foot
                    total_used += 1.0

            # Add document volumes (estimated)
            for document in record.document_ids:
                if hasattr(document, "volume") and document.volume:
                    total_used += document.volume
                else:
                    # Estimate 0.1 cubic feet per document if no volume specified
                    total_used += 0.1

            record.current_usage = total_used
            record.available_capacity = max(0, record.total_capacity - total_used)

            if record.total_capacity > 0:
                record.utilization_percentage = (
                    total_used / record.total_capacity
                ) * 100
            else:
                record.utilization_percentage = 0.0

    @api.depends("container_ids", "document_ids")
    def _compute_weight_metrics(self):
        """Compute weight metrics."""
        for record in self:
            total_weight = 0.0

            # Add container weights (primary tracking)
            for container in record.container_ids:
                if hasattr(container, "weight") and container.weight:
                    total_weight += container.weight
                else:
                    # Standard container estimate: 30 lbs
                    total_weight += 30.0

            # Add document weights (estimated)
            for document in record.document_ids:
                if hasattr(document, "weight") and document.weight:
                    total_weight += document.weight
                else:
                    # Estimate 0.1 lbs per document
                    total_weight += 0.1

            record.current_weight = total_weight

    @api.depends("container_ids", "document_ids")
    def _compute_item_counts(self):
        """Compute counts of stored items."""
        for record in self:
            record.container_count = len(record.container_ids)
            record.document_count = len(record.document_ids)

    def write(self, vals):
        """Override write to update modification date."""
        vals["updated_date"] = fields.Datetime.now()
        return super().write(vals)

    @api.constrains("total_capacity")
    def _check_total_capacity(self):
        """Validate total capacity is positive."""
        for record in self:
            if record.total_capacity <= 0:
                raise ValidationError(_("Total capacity must be greater than zero."))

    @api.constrains("target_temperature")
    def _check_target_temperature(self):
        """Validate temperature range."""
        for record in self:
            if record.temperature_controlled and (
                record.target_temperature < 32 or record.target_temperature > 100
            ):
                raise ValidationError(
                    _("Target temperature must be between 32°F and 100°F.")
                )

    @api.constrains("target_humidity")
    def _check_target_humidity(self):
        """Validate humidity range."""
        for record in self:
            if record.humidity_controlled and (
                record.target_humidity < 0 or record.target_humidity > 100
            ):
                raise ValidationError(_("Target humidity must be between 0% and 100%."))

    @api.onchange("climate_controlled")
    def _onchange_climate_controlled(self):
        """Update related fields when climate control is enabled."""
        if self.climate_controlled:
            self.temperature_controlled = True
            self.humidity_controlled = True
            self.climate_monitoring_enabled = True
        else:
            self.temperature_controlled = False
            self.humidity_controlled = False
            self.climate_monitoring_enabled = False

    @api.onchange("access_level")
    def _onchange_access_level(self):
        """Update security settings based on access level."""
        if self.access_level in ["confidential", "top_secret", "biometric"]:
            self.security_level = "maximum"
            self.access_card_required = True
            self.escort_required = True
            if self.access_level == "biometric":
                self.biometric_access = True

    @api.onchange("location_type")
    def _onchange_location_type(self):
        """Set default values based on location type."""
        if self.location_type == "vault":
            self.access_level = "confidential"
            self.security_level = "maximum"
            self.fireproof_rating = "2hour"
            self.fire_suppression_system = "gas"
        elif self.location_type == "climate_storage":
            self.climate_controlled = True
            self.temperature_controlled = True
            self.humidity_controlled = True
        elif self.location_type == "archive":
            self.climate_controlled = True
            self.fireproof_rating = "1hour"

    # Action Methods

    def action_activate(self):
        """Activate the location."""
        self.ensure_one()
        self.write({"state": "active"})

        self.message_post(
            body=_("Location activated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Location Activated"),
                "message": _("Location %s is now active and available for storage.")
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_set_maintenance(self):
        """Set location to maintenance mode."""
        self.ensure_one()
        self.write({"state": "maintenance"})

        # Create maintenance activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Location maintenance: %s") % self.name,
            note=_("Location is under maintenance. Access may be restricted."),
            user_id=self.responsible_user_id.id or self.env.user.id,
        )

        self.message_post(
            body=_("Location set to maintenance mode: %s") % self.name,
            message_type="notification",
        )

    def action_set_restricted(self):
        """Restrict access to location."""
        self.ensure_one()
        self.write({"state": "restricted"})

        self.message_post(
            body=_("Location access restricted: %s") % self.name,
            message_type="notification",
        )

    def action_mark_full(self):
        """Mark location as full capacity."""
        self.ensure_one()

        if self.utilization_percentage < 95:
            raise UserError(
                _("Location is not at full capacity (%.1f%% utilized).")
                % self.utilization_percentage
            )

        self.write({"state": "full"})

        self.message_post(
            body=_("Location marked as full capacity: %s") % self.name,
            message_type="notification",
        )

    def action_view_containers(self):
        """View all containers in this location."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Containers in Location: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("location_id", "=", self.id)],
            "context": {
                "default_location_id": self.id,
                "search_default_location_id": self.id,
                "search_default_group_by_status": True,
            },
        }

    def action_view_documents(self):
        """View all documents stored in this location."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Documents in Location: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("location_id", "=", self.id)],
            "context": {
                "default_location_id": self.id,
                "search_default_location_id": self.id,
                "search_default_group_by_state": True,
            },
        }

    def action_view_boxes(self):
        """View all containers stored in this location (customer box_number view)."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Boxes in Location: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("location_id", "=", self.id)],
            "context": {
                "default_location_id": self.id,
                "search_default_location_id": self.id,
                "search_default_group_by_status": True,
                "show_customer_view": True,  # Flag to show box_number prominently
            },
        }

    def action_location_report(self):
        """Generate comprehensive location report."""
        self.ensure_one()

        # Create report generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Location report generated: %s") % self.name,
            note=_(
                "Comprehensive location utilization and inventory report has been generated."
            ),
            user_id=self.responsible_user_id.id or self.env.user.id,
        )

        self.message_post(
            body=_("Location report generated for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_comprehensive_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_schedule_inspection(self):
        """Schedule location inspection."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Inspection"),
            "res_model": "location.inspection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_location_id": self.id,
                "default_inspection_date": fields.Date.today()
                + fields.timedelta(days=30),
                "default_inspector_id": self.responsible_user_id.id,
            },
        }

    def action_climate_monitoring(self):
        """Access climate monitoring dashboard."""
        self.ensure_one()

        if not self.climate_monitoring_enabled:
            raise UserError(_("Climate monitoring is not enabled for this location."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Climate Monitoring: %s") % self.name,
            "res_model": "climate.monitoring.log",
            "view_mode": "graph,tree,form",
            "target": "current",
            "domain": [("location_id", "=", self.id)],
            "context": {
                "search_default_location_id": self.id,
                "search_default_last_30_days": True,
                "search_default_group_by_date": True,
            },
        }

    def action_emergency_access(self):
        """Initiate emergency access procedures."""
        self.ensure_one()

        # Create emergency access activity
        self.activity_schedule(
            "mail.mail_activity_data_urgent",
            summary=_("Emergency access initiated: %s") % self.name,
            note=_("Emergency access procedures have been initiated for location: %s")
            % self.name,
            user_id=self.responsible_user_id.id or self.env.user.id,
        )

        self.message_post(
            body=_("Emergency access initiated for location: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Emergency Access"),
                "message": _("Emergency access procedures initiated for %s.")
                % self.name,
                "type": "warning",
                "sticky": True,
            },
        }

    def action_optimize_layout(self):
        """Optimize location layout and storage."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Optimize Layout"),
            "res_model": "location.optimization.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_location_id": self.id,
                "default_current_utilization": self.utilization_percentage,
                "default_container_count": self.container_count,
            },
        }

    def action_bulk_move_items(self):
        """Bulk move items from this location."""
        self.ensure_one()

        total_items = self.container_count + self.document_count
        if total_items == 0:
            raise UserError(_("No items found in this location to move."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Bulk Move Items"),
            "res_model": "bulk.location.move.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_source_location_id": self.id,
                "default_item_count": total_items,
            },
        }

    def get_location_statistics(self):
        """Get comprehensive location statistics."""
        self.ensure_one()

        stats = {
            "total_capacity": self.total_capacity,
            "current_usage": self.current_usage,
            "available_capacity": self.available_capacity,
            "utilization_percentage": self.utilization_percentage,
            "container_count": self.container_count,
            "document_count": self.document_count,
            "current_weight": self.current_weight,
            "max_weight_capacity": self.max_weight_capacity,
            "weight_utilization": (
                (self.current_weight / self.max_weight_capacity * 100)
                if self.max_weight_capacity > 0
                else 0
            ),
            "monthly_cost": self.monthly_cost,
            "cost_per_item": (
                self.monthly_cost / (self.container_count + self.document_count)
                if (self.container_count + self.document_count) > 0
                else 0
            ),
        }

        return stats

    def create(self, vals):
        """Override create to set default values and initialize location."""
        if not vals.get("name"):
            vals["name"] = _("New Location %s") % fields.Datetime.now().strftime(
                "%Y%m%d-%H%M%S"
            )

        if not vals.get("code"):
            code_base = vals.get("name", "LOC").upper().replace(" ", "")[:10]
            vals["code"] = f"{code_base}_{fields.Datetime.now().strftime('%m%d')}"

        # Set default capacity if not provided
        if not vals.get("total_capacity"):
            location_type_defaults = {
                "warehouse": 10000,  # cubic feet
                "storage_facility": 5000,
                "vault": 1000,
                "office": 500,
                "archive": 2000,
                "mobile": 200,
            }
            vals["total_capacity"] = location_type_defaults.get(
                vals.get("location_type"), 1000
            )

        # Auto-configure based on location type
        if vals.get("location_type") == "vault":
            vals.update(
                {
                    "access_level": "confidential",
                    "security_level": "maximum",
                    "fireproof_rating": "2hour",
                    "fire_suppression_system": "gas",
                }
            )
        elif vals.get("location_type") == "climate_storage":
            vals.update(
                {
                    "climate_controlled": True,
                    "temperature_controlled": True,
                    "humidity_controlled": True,
                    "climate_monitoring_enabled": True,
                }
            )

        # Create the record
        record = super().create(vals)

        # Create location creation activity
        record.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Location created: %s") % record.name,
            note=_("New storage location has been created and configured."),
            user_id=record.responsible_user_id.id,
        )

        return record

    @api.model
    def get_locations_summary(self):
        """Get summary of all locations."""
        locations = self.search([("active", "=", True)])

        summary = {
            "total_locations": len(locations),
            "total_capacity": sum(loc.total_capacity for loc in locations),
            "total_usage": sum(loc.current_usage for loc in locations),
            "average_utilization": (
                sum(loc.utilization_percentage for loc in locations) / len(locations)
                if locations
                else 0
            ),
            "locations_by_type": {},
            "locations_by_state": {},
            "high_utilization_locations": len(
                locations.filtered(lambda l: l.utilization_percentage > 90)
            ),
            "maintenance_locations": len(
                locations.filtered(lambda l: l.state == "maintenance")
            ),
        }

        # Group by type
        location_types = [
            "warehouse",
            "office",
            "storage_facility",
            "vault",
            "climate_storage",
            "archive",
        ]
        for loc_type in location_types:
            type_locations = locations.filtered(
                lambda l, t=loc_type: l.location_type == t
            )
            summary["locations_by_type"][loc_type] = len(type_locations)

        # Group by state
        location_states = [
            "draft",
            "active",
            "maintenance",
            "full",
            "restricted",
            "retired",
        ]
        for loc_state in location_states:
            state_locations = locations.filtered(lambda l, s=loc_state: l.state == s)
            summary["locations_by_state"][loc_state] = len(state_locations)

        return summary

    def name_get(self):
        """Custom name_get to show additional information."""
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            if record.location_type:
                name += f" ({record.location_type.title()})"
            if record.utilization_percentage:
                name += f" - {record.utilization_percentage:.1f}% utilized"
            result.append((record.id, name))
        return result
        # Group by state
        location_states = [
            "draft",
            "active",
            "maintenance",
            "full",
            "restricted",
            "retired",
        ]
        for loc_state in location_states:
            state_locations = locations.filtered(lambda l, s=loc_state: l.state == s)
            summary["locations_by_state"][loc_state] = len(state_locations)

        return summary

    def name_get(self):
        """Custom name_get to show additional information."""
        result = []
        for record in self:
            name = record.name
            if record.code:
                name = f"[{record.code}] {name}"
            if record.location_type:
                name += f" ({record.location_type.title()})"
            if record.utilization_percentage:
                name += f" - {record.utilization_percentage:.1f}% utilized"
            result.append((record.id, name))
        return result
