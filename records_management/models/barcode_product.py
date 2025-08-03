# -*- coding: utf-8 -*-
"""
Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BarcodeProduct(models.Model):
    """
    Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅
    """

    _name = "barcode.product"
    _description = (
        "Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅"
    )
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Essential Barcode Product Fields (from view analysis)
    product_category = fields.Selection(
        [
            ("container", "Container"),
            ("bin", "Shred Bin"),
            ("folder", "File Folder"),
            ("location", "Location Tag"),
        ],
        string="Product Category",
        required=True,
    )

    barcode_pattern = fields.Char(
        string="Barcode Pattern", help="Pattern for barcode generation"
    )
    barcode_length = fields.Integer(string="Barcode Length", default=10)
    barcode = fields.Char(string="Barcode", tracking=True)

    # Pricing Fields
    storage_rate = fields.Monetary(string="Storage Rate", currency_field="currency_id")
    shred_rate = fields.Monetary(string="Shredding Rate", currency_field="currency_id")
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate", currency_field="currency_id"
    )
    scanning_rate = fields.Monetary(
        string="Scanning Rate", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Physical Specifications
    box_size = fields.Selection(
        [
            ("letter", "Letter Size"),
            ("legal", "Legal Size"),
            ("banker", "Banker Box"),
            ("archive", "Archive Box"),
            ("custom", "Custom Size"),
        ],
        string="Box Size",
    )

    capacity = fields.Float(string="Storage Capacity (cubic feet)", digits=(10, 2))
    weight_limit = fields.Float(string="Weight Limit (lbs)", digits=(10, 2))
    dimensions = fields.Char(string="Dimensions (L x W x H)")

    # Business Logic Fields
    auto_generate = fields.Boolean(string="Auto Generate Barcode", default=True)
    allowed_characters = fields.Char(string="Allowed Characters", default="0123456789")
    access_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
            ("permanent", "Permanent Storage"),
        ],
        string="Access Frequency",
        default="monthly",
    )

    # === COMPREHENSIVE BARCODE PRODUCT FIELDS ===

    # Enhanced Product Details
    product_code = fields.Char(string="Product Code", tracking=True)
    material_type = fields.Selection(
        [
            ("cardboard", "Cardboard"),
            ("plastic", "Plastic"),
            ("metal", "Metal"),
            ("hybrid", "Hybrid Material"),
        ],
        string="Material Type",
        default="cardboard",
    )
    color = fields.Selection(
        [
            ("brown", "Brown"),
            ("white", "White"),
            ("blue", "Blue"),
            ("green", "Green"),
            ("custom", "Custom Color"),
        ],
        string="Color",
        default="brown",
    )

    # Enhanced Barcode Configuration
    barcode_prefix = fields.Char(string="Barcode Prefix", size=5)
    barcode_suffix = fields.Char(string="Barcode Suffix", size=5)
    check_digit_required = fields.Boolean(string="Check Digit Required", default=True)

    # Pricing Enhancements
    setup_fee = fields.Monetary(string="Setup Fee", currency_field="currency_id")
    rush_service_rate = fields.Monetary(
        string="Rush Service Rate", currency_field="currency_id"
    )
    volume_discount_threshold = fields.Integer(
        string="Volume Discount Threshold", default=100
    )
    volume_discount_rate = fields.Float(
        string="Volume Discount Rate (%)", digits=(5, 2)
    )

    # Analytics and Statistics
    monthly_volume = fields.Integer(
        string="Monthly Volume", compute="_compute_analytics", store=True
    )
    monthly_revenue = fields.Monetary(
        string="Monthly Revenue",
        compute="_compute_analytics",
        store=True,
        currency_field="currency_id",
    )
    average_storage_duration = fields.Float(
        string="Average Storage Duration (days)",
        compute="_compute_analytics",
        store=True,
    )
    utilization_rate = fields.Float(
        string="Utilization Rate (%)", compute="_compute_analytics", store=True
    )
    profit_margin = fields.Float(
        string="Profit Margin (%)", compute="_compute_analytics", store=True
    )

    # Count Fields for Stat Buttons
    storage_box_count = fields.Integer(
        string="Storage Box Count", compute="_compute_counts", store=True
    )
    shred_bin_count = fields.Integer(
        string="Shred Bin Count", compute="_compute_counts", store=True
    )

    # Storage Box Specific Configuration
    file_capacity = fields.Integer(
        string="File Capacity", help="Number of files that can be stored"
    )
    document_types_supported = fields.Text(string="Document Types Supported")
    climate_controlled = fields.Boolean(string="Climate Controlled", default=False)
    fire_protection = fields.Boolean(string="Fire Protection", default=True)
    security_level = fields.Selection(
        [
            ("standard", "Standard Security"),
            ("enhanced", "Enhanced Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Security Level",
        default="standard",
    )

    # Shred Bin Specific Configuration
    shred_capacity = fields.Float(string="Shred Capacity (lbs)", digits=(10, 2))
    max_document_size = fields.Selection(
        [
            ("letter", "Letter Size"),
            ("legal", "Legal Size"),
            ("ledger", "Ledger Size"),
            ("any", "Any Size"),
        ],
        string="Max Document Size",
        default="legal",
    )
    destruction_method = fields.Selection(
        [
            ("strip_cut", "Strip Cut"),
            ("cross_cut", "Cross Cut"),
            ("micro_cut", "Micro Cut"),
            ("pulverize", "Pulverize"),
        ],
        string="Destruction Method",
        default="cross_cut",
    )
    security_grade = fields.Selection(
        [
            ("grade_1", "Grade 1 - General Use"),
            ("grade_2", "Grade 2 - Internal Use"),
            ("grade_3", "Grade 3 - Confidential"),
            ("grade_4", "Grade 4 - Secret"),
            ("grade_5", "Grade 5 - Top Secret"),
        ],
        string="Security Grade",
        default="grade_3",
    )

    # Quality Control
    quality_standards = fields.Text(string="Quality Standards")
    inspection_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Inspection Frequency",
        default="monthly",
    )
    last_inspection_date = fields.Date(string="Last Inspection Date")
    next_inspection_date = fields.Date(
        string="Next Inspection Date", compute="_compute_next_inspection", store=True
    )

    # Environmental and Compliance
    recyclable = fields.Boolean(string="Recyclable", default=True)
    eco_friendly = fields.Boolean(string="Eco-Friendly", default=False)
    compliance_certifications = fields.Text(string="Compliance Certifications")
    environmental_impact_score = fields.Float(
        string="Environmental Impact Score", digits=(3, 1)
    )

    # Inventory Management
    current_stock = fields.Integer(string="Current Stock", default=0)
    minimum_stock = fields.Integer(string="Minimum Stock", default=10)
    maximum_stock = fields.Integer(string="Maximum Stock", default=1000)
    reorder_point = fields.Integer(string="Reorder Point", default=50)
    lead_time_days = fields.Integer(string="Lead Time (Days)", default=7)

    # Supplier Information
    supplier_id = fields.Many2one(
        "res.partner", string="Primary Supplier", domain=[("is_company", "=", True)]
    )
    supplier_product_code = fields.Char(string="Supplier Product Code")
    supplier_price = fields.Monetary(
        string="Supplier Price", currency_field="currency_id"
    )
    last_purchase_date = fields.Date(string="Last Purchase Date")

    # Customer Preferences
    popular_with_customers = fields.Boolean(
        string="Popular with Customers", default=False
    )
    customer_rating = fields.Float(string="Customer Rating", digits=(2, 1))
    customer_feedback = fields.Text(string="Customer Feedback")

    # Technology Integration
    rfid_enabled = fields.Boolean(string="RFID Enabled", default=False)
    gps_tracking = fields.Boolean(string="GPS Tracking", default=False)
    smart_sensors = fields.Boolean(string="Smart Sensors", default=False)
    iot_integration = fields.Boolean(string="IoT Integration", default=False)

    # Operational Efficiency
    setup_time_minutes = fields.Integer(string="Setup Time (Minutes)", default=5)
    processing_time_minutes = fields.Integer(
        string="Processing Time (Minutes)", default=2
    )
    efficiency_rating = fields.Selection(
        [
            ("low", "Low Efficiency"),
            ("medium", "Medium Efficiency"),
            ("high", "High Efficiency"),
            ("maximum", "Maximum Efficiency"),
        ],
        string="Efficiency Rating",
        default="medium",
    )

    # Cost Analysis
    manufacturing_cost = fields.Monetary(
        string="Manufacturing Cost", currency_field="currency_id"
    )
    shipping_cost = fields.Monetary(
        string="Shipping Cost", currency_field="currency_id"
    )
    handling_cost = fields.Monetary(
        string="Handling Cost", currency_field="currency_id"
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True,
        currency_field="currency_id",
    )

    # Performance Metrics
    defect_rate = fields.Float(string="Defect Rate (%)", digits=(5, 2))
    return_rate = fields.Float(string="Return Rate (%)", digits=(5, 2))
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )

    # Competitive Analysis
    competitor_products = fields.Text(string="Competitor Products")
    market_position = fields.Selection(
        [
            ("premium", "Premium"),
            ("standard", "Standard"),
            ("economy", "Economy"),
            ("budget", "Budget"),
        ],
        string="Market Position",
        default="standard",
    )

    # Lifecycle Management
    product_lifecycle_stage = fields.Selection(
        [
            ("development", "Development"),
            ("introduction", "Introduction"),
            ("growth", "Growth"),
            ("maturity", "Maturity"),
            ("decline", "Decline"),
            ("discontinued", "Discontinued"),
        ],
        string="Product Lifecycle Stage",
        default="introduction",
    )
    launch_date = fields.Date(string="Launch Date")
    discontinue_date = fields.Date(string="Discontinue Date")

    # Regulatory and Legal
    regulatory_approvals = fields.Text(string="Regulatory Approvals")
    safety_certifications = fields.Text(string="Safety Certifications")
    patent_numbers = fields.Text(string="Patent Numbers")
    trademark_info = fields.Text(string="Trademark Information")

    # Training and Documentation
    training_required = fields.Boolean(string="Training Required", default=False)
    training_duration_hours = fields.Float(string="Training Duration (Hours)")
    documentation_available = fields.Boolean(
        string="Documentation Available", default=True
    )
    user_manual_url = fields.Url(string="User Manual URL")

    # Warranty and Support
    warranty_period_months = fields.Integer(
        string="Warranty Period (Months)", default=12
    )
    support_level = fields.Selection(
        [
            ("basic", "Basic Support"),
            ("standard", "Standard Support"),
            ("premium", "Premium Support"),
            ("enterprise", "Enterprise Support"),
        ],
        string="Support Level",
        default="standard",
    )

    # Relationships
    related_products = fields.Many2many(
        "barcode.product",
        "product_related_rel",
        "product_id",
        "related_id",
        string="Related Products",
    )
    accessory_products = fields.Many2many(
        "barcode.product",
        "product_accessory_rel",
        "product_id",
        "accessory_id",
        string="Accessory Products",
    )

    # Tracking and Analytics
    average_storage_duration = fields.Float(
        string="Average Storage Duration (days)", compute="_compute_analytics"
    )
    usage_count = fields.Integer(string="Usage Count", default=0)
    last_used_date = fields.Date(string="Last Used Date")

    # Service Configuration
    billing_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")],
        string="Billing Frequency",
        default="monthly",
    )

    service_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("enterprise", "Enterprise"),
        ],
        string="Service Level",
        default="standard",
    )

    # Compliance and Security
    destruction_required = fields.Boolean(string="Destruction Required", default=False)
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)

    # Related Records
    container_ids = fields.One2many(
        "records.container", "product_id", string="Associated Containers"
    )
    document_type_ids = fields.Many2many(
        "records.document.type", string="Allowed Document Types"
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    @api.depends("container_ids", "usage_count", "last_used_date")
    def _compute_analytics(self):
        """Compute analytics for storage duration"""
        for record in self:
            if record.container_ids:
                # Calculate average storage duration from containers
                durations = []
                for container in record.container_ids:
                    if container.created_date and container.last_activity_date:
                        duration = (
                            container.last_activity_date - container.created_date
                        ).days
                        durations.append(duration)

                record.average_storage_duration = (
                    sum(durations) / len(durations) if durations else 0
                )
            else:
                record.average_storage_duration = 0

            # Calculate monthly volume and revenue
            record.monthly_volume = len(
                record.container_ids.filtered(
                    lambda c: c.create_date
                    and c.create_date >= fields.Date.add(fields.Date.today(), days=-30)
                )
            )
            record.monthly_revenue = record.monthly_volume * (record.storage_rate or 0)

            # Calculate utilization rate (percentage of capacity used)
            if record.capacity and record.monthly_volume:
                record.utilization_rate = min(
                    (record.monthly_volume / record.capacity) * 100, 100
                )
            else:
                record.utilization_rate = 0

            # Calculate profit margin
            if record.storage_rate and record.total_cost:
                record.profit_margin = (
                    (record.storage_rate - record.total_cost) / record.storage_rate
                ) * 100
            else:
                record.profit_margin = 0

    @api.depends("product_category")
    def _compute_counts(self):
        """Compute counts for stat buttons."""
        for record in self:
            if record.product_category == "container":
                # Count storage boxes using this product
                record.storage_box_count = self.env["records.container"].search_count(
                    [("barcode_product_id", "=", record.id)]
                )
                record.shred_bin_count = 0
            elif record.product_category == "bin":
                # Count shred bins using this product
                record.shred_bin_count = self.env[
                    "shredding.inventory.item"
                ].search_count([("barcode_product_id", "=", record.id)])
                record.storage_box_count = 0
            else:
                record.storage_box_count = 0
                record.shred_bin_count = 0

    @api.depends("last_inspection_date", "inspection_frequency")
    def _compute_next_inspection(self):
        """Compute next inspection date."""
        for record in self:
            if record.last_inspection_date and record.inspection_frequency:
                if record.inspection_frequency == "daily":
                    record.next_inspection_date = fields.Date.add(
                        record.last_inspection_date, days=1
                    )
                elif record.inspection_frequency == "weekly":
                    record.next_inspection_date = fields.Date.add(
                        record.last_inspection_date, days=7
                    )
                elif record.inspection_frequency == "monthly":
                    record.next_inspection_date = fields.Date.add(
                        record.last_inspection_date, days=30
                    )
                elif record.inspection_frequency == "quarterly":
                    record.next_inspection_date = fields.Date.add(
                        record.last_inspection_date, days=90
                    )
                else:
                    record.next_inspection_date = False
            else:
                record.next_inspection_date = False

    @api.depends("manufacturing_cost", "shipping_cost", "handling_cost")
    def _compute_total_cost(self):
        """Compute total cost."""
        for record in self:
            record.total_cost = (
                (record.manufacturing_cost or 0)
                + (record.shipping_cost or 0)
                + (record.handling_cost or 0)
            )

    def action_activate(self):
        """Activate barcode product for use."""
        self.ensure_one()
        if self.state == "done":
            raise UserError(_("Cannot activate completed barcode product."))

        # Update state and notes
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nActivated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create activation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Barcode product activated: %s") % self.name,
            note=_("Barcode product has been activated and is ready for use."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcode product activated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Activated"),
                "message": _("Barcode product %s is now active and ready for use.")
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_deactivate(self):
        """Deactivate barcode product."""
        self.ensure_one()

        # Update state and notes
        self.write(
            {
                "state": "inactive",
                "active": False,
                "notes": (self.notes or "")
                + _("\nDeactivated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create deactivation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Barcode product deactivated: %s") % self.name,
            note=_("Barcode product has been deactivated and is no longer in use."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcode product deactivated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Deactivated"),
                "message": _("Barcode product %s has been deactivated.") % self.name,
                "type": "warning",
                "sticky": False,
            },
        }

    def action_generate_barcodes(self):
        """Generate barcodes for this product."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active products can generate barcodes."))

        # Create barcode generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Barcodes generated: %s") % self.name,
            note=_("Barcode labels have been generated and are ready for printing."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcodes generated for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.barcode_label_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_update_pricing(self):
        """Update pricing for barcode product."""
        self.ensure_one()

        # Create pricing update activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Pricing updated: %s") % self.name,
            note=_("Pricing information has been updated for this barcode product."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Pricing updated for: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Update Pricing"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
            },
        }

    def action_view_revenue(self):
        """View revenue analytics for this barcode product."""
        self.ensure_one()

        # Create revenue viewing activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Revenue reviewed: %s") % self.name,
            note=_("Revenue analytics and performance data has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue Analytics: %s") % self.name,
            "res_model": "sale.order.line",
            "view_mode": "graph,pivot,tree",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_confirmed_orders": True,
                "group_by": ["order_partner_id"],
            },
        }

    def action_view_shred_bins(self):
        """View shred bins associated with this barcode product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Shred Bins: %s") % self.name,
            "res_model": "shred.bin",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_group_by_location": True,
            },
        }

    def action_view_storage_boxes(self):
        """View storage boxes associated with this barcode product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Boxes: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_group_by_customer": True,
            },
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
        self.write({"state": "done"})
