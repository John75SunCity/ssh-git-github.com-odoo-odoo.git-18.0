# -*- coding: utf-8 -*-
"""
Paper Bale Recycling Management Module

This module provides comprehensive management of paper bale recycling operations within the Records Management System.
It implements enterprise-grade tracking of paper bales from collection through processing, with environmental impact
monitoring and NAID compliance integration.

Key Features:
- Complete paper bale lifecycle tracking with weight and quality monitoring
- Environmental impact calculation (carbon footprint, water savings, energy savings)
- Financial tracking with market pricing and cost analysis
- Multi-grade paper type classification with contamination monitoring
- Integration with shredding services and destruction workflows
- Chain of custody documentation for compliance requirements
- Automated certificate generation for environmental compliance

Business Processes:
1. Bale Collection: Track collection from various sources with transport methods
2. Quality Assessment: Monitor contamination levels, moisture content, and grade quality
3. Processing Management: Handle recycling facility assignments and processing status
4. Environmental Monitoring: Calculate environmental benefits and impact metrics
5. Financial Tracking: Monitor market prices, costs, and profit margins
6. Compliance Documentation: Maintain chain of custody and certificate records

Technical Implementation:
- Modern Odoo 18.0 patterns with mail.thread inheritance
- Comprehensive validation with proper field constraints
- Automated sequence generation for bale identification
- Integration with partner management for recycling facilities
- Currency field support for multi-company financial tracking

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

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

    # Partner Relationship
    description = fields.Text(string="Description"),
    sequence = fields.Integer(string="Sequence", default=10),
    active = fields.Boolean(string="Active", default=True),
    company_id = fields.Many2one(
        "res.company",
        string="Company",
    )
        default=lambda self: self.env.company,
        required=True,
        index=True,
    ),
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record",
    )
    ),
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
    )
        tracking=True,
    )

    # ============================================================================
    # BALE INFORMATION
    # ============================================================================
    bale_id = fields.Char(
        string="Bale ID",
    )
        required=True,
        index=True,
        tracking=True,

    help="Unique identifier for the paper bale",

        )
    bale_weight = fields.Float(
        string="Bale Weight (lbs)",
        required=True,
        tracking=True,

    help="Total weight of the bale in pounds",
)

        )
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
    )
        required=True,
        default="mixed",
        tracking=True,
    ),
    grade_quality = fields.Selection(
        [
            ("grade_1", "Grade 1 - Highest"),
            ("grade_2", "Grade 2 - High"),
            ("grade_3", "Grade 3 - Standard"),
            ("grade_4", "Grade 4 - Low"),
        ],
        string="Grade Quality",
    )
        default="grade_3",
        tracking=True,
    ),
    contamination_level = fields.Float(
        string="Contamination Level (%)",
        default=0.0,

        help="Percentage of non-paper contamination",
    )

        )
    moisture_content = fields.Float(
        string="Moisture Content (%)",
    )
        default=0.0,
        help="Moisture percentage in the bale"
    )

    # ============================================================================
    # RECYCLING PROCESS
    # ============================================================================
    processing_date = fields.Date(string="Processing Date", tracking=True),
    recycling_facility_id = fields.Many2one(
        "res.partner",
        string="Recycling Facility",
    )
        domain=[("is_company", "=", True)],
        tracking=True,
    ),
    collection_date = fields.Date(string="Collection Date", tracking=True),
    transport_method = fields.Selection(
        [
            ("truck", "Truck Transport"),
            ("rail", "Rail Transport"),
            ("barge", "Barge Transport"),
            ("combination", "Combination"),
        ],
        string="Transport Method",
        default="truck",
    ),
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
    carbon_footprint_reduction = fields.Float(
        string="Carbon Footprint Reduction (tons CO2)",
    )

        help="Estimated carbon footprint reduction from recycling"

        )
    water_savings = fields.Float(
        string="Water Savings (gallons)", help="Estimated water savings from recycling"
    ),
    energy_savings = fields.Float(
        string="Energy Savings (kWh)", help="Estimated energy savings from recycling"
    ),
    landfill_diversion = fields.Float(
        string="Landfill Diversion (lbs)",
    )

        help="Weight of material diverted from landfill"

        )
    environmental_certificate = fields.Binary(string="Environmental Certificate"),
    recycling_certificate = fields.Binary(string="Recycling Certificate"),
    chain_of_custody = fields.Text(string="Chain of Custody Documentation")

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    ),
    market_price_per_ton = fields.Monetary(
        string="Market Price per Ton", currency_field="currency_id"
    ),
    total_revenue = fields.Monetary(
        string="Total Revenue",
    )
        currency_field="currency_id",
        compute="_compute_total_revenue",)
        store=True,
    ),
    processing_cost = fields.Monetary(
        string="Processing Cost", currency_field="currency_id"
    ),
    transport_cost = fields.Monetary(
        string="Transport Cost", currency_field="currency_id"
    ),
    net_profit = fields.Monetary(
        string="Net Profit",
        currency_field="currency_id",
        compute="_compute_net_profit",)
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    source_paper_bale_ids = fields.Many2many(
        "paper.bale", string="Source Paper Bales"
    ),
    shredding_service_ids = fields.One2many(
        "shredding.service", "recycling_bale_id", string="Related Shredding Services"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    source_bale_count = fields.Integer(
        compute="_compute_source_bale_count",
        string="Source Bales",

        help="Number of source bales used for this recycling batch",

        )

    # Additional status tracking fields
    contamination = fields.Char(string="Contamination Notes", tracking=True),
    mobile_entry = fields.Boolean(string="Mobile Entry", default=False, tracking=True),
    paper_grade = fields.Char(string="Paper Grade Classification", tracking=True),
    production_date = fields.Date(string="Production Date", tracking=True)

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance),
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    ),
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    gross_weight = fields.Float(string='Gross Weight (lbs)', required=True)
    # COMPUTE METHODS
    net_weight = fields.Float(string='Net Weight (lbs)', compute='_compute_net_weight', store=True)
    # ============================================================================
    @api.depends("bale_weight", "market_price_per_ton")
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
            record.net_profit = (
                record.total_revenue - record.processing_cost - record.transport_cost
            )

    @api.depends("source_paper_bales")
    def _compute_source_bale_count(self):
        for record in self:
            record.source_bale_count = len(record.source_paper_bales)

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("bale_id"):
                vals["bale_id"] = (
                    self.env["ir.sequence"].next_by_code("paper.bale.recycling")
                    or "PBR/"
                )
        return super(PaperBaleRecycling, self).create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_processing(self):
        """Start the recycling processing workflow"""

        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active bales can be processed."))
        self.write(
            {"processing_status": "in_process", "processing_date": fields.Date.today()}
        )
        self.message_post(
            body=_("Recycling processing started for bale %s", self.bale_id)
        )

    def action_complete_processing(self):
        """Complete the recycling processing workflow"""

        self.ensure_one()
        if self.processing_status != "in_process":
            raise UserError(_("Only bales in process can be completed."))
        self.write({"processing_status": "completed"})
        self.calculate_environmental_impact()
        self.message_post(
            body=_("Recycling processing completed for bale %s", self.bale_id)
        )

    def action_reject_bale(self):
        """Reject the bale for processing"""

        self.ensure_one()
        self.write({"processing_status": "rejected"})
        self.message_post(
            body=_("Bale %s has been rejected for processing", self.bale_id)
        )

    def action_view_source_bales(self):
        """View source paper bales used in this recycling batch"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Source Paper Bales",
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.source_paper_bales.ids)],
        }

    def action_generate_certificate(self):
        """Generate environmental certificate for this recycling batch"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Generate Environmental Certificate",
            "res_model": "environmental.certificate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_recycling_id": self.id},
        }

    def action_assign_to_load(self):
        """Assign bale to transportation load"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign To Load"),
            "res_model": "transport.load.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    def action_mark_delivered(self):
        """Mark bale as delivered to recycling facility"""

        self.ensure_one()
        self.write({"state": "active"})
        self.message_post(body=_("Bale %s marked as delivered", self.bale_id))
        return True

    def action_mark_paid(self):
        """Mark recycling payment as received"""

        self.ensure_one()
        # This would typically create an account.move entry
    self.message_post(body=_("Payment received for bale %s", self.bale_id))
        return True

    def action_ready_to_ship(self):
        """Mark bale as ready for shipping"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ready To Ship"),
            "res_model": "shipping.preparation.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    def action_ship_bale(self):
        """Process bale shipment to recycling facility"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ship Bale"),
            "res_model": "bale.shipment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    def action_store_bale(self):
        """Store bale in temporary storage before processing"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Store Bale"),
            "res_model": "bale.storage.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def calculate_environmental_impact(self):
        """Calculate environmental impact metrics based on industry standards"""
        self.ensure_one()

        # Standard environmental benefits per ton of recycled paper
        ton_weight = self.bale_weight / 2000

        self.write(
            {
                "carbon_footprint_reduction": ton_weight
                * 1.0,  # 1 ton CO2 per ton paper
                "water_savings": ton_weight * 7000,  # 7000 gallons per ton
                "energy_savings": ton_weight * 4100,  # 4100 kWh per ton
                "landfill_diversion": self.bale_weight,  # Full weight diverted
            }
        )

    def get_recycling_efficiency(self):
        """Calculate recycling efficiency based on contamination and quality"""
        self.ensure_one()

        base_efficiency = 0.85  # 85% base efficiency
        contamination_penalty = (
            self.contamination_level * 0.01
        )  # 1% penalty per % contamination

        grade_bonuses = {
            "grade_1": 0.10,
            "grade_2": 0.05,
            "grade_3": 0.00,
            "grade_4": -0.05,
        }

        grade_bonus = grade_bonuses.get(self.grade_quality, 0.0)
        efficiency = max(0.0, base_efficiency - contamination_penalty + grade_bonus)

        return min(1.0, efficiency)  # Cap at 100%

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("contamination_level", "moisture_content")
    def _check_percentages(self):
        for record in self:
            if record.contamination_level < 0 or record.contamination_level > 100:
                raise ValidationError(
                    _("Contamination level must be between 0 and 100%.")
                )
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
                existing = self.search(
                    [("bale_id", "=", record.bale_id), ("id", "!=", record.id)]
                )
                if existing:
                    raise ValidationError(_("Bale ID must be unique."))

    @api.constrains("market_price_per_ton", "processing_cost", "transport_cost")
    def _check_financial_fields(self):
        for record in self:
            if record.market_price_per_ton < 0:
                raise ValidationError(_("Market price cannot be negative."))
            if record.processing_cost < 0:
                raise ValidationError(_("Processing cost cannot be negative."))
            if record.transport_cost < 0:
                raise ValidationError(_("Transport cost cannot be negative."))
