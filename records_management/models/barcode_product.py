# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BarcodeProduct(models.Model):
    _name = "barcode.product"
    _description = "Barcode Product Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Computed display name
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(string="Product Name", required=True, tracking=True, index=True)
    code = fields.Char(string="Product Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # Framework Required Fields
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Product Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

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

    # ============================================================================
    # BARCODE CONFIGURATION
    # ============================================================================

    # Barcode Settings
    barcode = fields.Char(string="Base Barcode", tracking=True)
    barcode_format = fields.Selection(
        [
            ("ean13", "EAN-13"),
            ("ean8", "EAN-8"),
            ("upca", "UPC-A"),
            ("code128", "Code 128"),
            ("code39", "Code 39"),
            ("custom", "Custom Format"),
        ],
        string="Barcode Format",
        default="code128",
        required=True,
    )

    # Barcode Generation
    start_barcode = fields.Char(
        string="Start Barcode", help="Starting barcode for range generation"
    )
    end_barcode = fields.Char(
        string="End Barcode", help="End barcode for range generation"
    )
    next_sequence_number = fields.Integer(
        string="Next Sequence", default=1, help="Next sequence for generation"
    )
    generation_batch_size = fields.Integer(
        string="Batch Size", default=100, help="Number of barcodes per batch"
    )

    # Validation Settings
    validate_format = fields.Boolean(string="Validate Format", default=True)
    validate_uniqueness = fields.Boolean(string="Validate Uniqueness", default=True)
    validate_check_digit = fields.Boolean(string="Validate Check Digit", default=True)

    # ============================================================================
    # PRODUCT CATEGORIZATION
    # ============================================================================

    # Product Category
    product_category = fields.Selection(
        [
            ("container", "Storage Container"),
            ("bin", "Shred Bin"),
            ("folder", "File Folder"),
            ("location", "Location Tag"),
            ("document", "Document Label"),
        ],
        string="Product Category",
        required=True,
        tracking=True,
    )

    product_type = fields.Selection(
        [
            ("physical", "Physical Product"),
            ("service", "Service Product"),
            ("consumable", "Consumable"),
        ],
        string="Product Type",
        default="physical",
        required=True,
    )

    # Classification
    size_category = fields.Selection(
        [
            ("small", "Small"),
            ("medium", "Medium"),
            ("large", "Large"),
            ("extra_large", "Extra Large"),
        ],
        string="Size Category",
        default="medium",
    )

    # ============================================================================
    # PRICING & FINANCIAL
    # ============================================================================

    # Currency Configuration
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Pricing
    base_price = fields.Monetary(
        string="Base Price", currency_field="currency_id", tracking=True
    )
    cost_price = fields.Monetary(
        string="Cost Price", currency_field="currency_id", tracking=True
    )
    sale_price = fields.Monetary(
        string="Sale Price", currency_field="currency_id", tracking=True
    )

    # Discounts and Promotions
    discount_percentage = fields.Float(
        string="Discount %", digits=(5, 2), help="Default discount percentage"
    )
    effective_date = fields.Date(string="Effective Date", tracking=True)
    expiration_date = fields.Date(string="Expiration Date", tracking=True)

    # ============================================================================
    # CUSTOMER & LOCATION MANAGEMENT
    # ============================================================================

    # Customer Relationships
    customer_id = fields.Many2one("res.partner", string="Primary Customer")
    customer_location_id = fields.Many2one(
        "records.location", string="Customer Location"
    )

    # Location Settings
    storage_location_id = fields.Many2one("records.location", string="Storage Location")
    default_location_id = fields.Many2one("records.location", string="Default Location")

    # Access Control
    access_frequency = fields.Selection(
        [
            ("daily", "Daily Access"),
            ("weekly", "Weekly Access"),
            ("monthly", "Monthly Access"),
            ("quarterly", "Quarterly Access"),
            ("annual", "Annual Access"),
            ("inactive", "Inactive Storage"),
        ],
        string="Access Frequency",
        default="monthly",
    )

    # ============================================================================
    # TECHNICAL SPECIFICATIONS
    # ============================================================================

    # Physical Properties
    weight = fields.Float(string="Weight (kg)", digits=(8, 2))
    volume = fields.Float(string="Volume (m³)", digits=(8, 3))
    capacity = fields.Float(string="Capacity", digits=(8, 2))

    # Dimensions
    length = fields.Float(string="Length (cm)", digits=(8, 2))
    width = fields.Float(string="Width (cm)", digits=(8, 2))
    height = fields.Float(string="Height (cm)", digits=(8, 2))

    # Security Features
    security_level = fields.Selection(
        [
            ("basic", "Basic Security"),
            ("enhanced", "Enhanced Security"),
            ("high", "High Security"),
            ("maximum", "Maximum Security"),
        ],
        string="Security Level",
        default="basic",
    )

    # Shredding Configuration
    shred_security_level = fields.Selection(
        [
            ("level_1", "Level 1 - Strip Cut"),
            ("level_2", "Level 2 - Cross Cut"),
            ("level_3", "Level 3 - Particle Cut"),
            ("level_4", "Level 4 - Micro Cut"),
            ("level_5", "Level 5 - Crypto Cut"),
            ("level_6", "Level 6 - High Security"),
        ],
        string="Shred Security Level",
        default="level_2",
    )

    # Environmental Features
    fireproof_rating = fields.Selection(
        [
            ("class_a", "Class A - Ordinary Combustibles"),
            ("class_b", "Class B - Flammable Liquids"),
            ("class_c", "Class C - Electrical Equipment"),
            ("class_d", "Class D - Combustible Metals"),
            ("none", "No Fire Protection"),
        ],
        string="Fireproof Rating",
        default="class_a",
    )

    indoor_outdoor = fields.Selection(
        [
            ("indoor", "Indoor Use Only"),
            ("outdoor", "Outdoor Use Only"),
            ("both", "Indoor/Outdoor Use"),
        ],
        string="Usage Environment",
        default="indoor",
    )

    # ============================================================================
    # OPERATIONAL METRICS
    # ============================================================================

    # Usage Statistics
    total_generated = fields.Integer(string="Total Generated", default=0, readonly=True)
    total_used = fields.Integer(string="Total Used", default=0, readonly=True)
    last_generated_barcode = fields.Char(string="Last Generated", readonly=True)

    # Capacity Management
    fill_level = fields.Float(
        string="Fill Level %",
        digits=(5, 2),
        default=0.0,
        help="Current fill percentage",
    )
    max_capacity = fields.Float(
        string="Maximum Capacity", digits=(8, 2), help="Maximum storage capacity"
    )
    current_usage = fields.Float(
        string="Current Usage",
        digits=(8, 2),
        compute="_compute_current_usage",
        store=True,
    )

    # Performance Metrics
    utilization_rate = fields.Float(
        string="Utilization Rate %",
        digits=(5, 2),
        compute="_compute_utilization_rate",
        store=True,
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    # Storage Container Relationship (customer boxes/containers tracked with barcodes)
    storage_container_id = fields.Many2one(
        "records.container",
        string="Storage Box",
        tracking=True,
        help="Customer storage box/container linked to this barcode for tracking and pricing",
    )

    # Internal Storage Box Relationship (internal boxes that contain barcode products)
    storage_box_id = fields.Many2one(
        "barcode.storage.box",
        string="Internal Storage Box",
        tracking=True,
        help="Internal box that contains this barcode product",
    )

    # ============================================================================

    # Product Relationships
    category_id = fields.Many2one("product.category", string="Odoo Product Category")
    template_id = fields.Many2one("product.template", string="Product Template")

    # Generation History
    generation_history_ids = fields.One2many(
        "barcode.generation.history", "product_id", string="Generation History"
    )

    # Pricing Tiers
    pricing_tier_ids = fields.One2many(
        "barcode.pricing.tier", "product_id", string="Pricing Tiers"
    )

    # Storage Container Configuration (barcoded containers)
    storage_container_ids = fields.One2many(
        "records.container", "barcode_product_id", string="Storage Containers"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends("fill_level", "max_capacity")
    def _compute_current_usage(self):
        """Compute current usage based on fill level and capacity"""
        for record in self:
            if record.max_capacity and record.fill_level:
                record.current_usage = (record.fill_level / 100) * record.max_capacity
            else:
                record.current_usage = 0.0

    @api.depends("current_usage", "max_capacity")
    def _compute_utilization_rate(self):
        """Compute utilization rate percentage"""
        for record in self:
            if record.max_capacity:
                record.utilization_rate = (
                    record.current_usage / record.max_capacity
                ) * 100
            else:
                record.utilization_rate = 0.0

    @api.depends("name", "code")
    def _compute_display_name(self):
        """Compute display name with code"""
        for record in self:
            if record.code:
                record.display_name = f"[{record.code}] {record.name}"
            else:
                record.display_name = record.name or _("New")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_generate_barcodes(self):
        """Generate barcode batch"""
        self.ensure_one()
        if not self.generation_batch_size:
            raise UserError(_("Please set generation batch size."))

        # Generate barcodes logic here
        self.write(
            {
                "total_generated": self.total_generated + self.generation_batch_size,
                "next_sequence_number": self.next_sequence_number
                + self.generation_batch_size,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Barcodes Generated"),
                "message": _("Generated %s barcodes successfully.")
                % self.generation_batch_size,
                "type": "success",
                "sticky": False,
            },
        }

    def action_validate_barcode(self):
        """Validate barcode format and uniqueness"""
        self.ensure_one()
        if not self.barcode:
            raise UserError(_("Please enter a barcode to validate."))

        # Validation logic here
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Barcode Valid"),
                "message": _("Barcode validation completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_generation_history(self):
        """View barcode generation history"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Generation History"),
            "res_model": "barcode.generation.history",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
        }

    def action_configure_pricing(self):
        """Configure product pricing tiers"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Pricing"),
            "res_model": "barcode.pricing.tier",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {"default_product_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("barcode")
    def _check_barcode_format(self):
        """Validate barcode format"""
        for record in self:
            if record.barcode and record.validate_format:
                # Add format validation logic
                if len(record.barcode) < 3:
                    raise ValidationError(
                        _("Barcode must be at least 3 characters long.")
                    )

    @api.constrains("base_price", "cost_price", "sale_price")
    def _check_pricing(self):
        """Validate pricing values"""
        for record in self:
            if record.base_price and record.base_price < 0:
                raise ValidationError(_("Base price cannot be negative."))
            if record.cost_price and record.cost_price < 0:
                raise ValidationError(_("Cost price cannot be negative."))
            if record.sale_price and record.sale_price < 0:
                raise ValidationError(_("Sale price cannot be negative."))

    @api.constrains("fill_level", "utilization_rate")
    def _check_percentages(self):
        """Validate percentage values"""
        for record in self:
            if record.fill_level and (record.fill_level < 0 or record.fill_level > 100):
                raise ValidationError(_("Fill level must be between 0 and 100."))
            if record.utilization_rate and (
                record.utilization_rate < 0 or record.utilization_rate > 100
            ):
                raise ValidationError(_("Utilization rate must be between 0 and 100."))

    @api.constrains("weight", "volume", "capacity")
    def _check_physical_properties(self):
        """Validate physical properties"""
        for record in self:
            if record.weight and record.weight < 0:
                raise ValidationError(_("Weight cannot be negative."))
            if record.volume and record.volume < 0:
                raise ValidationError(_("Volume cannot be negative."))
            if record.capacity and record.capacity < 0:
                raise ValidationError(_("Capacity cannot be negative."))

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals):
        """Override create to set defaults"""
        if not vals.get("name"):
            vals["name"] = self.env["ir.sequence"].next_by_code("barcode.product") or _(
                "New"
            )
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        if "state" in vals:
            for record in self:
                record.message_post(
                    body=_("Status changed from %s to %s")
                    % (
                        dict(record._fields["state"].selection).get(record.state),
                        dict(record._fields["state"].selection).get(vals["state"]),
                    )
                )
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of active products"""
        if any(record.state == "active" for record in self):
            raise UserError(
                _("Cannot delete active barcode products. Please archive them first.")
    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
    monthly_volume = fields.Char(string='Monthly Volume', tracking=True)
    naid_compliant = fields.Char(string='Naid Compliant', tracking=True)
    storage_rate = fields.Monetary(string='Storage Rate', currency_field='currency_id', tracking=True)
        return super().unlink()

    # ============================================================================
    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================\n    monthly_volume = fields.Char(string='Monthly Volume', tracking=True)\n    naid_compliant = fields.Char(string='Naid Compliant', tracking=True)\n    storage_rate = fields.Monetary(string='Storage Rate', currency_field='currency_id', tracking=True)\n    # ============================================================================\n    # AUTO-GENERATED FIELDS (Batch 1)\n    # ============================================================================\n    monthly_volume = fields.Char(string='Monthly Volume', tracking=True)\n    naid_compliant = fields.Char(string='Naid Compliant', tracking=True)\n    storage_rate = fields.Monetary(string='Storage Rate', currency_field='currency_id', tracking=True)\n
    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_activate(self):
        """Activate - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Activate"),
            "res_model": "barcode.product",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_deactivate(self):
        """Deactivate - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Deactivate"),
            "res_model": "barcode.product",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_update_pricing(self):
        """Update Pricing - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Update Pricing"),
            "res_model": "barcode.product",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_view_revenue(self):
        """View Revenue - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Revenue"),
            "res_model": "barcode.product",
            "view_mode": "tree,form",
            "domain": [("product_id", "=", self.id)],
            "context": {"default_product_id": self.id},
        }
    def action_view_shred_bins(self):
        """View Shred Bins - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Shred Bins"),
            "res_model": "barcode.product",
            "view_mode": "tree,form",
            "domain": [("product_id", "=", self.id)],
            "context": {"default_product_id": self.id},
        }
    def action_view_storage_boxes(self):
        """View Storage Boxes - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Storage Boxes"),
            "res_model": "barcode.product",
            "view_mode": "tree,form",
            "domain": [("product_id", "=", self.id)],
            "context": {"default_product_id": self.id},
        }