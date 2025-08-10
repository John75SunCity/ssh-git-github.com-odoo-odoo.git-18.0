# -*- coding: utf-8 -*-
"""
Records Container Type Management Module

This module provides comprehensive container type management within the Records
Management System. It defines standardized container types with specifications,
capacity management, and pricing configuration for different storage containers.

Key Features:
- Standardized container type definitions with specifications
- Capacity management (weight and volume) with validation
- Pricing configuration with setup fees and monthly rates
- Container lifecycle management and tracking
- Integration with container management and billing systems
- Performance analytics and container utilization tracking

Business Processes:
1. Container Type Definition: Create standardized container types with specifications
2. Capacity Management: Define weight and volume capacities for proper allocation
3. Pricing Configuration: Set standard rates and setup fees for billing
4. Container Assignment: Assign containers to defined types for organization
5. Performance Tracking: Monitor container utilization and performance metrics
6. Lifecycle Management: Manage container type states and archival

Container Categories:
- Standard File Boxes: Letter and legal size document storage
- Archive Boxes: Long-term storage with higher capacity
- Media Storage: Specialized containers for electronic media
- Bulk Storage: Large capacity containers for bulk documents
- Secure Storage: High-security containers with special handling
- Custom Containers: Customer-specific container specifications

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerType(models.Model):
    """
    Records Container Type Management - Standardized container type definitions
    Provides container specifications, capacity management, and pricing configuration
    """

    _name = "records.container.type"
    _description = "Records Container Type"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Container Type Name",
        required=True,
        tracking=True,
        index=True,
        help="Name of the container type",
    )
    code = fields.Char(
        string="Container Code",
        required=True,
        index=True,
        help="Unique code for the container type",
    )

    # Standard container types based on actual business specifications
    standard_type = fields.Selection(
        [
            ("type_01", 'Type 01 - Standard Box (1.2 CF, 35 lbs, 12"x15"x10")'),
            ("type_02", 'Type 02 - Legal/Banker Box (2.4 CF, 65 lbs, 24"x15"x10")'),
            ("type_03", 'Type 03 - Map Box (0.875 CF, 35 lbs, 42"x6"x6")'),
            ("type_04", "Type 04 - Odd Size/Temp Box (5.0 CF, 75 lbs, dimensions unknown)"),
            ("type_06", 'Type 06 - Pathology Box (0.042 CF, 40 lbs, 12"x6"x10")'),
            ("custom", "Custom Size"),
        ],
        string="Standard Container Type",
        default="type_01",
        tracking=True,
        help="Business standard container type classification with actual specifications",
    )

    # Integration with existing barcode system
    barcode_product_id = fields.Many2one(
        "barcode.product",
        string="Barcode Product Template",
        help="Link to existing barcode product configuration",
    )
    barcode_prefix = fields.Char(
        string="Barcode Prefix",
        help="Prefix used for generating container barcodes of this type",
    )
    auto_generate_barcode = fields.Boolean(
        string="Auto Generate Barcode",
        default=True,
        help="Automatically generate barcodes for new containers of this type",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who created this container type",
    )
    active = fields.Boolean(
        string="Active", default=True, help="Whether this container type is active"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Order sequence for sorting container types"
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of container type"
    )
    dimensions = fields.Char(
        string="Standard Dimensions",
        help="Standard dimensions of the container (LxWxH)",
    )
    length = fields.Float(
        string="Length (inches)", digits=(10, 2), help="Container length in inches"
    )
    width = fields.Float(
        string="Width (inches)", digits=(10, 2), help="Container width in inches"
    )
    height = fields.Float(
        string="Height (inches)", digits=(10, 2), help="Container height in inches"
    )
    weight_capacity = fields.Float(
        string="Weight Capacity (lbs)",
        digits=(10, 2),
        default=0.0,
        help="Maximum weight capacity in pounds",
    )
    volume_capacity = fields.Float(
        string="Volume Capacity (cubic feet)",
        digits=(10, 2),
        default=0.0,
        help="Maximum volume capacity in cubic feet",
    )

    # ============================================================================
    # CLASSIFICATION AND CATEGORY
    # ============================================================================
    container_category = fields.Selection(
        [
            ("standard_file", "Standard File Storage"),
            ("legal_file", "Legal Size File Storage"),
            ("archive_bulk", "Archive Bulk Storage"),
            ("oversize_docs", "Oversize Document Storage"),
            ("map_storage", "Map and Large Format Storage"),
            ("specialty", "Specialty Box Storage"),
        ],
        string="Container Category",
        default="standard_file",
        tracking=True,
        help="Category based on document storage type and size requirements",
    )

    storage_location_type = fields.Selection(
        [
            ("general_warehouse", "General Warehouse Storage"),
            ("vault_storage", "Vault Storage Area"),
            ("climate_controlled", "Climate Controlled Area"),
            ("fire_suppression", "Fire Suppression Area"),
        ],
        string="Storage Location Type",
        default="general_warehouse",
        help="Type of storage area in the secure facility",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current state of the container type",
    )

    # ============================================================================
    # BILLING INTEGRATION WITH EXISTING MODELS
    # ============================================================================
    billing_config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Configuration",
        help="Link to existing billing configuration for this container type",
    )
    base_rate_id = fields.Many2one(
        "base.rates", string="Base Rate", help="Link to existing base rates model"
    )

    # Remove redundant pricing fields and compute from existing billing models
    standard_rate = fields.Monetary(
        string="Standard Monthly Rate",
        currency_field="currency_id",
        compute="_compute_rates_from_billing",
        store=True,
        help="Standard monthly storage rate from billing configuration",
    )
    setup_fee = fields.Monetary(
        string="Setup Fee",
        currency_field="currency_id",
        compute="_compute_rates_from_billing",
        store=True,
        help="One-time setup fee from billing configuration",
    )
    handling_fee = fields.Monetary(
        string="Handling Fee",
        currency_field="currency_id",
        compute="_compute_rates_from_billing",
        store=True,
        help="Fee for handling operations from billing configuration",
    )
    destruction_fee = fields.Monetary(
        string="Destruction Fee",
        currency_field="currency_id",
        compute="_compute_rates_from_billing",
        store=True,
        help="Fee for container destruction service from billing configuration",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # OPERATIONAL SETTINGS
    # ============================================================================
    stackable = fields.Boolean(
        string="Stackable", default=True, help="Whether containers can be stacked"
    )
    max_stack_height = fields.Integer(
        string="Max Stack Height",
        default=5,
        help="Maximum number of containers that can be stacked",
    )
    requires_special_handling = fields.Boolean(
        string="Requires Special Handling",
        default=False,
        help="Whether container type requires special handling procedures",
    )
    vault_eligible = fields.Boolean(
        string="Vault Storage Eligible",
        default=False,
        help="Whether this container type can be stored in vault area",
    )

    climate_controlled = fields.Boolean(
        string="Climate Controlled Required",
        default=False,
        help="Whether container requires climate controlled storage",
    )
    fireproof = fields.Boolean(
        string="Fireproof", default=False, help="Whether container is fireproof"
    )
    waterproof = fields.Boolean(
        string="Waterproof", default=False, help="Whether container is waterproof"
    )

    # ============================================================================
    # RELATIONSHIP FIELDS - INTEGRATE WITH EXISTING MODELS
    # ============================================================================
    container_ids = fields.One2many(
        "records.container",
        "container_type_id",
        string="Containers",
        help="Containers of this type",
    )
    # Link to existing shredding services
    shredding_service_ids = fields.One2many(
        "shredding.service",
        "container_type_id",
        string="Shredding Services",
        help="Shredding services for this container type",
    )
    # Link to existing barcode management
    barcode_sequence_ids = fields.One2many(
        "barcode.sequence",
        "container_type_id",
        string="Barcode Sequences",
        help="Barcode sequences for this container type",
    )

    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_metrics",
        store=True,
        help="Total number of containers of this type",
    )

    # Add missing computed fields referenced in methods
    utilization_percentage = fields.Float(
        string="Utilization Percentage",
        compute="_compute_container_metrics",
        store=True,
        help="Percentage of container capacity utilization",
    )
    total_revenue = fields.Monetary(
        string="Total Revenue",
        currency_field="currency_id",
        compute="_compute_total_revenue_metrics",
        store=True,
        help="Total monthly revenue from containers of this type",
    )
    volume_calculated = fields.Float(
        string="Calculated Volume",
        compute="_compute_volume_calculated",
        store=True,
        help="Volume calculated from dimensions",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity", "res_id", string="Activities"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages"
    )

    # ============================================================================
    # COMPUTED FIELDS - INTEGRATE WITH EXISTING DATA
    # ============================================================================
    @api.depends("billing_config_id", "base_rate_id", "standard_type", "currency_id")
    def _compute_rates_from_billing(self):
        """Compute rates from existing billing configuration models"""
        for record in self:
            if record.billing_config_id:
                # Get rates from existing billing configuration
                record.standard_rate = (
                    record.billing_config_id.default_monthly_rate or 0.0
                )
                record.setup_fee = record.billing_config_id.setup_fee or 0.0
                record.handling_fee = record.billing_config_id.handling_fee or 0.0
                record.destruction_fee = record.billing_config_id.destruction_fee or 0.0
            elif record.base_rate_id:
                # Fallback to base rates
                record.standard_rate = record.base_rate_id.monthly_rate or 0.0
                record.setup_fee = record.base_rate_id.setup_fee or 0.0
                record.handling_fee = record.base_rate_id.handling_fee or 0.0
                record.destruction_fee = record.base_rate_id.destruction_fee or 0.0
            elif record.standard_type and record.standard_type != "custom":
                # Use standard rates based on container type
                standard_rates = record._get_standard_type_rates()
                record.standard_rate = standard_rates.get("monthly_rate", 0.0)
                record.setup_fee = standard_rates.get("setup_fee", 0.0)
                record.handling_fee = standard_rates.get("handling_fee", 0.0)
                record.destruction_fee = standard_rates.get("destruction_fee", 0.0)
            else:
                record.standard_rate = 0.0
                record.setup_fee = 0.0
                record.handling_fee = 0.0
                record.destruction_fee = 0.0

    @api.depends("container_ids", "container_ids.state", "container_ids.current_weight")
    def _compute_container_metrics(self):
        """Compute metrics from existing container data"""
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)

            # Compute utilization from existing container weights
            if containers and record.weight_capacity > 0:
                total_weight = sum(
                    containers.filtered(
                        lambda c: c.state in ["active", "stored"]
                    ).mapped("current_weight")
                    or [0]
                )
                total_capacity = record.weight_capacity * len(containers)
                record.utilization_percentage = (
                    (total_weight / total_capacity) * 100 if total_capacity > 0 else 0.0
                )
            else:
                record.utilization_percentage = 0.0

    @api.depends("container_ids", "container_ids.state", "standard_rate")
    def _compute_total_revenue_metrics(self):
        """Compute total revenue from existing container billing data"""
        for record in self:
            # Get active containers that are being billed
            billable_containers = record.container_ids.filtered(
                lambda c: c.state in ["active", "stored"] and not c.billing_suspended
            )
            record.total_revenue = len(billable_containers) * record.standard_rate

    @api.depends("length", "width", "height")
    def _compute_volume_calculated(self):
        """Calculate volume from dimensions"""
        for record in self:
            if record.length and record.width and record.height:
                record.volume_calculated = (
                    record.length * record.width * record.height
                ) / 1728
            else:
                record.volume_calculated = 0.0

    @api.onchange("standard_type")
    def _onchange_standard_type(self):
        """Auto-populate dimensions and specifications based on standard type"""
        if self.standard_type and self.standard_type != "custom":
            # Get standard specifications for the selected type
            specs = self._get_standard_type_specifications()
            if specs:
                self.volume_capacity = specs.get("volume_cf", 0.0)
                self.weight_capacity = specs.get("avg_weight", 0.0)
                self.dimensions = specs.get("dimensions", "")

                # Parse dimensions and set individual dimension fields
                if specs.get("dimensions") != "unknown":
                    dims = specs.get("dimensions", "").split("x")
                    if len(dims) == 3:
                        try:
                            self.length = float(dims[0])
                            self.width = float(dims[1])
                            self.height = float(dims[2])
                        except ValueError:
                            pass  # Keep existing values if parsing fails

    def _get_standard_type_specifications(self):
        """Get standard specifications for container types"""
        specs_mapping = {
            "type_01": {  # Standard Box
                "volume_cf": 1.2,
                "avg_weight": 35,
                "dimensions": "12x15x10",
                "description": "Standard Box - General file storage",
            },
            "type_02": {  # Legal/Banker Box
                "volume_cf": 2.4,  # Corrected volume
                "avg_weight": 65,
                "dimensions": "24x15x10",
                "description": "Legal/Banker Box - Large capacity file storage",
            },
            "type_03": {  # Map Box
                "volume_cf": 0.875,
                "avg_weight": 35,
                "dimensions": "42x6x6",
                "description": "Map Box - Maps, blueprints, and long documents",
            },
            "type_04": {  # Odd Size/Temp Box
                "volume_cf": 5.0,
                "avg_weight": 75,
                "dimensions": "unknown",
                "description": "Odd Size/Temp Box - Variable size temporary storage",
            },
            "type_06": {  # Pathology Box
                "volume_cf": 0.042,
                "avg_weight": 40,
                "dimensions": "12x6x10",
                "description": "Pathology Box - Medical specimens and pathology documents",
            },
        }
        return specs_mapping.get(self.standard_type, {})

    # ============================================================================
    # CONSTRAINTS AND VALIDATION
    # ============================================================================
    _sql_constraints = [
        (
            "code_company_unique",
            "unique(code, company_id)",
            "Container type code must be unique per company!",
        ),
        (
            "name_company_unique",
            "unique(name, company_id)",
            "Container type name must be unique per company!",
        ),
        (
            "positive_weight_capacity",
            "check(weight_capacity >= 0)",
            "Weight capacity must be positive!",
        ),
        (
            "positive_volume_capacity",
            "check(volume_capacity >= 0)",
            "Volume capacity must be positive!",
        ),
    ]

    @api.constrains("length", "width", "height")
    def _check_dimensions(self):
        """Validate container dimensions"""
        for record in self:
            if record.length and record.length <= 0:
                raise ValidationError(_("Length must be positive"))
            if record.width and record.width <= 0:
                raise ValidationError(_("Width must be positive"))
            if record.height and record.height <= 0:
                raise ValidationError(_("Height must be positive"))

    @api.constrains("max_stack_height")
    def _check_stack_height(self):
        """Validate stack height"""
        for record in self:
            if record.max_stack_height < 1:
                raise ValidationError(_("Maximum stack height must be at least 1"))

    @api.constrains("standard_rate", "setup_fee", "handling_fee", "destruction_fee")
    def _check_pricing(self):
        """Validate pricing fields"""
        for record in self:
            if record.standard_rate < 0:
                raise ValidationError(_("Standard rate cannot be negative"))
            if record.setup_fee < 0:
                raise ValidationError(_("Setup fee cannot be negative"))
            if record.handling_fee < 0:
                raise ValidationError(_("Handling fee cannot be negative"))
            if record.destruction_fee < 0:
                raise ValidationError(_("Destruction fee cannot be negative"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the container type"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft container types can be activated"))

        self.write({"state": "active", "active": True})
        self.message_post(body=_("Container type activated"))

    def action_archive(self):
        """Archive the container type"""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active container types can be archived"))

        # Check for active containers
        active_containers = self.container_ids.filtered(
            lambda c: c.state == "active"
        )
        if active_containers:
            raise UserError(
                _(
                    "Cannot archive container type with active containers. "
                    "Please archive or reassign all containers first."
                )
            )

        self.write({"state": "archived", "active": False})
        self.message_post(body=_("Container type archived"))

    def action_view_containers(self):
        """View all containers of this type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Containers"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("container_type_id", "=", self.id)],
            "context": {"default_container_type_id": self.id},
        }

    def action_create_container(self):
        """Create a new container of this type"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Container"),
            "res_model": "records.container",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_container_type_id": self.id,
                "default_weight_capacity": self.weight_capacity,
                "default_volume_capacity": self.volume_capacity,
            },
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def get_pricing_info(self):
        """Get comprehensive pricing information"""
        self.ensure_one()
        return {
            "standard_rate": self.standard_rate,
            "setup_fee": self.setup_fee,
            "handling_fee": self.handling_fee,
            "destruction_fee": self.destruction_fee,
            "currency": self.currency_id.name,
            "total_monthly_revenue": self.total_revenue,
        }

    def calculate_storage_cost(self, months=1, include_setup=False):
        """Calculate storage cost for specified period"""
        self.ensure_one()
        cost = self.standard_rate * months
        if include_setup:
            cost += self.setup_fee
        return cost

    @api.constrains("container_ids")
    def _check_capacity_availability(self):
        """Check if there's capacity available for new containers"""
        for record in self:
            # This would depend on location capacity limits
            # For now, return True - implement based on business rules
            pass

    def get_container_summary(self):
        """Get summary information for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "code": self.code,
            "category": self.container_category,
            "container_count": self.container_count,
            "weight_capacity": self.weight_capacity,
            "volume_capacity": self.volume_capacity,
            "standard_rate": self.standard_rate,
            "utilization_percentage": self.utilization_percentage,
            "total_revenue": self.total_revenue,
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            if record.code:
                display_name = _("%s [%s]", record.name, record.code)
            else:
                display_name = record.name
            result.append((record.id, display_name))
        return result

    @api.model
    def _search_name_code(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
        """Enhanced search by name or code"""
        args = args or []
        domain = []
        if name:
            domain = [
                "|",
                "|",
                ("name", operator, name),
                ("code", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    @api.model
    def get_container_types_by_category(self, category):
        """Get container types by category"""
        return self.search(
            [("container_category", "=", category), ("state", "=", "active")]
        )

    def copy(self, default=None):
        """Override copy to ensure unique codes"""
        default = dict(default or {})
        # Generate a unique code for the copy
        base_code = self.code
        if base_code.endswith("_COPY"):
            # Code already has _COPY suffix, keep it as is
            new_code = base_code
        elif "_COPY" in base_code:
            base_code = base_code.split("_COPY")[0] + "_COPY"
            new_code = base_code
        else:
            new_code = f"{base_code}_COPY"

        # Find existing copies and increment a counter if needed
        existing_codes = self.search(
            [("code", "like", f"{new_code}%"), ("company_id", "=", self.company_id.id)]
        ).mapped("code")
        counter = 1
        final_code = new_code
        while final_code in existing_codes:
            counter += 1
            final_code = f"{new_code}{counter}"

        default.update(
            {
                "name": _("%(name)s (Copy)", name=self.name),
                "code": final_code,
            }
        )
        return super().copy(default)

    # ============================================================================
    # BUSINESS METHODS - INTEGRATE WITH EXISTING SYSTEMS
    # ============================================================================
    def _get_standard_type_rates(self):
        """Get standard rates based on container type from existing rate configuration"""
        self.ensure_one()

        # First priority: Direct billing configuration link
        if self.billing_config_id:
            return {
                "monthly_rate": self.billing_config_id.default_monthly_rate or 0.0,
                "setup_fee": self.billing_config_id.setup_fee or 0.0,
                "handling_fee": self.billing_config_id.handling_fee or 0.0,
                "destruction_fee": self.billing_config_id.destruction_fee or 0.0,
            }

        # Second priority: Direct base rate link
        if self.base_rate_id:
            return {
                "monthly_rate": self.base_rate_id.monthly_rate or 0.0,
                "setup_fee": self.base_rate_id.setup_fee or 0.0,
                "handling_fee": self.base_rate_id.handling_fee or 0.0,
                "destruction_fee": self.base_rate_id.destruction_fee or 0.0,
            }

        # Third priority: Search base rates by container type code
        base_rates = self.env["base.rates"].search(
            [("container_type_code", "=", self.code)], limit=1
        )

        if base_rates:
            return {
                "monthly_rate": base_rates.monthly_rate or 0.0,
                "setup_fee": base_rates.setup_fee or 0.0,
                "handling_fee": base_rates.handling_fee or 0.0,
                "destruction_fee": base_rates.destruction_fee or 0.0,
            }

        # Fourth priority: Search base rates by standard type
        if self.standard_type and self.standard_type != "custom":
            base_rates = self.env["base.rates"].search(
                [("container_type", "=", self.standard_type)], limit=1
            )

            if base_rates:
                return {
                    "monthly_rate": base_rates.monthly_rate or 0.0,
                    "setup_fee": base_rates.setup_fee or 0.0,
                    "handling_fee": base_rates.handling_fee or 0.0,
                    "destruction_fee": base_rates.destruction_fee or 0.0,
                }

        # Fifth priority: Hardcoded standard rates for actual business container types
        rate_mapping = {
            "type_01": {  # Standard Box - 1.2 CF, 35 lbs avg, 12x15x10
                "monthly_rate": 5.50,
                "setup_fee": 15.00,
                "handling_fee": 8.00,
                "destruction_fee": 12.00,
                "volume_cf": 1.2,
                "avg_weight": 35,
                "dimensions": "12x15x10",
            },
            "type_02": {  # Legal/Banker Box - 2.4 CF, 65 lbs avg, 24x15x10
                "monthly_rate": 7.50,
                "setup_fee": 20.00,
                "handling_fee": 12.00,
                "destruction_fee": 18.00,
                "volume_cf": 2.4,  # Corrected volume
                "avg_weight": 65,
                "dimensions": "24x15x10",
            },
            "type_03": {  # Map Box - 0.875 CF, 35 lbs avg, 42x6x6
                "monthly_rate": 8.00,
                "setup_fee": 25.00,
                "handling_fee": 15.00,
                "destruction_fee": 20.00,
                "volume_cf": 0.875,
                "avg_weight": 35,
                "dimensions": "42x6x6",
            },
            "type_04": {  # Odd Size/Temp Box - 5.0 CF, 75 lbs avg, unknown dimensions
                "monthly_rate": 15.00,
                "setup_fee": 40.00,
                "handling_fee": 25.00,
                "destruction_fee": 35.00,
                "volume_cf": 5.0,
                "avg_weight": 75,
                "dimensions": "unknown",
            },
            "type_06": {  # Pathology Box - 0.042 CF, 40 lbs avg, 12x6x10
                "monthly_rate": 4.50,
                "setup_fee": 12.00,
                "handling_fee": 6.00,
                "destruction_fee": 10.00,
                "volume_cf": 0.042,
                "avg_weight": 40,
                "dimensions": "12x6x10",
            },
        }

        # Return rates for the specific container type or zeros if not found
        return rate_mapping.get(
            self.standard_type,
            {
                "monthly_rate": 0.0,
                "setup_fee": 0.0,
                "handling_fee": 0.0,
                "destruction_fee": 0.0,
                "volume_cf": 0.0,
                "avg_weight": 0.0,
                "dimensions": "unknown",
            },
        )

    def generate_container_barcode(self):
        """Generate barcode using existing barcode system"""
        self.ensure_one()
        if not self.barcode_product_id:
            raise UserError(
                _("No barcode product template configured for this container type")
            )

        # Use existing barcode generation system
        barcode_service = self.env["barcode.product"]
        return barcode_service.generate_barcode_for_container_type(self)

    def get_billing_configuration(self):
        """Get billing configuration from existing billing system"""
        self.ensure_one()
        if self.billing_config_id:
            return self.billing_config_id
        elif self.standard_type != "custom":
            # Find or create billing config for standard type
            billing_config = self.env["records.billing.config"].search(
                [("container_type", "=", self.standard_type)], limit=1
            )
            if billing_config:
                self.billing_config_id = billing_config.id
                return billing_config
        return False

    def create_containers_from_barcodes(self, barcode_list):
        """Create containers from barcode list using existing container management"""
        self.ensure_one()
        container_model = self.env["records.container"]
        created_containers = container_model.browse()

        base_container_vals = {
            "container_type_id": self.id,
            "weight_capacity": self.weight_capacity,
            "volume_capacity": self.volume_capacity,
            "state": "draft",
        }

        for barcode in barcode_list:
            container_vals = dict(base_container_vals)
            container_vals.update(
                {
                    "name": f"Container {barcode}",
                    "barcode": barcode,
                }
            )
            container = container_model.create(container_vals)
            created_containers |= container

        return created_containers
