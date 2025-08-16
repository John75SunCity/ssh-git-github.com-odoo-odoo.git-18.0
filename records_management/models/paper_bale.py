# -*- coding: utf-8 -*-
"""
Paper Bale Management Module

This module provides comprehensive paper bale management for the Records
Management System. It tracks paper bales from creation through recycling,
including quality control, transportation, and environmental impact tracking.

Key Features:
- Complete paper bale lifecycle management
- Quality control and inspection workflows
- Transportation and logistics tracking
- Environmental impact assessment
- NAID compliance for confidential documents
- Financial tracking and cost management

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from odoo.osv import expression


class PaperBale(models.Model):
    _name = "paper.bale"
    _description = "Paper Bale"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Bale Number",
        required=True,
        tracking=True,
        index=True,
        help="Unique bale identifier",
    )
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
        help="User responsible for this bale",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Active status of the bale record"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering"
    )

    # ============================================================================
    # REFERENCE AND EXTERNAL TRACKING
    # ============================================================================
    reference_number = fields.Char(
        string="Reference Number", help="Internal reference number"
    )
    external_reference = fields.Char(
        string="External Reference", help="External system reference"
    )
    barcode = fields.Char(string="Barcode", help="Barcode for tracking")

    # ============================================================================
    # STATE AND STATUS MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("created", "Created"),
            ("weighed", "Weighed"),
            ("quality_checked", "Quality Checked"),
            ("approved", "Approved"),
            ("loaded", "Loaded on Trailer"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("recycled", "Recycled"),
            ("rejected", "Rejected"),
        ],
        string="Status",
        default="created",
        tracking=True,
        help="Current status of the paper bale",
    )

    # ============================================================================
    # PAPER AND BALE SPECIFICATIONS
    # ============================================================================
    weight = fields.Float(
        string="Weight",
        digits=(10, 2),
        tracking=True,
        help="Weight of the bale",
    )
    weight_unit = fields.Selection(
        [("lb", "Pounds"), ("kg", "Kilograms"), ("ton", "Tons")],
        string="Weight Unit",
        default="lb",
        help="Unit of measurement for weight",
    )
    paper_type = fields.Selection(
        [
            ("mixed", "Mixed Paper"),
            ("office", "Office Paper"),
            ("cardboard", "Cardboard"),
            ("newspaper", "Newspaper"),
            ("magazine", "Magazine"),
            ("shredded", "Shredded Paper"),
            ("confidential", "Confidential Documents"),
        ],
        string="Paper Type",
        tracking=True,
        help="Type of paper in the bale",
    )
    bale_type = fields.Selection(
        [
            ("standard", "Standard Bale"),
            ("compacted", "Compacted Bale"),
            ("loose", "Loose Collection"),
        ],
        string="Bale Type",
        default="standard",
        help="Physical type of bale",
    )
    paper_grade = fields.Selection(
        [
            ("high", "High Grade"),
            ("medium", "Medium Grade"),
            ("low", "Low Grade"),
        ],
        string="Paper Grade",
        help="Quality grade of paper",
    )
    contamination_level = fields.Selection(
        [
            ("none", "No Contamination"),
            ("low", "Low Contamination"),
            ("medium", "Medium Contamination"),
            ("high", "High Contamination"),
        ],
        string="Contamination Level",
        default="none",
        help="Level of contamination in the bale",
    )

    # ============================================================================
    # LOCATION AND LOGISTICS
    # ============================================================================
    pickup_location_id = fields.Many2one(
        "records.location",
        string="Pickup Location",
        help="Location where bale was picked up",
    )
    current_location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        help="Current physical location of the bale",
    )
    destination_location_id = fields.Many2one(
        "records.location",
        string="Destination Location",
        help="Final destination for the bale",
    )
    transportation_method = fields.Selection(
        [("truck", "Truck"), ("rail", "Rail"), ("ship", "Ship")],
        string="Transportation Method",
        default="truck",
        help="Method of transportation",
    )

    # ============================================================================
    # DATES AND SCHEDULING
    # ============================================================================
    creation_date = fields.Date(
        string="Creation Date",
        default=fields.Date.today,
        required=True,
        tracking=True,
        help="Date when bale was created",
    )
    weigh_date = fields.Date(
        string="Weigh Date", help="Date when bale was weighed"
    )
    quality_check_date = fields.Date(
        string="Quality Check Date", help="Date of quality inspection"
    )
    pickup_date = fields.Date(
        string="Pickup Date", help="Date when bale was picked up"
    )
    delivery_date = fields.Date(
        string="Delivery Date", help="Date when bale was delivered"
    )
    recycling_date = fields.Date(
        string="Recycling Date", help="Date when bale was recycled"
    )

    # ============================================================================
    # BUSINESS RELATIONSHIPS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain=[("is_company", "=", True)],
        help="Customer who provided the paper",
    )
    recycling_vendor_id = fields.Many2one(
        "res.partner",
        string="Recycling Vendor",
        domain=[("supplier_rank", ">", 0)],
        help="Vendor who will recycle the paper",
    )
    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        help="Driver assigned for transportation",
    )
    trailer_id = fields.Many2one(
        "records.trailer",
        string="Trailer",
        help="Trailer used for transportation",
    )

    # ============================================================================
    # COMPLIANCE AND SECURITY
    # ============================================================================
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
        help="Security level of documents in bale",
    )
    certificate_of_destruction = fields.Boolean(
        string="Certificate of Destruction",
        default=False,
        help="Whether certificate of destruction is required",
    )
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        default=False,
        tracking=True,
        help="Whether chain of custody has been verified",
    )
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=False,
        help="Whether bale meets NAID standards",
    )

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True,
    )
    sale_price = fields.Monetary(
        string="Sale Price",
        currency_field="currency_id",
        help="Price received for the bale",
    )
    processing_cost = fields.Monetary(
        string="Processing Cost",
        currency_field="currency_id",
        help="Cost to process the bale",
    )
    transportation_cost = fields.Monetary(
        string="Transportation Cost",
        currency_field="currency_id",
        help="Cost of transportation",
    )
    net_value = fields.Monetary(
        string="Net Value",
        currency_field="currency_id",
        compute="_compute_net_value",
        store=True,
        help="Net value after costs",
    )

    # ============================================================================
    # ENVIRONMENTAL AND METRICS
    # ============================================================================
    recycling_category = fields.Selection(
        [
            ("post_consumer", "Post Consumer"),
            ("post_industrial", "Post Industrial"),
            ("mixed", "Mixed"),
        ],
        string="Recycling Category",
        help="Environmental recycling category",
    )
    carbon_footprint = fields.Float(
        string="Carbon Footprint (kg CO2)",
        help="Estimated carbon footprint reduction",
    )
    trees_saved = fields.Float(
        string="Trees Saved",
        compute="_compute_environmental_impact",
        store=True,
        help="Estimated number of trees saved",
    )

    # ============================================================================
    # QUALITY CONTROL
    # ============================================================================
    quality_grade_qc = fields.Char(
        string="Quality Grade", help="Assigned quality grade"
    )
    quality_notes = fields.Text(
        string="Quality Notes", help="Notes from quality inspection"
    )
    moisture_content = fields.Float(
        string="Moisture Content (%)", help="Moisture content percentage"
    )
    density = fields.Float(
        string="Density (kg/m³)",
        compute="_compute_density",
        store=True,
        help="Calculated bale density",
    )

    # ============================================================================
    # EXTENDED TRACKING AND PROCESSING FIELDS
    # ============================================================================
    action_date = fields.Date(
        string="Action Date",
        help="Date of specific action or milestone"
    )

    action_type = fields.Selection([
        ('creation', 'Creation'),
        ('inspection', 'Inspection'),
        ('movement', 'Movement'),
        ('loading', 'Loading'),
        ('shipment', 'Shipment'),
        ('destruction', 'Destruction')
    ], string="Action Type", help="Type of action being tracked")

    bale_number = fields.Char(
        string="Bale Number",
        required=True,
        tracking=True,
        help="Unique identification number for the bale"
    )

    bale_status = fields.Selection([
        ('created', 'Created'),
        ('pending_inspection', 'Pending Inspection'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('shipped', 'Shipped'),
        ('processed', 'Processed')
    ], string="Bale Status", default='created', tracking=True)

    contamination_found = fields.Boolean(
        string="Contamination Found",
        default=False,
        help="Whether contamination was found during inspection"
    )

    contamination_percentage = fields.Float(
        string="Contamination Percentage",
        digits=(5, 2),
        help="Percentage of contamination found"
    )

    customer_name = fields.Char(
        string="Customer Name",
        help="Name of customer whose documents are in this bale"
    )

    destruction_date = fields.Date(
        string="Destruction Date",
        help="Date when original documents were destroyed"
    )

    document_name = fields.Char(
        string="Document Name",
        help="Name or description of source documents"
    )

    document_type = fields.Char(
        string="Document Type",
        help="Type of documents in this bale"
    )

    estimated_value = fields.Monetary(
        string="Estimated Value",
        currency_field="currency_id",
        help="Estimated monetary value of the bale"
    )

    grade_assigned = fields.Char(
        string="Grade Assigned",
        help="Quality grade assigned to the bale"
    )

    inspection_date = fields.Date(
        string="Inspection Date",
        help="Date when quality inspection was performed"
    )

    inspection_type = fields.Selection([
        ('visual', 'Visual Inspection'),
        ('sampling', 'Sample Testing'),
        ('comprehensive', 'Comprehensive Analysis'),
        ('random', 'Random Check')
    ], string="Inspection Type", help="Type of quality inspection performed")

    inspector = fields.Char(
        string="Inspector",
        help="Name of person who performed inspection"
    )

    loaded_by = fields.Char(
        string="Loaded By",
        help="Person who loaded the bale onto transport"
    )

    loaded_on_trailer = fields.Boolean(
        string="Loaded on Trailer",
        default=False,
        help="Whether bale has been loaded onto trailer"
    )

    loading_date = fields.Date(
        string="Loading Date",
        help="Date when bale was loaded for transport"
    )

    loading_notes = fields.Text(
        string="Loading Notes",
        help="Notes from the loading process"
    )

    loading_order = fields.Integer(
        string="Loading Order",
        help="Order in which bale was loaded"
    )

    loading_position = fields.Char(
        string="Loading Position",
        help="Position of bale on transport vehicle"
    )

    market_price_per_lb = fields.Float(
        string="Market Price per Lb",
        digits=(8, 4),
        help="Current market price per pound"
    )

    measured_by = fields.Char(
        string="Measured By",
        help="Person who performed measurements"
    )

    measurement_date = fields.Date(
        string="Measurement Date",
        help="Date when measurements were taken"
    )

    measurement_type = fields.Selection([
        ('initial', 'Initial Measurement'),
        ('pre_loading', 'Pre-Loading'),
        ('final', 'Final Measurement'),
        ('verification', 'Verification')
    ], string="Measurement Type", help="Type of measurement taken")

    moisture_reading = fields.Float(
        string="Moisture Reading",
        digits=(5, 2),
        help="Actual moisture content reading"
    )

    naid_compliance_verified = fields.Boolean(
        string="NAID Compliance Verified",
        default=False,
        help="Whether NAID compliance has been verified"
    )

    passed_inspection = fields.Boolean(
        string="Passed Inspection",
        default=False,
        help="Whether bale passed quality inspection"
    )

    performed_by = fields.Char(
        string="Performed By",
        help="Person who performed the action"
    )

    processing_time = fields.Float(
        string="Processing Time (hours)",
        digits=(8, 2),
        help="Time required for processing"
    )

    quality_grade = fields.Selection([
        ('grade_a', 'Grade A - Premium'),
        ('grade_b', 'Grade B - Standard'),
        ('grade_c', 'Grade C - Lower Grade'),
        ('reject', 'Reject')
    ], string="Quality Grade", help="Assigned quality grade")

    quality_score = fields.Float(
        string="Quality Score",
        digits=(5, 2),
        help="Numerical quality score (0-100)"
    )

    revenue_potential = fields.Monetary(
        string="Revenue Potential",
        currency_field="currency_id",
        help="Potential revenue from sale"
    )

    scale_used = fields.Char(
        string="Scale Used",
        help="Identification of scale used for weighing"
    )

    source_facility = fields.Char(
        string="Source Facility",
        help="Facility where bale was created"
    )

    special_handling = fields.Boolean(
        string="Special Handling Required",
        default=False,
        help="Whether special handling procedures are required"
    )

    trailer_info = fields.Char(
        string="Trailer Information",
        help="Information about transport trailer"
    )

    trailer_load_count = fields.Integer(
        string="Trailer Load Count",
        help="Number of bales on this trailer load"
    )

    variance_from_previous = fields.Float(
        string="Variance from Previous (%)",
        digits=(5, 2),
        help="Percentage variance from previous measurements"
    )

    weighed_by = fields.Char(
        string="Weighed By",
        help="Person who performed weighing"
    )

    weight_contributed = fields.Float(
        string="Weight Contributed (lbs)",
        digits=(8, 2),
        help="Weight contributed to total load"
    )

    weight_efficiency = fields.Float(
        string="Weight Efficiency (%)",
        digits=(5, 2),
        help="Efficiency rating based on weight metrics"
    )

    weight_recorded = fields.Float(
        string="Weight Recorded (lbs)",
        digits=(8, 2),
        help="Officially recorded weight"
    )

    # ============================================================================
    # ENVIRONMENTAL IMPACT EXTENDED FIELDS
    # ============================================================================
    carbon_footprint_saved = fields.Float(
        string="Carbon Footprint Saved (kg CO2)",
        compute='_compute_environmental_impact_extended',
        store=True,
        help="Calculated carbon footprint savings"
    )

    carbon_neutral = fields.Boolean(
        string="Carbon Neutral Process",
        default=False,
        help="Whether the process was carbon neutral"
    )

    energy_saved = fields.Float(
        string="Energy Saved (kWh)",
        compute='_compute_environmental_impact_extended',
        store=True,
        help="Estimated energy savings"
    )

    environmental_certification = fields.Selection([
        ('fsc', 'FSC Certified'),
        ('pefc', 'PEFC Certified'),
        ('sfi', 'SFI Certified'),
        ('none', 'No Certification')
    ], string="Environmental Certification", default='none')

    sustainable_source = fields.Boolean(
        string="Sustainable Source",
        default=True,
        help="Whether source material is sustainably sourced"
    )

    trees_saved_equivalent = fields.Float(
        string="Trees Saved Equivalent",
        compute='_compute_environmental_impact_extended',
        store=True,
        help="Equivalent number of trees saved"
    )

    water_saved = fields.Float(
        string="Water Saved (gallons)",
        compute='_compute_environmental_impact_extended',
        store=True,
        help="Estimated water savings"
    )

    # ============================================================================
    # HISTORY AND AUDIT FIELDS
    # ============================================================================
    loading_history_ids = fields.One2many(
        'paper.bale.loading.history',
        'bale_id',
        string="Loading History",
        help="History of loading events"
    )

    quality_inspection_ids = fields.One2many(
        'paper.bale.quality.inspection',
        'bale_id',
        string="Quality Inspections",
        help="Quality inspection records"
    )

    weight_history_count = fields.Integer(
        string="Weight History Count",
        compute='_compute_weight_history_count',
        help="Number of weight measurements recorded"
    )

    weight_measurement_ids = fields.One2many(
        'paper.bale.weight.measurement',
        'bale_id',
        string="Weight Measurements",
        help="History of weight measurements"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    total_volume = fields.Float(
        string="Total Volume (m³)", help="Estimated volume of the bale"
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
        help="Number of source documents",
    )

    # ============================================================================
    # DESCRIPTIVE FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of the bale"
    )
    notes = fields.Text(
        string="Internal Notes", help="Internal processing notes"
    )
    special_instructions = fields.Text(
        string="Special Instructions", help="Special handling instructions"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    source_document_ids = fields.One2many(
        "paper.bale.source.document",
        "bale_id",
        string="Source Documents",
        help="Documents that were processed into this bale",
    )
    movement_ids = fields.One2many(
        "paper.bale.movement",
        "bale_id",
        string="Movements",
        help="Movement history of the bale",
    )
    inspection_ids = fields.One2many(
        "paper.bale.inspection",
        "bale_id",
        string="Inspections",
        help="Quality inspection records",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
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
        domain=lambda self: [("model", "=", self._name)],
    )

    load_shipment_id = fields.Many2one(
        "paper.load.shipment", string="Load Shipment"
    )
    load_id = fields.Many2one("load", string="Load")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("sale_price", "processing_cost", "transportation_cost")
    def _compute_net_value(self):
        """Calculate net value after costs"""
        for record in self:
            costs = (record.processing_cost or 0) + (record.transportation_cost or 0)
            record.net_value = (record.sale_price or 0) - costs

    @api.depends("weight", "total_volume", "weight_unit")
    def _compute_density(self):
        """Calculate bale density"""
        for record in self:
            if record.weight and record.total_volume > 0:
                weight_kg = record.get_weight_in_kg()
                record.density = weight_kg / record.total_volume
            else:
                record.density = 0.0

    @api.depends("weight", "paper_type", "weight_unit")
    def _compute_environmental_impact(self):
        """Calculate environmental impact metrics"""
        for record in self:
            if record.weight and record.weight > 0:
                # Rough calculation: 17 trees per ton of paper
                weight_tons = record.weight
                if record.weight_unit == "lb":
                    weight_tons = record.weight / 2204.62
                elif record.weight_unit == "kg":
                    weight_tons = record.weight / 1000
                record.trees_saved = weight_tons * 17
            else:
                record.trees_saved = 0.0

    @api.depends("source_document_ids")
    def _compute_document_count(self):
        """Count source documents"""
        for record in self:
            record.document_count = len(record.source_document_ids)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and initial state"""
        for vals in vals_list:
            if not vals.get("name") or vals.get("name") == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("paper.bale") or "BALE-NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write for state change tracking"""
        if "state" in vals:
            for record in self:
                old_state = record.state
                new_state = vals["state"]
                if old_state != new_state:
                    record.message_post(
                        body=_(
                            "State changed from %s to %s", old_state, new_state
                        )
                    )
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of shipped bales"""
        for record in self:
            if record.state in ["shipped", "delivered", "recycled"]:
                raise UserError(
                    _(
                        "Cannot delete bale %s in state %s",
                        record.name,
                        record.state,
                    )
                )
        return super().unlink()

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_weigh_bale(self):
        """Weigh the bale"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weigh Bale"),
            "res_model": "paper.bale.weigh.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    def action_quality_inspection(self):
        """Perform quality inspection"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Inspection"),
            "res_model": "paper.bale.inspection.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_bale_id": self.id},
        }

    def action_load_on_trailer(self):
        """Load bale on trailer"""
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Only approved bales can be loaded"))
        self.write({"state": "loaded", "pickup_date": fields.Date.today()})
        self.message_post(body=_("Bale loaded on trailer"))

    def action_ship_bale(self):
        """Ship the bale"""
        self.ensure_one()
        if self.state != "loaded":
            raise UserError(_("Only loaded bales can be shipped"))
        self.write({"state": "shipped"})
        self.message_post(body=_("Bale shipped"))

    def action_confirm_delivery(self):
        """Confirm bale delivery"""
        self.ensure_one()
        if self.state != "shipped":
            raise UserError(_("Only shipped bales can be delivered"))
        self.write(
            {"state": "delivered", "delivery_date": fields.Date.today()}
        )
        self.message_post(body=_("Bale delivery confirmed"))

    def action_mark_recycled(self):
        """Mark bale as recycled"""
        self.ensure_one()
        if self.state != "delivered":
            raise UserError(_("Only delivered bales can be marked as recycled"))
        self.write(
            {"state": "recycled", "recycling_date": fields.Date.today()}
        )
        self.message_post(body=_("Bale marked as recycled"))

    def action_reject_bale(self):
        """Reject the bale"""
        self.ensure_one()
        self.write({"state": "rejected"})
        self.message_post(body=_("Bale rejected"))

    def action_print_label(self):
        """Print bale label"""
        self.ensure_one()
        return self.env.ref(
            "records_management.action_report_bale_label"
        ).report_action(self)

    def action_view_source_documents(self):
        """View source documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Source Documents"),
            "res_model": "paper.bale.source.document",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }

    def action_view_movements(self):
        """View bale movements"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Bale Movements"),
            "res_model": "paper.bale.movement",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }

    def action_view_inspections(self):
        """View quality inspections"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Inspections"),
            "res_model": "paper.bale.inspection",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def create_movement_record(
        self, from_location_id, to_location_id, movement_type="transfer"
    ):
        """Create movement record"""
        self.ensure_one()
        return self.env["paper.bale.movement"].create(
            {
                "bale_id": self.id,
                "from_location_id": from_location_id,
                "to_location_id": to_location_id,
                "movement_type": movement_type,
                "movement_date": fields.Datetime.now(),
                "user_id": self.env.user.id,
            }
        )

    def get_weight_in_kg(self):
        """Get weight converted to kilograms"""
        self.ensure_one()
        if not self.weight:
            return 0.0
        if self.weight_unit == "kg":
            return self.weight
        elif self.weight_unit == "lb":
            return self.weight * 0.453592
        elif self.weight_unit == "ton":
            return self.weight * 1000
        return self.weight

    def calculate_recycling_value(self):
        """Calculate estimated recycling value"""
        self.ensure_one()
        rates = {
            "office": 0.15,
            "cardboard": 0.12,
            "newspaper": 0.08,
            "magazine": 0.10,
            "mixed": 0.06,
            "shredded": 0.04,
            "confidential": 0.05,
        }
        weight_kg = self.get_weight_in_kg()
        base_rate = rates.get(self.paper_type, 0.05)
        quality_multipliers = {"high": 1.2, "medium": 1.0, "low": 0.8}
        quality_mult = quality_multipliers.get(self.paper_grade, 1.0)
        contamination_multipliers = {
            "none": 1.0,
            "low": 0.9,
            "medium": 0.7,
            "high": 0.5,
        }
        contamination_mult = contamination_multipliers.get(
            self.contamination_level, 1.0
        )
        return weight_kg * base_rate * quality_mult * contamination_mult

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("weight")
    def _check_weight(self):
        """Validate weight is positive"""
        for record in self:
            if record.weight and record.weight <= 0:
                raise ValidationError(_("Weight must be positive"))

    @api.constrains("pickup_date", "delivery_date")
    def _check_dates(self):
        """Validate date sequence"""
        for record in self:
            if record.pickup_date and record.delivery_date:
                if record.pickup_date > record.delivery_date:
                    raise ValidationError(
                        _("Pickup date cannot be after delivery date")
                    )

    @api.constrains("moisture_content")
    def _check_moisture_content(self):
        """Validate moisture content percentage"""
        for record in self:
            if record.moisture_content and (
                record.moisture_content < 0 or record.moisture_content > 100
            ):
                raise ValidationError(
                    _("Moisture content must be between 0 and 100 percent")
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.paper_type:
                paper_type_label = dict(
                    record._fields["paper_type"].selection
                ).get(record.paper_type, "")
                name = _("%s (%s)", record.name, paper_type_label)
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(
        self, name, args=None, operator="ilike", limit=100, name_get_uid=None
    ):
        """Enhanced search by name, reference, barcode, or paper type"""
        args = list(args or [])

        if name:
            # Search in multiple fields: name, reference_number, barcode, external_reference
            domain = [
                "|",
                "|",
                "|",
                ("name", operator, name),
                ("reference_number", operator, name),
                ("barcode", operator, name),
                ("external_reference", operator, name),
            ]
            return self._search(
                expression.AND([domain, args]),
                limit=limit,
                access_rights_uid=name_get_uid,
            )

        return super()._name_search(name, args, operator, limit, name_get_uid)
