# -*- coding: utf-8 -*-
"""
Shred Bins Management Module

This module provides comprehensive management of customer shred bins within the Records Management System.
It implements enterprise-grade shred bin tracking for customer document collection and secure destruction services.

Key Features:
- Customer shred bin location tracking with barcode integration
- Security level management with secure collection protocols
- Capacity tracking and collection scheduling
- Integration with shredding services and customer assignments
- Multi-location support with proper audit trails
- State management for bin service lifecycle

Business Processes:
1. Bin Deployment: Place secure bins at customer locations for document collection
2. Access Control: Manage secure collection and key access protocols
3. Capacity Management: Monitor fill levels and schedule collection services
4. Service Integration: Connect with shredding services for secure destruction
5. Customer Assignment: Link bins to specific customers for dedicated service

Technical Implementation:
- Modern Odoo 18.0 patterns with mail.thread inheritance
- Comprehensive validation with proper field constraints
- Secure domain filtering for multi-tenant access
- Integration with shredding services and customer management
- Performance optimized with proper indexing and relationships

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api
from odoo.exceptions import ValidationError


class ShredBin(models.Model):
    _name = "shred.bin"
    _description = "Customer Shred Bin"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Bin Number",
        required=True,
        tracking=True,
        index=True,
        help="Unique identifier for the customer shred bin",
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Service Representative",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
        help="Service representative responsible for this bin",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("deployed", "Deployed"),
            ("in_service", "In Service"),
            ("full", "Full - Needs Collection"),
            ("collecting", "Being Collected"),
            ("maintenance", "Maintenance"),
            ("retired", "Retired"),
        ],
        string="Service Status",
        default="deployed",
        tracking=True,
        help="Current service status of the shred bin",
    )

    # ============================================================================
    # BIN SPECIFICATIONS
    # ============================================================================
    barcode = fields.Char(
        string="Barcode",
        index=True,
        tracking=True,
        help="Barcode identifier for collection operations",
    )
    description = fields.Text(
        string="Service Notes",
        help="Additional details about the bin service requirements",
    )
    customer_location = fields.Char(
        string="Customer Location",
        tracking=True,
        help="Specific location at customer site where bin is placed",
    )
    bin_size = fields.Selection(
        [
            ("23", "23 GALLON SHREDINATOR"),
            ("3B", "32 GALLON BIN"),
            ("3C", "32 GALLON CONSOLE"),
            ("64", "64 GALLON BIN"),
            ("96", "96 GALLON BIN"),
        ],
        string="Bin Size",
        default="3C",
        required=True,
        tracking=True,
        help="Physical size and type of the shred bin using internal item codes",
    )

    # ============================================================================
    # CAPACITY MANAGEMENT
    # ============================================================================
    capacity_pounds = fields.Float(
        string="Capacity (Pounds)",
        digits="Stock Weight",
        compute="_compute_capacity_pounds",
        store=True,
        help="Maximum weight capacity of the bin in pounds (auto-calculated from bin size)",
    )
    current_fill_level = fields.Float(
        string="Fill Level (%)",
        compute="_compute_current_fill_level",
        store=True,
        help="Current fill level percentage of bin capacity",
    )
    estimated_weight = fields.Float(
        string="Estimated Weight (lbs)",
        compute="_compute_estimated_weight",
        store=True,
        help="Estimated current weight of documents in bin",
    )

    # ============================================================================
    # SECURITY & COLLECTION
    # ============================================================================
    is_locked = fields.Boolean(
        string="Locked",
        default=True,
        tracking=True,
        help="Whether this bin is securely locked",
    )
    lock_type = fields.Selection(
        [
            ("key", "Key Lock"),
            ("combination", "Combination Lock"),
            ("electronic", "Electronic Lock"),
        ],
        string="Lock Type",
        default="key",
        required=True,
        tracking=True,
        help="Type of locking mechanism used",
    )

    # ============================================================================
    # CUSTOMER & SERVICE RELATIONSHIP FIELDS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        domain="[('is_company', '=', True)]",
        tracking=True,
        required=True,
        help="Customer who owns this shred bin service",
    )
    shredding_service_ids = fields.One2many(
        "shredding.service",
        "shred_bin_id",
        string="Shredding Services",
        help="Collection and shredding services for this bin",
    )
    pickup_request_ids = fields.One2many(
        "pickup.request",
        "shred_bin_id",
        string="Pickup Requests",
        help="Pickup requests related to this shred bin",
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    service_count = fields.Integer(
        string="Service Count",
        compute="_compute_service_count",
        store=True,
        help="Number of shredding services performed on this bin",
    )
    needs_collection = fields.Boolean(
        string="Needs Collection",
        compute="_compute_needs_collection",
        help="Whether the bin needs immediate collection",
    )
    last_service_date = fields.Datetime(
        string="Last Service Date",
        compute="_compute_last_service_date",
        help="Date and time of last collection service",
    )
    location_status = fields.Selection(
        [
            ("at_facility", "At Facility"),
            ("at_customer", "At Customer Location"),
            ("in_transit", "In Transit"),
            ("unknown", "Location Unknown"),
        ],
        string="Location Status",
        compute="_compute_location_status",
        help="Current known location of the bin for color coding",
    )
    can_upsize = fields.Boolean(
        string="Can Upsize",
        compute="_compute_sizing_options",
        help="Whether this bin can be upsized",
    )
    can_downsize = fields.Boolean(
        string="Can Downsize",
        compute="_compute_sizing_options",
        help="Whether this bin can be downsized",
    )
    next_size_up = fields.Selection(
        [
            ("3B", "32 GALLON BIN"),
            ("3C", "32 GALLON CONSOLE"),
            ("64", "64 GALLON BIN"),
            ("96", "96 GALLON BIN"),
        ],
        string="Next Size Up",
        compute="_compute_sizing_options",
        help="Next available bin size up",
    )
    next_size_down = fields.Selection(
        [
            ("23", "23 GALLON SHREDINATOR"),
            ("3B", "32 GALLON BIN"),
            ("3C", "32 GALLON CONSOLE"),
            ("64", "64 GALLON BIN"),
        ],
        string="Next Size Down",
        compute="_compute_sizing_options",
        help="Next available bin size down",
    )

    # ============================================================================
    # CUSTOMER PORTAL & BILLING FIELDS
    # ============================================================================
    days_since_last_service = fields.Integer(
        string="Days Since Last Service",
        compute="_compute_days_since_last_service",
        help="Number of days since last service at customer location",
    )
    current_billing_period_services = fields.Integer(
        string="Current Billing Period Services",
        compute="_compute_billing_period_services",
        help="Number of services in current billing period",
    )
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        help="Department/division this bin belongs to for access control",
    )

    # ============================================================================
    # CAPACITY & EFFICIENCY ANALYSIS FIELDS
    # ============================================================================
    capacity_utilization_rating = fields.Selection(
        [
            ("underutilized", "Under-utilized"),
            ("optimal", "Optimal"),
            ("overutilized", "Over-utilized"),
            ("critical", "Critical - Needs Immediate Attention"),
        ],
        string="Capacity Rating",
        compute="_compute_capacity_utilization_rating",
        help="Assessment of bin capacity utilization efficiency",
    )
    recommended_service_frequency = fields.Char(
        string="Recommended Service Frequency",
        compute="_compute_service_recommendations",
        help="AI-recommended service frequency based on usage patterns",
    )
    monthly_capacity_lbs = fields.Float(
        string="Monthly Capacity (lbs)",
        compute="_compute_monthly_metrics",
        help="Theoretical monthly paper processing capacity in pounds",
    )
    cost_efficiency_rating = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor - Consider Upsize"),
        ],
        string="Cost Efficiency",
        compute="_compute_cost_efficiency_rating",
        help="Cost efficiency rating based on cost per pound processed",
    )
    bin_specifications = fields.Text(
        string="Bin Specifications",
        compute="_compute_bin_specifications",
        help="Detailed manufacturer specifications and capacity information",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("bin_size")
    def _compute_capacity_pounds(self):
        """Calculate capacity based on industry-standard bin specifications"""
        # Industry-standard weight capacities based on actual manufacturer data
        capacity_map = {
            "23": 60,  # 23 Gallon Shredinator - Exact manufacturer specification
            "3B": 125,  # 32 Gallon Bin - HSM and similar models, up to 125 lbs
            "3C": 90,  # 32 Gallon Console - Average of executive console range (80-100 lbs)
            "64": 240,  # 64 Gallon Bin - Industry average (225-250 lbs range)
            "96": 340,  # 96 Gallon Bin - Industry average (325-350 lbs range)
        }

        for record in self:
            record.capacity_pounds = capacity_map.get(
                record.bin_size, 90
            )  # Default to console capacity

    @api.depends("bin_size", "state")
    def _compute_current_fill_level(self):
        """Estimate current fill level based on bin size and state"""
        fill_levels = {
            "deployed": 0,
            "in_service": 25,
            "full": 95,
            "collecting": 95,
            "maintenance": 0,
            "retired": 0,
        }

        for record in self:
            record.current_fill_level = fill_levels.get(record.state, 0)

    @api.depends("current_fill_level", "capacity_pounds")
    def _compute_estimated_weight(self):
        """Calculate estimated weight based on fill level"""
        for record in self:
            record.estimated_weight = (
                record.current_fill_level / 100.0
            ) * record.capacity_pounds

    @api.depends("shredding_service_ids")
    def _compute_service_count(self):
        """Count shredding services performed on this bin"""
        for record in self:
            record.service_count = len(record.shredding_service_ids)

    @api.depends("current_fill_level", "state")
    def _compute_needs_collection(self):
        """Determine if bin needs collection"""
        for record in self:
            record.needs_collection = (
                record.current_fill_level >= 90.0 or record.state == "full"
            )

    def _compute_last_service_date(self):
        """Find the most recent service date"""
        for record in self:
            if record.shredding_service_ids:
                last_service = record.shredding_service_ids.sorted(
                    "service_date", reverse=True
                )[:1]
                record.last_service_date = (
                    last_service.service_date if last_service else False
                )
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.last_service_date = False

    @api.depends("bin_size")
    def _compute_sizing_options(self):
        """Compute whether bin can be upsized or downsized based on business rules"""
        # Size hierarchy: 23 -> 3B/3C (32 gal) -> 64 -> 96

        for record in self:
            current_size = record.bin_size

            # Can upsize logic
            if current_size == "96":
                # 96 gallon is largest - cannot upsize, but can request additional bins
                record.can_upsize = False
                record.next_size_up = False
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.can_upsize = True
                # Determine next size up
                if current_size in ["23", "3B"]:
                    record.next_size_up = "3C"  # Upgrade to console
                elif current_size == "3C":
            pass
            pass
                    record.next_size_up = "64"
                elif current_size == "64":
            pass
            pass
                    record.next_size_up = "96"
                else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                    record.next_size_up = "3C"  # Default

            # Can downsize logic
            if current_size == "23":
                # 23 gallon is smallest - cannot downsize
                record.can_downsize = False
                record.next_size_down = False
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.can_downsize = True
                # Determine next size down
                if current_size == "96":
                    record.next_size_down = "64"
                elif current_size == "64":
            pass
            pass
                    record.next_size_down = "3C"  # Default to console
                elif current_size == "3B":
            pass
                    record.next_size_down = "23"  # Bin to shredinator
                elif current_size == "3C":
            pass
            pass
                    record.next_size_down = "3B"  # Console to regular bin
                else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                    record.next_size_down = "3B"  # Default

    @api.depends("state", "partner_id")
    def _compute_location_status(self):
        """Determine location status for color coding"""
        for record in self:
            if record.state == "deployed":
                record.location_status = "at_facility"  # Blue - ready for deployment
            elif record.state in ("in_service", "full"):
            pass
                record.location_status = "at_customer"  # Green/Red based on fill
            elif record.state == "collecting":
            pass
                record.location_status = "in_transit"  # Orange - being collected
            elif record.state in ("maintenance", "retired"):
            pass
                record.location_status = "at_facility"  # Purple/Grey - at facility
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.location_status = "unknown"  # Grey - unknown status

    def _compute_days_since_last_service(self):
        """Calculate days since last service"""
        from datetime import datetime

        for record in self:
            if record.last_service_date:
                delta = datetime.now() - record.last_service_date
                record.days_since_last_service = delta.days
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.days_since_last_service = 0

    def _compute_billing_period_services(self):
        """Count services in current billing period"""
        from datetime import datetime

        # Get current month start (can be enhanced with actual billing period logic)
        today = datetime.now()
        month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        for record in self:
            services_this_period = record.shredding_service_ids.filtered(
                lambda s: s.service_date and s.service_date >= month_start.date()
            )
            record.current_billing_period_services = len(services_this_period)

    # ============================================================================
    # ENHANCED CAPACITY & EFFICIENCY COMPUTE METHODS
    # ============================================================================
    @api.depends("current_fill_level", "days_since_last_service", "service_count")
    def _compute_capacity_utilization_rating(self):
        """Rate capacity utilization efficiency"""
        for record in self:
            # High fill level with infrequent service = overutilized
            if record.current_fill_level >= 90 and record.days_since_last_service > 21:
                record.capacity_utilization_rating = "critical"
            elif (
                record.current_fill_level >= 75 and record.days_since_last_service > 14
            ):
            pass
                record.capacity_utilization_rating = "overutilized"
            elif record.current_fill_level < 30 and record.days_since_last_service > 45:
            pass
                record.capacity_utilization_rating = "underutilized"
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                record.capacity_utilization_rating = "optimal"

    @api.depends("bin_size", "service_count", "days_since_last_service")
    def _compute_service_recommendations(self):
        """Compute AI-recommended service frequency"""
        for record in self:
            record.recommended_service_frequency = (
                record.get_service_frequency_recommendation()
            )

    @api.depends("bin_size")
    def _compute_monthly_metrics(self):
        """Compute monthly capacity metrics"""
        for record in self:
            monthly_data = record.calculate_monthly_capacity()
            record.monthly_capacity_lbs = monthly_data["monthly_lbs"]

    @api.depends("bin_size", "service_count", "days_since_last_service")
    def _compute_cost_efficiency_rating(self):
        """Compute cost efficiency rating"""
        for record in self:
            efficiency_data = record.calculate_cost_efficiency()
            rating_map = {
                "Excellent": "excellent",
                "Good": "good",
                "Fair": "fair",
                "Poor - Consider Upsize": "poor",
            }
            record.cost_efficiency_rating = rating_map.get(
                efficiency_data["efficiency_rating"], "fair"
            )

    @api.depends("bin_size")
    def _compute_bin_specifications(self):
        """Compute detailed bin specifications text"""
        for record in self:
            specs = record.get_bin_specifications()
            record.bin_specifications = f"""
{specs['name']}
Capacity: {specs['capacity']} lbs ({specs['capacity_range']})
Typical Use: {specs['typical_use']}
Notes: {specs['notes']}
            """.strip()

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("capacity_pounds")
    def _check_capacity(self):
        """Validate bin capacity is positive"""
        for record in self:
            if record.capacity_pounds <= 0:
                raise ValidationError("Bin capacity must be greater than zero")

    @api.constrains("current_fill_level")
    def _check_fill_level(self):
        """Validate fill level percentage is within valid range"""
        for record in self:
            if record.current_fill_level < 0 or record.current_fill_level > 100:
                raise ValidationError("Fill level percentage must be between 0 and 100")

    @api.constrains("name")
    def _check_unique_name(self):
        """Ensure bin numbers are unique per company"""
        for record in self:
            if record.name:
                existing = self.search(
                    [
                        ("name", "=", record.name),
                        ("company_id", "=", record.company_id.id),
                        ("id", "!=", record.id),
                    ]
                )
                if existing:
                    raise ValidationError(
                        f"Shred bin number '{record.name}' already exists in this company"
                    )

    @api.constrains("bin_size")
    def _check_valid_bin_size(self):
        """Validate bin size matches company standards"""
        valid_sizes = ["23", "3B", "3C", "64", "96"]
        for record in self:
            if record.bin_size and record.bin_size not in valid_sizes:
                raise ValidationError(
                    f"Invalid bin size '{record.bin_size}'. "
                    f"Valid sizes are: {', '.join(valid_sizes)}"
                )

    @api.constrains("bin_size", "partner_id")
    def _validate_bin_capacity_for_customer(self):
        """Business rule validation for bin size appropriateness"""
        for record in self:
            if record.bin_size and record.partner_id:
                # Get customer's other bins for comparison
                customer_bins = self.search(
                    [
                        ("partner_id", "=", record.partner_id.id),
                        ("id", "!=", record.id),
                        ("state", "in", ["in_service", "full"]),
                    ]
                )

                # Warn if customer is getting a bin size that seems inappropriate
                # based on their existing service patterns
                if customer_bins and record.bin_size == "96":
                    # Check if customer has history of underutilizing smaller bins
                    underutilized_bins = customer_bins.filtered(
                        lambda b: b.capacity_utilization_rating == "underutilized"
                    )
                    if len(underutilized_bins) > len(customer_bins) / 2:
                        # More than half of customer's bins are underutilized
                        # This is a warning, not an error - business decision
                        record.message_post(
                            body=_("Warning: Customer has %slen(underutilized_bins) underutilized bins. ", len(underutilized_bins))
                            f"Consider reviewing bin sizing strategy before deploying 96-gallon bin.",
                            message_type="notification",
                        )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_deploy(self):
        """Deploy the bin to customer location"""
        self.ensure_one()
        if self.state != "deployed":
            raise ValidationError("Bin must be in deployed state")

        self.write({"state": "in_service"})

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Shred bin %sself.name deployed to %sself.partner_id.name", self.name, self.partner_id.name),
            message_type="notification",
        )

    def action_mark_full(self):
        """Mark bin as full and needing collection"""
        self.ensure_one()
        if self.state != "in_service":
            raise ValidationError("Only in-service bins can be marked as full")

        self.write({"state": "full"})

        # Create automatic pickup request
        self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "shred_bin_id": self.id,
                "request_type": "shredding",
                "urgency": "high" if self.current_fill_level >= 95 else "medium",
                "notes": f"Automatic pickup request for full shred bin {self.name}",
            }
        )

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Shred bin %sself.name marked as full - pickup request created", self.name),
            message_type="notification",
        )

    def action_start_collection(self):
        """Mark bin as being collected"""
        self.ensure_one()
        if self.state != "full":
            raise ValidationError("Only full bins can be collected")

        self.write({"state": "collecting"})

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Collection started for shred bin %sself.name", self.name),
            message_type="notification",
        )

    def action_complete_service(self):
        """Complete service and return bin to service"""
        self.ensure_one()
        if self.state != "collecting":
            raise ValidationError("Only bins being collected can complete service")

        self.write({"state": "in_service"})

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Service completed for shred bin %sself.name - returned to service", self.name),
            message_type="notification",
        )

    def action_customer_mark_full(self):
        """Customer portal action to mark bin as full"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_portal"):
            raise ValidationError("This action is only available to portal users")

        if self.state != "in_service":
            raise ValidationError(
                "Only in-service bins can be marked as full by customers"
            )

        # Check if user has access to this bin (same partner)
        if self.partner_id.id != self.env.user.partner_id.commercial_partner_id.id:
            raise ValidationError("You can only mark your own bins as full")

        self.write({"state": "full"})

        # Create automatic pickup request
        pickup_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "shred_bin_id": self.id,
                "request_type": "shredding",
                "urgency": "high" if self.current_fill_level >= 95 else "medium",
                "notes": f"Customer-requested pickup for full shred bin {self.name}",
                "requested_by_customer": True,
            }
        )

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Bin marked as full by customer - pickup request %spickup_request.name created", pickup_request.name),
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Collection Requested",
                "message": f"Your bin {self.name} has been marked for collection. We'll schedule pickup within 24-48 hours.",
                "type": "success",
                "sticky": True,
            },
        }

    def action_request_upsize(self):
        """Customer portal action to request larger bin"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_portal"):
            raise ValidationError("This action is only available to portal users")

        # Check if user has access to this bin
        if self.partner_id.id != self.env.user.partner_id.commercial_partner_id.id:
            raise ValidationError("You can only request changes for your own bins")

        # Business rule: 96 gallon bins cannot be upsized - offer additional bins instead
        if self.bin_size == "96":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Additional Bins Available",
                    "message": f"Your 96-gallon bin {self.name} is already our largest size. Would you like to request additional bins instead?",
                    "type": "info",
                    "sticky": True,
                },
            }

        # Determine next size up based on actual company item codes
        size_hierarchy = {
            "23": ("3B", "32 GALLON BIN"),  # 23 gallon → 32 gallon bin
            "3B": ("64", "64 GALLON BIN"),  # 32 gallon bin → 64 gallon
            "3C": ("64", "64 GALLON BIN"),  # 32 gallon console → 64 gallon
            "64": ("96", "96 GALLON BIN"),  # 64 gallon → 96 gallon
        }

        if self.bin_size not in size_hierarchy:
            raise ValidationError("Unable to determine upsize option for this bin")

        new_size_code, new_size_name = size_hierarchy[self.bin_size]

        # Create service request
        service_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "shred_bin_id": self.id,
                "request_type": "bin_replacement",
                "urgency": "normal",
                "notes": f"Customer-requested bin upsize from {self.bin_size} to {new_size_code} for bin {self.name}",
                "requested_by_customer": True,
                "special_instructions": f"Upsize request: Replace {self.bin_size} bin with {new_size_code} ({new_size_name})",
            }
        )

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Customer requested upsize from %sself.bin_size to %snew_size_code - service request %sservice_request.name created", self.bin_size, new_size_code, service_request.name),
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Upsize Request Submitted",
                "message": f"Your request to upgrade bin {self.name} from {self.bin_size} to {new_size_name} has been submitted. Our team will contact you to schedule the swap.",
                "type": "success",
                "sticky": True,
            },
        }

    def action_request_downsize(self):
        """Customer portal action to request smaller bin"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_portal"):
            raise ValidationError("This action is only available to portal users")

        # Check if user has access to this bin
        if self.partner_id.id != self.env.user.partner_id.commercial_partner_id.id:
            raise ValidationError("You can only request changes for your own bins")

        # Business rule: 23 gallon bins cannot be downsized - they're the smallest
        if self.bin_size == "23":
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "Minimum Size Reached",
                    "message": f"Your 23-gallon bin {self.name} is already our smallest size. Please contact customer service for special arrangements.",
                    "type": "warning",
                    "sticky": True,
                },
            }

        # Determine next size down based on actual company item codes
        downsize_hierarchy = {
            "96": ("64", "64 GALLON BIN"),  # 96 gallon → 64 gallon
            "64": (
                "3C",
                "32 GALLON CONSOLE",
            ),  # 64 gallon → 32 gallon console (most common)
            "3B": ("23", "23 GALLON SHREDINATOR"),  # 32 gallon bin → 23 gallon
            "3C": ("23", "23 GALLON SHREDINATOR"),  # 32 gallon console → 23 gallon
        }

        if self.bin_size not in downsize_hierarchy:
            raise ValidationError("Unable to determine downsize option for this bin")

        new_size_code, new_size_name = downsize_hierarchy[self.bin_size]

        # Create service request
        service_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "shred_bin_id": self.id,
                "request_type": "bin_replacement",
                "urgency": "normal",
                "notes": f"Customer-requested bin downsize from {self.bin_size} to {new_size_code} for bin {self.name}",
                "requested_by_customer": True,
                "special_instructions": f"Downsize request: Replace {self.bin_size} bin with {new_size_code} ({new_size_name})",
            }
        )

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Customer requested downsize from %sself.bin_size to %snew_size_code - service request %sservice_request.name created", self.bin_size, new_size_code, service_request.name),
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Downsize Request Submitted",
                "message": f"Your request to downgrade bin {self.name} from {self.bin_size} to {new_size_name} has been submitted. Our team will contact you to schedule the swap.",
                "type": "success",
                "sticky": True,
            },
        }

    def action_analyze_capacity_efficiency(self):
        """Open detailed capacity efficiency analysis"""
        self.ensure_one()

        specs = self.get_bin_specifications()
        monthly_metrics = self.calculate_monthly_capacity()
        cost_metrics = self.calculate_cost_efficiency()
        upsize_recommendations = self.get_upsize_recommendations()

        message = f"""
CAPACITY EFFICIENCY ANALYSIS - Bin {self.name}

CURRENT SPECIFICATIONS:
• Bin Type: {specs['name']}
• Capacity: {specs['capacity']} lbs ({specs['capacity_range']})
• Current Fill Level: {self.current_fill_level}%
• Estimated Weight: {self.estimated_weight:.1f} lbs

MONTHLY METRICS:
• Theoretical Capacity: {monthly_metrics['monthly_lbs']} lbs/month
• Services per Month: {monthly_metrics['services_per_month']}
• Cost Efficiency: {cost_metrics['efficiency_rating']}
• Cost per Pound: ${cost_metrics['cost_per_lb']:.3f}

SERVICE ANALYSIS:
• Days Since Last Service: {self.days_since_last_service}
• Total Services: {self.service_count}
• Recommended Frequency: {self.recommended_service_frequency}
• Capacity Rating: {self.capacity_utilization_rating.replace('_', ' ').title()}

RECOMMENDATIONS:
"""

        for rec in upsize_recommendations:
            if rec.get("recommended_size") != "Current size optimal":
                message += f"• {rec['recommended_size']}: {rec['justification']}\n"
                message += (
                    f"  Capacity Increase: {rec.get('capacity_increase', 'N/A')}\n"
                )
                message += f"  Estimated Savings: {rec['estimated_savings']}\n\n"
            else:
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
            pass
                message += "• Current bin size is optimal for usage patterns\n"

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"Capacity Analysis - Bin {self.name}",
                "message": message,
                "type": "info",
                "sticky": True,
            },
        }

    def action_smart_upsize_recommendation(self):
        """Smart upsize with automatic bin size selection"""
        self.ensure_one()

        recommendations = self.get_upsize_recommendations()

        if (
            not recommendations
            or recommendations[0].get("recommended_size") == "Current size optimal"
        ):
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": "No Upsize Needed",
                    "message": f"Bin {self.name} is optimally sized for current usage patterns.",
                    "type": "success",
                },
            }

        # Get the primary recommendation
        primary_rec = recommendations[0]
        recommended_size = primary_rec["recommended_size"]

        if recommended_size == "Additional 96-gallon bins":
            return self.action_request_additional_bins()

        # Create upsize request with detailed business justification
        service_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "shred_bin_id": self.id,
                "request_type": "bin_replacement",
                "urgency": (
                    "high"
                    if self.capacity_utilization_rating == "critical"
                    else "normal"
                ),
                "notes": f"Smart upsize recommendation: {primary_rec['justification']}",
                "special_instructions": f"""
INTELLIGENT UPSIZE REQUEST

Current Bin: {self.name} ({self.bin_size})
Current Capacity: {primary_rec.get('current_capacity', 'Unknown')} lbs
Recommended Size: {recommended_size}
New Capacity: {primary_rec['new_capacity']} lbs
Capacity Increase: {primary_rec.get('capacity_increase', 'N/A')}

Business Justification: {primary_rec['justification']}
Expected Benefits: {primary_rec['estimated_savings']}

Efficiency Metrics:
- Current Fill Level: {self.current_fill_level}%
- Days Since Last Service: {self.days_since_last_service}
- Capacity Rating: {self.capacity_utilization_rating.replace('_', ' ').title()}
- Service Count: {self.service_count}
            """,
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Smart Upsize Request Created",
                "message": f"Upsize request {service_request.name} created for bin {self.name}. "
                f"Upgrading from {self.bin_size} to {recommended_size} "
                f"({primary_rec.get('capacity_increase', 'N/A')} capacity increase).",
                "type": "success",
                "sticky": True,
            },
        }

    def action_schedule_pickup(self):
        """Create a pickup request for this bin"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Schedule Pickup for Bin {self.name}",
            "res_model": "pickup.request",
            "view_mode": "form",
            "context": {
                "default_partner_id": self.partner_id.id,
                "default_shred_bin_id": self.id,
                "default_request_type": "shredding",
            },
            "target": "new",
        }

    def action_view_services(self):
        """View shredding services for this bin"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": f"Services for Bin {self.name}",
            "res_model": "shredding.service",
            "view_mode": "tree,form",
            "domain": [("shred_bin_id", "=", self.id)],
            "context": {"default_shred_bin_id": self.id},
            "target": "current",
        }

    def action_request_additional_bins(self):
        """Customer portal action to request additional bins (enhanced with capacity analysis)"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_portal"):
            raise ValidationError("This action is only available to portal users")

        # Check if user has access to this bin
        if self.partner_id.id != self.env.user.partner_id.commercial_partner_id.id:
            raise ValidationError("You can only request changes for your own bins")

        # Enhanced analysis for additional bin requests
        specs = self.get_bin_specifications()
        monthly_metrics = self.calculate_monthly_capacity()

        # Create service request for additional bins with detailed analysis
        service_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "request_type": "service_call",
                "urgency": "normal",
                "notes": f"Customer-requested additional bins. Current bin {self.name} ({self.bin_size}) at capacity",
                "requested_by_customer": True,
                "special_instructions": f"""
