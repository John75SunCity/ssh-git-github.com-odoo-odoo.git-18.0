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
        default=50.0,
        help="Maximum weight capacity of the bin in pounds",
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
    # COMPUTE METHODS
    # ============================================================================
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
                record.can_upsize = True
                # Determine next size up
                if current_size in ["23", "3B"]:
                    record.next_size_up = "3C"  # Upgrade to console
                elif current_size == "3C":
                    record.next_size_up = "64"
                elif current_size == "64":
                    record.next_size_up = "96"
                else:
                    record.next_size_up = "3C"  # Default

            # Can downsize logic
            if current_size == "23":
                # 23 gallon is smallest - cannot downsize
                record.can_downsize = False
                record.next_size_down = False
            else:
                record.can_downsize = True
                # Determine next size down
                if current_size == "96":
                    record.next_size_down = "64"
                elif current_size == "64":
                    record.next_size_down = "3C"  # Default to console
                elif current_size == "3B":
                    record.next_size_down = "23"  # Bin to shredinator
                elif current_size == "3C":
                    record.next_size_down = "3B"  # Console to regular bin
                else:
                    record.next_size_down = "3B"  # Default

    @api.depends("state", "partner_id")
    def _compute_location_status(self):
        """Determine location status for color coding"""
        for record in self:
            if record.state == "deployed":
                record.location_status = "at_facility"  # Blue - ready for deployment
            elif record.state in ("in_service", "full"):
                record.location_status = "at_customer"  # Green/Red based on fill
            elif record.state == "collecting":
                record.location_status = "in_transit"  # Orange - being collected
            elif record.state in ("maintenance", "retired"):
                record.location_status = "at_facility"  # Purple/Grey - at facility
            else:
                record.location_status = "unknown"  # Grey - unknown status

    def _compute_days_since_last_service(self):
        """Calculate days since last service"""
        from datetime import datetime

        for record in self:
            if record.last_service_date:
                delta = datetime.now() - record.last_service_date
                record.days_since_last_service = delta.days
            else:
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
        self.message_post(
            body=f"Shred bin {self.name} deployed to {self.partner_id.name}",
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
        self.message_post(
            body=f"Shred bin {self.name} marked as full - pickup request created",
            message_type="notification",
        )

    def action_start_collection(self):
        """Mark bin as being collected"""
        self.ensure_one()
        if self.state != "full":
            raise ValidationError("Only full bins can be collected")

        self.write({"state": "collecting"})

        # Log activity
        self.message_post(
            body=f"Collection started for shred bin {self.name}",
            message_type="notification",
        )

    def action_complete_service(self):
        """Complete service and return bin to service"""
        self.ensure_one()
        if self.state != "collecting":
            raise ValidationError("Only bins being collected can complete service")

        self.write({"state": "in_service"})

        # Log activity
        self.message_post(
            body=f"Service completed for shred bin {self.name} - returned to service",
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
        self.message_post(
            body=f"Bin marked as full by customer - pickup request {pickup_request.name} created",
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
        self.message_post(
            body=f"Customer requested upsize from {self.bin_size} to {new_size_code} - service request {service_request.name} created",
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
        self.message_post(
            body=f"Customer requested downsize from {self.bin_size} to {new_size_code} - service request {service_request.name} created",
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

    def action_request_additional_bins(self):
        """Customer portal action to request additional bins (for customers with 96-gallon bins)"""
        self.ensure_one()
        if not self.env.user.has_group("base.group_portal"):
            raise ValidationError("This action is only available to portal users")

        # Check if user has access to this bin
        if self.partner_id.id != self.env.user.partner_id.commercial_partner_id.id:
            raise ValidationError("You can only request changes for your own bins")

        # Create service request for additional bins
        service_request = self.env["pickup.request"].create(
            {
                "partner_id": self.partner_id.id,
                "request_type": "service_call",
                "urgency": "normal",
                "notes": f"Customer-requested additional bins. Current bin {self.name} ({self.bin_size}) at capacity",
                "requested_by_customer": True,
                "special_instructions": f"Additional bin request: Customer needs more capacity beyond current {self.bin_size} bin",
            }
        )

        # Log activity
        self.message_post(
            body=f"Customer requested additional bins - service request {service_request.name} created",
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Additional Bins Request Submitted",
                "message": "Your request for additional bins has been submitted. Our sales team will contact you to discuss options and pricing.",
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

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_capacity_status(self):
        """Get human-readable capacity status"""
        self.ensure_one()
        if self.current_fill_level < 25:
            return "Low"
        elif self.current_fill_level < 75:
            return "Medium"
        elif self.current_fill_level < 90:
            return "High"
        else:
            return "Full"

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
