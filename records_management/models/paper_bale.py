# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError


class PaperBale(models.Model):
    _name = "paper.bale"
    _description = "Paper Bale"
    _inherit = ["mail.thread", "mail.activity.mixin"]

    name = fields.Char(string="Bale Number", required=True, tracking=True)
    weight = fields.Float(string="Weight (kg)")
    creation_date = fields.Date(string="Creation Date", default=fields.Date.today)
    load_id = fields.Many2one("load", string="Load")
    recycling_facility = fields.Char(string="Recycling Facility")
    state = fields.Selection(
        [
            ("created", "Created"),
            ("shipped", "Shipped"),
            ("recycled", "Recycled"),
            ("rejected", "Rejected/Sent to Trash"),
        ],
        default="created",
        tracking=True,
    )

    # Essential Paper Bale Fields (from view analysis)
    bale_number = fields.Char(
        string="Bale Number", required=True, tracking=True
    )  # Alternative to name
    bale_status = fields.Selection(
        [
            ("created", "Created"),
            ("quality_checked", "Quality Checked"),
            ("loaded", "Loaded on Trailer"),
            ("shipped", "Shipped"),
            ("delivered", "Delivered"),
            ("recycled", "Recycled"),
            ("rejected", "Rejected/Sent to Trash"),
        ],
        string="Bale Status",
        default="created",
        tracking=True,
    )

    loaded_on_trailer = fields.Boolean(
        string="Loaded on Trailer", default=False, tracking=True
    )

    # Physical Properties
    weight_lbs = fields.Float(string="Weight (lbs)", digits=(10, 2))
    dimensions = fields.Char(string="Dimensions (L x W x H)")
    density = fields.Float(string="Density", digits=(8, 2), compute="_compute_density")

    # Composition and Quality
    paper_type = fields.Selection(
        [
            ("mixed_office", "Mixed Office Paper"),
            ("white_ledger", "White Ledger"),
            ("newspaper", "Newspaper"),
            ("cardboard", "Cardboard/OCC"),
            ("magazines", "Magazines"),
            ("mixed_paper", "Mixed Paper"),
            ("non_paper", "Non-Paper Material (Trash)"),
        ],
        string="Material Type",
        required=True,
    )

    contamination_level = fields.Selection(
        [
            ("none", "No Contamination"),
            ("low", "Low (<2%)"),
            ("medium", "Medium (2-5%)"),
            ("high", "High (>5%)"),
        ],
        string="Contamination Level",
        default="none",
    )

    moisture_content = fields.Float(string="Moisture Content (%)", digits=(5, 2))

    # Rejection tracking
    is_rejected = fields.Boolean(string="Is Rejected", default=False, tracking=True)
    rejection_reason = fields.Text(string="Rejection Reason")
    rejection_date = fields.Date(string="Rejection Date")

    # Logistics and Shipping
    trailer_id = fields.Many2one("fleet.vehicle", string="Trailer")
    load_date = fields.Date(string="Load Date")
    shipping_date = fields.Date(string="Shipping Date")
    delivery_date = fields.Date(string="Delivery Date")

    # Financial (excluded from calculations if rejected)
    market_value = fields.Monetary(string="Market Value", currency_field="currency_id")
    sale_price = fields.Monetary(string="Sale Price", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Documentation
    photos_taken = fields.Boolean(string="Photos Taken", default=False)
    weight_ticket_number = fields.Char(string="Weight Ticket Number")
    quality_certificate = fields.Boolean(string="Quality Certificate", default=False)

    # Environmental (excluded from calculations if rejected)
    carbon_footprint_saved = fields.Float(
        string="Carbon Footprint Saved (kg CO2)", digits=(10, 2)
    )
    trees_saved = fields.Float(
        string="Trees Saved", digits=(8, 2), compute="_compute_environmental_impact"
    )
    water_saved = fields.Float(
        string="Water Saved (gallons)",
        digits=(10, 2),
        compute="_compute_environmental_impact",
    )

    # Production Details
    production_date = fields.Date(string="Production Date")
    production_facility = fields.Char(string="Production Facility")
    operator_id = fields.Many2one("res.users", string="Operator")

    # Tracking and Chain of Custody
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )
    source_containers = fields.Text(string="Source Containers")
    destruction_certificate_ids = fields.Many2many(
        "destruction.certificate", string="Related Destruction Certificates"
    )

    # Quality Control
    quality_check_date = fields.Date(string="Quality Check Date")
    quality_checked_by = fields.Many2one("res.users", string="Quality Checked By")
    quality_notes = fields.Text(string="Quality Notes")

    # Customer and Business
    customer_id = fields.Many2one("res.partner", string="Customer")
    service_location = fields.Char(string="Service Location")

    # Related Records
    paper_bale_recycling_id = fields.Many2one(
        "paper.bale.recycling", string="Recycling Record"
    )
    load_shipment_id = fields.Many2one("paper.load.shipment", string="Load Shipment")

    @api.depends("weight_lbs", "dimensions")
    def _compute_density(self):
        """Compute density of the bale"""
        for record in self:
            if record.weight_lbs and record.dimensions:
                # Simple density calculation - would need actual volume calculation
                record.density = record.weight_lbs / 100  # Placeholder calculation
            else:
                record.density = 0

    @api.depends("weight_lbs", "paper_type", "is_rejected")
    def _compute_environmental_impact(self):
        """Compute environmental impact metrics (excluded if rejected)"""
        for record in self:
            if (
                record.weight_lbs
                and not record.is_rejected
                and record.paper_type != "non_paper"
            ):
                # Standard environmental impact calculations for recycled paper
                weight_tons = record.weight_lbs / 2000
                record.trees_saved = weight_tons * 17  # Approximately 17 trees per ton
                record.water_saved = (
                    weight_tons * 7000
                )  # Approximately 7000 gallons per ton
            else:
                record.trees_saved = 0
                record.water_saved = 0

    @api.onchange("paper_type")
    def _onchange_paper_type(self):
        """Auto-mark non-paper materials for rejection"""
        if self.paper_type == "non_paper":
            self.is_rejected = True
            self.state = "rejected"
            self.bale_status = "rejected"
            self.rejection_reason = "Non-paper material - sent to trash"
            self.rejection_date = fields.Date.today()

    bale_type = fields.Selection(
        [
            ("mixed", "Mixed Paper"),
            ("cardboard", "Cardboard"),
            ("newspaper", "Newspaper"),
            ("office", "Office Paper"),
        ],
        string="Bale Type",
        default="mixed",
    )
    storage_location = fields.Char(string="Storage Location")
    trailer_id = fields.Many2one("records.vehicle", string="Trailer")
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Bale Manager", default=lambda self: self.env.user
    )
    active = fields.Boolean(string="Active", default=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    pickup_date = fields.Date(string='Pickup Date')
    price_per_ton = fields.Monetary(string='Price per Ton', currency_field='currency_id')
    sequence = fields.Integer(string='Sequence', default=10)
    notes = fields.Text(string='Notes')
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')
    # === COMPREHENSIVE MISSING FIELDS ===
    workflow_state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Workflow State', default='draft')
    next_action_date = fields.Date(string='Next Action Date')
    deadline_date = fields.Date(string='Deadline')
    completion_date = fields.Datetime(string='Completion Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    assigned_team_id = fields.Many2one('hr.department', string='Assigned Team')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_score = fields.Float(string='Quality Score', digits=(3, 2))
    validation_required = fields.Boolean(string='Validation Required')
    validated_by_id = fields.Many2one('res.users', string='Validated By')
    validation_date = fields.Datetime(string='Validation Date')
    reference_number = fields.Char(string='Reference Number')
    external_reference = fields.Char(string='External Reference')
    documentation_complete = fields.Boolean(string='Documentation Complete')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments')
    performance_score = fields.Float(string='Performance Score', digits=(5, 2))
    efficiency_rating = fields.Selection([('poor', 'Poor'), ('fair', 'Fair'), ('good', 'Good'), ('excellent', 'Excellent')], string='Efficiency Rating')
    last_review_date = fields.Date(string='Last Review Date')
    next_review_date = fields.Date(string='Next Review Date')



    # =============================================================================
    # PAPER BALE ACTION METHODS
    # =============================================================================

    def action_reject_bale(self):
        """Reject bale and send to trash"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Reject Bale",
            "res_model": "paper.bale",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "form_view_initial_mode": "edit",
                "default_is_rejected": True,
                "default_state": "rejected",
                "default_bale_status": "rejected",
                "default_rejection_date": fields.Date.today(),
            },
        }

    def action_unreject_bale(self):
        """Unreject a bale if it was mistakenly rejected"""
        self.ensure_one()
        if self.is_rejected:
            self.write(
                {
                    "is_rejected": False,
                    "state": "created",
                    "bale_status": "created",
                    "rejection_reason": False,
                    "rejection_date": False,
                }
            )
            self.message_post(
                body="Bale has been unrejected and returned to active status."
            )
        return True

    def action_load_trailer(self):
        """Load bale onto trailer."""
        self.ensure_one()
        if self.is_rejected:
            raise UserError("Cannot load rejected bales onto trailers.")

        return {
            "type": "ir.actions.act_window",
            "name": "Select Trailer",
            "res_model": "records.vehicle",
            "view_mode": "tree",
            "domain": [("vehicle_type", "=", "trailer"), ("state", "=", "available")],
            "context": {
                "default_bale_id": self.id,
                "search_default_available": 1,
            },
        }

    def action_move_to_storage(self):
        """Move bale to storage location."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Move to Storage",
            "res_model": "stock.picking",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_picking_type_id": self.env.ref(
                    "stock.picking_type_internal"
                ).id,
                "default_origin": self.name,
                "default_note": f"Moving bale {self.name} to storage",
            },
        }

    def action_print_label(self):
        """Print bale identification label."""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.paper_bale_label_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_quality_inspection(self):
        """Perform quality inspection of bale."""
        self.ensure_one()
        if self.is_rejected:
            raise UserError("Cannot perform quality inspection on rejected bales.")

        # Create quality check activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Quality Inspection: {self.name}",
            note="Perform comprehensive quality inspection including contamination check and moisture content assessment.",
            user_id=self.user_id.id,
        )
        self.message_post(body="Quality inspection scheduled.")
        return True

    def action_view_inspection_details(self):
        """View quality inspection details."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Inspection Details",
            "res_model": "quality.check",
            "view_mode": "tree,form",
            "domain": [("product_id.name", "ilike", self.name)],
            "context": {
                "search_default_product_id": self.name,
            },
        }

    def action_view_source_documents(self):
        """View source documents that contributed to this bale."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Source Documents",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {
                "default_bale_id": self.id,
                "search_default_bale_id": self.id,
            },
        }

    def action_view_trailer_info(self):
        """View trailer information for this bale."""
        self.ensure_one()
        if not self.trailer_id:
            raise UserError("No trailer assigned to this bale.")

        return {
            "type": "ir.actions.act_window",
            "name": "Trailer Information",
            "res_model": "records.vehicle",
            "res_id": self.trailer_id.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_weight_history(self):
        """View weight measurement history."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Weight History",
            "res_model": "stock.quant",
            "view_mode": "tree,form",
            "domain": [("product_id.name", "ilike", self.name)],
            "context": {
                "search_default_product_id": self.name,
                "group_by": "in_date",
            },
        }

    def action_weigh_bale(self):
        """Record bale weight measurement."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Weigh Bale",
            "res_model": "paper.bale",
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_weight": self.weight,
                "focus_field": "weight",
            },
        }

    @api.model
    def get_active_bales_total_weight(self):
        """Get total weight of non-rejected bales"""
        active_bales = self.search([("is_rejected", "=", False)])
        return sum(active_bales.mapped("weight_lbs"))

    @api.model
    def get_recyclable_value_total(self):
        """Get total market value of non-rejected bales"""
        active_bales = self.search([("is_rejected", "=", False)])
        return sum(active_bales.mapped("market_value"))

    @api.model
    def get_environmental_impact_totals(self):
        """Get environmental impact totals (excluding rejected bales)"""
        active_bales = self.search([("is_rejected", "=", False)])
        return {
            "total_trees_saved": sum(active_bales.mapped("trees_saved")),
            "total_water_saved": sum(active_bales.mapped("water_saved")),
            "total_carbon_saved": sum(active_bales.mapped("carbon_footprint_saved")),
        }