ADDITIONAL BIN REQUEST - CAPACITY ANALYSIS

Current Bin Analysis:
- Bin: {self.name} ({specs['name']})
- Current Capacity: {specs['capacity']} lbs
- Monthly Capacity: {monthly_metrics['monthly_lbs']} lbs
- Fill Level: {self.current_fill_level}%
- Days Since Service: {self.days_since_last_service}

Customer Request: Additional bins needed for increased document volume
Justification: Current {self.bin_size} bin at maximum capacity, additional bins needed for continued service efficiency

Recommendation: Deploy additional {self.bin_size} bins to maintain optimal service frequency
            """,
            }
        )

        # Log activity
        self.message_post(body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))body=_("Action completed"))
            body=_("Customer requested additional bins - service request %sservice_request.name created with capacity analysis", service_request.name),
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Additional Bins Request Submitted",
                "message": f"Your request for additional bins has been submitted with capacity analysis. "
                f"Current {specs['name']} at {self.current_fill_level}% capacity. "
                f"Our sales team will contact you to discuss options and pricing.",
                "type": "success",
                "sticky": True,
            },
        }

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_capacity_status(self):
        """Get human-readable capacity status"""
        self.ensure_one()
        if self.current_fill_level < 25:
            return "Low"
        elif self.current_fill_level < 75:
            pass
            return "Medium"
        elif self.current_fill_level < 90:
            pass
            return "High"
        else:
            pass
            pass
            pass
            return "Full"

    def get_bin_specifications(self):
        """Get detailed bin specifications including capacity ranges"""
        self.ensure_one()

        # Industry data with ranges and notes
        specifications = {
            "23": {
                "name": "23 Gallon Shredinator",
                "capacity": 60,
                "capacity_range": "Exactly 60 lbs",
                "notes": "Slim, desk-side container. HSM Shredinator model standard.",
                "typical_use": "Personal offices, small businesses",
            },
            "3B": {
                "name": "32 Gallon Bin",
                "capacity": 125,
                "capacity_range": "100-125 lbs",
                "notes": "Medium-sized bins, rated around 100 lbs minimum, up to 125 lbs for HSM models.",
                "typical_use": "Medium offices, departments",
            },
            "3C": {
                "name": "32 Gallon Console",
                "capacity": 90,
                "capacity_range": "60-120 lbs",
                "notes": "Executive console design. Varies by model: 60-80 lbs basic, up to 120 lbs premium.",
                "typical_use": "Executive offices, secure reception areas",
            },
            "64": {
                "name": "64 Gallon Bin",
                "capacity": 240,
                "capacity_range": "200-250 lbs",
                "notes": "Large rolling bins. 225 lbs (Access), 250 lbs (HSM/ShredSmart).",
                "typical_use": "Large offices, departments, warehouses",
            },
            "96": {
                "name": "96 Gallon Bin",
                "capacity": 340,
                "capacity_range": "300-350 lbs",
                "notes": "Largest standard size. 300 lbs (Shred Truck) to 350 lbs (ShredSmart/Legal Shred).",
                "typical_use": "Large facilities, high-volume document generation",
            },
        }

        return specifications.get(
            self.bin_size,
            {
                "name": "Unknown Bin Size",
                "capacity": 90,
                "capacity_range": "Unknown",
                "notes": "Bin size not recognized",
                "typical_use": "Unknown",
            },
        )

    def get_service_frequency_recommendation(self):
        """Recommend service frequency based on bin size and usage patterns"""
        self.ensure_one()

        # Base recommendations per bin size
        frequency_map = {
            "23": "Weekly or Bi-weekly",  # Small bins fill quickly
            "3B": "Bi-weekly to Monthly",  # Medium capacity
            "3C": "Bi-weekly to Monthly",  # Medium capacity, secure location
            "64": "Monthly to Bi-monthly",  # Large capacity
            "96": "Monthly to Quarterly",  # Largest capacity
        }

        base_frequency = frequency_map.get(self.bin_size, "Monthly")

        # Adjust based on historical data if available
        if self.service_count > 3:
            avg_days = self.days_since_last_service / max(1, self.service_count)
            if avg_days < 14:
                return f"{base_frequency} (High Usage - Consider Upsize)"
            elif avg_days > 60:
            pass
                return f"{base_frequency} (Low Usage - Consider Downsize)"

        return base_frequency

    def calculate_monthly_capacity(self):
        """Calculate theoretical monthly paper processing capacity"""
        self.ensure_one()

        # Estimate based on bin size and typical usage
        specs = self.get_bin_specifications()
        capacity_lbs = specs["capacity"]

        # Typical service frequencies (times per month)
        service_frequency_map = {
            "23": 3,  # Weekly/bi-weekly = ~3 times/month
            "3B": 2,  # Bi-weekly = 2 times/month
            "3C": 2,  # Bi-weekly = 2 times/month
            "64": 1,  # Monthly = 1 time/month
            "96": 0.5,  # Bi-monthly = 0.5 times/month
        }

        services_per_month = service_frequency_map.get(self.bin_size, 1)
        monthly_capacity = capacity_lbs * services_per_month

        return {
            "monthly_lbs": monthly_capacity,
            "services_per_month": services_per_month,
            "capacity_per_service": capacity_lbs,
        }

    def get_upsize_recommendations(self):
        """Get intelligent upsize recommendations with business justification"""
        self.ensure_one()

        current_specs = self.get_bin_specifications()

        # Service frequency analysis
        if self.service_count > 2:
            avg_days_between_service = 30  # Default assumption
            if self.last_service_date:
                from datetime import datetime

                days_since = (datetime.now().date() - self.last_service_date).days
                avg_days_between_service = days_since / max(1, self.service_count)
        else:
            pass
            pass
            pass
            avg_days_between_service = 30

        recommendations = []

        # High-frequency service recommendation
        if avg_days_between_service < 14:
            if self.bin_size == "23":
                recommendations.append(
                    {
                        "recommended_size": "3C",
                        "new_capacity": 90,
                        "capacity_increase": "50%",
                        "current_capacity": current_specs["capacity"],
                        "justification": "High service frequency suggests need for larger capacity",
                        "estimated_savings": "Reduce service calls by 40-50%",
                    }
                )
            elif self.bin_size == "3B":
            pass
                recommendations.append(
                    {
                        "recommended_size": "64",
                        "new_capacity": 240,
                        "capacity_increase": "92%",
                        "current_capacity": current_specs["capacity"],
                        "justification": "Bi-weekly service pattern indicates outgrowing current bin",
                        "estimated_savings": "Reduce to monthly service calls",
                    }
                )
            elif self.bin_size == "3C":
            pass
                recommendations.append(
                    {
                        "recommended_size": "64",
                        "new_capacity": 240,
                        "capacity_increase": "167%",
                        "current_capacity": current_specs["capacity"],
                        "justification": "Console usage exceeding capacity, rolling bin provides efficiency",
                        "estimated_savings": "Reduce service frequency by 60%",
                    }
                )
            elif self.bin_size == "64":
            pass
                recommendations.append(
                    {
                        "recommended_size": "96",
                        "new_capacity": 340,
                        "capacity_increase": "42%",
                        "current_capacity": current_specs["capacity"],
                        "justification": "Large bin reaching capacity quickly, upgrade to maximum size",
                        "estimated_savings": "Reduce to quarterly service calls",
                    }
                )

        # Multiple bin recommendation for 96-gallon
        if self.bin_size == "96" and avg_days_between_service < 21:
            recommendations.append(
                {
                    "recommended_size": "Additional 96-gallon bins",
                    "new_capacity": 340,
                    "capacity_increase": "100% per additional bin",
                    "current_capacity": current_specs["capacity"],
                    "justification": "Maximum single bin size reached, additional bins needed",
                    "estimated_savings": "Maintain optimal service frequency with increased total capacity",
                }
            )

        return (
            recommendations
            if recommendations
            else [
                {
                    "recommended_size": "Current size optimal",
                    "current_capacity": current_specs["capacity"],
                    "justification": "Service frequency indicates proper bin sizing",
                    "estimated_savings": "No change recommended",
                }
            ]
        )

    def calculate_cost_efficiency(self):
        """Calculate cost efficiency metrics for pricing and sales analysis"""
        self.ensure_one()

        specs = self.get_bin_specifications()
        monthly_capacity = self.calculate_monthly_capacity()

        # Estimated cost per pound (this would typically come from pricing models)
        # These are example values - should be integrated with actual pricing system
        base_cost_per_service = {
            "23": 25,  # Smaller bins, lower service cost
            "3B": 35,  # Medium bins
            "3C": 40,  # Console bins (premium for security)
            "64": 50,  # Large bins
            "96": 65,  # Largest bins, highest service cost
        }

        service_cost = base_cost_per_service.get(self.bin_size, 40)
        monthly_services = monthly_capacity["services_per_month"]
        monthly_cost = service_cost * monthly_services
        cost_per_lb = (
            monthly_cost / monthly_capacity["monthly_lbs"]
            if monthly_capacity["monthly_lbs"] > 0
            else 0
        )

        return {
            "service_cost": service_cost,
            "monthly_services": monthly_services,
            "monthly_cost": monthly_cost,
            "monthly_capacity_lbs": monthly_capacity["monthly_lbs"],
            "cost_per_lb": round(cost_per_lb, 3),
            "efficiency_rating": self._calculate_efficiency_rating(cost_per_lb),
            "bin_specs": specs,
        }

    def _calculate_efficiency_rating(self, cost_per_lb):
        """Calculate efficiency rating based on cost per pound"""
        if cost_per_lb < 0.15:
            return "Excellent"
        elif cost_per_lb < 0.25:
            pass
            return "Good"
        elif cost_per_lb < 0.40:
            pass
            return "Fair"
        else:
            pass
            pass
            pass
            return "Poor - Consider Upsize"

    # ============================================================================
    # FIELD SERVICE OPERATIONS (Advanced Bin Management)
    # ============================================================================

    def action_swap_bin(self, new_bin_id):
        """Swap full bin with empty bin - charges only for new bin service"""
        self.ensure_one()
        if not new_bin_id:
            raise ValidationError("New bin must be specified for swap operation")

        new_bin = self.env["shred.bin"].browse(new_bin_id)
        if not new_bin.exists():
            raise ValidationError("New bin not found")

        if new_bin.partner_id != self.partner_id:
            raise ValidationError("Bins must belong to the same customer for swap")

        # Mark current bin as collected (orange - in transit)
        self.write({"state": "collecting", "location_status": "in_transit"})

        # Deploy new bin at customer location (green - in service)
        new_bin.write(
            {
                "state": "in_service",
                "customer_location": self.customer_location,
                "location_status": "at_customer",
            }
        )

        # Create single service record for the new bin deployment
        service = self.env["shredding.service"].create(
            {
                "partner_id": self.partner_id.id,
                "service_type": "swap",
                "material_type": "paper",
                "shred_bin_id": new_bin.id,  # Charges for new bin only
                "notes": f"Bin swap: {self.name} (full) replaced with {new_bin.name} (empty)",
                "state": "completed",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Bin Swap Completed",
                "message": f"Bin {self.name} collected, {new_bin.name} deployed. Service: {service.name}",
                "type": "success",
            },
        }

    def action_upsize_bin(self, new_bin_id):
        """Replace smaller bin with larger bin"""
        self.ensure_one()
        new_bin = self.env["shred.bin"].browse(new_bin_id)

        # Validate bin sizes
        size_order = {"small": 1, "medium": 2, "large": 3, "console": 4}
        if size_order.get(new_bin.bin_size, 0) <= size_order.get(self.bin_size, 0):
            raise ValidationError(
                "New bin must be larger than current bin for upsize operation"
            )

        return self._resize_bin(new_bin, "upsize")

    def action_downsize_bin(self, new_bin_id):
        """Replace larger bin with smaller bin"""
        self.ensure_one()
        new_bin = self.env["shred.bin"].browse(new_bin_id)

        # Validate bin sizes
        size_order = {"small": 1, "medium": 2, "large": 3, "console": 4}
        if size_order.get(new_bin.bin_size, 0) >= size_order.get(self.bin_size, 0):
            raise ValidationError(
                "New bin must be smaller than current bin for downsize operation"
            )

        return self._resize_bin(new_bin, "downsize")

    def _resize_bin(self, new_bin, operation_type):
        """Common logic for upsize/downsize operations"""
        # Remove old bin
        self.write({"state": "collecting", "location_status": "in_transit"})

        # Deploy new sized bin
        new_bin.write(
            {
                "state": "in_service",
                "customer_location": self.customer_location,
                "location_status": "at_customer",
            }
        )

        # Create service record for new bin deployment (charges for new bin rate)
        service = self.env["shredding.service"].create(
            {
                "partner_id": self.partner_id.id,
                "service_type": operation_type,
                "material_type": "paper",
                "shred_bin_id": new_bin.id,  # Charges for new bin size
                "notes": f"Bin {operation_type}: {self.name} ({self.bin_size}) replaced with {new_bin.name} ({new_bin.bin_size})",
                "state": "completed",
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": f"Bin {operation_type.title()} Completed",
                "message": f"Bin {operation_type}: {self.name} → {new_bin.name}. Service: {service.name}",
                "type": "success",
            },
        }
