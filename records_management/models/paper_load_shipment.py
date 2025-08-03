# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperLoadShipment(models.Model):
    _name = "paper.load.shipment"
    _description = "Paper Load Shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    # === PAPER LOAD SHIPMENT MANAGEMENT FIELDS ===

    # Shipment Identification
    load_number = fields.Char(string="Load Number", required=True, tracking=True)
    pickup_date = fields.Date(
        string="Pickup Date", default=fields.Date.today, tracking=True
    )
    driver_name = fields.Char(string="Driver Name", tracking=True)
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)

    # Bale Information and Counts
    bale_count = fields.Integer(
        string="Total Bales", compute="_compute_bale_totals", store=True
    )
    bale_ids = fields.One2many("paper.bale", "load_shipment_id", string="Paper Bales")

    # Weight Tracking
    total_weight_lbs = fields.Float(
        string="Total Weight (lbs)", compute="_compute_weight_totals", store=True
    )
    total_weight_kg = fields.Float(
        string="Total Weight (kg)", compute="_compute_weight_totals", store=True
    )
    average_bale_weight = fields.Float(
        string="Average Bale Weight", compute="_compute_weight_totals", store=True
    )

    # Paper Type Specific Counts
    white_paper_count = fields.Integer(
        string="White Paper Bales", compute="_compute_paper_types", store=True
    )
    mixed_paper_count = fields.Integer(
        string="Mixed Paper Bales", compute="_compute_paper_types", store=True
    )
    cardboard_count = fields.Integer(
        string="Cardboard Bales", compute="_compute_paper_types", store=True
    )
    newspaper_count = fields.Integer(
        string="Newspaper Bales", compute="_compute_paper_types", store=True
    )
    magazine_count = fields.Integer(
        string="Magazine Bales", compute="_compute_paper_types", store=True
    )

    # Weight by Paper Type
    white_paper_weight = fields.Float(
        string="White Paper Weight (lbs)", compute="_compute_paper_weights", store=True
    )
    mixed_paper_weight = fields.Float(
        string="Mixed Paper Weight (lbs)", compute="_compute_paper_weights", store=True
    )
    cardboard_weight = fields.Float(
        string="Cardboard Weight (lbs)", compute="_compute_paper_weights", store=True
    )
    newspaper_weight = fields.Float(
        string="Newspaper Weight (lbs)", compute="_compute_paper_weights", store=True
    )
    magazine_weight = fields.Float(
        string="Magazine Weight (lbs)", compute="_compute_paper_weights", store=True
    )

    # Shipment Status (Enhanced)
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("scheduled", "Scheduled"),
            ("ready_pickup", "Ready for Pickup"),
            ("in_transit", "In Transit"),
            ("delivered", "Delivered"),
            ("invoiced", "Invoiced"),
            ("paid", "Paid"),
            ("cancelled", "Cancelled"),
        ],
        string="Shipment Status",
        default="draft",
        tracking=True,
    )

    # Manifest and Documentation
    manifest_generated = fields.Boolean(string="Manifest Generated", tracking=True)
    mobile_manifest = fields.Boolean(string="Mobile Manifest", tracking=True)
    manifest_number = fields.Char(string="Manifest Number", tracking=True)
    bill_of_lading = fields.Char(string="Bill of Lading", tracking=True)

    # Transportation Details
    truck_id = fields.Many2one("fleet.vehicle", string="Truck", tracking=True)
    trailer_id = fields.Many2one("fleet.vehicle", string="Trailer", tracking=True)
    driver_id = fields.Many2one("hr.employee", string="Driver Employee", tracking=True)
    transportation_company = fields.Char(string="Transportation Company", tracking=True)

    # Scheduling and Timing
    scheduled_pickup_time = fields.Datetime(
        string="Scheduled Pickup Time", tracking=True
    )
    actual_pickup_time = fields.Datetime(string="Actual Pickup Time", tracking=True)
    estimated_delivery_time = fields.Datetime(
        string="Estimated Delivery Time", tracking=True
    )
    actual_delivery_time = fields.Datetime(string="Actual Delivery Time", tracking=True)
    transit_duration_hours = fields.Float(
        string="Transit Duration (Hours)",
        compute="_compute_transit_duration",
        store=True,
    )

    # Location Information
    pickup_location_id = fields.Many2one(
        "stock.location", string="Pickup Location", tracking=True
    )
    delivery_location_id = fields.Many2one(
        "stock.location", string="Delivery Location", tracking=True
    )
    pickup_address = fields.Text(string="Pickup Address")
    delivery_address = fields.Text(string="Delivery Address")

    # Load Reference
    load_id = fields.Many2one("load", string="Parent Load", tracking=True)

    # Quality and Compliance
    quality_inspection_passed = fields.Boolean(
        string="Quality Inspection Passed", tracking=True
    )
    contamination_check_passed = fields.Boolean(
        string="Contamination Check Passed", tracking=True
    )
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified", tracking=True
    )
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=True, tracking=True
    )

    # Financial Information
    shipping_cost = fields.Monetary(
        string="Shipping Cost", currency_field="currency_id", tracking=True
    )
    fuel_surcharge = fields.Monetary(
        string="Fuel Surcharge", currency_field="currency_id"
    )
    total_shipping_cost = fields.Monetary(
        string="Total Shipping Cost",
        compute="_compute_total_shipping_cost",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Special Requirements
    hazmat_shipment = fields.Boolean(string="Hazmat Shipment", tracking=True)
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled", tracking=True
    )
    special_handling_instructions = fields.Text(string="Special Handling Instructions")

    # Performance Metrics
    on_time_pickup = fields.Boolean(
        string="On Time Pickup", compute="_compute_performance_metrics", store=True
    )
    on_time_delivery = fields.Boolean(
        string="On Time Delivery", compute="_compute_performance_metrics", store=True
    )
    customer_satisfaction_rating = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Customer Satisfaction",
        tracking=True,
    )

    # Tracking and Communication
    tracking_number = fields.Char(string="Tracking Number", tracking=True)
    gps_coordinates = fields.Char(string="GPS Coordinates")
    last_location_update = fields.Datetime(string="Last Location Update")
    customer_notifications_sent = fields.Integer(
        string="Customer Notifications Sent", default=0
    )

    # Weight Tickets and Documentation
    weight_ticket_in = fields.Char(string="Weight Ticket In", tracking=True)
    weight_ticket_out = fields.Char(string="Weight Ticket Out", tracking=True)
    tare_weight = fields.Float(string="Tare Weight (lbs)")
    gross_weight = fields.Float(string="Gross Weight (lbs)")
    net_weight = fields.Float(
        string="Net Weight (lbs)", compute="_compute_net_weight", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    bale_number = fields.Char(string="Bale Number")
    weight = fields.Float(string="Weight (lbs)", digits=(10, 2))
    delivery_date = fields.Date(string="Delivery Date")
    recycling_facility = fields.Char(string="Recycling Facility")
    contamination_level = fields.Selection(
        [("clean", "Clean"), ("light", "Light"), ("heavy", "Heavy")],
        string="Contamination Level",
    )
    price_per_ton = fields.Monetary(
        string="Price per Ton", currency_field="currency_id"
    )
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("bale_ids")
    def _compute_bale_totals(self):
        """Compute total bale count."""
        for record in self:
            record.bale_count = len(record.bale_ids)

    @api.depends("bale_ids", "bale_ids.weight_lbs")
    def _compute_weight_totals(self):
        """Compute weight totals from bales."""
        for record in self:
            if record.bale_ids:
                weights = [
                    bale.weight_lbs for bale in record.bale_ids if bale.weight_lbs
                ]
                record.total_weight_lbs = sum(weights)
                record.total_weight_kg = record.total_weight_lbs * 0.453592  # lbs to kg
                record.average_bale_weight = (
                    record.total_weight_lbs / len(weights) if weights else 0
                )
            else:
                record.total_weight_lbs = 0
                record.total_weight_kg = 0
                record.average_bale_weight = 0

    @api.depends("bale_ids", "bale_ids.paper_type")
    def _compute_paper_types(self):
        """Compute counts by paper type."""
        for record in self:
            bales = record.bale_ids
            record.white_paper_count = len(
                bales.filtered(lambda b: b.paper_type == "white")
            )
            record.mixed_paper_count = len(
                bales.filtered(lambda b: b.paper_type == "mixed")
            )
            record.cardboard_count = len(
                bales.filtered(lambda b: b.paper_type == "cardboard")
            )
            record.newspaper_count = len(
                bales.filtered(lambda b: b.paper_type == "newspaper")
            )
            record.magazine_count = len(
                bales.filtered(lambda b: b.paper_type == "magazine")
            )

    @api.depends("bale_ids", "bale_ids.paper_type", "bale_ids.weight_lbs")
    def _compute_paper_weights(self):
        """Compute weight totals by paper type."""
        for record in self:
            bales = record.bale_ids
            record.white_paper_weight = sum(
                bales.filtered(lambda b: b.paper_type == "white").mapped("weight_lbs")
            )
            record.mixed_paper_weight = sum(
                bales.filtered(lambda b: b.paper_type == "mixed").mapped("weight_lbs")
            )
            record.cardboard_weight = sum(
                bales.filtered(lambda b: b.paper_type == "cardboard").mapped(
                    "weight_lbs"
                )
            )
            record.newspaper_weight = sum(
                bales.filtered(lambda b: b.paper_type == "newspaper").mapped(
                    "weight_lbs"
                )
            )
            record.magazine_weight = sum(
                bales.filtered(lambda b: b.paper_type == "magazine").mapped(
                    "weight_lbs"
                )
            )

    @api.depends("actual_pickup_time", "actual_delivery_time")
    def _compute_transit_duration(self):
        """Compute transit duration in hours."""
        for record in self:
            if record.actual_pickup_time and record.actual_delivery_time:
                delta = record.actual_delivery_time - record.actual_pickup_time
                record.transit_duration_hours = delta.total_seconds() / 3600
            else:
                record.transit_duration_hours = 0

    @api.depends("shipping_cost", "fuel_surcharge")
    def _compute_total_shipping_cost(self):
        """Compute total shipping cost including surcharges."""
        for record in self:
            record.total_shipping_cost = (record.shipping_cost or 0) + (
                record.fuel_surcharge or 0
            )

    @api.depends("gross_weight", "tare_weight")
    def _compute_net_weight(self):
        """Compute net weight."""
        for record in self:
            record.net_weight = (record.gross_weight or 0) - (record.tare_weight or 0)

    @api.depends(
        "scheduled_pickup_time",
        "actual_pickup_time",
        "estimated_delivery_time",
        "actual_delivery_time",
    )
    def _compute_performance_metrics(self):
        """Compute performance metrics."""
        for record in self:
            # On time pickup (within 1 hour)
            if record.scheduled_pickup_time and record.actual_pickup_time:
                pickup_diff = abs(
                    (
                        record.actual_pickup_time - record.scheduled_pickup_time
                    ).total_seconds()
                    / 3600
                )
                record.on_time_pickup = pickup_diff <= 1.0
            else:
                record.on_time_pickup = False

            # On time delivery (within 2 hours)
            if record.estimated_delivery_time and record.actual_delivery_time:
                delivery_diff = abs(
                    (
                        record.actual_delivery_time - record.estimated_delivery_time
                    ).total_seconds()
                    / 3600
                )
                record.on_time_delivery = delivery_diff <= 2.0
            else:
                record.on_time_delivery = False

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()

    # Paper Load Shipment Management Fields
    company_signature_date = fields.Date("Company Signature Date")
    delivery_notes = fields.Text("Delivery Notes")
    destination_address = fields.Text("Destination Address")
    driver_license = fields.Char("Driver License Number")
    driver_phone = fields.Char("Driver Phone")
    cargo_insurance_required = fields.Boolean("Cargo Insurance Required", default=False)
    customs_documentation = fields.Text("Customs Documentation")
    delivery_confirmation_method = fields.Selection(
        [
            ("signature", "Signature"),
            ("photo", "Photo"),
            ("gps", "GPS"),
            ("code", "Confirmation Code"),
        ],
        default="signature",
    )
    delivery_priority = fields.Selection(
        [("standard", "Standard"), ("expedited", "Expedited"), ("urgent", "Urgent")],
        default="standard",
    )
    delivery_window_end = fields.Datetime("Delivery Window End")
    delivery_window_start = fields.Datetime("Delivery Window Start")
    environmental_conditions = fields.Selection(
        [
            ("standard", "Standard"),
            ("climate_controlled", "Climate Controlled"),
            ("hazmat", "Hazmat"),
        ],
        default="standard",
    )
    load_securing_equipment = fields.Text("Load Securing Equipment")
    manifest_number = fields.Char("Manifest Number")
    pickup_confirmation_required = fields.Boolean(
        "Pickup Confirmation Required", default=True
    )
    route_optimization_enabled = fields.Boolean(
        "Route Optimization Enabled", default=True
    )
    shipment_tracking_enabled = fields.Boolean(
        "Shipment Tracking Enabled", default=True
    )
    special_handling_instructions = fields.Text("Special Handling Instructions")
    temperature_monitoring_required = fields.Boolean(
        "Temperature Monitoring Required", default=False
    )
    third_party_logistics_provider = fields.Many2one(
        "res.partner", "Third Party Logistics Provider"
    )
    transportation_mode = fields.Selection(
        [("road", "Road"), ("rail", "Rail"), ("air", "Air"), ("sea", "Sea")],
        default="road",
    )
    vehicle_capacity_utilized = fields.Float("Vehicle Capacity Utilized %", default=0.0)
    vehicle_inspection_completed = fields.Boolean(
        "Vehicle Inspection Completed", default=False
    )
    weight_distribution_verified = fields.Boolean(
        "Weight Distribution Verified", default=False
    )

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =============================================================================
    # PAPER LOAD SHIPMENT ACTION METHODS
    # =============================================================================

    def action_add_bales_to_load(self):
        """Add paper bales to this load shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Bales to Load"),
            "res_model": "paper.bale",
            "view_mode": "tree",
            "domain": [
                ("state", "=", "ready_to_ship"),
                ("load_shipment_id", "=", False),
            ],
            "context": {
                "default_load_shipment_id": self.id,
                "search_default_ready_to_ship": 1,
            },
        }

    def action_create_invoice(self):
        """Create invoice for this shipment."""
        self.ensure_one()
        # Create invoice based on shipment value
        invoice_vals = {
            "move_type": "out_invoice",
            "partner_id": self.company_id.partner_id.id,  # Default to company partner
            "invoice_date": fields.Date.today(),
            "payment_reference": self.name,
            "narration": f"Invoice for paper load shipment: {self.name}",
        }

        invoice = self.env["account.move"].create(invoice_vals)
        self.message_post(body=_("Invoice created: %s") % invoice.name)

        return {
            "type": "ir.actions.act_window",
            "name": _("Created Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_generate_manifest(self):
        """Generate shipping manifest for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_load_manifest_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_mark_delivered(self):
        """Mark shipment as delivered."""
        self.ensure_one()
        self.write(
            {
                "state": "inactive",  # Using inactive as "delivered" state
                "date_modified": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Shipment marked as delivered."))
        return True

    def action_mark_in_transit(self):
        """Mark shipment as in transit."""
        self.ensure_one()
        self.write({"state": "active"})  # Using active as "in transit" state
        self.message_post(body=_("Shipment marked as in transit."))
        return True

    def action_mark_paid(self):
        """Mark shipment as paid."""
        self.ensure_one()
        # Add payment tracking field if needed
        self.message_post(body=_("Shipment marked as paid."))
        return True

    def action_ready_for_pickup(self):
        """Mark shipment as ready for pickup."""
        self.ensure_one()
        self.write({"state": "draft"})  # Using draft as "ready for pickup"
        self.message_post(body=_("Shipment ready for pickup."))
        return True

    def action_schedule_pickup(self):
        """Schedule pickup for this shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Pickup"),
            "res_model": "pickup.request",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_name": f"Pickup for {self.name}",
                "default_description": f"Scheduled pickup for paper load shipment: {self.name}",
                "default_load_shipment_id": self.id,
            },
        }

    def action_view_manifest(self):
        """View shipping manifest."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_load_manifest_report",
            "report_type": "qweb-html",  # View in browser instead of download
            "context": {"active_ids": [self.id]},
        }

    def action_view_weight_breakdown(self):
        """View weight breakdown of bales in this shipment."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weight Breakdown"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_shipment_id", "=", self.id)],
            "context": {
                "search_default_load_shipment_id": self.id,
                "group_by": "bale_type",
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)
