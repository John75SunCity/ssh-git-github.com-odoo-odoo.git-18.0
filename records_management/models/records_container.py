# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsContainer(models.Model):
    _name = "records.container"
    _description = "Records Container"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(
        string="Container Number", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Container Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)

    # Container Classification
    container_type = fields.Selection(
        [
            ("standard_box", "Standard Storage Box"),
            ("legal_box", "Legal Size Box"),
            ("file_folder", "File Folder"),
            ("binder", "Binder"),
            ("archive_box", "Archive Box"),
            ("media_container", "Media Container"),
            ("custom", "Custom Container"),
        ],
        string="Container Type",
        required=True,
        tracking=True,
    )
    container_category = fields.Selection(
        [
            ("permanent", "Permanent Storage"),
            ("temporary", "Temporary Storage"),
            ("transit", "In Transit"),
            ("destruction", "Pending Destruction"),
        ],
        string="Container Category",
        default="permanent",
        tracking=True,
    )
    container_material = fields.Selection(
        [
            ("cardboard", "Cardboard"),
            ("plastic", "Plastic"),
            ("metal", "Metal"),
            ("fireproof", "Fireproof Material"),
        ],
        string="Container Material",
        default="cardboard",
        tracking=True,
    )

    # Physical Specifications
    length = fields.Float(
        string="Length (inches)", tracking=True, help="Container length in inches"
    )
    width = fields.Float(
        string="Width (inches)", tracking=True, help="Container width in inches"
    )
    height = fields.Float(
        string="Height (inches)", tracking=True, help="Container height in inches"
    )
    volume = fields.Float(
        string="Volume (cubic inches)",
        compute="_compute_volume",
        store=True,
        help="Total volume in cubic inches",
    )
    volume_cubic_feet = fields.Float(
        string="Volume (cubic feet)",
        compute="_compute_volume",
        store=True,
        help="Total volume in cubic feet",
    )
    weight_empty = fields.Float(
        string="Empty Weight (lbs)", tracking=True, help="Weight of empty container"
    )
    weight_current = fields.Float(
        string="Current Weight (lbs)",
        compute="_compute_current_weight",
        store=True,
        help="Current total weight including contents",
    )
    weight_capacity = fields.Float(
        string="Weight Capacity (lbs)",
        default=35.0,
        tracking=True,
        help="Maximum weight capacity",
    )

    # Capacity and Usage
    document_capacity = fields.Integer(
        string="Document Capacity",
        default=100,
        tracking=True,
        help="Maximum number of documents this container can hold",
    )
    current_document_count = fields.Integer(
        string="Current Document Count",
        compute="_compute_document_metrics",
        store=True,
        help="Current number of documents in container",
    )
    available_document_space = fields.Integer(
        string="Available Document Space",
        compute="_compute_document_metrics",
        store=True,
        help="Remaining document capacity",
    )
    utilization_percentage = fields.Float(
        string="Utilization %",
        compute="_compute_document_metrics",
        store=True,
        digits=(5, 2),
        help="Percentage of capacity currently used",
    )

    # Location and Movement
    location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        tracking=True,
        help="Current storage location",
    )
    previous_location_id = fields.Many2one(
        "records.location",
        string="Previous Location",
        readonly=True,
        help="Previous storage location",
    )
    zone = fields.Char(string="Zone", tracking=True)
    aisle = fields.Char(string="Aisle", tracking=True)
    shelf = fields.Char(string="Shelf", tracking=True)
    position = fields.Char(string="Position", tracking=True)

    # Customer and Ownership
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    customer_inventory_id = fields.Many2one(
        "customer.inventory", string="Customer Inventory", tracking=True
    )
    department_id = fields.Many2one("hr.department", string="Department", tracking=True)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("stored", "Stored"),
            ("in_transit", "In Transit"),
            ("retrieved", "Retrieved"),
            ("pending_destruction", "Pending Destruction"),
            ("destroyed", "Destroyed"),
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
        string="Container Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # Identification and Tracking
    barcode = fields.Char(
        string="Barcode",
        copy=False,
        index=True,
        tracking=True,
        help="Unique barcode for container identification",
    )
    qr_code = fields.Char(
        string="QR Code", copy=False, tracking=True, help="QR code for mobile scanning"
    )
    rfid_tag = fields.Char(
        string="RFID Tag", copy=False, tracking=True, help="RFID tag identifier"
    )

    # Security and Access
    security_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("classified", "Classified"),
        ],
        string="Security Level",
        default="standard",
        tracking=True,
    )
    access_restricted = fields.Boolean(
        string="Access Restricted",
        default=False,
        tracking=True,
    )
    security_seal_number = fields.Char(
        string="Security Seal Number",
        tracking=True,
    )
    security_seal_applied = fields.Boolean(
        string="Security Seal Applied",
        default=False,
        tracking=True,
    )

    # Environmental Requirements
    climate_controlled = fields.Boolean(
        string="Climate Controlled Required",
        default=False,
        tracking=True,
    )
    temperature_sensitive = fields.Boolean(
        string="Temperature Sensitive",
        default=False,
        tracking=True,
    )
    humidity_sensitive = fields.Boolean(
        string="Humidity Sensitive",
        default=False,
        tracking=True,
    )
    fireproof_required = fields.Boolean(
        string="Fireproof Storage Required",
        default=False,
        tracking=True,
    )

    # Document Management
    document_ids = fields.One2many(
        "records.document", "container_id", string="Documents"
    )
    document_type_id = fields.Many2one(
        "records.document.type",
        string="Primary Document Type",
        tracking=True,
        help="Primary type of documents stored in this container",
    )

    # Service and Operations
    service_type = fields.Selection(
        [
            ("storage", "Storage Service"),
            ("retrieval", "Retrieval Service"),
            ("destruction", "Destruction Service"),
            ("scanning", "Scanning Service"),
            ("indexing", "Indexing Service"),
        ],
        string="Primary Service Type",
        tracking=True,
    )
    pickup_required = fields.Boolean(
        string="Pickup Required",
        default=False,
        tracking=True,
    )
    delivery_required = fields.Boolean(
        string="Delivery Required",
        default=False,
        tracking=True,
    )

    # Quality and Condition
    container_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Container Condition",
        default="good",
        tracking=True,
    )
    last_inspection_date = fields.Date(
        string="Last Inspection Date",
        tracking=True,
    )
    next_inspection_date = fields.Date(
        string="Next Inspection Date",
        tracking=True,
    )
    inspection_notes = fields.Text(
        string="Inspection Notes", help="Notes from last inspection"
    )

    # Financial Information
    storage_cost_monthly = fields.Monetary(
        string="Monthly Storage Cost",
        currency_field="currency_id",
        tracking=True,
    )
    retrieval_fee = fields.Monetary(
        string="Retrieval Fee",
        currency_field="currency_id",
        tracking=True,
    )
    destruction_fee = fields.Monetary(
        string="Destruction Fee",
        currency_field="currency_id",
        tracking=True,
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
    stored_date = fields.Date(
        string="Stored Date",
        tracking=True,
    )
    last_access_date = fields.Date(
        string="Last Access Date",
        tracking=True,
    )
    destruction_date = fields.Date(
        string="Destruction Date",
        tracking=True,
    )

    # Movement and History
    movement_history_ids = fields.One2many(
        "records.container.movement", "container_id", string="Movement History"
    )
    last_movement_date = fields.Datetime(
        string="Last Movement Date",
        compute="_compute_last_movement",
        store=True,
    )
    movement_count = fields.Integer(
        string="Movement Count",
        compute="_compute_movement_count",
        store=True,
    )

    # Computed Display Fields
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
    )
    dimensions_display = fields.Char(
        string="Dimensions",
        compute="_compute_dimensions_display",
        help="Formatted dimension display (L×W×H)",
    )
    location_path = fields.Char(
        string="Location Path",
        compute="_compute_location_path",
        store=True,
        help="Full location path",
    )

    # Standard Size Recognition
    container_size_type = fields.Selection(
        [
            ("standard", 'Standard (15"×12"×10")'),
            ("legal", 'Legal/Double-size (15"×24"×10")'),
            ("letter", 'Letter Size (12"×15"×10")'),
            ("custom", "Custom Size"),
        ],
        string="Container Size Type",
        compute="_compute_container_size_type",
        help="Recognized standard container sizes",
    )

    # ============ COMPUTE METHODS ============

    @api.depends("length", "width", "height")
    def _compute_volume(self):
        """Calculate container volume in cubic inches and cubic feet"""
        for record in self:
            if record.length and record.width and record.height:
                cubic_inches = record.length * record.width * record.height
                record.volume = cubic_inches
                record.volume_cubic_feet = (
                    cubic_inches / 1728.0
                )  # 1 cubic foot = 1728 cubic inches
            else:
                record.volume = 0.0
                record.volume_cubic_feet = 0.0

    @api.depends("weight_empty", "document_ids", "document_ids.weight")
    def _compute_current_weight(self):
        """Calculate current total weight including contents"""
        for record in self:
            document_weight = sum(record.document_ids.mapped("weight") or [0.0])
            record.weight_current = (record.weight_empty or 0.0) + document_weight

    @api.depends("document_ids", "document_capacity")
    def _compute_document_metrics(self):
        """Calculate document utilization metrics"""
        for record in self:
            current_count = len(record.document_ids)
            capacity = record.document_capacity or 1

            record.current_document_count = current_count
            record.available_document_space = max(0, capacity - current_count)
            record.utilization_percentage = (
                (current_count / capacity) * 100.0 if capacity > 0 else 0.0
            )

    @api.depends("movement_history_ids", "movement_history_ids.movement_date")
    def _compute_last_movement(self):
        """Calculate last movement date"""
        for record in self:
            if record.movement_history_ids:
                record.last_movement_date = max(
                    record.movement_history_ids.mapped("movement_date")
                )
            else:
                record.last_movement_date = False

    @api.depends("movement_history_ids")
    def _compute_movement_count(self):
        """Calculate total number of movements"""
        for record in self:
            record.movement_count = len(record.movement_history_ids)

    @api.depends("name", "container_type", "customer_id")
    def _compute_display_name(self):
        """Create display name for container"""
        for record in self:
            parts = [record.name or ""]
            if record.container_type:
                parts.append(
                    f"({dict(record._fields['container_type'].selection).get(record.container_type, '')})"
                )
            if record.customer_id:
                parts.append(f"- {record.customer_id.name}")
            record.display_name = " ".join(filter(None, parts))

    @api.depends("length", "width", "height")
    def _compute_dimensions_display(self):
        """Format dimensions for display"""
        for record in self:
            if record.length and record.width and record.height:
                record.dimensions_display = (
                    f'{record.length}"×{record.width}"×{record.height}"'
                )
            else:
                record.dimensions_display = "Not specified"

    @api.depends("location_id", "zone", "aisle", "shelf", "position")
    def _compute_location_path(self):
        """Build full location path"""
        for record in self:
            path_parts = []
            if record.location_id:
                path_parts.append(record.location_id.name)
            if record.zone:
                path_parts.append(f"Zone {record.zone}")
            if record.aisle:
                path_parts.append(f"Aisle {record.aisle}")
            if record.shelf:
                path_parts.append(f"Shelf {record.shelf}")
            if record.position:
                path_parts.append(f"Pos {record.position}")
            record.location_path = " / ".join(path_parts) if path_parts else ""

    @api.depends("length", "width", "height")
    def _compute_container_size_type(self):
        """Recognize standard container sizes"""
        for record in self:
            if record.length and record.width and record.height:
                # Standard box: 15"×12"×10"
                if (
                    abs(record.length - 15) <= 0.5
                    and abs(record.width - 12) <= 0.5
                    and abs(record.height - 10) <= 0.5
                ):
                    record.container_size_type = "standard"
                # Legal/Double-size: 15"×24"×10"
                elif (
                    abs(record.length - 15) <= 0.5
                    and abs(record.width - 24) <= 0.5
                    and abs(record.height - 10) <= 0.5
                ):
                    record.container_size_type = "legal"
                # Letter size: 12"×15"×10"
                elif (
                    abs(record.length - 12) <= 0.5
                    and abs(record.width - 15) <= 0.5
                    and abs(record.height - 10) <= 0.5
                ):
                    record.container_size_type = "letter"
                else:
                    record.container_size_type = "custom"
            else:
                record.container_size_type = "custom"

    # ============ ONCHANGE METHODS ============

    @api.onchange("container_type")
    def _onchange_container_type(self):
        """Set default dimensions based on container type"""
        if self.container_type == "standard_box":
            self.length = 15.0
            self.width = 12.0
            self.height = 10.0
            self.document_capacity = 100
            self.weight_capacity = 35.0
        elif self.container_type == "legal_box":
            self.length = 15.0
            self.width = 24.0
            self.height = 10.0
            self.document_capacity = 200
            self.weight_capacity = 45.0
        elif self.container_type == "file_folder":
            self.length = 12.0
            self.width = 9.0
            self.height = 1.5
            self.document_capacity = 50
            self.weight_capacity = 5.0

    @api.onchange("location_id")
    def _onchange_location_id(self):
        """Update previous location when location changes"""
        if self.location_id and self._origin.location_id != self.location_id:
            self.previous_location_id = self._origin.location_id

    # ============ CONSTRAINT METHODS ============

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate container dimensions are positive"""
        for record in self:
            if record.length and record.length <= 0:
                raise ValidationError("Container length must be positive")
            if record.width and record.width <= 0:
                raise ValidationError("Container width must be positive")
            if record.height and record.height <= 0:
                raise ValidationError("Container height must be positive")

    @api.constrains("weight_capacity", "weight_current")
    def _check_weight_limits(self):
        """Validate weight constraints"""
        for record in self:
            if record.weight_capacity and record.weight_capacity <= 0:
                raise ValidationError("Weight capacity must be positive")
            if record.weight_current > record.weight_capacity:
                raise ValidationError(
                    f"Current weight ({record.weight_current} lbs) exceeds capacity ({record.weight_capacity} lbs)"
                )

    @api.constrains("document_capacity", "current_document_count")
    def _check_document_capacity(self):
        """Validate document capacity constraints"""
        for record in self:
            if record.document_capacity and record.document_capacity <= 0:
                raise ValidationError("Document capacity must be positive")

    @api.constrains("barcode")
    def _check_barcode_unique(self):
        """Ensure barcode uniqueness"""
        for record in self:
            if record.barcode:
                existing = self.search(
                    [("barcode", "=", record.barcode), ("id", "!=", record.id)]
                )
                if existing:
                    raise ValidationError(
                        f"Barcode {record.barcode} already exists for container {existing.name}"
                    )

    # ============ ACTION METHODS ============

    def action_activate_container(self):
        """Activate container for use"""
        for record in self:
            if record.state != "draft":
                raise UserError("Can only activate draft containers")
            record.write(
                {
                    "state": "active",
                    "stored_date": fields.Date.today(),
                }
            )
            record.message_post(body="Container activated and ready for use")

    def action_store_container(self):
        """Mark container as stored in location"""
        for record in self:
            if record.state not in ["active", "in_transit"]:
                raise UserError("Can only store active or in-transit containers")
            if not record.location_id:
                raise UserError("Storage location must be specified")
            record.write(
                {
                    "state": "stored",
                    "stored_date": fields.Date.today(),
                    "last_access_date": fields.Date.today(),
                }
            )
            record.message_post(body=f"Container stored at {record.location_id.name}")

    def action_mark_in_transit(self):
        """Mark container as in transit"""
        for record in self:
            if record.state not in ["active", "stored"]:
                raise UserError("Can only transit active or stored containers")
            record.write({"state": "in_transit"})
            record.message_post(body="Container marked as in transit")

    def action_retrieve_container(self):
        """Mark container as retrieved from storage"""
        for record in self:
            if record.state != "stored":
                raise UserError("Can only retrieve stored containers")
            record.write(
                {
                    "state": "retrieved",
                    "last_access_date": fields.Date.today(),
                }
            )
            record.message_post(body="Container retrieved from storage")

    def action_prepare_destruction(self):
        """Prepare container for destruction"""
        for record in self:
            if record.state not in ["stored", "retrieved"]:
                raise UserError(
                    "Can only prepare stored or retrieved containers for destruction"
                )
            record.write({"state": "pending_destruction"})
            record.message_post(body="Container prepared for destruction")

    def action_destroy_container(self):
        """Mark container as destroyed"""
        for record in self:
            if record.state != "pending_destruction":
                raise UserError("Can only destroy containers pending destruction")
            record.write(
                {
                    "state": "destroyed",
                    "destruction_date": fields.Date.today(),
                    "active": False,
                }
            )
            record.message_post(body="Container destroyed")

    def action_apply_security_seal(self):
        """Apply security seal to container"""
        for record in self:
            if not record.security_seal_number:
                raise UserError("Security seal number must be specified")
            record.write(
                {
                    "security_seal_applied": True,
                }
            )
            record.message_post(
                body=f"Security seal {record.security_seal_number} applied"
            )

    def action_remove_security_seal(self):
        """Remove security seal from container"""
        for record in self:
            record.write(
                {
                    "security_seal_applied": False,
                    "security_seal_number": False,
                }
            )
            record.message_post(body="Security seal removed")

    def action_schedule_inspection(self):
        """Schedule container inspection"""
        for record in self:
            # Calculate next inspection date (quarterly)
            next_date = fields.Date.add(fields.Date.today(), months=3)
            record.write({"next_inspection_date": next_date})
            record.message_post(body=f"Inspection scheduled for {next_date}")

    def action_complete_inspection(self):
        """Complete container inspection"""
        for record in self:
            today = fields.Date.today()
            # Calculate next inspection date (quarterly)
            next_date = fields.Date.add(today, months=3)
            record.write(
                {
                    "last_inspection_date": today,
                    "next_inspection_date": next_date,
                }
            )
            record.message_post(body="Container inspection completed")

    def action_update_location(self):
        """Update container location with movement tracking"""
        for record in self:
            if record.location_id:
                # Create movement history record
                self.env["records.container.movement"].create(
                    {
                        "container_id": record.id,
                        "from_location_id": (
                            record.previous_location_id.id
                            if record.previous_location_id
                            else False
                        ),
                        "to_location_id": record.location_id.id,
                        "movement_date": fields.Datetime.now(),
                        "movement_type": "relocation",
                        "user_id": self.env.user.id,
                    }
                )
                record.message_post(
                    body=f"Container moved to {record.location_id.name}"
                )

    def action_generate_barcode(self):
        """Generate unique barcode for container"""
        for record in self:
            if not record.barcode:
                # Generate barcode based on container type and sequence
                sequence = self.env["ir.sequence"].next_by_code(
                    "records.container.barcode"
                )
                prefix = {
                    "standard_box": "SB",
                    "legal_box": "LB",
                    "file_folder": "FF",
                    "binder": "BN",
                    "archive_box": "AB",
                    "media_container": "MC",
                    "custom": "CU",
                }.get(record.container_type, "CT")
                record.barcode = f"{prefix}{sequence}"
                record.message_post(body=f"Barcode generated: {record.barcode}")

    def action_generate_qr_code(self):
        """Generate QR code for container"""
        for record in self:
            if not record.qr_code:
                # Generate QR code with container information
                qr_data = f"CONTAINER:{record.name}:{record.customer_id.name if record.customer_id else 'UNKNOWN'}"
                record.qr_code = qr_data
                record.message_post(body="QR code generated for mobile scanning")

    def action_view_documents(self):
        """View documents in this container"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Documents in {self.name}",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id},
        }

    def action_view_movement_history(self):
        """View container movement history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Movement History - {self.name}",
            "res_model": "records.container.movement",
            "view_mode": "tree,form",
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id},
        }

    def action_create_pickup_request(self):
        """Create pickup request for container"""
        for record in self:
            pickup_request = self.env["pickup.request"].create(
                {
                    "name": f"Pickup Request - {record.name}",
                    "customer_id": record.customer_id.id,
                    "pickup_date": fields.Date.today(),
                    "container_ids": [(4, record.id)],
                    "state": "draft",
                }
            )
            record.pickup_required = False
            record.message_post(body=f"Pickup request created: {pickup_request.name}")

    def action_create_delivery_request(self):
        """Create delivery request for container"""
        for record in self:
            delivery_request = self.env["delivery.request"].create(
                {
                    "name": f"Delivery Request - {record.name}",
                    "customer_id": record.customer_id.id,
                    "delivery_date": fields.Date.today(),
                    "container_ids": [(4, record.id)],
                    "state": "draft",
                }
            )
            record.delivery_required = False
            record.message_post(
                body=f"Delivery request created: {delivery_request.name}"
            )

    def action_reset_to_draft(self):
        """Reset container to draft state"""
        for record in self:
            if record.state == "destroyed":
                raise UserError("Cannot reset destroyed containers")
            record.write(
                {
                    "state": "draft",
                    "stored_date": False,
                    "destruction_date": False,
                    "last_access_date": False,
                }
            )
            record.message_post(body="Container reset to draft state")

    # ============ UTILITY METHODS ============

    def get_capacity_status(self):
        """Get container capacity status"""
        self.ensure_one()
        if self.utilization_percentage >= 95:
            return "full"
        elif self.utilization_percentage >= 80:
            return "near_full"
        elif self.utilization_percentage >= 50:
            return "half_full"
        else:
            return "available"

    def is_overweight(self):
        """Check if container is overweight"""
        self.ensure_one()
        return self.weight_current > self.weight_capacity

    def is_due_for_inspection(self):
        """Check if container is due for inspection"""
        self.ensure_one()
        if not self.next_inspection_date:
            return True
        return fields.Date.today() >= self.next_inspection_date

    def get_storage_requirements(self):
        """Get special storage requirements"""
        self.ensure_one()
        requirements = []
        if self.climate_controlled:
            requirements.append("Climate Controlled")
        if self.temperature_sensitive:
            requirements.append("Temperature Sensitive")
        if self.humidity_sensitive:
            requirements.append("Humidity Sensitive")
        if self.fireproof_required:
            requirements.append("Fireproof Storage")
        if self.access_restricted:
            requirements.append("Restricted Access")
        return requirements

    @api.model
    def create(self, vals):
        """Override create to handle automatic field population"""
        # Auto-generate barcode if not provided
        if not vals.get("barcode") and vals.get("container_type"):
            sequence = (
                self.env["ir.sequence"].next_by_code("records.container.barcode")
                or "001"
            )
            prefix = {
                "standard_box": "SB",
                "legal_box": "LB",
                "file_folder": "FF",
                "binder": "BN",
                "archive_box": "AB",
                "media_container": "MC",
                "custom": "CU",
            }.get(vals["container_type"], "CT")
            vals["barcode"] = f"{prefix}{sequence}"

        # Set default dimensions based on container type
        if vals.get("container_type") and not any(
            k in vals for k in ["length", "width", "height"]
        ):
            defaults = {
                "standard_box": {
                    "length": 15.0,
                    "width": 12.0,
                    "height": 10.0,
                    "document_capacity": 100,
                },
                "legal_box": {
                    "length": 15.0,
                    "width": 24.0,
                    "height": 10.0,
                    "document_capacity": 200,
                },
                "file_folder": {
                    "length": 12.0,
                    "width": 9.0,
                    "height": 1.5,
                    "document_capacity": 50,
                },
            }
            if vals["container_type"] in defaults:
                vals.update(defaults[vals["container_type"]])

        return super().create(vals)

    def write(self, vals):
        """Override write to handle location changes and tracking"""
        # Track location changes
        if "location_id" in vals:
            for record in self:
                if record.location_id and record.location_id.id != vals["location_id"]:
                    vals["previous_location_id"] = record.location_id.id

        # Update timestamp
        vals["updated_date"] = fields.Datetime.now()

        return super().write(vals)
