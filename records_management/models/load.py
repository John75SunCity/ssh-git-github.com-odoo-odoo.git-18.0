# -*- coding: utf-8 -*-
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class Load(models.Model):
    _name = "load"
    _description = "Paper Bale Load Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "date_created desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Load Number", required=True, tracking=True, index=True)
    description = fields.Text(string="Load Description")
    sequence = fields.Integer(string="Sequence", default=10)
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
        string="Load Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preparing", "Preparing"),
            ("loading", "Loading"),
            ("ready", "Ready to Ship"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("sold", "Sold"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # LOAD DETAILS & SPECIFICATIONS
    # ============================================================================

    # Load Information
    load_type = fields.Selection(
        [
            ("standard", "Standard Load"),
            ("oversized", "Oversized Load"),
            ("mixed", "Mixed Load"),
            ("priority", "Priority Load"),
        ],
        string="Load Type",
        default="standard",
        required=True,
    )

    # Bale Information
    total_bales = fields.Integer(string="Total Bales", default=0)
    total_weight = fields.Float(string="Total Weight (lbs)", digits=(10, 2))
    average_bale_weight = fields.Float(
        string="Average Bale Weight",
        compute="_compute_load_metrics",
        store=True,
        digits=(8, 2),
    )

    # Quality Information
    quality_grade = fields.Selection(
        [
            ("premium", "Premium Grade"),
            ("standard", "Standard Grade"),
            ("mixed", "Mixed Grade"),
            ("rejected", "Rejected"),
        ],
        string="Quality Grade",
        default="standard",
    )

    quality_certificate = fields.Binary(string="Quality Certificate")
    quality_notes = fields.Text(string="Quality Notes")

    # ============================================================================
    # SCHEDULING & LOGISTICS
    # ============================================================================

    # Date Management
    date_created = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True,
    )
    date_scheduled = fields.Datetime(string="Scheduled Date", tracking=True)
    date_loaded = fields.Datetime(string="Loading Date")
    date_shipped = fields.Datetime(string="Shipping Date")
    date_delivered = fields.Datetime(string="Delivery Date")
    production_date = fields.Date(string="Production Date")

    # Loading Information
    loading_start_time = fields.Datetime(string="Loading Start Time")
    loading_end_time = fields.Datetime(string="Loading End Time")
    loading_duration = fields.Float(
        string="Loading Duration (Hours)",
        compute="_compute_loading_metrics",
        store=True,
        digits=(5, 2),
    )

    # Delivery Information
    estimated_delivery_date = fields.Datetime(string="Estimated Delivery")
    actual_delivery_date = fields.Datetime(string="Actual Delivery")
    delivery_variance = fields.Float(
        string="Delivery Variance (Hours)",
        compute="_compute_delivery_metrics",
        store=True,
        digits=(5, 2),
    )

    # ============================================================================
    # TRANSPORTATION & LOGISTICS
    # ============================================================================

    # Vehicle Information
    truck_number = fields.Char(string="Truck Number")
    trailer_number = fields.Char(string="Trailer Number")
    driver_name = fields.Char(string="Driver Name")
    driver_contact = fields.Char(string="Driver Contact")

    # Loading Dock Requirements
    loading_dock_requirements = fields.Text(string="Loading Dock Requirements")
    special_handling_required = fields.Boolean(string="Special Handling Required")
    equipment_needed = fields.Text(string="Equipment Needed")

    # Route Information
    destination_address = fields.Text(string="Destination Address")
    route_notes = fields.Text(string="Route Notes")
    estimated_distance = fields.Float(string="Distance (Miles)", digits=(8, 2))

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Pricing Information
    market_price = fields.Monetary(
        string="Market Price per Ton",
        currency_field="currency_id",
    )
    contracted_price = fields.Monetary(
        string="Contracted Price per Ton",
        currency_field="currency_id",
    )
    price_variance = fields.Monetary(
        string="Price Variance",
        compute="_compute_financial_metrics",
        store=True,
        currency_field="currency_id",
    )

    # Revenue Calculation
    gross_revenue = fields.Monetary(
        string="Gross Revenue",
        compute="_compute_financial_metrics",
        store=True,
        currency_field="currency_id",
    )
    transportation_cost = fields.Monetary(
        string="Transportation Cost",
        currency_field="currency_id",
    )
    commission = fields.Monetary(
        string="Commission",
        compute="_compute_financial_metrics",
        store=True,
        currency_field="currency_id",
    )
    net_revenue = fields.Monetary(
        string="Net Revenue",
        compute="_compute_financial_metrics",
        store=True,
        currency_field="currency_id",
    )

    # Profitability
    profit_margin = fields.Float(
        string="Profit Margin (%)",
        compute="_compute_financial_metrics",
        store=True,
        digits=(5, 2),
    )

    # ============================================================================
    # OPERATIONAL METRICS
    # ============================================================================

    # Efficiency Metrics
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
        compute="_compute_efficiency_metrics",
        store=True,
    )

    load_utilization = fields.Float(
        string="Load Utilization (%)",
        compute="_compute_efficiency_metrics",
        store=True,
        digits=(5, 2),
    )

    delivery_efficiency = fields.Float(
        string="Delivery Efficiency (%)",
        compute="_compute_efficiency_metrics",
        store=True,
        digits=(5, 2),
    )

    # Environmental Impact
    fuel_consumption = fields.Float(string="Fuel Consumption (Gallons)", digits=(8, 2))
    co2_emissions = fields.Float(
        string="CO2 Emissions (lbs)",
        compute="_compute_environmental_impact",
        store=True,
        digits=(10, 2),
    )

    # ============================================================================
    # DOCUMENTATION & ATTACHMENTS
    # ============================================================================

    # Documentation
    weight_tickets = fields.Integer(
        string="Weight Tickets Count",
        compute="_compute_documentation",
        store=True,
    )
    bill_of_lading = fields.Binary(string="Bill of Lading")
    delivery_receipt = fields.Binary(string="Delivery Receipt")
    invoice_number = fields.Char(string="Invoice Number")

    # Photos and Images
    image = fields.Binary(string="Load Image")
    photo_ids = fields.One2many(
        "ir.attachment",
        "res_id",
        string="Load Photos",
        domain=[("res_model", "=", "load")],
    )

    # Notes and Comments
    notes = fields.Text(string="Internal Notes")
    customer_notes = fields.Text(string="Customer Notes")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Related Records
    bale_ids = fields.One2many(
        "paper.bale",
        "load_id",
        string="Paper Bales",
    )
    customer_id = fields.Many2one("res.partner", string="Customer")
    vendor_id = fields.Many2one("res.partner", string="Vendor/Supplier")

    # Billing Information
    invoice_id = fields.Many2one("account.move", string="Customer Invoice")
    vendor_bill_id = fields.Many2one("account.move", string="Vendor Bill")

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("total_bales", "total_weight")
    def _compute_load_metrics(self):
        """Compute load-related metrics"""
        for record in self:
            if record.total_bales and record.total_weight:
                record.average_bale_weight = record.total_weight / record.total_bales
            else:
                record.average_bale_weight = 0.0

    @api.depends("loading_start_time", "loading_end_time")
    def _compute_loading_metrics(self):
        """Compute loading duration and efficiency"""
        for record in self:
            if record.loading_start_time and record.loading_end_time:
                delta = record.loading_end_time - record.loading_start_time
                record.loading_duration = delta.total_seconds() / 3600.0
            else:
                record.loading_duration = 0.0

    @api.depends("estimated_delivery_date", "actual_delivery_date")
    def _compute_delivery_metrics(self):
        """Compute delivery variance"""
        for record in self:
            if record.estimated_delivery_date and record.actual_delivery_date:
                delta = record.actual_delivery_date - record.estimated_delivery_date
                record.delivery_variance = delta.total_seconds() / 3600.0
            else:
                record.delivery_variance = 0.0

    @api.depends("total_weight", "market_price", "contracted_price", "transportation_cost")
    def _compute_financial_metrics(self):
        """Compute financial metrics and profitability"""
        for record in self:
            weight_tons = record.total_weight / 2000.0 if record.total_weight else 0.0
            
            # Price variance
            if record.market_price and record.contracted_price:
                record.price_variance = (record.contracted_price - record.market_price) * weight_tons
            else:
                record.price_variance = 0.0
            
            # Gross revenue
            if record.contracted_price and weight_tons:
                record.gross_revenue = record.contracted_price * weight_tons
            else:
                record.gross_revenue = 0.0
            
            # Commission (5% of gross revenue)
            record.commission = record.gross_revenue * 0.05
            
            # Net revenue
            record.net_revenue = record.gross_revenue - (record.transportation_cost or 0.0) - record.commission
            
            # Profit margin
            if record.gross_revenue:
                record.profit_margin = (record.net_revenue / record.gross_revenue) * 100
            else:
                record.profit_margin = 0.0

    @api.depends("loading_duration", "delivery_variance", "total_weight")
    def _compute_efficiency_metrics(self):
        """Compute efficiency ratings and utilization"""
        for record in self:
            # Load utilization (based on standard capacity)
            standard_capacity = 50000  # 50,000 lbs standard capacity
            if record.total_weight and standard_capacity:
                record.load_utilization = min((record.total_weight / standard_capacity) * 100, 100)
            else:
                record.load_utilization = 0.0
            
            # Delivery efficiency (on-time performance)
            if record.delivery_variance is not False:
                if abs(record.delivery_variance) <= 2:  # Within 2 hours
                    record.delivery_efficiency = 100.0
                elif abs(record.delivery_variance) <= 8:  # Within 8 hours
                    record.delivery_efficiency = 75.0
                elif abs(record.delivery_variance) <= 24:  # Within 24 hours
                    record.delivery_efficiency = 50.0
                else:
                    record.delivery_efficiency = 25.0
            else:
                record.delivery_efficiency = 0.0
            
            # Overall efficiency rating
            avg_efficiency = (record.load_utilization + record.delivery_efficiency) / 2
            if avg_efficiency >= 90:
                record.efficiency_rating = "excellent"
            elif avg_efficiency >= 75:
                record.efficiency_rating = "good"
            elif avg_efficiency >= 50:
                record.efficiency_rating = "fair"
            else:
                record.efficiency_rating = "poor"

    @api.depends("fuel_consumption")
    def _compute_environmental_impact(self):
        """Compute environmental impact metrics"""
        for record in self:
            # CO2 emissions: approximately 22 lbs CO2 per gallon of diesel
            if record.fuel_consumption:
                record.co2_emissions = record.fuel_consumption * 22.0
            else:
                record.co2_emissions = 0.0

    @api.depends("bale_ids")
    def _compute_documentation(self):
        """Compute documentation counts"""
        for record in self:
            # Count weight tickets from related bales or attachments
            record.weight_tickets = len(record.bale_ids.filtered(lambda b: b.weight_ticket))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_prepare_load(self):
        """Prepare load for loading"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft loads can be prepared."))
        
        self.write({"state": "preparing"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Load Prepared"),
                "message": _("Load is now being prepared for loading."),
                "type": "success",
            },
        }

    def action_start_loading(self):
        """Start loading process"""
        self.ensure_one()
        if self.state != "preparing":
            raise UserError(_("Load must be in preparing state to start loading."))
        
        self.write({
            "state": "loading",
            "loading_start_time": fields.Datetime.now(),
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Loading Started"),
                "message": _("Load loading process has been initiated."),
                "type": "success",
            },
        }

    def action_complete_loading(self):
        """Complete loading and mark ready to ship"""
        self.ensure_one()
        if self.state != "loading":
            raise UserError(_("Load must be in loading state to complete."))
        
        self.write({
            "state": "ready",
            "loading_end_time": fields.Datetime.now(),
            "date_loaded": fields.Datetime.now(),
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Loading Completed"),
                "message": _("Load is ready for shipping."),
                "type": "success",
            },
        }

    def action_ship_load(self):
        """Ship the load"""
        self.ensure_one()
        if self.state != "ready":
            raise UserError(_("Load must be ready to ship."))
        
        self.write({
            "state": "shipped",
            "date_shipped": fields.Datetime.now(),
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Load Shipped"),
                "message": _("Load has been shipped successfully."),
                "type": "success",
            },
        }

    def action_mark_delivered(self):
        """Mark load as delivered"""
        self.ensure_one()
        if self.state != "shipped":
            raise UserError(_("Load must be shipped to mark as delivered."))
        
        self.write({
            "state": "delivered",
            "date_delivered": fields.Datetime.now(),
            "actual_delivery_date": fields.Datetime.now(),
        })
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Load Delivered"),
                "message": _("Load has been delivered successfully."),
                "type": "success",
            },
        }

    def action_mark_sold(self):
        """Mark load as sold"""
        self.ensure_one()
        if self.state != "delivered":
            raise UserError(_("Load must be delivered to mark as sold."))
        
        self.write({"state": "sold"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Load Sold"),
                "message": _("Load has been marked as sold."),
                "type": "success",
            },
        }

    def action_cancel(self):
        """Cancel the load"""
        self.ensure_one()
        if self.state in ["delivered", "sold"]:
            raise UserError(_("Cannot cancel delivered or sold loads."))
        
        self.write({"state": "cancelled"})
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Load Cancelled"),
                "message": _("Load has been cancelled."),
                "type": "warning",
            },
        }

    def action_view_bales(self):
        """View related paper bales"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Paper Bales"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {"default_load_id": self.id},
        }

    def action_create_invoice(self):
        """Create customer invoice for this load"""
        self.ensure_one()
        if not self.customer_id:
            raise UserError(_("Customer must be specified to create invoice."))
        
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_partner_id": self.customer_id.id,
                "default_move_type": "out_invoice",
                "default_ref": self.name,
                "default_invoice_origin": self.name,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("loading_start_time", "loading_end_time")
    def _check_loading_times(self):
        """Ensure loading end time is after start time"""
        for record in self:
            if record.loading_start_time and record.loading_end_time:
                if record.loading_end_time <= record.loading_start_time:
                    raise ValidationError(_("Loading end time must be after start time."))

    @api.constrains("estimated_delivery_date", "date_scheduled")
    def _check_delivery_dates(self):
        """Ensure delivery dates are logical"""
        for record in self:
            if record.date_scheduled and record.estimated_delivery_date:
                if record.estimated_delivery_date <= record.date_scheduled:
                    raise ValidationError(_("Estimated delivery must be after scheduled date."))

    @api.constrains("market_price", "contracted_price")
    def _check_prices(self):
        """Ensure prices are positive"""
        for record in self:
            if record.market_price and record.market_price < 0:
                raise ValidationError(_("Market price must be positive."))
            if record.contracted_price and record.contracted_price < 0:
                raise ValidationError(_("Contracted price must be positive."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model
    def create(self, vals_list):
        """Override create to set defaults"""
        if isinstance(vals_list, dict):
            vals_list = [vals_list]
        
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("load") or _("New Load")
        
        return super().create(vals_list)

    def write(self, vals):
        """Override write to track changes and update totals"""
        # Update modification date
        vals["date_modified"] = fields.Datetime.now()
        
        # Track state changes
        if "state" in vals:
            for record in self:
                old_state = dict(record._fields["state"].selection).get(record.state)
                new_state = dict(record._fields["state"].selection).get(vals["state"])
                record.message_post(
                    body=_("Load status changed from %s to %s") % (old_state, new_state)
                )
        
        return super().write(vals)
