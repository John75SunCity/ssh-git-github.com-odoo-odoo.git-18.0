# -*- coding: utf-8 -*-
"""
Document Retrieval Item Model

Individual items in a document retrieval work order with detailed tracking
and quality control capabilities.
"""

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class DocumentRetrievalItem(models.Model):
    """Individual items in a document retrieval work order"""

    _name = "document.retrieval.item"
    _description = "Document Retrieval Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "work_order_id, sequence"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Item Reference", required=True, tracking=True, index=True)
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
    active = fields.Boolean(string="Active", default=True, tracking=True)

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
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High'),
    ], string="Priority", default='1', tracking=True, index=True)  # Added index=True

    # ============================================================================
    # DOCUMENT REFERENCE FIELDS
    # ============================================================================
    document_id = fields.Many2one("records.document", string="Document")
    container_id = fields.Many2one("records.container", string="Container")
    location_id = fields.Many2one("records.location", string="Storage Location")

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

    description = fields.Text(string="Item Description")
    barcode = fields.Char(string="Barcode/ID", tracking=True)

    # ============================================================================
    # STATUS TRACKING FIELDS
    # ============================================================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("searching", "Searching"),
            ("located", "Located"),
            ("retrieved", "Retrieved"),
            ("packaged", "Packaged"),
            ("scanned", "Scanned"),
            ("delivered", "Delivered"),
            ("returned", "Returned"),
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="pending",
        tracking=True,
    )

    # ============================================================================
    # LOCATION AND SEARCH FIELDS
    # ============================================================================
    current_location = fields.Char(string="Current Location")
    storage_location_id = fields.Many2one("records.location", string="Storage Location")

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
    retrieval_date = fields.Datetime(string="Retrieved Date", tracking=True)
    retrieved_by_id = fields.Many2one("res.users", string="Retrieved By")
    condition_notes = fields.Text(string="Condition Notes")
    special_handling = fields.Boolean(string="Special Handling Required", default=False)

    # ============================================================================
    # QUALITY CONTROL FIELDS
    # ============================================================================
    quality_checked = fields.Boolean(string="Quality Checked", default=False)
    quality_issues = fields.Text(string="Quality Issues")
    completeness_verified = fields.Boolean(string="Completeness Verified", default=False)

    # ============================================================================
    # SEARCH RESULTS AND HISTORY
    # ============================================================================
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

    # ============================================================================
    # NOT FOUND TRACKING
    # ============================================================================
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

    # ============================================================================
    # FILE DISCOVERY AND BARCODING
    # ============================================================================
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

    retrieval_notes = fields.Text(string="Retrieval Notes")

    # ============================================================================
    # CUSTOMER RELATIONSHIP
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="work_order_id.partner_id",
        store=True,
        readonly=True,
    )

    # ============================================================================
    # HANDLING AND PHYSICAL ATTRIBUTES
    # ============================================================================
    handling_instructions = fields.Text(string="Handling Instructions")
    fragile = fields.Boolean(string="Fragile Item", default=False)
    estimated_weight = fields.Float(string="Estimated Weight (kg)", digits="Product Price")
    actual_weight = fields.Float(string="Actual Weight (kg)", digits="Product Unit of Measure")
    dimensions = fields.Char(string="Dimensions (LxWxH)")

    # ============================================================================
    # SECURITY AND ACCESS
    # ============================================================================
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
    access_authorized_by_id = fields.Many2one("res.users", string="Access Authorized By")
    authorization_date = fields.Datetime(string="Authorization Date")

    # ============================================================================
    # CONDITION AND QUALITY
    # ============================================================================
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

    # ============================================================================
    # DIGITAL PROCESSING
    # ============================================================================
    scan_required = fields.Boolean(string="Scan Required", default=False)
    scan_completed = fields.Boolean(string="Scan Completed", default=False)
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

    # ============================================================================
    # RETURN INFORMATION
    # ============================================================================
    return_required = fields.Boolean(string="Return Required", default=True)
    return_date = fields.Date(string="Return Date")
    return_location_id = fields.Many2one("records.location", string="Return Location")
    return_notes = fields.Text(string="Return Notes")

    # ============================================================================
    # COST AND BILLING
    # ============================================================================
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
        help="Cost for accessing containers where file was NOT found",
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
        help="Total cost: retrieval fee + container access fees + delivery + not found fee",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        compute="_compute_currency_id",
        store=True,
        required=True,
    )

    # ============================================================================
    # TRACKING AND AUDIT
    # ============================================================================
    tracking_number = fields.Char(string="Tracking Number")
    audit_trail = fields.Text(string="Audit Trail")

    # ============================================================================
    # COMPUTED DISPLAY FIELDS
    # ============================================================================
    display_name = fields.Char(string="Display Name", compute="_compute_display_name", store=True)
    location_display = fields.Char(string="Location Display", compute="_compute_location_display", store=True)

    # ============================================================================
    # WORKFLOW STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('archived', 'Archived'),
        ],
        string='Status',
        default='draft',
        tracking=True,
        required=True,
        index=True,
        help='Current status of the record'
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )
    effective_priority = fields.Selection([("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Very High")], string="Effective Priority", compute="_compute_effective_priority")
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("work_order_id.currency_id", "company_id.currency_id")
    def _compute_currency_id(self):
        for item in self:
            if item.work_order_id and item.work_order_id.currency_id:
                item.currency_id = item.work_order_id.currency_id
            else:
                item.currency_id = item.company_id.currency_id or self.env.company.currency_id

    @api.depends("searched_container_ids")
    def _compute_containers_accessed_count(self):
        for item in self:
            item.containers_accessed_count = len(item.searched_container_ids)

    @api.depends("search_attempt_ids.found")
    def _compute_containers_not_found_count(self):
        for item in self:
            unsuccessful_searches = item.search_attempt_ids.filtered(lambda x: not x.found)
            item.containers_not_found_count = len(unsuccessful_searches)

    @api.depends("search_attempt_ids")
    def _compute_total_search_attempts(self):
        for item in self:
            item.total_search_attempts = len(item.search_attempt_ids)

    @api.depends("partner_id", "item_type")
    def _compute_retrieval_cost(self):
        for item in self:
            retrieval_rate = 0.0
            if item.partner_id:
                negotiated_rate = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", item.partner_id.id),
                    ("active", "=", True),
                ], limit=1)
                if negotiated_rate:
                    retrieval_rate = negotiated_rate.get_effective_rate("managed_retrieval_rate")

            if not retrieval_rate:
                base_rate = self.env["base.rate"].search([
                    ("service_type", "=", "retrieval"),
                    ("state", "=", "confirmed"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], order="effective_date desc", limit=1)
                if base_rate:
                    retrieval_rate = base_rate.managed_retrieval_rate or 3.50

            item.retrieval_cost = retrieval_rate or 3.50

    @api.depends("containers_not_found_count", "partner_id")
    def _compute_container_access_cost(self):
        for item in self:
            if not item.containers_not_found_count:
                item.container_access_cost = 0.0
                continue

            access_rate = 0.0
            if item.partner_id:
                negotiated_rate = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", item.partner_id.id),
                    ("rate_type", "=", "container_access"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)
                if negotiated_rate:
                    access_rate = negotiated_rate.get_effective_rate("container_access_rate")

            if not access_rate:
                base_rate = self.env["base.rate"].search([
                    ("service_type", "=", "container_access"),
                    ("state", "=", "confirmed"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], order="effective_date desc", limit=1)
                if base_rate:
                    access_rate = base_rate.external_per_bin_rate or 3.50

            access_rate = access_rate or 3.50
            item.container_access_cost = item.containers_not_found_count * access_rate

    @api.depends("retrieval_cost", "container_access_cost", "partner_id", "work_order_id.delivery_required", "status")
    def _compute_total_cost(self):
        for item in self:
            total = item.retrieval_cost + item.container_access_cost
            partner = item.partner_id

            if item.work_order_id and item.work_order_id.delivery_required and partner:
                delivery_fee = 0.0
                negotiated_delivery = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", partner.id),
                    ("rate_type", "=", "delivery"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)
                if negotiated_delivery:
                    delivery_fee = negotiated_delivery.get_effective_rate("pickup_rate")
                else:
                    base_delivery = self.env["base.rate"].search([
                        ("service_type", "=", "delivery"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),
                    ], order="effective_date desc", limit=1)
                    if base_delivery:
                        delivery_fee = base_delivery.pickup_rate
                total += delivery_fee or 25.00

            if item.status == "not_found" and partner:
                not_found_fee = 0.0
                negotiated_not_found = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", partner.id),
                    ("rate_type", "=", "not_found_search"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                ], limit=1)
                if negotiated_not_found:
                    not_found_fee = negotiated_not_found.get_effective_rate("managed_retrieval_rate")
                else:
                    base_not_found = self.env["base.rate"].search([
                        ("service_type", "=", "not_found_search"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                    ], limit=1)
                    if base_not_found:
                        not_found_fee = base_not_found.managed_retrieval_rate
                total += not_found_fee or 3.50

            item.total_cost = total

    @api.depends("name", "item_type", "barcode")
    def _compute_display_name(self):
        for item in self:
            parts = [item.name or "New Item"]
            if item.item_type:
                type_display = dict(item._fields["item_type"].selection).get(item.item_type, item.item_type)
                parts.append("(%s)" % type_display)
            if item.barcode:
                parts.append("[%s]" % item.barcode)
            item.display_name = " ".join(parts)

    @api.depends("current_location", "storage_location_id.name")
    def _compute_location_display(self):
        for item in self:
            if item.storage_location_id:
                item.location_display = item.storage_location_id.name
            elif item.current_location:
                item.location_display = item.current_location
            else:
                item.location_display = _("Location Unknown")

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange("container_id")
    def _onchange_container_id(self):
        if self.container_id:
            self.current_location = self.container_id.current_location
            self.storage_location_id = self.container_id.storage_location_id

    @api.onchange("document_id")
    def _onchange_document_id(self):
        if self.document_id:
            if self.document_id.container_id:
                self.container_id = self.document_id.container_id
            if self.item_type == "document" and not self.name and self.document_id.name:
                self.name = self.document_id.name

    @api.onchange("item_type")
    def _onchange_item_type(self):
        if self.item_type in ("container", "box"):
            self.document_id = False

    @api.onchange("priority")
    def _onchange_priority(self):
        """Update sequence based on priority for ordering"""
        if self.priority:
            priority_sequence_map = {
                '0': 100,  # Low priority - higher sequence number
                '1': 50,   # Normal priority
                '2': 20,   # High priority - lower sequence number  
                '3': 10,   # Very High priority - lowest sequence number
            }
            self.sequence = priority_sequence_map.get(self.priority, 50)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def _update_status(self, new_status, message_body, extra_vals=None):
        self.ensure_one()
        vals = {"status": new_status}
        if extra_vals:
            vals.update(extra_vals)
        self.write(vals)
        self.message_post(body=message_body, message_type="notification")

    def action_locate_item(self):
        for item in self:
            if item.status != "pending":
                raise UserError(_("Only pending items can be located."))
            item._update_status(
                "located",
                _("Item located by %s", self.env.user.name),
                {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}
            )

    def action_retrieve_item(self):
        for item in self:
            if item.status != "located":
                raise UserError(_("Item must be located before retrieval."))
            item._update_status(
                "retrieved",
                _("Item retrieved by %s", self.env.user.name),
                {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}
            )

    def action_package_item(self):
        for item in self:
            if item.status != "retrieved":
                raise UserError(_("Item must be retrieved before packaging."))
            item._update_status("packaged", _("Item packaged by %s", self.env.user.name))

    def action_deliver_item(self):
        for item in self:
            if item.status != "packaged":
                raise UserError(_("Item must be packaged before delivery."))
            item._update_status("delivered", _("Item delivered by %s", self.env.user.name))

    def action_return_item(self):
        for item in self:
            if item.status != "delivered":
                raise UserError(_("Item must be delivered before return."))
            item._update_status(
                "returned",
                _("Item returned by %s", self.env.user.name),
                {"return_date": fields.Date.today()}
            )

    # ============================================================================
    # SEARCH WORKFLOW ACTION METHODS
    # ============================================================================
    def action_begin_search_process(self):
        for item in self:
            if item.status != "pending":
                raise UserError(_("Only pending items can start the search process."))
            item._update_status(
                "searching",
                _("Search started by %s for file: %s", self.env.user.name, item.requested_file_name or item.name)
            )

    def action_record_container_search(self, container_id, found=False, notes=""):
        self.ensure_one()
        if container_id not in self.searched_container_ids.ids:
            self.searched_container_ids = [(4, container_id)]

        self.env["document.search.attempt"].create({
            "retrieval_item_id": self.id,
            "container_id": container_id,
            "searched_by_id": self.env.user.id,
            "search_date": fields.Datetime.now(),
            "found": found,
            "notes": notes,
        })

        if found:
            self.write({
                "status": "located",
                "file_discovered": True,
                "discovery_date": fields.Datetime.now(),
                "discovery_container_id": container_id,
                "container_id": container_id,
            })
        return True

    def action_mark_not_found(self, reason="not_in_container", notes=""):
        for item in self:
            reason_display = dict(item._fields["not_found_reason"].selection).get(reason, reason)
            message = _(
                "File marked as NOT FOUND by %s. Searched %s containers (%s unsuccessful). Reason: %s",
                self.env.user.name,
                item.containers_accessed_count,
                item.containers_not_found_count,
                reason_display
            )
            item._update_status(
                "not_found",
                message,
                {"not_found_reason": reason, "not_found_notes": notes or _("File not found after search.")}
            )

    def action_barcode_discovered_file(self, barcode, document_vals=None):
        self.ensure_one()
        if not self.file_discovered:
            raise UserError(_("File must be marked as discovered before barcoding."))

        self.write({"barcode": barcode, "status": "located"})

        if document_vals and self.discovery_container_id:
            document_vals.update({
                "name": self.requested_file_name or self.name,
                "barcode": barcode,
                "container_id": self.discovery_container_id.id,
                "partner_id": self.partner_id.id if self.partner_id else False,
            })
            document = self.env["records.document"].create(document_vals)
            self.document_id = document.id

        self.message_post(
            body=_("File barcoded by %s with barcode: %s", self.env.user.name, barcode),
            message_type="notification",
        )
        return True

    # ============================================================================
    # SEARCH AND QUERY METHODS
    # ============================================================================
    @api.model
    def search_items_by_status(self, status_list=None):
        """Search retrieval items by status"""
        if not status_list:
            status_list = ['pending', 'searching', 'located']
        
        domain = [('status', 'in', status_list)]
        return self.search(domain, order='priority desc, create_date desc')

    @api.model
    def search_items_by_partner(self, partner_id, limit=None):
        """Search retrieval items by partner"""
        domain = [('partner_id', '=', partner_id)]
        return self.search(domain, limit=limit, order='create_date desc')

    def search_related_containers(self):
        """Search for containers related to this item"""
        self.ensure_one()
        if self.partner_id:
            return self.env['records.container'].search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'active')
            ])
        return self.env['records.container']

    @api.model
    def search_items_by_priority(self, priority_level='2', limit=None):
        """Search retrieval items by priority level"""
        domain = [('priority', '>=', priority_level)]
        return self.search(domain, limit=limit, order='priority desc, create_date desc')

    @api.model
    def get_high_priority_items(self, partner_id=None):
        """Get high and very high priority items"""
        domain = [('priority', 'in', ['2', '3']), ('status', 'in', ['pending', 'searching', 'located'])]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(domain, order='priority desc, create_date desc')