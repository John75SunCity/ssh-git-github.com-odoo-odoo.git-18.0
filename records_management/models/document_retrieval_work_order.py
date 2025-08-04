# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class DocumentRetrievalWorkOrder(models.Model):
    _name = "document.retrieval.work.order"
    _description = "Document Retrieval Work Order"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("assigned", "Assigned"),
            ("in_progress", "In Progress"),
            ("ready_delivery", "Ready for Delivery"),
            ("delivered", "Delivered"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # Company and User
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")

    # === DOCUMENT RETRIEVAL SPECIFIC FIELDS ===
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    retrieval_type = fields.Selection(
        [
            ("permanent", "Permanent Retrieval"),
            ("temporary", "Temporary Retrieval"),
            ("copy", "Copy Request"),
            ("scan", "Scan to Digital"),
        ],
        string="Retrieval Type",
        default="permanent",
    )

    # Document Management
    document_ids = fields.One2many(
        "records.document", "retrieval_work_order_id", string="Documents to Retrieve"
    )
    container_ids = fields.Many2many("records.container", string="Containers Involved")
    location_ids = fields.Many2many("records.location", string="Retrieval Locations")
    total_document_count = fields.Integer(
        string="Total Documents", compute="_compute_totals", store=True
    )

    # Scheduling & Resources
    requested_date = fields.Date(string="Requested Date", default=fields.Date.today)
    target_completion_date = fields.Date(string="Target Completion Date")
    technician_id = fields.Many2one("hr.employee", string="Assigned Technician")
    estimated_hours = fields.Float(string="Estimated Hours", digits=(5, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(5, 2))

    # Customer Service
    delivery_method = fields.Selection(
        [
            ("pickup", "Customer Pickup"),
            ("delivery", "Courier Delivery"),
            ("scan_email", "Scan & Email"),
            ("portal_access", "Portal Access"),
        ],
        string="Delivery Method",
        default="pickup",
    )
    delivery_address_id = fields.Many2one("res.partner", string="Delivery Address")
    customer_contact_phone = fields.Char(string="Contact Phone")
    special_instructions = fields.Text(string="Special Instructions")

    # Billing & Financial
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id"
    )
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    billable_amount = fields.Monetary(
        string="Billable Amount", currency_field="currency_id"
    )
    invoice_required = fields.Boolean(string="Invoice Required", default=True)

    # Quality & Compliance
    quality_check_required = fields.Boolean(
        string="Quality Check Required", default=True
    )
    quality_checked_by = fields.Many2one("res.users", string="Quality Checked By")
    quality_check_date = fields.Datetime(string="Quality Check Date")
    compliance_notes = fields.Text(string="Compliance Notes")

    # === COMPREHENSIVE MISSING FIELDS ===
    workflow_state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Workflow State",
        default="draft",
    )
    next_action_date = fields.Date(string="Next Action Date")
    deadline_date = fields.Date(string="Deadline")
    completion_date = fields.Datetime(string="Completion Date")
    responsible_user_id = fields.Many2one("res.users", string="Responsible User")
    assigned_team_id = fields.Many2one("hr.department", string="Assigned Team")
    supervisor_id = fields.Many2one("res.users", string="Supervisor")
    quality_checked = fields.Boolean(string="Quality Checked")
    quality_score = fields.Float(string="Quality Score", digits=(3, 2))
    validation_required = fields.Boolean(string="Validation Required")
    validated_by_id = fields.Many2one("res.users", string="Validated By")
    validation_date = fields.Datetime(string="Validation Date")
    reference_number = fields.Char(string="Reference Number")

    # === CRITICAL MISSING FIELDS FOR VIEWS COMPATIBILITY ===

    # Customer Inventory Tracking System
    container_id = fields.Many2one(
        "records.container",
        string="Container ID",
        help="Internal barcoded container tracking",
    )
    box_number = fields.Char(
        string="Customer Box Number", help="Customer's own box numbering system"
    )

    # Barcode Integration
    barcode = fields.Char(string="Barcode", help="System-generated or scanned barcode")

    # === CRITICAL VIEW FIELDS ===
    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
    )

    request_date = fields.Date(
        string="Request Date", default=fields.Date.today, tracking=True
    )

    item_count = fields.Integer(
        string="Item Count", compute="_compute_item_count", store=True
    )

    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
    )

    has_custom_rates = fields.Boolean(
        string="Has Custom Rates", compute="_compute_has_custom_rates", store=True
    )

    customer_rates_id = fields.Many2one(
        "records.customer.billing.profile",
        string="Customer Rates",
        help="Custom billing rates for this customer",
    )

    technician_id = fields.Many2one(
        "hr.employee", string="Assigned Technician", tracking=True
    )

    department_id = fields.Many2one("hr.department", string="Department", tracking=True)

    requested_by = fields.Many2one(
        "res.users", string="Requested By", default=lambda self: self.env.user
    )

    delivery_date = fields.Date(string="Delivery Date")
    delivery_time = fields.Char(string="Delivery Time")

    driver_id = fields.Many2one("hr.employee", string="Driver")

    # Priority Pricing
    priority_item_cost = fields.Monetary(
        string="Priority Item Cost",
        currency_field="currency_id",
        compute="_compute_priority_costs",
        store=True,
    )

    priority_order_cost = fields.Monetary(
        string="Priority Order Cost",
        currency_field="currency_id",
        compute="_compute_priority_costs",
        store=True,
    )

    # Retrieval Items Relationship
    retrieval_item_ids = fields.One2many(
        "document.retrieval.item", "work_order_id", string="Retrieval Items"
    )

    # Delivery Information
    delivery_address = fields.Text(string="Delivery Address")
    delivery_contact = fields.Char(string="Delivery Contact")
    delivery_phone = fields.Char(string="Delivery Phone")
    actual_delivery_date = fields.Datetime(string="Actual Delivery Date")
    delivered_by = fields.Many2one("res.users", string="Delivered By")
    customer_signature_date = fields.Datetime(string="Customer Signature Date")
    customer_signature = fields.Binary(string="Customer Signature")

    # Notes Fields
    retrieval_notes = fields.Text(string="Retrieval Notes")
    delivery_notes = fields.Text(string="Delivery Notes")
    internal_notes = fields.Text(string="Internal Notes")

    # Cost Structure Fields
    base_delivery_cost = fields.Monetary(
        string="Base Delivery Cost",
        currency_field="currency_id",
        help="Standard delivery fee",
    )
    base_retrieval_cost = fields.Monetary(
        string="Base Retrieval Cost",
        currency_field="currency_id",
        help="Standard retrieval fee",
    )

    # Visual and Organization
    color = fields.Integer(string="Color Index", help="Color coding for organization")

    # Document Details
    document_description = fields.Text(string="Document Description")
    document_type_id = fields.Many2one("records.document.type", string="Document Type")
    file_count = fields.Integer(string="File Count", help="Number of files in request")

    # Processing Workflow
    processing_status = fields.Selection(
        [
            ("pending", "Pending"),
            ("locating", "Locating Items"),
            ("retrieving", "Retrieving"),
            ("packaging", "Packaging"),
            ("ready", "Ready for Delivery"),
            ("delivered", "Delivered"),
        ],
        string="Processing Status",
        default="pending",
        tracking=True,
    )

    # Location and Logistics
    storage_location_id = fields.Many2one("records.location", string="Storage Location")
    pickup_location = fields.Char(string="Pickup Location")
    delivery_method = fields.Selection(
        [
            ("courier", "Courier Delivery"),
            ("customer_pickup", "Customer Pickup"),
            ("mail", "Mail Delivery"),
            ("digital", "Digital Delivery"),
        ],
        string="Delivery Method",
        default="courier",
    )

    # Time Tracking
    estimated_hours = fields.Float(string="Estimated Hours", digits=(5, 2))
    actual_hours = fields.Float(string="Actual Hours", digits=(5, 2))
    start_time = fields.Datetime(string="Start Time")
    end_time = fields.Datetime(string="End Time")

    # Customer Communication
    customer_notified = fields.Boolean(string="Customer Notified", default=False)
    notification_sent_date = fields.Datetime(string="Notification Sent Date")
    customer_confirmation = fields.Boolean(
        string="Customer Confirmation", default=False
    )

    # Retrieval Specifics
    retrieval_type = fields.Selection(
        [
            ("permanent", "Permanent Retrieval"),
            ("temporary", "Temporary Access"),
            ("copy", "Copy Only"),
            ("scan", "Scan to Digital"),
        ],
        string="Retrieval Type",
        default="temporary",
    )

    return_required = fields.Boolean(string="Return Required", default=True)
    return_deadline = fields.Date(string="Return Deadline")

    # Security and Access Control
    security_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="standard",
    )

    access_authorization = fields.Text(string="Access Authorization")
    authorized_by = fields.Many2one("res.users", string="Authorized By")

    # Special Handling
    fragile_items = fields.Boolean(string="Fragile Items", default=False)
    special_handling_required = fields.Boolean(
        string="Special Handling Required", default=False
    )
    handling_instructions = fields.Text(string="Handling Instructions")

    # Packaging and Transport
    packaging_type = fields.Selection(
        [
            ("standard_box", "Standard Box"),
            ("secure_container", "Secure Container"),
            ("envelope", "Envelope"),
            ("custom", "Custom Packaging"),
        ],
        string="Packaging Type",
        default="standard_box",
    )

    transport_requirements = fields.Text(string="Transport Requirements")
    insurance_required = fields.Boolean(string="Insurance Required", default=False)
    insurance_value = fields.Monetary(
        string="Insurance Value", currency_field="currency_id"
    )

    # Digital Processing
    scan_required = fields.Boolean(string="Scan Required", default=False)
    scan_resolution = fields.Selection(
        [
            ("standard", "Standard (300 DPI)"),
            ("high", "High (600 DPI)"),
            ("archive", "Archive Quality (1200 DPI)"),
        ],
        string="Scan Resolution",
        default="standard",
    )

    digital_format = fields.Selection(
        [("pdf", "PDF"), ("tiff", "TIFF"), ("jpeg", "JPEG"), ("png", "PNG")],
        string="Digital Format",
        default="pdf",
    )

    # Performance Metrics
    efficiency_score = fields.Float(string="Efficiency Score", digits=(3, 2))
    customer_satisfaction = fields.Selection(
        [
            ("1", "Very Poor"),
            ("2", "Poor"),
            ("3", "Average"),
            ("4", "Good"),
            ("5", "Excellent"),
        ],
        string="Customer Satisfaction",
    )

    # Audit and Compliance
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )
    audit_trail = fields.Text(string="Audit Trail")
    compliance_verified = fields.Boolean(string="Compliance Verified", default=False)

    # Integration Fields
    external_tracking_id = fields.Char(string="External Tracking ID")
    third_party_service = fields.Char(string="Third Party Service")

    # Statistical and Reporting
    complexity_level = fields.Selection(
        [
            ("simple", "Simple"),
            ("moderate", "Moderate"),
            ("complex", "Complex"),
            ("very_complex", "Very Complex"),
        ],
        string="Complexity Level",
        default="simple",
    )

    volume_category = fields.Selection(
        [
            ("single_item", "Single Item"),
            ("small_batch", "Small Batch (2-10)"),
            ("medium_batch", "Medium Batch (11-50)"),
            ("large_batch", "Large Batch (51+)"),
        ],
        string="Volume Category",
        default="single_item",
    )

    # Emergency and Priority Handling
    emergency_request = fields.Boolean(string="Emergency Request", default=False)
    emergency_contact = fields.Char(string="Emergency Contact")
    emergency_reason = fields.Text(string="Emergency Reason")

    after_hours_service = fields.Boolean(string="After Hours Service", default=False)
    weekend_service = fields.Boolean(string="Weekend Service", default=False)

    # Customer Portal Integration
    portal_visible = fields.Boolean(string="Portal Visible", default=True)
    customer_updates_enabled = fields.Boolean(
        string="Customer Updates Enabled", default=True
    )
    tracking_url = fields.Char(string="Tracking URL")

    # Environmental and Sustainability
    eco_friendly_packaging = fields.Boolean(
        string="Eco-Friendly Packaging", default=False
    )
    carbon_footprint_offset = fields.Boolean(
        string="Carbon Footprint Offset", default=False
    )
    external_reference = fields.Char(string="External Reference")
    documentation_complete = fields.Boolean(string="Documentation Complete")
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    performance_score = fields.Float(string="Performance Score", digits=(5, 2))
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
    )

    # === COMPREHENSIVE DOCUMENT RETRIEVAL FIELDS ===

    # Enhanced Request Management
    urgency_level = fields.Selection(
        [
            ("low", "Low Priority"),
            ("medium", "Medium Priority"),
            ("high", "High Priority"),
            ("critical", "Critical"),
        ],
        string="Urgency Level",
        default="medium",
    )

    retrieval_reason = fields.Selection(
        [
            ("legal", "Legal Request"),
            ("audit", "Audit Purpose"),
            ("business", "Business Need"),
            ("compliance", "Compliance Review"),
            ("research", "Research"),
            ("other", "Other"),
        ],
        string="Retrieval Reason",
        required=True,
    )

    # Advanced Document Management
    document_categories = fields.Text(string="Document Categories")
    date_range_from = fields.Date(string="Document Date Range From")
    date_range_to = fields.Date(string="Document Date Range To")
    keyword_search = fields.Text(string="Search Keywords")
    file_types_requested = fields.Char(string="File Types Requested")
    estimated_volume = fields.Float(string="Estimated Volume (boxes)", digits=(5, 2))
    actual_volume = fields.Float(string="Actual Volume (boxes)", digits=(5, 2))

    # Enhanced Customer Information
    requestor_name = fields.Char(string="Requestor Name")
    requestor_email = fields.Char(string="Requestor Email")
    requestor_phone = fields.Char(string="Requestor Phone")
    department_requesting = fields.Many2one(
        "hr.department", string="Requesting Department"
    )
    authorization_level = fields.Selection(
        [
            ("basic", "Basic Access"),
            ("elevated", "Elevated Access"),
            ("restricted", "Restricted Access"),
            ("confidential", "Confidential"),
        ],
        string="Authorization Level",
        default="basic",
    )

    # Enhanced Delivery & Logistics
    delivery_date_requested = fields.Date(string="Requested Delivery Date")
    actual_delivery_date = fields.Date(string="Actual Delivery Date")
    delivery_time_window = fields.Char(string="Delivery Time Window")
    delivery_contact_name = fields.Char(string="Delivery Contact Name")
    delivery_instructions = fields.Text(string="Delivery Instructions")
    shipping_carrier = fields.Char(string="Shipping Carrier")
    tracking_number = fields.Char(string="Tracking Number")
    delivery_confirmation = fields.Boolean(string="Delivery Confirmed", default=False)

    # Enhanced Billing & Pricing
    hourly_rate = fields.Monetary(string="Hourly Rate", currency_field="currency_id")
    rush_service_fee = fields.Monetary(
        string="Rush Service Fee", currency_field="currency_id"
    )
    delivery_fee = fields.Monetary(string="Delivery Fee", currency_field="currency_id")
    scanning_fee = fields.Monetary(string="Scanning Fee", currency_field="currency_id")
    storage_access_fee = fields.Monetary(
        string="Storage Access Fee", currency_field="currency_id"
    )
    total_estimated_fee = fields.Monetary(
        string="Total Estimated Fee",
        currency_field="currency_id",
        compute="_compute_total_fees",
    )
    total_actual_fee = fields.Monetary(
        string="Total Actual Fee", currency_field="currency_id"
    )
    discount_applied = fields.Monetary(
        string="Discount Applied", currency_field="currency_id"
    )
    payment_terms = fields.Char(string="Payment Terms")

    # Enhanced Resource Management
    vehicle_required = fields.Boolean(string="Vehicle Required", default=False)
    vehicle_id = fields.Many2one("records.vehicle", string="Assigned Vehicle")
    equipment_needed = fields.Text(string="Equipment Needed")
    team_members = fields.Many2many("hr.employee", string="Team Members")
    backup_technician_id = fields.Many2one("hr.employee", string="Backup Technician")
    skill_requirements = fields.Text(string="Required Skills")

    # Enhanced Security & Compliance
    security_clearance_required = fields.Boolean(
        string="Security Clearance Required", default=False
    )
    witness_required = fields.Boolean(string="Witness Required", default=False)
    witness_name = fields.Char(string="Witness Name")
    chain_of_custody = fields.Boolean(string="Chain of Custody Required", default=True)
    security_escort_required = fields.Boolean(
        string="Security Escort Required", default=False
    )
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Use"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
        ],
        string="Confidentiality Level",
        default="internal",
    )

    # Enhanced Progress Tracking
    progress_percentage = fields.Float(
        string="Progress (%)", digits=(5, 2), compute="_compute_progress"
    )
    milestone_reached = fields.Char(string="Current Milestone")
    blockers_identified = fields.Text(string="Identified Blockers")
    risk_factors = fields.Text(string="Risk Factors")
    mitigation_actions = fields.Text(string="Mitigation Actions")

    # Enhanced Communication
    customer_notifications_sent = fields.Integer(string="Notifications Sent", default=0)
    last_customer_contact = fields.Datetime(string="Last Customer Contact")
    communication_preference = fields.Selection(
        [
            ("email", "Email"),
            ("phone", "Phone"),
            ("sms", "SMS"),
            ("portal", "Customer Portal"),
        ],
        string="Communication Preference",
        default="email",
    )

    # Enhanced Quality Management
    accuracy_score = fields.Float(string="Accuracy Score (%)", digits=(5, 2))
    completeness_score = fields.Float(string="Completeness Score (%)", digits=(5, 2))
    timeliness_score = fields.Float(string="Timeliness Score (%)", digits=(5, 2))
    customer_satisfaction_score = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )
    quality_issues_count = fields.Integer(string="Quality Issues", default=0)
    rework_required = fields.Boolean(string="Rework Required", default=False)
    rework_reason = fields.Text(string="Rework Reason")

    # Enhanced Digital Services
    digital_copy_requested = fields.Boolean(
        string="Digital Copy Requested", default=False
    )
    scan_resolution = fields.Selection(
        [
            ("low", "Low (150 DPI)"),
            ("medium", "Medium (300 DPI)"),
            ("high", "High (600 DPI)"),
            ("ultra", "Ultra High (1200 DPI)"),
        ],
        string="Scan Resolution",
        default="medium",
    )
    file_format = fields.Selection(
        [
            ("pdf", "PDF"),
            ("tiff", "TIFF"),
            ("jpeg", "JPEG"),
            ("png", "PNG"),
        ],
        string="Digital File Format",
        default="pdf",
    )
    ocr_required = fields.Boolean(string="OCR Required", default=False)
    digital_delivery_method = fields.Selection(
        [
            ("email", "Email"),
            ("portal", "Customer Portal"),
            ("ftp", "FTP"),
            ("cloud", "Cloud Storage"),
        ],
        string="Digital Delivery Method",
        default="portal",
    )

    # Enhanced Analytics & Reporting
    retrieval_efficiency = fields.Float(
        string="Retrieval Efficiency (%)", digits=(5, 2), compute="_compute_efficiency"
    )
    cost_per_document = fields.Monetary(
        string="Cost per Document",
        currency_field="currency_id",
        compute="_compute_cost_metrics",
    )
    time_per_document = fields.Float(
        string="Time per Document (minutes)",
        digits=(5, 2),
        compute="_compute_time_metrics",
    )
    value_score = fields.Float(
        string="Value Score", digits=(5, 2), compute="_compute_value_score"
    )

    # Enhanced Integration
    related_orders_count = fields.Integer(
        string="Related Orders", compute="_compute_related_orders"
    )
    parent_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Parent Order"
    )
    child_order_ids = fields.One2many(
        "document.retrieval.work.order", "parent_order_id", string="Child Orders"
    )
    fsm_task_id = fields.Many2one("fsm.task", string="Related FSM Task")
    invoice_id = fields.Many2one("account.move", string="Generated Invoice")
    portal_request_id = fields.Many2one("portal.request", string="Portal Request")
    external_reference = fields.Char(string="External Reference")
    documentation_complete = fields.Boolean(string="Documentation Complete")
    attachment_ids = fields.One2many("ir.attachment", "res_id", string="Attachments")
    performance_score = fields.Float(string="Performance Score", digits=(5, 2))
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
    )
    last_review_date = fields.Date(string="Last Review Date")
    next_review_date = fields.Date(string="Next Review Date")

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("document_ids")
    def _compute_totals(self):
        """Compute total counts and amounts."""
        for record in self:
            record.total_document_count = len(record.document_ids)

    # === NEW COMPUTE METHODS FOR VIEW FIELDS ===

    @api.depends("retrieval_item_ids")
    def _compute_item_count(self):
        """Compute total number of items to retrieve"""
        for record in self:
            record.item_count = len(record.retrieval_item_ids)

    @api.depends(
        "base_retrieval_cost",
        "base_delivery_cost",
        "priority_item_cost",
        "priority_order_cost",
    )
    def _compute_total_cost(self):
        """Compute total cost including all components"""
        for record in self:
            record.total_cost = (
                (record.base_retrieval_cost or 0)
                + (record.base_delivery_cost or 0)
                + (record.priority_item_cost or 0)
                + (record.priority_order_cost or 0)
            )

    @api.depends("customer_id", "customer_rates_id")
    def _compute_has_custom_rates(self):
        """Check if customer has custom billing rates"""
        for record in self:
            if record.customer_id and record.customer_rates_id:
                record.has_custom_rates = True
            elif record.customer_id:
                # Check if customer has any custom rates defined
                custom_rates = self.env["records.customer.billing.profile"].search(
                    [("partner_id", "=", record.customer_id.id)], limit=1
                )
                record.has_custom_rates = bool(custom_rates)
                if custom_rates and not record.customer_rates_id:
                    record.customer_rates_id = custom_rates.id
            else:
                record.has_custom_rates = False

    @api.depends("priority", "item_count")
    def _compute_priority_costs(self):
        """Compute priority-based additional costs"""
        for record in self:
            base_priority_item = 5.0  # Base priority surcharge per item
            base_priority_order = 25.0  # Base priority surcharge per order

            if record.priority == "urgent":
                multiplier = 2.0
            elif record.priority == "high":
                multiplier = 1.5
            else:
                multiplier = 0.0

            record.priority_item_cost = (
                (record.item_count or 0) * base_priority_item * multiplier
            )
            record.priority_order_cost = base_priority_order * multiplier

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =============================================================================
    # DOCUMENT RETRIEVAL WORK ORDER ACTION METHODS
    # =============================================================================

    def action_add_items(self):
        """Add items to the retrieval work order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Retrieval Items"),
            "res_model": "records.document",
            "view_mode": "tree",
            "domain": [
                ("state", "=", "stored"),
                ("retrieval_work_order_id", "=", False),
            ],
            "context": {
                "default_retrieval_work_order_id": self.id,
                "search_default_stored": 1,
            },
        }

    def action_assign_technician(self):
        """Assign technician to work order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign Technician"),
            "res_model": "res.users",
            "view_mode": "tree",
            "domain": [
                (
                    "groups_id",
                    "in",
                    [self.env.ref("records_management.group_records_user").id],
                )
            ],
            "context": {
                "default_work_order_id": self.id,
                "search_default_records_users": 1,
            },
        }

    def action_complete(self):
        """Complete the retrieval work order."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active work orders can be completed."))

        self.write({"state": "inactive"})  # Using inactive as "completed" state
        self.message_post(
            body=_("Document retrieval work order completed successfully.")
        )
        return True

    def action_confirm(self):
        """Confirm the work order."""
        self.ensure_one()
        self.write({"state": "active"})
        self.message_post(body=_("Work order confirmed and activated."))

        # Create activity for assigned technician
        if self.user_id:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=f"Document Retrieval: {self.name}",
                note="Begin document retrieval process as per work order specifications.",
                user_id=self.user_id.id,
            )
        return True

    def action_deliver(self):
        """Mark work order as delivered."""
        self.ensure_one()
        self.write({"state": "archived"})  # Using archived as "delivered" state
        self.message_post(body=_("Documents delivered to customer."))
        return True

    def action_ready_for_delivery(self):
        """Mark work order ready for delivery."""
        self.ensure_one()
        self.message_post(body=_("Work order ready for delivery."))

        # Create delivery activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Ready for Delivery: {self.name}",
            note="Documents are ready for delivery to customer. Schedule delivery arrangement.",
            user_id=self.user_id.id,
        )
        return True

    def action_start_retrieval(self):
        """Start the document retrieval process."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(
                _("Work order must be confirmed before starting retrieval.")
            )

        self.message_post(body=_("Document retrieval process started."))

        # Update any related documents to "in_retrieval" state if such state exists
        return True

    def action_view_pricing_breakdown(self):
        """View pricing breakdown for this work order."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing Breakdown"),
            "res_model": "account.move.line",
            "view_mode": "tree,form",
            "domain": [("name", "ilike", self.name)],
            "context": {
                "search_default_work_order": self.name,
                "group_by": "product_id",
            },
        }

    # ===== ACTION METHODS =====

    def action_start_retrieval(self):
        """Start the document retrieval process"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only start retrieval for draft orders"))

        # Validate required fields
        if not self.assigned_team_id:
            raise UserError(_("Please assign a team before starting retrieval"))

        self.write(
            {
                "state": "in_progress",
                "start_date": fields.Datetime.now(),
            }
        )

        # Create activity for team lead
        if self.assigned_team_id.team_lead_id:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                user_id=self.assigned_team_id.team_lead_id.user_id.id,
                summary=f"Document Retrieval Started: {self.name}",
                note=f"Document retrieval work order has been started. Priority: {self.priority_level}",
            )

        return True

    def action_pause_retrieval(self):
        """Pause the document retrieval process"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Can only pause active retrieval orders"))

        self.write(
            {
                "state": "paused",
                "pause_reason": self.env.context.get("pause_reason", "Manual pause"),
            }
        )

        return True

    def action_resume_retrieval(self):
        """Resume the document retrieval process"""
        self.ensure_one()
        if self.state != "paused":
            raise UserError(_("Can only resume paused retrieval orders"))

        self.write(
            {
                "state": "in_progress",
                "pause_reason": False,
            }
        )

        return True

    def action_complete_retrieval(self):
        """Complete the document retrieval process"""
        self.ensure_one()
        if self.state not in ["in_progress", "paused"]:
            raise UserError(_("Can only complete active retrieval orders"))

        # Validate completion requirements
        if self.quality_required and not self.quality_checked:
            raise UserError(_("Quality check is required before completion"))

        # Calculate actual completion metrics
        completion_date = fields.Datetime.now()
        if self.start_date:
            total_hours = (completion_date - self.start_date).total_seconds() / 3600.0
            self.actual_hours = total_hours

        self.write(
            {
                "state": "completed",
                "completion_date": completion_date,
                "progress_percentage": 100.0,
            }
        )

        # Create completion activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Document Retrieval Completed: {self.name}",
            note=f"Document retrieval work order has been completed successfully.",
        )

        # Update customer if portal request
        if self.portal_request_id:
            self.portal_request_id.write(
                {
                    "state": "completed",
                    "completion_date": completion_date,
                }
            )

        return True

    def action_cancel_retrieval(self):
        """Cancel the document retrieval process"""
        self.ensure_one()
        if self.state in ["completed", "cancelled"]:
            raise UserError(_("Cannot cancel completed or already cancelled orders"))

        # Get cancellation reason from context or prompt user
        cancel_reason = self.env.context.get("cancel_reason", "Cancelled by user")

        self.write(
            {
                "state": "cancelled",
                "cancellation_reason": cancel_reason,
                "cancellation_date": fields.Datetime.now(),
            }
        )

        # Update customer if portal request
        if self.portal_request_id:
            self.portal_request_id.write(
                {
                    "state": "cancelled",
                    "cancellation_reason": cancel_reason,
                }
            )

        return True

    def action_reset_to_draft(self):
        """Reset order back to draft state"""
        self.ensure_one()
        if self.state == "completed":
            raise UserError(_("Cannot reset completed orders"))

        self.write(
            {
                "state": "draft",
                "start_date": False,
                "completion_date": False,
                "cancellation_date": False,
                "progress_percentage": 0.0,
            }
        )

        return True

    def action_schedule_delivery(self):
        """Schedule delivery of retrieved documents"""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Can only schedule delivery for completed orders"))

        if not self.delivery_method:
            raise UserError(_("Please select a delivery method"))

        # Auto-schedule based on method
        if self.delivery_method == "pickup":
            # Customer pickup - no scheduling needed
            self.delivery_status = "ready_pickup"
        elif self.delivery_method in ["courier", "mail"]:
            # Schedule delivery
            self.delivery_status = "scheduled"
            if not self.delivery_date_scheduled:
                # Auto-schedule for next business day
                import datetime

                next_day = fields.Date.today() + datetime.timedelta(days=1)
                self.delivery_date_scheduled = next_day
        elif self.delivery_method == "digital":
            # Immediate digital delivery
            self.action_deliver_digital()

        return True

    def action_deliver_digital(self):
        """Handle digital delivery of documents"""
        self.ensure_one()
        if not self.digital_delivery_method:
            raise UserError(_("Please specify digital delivery method"))

        # Mark as delivered digitally
        self.write(
            {
                "delivery_status": "delivered",
                "delivery_date_actual": fields.Datetime.now(),
                "digital_delivery_completed": True,
            }
        )

        # Send notification to customer
        if self.customer_id:
            # Create message/email notification
            self.message_post(
                body=f"Documents have been delivered digitally via {self.digital_delivery_method}",
                message_type="notification",
                partner_ids=[self.customer_id.id],
            )

        return True

    def action_generate_invoice(self):
        """Generate invoice for the retrieval service"""
        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Can only invoice completed orders"))

        if self.invoice_id:
            raise UserError(_("Invoice already generated"))

        # Create invoice
        invoice_vals = {
            "partner_id": self.customer_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            "ref": self.name,
            "invoice_line_ids": [
                (
                    0,
                    0,
                    {
                        "name": f"Document Retrieval Service - {self.name}",
                        "quantity": 1,
                        "price_unit": self.total_estimated_fee,
                        "account_id": self.env["account.account"]
                        .search([("user_type_id.name", "=", "Income")], limit=1)
                        .id,
                    },
                )
            ],
        }

        invoice = self.env["account.move"].create(invoice_vals)
        self.invoice_id = invoice.id

        return {
            "type": "ir.actions.act_window",
            "name": "Invoice",
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_quality_check(self):
        """Perform quality check on retrieved documents"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Can only perform quality check on active orders"))

        # Update quality metrics
        self.write(
            {
                "quality_checked": True,
                "quality_check_date": fields.Datetime.now(),
                "quality_check_by": self.env.user.id,
            }
        )

        # If quality issues found, create activity
        if self.quality_issues:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=f"Quality Issues Found: {self.name}",
                note=f"Quality check revealed issues: {self.quality_issues}",
            )

        return True

    def action_assign_team(self):
        """Open wizard to assign team to the work order"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Assign Team",
            "res_model": "document.retrieval.team.assignment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_work_order_id": self.id},
        }

    # ============================================================================
    # COMPUTE METHODS FOR NEW FIELDS
    # ============================================================================

    @api.depends("start_time", "end_time")
    def _compute_actual_hours(self):
        """Compute actual hours based on start and end time"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.actual_hours = delta.total_seconds() / 3600.0
            else:
                record.actual_hours = 0.0

    @api.depends("file_count")
    def _compute_volume_category(self):
        """Compute volume category based on file count"""
        for record in self:
            count = record.file_count
            if count <= 1:
                record.volume_category = "single_item"
            elif count <= 10:
                record.volume_category = "small_batch"
            elif count <= 50:
                record.volume_category = "medium_batch"
            else:
                record.volume_category = "large_batch"

    @api.depends("estimated_hours", "special_handling_required", "security_level")
    def _compute_complexity_level(self):
        """Compute complexity level based on various factors"""
        for record in self:
            complexity_score = 0

            # Base complexity from estimated hours
            if record.estimated_hours:
                if record.estimated_hours <= 1:
                    complexity_score += 1
                elif record.estimated_hours <= 4:
                    complexity_score += 2
                elif record.estimated_hours <= 8:
                    complexity_score += 3
                else:
                    complexity_score += 4

            # Add complexity for special handling
            if record.special_handling_required:
                complexity_score += 1

            # Add complexity for security level
            if record.security_level in ["restricted", "top_secret"]:
                complexity_score += 2
            elif record.security_level == "confidential":
                complexity_score += 1

            # Determine final complexity
            if complexity_score <= 2:
                record.complexity_level = "simple"
            elif complexity_score <= 4:
                record.complexity_level = "moderate"
            elif complexity_score <= 6:
                record.complexity_level = "complex"
            else:
                record.complexity_level = "very_complex"

    @api.depends("actual_hours", "estimated_hours")
    def _compute_efficiency_score(self):
        """Compute efficiency score based on estimated vs actual time"""
        for record in self:
            if record.estimated_hours and record.actual_hours:
                if record.actual_hours <= record.estimated_hours:
                    # Completed on time or early
                    record.efficiency_score = min(
                        100.0, (record.estimated_hours / record.actual_hours) * 100
                    )
                else:
                    # Took longer than estimated
                    record.efficiency_score = max(
                        0.0,
                        100.0
                        - (
                            (record.actual_hours - record.estimated_hours)
                            / record.estimated_hours
                            * 50
                        ),
                    )
            else:
                record.efficiency_score = 0.0

    @api.depends("container_id")
    def _compute_storage_location(self):
        """Auto-compute storage location from container"""
        for record in self:
            if record.container_id and record.container_id.location_id:
                record.storage_location_id = record.container_id.location_id
            else:
                record.storage_location_id = False

    @api.depends("retrieval_type", "return_required")
    def _compute_return_deadline(self):
        """Compute return deadline based on retrieval type"""
        for record in self:
            if record.retrieval_type == "temporary" and record.return_required:
                from datetime import timedelta

                # Default 30 days for temporary retrieval
                if record.request_date:
                    record.return_deadline = record.request_date + timedelta(days=30)
                else:
                    record.return_deadline = fields.Date.today() + timedelta(days=30)
            else:
                record.return_deadline = False

    @api.depends("notification_sent_date")
    def _compute_customer_notified(self):
        """Auto-set customer notified flag"""
        for record in self:
            record.customer_notified = bool(record.notification_sent_date)

    # ============================================================================
    # ACTION METHODS FOR NEW FUNCTIONALITY
    # ============================================================================

    def action_locate_container(self):
        """Locate the container based on box number"""
        self.ensure_one()
        if not self.box_number:
            raise UserError(_("Please specify the customer box number first"))

        # Find container by box number
        container = self.env["records.container"].search(
            [("box_number", "=", self.box_number)], limit=1
        )

        if container:
            self.container_id = container.id
            self.storage_location_id = (
                container.location_id.id if container.location_id else False
            )
            self.message_post(
                body=_("Container %s located at %s for box number %s")
                % (
                    container.name,
                    container.location_id.name if container.location_id else "Unknown",
                    self.box_number,
                )
            )
        else:
            raise UserError(_("No container found for box number %s") % self.box_number)

        return True

    def action_notify_customer(self):
        """Send notification to customer about retrieval status"""
        self.ensure_one()
        template = self.env.ref(
            "records_management.email_template_retrieval_notification", False
        )
        if template:
            template.send_mail(self.id, force_send=True)
            self.notification_sent_date = fields.Datetime.now()
            self.customer_notified = True
        return True

    def action_generate_tracking_url(self):
        """Generate tracking URL for customer portal"""
        self.ensure_one()
        base_url = self.env["ir.config_parameter"].sudo().get_param("web.base.url")
        self.tracking_url = f"{base_url}/my/retrieval/{self.id}"
        return True

    def action_emergency_escalate(self):
        """Escalate as emergency request"""
        self.ensure_one()
        self.write({"emergency_request": True, "priority": "urgent"})

        # Notify management
        manager_group = self.env.ref("records_management.group_records_manager")
        if manager_group and manager_group.users:
            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Emergency Retrieval Request: %s") % self.name,
                note=_(
                    "This retrieval request has been marked as emergency. Immediate attention required."
                ),
                user_id=manager_group.users[0].id,
            )

        return True
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Assign Team",
            "res_model": "document.retrieval.team.assignment.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_work_order_id": self.id,
                "default_current_team_id": self.assigned_team_id.id,
            },
        }

    def action_view_retrieval_items(self):
        """View individual retrieval items"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": "Retrieval Items",
            "res_model": "document.retrieval.item",
            "view_mode": "tree,form",
            "domain": [("work_order_id", "=", self.id)],
            "context": {
                "default_work_order_id": self.id,
            },
        }

    def action_update_progress(self):
        """Update progress based on completed items"""
        self.ensure_one()

        # Count completed items
        total_items = len(self.retrieval_item_ids)
        if total_items > 0:
            completed_items = len(
                self.retrieval_item_ids.filtered(
                    lambda x: x.status in ["delivered", "completed"]
                )
            )
            progress = (completed_items / total_items) * 100
            self.progress_percentage = progress

        return True

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        # Handle both single dict and list of dicts
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Record")

        return super().create(vals_list)

    # === COMPREHENSIVE COMPUTE METHODS ===

    @api.depends(
        "hourly_rate",
        "rush_service_fee",
        "delivery_fee",
        "scanning_fee",
        "storage_access_fee",
    )
    def _compute_total_fees(self):
        """Compute total estimated fees"""
        for record in self:
            record.total_estimated_fee = (
                (
                    record.hourly_rate * record.estimated_hours
                    if record.hourly_rate and record.estimated_hours
                    else 0
                )
                + (record.rush_service_fee or 0)
                + (record.delivery_fee or 0)
                + (record.scanning_fee or 0)
                + (record.storage_access_fee or 0)
            )

    @api.depends("state", "completion_date", "target_completion_date")
    def _compute_progress(self):
        """Compute progress percentage based on state and milestones"""
        for record in self:
            if record.state == "draft":
                record.progress_percentage = 0
            elif record.state == "active":
                # Calculate based on time elapsed vs total time
                if record.target_completion_date and record.requested_date:
                    total_days = (
                        record.target_completion_date - record.requested_date
                    ).days
                    elapsed_days = (fields.Date.today() - record.requested_date).days
                    if total_days > 0:
                        record.progress_percentage = min(
                            (elapsed_days / total_days) * 100, 95
                        )
                    else:
                        record.progress_percentage = 50
                else:
                    record.progress_percentage = 25
            elif record.state == "inactive":
                record.progress_percentage = 100
            else:
                record.progress_percentage = 100

    @api.depends("actual_hours", "estimated_hours")
    def _compute_efficiency(self):
        """Compute retrieval efficiency based on time performance"""
        for record in self:
            if record.estimated_hours and record.actual_hours:
                record.retrieval_efficiency = (
                    record.estimated_hours / record.actual_hours
                ) * 100
            else:
                record.retrieval_efficiency = 0

    @api.depends("total_actual_fee", "total_document_count")
    def _compute_cost_metrics(self):
        """Compute cost per document"""
        for record in self:
            if record.total_document_count and record.total_actual_fee:
                record.cost_per_document = (
                    record.total_actual_fee / record.total_document_count
                )
            else:
                record.cost_per_document = 0

    @api.depends("actual_hours", "total_document_count")
    def _compute_time_metrics(self):
        """Compute time per document in minutes"""
        for record in self:
            if record.total_document_count and record.actual_hours:
                record.time_per_document = (
                    record.actual_hours * 60
                ) / record.total_document_count
            else:
                record.time_per_document = 0

    @api.depends(
        "customer_satisfaction_score",
        "retrieval_efficiency",
        "accuracy_score",
        "timeliness_score",
    )
    def _compute_value_score(self):
        """Compute overall value score based on multiple metrics"""
        for record in self:
            scores = [
                record.customer_satisfaction_score or 0,
                record.retrieval_efficiency or 0,
                record.accuracy_score or 0,
                record.timeliness_score or 0,
            ]
            valid_scores = [s for s in scores if s > 0]
            record.value_score = (
                sum(valid_scores) / len(valid_scores) if valid_scores else 0
            )

    @api.depends("parent_order_id", "child_order_ids")
    def _compute_related_orders(self):
        """Compute count of related orders"""
        for record in self:
            related_count = 0
            if record.parent_order_id:
                related_count += 1
            related_count += len(record.child_order_ids)
            record.related_orders_count = related_count
