# -*- coding: utf-8 -*-
"""
Document Retrieval Item Model

Individual items in a document retrieval work order with detailed tracking
and quality control capabilities.
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class DocumentRetrievalItem(models.Model):
    """Individual items in a document retrieval work order"""

    _name = "document.retrieval.item"
    _description = "Document Retrieval Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "work_order_id, sequence"
    _rec_name = "description"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Reference", required=True, tracking=True, index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True,)

    # ============================================================================
    # WORK ORDER RELATIONSHIP FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(
        "file.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # DOCUMENT REFERENCE FIELDS
    # ============================================================================
    document_id = fields.Many2one("records.document", string="Document"),
    container_id = fields.Many2one("records.container", string="Container"),
    location_id = fields.Many2one("records.location", string="Storage Location"),

    item_type = fields.Selection(
        [
            ("document", "Single Document"),
            ("folder", "Document Folder"),
            ("container", "Full Container"),
            ("box", "Storage Box"),
        ],
        string="Item Type",
        required=True,
        default="document",
    )

    description = fields.Text(string="Item Description"),
    barcode = fields.Char(string="Barcode/ID", tracking=True,)

    # ============================================================================
    # STATUS TRACKING FIELDS
    # ============================================================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("searching", "Searching"),  # Added missing status
            ("located", "Located"),
            ("retrieved", "Retrieved"),
            ("packaged", "Packaged"),  # Added missing status
            ("scanned", "Scanned"),
            ("delivered", "Delivered"),
            ("returned", "Returned"),  # Added missing status
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # LOCATION AND SEARCH FIELDS
    # ============================================================================
    current_location = fields.Char(string="Current Location"),
    storage_location_id = fields.Many2one("records.location", string="Storage Location")

    # Search container tracking
    searched_container_ids = fields.Many2many(
        "records.container",
        "retrieval_item_container_rel",
        "item_id",
        "container_id",
        string="Searched Containers",
    )

    containers_accessed_count = fields.Integer(
        string="Containers Accessed",
        compute="_compute_containers_accessed_count",
        store=True,
    )

    containers_not_found_count = fields.Integer(
        string="Containers Not Found",
        compute="_compute_containers_not_found_count", 
        store=True,
    )

    # File request information
    requested_file_name = fields.Char(string="Requested File Name")

    # ============================================================================
    # EFFORT TRACKING FIELDS
    # ============================================================================
    estimated_time = fields.Float(string="Estimated Time (hours)", digits=(5, 2))
    actual_time = fields.Float(string="Actual Time (hours)", digits=(5, 2))
    difficulty_level = fields.Selection(
        [
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
            ("very_hard", "Very Hard"),
        ],
        string="Difficulty",
        default="medium",
    )

    # ============================================================================
    # PROCESSING DETAILS FIELDS
    # ============================================================================
    retrieval_date = fields.Datetime(string="Retrieved Date", tracking=True,),
    retrieved_by_id = fields.Many2one("res.users", string="Retrieved By")  # Fixed to res.users
    condition_notes = fields.Text(string="Condition Notes"),
    special_handling = fields.Boolean(string="Special Handling Required", default=False)

    # ============================================================================
    # QUALITY CONTROL FIELDS
    # ============================================================================
    quality_checked = fields.Boolean(string="Quality Checked", default=False),
    quality_issues = fields.Text(string="Quality Issues"),
    completeness_verified = fields.Boolean(
        string="Completeness Verified", default=False
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # Search Results and History
    search_attempt_ids = fields.One2many(
        "document.search.attempt",
        "retrieval_item_id",
        string="Search Attempts",
        help="History of all search attempts for this file",
    )

    total_search_attempts = fields.Integer(
        string="Total Search Attempts",
        compute="_compute_total_search_attempts",
        store=True,
    )

    # Not Found Tracking
    not_found_reason = fields.Selection(
        [
            ("not_in_container", "File not in searched containers"),
            ("mislabeled", "File may be mislabeled"),
            ("damaged", "File damaged/destroyed"),
            ("misfiled", "File filed in wrong location"),
            ("customer_error", "Customer provided incorrect information"),
            ("other", "Other reason"),
        ],
        string="Not Found Reason",
        help="Reason why file was not found",
    )

    not_found_notes = fields.Text(
        string="Not Found Notes",
        help="Detailed notes about the search process and why file wasn't found",
    )

    # File Discovery and Barcoding
    file_discovered = fields.Boolean(
        string="File Discovered During Search",
        default=False,
        help="File was found and barcoded during the search process",
    )

    discovery_date = fields.Datetime(
        string="Discovery Date",
        help="Date when file was discovered and barcoded",
    )

    discovery_container_id = fields.Many2one(
        "records.container",
        string="Discovery Container",
        help="Container where file was actually found",
    )

    # Retrieval Notes
    retrieval_notes = fields.Text(string="Retrieval Notes")

    # === CUSTOMER RELATIONSHIP ===
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        readonly=True,
    )

    # Handling Instructions
    handling_instructions = fields.Text(string="Handling Instructions"),
    fragile = fields.Boolean(string="Fragile Item", default=False)

    # Physical Attributes
    estimated_weight = fields.Float(
        string="Estimated Weight (kg)", digits="Product Price"
        )
    actual_weight = fields.Float(
        string="Actual Weight (kg)", digits="Product Unit of Measure"
        )
    dimensions = fields.Char(string="Dimensions (LxWxH)")

    # Security and Access
    security_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("classified", "Classified"),
        ],
        string="Security Level",
        default="standard",
    )

    access_authorized_by_id = fields.Many2one("res.users", string="Access Authorized By"),
    authorization_date = fields.Datetime(string="Authorization Date")

    # Condition and Quality
    condition_before = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Condition Before",
        default="good",
    )

    condition_after = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Condition After",
    )

    # Digital Processing
    scan_required = fields.Boolean(string="Scan Required", default=False),
    scan_completed = fields.Boolean(string="Scan Completed", default=False),
    digital_format = fields.Selection(
        [("pdf", "PDF"), ("jpg", "JPEG"), ("tiff", "TIFF"), ("png", "PNG")],
        string="Digital Format",
        default="pdf",
    )

    scan_quality = fields.Selection(
        [
            ("draft", "Draft (150 DPI)"),
            ("standard", "Standard (300 DPI)"),
            ("high", "High (600 DPI)"),
            ("archive", "Archive (1200 DPI)"),
        ],
        string="Scan Quality",
        default="standard",
    )

    # Return Information
    return_required = fields.Boolean(string="Return Required", default=True),
    return_date = fields.Date(string="Return Date"),
    return_location_id = fields.Many2one("records.location", string="Return Location"),
    return_notes = fields.Text(string="Return Notes")

    # Cost and Billing - ENHANCED for container access billing
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost",
        currency_field="currency_id",
        compute="_compute_retrieval_cost",
        store=True,
        help="Cost to retrieve this specific item (dynamic based on customer rates)",
        )

    container_access_cost = fields.Monetary(
        string="Container Access Cost",
        currency_field="currency_id",
        compute="_compute_container_access_cost",
        store=True,
        help="Cost for accessing containers where file was NOT found (excludes successful retrieval container)",
        )

    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
        help="Total cost: retrieval fee (if found) + container access fees (unsuccessful searches) + delivery + not found fee",
        )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        required=True,
    )

    # Tracking and Audit
    tracking_number = fields.Char(string="Tracking Number"),
    audit_trail = fields.Text(string="Audit Trail")

    # === COMPUTED FIELDS ===
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    location_display = fields.Char(

    # Workflow state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string='Status', default='draft', tracking=True, required=True, index=True,
       help='Current status of the record')
        string="Location Display", compute="_compute_location_display", store=True
    )

    # === COMPUTE METHODS ===
    @api.depends("work_order_id.currency_id")
    def _compute_currency_id(self):
        for item in self:
            if item.work_order_id and item.work_order_id.currency_id:
                item.currency_id = item.work_order_id.currency_id
            else:
                item.currency_id = (
                    item.company_id.currency_id
                    if item.company_id and item.company_id.currency_id
                    else self.env.company.currency_id
                )

    @api.depends("searched_container_ids")
    def _compute_containers_accessed_count(self):
        """Count number of containers actually searched"""
        for item in self:
            item.containers_accessed_count = len(item.searched_container_ids)

    @api.depends("search_attempt_ids", "search_attempt_ids.found")
    def _compute_containers_not_found_count(self):
        """Count containers where file was NOT found (for billing purposes)"""
        for item in self:
            # Count search attempts where found = False
            unsuccessful_searches = item.search_attempt_ids.filtered(lambda x: not x.found)
            item.containers_not_found_count = len(unsuccessful_searches)

    @api.depends("search_attempt_ids")
    def _compute_total_search_attempts(self):
        """Count total number of search attempts"""
        for item in self:
            item.total_search_attempts = len(item.search_attempt_ids)

    @api.depends("partner_id", "work_order_id.partner_id", "item_type")
    def _compute_retrieval_cost(self):
        """Calculate retrieval cost using customer rates (dynamic pricing)"""
        for item in self:
            retrieval_rate = 0.0
            if item.work_order_id and item.work_order_id.customer_id:
                negotiated_rate = self.env["customer.negotiated.rates"].search(
                    [
                        ("partner_id", "=", item.work_order_id.customer_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )

                if negotiated_rate:
                    # Use the effective rate method for proper rate calculation
                    retrieval_rate = negotiated_rate.get_effective_rate(
                        "managed_retrieval_rate"
                    )
                else:
                    retrieval_rate = 0.0

            # Fall back to base rates
            base_rate = self.env["base.rate"].search(
                [
                    ("service_type", "=", "retrieval"),
                    ("state", "=", "confirmed"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ],
                order="effective_date desc",
                limit=1,
            )

            if base_rate:
                retrieval_rate = base_rate.managed_retrieval_rate or 3.50

            # Use company default rate if no rates configured
            if not retrieval_rate:
                retrieval_rate = 3.50  # Default fallback rate

            item.retrieval_cost = retrieval_rate

    @api.depends("containers_not_found_count", "partner_id", "work_order_id.partner_id")
    def _compute_container_access_cost(self):
        """Calculate cost based on unsuccessful container searches using customer rates"""
        for item in self:
            if not item.containers_not_found_count:
                item.container_access_cost = 0.0
                continue

            # Get customer's container access rate
            access_rate = 0.0
            partner = item.partner_id or (
                item.work_order_id.partner_id if item.work_order_id else False
            )

            if partner:
                # Check for negotiated rates first
                negotiated_rate = self.env["customer.negotiated.rates"].search(
                    [
                        ("partner_id", "=", partner.id),
                        ("rate_type", "=", "container_access"),
                        ("state", "=", "active"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),
                    ],
                    limit=1,
                )

                if negotiated_rate:
                    # Use the effective rate method for proper rate calculation
                    access_rate = negotiated_rate.get_effective_rate(
                        "container_access_rate"
                    )
                else:
                    # Fall back to base rates
                    base_rate = self.env["base.rate"].search(
                        [
                            ("service_type", "=", "container_access"),
                            ("state", "=", "confirmed"),
                            ("active", "=", True),
                            "|",
                            ("expiry_date", "=", False),
                            ("expiry_date", ">=", fields.Date.today()),
                        ],
                        order="effective_date desc",
                        limit=1,
                    )

                    if base_rate:
                        access_rate = base_rate.external_per_bin_rate or 3.50

            # Use company default rate if no rates configured
            if not access_rate:
                access_rate = 3.50  # Default fallback rate

            # Charge only for unsuccessful container searches
            item.container_access_cost = item.containers_not_found_count * access_rate

    @api.depends(
        "retrieval_cost",
        "container_access_cost",
        "partner_id",
        "work_order_id.partner_id",
        "work_order_id.delivery_required",
        "status",  # Added to recalculate when status changes to not_found
    )
    def _compute_total_cost(self):
        """Calculate total cost including delivery fees from rate structure"""
        for item in self:
            total = item.retrieval_cost + item.container_access_cost

            # Add delivery fee if applicable (from existing rate structure)
            if item.work_order_id and getattr(
                item.work_order_id, "delivery_required", False
            ):
                partner = item.partner_id or (
                    item.work_order_id.partner_id if item.work_order_id else False
                )
                delivery_fee = 0.0

                if partner:
                    # Check negotiated delivery rates
                    negotiated_delivery = self.env["customer.negotiated.rates"].search(
                        [
                            ("partner_id", "=", partner.id),
                            ("rate_type", "=", "delivery"),
                            ("state", "=", "active"),
                            ("active", "=", True),
                            "|",
                            ("expiry_date", "=", False),
                            ("expiry_date", ">=", fields.Date.today()),
                        ],
                        limit=1,
                    )

                    if negotiated_delivery:
                        delivery_fee = negotiated_delivery.get_effective_rate(
                            "pickup_rate"
                        )
                    else:
                        # Fall back to base delivery rate
                        base_delivery = self.env["base.rates"].search(
                            [
                                ("service_type", "=", "delivery"),
                                ("state", "=", "confirmed"),
                                ("active", "=", True),
                                "|",
                                ("expiry_date", "=", False),
                                ("expiry_date", ">=", fields.Date.today()),
                            ],
                            order="effective_date desc",
                            limit=1,
                        )

                        if base_delivery:
                            delivery_fee = base_delivery.pickup_rate or 25.00

                # Use fallback rate if none configured
                if not delivery_fee:
                    delivery_fee = 25.00

                total += delivery_fee

            # Add not found search fee if applicable
            if item.status == "not_found":
                partner = item.partner_id or (
                    item.work_order_id.partner_id if item.work_order_id else False
                )
                not_found_fee = 0.0

                if partner:
                    # Check negotiated not found rates
                    negotiated_not_found = self.env["customer.negotiated.rates"].search(
                        [
                            ("partner_id", "=", partner.id),
                            ("rate_type", "=", "not_found_search"),
                            ("state", "=", "active"),
                            ("active", "=", True),
                        ],
                        limit=1,
                    )

                    if negotiated_not_found:
                        not_found_fee = negotiated_not_found.get_effective_rate(
                            "managed_retrieval_rate"
                        )
                    else:
                        # Fall back to base not found rate
                        base_not_found = self.env["base.rates"].search(
                            [
                                ("service_type", "=", "not_found_search"),
                                ("state", "=", "confirmed"),
                                ("active", "=", True),
                            ],
                            limit=1,
                        )

                        if base_not_found:
                            not_found_fee = (
                                base_not_found.managed_retrieval_rate or 3.50
                            )

                # Use fallback rate if none configured
                if not not_found_fee:
                    not_found_fee = 3.50

                total += not_found_fee

            item.total_cost = total

    @api.depends("name", "item_type", "barcode")
    def _compute_display_name(self):
        """
        Compute display name for better identification.

        Format: "<name> (<Item Type>) [<Barcode>]"
        Example: "Invoice 2023 (File) [123456789]"
        If no name is set, defaults to "New Item".
        """
        for item in self:
            parts = []
            if item.name:
                parts.append(item.name)
            else:
                parts.append("New Item")

            if item.item_type:
                type_display = dict(item._fields["item_type"].selection).get(
                    item.item_type, item.item_type
                )
                parts.append(f"({type_display})")

            if item.barcode:
                parts.append(f"[{item.barcode}]")

            item.display_name = " ".join(parts)

    @api.depends("current_location", "storage_location_id")
    def _compute_location_display(self):
        """
        Compute user-friendly location display.

        Shows:
            - Storage location name if available.
            - Current location if storage location is not set.
            - "Location Unknown" if neither is available.
        """
        for item in self:
            if item.storage_location_id:
                item.location_display = item.storage_location_id.name
            elif item.current_location:
                item.location_display = item.current_location
            else:
                item.location_display = "Location Unknown"

    # === ONCHANGE METHODS ===

    @api.onchange("container_id")
    def _onchange_container_id(self):
        """Auto-fill location information when container is selected"""
        if self.container_id and hasattr(self.container_id, "id"):
            try:
                if hasattr(self.container_id, "current_location"):
                    self.current_location = self.container_id.current_location
                if hasattr(self.container_id, "storage_location_id"):
                    self.storage_location_id = self.container_id.storage_location_id
            except AttributeError:
                # Handle missing attributes gracefully
                _logger.warning(
                    "container_id is missing expected attributes on DocumentRetrievalItem ID %s",
                    self.id,
                )

    @api.onchange("document_id")
    def _onchange_document_id(self):
        """Auto-fill information when single document is selected"""
        if self.document_id and hasattr(self.document_id, "id"):
            try:
                container = getattr(self.document_id, "container_id", False)
                if container:
                    self.container_id = container
            except AttributeError:
                # Handle missing container_id attribute gracefully
                pass

            # Only change to document type if the current type is "file".
            # This prevents overwriting the item type for other retrieval types (e.g., "container").
            if self.item_type == "file":
                self.item_type = "document"
            # Only set name if it's currently empty to avoid overwriting custom names
            document_name = getattr(self.document_id, "name", False)
            if not self.name and document_name:
                self.name = document_name

    @api.onchange("item_type")
    def _onchange_item_type(self):
        """Clear inappropriate fields when item type changes"""
        if self.item_type in ("file", "container"):
            # For file or container retrieval, clear specific document selection
            self.document_id = False

    # === ACTION METHODS ===
    def action_locate_item(self):
        """Mark item as located.

        Side effects:
            - Updates status, retrieval date, and retrieved by fields.
            - Posts a notification message to the chatter.
        """

        self.ensure_one()
        if self.status != "pending":
            raise UserError(_("Only pending items can be located"))

        self.write(
            {
                "status": "located",
                "retrieval_date": fields.Datetime.now(),
                "retrieved_by_id": self.env.user.id,
            }
        )

        # Post a notification message to the chatter - FIXED translation
        self.message_post(
            body=_("Item located by %s", self.env.user.name),
            message_type="notification",
        )

    def action_retrieve_item(self):
        """Mark item as retrieved.

        Side effects:
            - Updates status, retrieval date, and retrieved by fields.
            - Posts a notification message to the chatter.
        """

        self.ensure_one()
        if self.status != "located":
            raise UserError(_("Item must be located before retrieval"))

        self.write(
            {
                "status": "retrieved",
                "retrieval_date": fields.Datetime.now(),
                "retrieved_by_id": self.env.user.id,
            }
        )

        # Post a notification message to the chatter - FIXED translation
        self.message_post(
            body=_("Item retrieved by %s", self.env.user.name),
            message_type="notification",
        )

    def action_package_item(self):
        """Mark item as packaged.

        Side effects:
            - Updates status field.
            - Posts a notification message to the chatter.
        """

        self.ensure_one()
        if self.status != "retrieved":
            raise UserError(_("Item must be retrieved before packaging"))

        self.write(
            {
                "status": "packaged",
                "retrieval_date": fields.Datetime.now(),
            }
        }
        # FIXED translation
        self.message_post(
            body=_("Item packaged by %s", self.env.user.name),
            message_type="notification",
        }

    def action_deliver_item(self):
        """Mark item as delivered.

        Side effects:
            - Updates status field.
            - Posts a notification message to the chatter.
        """

        self.ensure_one()
        if self.status != "packaged":
            raise UserError(_("Item must be packaged before delivery"))

        self.write({"status": "delivered"})

        # Post a notification message to the chatter - FIXED translation
        self.message_post(
            body=_("Item delivered by %s", self.env.user.name),
            message_type="notification",
        )

    def action_return_item(self):
        """Mark item as returned.

        Side effects:
            - Updates status and return date fields.
            - Posts a notification message to the chatter.
        """

        self.ensure_one()
        if self.status != "delivered":
            raise UserError(_("Item must be delivered before return"))

        self.write(
            {
                "status": "returned",
                "return_date": fields.Datetime.now(),
            }
        }
        # Post a notification message to the chatter - FIXED translation
        self.message_post(
            body=_("Item returned by %s", self.env.user.name),
            message_type="notification",
        }

    # === SEARCH WORKFLOW ACTION METHODS ===
    def action_begin_search_process(self):
        """Start the search process for this file"""

        self.ensure_one()
        if self.status != "pending":
            raise UserError(_("Only pending items can start search process"))

        self.write({"status": "searching"})
        self.message_post(
            body=_("Search started by %s for file: %s", self.env.user.name, self.requested_file_name or self.name),
            message_type="notification",
        )

    def action_record_container_search(self, container_id, found=False, notes=""):
        """Add a container to the searched list and create search attempt record"""

        self.ensure_one()

        # Add to searched containers
        if container_id not in self.searched_container_ids.ids:
            self.searched_container_ids = [(4, container_id)]

        # Create search attempt record
        search_attempt_vals = {
            "retrieval_item_id": self.id,
            "container_id": container_id,
            "searched_by_id": self.env.user.id,
            "search_date": fields.Datetime.now(),
            "found": found,
            "notes": notes,
        }
        self.env["document.search.attempt"].create(search_attempt_vals)

        if found:
            self.write(
                {
                    "status": "located",
                    "file_discovered": True,
                    "discovery_date": fields.Datetime.now(),
                    "discovery_container_id": container_id,
                    "container_id": container_id,  # Set as the official container
                }
            }

        return True

    def action_mark_not_found(self, reason="not_in_container", notes=""):
        """Mark file as not found after search completion"""

        self.ensure_one()

        # Use simple default notes if none provided
        if not notes:
            notes = "File not found"

        self.write(
            {
                "status": "not_found",
                "not_found_reason": reason,
                "not_found_notes": notes,
            }
        }

        # Create final search attempt record - FIXED translation
        reason_display = dict(self._fields["not_found_reason"].selection).get(reason, reason)
        self.message_post(
            body=_("File marked as NOT FOUND by %s. Searched %s containers (%s unsuccessful - will be charged as container access fees). Reason: %s",
                   self.env.user.name,
                   self.containers_accessed_count,
                   self.containers_not_found_count,
                   reason_display),
            message_type="notification",
        )

    def action_barcode_discovered_file(self, barcode, document_vals=None):
        """Barcode a newly discovered file and add it to the system"""

        self.ensure_one()

        if not self.file_discovered:
            raise UserError(_("File must be marked as discovered before barcoding"))

        # Update the item with barcode
        self.write(
            {
                "barcode": barcode,
                "status": "located",
            }
        }

        # Create document record if provided
        if document_vals and self.discovery_container_id:
            document_vals.update(
                {
                    "name": self.requested_file_name or self.name,
                    "barcode": barcode,
                    "container_id": self.discovery_container_id.id,
                    "partner_id": self.partner_id.id if self.partner_id else False,
                }
            }
            document = self.env["records.document"].create(document_vals)
            self.document_id = document.id

        # FIXED translation
        self.message_post(
            body=_("File barcoded by %s with barcode: %s", self.env.user.name, barcode),
            message_type="notification",
        )

        return True
