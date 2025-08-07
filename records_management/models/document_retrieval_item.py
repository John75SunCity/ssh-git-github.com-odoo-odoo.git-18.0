# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class DocumentRetrievalItem(models.Model):
    _name = "document.retrieval.item"
    _description = "Document Retrieval Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "name"

    # Core identification
    name = fields.Char(string="Name", required=True, tracking=True),
    sequence = fields.Integer(string="Sequence", default=10)

    # Work Order Relationship
    work_order_id = fields.Many2one(
        "document.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
    )

    # Item Type and References
    item_type = fields.Selection(
        [
            ("file", "File"),
            ("document", "Single Document"),
            ("container", "Entire Container"),
        ],
        string="Item Type",
        required=True,
        default="file",
        help="File: Complete file folder (most common), Document: Single document from file, Container: Entire container",
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container Location",
        help="Container where the file is stored (for location purposes)",
        tracking=True,
    )

    box_number = fields.Char(
        string="Customer Box Number",
        help="Customer's own box numbering system for the container",
    )

    document_id = fields.Many2one(
        "records.document",
        string="Specific Document",
        help="Only used when retrieving a single document from a file",
    )

    # Barcode and Identification
    barcode = fields.Char(string="Barcode", help="Item barcode for tracking"),
    description = fields.Text(string="Description")

    # Location Information
    current_location = fields.Char(
        string="Current Location", help="Current storage location"
    storage_location_id = fields.Many2one("records.location", string="Storage Location")

    # Status and Processing
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("located", "Located"),
            ("retrieved", "Retrieved"),
            ("packaged", "Packaged"),
            ("delivered", "Delivered"),
            ("returned", "Returned"),
        ],
        string="Status",
        default="pending",
        tracking=True,
    )

    # Retrieval Details
    retrieval_notes = fields.Text(string="Retrieval Notes")
    retrieved_by = fields.Many2one("res.users", string="Retrieved By")
    retrieval_date = fields.Datetime(string="Retrieval Date")

    # Company and Basic Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
    active = fields.Boolean(string="Active", default=True)

    # === FRAMEWORK FIELDS ===        "mail.followers", "res_id", string="Followers"
    string="Customer",
        store=True,
        readonly=True,
    )

    # Handling Instructions
    special_handling = fields.Boolean(string="Special Handling Required", default=False)
    handling_instructions = fields.Text(string="Handling Instructions")
    fragile = fields.Boolean(string="Fragile Item", default=False)

    # Physical Attributes
    estimated_weight = fields.Float(string="Estimated Weight (kg)", digits=(8, 2))
    actual_weight = fields.Float(string="Actual Weight (kg)", digits=(8, 2))
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

    access_authorized_by = fields.Many2one("res.users", string="Access Authorized By")
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

    condition_notes = fields.Text(string="Condition Notes")

    # Digital Processing
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

    # Return Information
    return_required = fields.Boolean(string="Return Required", default=True)
    return_date = fields.Date(string="Return Date")
    return_location_id = fields.Many2one("records.location", string="Return Location")
    return_notes = fields.Text(string="Return Notes")

    # Cost and Billing
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost",
        currency_field="currency_id",
        help="Cost to retrieve this specific item",
    currency_id = fields.Many2one(
        related="work_order_id.currency_id",
        string="Currency",
        store=True,
        readonly=True,
    )

    # Tracking and Audit
    tracking_number = fields.Char(string="Tracking Number")
    audit_trail = fields.Text(string="Audit Trail")

    # === COMPUTED FIELDS ===

    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )

    location_display = fields.Char(
        string="Location Display", compute="_compute_location_display", store=True
    )

    # === COMPUTE METHODS ===

    @api.depends("name", "item_type", "barcode")
    def _compute_display_name(self):
        """Compute display name for better identification"""
        for item in self:
            parts = []
            if item.name:
                parts.append(item.name)
            if item.item_type:
                parts.append(f"({item.item_type.title()})")
            if item.barcode:
                parts.append(f"[{item.barcode}]")
            item.display_name = " ".join(parts) or "New Item"

    @api.depends("current_location", "storage_location_id")
    def _compute_location_display(self):
        """Compute user-friendly location display"""
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
        if self.container_id:
            self.storage_location_id = self.container_id.location_id
            if (
                hasattr(self.container_id, "current_location")
                and self.container_id.current_location
            ):
                self.current_location = self.container_id.current_location
            # Container is just for location - don't change item type unless specifically retrieving whole container

    @api.onchange("document_id")
    def _onchange_document_id(self):
        """Auto-fill information when single document is selected"""
        if self.document_id:
            if (
                hasattr(self.document_id, "container_id")
                and self.document_id.container_id
            ):
                self.container_id = self.document_id.container_id
            # Only change to document type if specifically selecting a single document
            if self.item_type == "file":
                self.item_type = "document"
            if not self.name:
                self.name = self.document_id.name

    @api.onchange("item_type")
    def _onchange_item_type(self):
        """Clear inappropriate fields when item type changes"""
        if self.item_type == "file":
            # For file retrieval, clear specific document selection
            self.document_id = False
        elif self.item_type == "container":
            # For container retrieval, clear specific document selection
            self.document_id = False

    # === ACTION METHODS ===

    def action_locate_item(self):
        """Mark item as located"""
        self.ensure_one()
        if self.status != "pending":
            raise UserError(_("Only pending items can be located"))

        self.write(
            {
                "status": "located",
                "retrieval_date": fields.Datetime.now(),
                "retrieved_by": self.env.user.id,
            }
        )

        self.message_post(
            body=f"Item located by {self.env.user.name}", message_type="notification"
        )

    def action_retrieve_item(self):
        """Mark item as retrieved"""
        self.ensure_one()
        if self.status != "located":
            raise UserError(_("Item must be located before retrieval"))

        self.write(
            {
                "status": "retrieved",
                "retrieval_date": fields.Datetime.now(),
                "retrieved_by": self.env.user.id,
            }
        )

        self.message_post(
            body=f"Item retrieved by {self.env.user.name}", message_type="notification"
        )

    def action_package_item(self):
        """Mark item as packaged"""
        self.ensure_one()
        if self.status != "retrieved":
            raise UserError(_("Item must be retrieved before packaging"))

        self.write({"status": "packaged"})

        self.message_post(
            body=f"Item packaged by {self.env.user.name}", message_type="notification"
        )

    def action_deliver_item(self):
        """Mark item as delivered"""
        self.ensure_one()
        if self.status != "packaged":
            raise UserError(_("Item must be packaged before delivery"))

        self.write({"status": "delivered"})

        self.message_post(
            body=f"Item delivered by {self.env.user.name}", message_type="notification"
        )

    def action_return_item(self):
        """Mark item as returned"""
        self.ensure_one()
        if not self.return_required:
            raise UserError(_("This item does not require return"))

        self.write({"status": "returned", "return_date": fields.Date.today()})

        self.message_post(
            body=f"Item returned by {self.env.user.name}", message_type="notification"
        ))
