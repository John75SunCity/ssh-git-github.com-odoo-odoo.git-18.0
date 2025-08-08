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
    active = fields.Boolean(string="Active", default=True, tracking=True)
    description = fields.Text(string="Load Description")
    sequence = fields.Integer(string="Sequence", default=10)

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

    # ============================================================================
    # CAPACITY AND WEIGHT TRACKING
    # ============================================================================
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
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
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
            record.total_costs = (record.transportation_cost or 0.0) + (
                record.fuel_cost or 0.0
            )

    @api.depends("actual_revenue", "total_costs")
    def _compute_net_profit(self):
        for record in self:
            record.net_profit = (record.actual_revenue or 0.0) - (
                record.total_costs or 0.0
            )

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code("load") or "LOAD/"
        return super().create(vals_list)
