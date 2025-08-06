# -*- coding: utf-8 -*-
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

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
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
    # LOAD SPECIFICATIONS
    # ============================================================================
    load_type = fields.Selection(
        [
            ("paper_bales", "Paper Bales"),
            ("mixed_materials", "Mixed Materials"),
            ("cardboard", "Cardboard"),
            ("confidential_destruction", "Confidential Destruction"),
        ],
        string="Load Type",
        required=True,
        default="paper_bales",
    )

    trailer_id = fields.Many2one(
        "fleet.vehicle", string="Trailer", domain=[("vehicle_type", "=", "trailer")]
    )
    driver_id = fields.Many2one(
        "res.partner", string="Driver", domain=[("is_company", "=", False)]
    )

    # Capacity and weight tracking
    max_weight_capacity = fields.Float(
        string="Max Weight Capacity (lbs)", default=80000.0
    )
    current_weight = fields.Float(
        string="Current Weight (lbs)", compute="_compute_current_weight", store=True
    )
    weight_utilization = fields.Float(
        string="Weight Utilization (%)", compute="_compute_weight_utilization"
    )

    # ============================================================================
    # SCHEDULING & TIMING
    # ============================================================================
    date_created = fields.Datetime(
        string="Created Date", default=fields.Datetime.now, tracking=True
    )
    loading_start_date = fields.Datetime(string="Loading Start Date", tracking=True)
    loading_end_date = fields.Datetime(string="Loading End Date", tracking=True)
    scheduled_ship_date = fields.Date(string="Scheduled Ship Date", tracking=True)
    actual_ship_date = fields.Date(string="Actual Ship Date", tracking=True)
    estimated_delivery_date = fields.Date(
        string="Estimated Delivery Date", tracking=True
    )
    actual_delivery_date = fields.Date(string="Actual Delivery Date", tracking=True)

    # ============================================================================
    # DESTINATION & LOGISTICS
    # ============================================================================
    destination_partner_id = fields.Many2one(
        "res.partner", string="Destination", required=True, tracking=True
    )
    pickup_location = fields.Char(string="Pickup Location")
    delivery_address = fields.Text(string="Delivery Address")
    special_delivery_instructions = fields.Text(string="Special Delivery Instructions")

    route_optimization = fields.Boolean(string="Route Optimization", default=False)
    estimated_distance = fields.Float(string="Estimated Distance (miles)")
    estimated_fuel_cost = fields.Float(string="Estimated Fuel Cost")

    # ============================================================================
    # LOAD CONTENTS
    # ============================================================================
    paper_bale_ids = fields.One2many("paper.bale", "load_id", string="Paper Bales")
    total_bales = fields.Integer(string="Total Bales", compute="_compute_total_bales")

    # Content breakdown
    mixed_paper_weight = fields.Float(string="Mixed Paper Weight (lbs)")
    cardboard_weight = fields.Float(string="Cardboard Weight (lbs)")
    white_paper_weight = fields.Float(string="White Paper Weight (lbs)")
    confidential_weight = fields.Float(string="Confidential Weight (lbs)")

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    estimated_revenue = fields.Monetary(
        string="Estimated Revenue", currency_field="currency_id", tracking=True
    )
    actual_revenue = fields.Monetary(
        string="Actual Revenue", currency_field="currency_id", tracking=True
    )
    transportation_cost = fields.Monetary(
        string="Transportation Cost", currency_field="currency_id"
    )
    fuel_cost = fields.Monetary(string="Fuel Cost", currency_field="currency_id")
    total_costs = fields.Monetary(
        string="Total Costs",
        currency_field="currency_id",
        compute="_compute_total_costs",
        store=True,
    )
    net_profit = fields.Monetary(
        string="Net Profit",
        currency_field="currency_id",
        compute="_compute_net_profit",
        store=True,
    )

    # ============================================================================
    # QUALITY & COMPLIANCE
    # ============================================================================
    quality_grade = fields.Selection(
        [
            ("grade_1", "Grade 1 - Premium"),
            ("grade_2", "Grade 2 - Standard"),
            ("grade_3", "Grade 3 - Mixed"),
            ("grade_4", "Grade 4 - Low"),
        ],
        string="Quality Grade",
        default="grade_2",
    )

    contamination_level = fields.Float(string="Contamination Level (%)", default=0.0)
    moisture_content = fields.Float(string="Moisture Content (%)", default=0.0)
    quality_inspection_passed = fields.Boolean(
        string="Quality Inspection Passed", default=True
    )
    inspection_notes = fields.Text(string="Inspection Notes")

    # ============================================================================
    # DOCUMENTATION
    # ============================================================================
    bill_of_lading = fields.Binary(string="Bill of Lading")
    weight_ticket = fields.Binary(string="Weight Ticket")
    quality_certificate = fields.Binary(string="Quality Certificate")
    delivery_receipt = fields.Binary(string="Delivery Receipt")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("paper_bale_ids", "paper_bale_ids.weight")
    def _compute_current_weight(self):
        for record in self:
            record.current_weight = sum(record.paper_bale_ids.mapped("weight"))

    @api.depends("current_weight", "max_weight_capacity")
    def _compute_weight_utilization(self):
        for record in self:
            if record.max_weight_capacity > 0:
                record.weight_utilization = (
                    record.current_weight / record.max_weight_capacity
                ) * 100
            else:
                record.weight_utilization = 0.0

    @api.depends("paper_bale_ids")
    def _compute_total_bales(self):
        for record in self:
            record.total_bales = len(record.paper_bale_ids)

    @api.depends("transportation_cost", "fuel_cost")
    def _compute_total_costs(self):
        for record in self:
            record.total_costs = record.transportation_cost + record.fuel_cost

    @api.depends("actual_revenue", "total_costs")
    def _compute_net_profit(self):
        for record in self:
            record.net_profit = record.actual_revenue - record.total_costs

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("load") or "LOAD/"
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_loading(self):
        self.ensure_one()
        if self.state != "preparing":
            raise UserError(_("Only loads in preparing state can start loading."))
        self.write({"state": "loading", "loading_start_date": fields.Datetime.now()})

    def action_complete_loading(self):
        self.ensure_one()
        if self.state != "loading":
            raise UserError(_("Only loads in loading state can be completed."))
        if not self.paper_bale_ids:
            raise UserError(_("Cannot complete loading without any bales."))
        self.write({"state": "ready", "loading_end_date": fields.Datetime.now()})

    def action_ship(self):
        self.ensure_one()
        if self.state != "ready":
            raise UserError(_("Only ready loads can be shipped."))
        if not self.driver_id:
            raise UserError(_("Please assign a driver before shipping."))
        self.write({"state": "shipped", "actual_ship_date": fields.Date.today()})

    def action_deliver(self):
        self.ensure_one()
        if self.state != "shipped":
            raise UserError(_("Only shipped loads can be delivered."))
        self.write({"state": "delivered", "actual_delivery_date": fields.Date.today()})

    def action_mark_sold(self):
        self.ensure_one()
        if self.state != "delivered":
            raise UserError(_("Only delivered loads can be marked as sold."))
        self.write({"state": "sold"})

    def action_cancel(self):
        self.ensure_one()
        if self.state in ["delivered", "sold"]:
            raise UserError(_("Cannot cancel delivered or sold loads."))
        self.write({"state": "cancelled"})

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_load_summary(self):
        """Return load summary for reporting"""
        self.ensure_one()
        return {
            "load_number": self.name,
            "total_weight": self.current_weight,
            "total_bales": self.total_bales,
            "destination": self.destination_partner_id.name,
            "status": self.state,
            "profit": self.net_profit,
        }

    def check_weight_capacity(self):
        """Check if load exceeds weight capacity"""
        self.ensure_one()
        return self.current_weight <= self.max_weight_capacity

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("current_weight", "max_weight_capacity")
    def _check_weight_capacity(self):
        for record in self:
            if record.current_weight > record.max_weight_capacity:
                raise ValidationError(_("Current weight exceeds maximum capacity."))

    @api.constrains("contamination_level", "moisture_content")
    def _check_quality_percentages(self):
        for record in self:
            if record.contamination_level < 0 or record.contamination_level > 100:
                raise ValidationError(
                    _("Contamination level must be between 0 and 100%.")
                )
            if record.moisture_content < 0 or record.moisture_content > 100:
                raise ValidationError(_("Moisture content must be between 0 and 100%."))

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================\n    estimated_delivery = fields.Char(string='Estimated Delivery', tracking=True)\n    hazmat_required = fields.Boolean(string='Hazmat Required', default=False)\n    load_date = fields.Date(string='Load Date', tracking=True)\n    priority = fields.Selection([('draft', 'Draft')], string='Priority', default='draft', tracking=True)\n    scheduled_departure = fields.Char(string='Scheduled Departure', tracking=True)\n    temperature_controlled = fields.Char(string='Temperature Controlled', tracking=True)\n
    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_prepare_load(self):
        """Prepare Load - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Prepare Load"),
            "res_model": "load",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_ship_load(self):
        """Ship Load - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ship Load"),
            "res_model": "load",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_view_bales(self):
        """View Bales - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Bales"),
            "res_model": "load",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {"default_load_id": self.id},
        }
    def action_view_revenue_report(self):
        """View Revenue Report - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Revenue Report"),
            "res_model": "load",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {"default_load_id": self.id},
        }
    def action_view_weight_tickets(self):
        """View Weight Tickets - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Weight Tickets"),
            "res_model": "load",
            "view_mode": "tree,form",
            "domain": [("load_id", "=", self.id)],
            "context": {"default_load_id": self.id},
        }