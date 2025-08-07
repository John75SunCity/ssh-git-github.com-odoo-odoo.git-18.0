# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PaperBaleRecycling(models.Model):
    _name = "paper.bale.recycling"
    _description = "Paper Bale Recycling"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="Assigned User", default=lambda self: self.env.user)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
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

    # ============================================================================
    # BALE INFORMATION
    # ============================================================================
    bale_id = fields.Char(string="Bale ID", required=True, index=True, tracking=True)
    bale_weight = fields.Float(string="Bale Weight (lbs)", required=True, tracking=True)
    paper_type = fields.Selection(
        [
            ("mixed", "Mixed Paper"),
            ("white", "White Office Paper"),
            ("newspaper", "Newspaper"),
            ("cardboard", "Cardboard"),
            ("magazine", "Magazine/Glossy"),
            ("confidential", "Confidential Documents"),
        ],
        string="Paper Type",
        required=True,
        default="mixed",
    )

    grade_quality = fields.Selection(
        [
            ("grade_1", "Grade 1 - Highest"),
            ("grade_2", "Grade 2 - High"),
            ("grade_3", "Grade 3 - Standard"),
            ("grade_4", "Grade 4 - Low"),
        ],
        string="Grade Quality",
        default="grade_3",
        tracking=True,
    )

    contamination_level = fields.Float(string="Contamination Level (%)", default=0.0)
    moisture_content = fields.Float(string="Moisture Content (%)", default=0.0)

    # ============================================================================
    # RECYCLING PROCESS
    # ============================================================================
    processing_date = fields.Date(string="Processing Date", tracking=True)
    recycling_facility_id = fields.Many2one(
        "res.partner", string="Recycling Facility", domain=[("is_company", "=", True)]
    )

    collection_date = fields.Date(string="Collection Date", tracking=True)
    transport_method = fields.Selection(
        [
            ("truck", "Truck Transport"),
            ("rail", "Rail Transport"),
            ("barge", "Barge Transport"),
            ("combination", "Combination"),
        ],
        string="Transport Method",
        default="truck",
    )

    processing_status = fields.Selection(
        [
            ("pending", "Pending Processing"),
            ("in_process", "In Process"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
        ],
        string="Processing Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # ENVIRONMENTAL & COMPLIANCE
    # ============================================================================
    carbon_footprint_reduction = fields.Float(string="Carbon Footprint Reduction (tons CO2)")
    water_savings = fields.Float(string="Water Savings (gallons)")
    energy_savings = fields.Float(string="Energy Savings (kWh)")
    landfill_diversion = fields.Float(string="Landfill Diversion (lbs)")

    environmental_certificate = fields.Binary(string="Environmental Certificate")
    recycling_certificate = fields.Binary(string="Recycling Certificate")
    chain_of_custody = fields.Text(string="Chain of Custody Documentation")

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    market_price_per_ton = fields.Monetary(string="Market Price per Ton", currency_field="currency_id")
    total_revenue = fields.Monetary(
        string="Total Revenue",
        currency_field="currency_id",
        compute="_compute_total_revenue",
        store=True,
    )
    processing_cost = fields.Monetary(string="Processing Cost", currency_field="currency_id")
    transport_cost = fields.Monetary(string="Transport Cost", currency_field="currency_id")
    net_profit = fields.Monetary(
        string="Net Profit",
        currency_field="currency_id",
        compute="_compute_net_profit",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    source_paper_bales = fields.Many2many("paper.bale", string="Source Paper Bales")
    shredding_service_ids = fields.One2many(
        "shredding.service", "recycling_bale_id", string="Related Shredding Services"
    )

    # Mail framework fields    @api.depends("bale_weight", "market_price_per_ton")
    def _compute_total_revenue(self):
        for record in self:
            if record.bale_weight and record.market_price_per_ton:
                weight_tons = record.bale_weight / 2000  # Convert lbs to tons
                record.total_revenue = weight_tons * record.market_price_per_ton
            else:
                record.total_revenue = 0.0

    @api.depends("total_revenue", "processing_cost", "transport_cost")
    def _compute_net_profit(self):
        for record in self:
            record.net_profit = record.total_revenue - record.processing_cost - record.transport_cost

    @api.depends("source_paper_bales")
    def _compute_source_bale_count(self):
        for record in self:
            record.source_bale_count = len(record.source_paper_bales)

    source_bale_count = fields.Integer(compute="_compute_source_bale_count", string="Source Bales")

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("bale_id"):
                vals["bale_id"] = self.env["ir.sequence"].next_by_code("paper.bale.recycling") or "PBR/"
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_processing(self):
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active bales can be processed."))
        self.write({"processing_status": "in_process", "processing_date": fields.Date.today()})

    def action_complete_processing(self):
        self.ensure_one()
        if self.processing_status != "in_process":
            raise UserError(_("Only bales in process can be completed."))
        self.write({"processing_status": "completed"})

    def action_reject_bale(self):
        self.ensure_one()
        self.write({"processing_status": "rejected"})

    def action_view_source_bales(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Source Paper Bales",
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.source_paper_bales.ids)],
        }

    def action_generate_certificate(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Generate Environmental Certificate",
            "res_model": "environmental.certificate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_recycling_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def calculate_environmental_impact(self):
        """Calculate environmental impact metrics"""
        self.ensure_one()

        # Standard environmental benefits per ton of recycled paper
        ton_weight = self.bale_weight / 2000

        self.write(
            {
                "carbon_footprint_reduction": ton_weight * 1.0,  # 1 ton CO2 per ton paper
                "water_savings": ton_weight * 7000,  # 7000 gallons per ton
                "energy_savings": ton_weight * 4100,  # 4100 kWh per ton
                "landfill_diversion": self.bale_weight,  # Full weight diverted
            }
        )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("contamination_level", "moisture_content")
    def _check_percentages(self):
        for record in self:
            if record.contamination_level < 0 or record.contamination_level > 100:
                raise ValidationError(_("Contamination level must be between 0 and 100%."))
            if record.moisture_content < 0 or record.moisture_content > 100:
                raise ValidationError(_("Moisture content must be between 0 and 100%."))

    @api.constrains("bale_weight")
    def _check_bale_weight(self):
        for record in self:
            if record.bale_weight <= 0:
                raise ValidationError(_("Bale weight must be greater than zero."))

    @api.constrains("bale_id")
    def _check_bale_id_uniqueness(self):
        for record in self:
            if record.bale_id:
                existing = self.search([("bale_id", "=", record.bale_id), ("id", "!=", record.id)])
                if existing:
                    raise ValidationError(_("Bale ID must be unique."))

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    contamination = fields.Char(string='Contamination', tracking=True)
    mobile_entry = fields.Char(string='Mobile Entry', tracking=True)
    paper_grade = fields.Char(string='Paper Grade', tracking=True)
    production_date = fields.Date(string='Production Date', tracking=True)
    status = fields.Selection([('draft', 'Draft')], string='Status', default='draft', tracking=True)

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_assign_to_load(self):
        """Assign To Load - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign To Load"),
            "res_model": "paper.bale.recycling",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_mark_delivered(self):
        """Mark Delivered - Update field"""
        self.ensure_one()
        self.write({"delivered": True})
        self.message_post(body=_("Mark Delivered"))
        return True
    def action_mark_paid(self):
        """Mark Paid - Update field"""
        self.ensure_one()
        self.write({"paid": True})
        self.message_post(body=_("Mark Paid"))
        return True
    def action_ready_to_ship(self):
        """Ready To Ship - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ready To Ship"),
            "res_model": "paper.bale.recycling",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_ship_bale(self):
        """Ship Bale - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ship Bale"),
            "res_model": "paper.bale.recycling",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_store_bale(self):
        """Store Bale - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Store Bale"),
            "res_model": "paper.bale.recycling",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }