# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Load(models.Model):
    _name = "load"
    _description = "Load"
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

    # === PAPER BALE LOAD MANAGEMENT FIELDS ===

    # Load Identification & Tracking
    load_date = fields.Date(
        string="Load Date", default=fields.Date.today, tracking=True
    )
    load_number = fields.Char(string="Load Number", copy=False, tracking=True)
    buyer_company = fields.Char(string="Buyer Company", tracking=True)
    sale_contract_number = fields.Char(string="Sale Contract Number", tracking=True)

    # Weight and Quantity Measurements
    total_weight = fields.Float(
        string="Total Weight (lbs)", compute="_compute_load_totals", store=True
    )
    total_weight_kg = fields.Float(
        string="Total Weight (kg)", compute="_compute_load_totals", store=True
    )
    bale_count = fields.Integer(
        string="Bale Count", compute="_compute_load_totals", store=True
    )
    average_bale_weight = fields.Float(
        string="Average Bale Weight", compute="_compute_load_totals", store=True
    )
    weight_ticket_count = fields.Integer(
        string="Weight Tickets", compute="_compute_weight_tickets", store=True
    )

    # Quality Control
    load_quality_grade = fields.Selection(
        [
            ("premium", "Premium Grade"),
            ("standard", "Standard Grade"),
            ("economy", "Economy Grade"),
            ("reject", "Reject"),
        ],
        string="Load Quality Grade",
        tracking=True,
    )
    moisture_content = fields.Float(string="Moisture Content (%)", tracking=True)
    contamination_level = fields.Selection(
        [
            ("none", "No Contamination"),
            ("minimal", "Minimal (<2%)"),
            ("acceptable", "Acceptable (2-5%)"),
            ("excessive", "Excessive (>5%)"),
        ],
        string="Contamination Level",
        tracking=True,
    )

    # Market and Pricing
    market_price_per_ton = fields.Monetary(
        string="Market Price per Ton", currency_field="currency_id", tracking=True
    )
    estimated_revenue = fields.Monetary(
        string="Estimated Revenue",
        compute="_compute_revenue",
        store=True,
        currency_field="currency_id",
    )
    actual_sale_price = fields.Monetary(
        string="Actual Sale Price", currency_field="currency_id", tracking=True
    )
    price_variance = fields.Monetary(
        string="Price Variance",
        compute="_compute_price_variance",
        store=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Shipping and Logistics
    shipping_date = fields.Date(string="Shipping Date", tracking=True)
    estimated_delivery = fields.Datetime(string="Estimated Delivery", tracking=True)
    actual_delivery = fields.Datetime(string="Actual Delivery", tracking=True)
    delivery_variance_hours = fields.Float(
        string="Delivery Variance (Hours)",
        compute="_compute_delivery_variance",
        store=True,
    )

    # Special Requirements
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
    )
    temperature_controlled = fields.Boolean(
        string="Temperature Controlled", tracking=True
    )
    hazmat_required = fields.Boolean(string="Hazmat Required", tracking=True)
    special_instructions = fields.Text(string="Special Instructions")

    # Load State Management (Enhanced)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready for Loading"),
            ("loading", "Loading in Progress"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Relationships
    bale_ids = fields.One2many("paper.bale", "load_id", string="Paper Bales")
    load_shipment_ids = fields.One2many(
        "paper.load.shipment", "load_id", string="Load Shipments"
    )

    # Documentation and Compliance
    manifest_number = fields.Char(string="Manifest Number", tracking=True)
    bill_of_lading = fields.Char(string="Bill of Lading", tracking=True)
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified", tracking=True
    )
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=True, tracking=True
    )

    # Customer and Market Information
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    market_location = fields.Char(string="Market Location", tracking=True)
    transportation_method = fields.Selection(
        [
            ("truck", "Truck"),
            ("rail", "Rail"),
            ("barge", "Barge"),
            ("container", "Container"),
        ],
        string="Transportation Method",
        tracking=True,
    )

    # Load Performance Metrics
    loading_start_time = fields.Datetime(string="Loading Start Time")
    loading_end_time = fields.Datetime(string="Loading End Time")
    loading_duration_hours = fields.Float(
        string="Loading Duration (Hours)",
        compute="_compute_loading_duration",
        store=True,
    )
    efficiency_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
        ],
        string="Efficiency Rating",
        compute="_compute_efficiency_rating",
        store=True,
    )

    # Revenue and Financial Tracking
    commission_rate = fields.Float(string="Commission Rate (%)", default=5.0)
    commission_amount = fields.Monetary(
        string="Commission Amount",
        compute="_compute_commission",
        store=True,
        currency_field="currency_id",
    )
    net_revenue = fields.Monetary(
        string="Net Revenue",
        compute="_compute_net_revenue",
        store=True,
        currency_field="currency_id",
    )
    profit_margin = fields.Float(
        string="Profit Margin (%)", compute="_compute_profit_margin", store=True
    )

    # Quality and Environmental Impact
    recycled_paper_percentage = fields.Float(
        string="Recycled Content (%)", default=100.0
    )
    carbon_footprint_reduction = fields.Float(
        string="Carbon Footprint Reduction (tons CO2)",
        compute="_compute_environmental_impact",
        store=True,
    )
    trees_saved = fields.Float(
        string="Trees Saved", compute="_compute_environmental_impact", store=True
    )
    water_saved = fields.Float(
        string="Water Saved (gallons)",
        compute="_compute_environmental_impact",
        store=True,
    )

    # Operational Fields
    driver_id = fields.Many2one("hr.employee", string="Driver", tracking=True)
    truck_id = fields.Many2one("fleet.vehicle", string="Truck", tracking=True)
    trailer_id = fields.Many2one("fleet.vehicle", string="Trailer", tracking=True)
    route_id = fields.Many2one("stock.route", string="Delivery Route")

    # Author and Audit Trail
    author_id = fields.Many2one(
        "res.users", string="Author", default=lambda self: self.env.user, tracking=True
    )
    last_updated_by = fields.Many2one(
        "res.users", string="Last Updated By", tracking=True
    )
    revision_number = fields.Integer(string="Revision Number", default=1)
    approval_required = fields.Boolean(string="Approval Required", default=False)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("bale_ids", "bale_ids.weight_lbs")
    def _compute_load_totals(self):
        """Compute load totals from associated bales."""
        for record in self:
            if record.bale_ids:
                record.total_weight = sum(
                    bale.weight_lbs for bale in record.bale_ids if bale.weight_lbs
                )
                record.total_weight_kg = (
                    record.total_weight * 0.453592
                )  # lbs to kg conversion
                record.bale_count = len(record.bale_ids)
                record.average_bale_weight = (
                    record.total_weight / record.bale_count if record.bale_count else 0
                )
            else:
                record.total_weight = 0
                record.total_weight_kg = 0
                record.bale_count = 0
                record.average_bale_weight = 0

    @api.depends("total_weight", "market_price_per_ton")
    def _compute_revenue(self):
        """Compute estimated revenue based on weight and market price."""
        for record in self:
            if record.total_weight and record.market_price_per_ton:
                tons = record.total_weight / 2000  # Convert lbs to tons
                record.estimated_revenue = tons * record.market_price_per_ton
            else:
                record.estimated_revenue = 0

    @api.depends("estimated_revenue", "actual_sale_price")
    def _compute_price_variance(self):
        """Compute variance between estimated and actual sale price."""
        for record in self:
            if record.actual_sale_price and record.estimated_revenue:
                record.price_variance = (
                    record.actual_sale_price - record.estimated_revenue
                )
            else:
                record.price_variance = 0

    @api.depends("estimated_delivery", "actual_delivery")
    def _compute_delivery_variance(self):
        """Compute delivery time variance in hours."""
        for record in self:
            if record.estimated_delivery and record.actual_delivery:
                delta = record.actual_delivery - record.estimated_delivery
                record.delivery_variance_hours = delta.total_seconds() / 3600
            else:
                record.delivery_variance_hours = 0

    @api.depends("loading_start_time", "loading_end_time")
    def _compute_loading_duration(self):
        """Compute loading duration in hours."""
        for record in self:
            if record.loading_start_time and record.loading_end_time:
                delta = record.loading_end_time - record.loading_start_time
                record.loading_duration_hours = delta.total_seconds() / 3600
            else:
                record.loading_duration_hours = 0

    @api.depends("loading_duration_hours", "bale_count")
    def _compute_efficiency_rating(self):
        """Compute efficiency rating based on loading time per bale."""
        for record in self:
            if record.bale_count and record.loading_duration_hours:
                time_per_bale = record.loading_duration_hours / record.bale_count
                if time_per_bale <= 0.25:  # 15 minutes per bale
                    record.efficiency_rating = "excellent"
                elif time_per_bale <= 0.5:  # 30 minutes per bale
                    record.efficiency_rating = "good"
                elif time_per_bale <= 1.0:  # 1 hour per bale
                    record.efficiency_rating = "fair"
                else:
                    record.efficiency_rating = "poor"
            else:
                record.efficiency_rating = "fair"

    @api.depends("estimated_revenue", "commission_rate")
    def _compute_commission(self):
        """Compute commission amount."""
        for record in self:
            if record.estimated_revenue and record.commission_rate:
                record.commission_amount = record.estimated_revenue * (
                    record.commission_rate / 100
                )
            else:
                record.commission_amount = 0

    @api.depends("estimated_revenue", "commission_amount")
    def _compute_net_revenue(self):
        """Compute net revenue after commission."""
        for record in self:
            record.net_revenue = record.estimated_revenue - record.commission_amount

    @api.depends("net_revenue", "estimated_revenue")
    def _compute_profit_margin(self):
        """Compute profit margin percentage."""
        for record in self:
            if record.estimated_revenue:
                record.profit_margin = (
                    record.net_revenue / record.estimated_revenue
                ) * 100
            else:
                record.profit_margin = 0

    @api.depends("total_weight")
    def _compute_environmental_impact(self):
        """Compute environmental impact metrics."""
        for record in self:
            if record.total_weight:
                tons = record.total_weight / 2000
                # Standard recycling impact calculations
                record.carbon_footprint_reduction = (
                    tons * 3.3
                )  # tons CO2 saved per ton recycled
                record.trees_saved = tons * 17  # trees saved per ton
                record.water_saved = tons * 7000  # gallons saved per ton
            else:
                record.carbon_footprint_reduction = 0
                record.trees_saved = 0
                record.water_saved = 0

    def _compute_weight_tickets(self):
        """Compute count of weight tickets."""
        for record in self:
            # Count related stock pickings or weight documents
            tickets = self.env["stock.picking"].search_count(
                [("origin", "ilike", record.name)]
            )
            record.weight_ticket_count = tickets

    def write(self, vals):
        """Override write to update modification date and track revisions."""
        vals["date_modified"] = fields.Datetime.now()

    # Load Management Fields
    activity_exception_decoration = fields.Selection(
        [("warning", "Warning"), ("danger", "Danger")], "Activity Exception Decoration"
    )
    activity_state = fields.Selection(
        [("overdue", "Overdue"), ("today", "Today"), ("planned", "Planned")],
        "Activity State",
    )
    message_type = fields.Selection(
        [("email", "Email"), ("comment", "Comment"), ("notification", "Notification")],
        "Message Type",
    )
    bale_number = fields.Char("Bale Number")
    capacity_utilization = fields.Float("Capacity Utilization %", default=0.0)
    contamination_notes = fields.Text("Contamination Notes")
    contamination_report = fields.Text("Contamination Report")
    date = fields.Date("Load Date")
    delivery_confirmation_required = fields.Boolean(
        "Delivery Confirmation Required", default=True
    )
    delivery_instructions = fields.Text("Delivery Instructions")
    driver_certification_verified = fields.Boolean(
        "Driver Certification Verified", default=False
    )
    estimated_arrival_time = fields.Datetime("Estimated Arrival Time")
    load_configuration = fields.Text("Load Configuration")
    load_optimization_algorithm = fields.Selection(
        [("weight", "Weight Based"), ("volume", "Volume Based"), ("mixed", "Mixed")],
        default="mixed",
    )
    load_securing_method = fields.Text("Load Securing Method")
    material_compatibility_verified = fields.Boolean(
        "Material Compatibility Verified", default=False
    )
    route_optimization_data = fields.Text("Route Optimization Data")
    safety_inspection_completed = fields.Boolean(
        "Safety Inspection Completed", default=False
    )
    temperature_monitoring_required = fields.Boolean(
        "Temperature Monitoring Required", default=False
    )
    transportation_hazards = fields.Text("Transportation Hazards")
    vehicle_inspection_completed = fields.Boolean(
        "Vehicle Inspection Completed", default=False
    )
    weight_distribution_notes = fields.Text("Weight Distribution Notes")

    def write(self, vals):
        """Override write method to track changes."""
        if any(
            key in vals
            for key in ["market_price_per_ton", "buyer_company", "total_weight"]
        ):
            vals["last_updated_by"] = self.env.user.id
            vals["revision_number"] = self.revision_number + 1
        return super().write(vals)

    @api.constrains("market_price_per_ton")
    def _check_market_price(self):
        """Validate market price is positive."""
        for record in self:
            if record.market_price_per_ton and record.market_price_per_ton < 0:
                raise ValidationError(_("Market price per ton must be positive."))

    @api.constrains("loading_start_time", "loading_end_time")
    def _check_loading_times(self):
        """Validate loading times are logical."""
        for record in self:
            if record.loading_start_time and record.loading_end_time:
                if record.loading_end_time <= record.loading_start_time:
                    raise ValidationError(
                        _("Loading end time must be after start time.")
                    )

    @api.constrains("estimated_delivery", "actual_delivery")
    def _check_delivery_times(self):
        """Validate delivery times."""
        for record in self:
            if record.estimated_delivery and record.actual_delivery:
                if record.actual_delivery < record.estimated_delivery - timedelta(
                    days=30
                ):
                    raise ValidationError(
                        _("Actual delivery time seems too early compared to estimate.")
                    )

    @api.model
    def get_load_performance_summary(self):
        """Get performance summary for dashboard."""
        loads = self.search([("state", "in", ["delivered", "sold"])])
        return {
            "total_loads": len(loads),
            "total_revenue": sum(loads.mapped("estimated_revenue")),
            "average_efficiency": loads.mapped("efficiency_rating"),
            "on_time_delivery_rate": (
                len(loads.filtered(lambda l: l.delivery_variance_hours <= 0))
                / len(loads)
                * 100
                if loads
                else 0
            ),
        }

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
    # LOAD ACTION METHODS
    # =============================================================================

    def action_prepare_load(self):
        """Prepare load for shipping."""
        self.ensure_one()
        self.write({"state": "ready", "loading_start_time": fields.Datetime.now()})
        self.message_post(body=_("Load preparation started."))

        # Create preparation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Prepare Load: {self.name}",
            note="Prepare load for shipping including bale verification, weight confirmation, and documentation.",
            user_id=self.user_id.id,
        )
        return True

    def action_ship_load(self):
        """Ship the load."""
        self.ensure_one()
        if self.state != "loading":
            raise UserError(_("Only loads in loading state can be shipped."))

        self.write(
            {
                "state": "shipped",
                "shipping_date": fields.Date.today(),
                "loading_end_time": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Load shipped successfully."))
        return True

    def action_start_loading(self):
        """Start loading process."""
        self.ensure_one()
        if self.state != "ready":
            raise UserError(_("Load must be in ready state to start loading."))

        self.write({"state": "loading", "loading_start_time": fields.Datetime.now()})
        self.message_post(body=_("Loading process started."))
        return True

    def action_mark_delivered(self):
        """Mark load as delivered."""
        self.ensure_one()
        if self.state != "shipped":
            raise UserError(_("Only shipped loads can be marked as delivered."))

        self.write({"state": "delivered", "actual_delivery": fields.Datetime.now()})
        self.message_post(body=_("Load delivered successfully."))
        return True

    def action_mark_sold(self):
        """Mark load as sold."""
        self.ensure_one()
        if self.state not in ["shipped", "delivered"]:
            raise UserError(_("Only shipped or delivered loads can be marked as sold."))

        self.write({"state": "sold"})
        self.message_post(body=_("Load marked as sold."))
        return True

    def action_cancel(self):
        """Cancel the load."""
        self.ensure_one()
        if self.state in ["sold", "delivered"]:
            raise UserError(_("Cannot cancel sold or delivered loads."))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Load cancelled."))
        return True

    def action_view_bales(self):
        """View bales in this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Load Bales"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {
                "default_load_id": self.id,
                "search_default_load_id": self.id,
            },
        }

    def action_view_revenue_report(self):
        """View revenue report for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.load_revenue_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_view_weight_tickets(self):
        """View weight tickets for this load."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weight Tickets"),
            "res_model": "stock.picking",
            "view_mode": "tree,form",
            "domain": [("origin", "ilike", self.name)],
            "context": {
                "search_default_origin": self.name,
                "group_by": "date",
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
