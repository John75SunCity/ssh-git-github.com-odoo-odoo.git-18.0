# -*- coding: utf-8 -*-
"""
Records Container Management Module

See RECORDS_MANAGEMENT_SYSTEM_MANUAL.md - Section 7: Records Container Management Module
for comprehensive documentation, business processes, and integration details.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from dateutil.relativedelta import relativedelta

from odoo import _, api, fields, models

from odoo.exceptions import UserError, ValidationError


class RecordsContainer(models.Model):
    """
    Records Container Management

    Note: Removed duplicate customer_id field to avoid confusion.
    The partner_id field is now used as the customer reference throughout this model.
    """

    _name = "records.container"
    _description = "Records Container Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string="Container Number", required=True, tracking=True, index=True
    )
    code = fields.Char(string="Container Code", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    # ============================================================================
    # CURRENCY FIELD (AUTO-ADDED)
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
        help="Currency for monetary fields"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Container Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("in_transit", "In Transit"),
            ("stored", "Stored"),
            ("pending_destruction", "Pending Destruction"),
            ("destroyed", "Destroyed"),
        ],
        string="Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # CUSTOMER & LOCATION RELATIONSHIPS
    # ============================================================================

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    department_id = fields.Many2one("records.department", string="Department")
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True
    )
    temp_inventory_id = fields.Many2one(
        "temp.inventory",
        string="Temporary Inventory",
        help="Temporary inventory location for this container",
    )
    customer_inventory_id = fields.Many2one(
        "customer.inventory",
        string="Customer Inventory",
        help="Customer inventory record for this container",
    )

    # Barcode Product Relationship (for barcoded containers)
    barcode_product_id = fields.Many2one(
        "barcode.product", string="Barcode Product", tracking=True
    )

    # ============================================================================
    # CONTAINER SPECIFICATIONS
    # ============================================================================

    container_type_id = fields.Many2one(
        "records.container.type", string="Container Type", required=True
    )
    document_type_id = fields.Many2one(
        "records.document.type", 
        string="Primary Document Type", 
        help="Primary document type for containers with uniform content"
    )
    barcode = fields.Char(string="Barcode", index=True, tracking=True)
    dimensions = fields.Char(string="Dimensions")
    weight = fields.Float(string="Weight (lbs)", digits="Stock Weight", default=0.0)
    cubic_feet = fields.Float(string="Cubic Feet", digits="Stock Weight", default=0.0)

    # ============================================================================
    # CONTENT MANAGEMENT
    # ============================================================================

    document_ids = fields.One2many(
        "records.document", "container_id", string="Documents"
    )
    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count", store=True
    )
    content_description = fields.Text(string="Content Description")
    is_full = fields.Boolean(string="Container Full", default=False)

    # ============================================================================
    # CONTAINER LABELING & CONTENT ORGANIZATION (For Intelligent Search)
    # ============================================================================

    # Alphabetical range for file organization
    alpha_range_start = fields.Char(
        string="Alphabetical Start",
        size=5,
        index=True,  # Indexed for fast alphabetical searching
        help="Starting letter/sequence for files in this container (e.g., 'A', 'Adams')",
    )
    alpha_range_end = fields.Char(
        string="Alphabetical End",
        size=5,
        index=True,  # Indexed for fast alphabetical searching
        help="Ending letter/sequence for files in this container (e.g., 'G', 'Green')",
    )
    alpha_range_display = fields.Char(
        string="Alpha Range",
        compute="_compute_alpha_range_display",
        store=True,
        help="Display format: A-G or Adams-Green",
    )

    # Date ranges for content organization
    content_date_from = fields.Date(
        string="Content Date From",
        index=True,  # Indexed for fast date range searches
        help="Earliest date of documents/services in this container",
    )
    content_date_to = fields.Date(
        string="Content Date To",
        index=True,  # Indexed for fast date range searches
        help="Latest date of documents/services in this container",
    )
    content_date_range_display = fields.Char(
        string="Date Range",
        compute="_compute_date_range_display",
        store=True,
        help="Display format: 07/01/2024 - 09/23/2024",
    )

    # Content type and categorization
    primary_content_type = fields.Selection(
        [
            ("medical", "Medical Records"),
            ("financial", "Financial Documents"),
            ("legal", "Legal Files"),
            ("personnel", "Personnel Files"),
            ("contracts", "Contracts"),
            ("invoices", "Invoices"),
            ("tax_documents", "Tax Documents"),
            ("insurance", "Insurance Records"),
            ("mixed", "Mixed Content"),
            ("other", "Other"),
        ],
        string="Primary Content Type",
        index=True,  # Indexed for content type filtering
        help="Main type of content in this container",
    )

    # Search keywords and tags for content
    search_keywords = fields.Text(
        string="Search Keywords",
        help="Keywords that help identify content in this container (names, topics, etc.)",
    )

    # Customer-specific organization fields
    customer_sequence_start = fields.Char(
        string="Customer Sequence Start",
        index=True,  # Indexed for customer sequence searches
        help="Starting sequence for customer-specific numbering/organization",
    )
    customer_sequence_end = fields.Char(
        string="Customer Sequence End",
        index=True,  # Indexed for customer sequence searches
        help="Ending sequence for customer-specific numbering/organization",
    )

    # ============================================================================
    # DATE TRACKING
    # ============================================================================

    received_date = fields.Date(
        string="Received Date", default=fields.Date.today, tracking=True
    )
    collection_date = fields.Date(
        string="Collection Date", 
        tracking=True,
        help="Date when container was collected from customer"
    )
    service_date = fields.Date(
        string="Service Date",
        tracking=True, 
        help="Date of last service performed on this container"
    )
    storage_start_date = fields.Date(string="Storage Start Date")
    stored_date = fields.Date(string="Stored Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date")
    destruction_date = fields.Date(string="Destruction Date")

    # ============================================================================
    # MOVEMENT TRACKING FIELDS
    # ============================================================================
    
    from_location_id = fields.Many2one(
        'records.location',
        string='From Location',
        help="Location where container was moved from during last movement",
        tracking=True,
    )
    to_location_id = fields.Many2one(
        'records.location', 
        string='To Location',
        help="Location where container was moved to during last movement",
        tracking=True,
    )
    movement_date = fields.Datetime(
        string='Movement Date',
        help="Date and time of last container movement",
        tracking=True,
    )
    movement_type = fields.Selection(
        [
            ('in', 'Incoming'),
            ('out', 'Outgoing'),
            ('transfer', 'Transfer'),
            ('pickup', 'Customer Pickup'),
            ('delivery', 'Customer Delivery'),
        ],
        string='Movement Type',
        help="Type of the last movement performed",
        tracking=True,
    )

    # ============================================================================
    # SERVICE & BUSINESS CLASSIFICATION
    # ============================================================================
    
    service_type = fields.Selection(
        [
            ('pickup', 'Pickup Service'),
            ('delivery', 'Delivery Service'),
            ('destruction', 'Destruction Service'), 
            ('storage', 'Storage Service'),
            ('retrieval', 'Retrieval Service'),
            ('scanning', 'Document Scanning'),
            ('other', 'Other Service'),
        ],
        string='Service Type',
        help="Primary service type for this container",
        index=True,
        tracking=True,
    )
    
    access_level = fields.Selection(
        [
            ('public', 'Public Access'),
            ('restricted', 'Restricted Access'),
            ('confidential', 'Confidential'),
            ('top_secret', 'Top Secret'),
        ],
        string='Access Level',
        default='public',
        help="Security access level for container contents",
        tracking=True,
    )
    
    # ============================================================================
    # ADVANCED CATEGORIZATION & METADATA
    # ============================================================================
    
    compliance_category = fields.Char(
        string='Compliance Category',
        help="Regulatory compliance category (HIPAA, SOX, PCI, etc.)",
        index=True,
    )
    
    industry_category = fields.Selection(
        [
            ('healthcare', 'Healthcare'),
            ('financial', 'Financial Services'),
            ('legal', 'Legal Services'), 
            ('education', 'Education'),
            ('government', 'Government'),
            ('manufacturing', 'Manufacturing'),
            ('retail', 'Retail'),
            ('other', 'Other'),
        ],
        string='Industry Category',
        help="Industry classification for specialized handling",
        index=True,
    )
    
    department_code = fields.Char(
        string='Department Code',
        help="Internal department code for organization",
        index=True,
    )
    
    project_number = fields.Char(
        string='Project Number',
        help="Associated project or job number",
        index=True,
    )
    
    priority_level = fields.Selection(
        [
            ('low', 'Low Priority'),
            ('normal', 'Normal Priority'),
            ('high', 'High Priority'),
            ('urgent', 'Urgent'),
        ],
        string='Priority Level',
        default='normal',
        help="Priority level for handling and processing",
        tracking=True,
    )
    
    # ============================================================================
    # ADDITIONAL METADATA & TRACKING
    # ============================================================================
    
    media_type = fields.Selection(
        [
            ('paper', 'Paper Documents'),
            ('digital', 'Digital Media'),
            ('film', 'Microfilm/Microfiche'),
            ('magnetic', 'Magnetic Media'),
            ('optical', 'Optical Media'),
            ('mixed', 'Mixed Media'),
        ],
        string='Media Type',
        default='paper',
        help="Primary media type stored in container",
    )
    
    language_codes = fields.Char(
        string='Language Codes', 
        help="Language codes for multilingual content (e.g., en,es,fr)",
    )
    
    retention_category = fields.Char(
        string='Retention Category',
        help="Categorization for retention policy application",
        index=True,
    )
    
    special_dates = fields.Text(
        string='Special Dates',
        help="JSON or text field for storing special dates and milestones",
    )
    
    bale_weight = fields.Float(
        string='Bale Weight',
        digits='Stock Weight',
        help="Weight when container is prepared for baling/recycling",
    )
    
    # Key-value metadata fields for flexible data storage
    key = fields.Char(
        string='Metadata Key',
        help="Key for key-value metadata pairs",
    )
    
    value = fields.Text(
        string='Metadata Value', 
        help="Value for key-value metadata pairs",
    )

    # ============================================================================
    # RETENTION MANAGEMENT
    # ============================================================================

    retention_policy_id = fields.Many2one(
        "records.retention.policy", string="Retention Policy"
    )
    retention_years = fields.Integer(string="Retention Years", default=7)
    destruction_due_date = fields.Date(
        string="Destruction Due Date",
        compute="_compute_destruction_due_date",
        store=True,
    )
    permanent_retention = fields.Boolean(string="Permanent Retention", default=False)

    # ============================================================================
    # BILLING & SERVICES
    # ============================================================================

    billing_rate = fields.Float(
        string="Monthly Billing Rate", digits="Product Price", default=0.0
    )
    service_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("climate_controlled", "Climate Controlled"),
            ("high_security", "High Security"),
        ],
        string="Service Level",
        default="standard",
    )

    # ============================================================================
    # SECURITY & ACCESS
    # ============================================================================

    security_level = fields.Selection(
        [
            ("public", "Public"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        default="confidential",
    )
    access_restriction = fields.Text(string="Access Restrictions")
    authorized_user_ids = fields.Many2many("res.users", string="Authorized Users")

    # ============================================================================
    # CONDITION & MAINTENANCE
    # ============================================================================

    condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
        ],
        string="Condition",
        default="good",
    )
    maintenance_notes = fields.Text(string="Maintenance Notes")
    last_inspection_date = fields.Date(string="Last Inspection Date")

    # ============================================================================
    # MOVEMENT TRACKING
    # ============================================================================

    movement_ids = fields.One2many(
        "records.container.movement", "container_id", string="Movement History"
    )
    current_movement_id = fields.Many2one(
        "records.container.movement", string="Current Movement"
    )

    # Add conversion tracking fields
    conversion_date = fields.Datetime(
        string="Conversion Date",
        help="Date when container type was last converted",
        tracking=True,
    )
    conversion_reason = fields.Text(
        string="Conversion Reason", help="Reason for container type conversion"
    )
    converter_id = fields.Many2one(
        "records.container.type.converter",
        string="Type Converter",
        help="Reference to the conversion operation that modified this container",
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
    # Added by Safe Business Fields Fixer
    security_seal_number = fields.Char(string="Security Seal Number", tracking=True)

    # Added by Safe Business Fields Fixer
    last_inventory_date = fields.Date(string="Last Inventory Date")

    # Added by Safe Business Fields Fixer
    next_inspection_due = fields.Date(string="Next Inspection Due")

    # Added by Safe Business Fields Fixer
    temperature_controlled = fields.Boolean(string="Temperature Controlled", default=False)

    # Added by Safe Business Fields Fixer
    humidity_controlled = fields.Boolean(string="Humidity Controlled", default=False)

    # Added by Safe Business Fields Fixer
    fire_suppression = fields.Boolean(string="Fire Suppression Available", default=False)

    # Added by Safe Business Fields Fixer
    access_restrictions = fields.Text(string="Access Restrictions")

    # Added by Safe Business Fields Fixer
    insurance_value = fields.Monetary(string="Insurance Value", currency_field="currency_id")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================

    def action_activate(self):
        """Activate container for storage"""

        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation"))
        if not self.location_id:
            raise UserError(_("Storage location must be assigned"))

        self.write(
            {
                "state": "active",
                "storage_start_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Container activated for storage"))

    def action_mark_full(self):
        """Mark container as full"""

        self.ensure_one()
        self.write({"is_full": True})
        self.message_post(body=_("Container marked as full"))

    def action_schedule_destruction(self):
        """Schedule container for destruction"""

        self.ensure_one()
        if self.permanent_retention:
            raise UserError(
                _("Cannot schedule permanent retention containers for destruction")
            )

        self.write({"state": "pending_destruction"})
        self.message_post(body=_("Container scheduled for destruction"))

    def action_destroy(self):
        """Mark container as destroyed"""

        self.ensure_one()
        if self.state != "pending_destruction":
            raise UserError(_("Only containers pending destruction can be destroyed"))

        self.write(
            {
                "destruction_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Container destroyed"))

    def action_view_documents(self):
        """View all documents in this container"""

        self.ensure_one()
        return {
            "name": _("Documents in Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("container_id", "=", self.id)],
        }

    def action_generate_barcode(self):
        """
        Generates a barcode if one doesn't exist and returns an action to print it.
        This assumes a report with the external ID 'records_management.report_container_barcode' exists.
        """

        self.ensure_one()
        if not self.barcode:
            # Generate barcode if not exists
            self.barcode = (
                self.env["ir.sequence"].next_by_code("records.container.barcode")
                or self.name
            )
        # Return a report action to print the barcode
        return self.env.ref("records_management.report_container_barcode").report_action(self)

    def action_index_container(self):
        """Index container - change state from received to indexed"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft containers can be indexed"))
        self.write({"state": "active"})
        self.message_post(body=_("Container indexed and activated"))

    def action_store_container(self):
        """Store container - change state from indexed to stored"""

        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active containers can be stored"))
        if not self.location_id:
            raise UserError(_("Storage location must be assigned before storing"))
        vals = {"state": "stored"}
        if not self.storage_start_date:
            vals["storage_start_date"] = fields.Date.today()
        self.write(vals)
        self.message_post(
            body=_("Container stored at location %s", self.location_id.name)
        )

    def action_retrieve_container(self):
        """Retrieve container from storage"""

        self.ensure_one()
        if self.state not in ["stored", "active"]:
            raise UserError(_("Only stored or active containers can be retrieved"))
        self.write({"state": "in_transit", "last_access_date": fields.Date.today()})
        self.message_post(body=_("Container retrieved from storage"))

    def action_destroy_container(self):
        """Prepare container for destruction"""

        self.ensure_one()
        if self.permanent_retention:
            raise UserError(_("Cannot destroy containers with permanent retention"))
        self.action_schedule_destruction()

    def action_bulk_convert_container_type(self):
        """Bulk convert container types"""

        self.ensure_one()
        return {
            "name": _("Bulk Convert Container Types"),
            "type": "ir.actions.act_window",
            "res_model": "records.container.type.converter.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_container_ids": [(6, 0, self.ids)]},
        }

    def create_movement_record(
        self, from_location_id, to_location_id, movement_type="transfer"
    ):
        """Create movement record for container"""
        self.ensure_one()
        movement_vals = {
            "movement_date": fields.Date.today(),
            "from_location_id": from_location_id,
            "to_location_id": to_location_id,
            "movement_type": movement_type,
            "container_id": self.id,
        }

        movement = self.env["records.container.movement"].create(movement_vals)
        self.current_movement_id = movement.id
        return movement

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    @api.depends("document_ids")
    def _compute_document_count(self):
        for container in self:
            container.document_count = len(container.document_ids)

    @api.depends("storage_start_date", "retention_years", "permanent_retention")
    def _compute_destruction_due_date(self):
        for container in self:
            if container.permanent_retention or not container.storage_start_date:
                container.destruction_due_date = False
            else:
                container.destruction_due_date = (
                    container.storage_start_date
                    + relativedelta(years=container.retention_years)
                )

    is_due_for_destruction = fields.Boolean(
        string="Due for Destruction",
        compute="_compute_is_due_for_destruction",
        search="_search_due_for_destruction",
    )
    action_bulk_convert_container_type = fields.Selection([], string='Action Bulk Convert Container Type')  # TODO: Define selection options
    action_destroy_container = fields.Char(string='Action Destroy Container')
    action_generate_barcode = fields.Char(string='Action Generate Barcode')
    action_index_container = fields.Char(string='Action Index Container')
    action_retrieve_container = fields.Char(string='Action Retrieve Container')
    action_store_container = fields.Char(string='Action Store Container')
    action_view_documents = fields.Char(string='Action View Documents')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    destroyed = fields.Char(string='Destroyed')
    details = fields.Char(string='Details')
    documents = fields.Char(string='Documents')
    group_by_creation_date = fields.Date(string='Group By Creation Date')
    group_by_customer = fields.Char(string='Group By Customer')
    group_by_department = fields.Char(string='Group By Department')
    group_by_location = fields.Char(string='Group By Location')
    group_by_state = fields.Selection([], string='Group By State')  # TODO: Define selection options
    help = fields.Char(string='Help')
    indexed = fields.Char(string='Indexed')
    movements = fields.Char(string='Movements')
    near_destruction = fields.Char(string='Near Destruction')
    received = fields.Char(string='Received')
    res_model = fields.Char(string='Res Model')
    retrieved = fields.Char(string='Retrieved')
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    stored = fields.Char(string='Stored')
    this_month = fields.Char(string='This Month')
    this_year = fields.Char(string='This Year')
    view_mode = fields.Char(string='View Mode')

    @api.depends("destruction_due_date")
    def _compute_is_due_for_destruction(self):
        today = fields.Date.today()
        for container in self:
            container.is_due_for_destruction = (
                container.destruction_due_date
                and container.destruction_due_date <= today
                and not container.permanent_retention
            )

    @api.depends("alpha_range_start", "alpha_range_end")
    def _compute_alpha_range_display(self):
        """Compute alphabetical range display for search purposes"""
        for container in self:
            if container.alpha_range_start and container.alpha_range_end:
                container.alpha_range_display = (
                    f"{container.alpha_range_start}-{container.alpha_range_end}"
                )
            elif container.alpha_range_start:
                container.alpha_range_display = f"{container.alpha_range_start}+"
            else:
                container.alpha_range_display = ""

    @api.depends("content_date_from", "content_date_to")
    def _compute_date_range_display(self):
        """Compute date range display for search purposes"""
        for container in self:
            if container.content_date_from and container.content_date_to:
                from_str = container.content_date_from.strftime("%m/%d/%Y")
                to_str = container.content_date_to.strftime("%m/%d/%Y")
                container.content_date_range_display = f"{from_str} - {to_str}"
            elif container.content_date_from:
                from_str = container.content_date_from.strftime("%m/%d/%Y")
                container.content_date_range_display = f"From {from_str}"
            elif container.content_date_to:
                to_str = container.content_date_to.strftime("%m/%d/%Y")
                container.content_date_range_display = f"Until {to_str}"
            else:
                container.content_date_range_display = ""

    def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
        if operator == "=" and value:
            # Due for destruction: due date is today or earlier, not permanent, not destroyed
            return [
                ("destruction_due_date", "<=", today),
                ("permanent_retention", "=", False),
                ("state", "!=", "destroyed"),
            ]
        elif operator == "=" and not value:
            # Not due for destruction: due date is in future or permanent retention or destroyed
            return [
                "|",
                ("destruction_due_date", ">", today),
                "|",
                ("permanent_retention", "=", True),
                ("state", "=", "destroyed"),
            ]
        elif operator == "!=" and value:
            # Not due for destruction
            return [
                "|",
                ("destruction_due_date", ">", today),
                "|",
                ("permanent_retention", "=", True),
                ("state", "=", "destroyed"),
            ]
        elif operator == "!=" and not value:
            # Due for destruction
            return [
                ("destruction_due_date", "<=", today),
                ("permanent_retention", "=", False),
                ("state", "!=", "destroyed"),
            ]
        else:
            return []

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("weight", "cubic_feet")
    def _check_positive_values(self):
        for record in self:
            if record.weight < 0 or record.cubic_feet < 0:
                raise ValidationError(
                    _("Weight and cubic feet must be positive values")
                )

    @api.constrains("retention_years")
    def _check_retention_years(self):
        for record in self:
            if record.retention_years < 0:
                raise ValidationError(_("Retention years cannot be negative"))

    @api.constrains("received_date", "storage_start_date")
    def _check_date_consistency(self):
        for record in self:
            if (
                record.received_date
                and record.storage_start_date
                and record.received_date > record.storage_start_date
            ):
                raise ValidationError(
                    _("Storage start date cannot be before received date")
                )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("records.container") or "NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        # Update last access date only if location_id or state actually changes
        if any(key in vals for key in ["location_id", "state"]):
            if "last_access_date" not in vals:
                vals["last_access_date"] = fields.Date.today()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state in ("active", "stored"):
                raise UserError(_("Cannot delete active containers"))
            if record.document_ids:
                raise UserError(_("Cannot delete containers with documents"))
        return super().unlink()

    def get_next_inspection_date(self):
        """Calculate next inspection date based on service level"""
        self.ensure_one()
        inspection_intervals = {
            "standard": 12,
            "premium": 6,
            "climate_controlled": 4,
            "high_security": 3,
        }
        interval = inspection_intervals.get(self.service_level, 12)
        base_date = self.last_inspection_date or fields.Date.today()
        return base_date + relativedelta(months=interval)

    # AUTO-GENERATED FIELDS (Batch 1)
    # ============================================================================
