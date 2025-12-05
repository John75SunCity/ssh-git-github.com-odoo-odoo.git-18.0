from dateutil.relativedelta import relativedelta  # type: ignore
import base64
from io import BytesIO

from odoo import models, fields, api, _  # pyright: ignore[reportMissingModuleSource, reportAttributeAccessIssue]
from odoo.exceptions import ValidationError, UserError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


# Replace direct qrcode import with guarded import (removes unused type: ignore)
try:
    import qrcode  # noqa: F401
except Exception:  # pragma: no cover - optional dependency fallback
    qrcode = None


class RecordsContainer(models.Model):
    _name = "records.container"
    _description = "Records Container"
    _inherit = ["mail.thread", "mail.activity.mixin", "barcodes.barcode_events_mixin", "records.container.movement.mixin"]
    _order = "create_date desc, name"

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Box Number",
        required=True,
        copy=False,
        tracking=True,
        help="Customer's name or number for this container. Examples:\n"
             "- 'HR Personnel 2024'\n"
             "- 'Legal Files - Smith Case'\n"
             "- 'Financial Records Q1 2023'\n"
             "Customer uses their own naming/numbering system. This is what appears on portal.\n"
             "EDITABLE: Customer can update this name at any time (except when destroyed)."
    )
    active = fields.Boolean(
        default=True,
        help="Uncheck to archive (mark as Destroyed). Archived containers are read-only and represent physically destroyed records."
    )
    color = fields.Integer(
        string="Color Index",
        default=0,
        help="Color index for kanban view and tags (0-11)"
    )
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, readonly=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True, comodel_name="res.currency")
    user_id = fields.Many2one(
        comodel_name="res.users",
        string="Responsible",
        tracking=True,
        help="User responsible for this container. Defaults to the department's responsible user "
             "when a department is selected. The dropdown shows users with their department name."
    )
    barcode = fields.Char(
        string="Physical Barcode",
        copy=False,
        index=True,
        tracking=True,
        help="Pre-printed barcode from sheet, assigned by staff during indexing.\n"
             "Used for scanning to retrieve all container metadata (name, location, customer, files, etc.).\n"
             "NOT auto-generated - manually assigned from physical barcode sheets.\n"
             "Scanning this barcode displays customer-defined container name and current status."
    )
    # Temporary barcode assigned at portal/customer creation time before a physical barcode is applied by technicians.
    # Remains immutable once a physical barcode is assigned. Searchable and billable reference.
    temp_barcode = fields.Char(
        string="Temporary Barcode",
        copy=False,
        index=True,
        tracking=True,
        help="System-generated temporary tracking barcode assigned when the customer creates the container in the portal.\n"
             "Used before physical barcode from pre-printed sheet is assigned during warehouse indexing."
    )
    barcode_assigned = fields.Boolean(
        string="Physical Barcode Assigned",
        compute="_compute_barcode_assigned",
        store=True,
        help="Indicates a physical warehouse barcode from pre-printed sheet has been assigned."
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain="[('is_records_customer', '=', True), ('is_company', '=', True)]",
        default=lambda self: self._default_partner_id(),
        help="The customer company for whom this container is being managed. Internal users can select any customer; portal users are restricted to their own company.",
    )
    department_id = fields.Many2one("records.department", string="Department", tracking=True)
    
    # Customer Staging Location (before pickup)
    customer_staging_location_id = fields.Many2one(
        comodel_name='customer.staging.location',
        string='Customer Staging Location',
        tracking=True,
        domain="[('partner_id', '=', partner_id)]",
        help="Virtual location at customer site where container is staged before pickup.\n"
             "Examples: 'City of EP/Records Dept/Basement/Room B-006'\n"
             "Technicians use this to locate containers during pickup."
    )

    # ============================================================================
    # LOCATION TRACKING - Native Odoo Stock Integration
    # ============================================================================
    location_id = fields.Many2one(
        "stock.location",
        string="Stock Location",
        tracking=True,
        domain="[('usage', '=', 'internal')]",
        help="WHERE YOU PUT THE CONTAINER: Set this to the aisle/row where you physically placed the box "
             "(e.g., Aisle 10/Row 0/000). This is the location you assign when storing the container."
    )
    # Backwards compatibility alias for Studio customizations
    stock_location_id = fields.Many2one(
        "stock.location",
        related="location_id",
        string="Stock Location (Legacy)",
        store=False,
        readonly=True,
        help="Alias for location_id - for backwards compatibility with Studio customizations."
    )
    quant_id = fields.Many2one(
        "stock.quant",
        string="Stock Quant",
        readonly=True,
        help="Inventory record in Odoo's stock system. "
             "Auto-created when container is activated. "
             "Links container to native inventory tracking."
    )
    package_id = fields.Many2one(
        "stock.quant.package",
        string="Stock Package",
        readonly=True,
        copy=False,
        help="Linked stock package for barcode scanning in Stock Barcode app. "
             "Auto-created when container is created. "
             "Syncs barcode with container barcode or temp_barcode."
    )
    stock_owner_id = fields.Many2one(
        "res.partner",
        string="Stock Owner",
        tracking=True,
        index=True,
        help="Inventory ownership hierarchy: Company → Department → Child Department. "
             "Auto-filled from Customer or Department selection. "
             "Organizational unit ownership (not individual users)."
    )
    current_location_id = fields.Many2one(
        "stock.location",
        related="quant_id.location_id",
        string="Current Location",
        store=True,
        readonly=True,
        help="REAL-TIME INVENTORY SYNC: Shows where the inventory system says the container is. "
             "Usually same as Stock Location unless moved via inventory transfers. "
             "Grayed out because it auto-updates from inventory movements - you don't set this manually."
    )
    temp_inventory_id = fields.Many2one(
        "temp.inventory",
        string="Temporary Inventory",
        domain="[('partner_id', '=', partner_id)]",
        help="Temporary location at customer site (portal users only). Used to track containers before pickup using temp barcodes and locations. Linked to official system after pickup for full lifecycle visibility. Filtered to show only locations belonging to the selected customer.",
    )
    container_type_id = fields.Many2one("records.container.type", string="Container Type", required=True)
    # Compatibility alias for legacy references and reporting convenience
    # Many existing views/controllers expect a `container_type` field (string)
    # Provide a stored related Char to the type name for grouping/read_group
    container_type = fields.Char(
        related="container_type_id.name",
        string="Container Type Name",
        store=True,
        readonly=True,
        help="Read-only name of the selected Container Type (for reporting/grouping)."
    )
    retention_policy_id = fields.Many2one("records.retention.policy", string="Retention Policy")
    document_type_id = fields.Many2one("records.document.type", string="Document Type")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection(
        [
            ("pending", "Pending"),      # Created but never scanned into internal location
            ("in", "In Storage"),        # At internal warehouse location
            ("out", "Out"),              # Transferred to customer via work order
            ("perm_out", "Perm-Out"),    # Permanent removal - returned to customer, service discontinued (active=False, removal fee only)
            ("destroyed", "Destroyed"),   # Physically destroyed/shredded (active=False, removal fee + shredding fee)
        ],
        string="Status",
        default="pending",
        required=True,
        tracking=True,
        help="Container status: PENDING = Created but not scanned in | IN = At internal location | OUT = With customer | PERM-OUT = Permanent removal (returned to customer, removal fee charged) | DESTROYED = Physically shredded (removal + shredding fees charged). Both perm_out and destroyed archive the container."
    )
    
    state_display = fields.Char(
        string="Status Display",
        compute='_compute_state_display',
        help="Shows current state or 'Destroyed' if archived"
    )

    # ============================================================================
    # PHYSICAL & CONTENT DETAILS
    # ============================================================================
    # Contextual label disambiguation (Batch 2): Clarify generic 'Description'
    description = fields.Text(string="Container Description")
    # Batch 3 label disambiguation
    content_description = fields.Text(string="Box Contents")
    # Intelligent Search metadata (alpha/date ranges, content type, keywords)
    alpha_range_start = fields.Char(
        string="Alpha Range Start",
        help="Starting letter of the primary alphabetical range for the contents (e.g., A).",
    )
    alpha_range_end = fields.Char(
        string="Alpha Range End",
        help="Ending letter of the primary alphabetical range for the contents (e.g., G).",
    )
    alpha_range_display = fields.Char(
        string="Alphabetical Range",
        compute="_compute_alpha_range_display",
        store=True,
        help="Computed display of the alphabetical range (e.g., 'A - G').",
    )
    alpha_range = fields.Char(
        string="Alpha Range (Searchable)",
        compute="_compute_alpha_range_display",
        store=True,
        index=True,
        help="Indexed field for fast searching. Same as alpha_range_display."
    )
    content_date_from = fields.Date(
        string="Content Date From",
        index=True,
        help="Earliest relevant content date contained in this container.",
    )
    content_date_to = fields.Date(
        string="Content Date To",
        index=True,
        help="Latest relevant content date contained in this container.",
    )
    # Alias fields for search compatibility
    date_range_start = fields.Date(
        string="Date Range Start",
        related="content_date_from",
        store=True,
        readonly=True
    )
    date_range_end = fields.Date(
        string="Date Range End", 
        related="content_date_to",
        store=True,
        readonly=True
    )
    content_date_range_display = fields.Char(
        string="Content Date Range",
        compute="_compute_content_date_range_display",
        store=True,
        help="Computed display of the content date range (e.g., '2024-01-01 to 2024-03-31').",
    )
    primary_content_type = fields.Selection(
        selection=[
            ("medical", "Medical"),
            ("financial", "Financial"),
            ("legal", "Legal"),
            ("personnel", "Personnel"),
            ("insurance", "Insurance"),
            ("mixed", "Mixed"),
            ("project", "Project"),
            ("compliance", "Compliance"),
            ("vendor", "Vendor"),
            ("customer", "Customer"),
            ("test", "Test"),
            ("international", "International"),
            ("digital", "Digital"),
            ("emergency", "Emergency"),
            ("litigation", "Litigation"),
            ("tax", "Tax"),
        ],
        default="mixed",
        string="Primary Content Type",
        help="Main classification of the contents to improve search suggestions.",
    )
    search_keywords = fields.Text(
        string="Search Keywords",
        help="Comma-separated keywords to improve findability (e.g., names, identifiers).",
    )
    dimensions = fields.Char(string="Dimensions", related="container_type_id.dimensions", readonly=True)
    weight = fields.Float(string="Weight (lbs)")
    cubic_feet = fields.Float(string="Cubic Feet", related="container_type_id.cubic_feet", readonly=True)
    is_full = fields.Boolean(string="Container Full", default=False)
    document_ids = fields.One2many("records.document", "container_id", string="Documents")
    document_count = fields.Integer(compute="_compute_document_count", string="Document Count", store=True)

    # File Folder Management
    file_ids = fields.One2many("records.file", "container_id", string="File Folders")
    file_count = fields.Integer(compute="_compute_file_count", string="File Count", store=True)

    # ============================================================================
    # BILLING & RATES (Derived from customer rates, then container type)
    # ============================================================================
    customer_rate_id = fields.Many2one(
        comodel_name="customer.negotiated.rate",
        string="Applied Rate",
        domain="[('rate_type', '=', 'storage'), ('is_current', '=', True), ('partner_id', '=', partner_id), ('container_type_id', '=', container_type_id)]",
        help="Storage rate applied to this container. When set, the container type is derived from the rate.",
        tracking=True,
    )
    monthly_rate_effective = fields.Monetary(
        string="Effective Monthly Rate",
        currency_field="currency_id",
        compute="_compute_effective_rate",
        store=True,
        help="The effective storage monthly rate charge for this container. Prefers approved negotiated rate; falls back to container type's standard rate.",
    )
    
    # Setup Fee Tracking - charged only once per container (tied to database ID)
    setup_fee_charged = fields.Boolean(
        string="Setup Fee Charged",
        default=False,
        copy=False,
        tracking=True,
        help="Indicates if the one-time initial setup fee has been invoiced for this container. "
             "Once charged, this is set to True and the fee will never be charged again, "
             "even if the container moves between temp inventory and stock locations."
    )
    setup_fee_invoice_id = fields.Many2one(
        comodel_name="account.move",
        string="Setup Fee Invoice",
        readonly=True,
        copy=False,
        help="The invoice on which this container's setup fee was charged."
    )
    setup_fee_date = fields.Date(
        string="Setup Fee Date",
        readonly=True,
        copy=False,
        help="Date when the setup fee was invoiced."
    )
    
    # Monthly Storage Fee Tracking
    last_storage_billing_date = fields.Date(
        string="Last Storage Billing Date",
        readonly=True,
        copy=False,
        help="Date of the last monthly storage fee billing for this container."
    )
    last_storage_billing_period_id = fields.Many2one(
        comodel_name="billing.period",
        string="Last Billing Period",
        readonly=True,
        copy=False,
        help="The last billing period for which storage fees were charged."
    )

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    storage_start_date = fields.Date(string="Storage Start Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date", readonly=True)
    destruction_due_date = fields.Date(
        string="Destruction Due Date", compute="_compute_destruction_due_date", store=True
    )
    destruction_date = fields.Date(string="Actual Destruction Date", readonly=True)
    permanent_retention = fields.Boolean(string="Permanent Retention", default=False)
    is_due_for_destruction = fields.Boolean(
        string="Due for Destruction", compute="_compute_is_due_for_destruction", search="_search_due_for_destruction"
    )

    # Virtual search helper flags replacing relativedelta usage in XML search filters
    stored_last_30d = fields.Boolean(
        string="Stored Last 30 Days",
        compute="_compute_storage_recency_flags",
        search="_search_stored_last_30d",
        help="True when storage_start_date is within the last 30 days.")
    destruction_due_6m = fields.Boolean(
        string="Destruction Due ≤6 Months",
        compute="_compute_storage_recency_flags",
        search="_search_destruction_due_6m",
        help="True when destruction_due_date is within the next ~6 months (180 days).")

    # ============================================================================
    # LEGAL CITATIONS & RECORD SERIES (Optional Compliance Features)
    # ============================================================================
    record_series_id = fields.Many2one(
        comodel_name='record.series',
        string='Record Series',
        tracking=True,
        help='Optional: Assign a record series for grouping and retention policy management. '
             'Record series can automatically set legal citations and disposition methods.'
    )
    legal_citation_ids = fields.Many2many(
        comodel_name='legal.citation',
        relation='container_legal_citation_rel',
        column1='container_id',
        column2='citation_id',
        string='Legal Citations',
        tracking=True,
        help='Optional: Legal citations that justify retention policy for this container. '
             'Can be inherited from record series or set manually.'
    )
    disposition_id = fields.Many2one(
        comodel_name='record.disposition',
        string='Disposition Method',
        tracking=True,
        help='Optional: How this container should be handled at end of retention (Shred, Archive, etc.). '
             'Can be inherited from record series or set manually.'
    )

    # ============================================================================
    # MOVEMENT & SECURITY
    # ============================================================================
    movement_ids = fields.One2many("records.container.movement", "container_id", string="Movement History")
    security_level = fields.Selection(
        [("1", "Standard"), ("2", "Confidential"), ("3", "High Security")], string="Security Level", default="1"
    )
    access_restrictions = fields.Text(string="Access Restrictions")

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    # SQL constraints
    _sql_constraints = [
        ('barcode_company_uniq', 'unique(barcode, company_id)', 'The barcode must be unique per company.'),
        ('temp_barcode_company_uniq', 'unique(temp_barcode, company_id)', 'The temporary barcode must be unique per company.'),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model
    def _get_default_container_type_id(self):
        """Resolve a safe default for container_type_id.

        Strategy:
        1) Use system parameter 'records_management.default_container_type_id' if set and valid.
        2) Fallback to the first active `records.container.type` (optionally scoped to current company when available).
        """
        # 1) System parameter (global)
        try:
            param_val = self.env["ir.config_parameter"].sudo().get_param(
                "records_management.default_container_type_id"
            )
        except Exception:
            param_val = None

        if param_val:
            try:
                ctype_id = int(param_val)
                if ctype_id:
                    ctype = self.env["records.container.type"].browse(ctype_id)
                    if ctype.exists() and (not hasattr(ctype, "active") or ctype.active):
                        return ctype.id
            except Exception:
                # Ignore malformed parameter values
                pass

        # 2) Fallback to first active container type (prefer current company if model supports it)
        comodel = self.env["records.container.type"]
        search_domain = [("active", "=", True)] if "active" in getattr(comodel, "_fields", {}) else []
        if "company_id" in getattr(comodel, "_fields", {}):
            search_domain.append(("company_id", "in", [False, self.env.company.id]))
        ctype = comodel.search(search_domain, order="sequence, name", limit=1)
        return ctype.id if ctype else False

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        if "container_type_id" in fields_list and not vals.get("container_type_id"):
            default_type_id = self._get_default_container_type_id()
            if default_type_id:
                vals["container_type_id"] = default_type_id
        return vals

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # Ensure required linkage to a partner to satisfy DB NOT NULL and test scenarios
            if not vals.get("partner_id"):
                # Prefer current user's partner; fallback to company partner; then root partner
                partner = self.env.user.partner_id or self.env.company.partner_id
                if not partner:
                    try:
                        partner = self.env.ref("base.partner_root")
                    except Exception:
                        partner = False
                if partner:
                    vals["partner_id"] = partner.id

            # Default stock_owner_id to partner_id if not explicitly set
            # Organizational hierarchy: Company → Department → Child Department
            if not vals.get("stock_owner_id") and vals.get("partner_id"):
                vals["stock_owner_id"] = vals["partner_id"]

            # ============================================================================
            # DEFAULT RESPONSIBLE USER FROM DEPARTMENT
            # ============================================================================
            # Priority: Department's responsible user > First department user > Current user
            if not vals.get("user_id"):
                user_set = False
                if vals.get("department_id"):
                    department = self.env['records.department'].browse(vals["department_id"])
                    if department.exists():
                        # Priority 1: Department's responsible user (user_id)
                        if department.user_id and department.user_id.active:
                            vals["user_id"] = department.user_id.id
                            user_set = True
                        # Priority 2: First active user in department's user_ids
                        elif department.user_ids:
                            active_users = department.user_ids.filtered(lambda u: u.active)
                            if active_users:
                                vals["user_id"] = active_users[0].id
                                user_set = True
                
                # Fallback: Current user if no department user found
                if not user_set:
                    vals["user_id"] = self.env.user.id

            # ⚠️ REMOVED: Automatic name generation
            # Customer must provide their own container name/number
            # No more auto-generated sequential names - customer controls naming

            # Ensure a safe default container type to satisfy NOT NULL constraints in tests/runtime
            if not vals.get("container_type_id"):
                default_type_id = self._get_default_container_type_id()
                if default_type_id:
                    vals["container_type_id"] = default_type_id

            # ⚠️ REMOVED: Automatic temp_barcode generation
            # Barcodes are pre-printed on sheets and manually assigned by staff
            # NO auto-generation - enforces manual workflow from physical barcode sheets

            # Billing starts at portal creation → if storage_start_date is empty set today
            if not vals.get("storage_start_date"):
                vals["storage_start_date"] = fields.Date.today()

        # Create records
        records = super().create(vals_list)

        # ✅ Create stock.quant.package for each container (enables Stock Barcode scanning)
        for record in records:
            record._create_or_update_stock_package()
        
        # ✅ Create stock.quant when container is scanned IN (not pending)
        for record in records:
            if record.state == 'in' and not record.quant_id:
                record._create_stock_quant()
        
        # Update location container counts
        records._update_location_counts()

        return records

    def write(self, vals):
        # Track old locations before write
        old_locations = self.mapped('location_id')
        
        if any(key in vals for key in ["location_id", "state"]) and "last_access_date" not in vals:
            vals["last_access_date"] = fields.Date.today()
        # Prevent changing temp_barcode after physical barcode assigned unless superuser context flag
        if "temp_barcode" in vals and any(rec.barcode for rec in self) and not self.env.context.get("allow_temp_barcode_edit"):
            vals.pop("temp_barcode")

        result = super().write(vals)

        # ✅ Sync stock.quant.package barcode when container barcode changes
        if 'barcode' in vals or 'temp_barcode' in vals:
            for record in self:
                record._create_or_update_stock_package()

        # ✅ Create stock.quant when container is scanned IN (state changes to 'in')
        # ✅ Also update child file folder states to match container state
        if 'state' in vals:
            for record in self:
                if record.state == 'in' and not record.quant_id:
                    record._create_stock_quant()
                
                # Sync file folder states with container state
                # When container goes IN, files should also be IN
                # When container goes OUT, files should also be OUT
                # When container is DESTROYED, files should also be DESTROYED
                if record.file_ids:
                    files_to_update = record.file_ids.filtered(
                        lambda f: f.state != record.state and f.state not in ('perm_out', 'destroyed')
                    )
                    if files_to_update:
                        files_to_update.write({'state': record.state})
                        record.message_post(
                            body=_('Updated %d file folder(s) to status: %s') % (
                                len(files_to_update), 
                                dict(record._fields['state'].selection).get(record.state, record.state)
                            )
                        )
        
        # Update location counts if location changed
        if 'location_id' in vals:
            new_locations = self.mapped('location_id')
            affected_locations = old_locations | new_locations
            # Location counts are handled via native quant_ids relationship
            pass
        
        return result

    def unlink(self):
        # Track locations before deletion
        locations = self.mapped('location_id')
        
        for record in self:
            if record.active:
                raise UserError(_("You can only delete archived (destroyed) containers. Use the Archive button to mark as destroyed first."))
            if record.document_ids:
                raise UserError(_("Cannot delete a container that has documents linked to it."))
        
        result = super().unlink()
        
        # Location counts are handled via native quant_ids relationship
        
        return result

    # ============================================================================
    # DEFAULT METHODS
    # ============================================================================
    def _default_partner_id(self):
        """
        Smart default for partner_id based on user type:
        - Portal users: Return their commercial partner (the company they belong to)
        - Internal users: Return False (no default, forces selection of customer)
        
        This ensures service provider workflow where internal employees manage
        containers for multiple customer companies.
        """
        user = self.env.user
        # Check if user is in portal group (not internal)
        if user.has_group('base.group_portal'):
            # Portal user - default to their commercial partner (company)
            return user.partner_id.commercial_partner_id.id if user.partner_id else False
        # Internal user - no default (must select customer)
        return False

    # ============================================================================
    # COMPUTE & SEARCH METHODS
    # ============================================================================
    @api.depends('state', 'active')
    def _compute_state_display(self):
        """Show 'Destroyed' when archived, otherwise show current state"""
        for container in self:
            if not container.active:
                container.state_display = "Destroyed"
            else:
                state_dict = dict(container._fields['state'].selection)
                container.state_display = state_dict.get(container.state, container.state)
    
    @api.depends("document_ids")
    def _compute_document_count(self):
        for container in self:
            container.document_count = len(container.document_ids)

    @api.depends("file_ids")
    def _compute_file_count(self):
        for container in self:
            container.file_count = len(container.file_ids)

    @api.depends("storage_start_date", "retention_policy_id.retention_years", "permanent_retention")
    def _compute_destruction_due_date(self):
        for container in self:
            if container.permanent_retention or not container.storage_start_date or not container.retention_policy_id:
                container.destruction_due_date = False
            else:
                retention_years = container.retention_policy_id.retention_years
                container.destruction_due_date = container.storage_start_date + relativedelta(years=retention_years)

    @api.depends("destruction_due_date", "permanent_retention", "state")
    def _compute_is_due_for_destruction(self):
        today = fields.Date.today()
        for container in self:
            container.is_due_for_destruction = bool(
                container.destruction_due_date
                and container.destruction_due_date <= today
                and not container.permanent_retention
                and container.active  # Only active (non-archived) containers
            )

    def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
        domain = [
            ("destruction_due_date", "<=", today),
            ("permanent_retention", "=", False),
            ("active", "=", True),  # Only active (non-archived)
        ]
        if (operator == "=" and value) or (operator == "!=" and not value):
            return domain

        # This handles the inverse case: (operator == '!=' and value) or (operator == '=' and not value)
        # which means we are searching for containers NOT due for destruction.
        inverse_domain = [
            "|",
            ("destruction_due_date", ">", today),
            "|",
            ("permanent_retention", "=", True),
            ("state", "=", "destroyed"),
        ]
        return inverse_domain

    @api.depends("alpha_range_start", "alpha_range_end")
    def _compute_alpha_range_display(self):
        for rec in self:
            start = (rec.alpha_range_start or "").strip()
            end = (rec.alpha_range_end or "").strip()
            if start and end:
                if start.upper() == end.upper():
                    display_value = start.upper()
                else:
                    display_value = "%s - %s" % (start.upper(), end.upper())
            elif start:
                display_value = start.upper()
            elif end:
                display_value = end.upper()
            else:
                display_value = False
            
            rec.alpha_range_display = display_value
            rec.alpha_range = display_value  # For indexed searching

    @api.depends("content_date_from", "content_date_to")
    def _compute_content_date_range_display(self):
        for rec in self:
            d_from = rec.content_date_from
            d_to = rec.content_date_to
            if d_from and d_to:
                rec.content_date_range_display = "%s to %s" % (d_from, d_to)
            elif d_from:
                rec.content_date_range_display = "%s" % (d_from)
            elif d_to:
                rec.content_date_range_display = "%s" % (d_to)
            else:
                rec.content_date_range_display = False

    # ------------------------------------------------------------------
    # RECENCY & DESTRUCTION VIRTUAL FLAGS
    # ------------------------------------------------------------------
    def _compute_storage_recency_flags(self):
        from datetime import timedelta
        today = fields.Date.today()
        cutoff = today - timedelta(days=30)
        six_months = today + timedelta(days=180)
        for rec in self:
            rec.stored_last_30d = bool(rec.storage_start_date and rec.storage_start_date >= cutoff)
            rec.destruction_due_6m = bool(rec.destruction_due_date and rec.destruction_due_date <= six_months)

    def _search_stored_last_30d(self, operator, value):
        from datetime import timedelta
        if operator not in ('=', '=='):
            return [('id', '!=', 0)]
        today = fields.Date.today()
        cutoff = today - timedelta(days=30)
        if value:
            return [('storage_start_date', '>=', cutoff)]
        return ['|', ('storage_start_date', '=', False), ('storage_start_date', '<', cutoff)]

    def _search_destruction_due_6m(self, operator, value):
        from datetime import timedelta
        if operator not in ('=', '=='):
            return [('id', '!=', 0)]
        today = fields.Date.today()
        six_months = today + timedelta(days=180)
        if value:
            return [('destruction_due_date', '<=', six_months)]
        return ['|', ('destruction_due_date', '=', False), ('destruction_due_date', '>', six_months)]

    # ============================================================================
    # ONCHANGE & HELPERS (Rates ↔ Container Type)
    # ============================================================================
    @api.onchange("customer_rate_id")
    def _onchange_customer_rate_id(self):
        """When a rate is chosen, derive the container type and partner if missing.

        Business rule:
        - If rate has container_type_id, apply it to container_type_id.
        - If partner not set but rate.partner_id exists, set partner.
        """
        if self.customer_rate_id:
            rate = self.customer_rate_id
            if getattr(rate, "container_type_id", False):
                self.container_type_id = rate.container_type_id.id
            if not self.partner_id and getattr(rate, "partner_id", False):
                self.partner_id = rate.partner_id.id

    @api.onchange("partner_id", "container_type_id")
    def _onchange_partner_type_autorate(self):
        """Auto-select the best matching current rate for this partner and type.

        Selection strategy:
        - Find active/current storage rates for partner & type, choose highest priority (lowest number),
          or most recent effective_date if priorities equal.
        - Do not override manually selected customer_rate_id if already set and matches partner & type.
        """
        if not self.partner_id or not self.container_type_id:
            return

        # Keep current selection if it matches
        if (
            self.customer_rate_id
            and self.customer_rate_id.partner_id == self.partner_id
            and self.customer_rate_id.container_type_id == self.container_type_id
            and self.customer_rate_id.state == "active"
            and self.customer_rate_id.is_current
        ):
            return

        rates = self.env["customer.negotiated.rate"].search(
            [
                ("partner_id", "=", self.partner_id.id),
                ("rate_type", "=", "storage"),
                ("container_type_id", "=", self.container_type_id.id),
                ("state", "=", "active"),
                ("is_current", "=", True),
            ],
            order="priority asc, effective_date desc",
            limit=1,
        )
        if rates:
            self.customer_rate_id = rates.id

    @api.onchange('container_type_id')
    def _onchange_container_type_default_weight(self):
        """Set default weight from container type's average weight.
        
        This provides a reasonable estimate for route planning and statistics.
        The weight field is typically hidden from portal users but used internally.
        """
        if self.container_type_id and self.container_type_id.average_weight_lbs:
            # Only set if weight hasn't been manually set
            if not self.weight or self.weight == 0:
                self.weight = self.container_type_id.average_weight_lbs

    @api.onchange('partner_id', 'department_id')
    def _onchange_partner_department_stock_owner(self):
        """
        Auto-set stock_owner_id and user_id based on organizational hierarchy.
        
        Ownership Hierarchy (all res.partner records):
        1. Company (top level): Main customer company
        2. Department (mid level): Organizational unit (child of company)
        3. Child Department (sub level): Subdivision (child of department, grandchild of company)
        
        Business Logic:
        - If department selected: stock_owner = department's partner contact
        - If only customer selected: stock_owner = customer company
        - Filter shows: Company + Departments (children) + Child Departments (grandchildren)
        
        Responsible User Logic:
        - If department selected: default to department's responsible user (user_id)
        - Fallback to first active user in department's user_ids
        - If no department: keep current user or leave empty
        
        Example:
        - Customer: City of Las Cruces (company)
        - Department: Fleet (child contact of City)
        - Child Dept: Vehicle Maintenance (child of Fleet, grandchild of City)
        - Stock Owner options: [City of Las Cruces, Fleet, Vehicle Maintenance, Parks, ...]
        """
        # Set stock_owner_id based on selections
        if self.department_id and self.department_id.partner_id:
            # Department selected - use department's partner contact as stock owner
            self.stock_owner_id = self.department_id.partner_id.id
        elif self.partner_id:
            # Only customer selected - use customer company as stock owner
            self.stock_owner_id = self.partner_id.id
        else:
            # No customer selected - clear stock owner
            self.stock_owner_id = False

        # ============================================================================
        # AUTO-SET RESPONSIBLE USER FROM DEPARTMENT
        # ============================================================================
        # When department changes, suggest the department's responsible user
        if self.department_id:
            # Priority 1: Department's responsible user (user_id field on department)
            if self.department_id.user_id and self.department_id.user_id.active:
                self.user_id = self.department_id.user_id.id
            # Priority 2: First active user in department's user_ids
            elif self.department_id.user_ids:
                active_users = self.department_id.user_ids.filtered(lambda u: u.active)
                if active_users:
                    self.user_id = active_users[0].id
            # If no department users found, leave user_id as-is (could be manually set)

        # Build domain to filter stock_owner_id options
        if self.partner_id:
            # Show company + departments (children) + child departments (grandchildren)
            return {
                'domain': {
                    'stock_owner_id': [
                        '|', '|',
                        ('id', '=', self.partner_id.id),  # Company itself
                        ('parent_id', '=', self.partner_id.id),  # Departments (children)
                        ('parent_id.parent_id', '=', self.partner_id.id)  # Child departments (grandchildren)
                    ]
                }
            }
        else:
            # No customer - clear domain
            return {'domain': {'stock_owner_id': []}}

    @api.depends("customer_rate_id.state", "customer_rate_id.is_current", "customer_rate_id.monthly_rate", "customer_rate_id.discount_percentage", "container_type_id.standard_rate")
    def _compute_effective_rate(self):
        """Compute the effective monthly storage rate.

        Contract:
        - If a current approved negotiated rate exists on the container, use its discounted value.
        - Otherwise, fall back to the container type's standard monthly rate.
        - Missing values resolve to 0.0.
        """
        for rec in self:
            value = 0.0
            rate = rec.customer_rate_id
            if rate and getattr(rate, "is_current", False) and getattr(rate, "state", "") == "active":
                # Use helper to apply discount logic if present
                try:
                    value = rate.get_effective_rate("monthly_rate")
                except Exception:
                    # Fallback to raw monthly_rate if helper unavailable
                    value = rate.monthly_rate or 0.0
            else:
                # Fallback to container type standard rate
                value = getattr(rec.container_type_id, "standard_rate", 0.0) or 0.0
            rec.monthly_rate_effective = value

    # ============================================================================
    # BUTTON ACTIONS
    # ============================================================================
    def action_activate(self):
        """Activate container for storage and create stock quant"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation"))

        # If location_id is set and no quant exists, create stock quant
        if self.location_id and not self.quant_id:
            # Get or create the generic container product
            product = self._get_or_create_container_product()

            quant_vals = {
                'product_id': product.id,
                'location_id': self.location_id.id,
                'quantity': 1.0,
                'owner_id': self.stock_owner_id.id or self.partner_id.id,  # Use stock owner hierarchy
                'company_id': self.company_id.id,
            }
            quant = self.env['stock.quant'].sudo().create(quant_vals)
            self.quant_id = quant.id

        self.write(
            {
                "state": "active",
            }
        )
        self.message_post(body=_("Container activated and ready for storage."))

    def action_mark_full(self):
        """Mark container as full"""
        self.ensure_one()
        self.write({"is_full": True})
        self.message_post(body=_("Container marked as full"))

    def action_schedule_destruction(self):
        """Schedule container for destruction"""
        self.ensure_one()
        if self.permanent_retention:
            raise UserError(_("Cannot schedule permanent retention containers for destruction"))
        if not self.is_due_for_destruction:
            raise UserError(_("This container is not yet due for destruction."))

        self.write({"state": "pending_destruction"})
        self.message_post(body=_("Container scheduled for destruction"))

    def action_destroy(self):
        """Mark container as destroyed"""
        self.ensure_one()
        if self.state != "pending_destruction":
            raise UserError(_("Only containers pending destruction can be destroyed"))

        self.write(
            {
                "state": "destroyed",
                "destruction_date": fields.Date.today(),
                "active": False,
            }
        )
        self.message_post(body=_("Container destroyed"))

    def action_view_documents(self):
        """View all documents in this container"""
        self.ensure_one()
        if not self.id:
            return {'type': 'ir.actions.act_window_close'}
        list_view_id = self.env.ref('records_management.records_document_view_list').id
        form_view_id = self.env.ref('records_management.records_document_view_form').id
        return {
            "name": _("Documents in Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.document",
            "view_mode": "list,form",
            "views": [(list_view_id, 'list'), (form_view_id, 'form')],
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id},
        }

    def action_view_files(self):
        """View all file folders in this container"""
        self.ensure_one()
        if not self.id:
            return {'type': 'ir.actions.act_window_close'}
        list_view_id = self.env.ref('records_management.records_file_view_list').id
        form_view_id = self.env.ref('records_management.records_file_view_form').id
        return {
            "name": _("File Folders in Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.file",
            "view_mode": "list,form",
            "views": [(list_view_id, 'list'), (form_view_id, 'form')],
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id},
        }

    def action_add_files(self):
        """Add new file folders to this container during indexing/scanning
        
        Used when:
        - Indexing container contents (scanning physical files in box)
        - Adding newly discovered files to existing container
        - Container receiving workflow
        
        Opens form to CREATE new file folder records that will belong to this container
        """
        self.ensure_one()
        form_view_id = self.env.ref('records_management.records_file_view_form').id
        return {
            "name": _("Add Files to Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.file",
            "view_mode": "form",
            "views": [(form_view_id, 'form')],
            "context": {
                "default_container_id": self.id,
                "default_partner_id": self.partner_id.id,
                "default_stock_owner_id": self.stock_owner_id.id if self.stock_owner_id else False,
                "default_location_id": self.location_id.id if self.location_id else False,
            },
            "target": "new",
        }

    def action_remove_files(self):
        """Check out files from container - creates retrieval order workflow
        
        Business Flow:
        1. User selects files to retrieve from container
        2. System creates retrieval order
        3. Warehouse staff locates container and files
        4. Files are barcoded and prepared for delivery
        5. Customer receives files
        
        Note: This is NOT deletion - files remain tracked for return
        """
        self.ensure_one()
        if not self.id:
            return {'type': 'ir.actions.act_window_close'}
        list_view_id = self.env.ref('records_management.records_file_view_list').id
        form_view_id = self.env.ref('records_management.records_file_view_form').id
        return {
            "name": _("Check Out Files from %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.file",
            "view_mode": "list,form",
            "views": [(list_view_id, 'list'), (form_view_id, 'form')],
            "domain": [("container_id", "=", self.id)],
            "context": {
                "container_checkout_mode": True,
                "active_container_id": self.id,
                "default_partner_id": self.partner_id.id,
            },
            "target": "new",
        }

    def action_generate_barcode(self):
        """
        Generates a barcode if one doesn't exist and returns an action to print it.
        This assumes a report with the external ID 'records_management.report_container_barcode' exists.
        """
        self.ensure_one()
        if not self.barcode:
            self.barcode = self.env["ir.sequence"].next_by_code("records.container.barcode") or self.name
        return self.env.ref("records_management.report_container_barcode").report_action(self)

    def action_assign_physical_barcode(self, barcode_value=None):
        """Assign a physical (warehouse) barcode, preserving the temporary barcode.

        Contract:
        - Fails if a physical barcode already exists unless context 'force_reassign' set.
        - Validates uniqueness via SQL constraint.
        - Posts chatter message with both refs.
        - Leaves temp_barcode unchanged and immutable after assignment.
        """
        self.ensure_one()

        # Handle case where method is called without arguments (UI button)
        if barcode_value is None:
            # Return action to open wizard for barcode assignment
            return {
                'type': 'ir.actions.act_window',
                'name': _('Assign Physical Barcode'),
                'res_model': 'records.container.assign.barcode.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {'default_container_id': self.id},
            }

        force_reassign = bool(self.env.context.get("force_reassign"))
        if self.barcode and not force_reassign:
            raise UserError(_("A physical barcode is already assigned. Use force_reassign in context to override."))
        if not barcode_value:
            raise UserError(_("A physical barcode value is required."))
        old_barcode = self.barcode
        self.write({"barcode": barcode_value})
        # Distinct audit + chatter messaging paths
        if force_reassign and old_barcode and old_barcode != barcode_value:
            # Forced reassignment path
            forced_msg = _("PHYSICAL BARCODE REASSIGNED (FORCED): %s → %s (temp %s)") % (
                old_barcode,
                barcode_value,
                self.temp_barcode or _("N/A"),
            )
            try:
                self.env['records.audit.log'].log_event(self, 'action', forced_msg)
            except Exception:
                pass
            self.message_post(body=forced_msg)
        else:
            # Initial assignment (or non-changing reassignment edge case)
            assign_msg = _("Physical barcode %s assigned (temporary reference %s).") % (
                barcode_value,
                self.temp_barcode or _("N/A"),
            )
            try:
                self.env['records.audit.log'].log_event(self, 'action', assign_msg)
            except Exception:
                pass
            self.message_post(body=assign_msg)
            if old_barcode and old_barcode != barcode_value:
                # Non-forced (should not usually occur) but keep legacy message for clarity
                self.message_post(body=_("Physical barcode changed from %s to %s") % (old_barcode, barcode_value))
        return True

    # ==========================================================================
    # TEMP BARCODE HELPERS
    # ==========================================================================
    def _generate_temp_barcode(self, vals=None):
        """Generate a temporary barcode.

        Strategy:
        1. Try dedicated sequence 'records.container.temp.barcode'.
        2. Fallback: TMP-<company>-<YYYYMMDD>-<zero padded sequence from container seq or random>.
        3. Ensure uniqueness (attempt up to 5 tries on collision).
        """
        import random, string
        date_part = fields.Date.today().strftime("%Y%m%d")
        company = self.env.company.id if self.env.company else 0
        attempt = 0
        while attempt < 5:
            seq = self.env["ir.sequence"].next_by_code("records.container.temp.barcode")
            if not seq:
                # Fallback simple random segment
                rand_seg = "".join(random.choices(string.ascii_uppercase + string.digits, k=6))
                seq = f"TMP-{company}-{date_part}-{rand_seg}"
            # Check uniqueness quickly (no full search if likely unique)
            exists = self.env["records.container"].sudo().search_count([("temp_barcode", "=", seq)])
            if not exists:
                # Audit log only if context indicates creation phase
                if self.env.context.get('creating_temp_barcode_log'):
                    try:
                        self.env['records.audit.log'].log_event(self, 'action', _("Temporary barcode %s generated") % seq)
                    except Exception:
                        pass
                return seq
            attempt += 1
        # Final fallback with high entropy
        rand_seg = "".join(random.choices(string.ascii_uppercase + string.digits, k=10))
        return f"TMP-{company}-{date_part}-{rand_seg}"

    @api.depends("barcode")
    def _compute_barcode_assigned(self):
        for rec in self:
            rec.barcode_assigned = bool(rec.barcode)

    # ==========================================================================
    # SEARCH EXTENSIONS
    # ==========================================================================
    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):  # type: ignore[override]
        args = list(args or [])
        if name:
            # Expand search to include temp_barcode and barcode
            domain = ['|', '|', ('name', operator, name), ('barcode', operator, name), ('temp_barcode', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

    def action_store_container(self):
        """
        Store Container Workflow:
        1. Generate field service ticket for pickup
        2. Change status to 'pending_pickup' 
        3. After pickup/location assignment → changes to 'in_storage'
        
        This creates the complete workflow from customer request to warehouse storage.
        """
        self.ensure_one()

        # Can process containers that are pending or already in storage
        if self.state == 'out':
            raise UserError(_("Cannot process containers that are OUT with customer. Request return first."))

        # Create field service ticket for pickup
        fsm_project = self.env['project.project'].search([
            ('is_fsm', '=', True)
        ], limit=1)

        if not fsm_project:
            raise UserError(_("No Field Service Management project found. Please configure FSM first."))

        # Create the pickup task
        task_vals = {
            'name': _('Pickup Container: %s', self.name),
            'project_id': fsm_project.id,
            'partner_id': self.partner_id.id,
            'description': _(
                'Container Pickup Request\n'
                'Container: %s\n'
                'Customer: %s\n'
                'Department: %s\n'
                'Please pick up this container and assign it to a warehouse location.',
                self.name,
                self.partner_id.name,
                self.department_id.name if self.department_id else 'N/A'
            ),
            'container_ids': [(6, 0, [self.id])],
        }

        pickup_task = self.env['project.task'].create(task_vals)

        # Change container state to in storage
        vals = {
            'state': 'in',
        }
        if not self.storage_start_date:
            vals['storage_start_date'] = fields.Date.today()

        self.write(vals)

        # Post message with link to service ticket
        self.message_post(
            body=_('Field service ticket created for container pickup. <a href="/web#id=%s&model=project.task&view_type=form">View Ticket #%s</a>',
                   pickup_task.id, pickup_task.id)
        )

        # Return action to view the created task
        return {
            'name': _('Pickup Service Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': pickup_task.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_retrieve_container(self):
        """Retrieve container from storage - creates work order and billing charge"""
        self.ensure_one()
        if self.state not in ["in"]:
            raise UserError(_("Only containers in storage can be retrieved"))
        
        # Create retrieval work order
        work_order = self.env['records.retrieval.work.order'].create({
            'name': _('New'),
            'partner_id': self.partner_id.id,
            'company_id': self.company_id.id or self.env.company.id,
            'delivery_method': 'physical',
            'scanned_barcode_ids': [(6, 0, [self.id])],
        })
        
        # Create billing charge for retrieval service
        retrieval_product = self.env.ref('records_management.product_retrieval_service', raise_if_not_found=False)
        if retrieval_product and self.partner_id:
            # Get retrieval rate - check customer negotiated rate first, then product price
            retrieval_rate = self._get_retrieval_rate(retrieval_product)
            
            # Find or create billing record for this period
            today = fields.Date.today()
            billing = self.env['records.billing'].sudo().search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'draft'),
                ('date', '>=', today.replace(day=1)),
            ], limit=1)
            if not billing:
                # Get default billing config
                billing_config = self.env['records.billing.config'].sudo().search([
                    ('company_id', '=', self.env.company.id),
                ], limit=1)
                if billing_config:
                    billing = self.env['records.billing'].sudo().create({
                        'partner_id': self.partner_id.id,
                        'date': today,
                        'billing_config_id': billing_config.id,
                        'state': 'draft',
                    })
            if billing:
                self.env['advanced.billing.line'].sudo().create({
                    'billing_id': billing.id,
                    'name': _('Container Retrieval - %s') % self.name,
                    'product_id': retrieval_product.id,
                    'quantity': 1,
                    'amount': retrieval_rate,
                    'type': 'service',
                })
        
        # Update container state
        self.write({"state": "out", "last_access_date": fields.Date.today()})
        self.message_post(body=_("Container retrieved from storage - Work Order: %s") % work_order.name)
        
        # Return action to view work order
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retrieval Work Order'),
            'res_model': 'records.retrieval.work.order',
            'res_id': work_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _get_retrieval_rate(self, product):
        """Get the retrieval rate for billing.
        
        Rate lookup order:
        1. Customer's negotiated rate (if retrieval_rate field exists)
        2. Base rate (if retrieval_rate field exists)
        3. Product list price
        """
        if self.partner_id:
            # Try customer's negotiated rate
            negotiated_rate = self.env['customer.negotiated.rate'].sudo().search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'active'),
            ], limit=1)
            if negotiated_rate and hasattr(negotiated_rate, 'retrieval_rate') and negotiated_rate.retrieval_rate:
                return negotiated_rate.retrieval_rate
        
        # Try base rate
        base_rate = self.env['records.base.rate'].sudo().search([
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        if base_rate and hasattr(base_rate, 'retrieval_rate') and base_rate.retrieval_rate:
            return base_rate.retrieval_rate
        
        # Fall back to product price
        return product.list_price if product else 35.00

    def action_bulk_convert_container_type(self):
        """Bulk convert container types"""
        self.ensure_one()
        return {
            "name": _("Bulk Convert Container Types"),
            "type": "ir.actions.act_window",
            "res_model": "records.container.type.converter",
            "view_mode": "form",
            "target": "new",
            "context": {"default_container_ids": [(6, 0, self.ids)]},
        }

    def action_generate_qr_code(self):
        """Generate secure QR code for the container
        
        QR code contains secure portal URL requiring authentication.
        Prevents unauthorized access to sensitive container metadata.
        """
        self.ensure_one()
        
        # Return QR code report action
        return self.env.ref('records_management.report_container_qrcode').report_action(self)

    # ============================================================================
    # SMART BUTTON ACTIONS (Stock Integration)
    # ============================================================================
    def action_view_stock_quant(self):
        """
        Smart button: View container's stock quant in Inventory system.
        Opens the stock.quant record showing inventory details.
        """
        self.ensure_one()

        if not self.quant_id:
            raise UserError(_(
                "This container is not yet in the inventory system.\n"
                "Please index the container first by clicking 'Index Container' button."
            ))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Quant: %s') % self.name,
            'res_model': 'stock.quant',
            'res_id': self.quant_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False},
        }

    def action_view_stock_location(self):
        """
        Smart button: View container's stock location.
        Opens the stock.location record showing location details.
        """
        self.ensure_one()

        if not self.location_id:
            raise UserError(_(
                "No stock location assigned to this container.\n"
                "Please assign a stock location or index the container."
            ))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Location: %s') % self.location_id.complete_name,
            'res_model': 'stock.location',
            'res_id': self.location_id.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False},
        }

    # ============================================================================
    # STOCK INTEGRATION METHODS
    # ============================================================================
    def _create_or_update_stock_package(self):
        """
        Create or update stock.quant.package for this container.
        
        This enables container barcodes to be recognized by the Stock Barcode app:
        - Creates a package with matching barcode (uses barcode or temp_barcode)
        - Links container to package via package_id field
        - Syncs barcode when container barcode changes
        
        Stock packages are just tracking containers - NO stock valuation impact.
        Valuation is controlled by product categories, not packages.
        """
        self.ensure_one()
        
        # Determine which barcode to use (prefer physical barcode over temp)
        package_barcode = self.barcode or self.temp_barcode
        
        if not package_barcode:
            # No barcode yet - nothing to sync
            return
        
        Package = self.env['stock.quant.package'].sudo()
        
        if self.package_id:
            # Package exists - update barcode if changed
            if self.package_id.name != package_barcode:
                self.package_id.write({
                    'name': package_barcode,
                })
        else:
            # Check if package with this barcode already exists
            existing_package = Package.search([('name', '=', package_barcode)], limit=1)
            
            if existing_package:
                # Link to existing package
                self.write({'package_id': existing_package.id})
            else:
                # Create new package
                package = Package.create({
                    'name': package_barcode,
                    'company_id': self.company_id.id,
                    'location_id': self.location_id.id if self.location_id else False,
                })
                self.write({'package_id': package.id})
    
    def _create_stock_quant(self):
        """
        Create stock.quant for this container in Odoo's inventory system.
        
        This integrates the container with native Odoo stock tracking:
        - Creates a quant (inventory on-hand record)
        - Sets location to location_id (native stock.location)
        - Sets owner to partner_id (customer ownership)
        - Quantity = 1 (one container)
        
        Called automatically when container state changes from draft to active.
        
        TEMPORARILY DISABLED - Product type field compatibility issue
        """
        self.ensure_one()
        return  # Disabled until product type field resolved

        # Don't create duplicate quants
        if self.quant_id:
            return self.quant_id

        # Get or create default records location
        stock_location = self.location_id  # Use location_id (now stock.location)
        if not stock_location:
            # Find or create a default "Records Storage" location
            stock_location = self.env['stock.location'].search([
                ('usage', '=', 'internal'),
                ('company_id', '=', self.company_id.id),
                ('name', 'ilike', 'Records Storage'),
            ], limit=1)

            if not stock_location:
                # Use WH/Stock as parent (standard Odoo location that always exists)
                # This is the main warehouse stock location, guaranteed to be usage='internal'
                wh_stock = self.env.ref('stock.stock_location_stock', raise_if_not_found=False)

                if not wh_stock:
                    # Fallback: search for any location named 'Stock' with usage='internal'
                    wh_stock = self.env['stock.location'].search([
                        ('usage', '=', 'internal'),
                        ('name', '=', 'Stock'),
                    ], limit=1)

                # Create Records Storage as child of WH/Stock
                stock_location = self.env['stock.location'].create({
                    'name': 'Records Storage',
                    'usage': 'internal',
                    'location_id': wh_stock.id if wh_stock else False,
                    'company_id': self.company_id.id,
                })

        # Get or create product for containers (needed for stock.quant)
        product = self._get_or_create_container_product()

        # Create the stock quant with organizational ownership
        quant = self.env['stock.quant'].create({
            'product_id': product.id,
            'location_id': stock_location.id,
            'owner_id': self.stock_owner_id.id or self.partner_id.id,  # Department/child dept or company
            'quantity': 1,  # One container
            'company_id': self.company_id.id,
        })

        # Link quant to container
        self.write({
            'quant_id': quant.id,
            'location_id': stock_location.id,  # Use location_id (now stock.location)
        })

        # Post message to chatter
        self.message_post(
            body=_("Stock quant created: Container integrated with Odoo inventory system at location %s") % stock_location.complete_name
        )

        return quant

    def _get_or_create_container_product(self):
        """
        Get or create a generic 'Records Container' product for stock tracking.
        
        Stock.quant requires a product_id, so we use a generic product to represent
        all records containers. The actual container details are in records.container.
        """
        # Try to find existing product
        product = self.env['product.product'].search([
            ('default_code', '=', 'RECORDS-CONTAINER'),
            ('company_id', 'in', [False, self.company_id.id]),
        ], limit=1)

        if not product:
            # Create generic container product - consumable for inventory tracking
            # Odoo 18: Use 'type' = 'consu' (consumable)

            product_vals = {
                'name': 'Records Container (Generic)',
                'default_code': 'RECORDS-CONTAINER',
                'type': 'consu',  # Odoo 18: 'consu' type for consumable products
                'categ_id': self.env.ref('product.product_category_all').id,
                'list_price': 0.0,
                'standard_price': 0.0,
                'description': 'Generic storable product for records container inventory tracking. '
                              'Actual container details are in Records Management module.',
                'company_id': False,  # Available to all companies
            }

            product = self.env['product.product'].create(product_vals)

        return product

    def action_index_container(self):
        """
        Launch Container Indexing Service wizard.
        
        Creates a complete manifest of ALL files in the container with barcodes
        for premium customers who want comprehensive tracking. This is different
        from on-the-fly file addition during retrieval requests.
        """
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Container Indexing Service - Complete Manifest'),
            'res_model': 'container.indexing.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_container_id': self.id,
                'default_container_name': self.name,
                'default_customer_id': self.partner_id.id if self.partner_id else False,
                'default_barcode': self.barcode or False,
            }
        }

    def _index_container_with_files(self, barcode, file_data_list):
        """
        Internal method to complete container indexing with files.
        Called from the indexing wizard.
        
        Args:
            barcode (str): Physical barcode to assign
            file_data_list (list): List of file dictionaries to create
        """
        self.ensure_one()

        if self.state != 'pending':
            raise UserError(_("Only pending containers can be indexed"))

        # Assign barcode
        if barcode and barcode != self.barcode:
            self.barcode = barcode

        # Validate barcode assigned
        if not self.barcode:
            raise UserError(_(
                "Cannot index container without physical barcode. "
                "Please assign a barcode from the pre-printed sheet first."
            ))

        # Create stock quant if not exists
        if not self.quant_id:
            self._create_stock_quant()

        # Create files in bulk
        created_files = []
        for file_data in file_data_list:
            if file_data.get('name'):  # Only create files with names
                file_vals = {
                    'name': file_data['name'],
                    'description': file_data.get('description', ''),
                    'container_id': self.id,
                    'partner_id': self.partner_id.id,
                    'file_category': file_data.get('file_category', 'general'),
                    'received_date': file_data.get('received_date') or fields.Date.today(),
                    'barcode': file_data.get('barcode', ''),
                    'temp_barcode': file_data.get('temp_barcode', ''),
                }
                file_record = self.env['records.file'].create(file_vals)
                created_files.append(file_record)

        # Update container state to in storage
        self.write({
            'state': 'in',
        })

        # Post message
        files_msg = ""
        if created_files:
            files_msg = _(" and %d files created") % len(created_files)

        self.message_post(
            body=_("Container indexed with barcode %s%s") % (self.barcode, files_msg)
        )

        return {
            'created_files_count': len(created_files),
            'created_file_names': [f.name for f in created_files]
        }

    def action_move_container(self, new_location_id=None):
        """
        Move container to new location using stock.picking (proper Odoo way).
        
        Args:
            new_location_id: ID of destination stock.location
        
        This creates a proper stock transfer (picking) to move the container,
        which creates audit trail and updates quant.location_id automatically.
        """
        self.ensure_one()

        # Handle case where method is called without arguments (UI button)
        if new_location_id is None:
            # Return action to open location selection wizard
            return {
                'type': 'ir.actions.act_window',
                'name': _('Move Container'),
                'res_model': 'stock.location',
                'view_mode': 'list',
                'target': 'new',
                'domain': [('usage', '=', 'internal')],
                'context': {
                    'search_default_internal': 1,
                    'container_id': self.id,
                },
            }

        if not self.quant_id:
            raise UserError(_("Container not in inventory system. Please index it first."))

        new_location = self.env['stock.location'].browse(new_location_id)
        current_location = self.quant_id.location_id

        if current_location == new_location:
            raise UserError(_("Container is already at location %s") % new_location.complete_name)

        # Create stock picking (transfer)
        picking = self.env['stock.picking'].create({
            'picking_type_id': self.env.ref('stock.picking_type_internal').id,
            'location_id': current_location.id,
            'location_dest_id': new_location.id,
            'origin': _("Container Move: %s") % self.name,
        })

        # Create stock move
        product = self.quant_id.product_id
        move = self.env['stock.move'].create({
            'name': self.name,
            'product_id': product.id,
            'product_uom_qty': 1,
            'product_uom': product.uom_id.id,
            'picking_id': picking.id,
            'location_id': current_location.id,
            'location_dest_id': new_location.id,
        })

        # Confirm and execute transfer
        picking.action_confirm()
        picking.action_assign()
        for move_line in picking.move_line_ids:
            move_line.quantity = 1
        picking.button_validate()

        # Update container record
        self.write({
            'location_id': new_location.id,
        })

        # Post message
        self.message_post(
            body=_("Container moved from %s to %s") % (current_location.complete_name, new_location.complete_name)
        )

        return picking

    # ============================================================================
    # BARCODE SCANNING INTEGRATION (Odoo Barcode Infrastructure)
    # ============================================================================
    def on_barcode_scanned(self, barcode):
        """
        Handle barcode scanning events from Odoo's barcode scanner.
        
        Integrates with Odoo's native barcode infrastructure:
        - Inherits from barcodes.barcode_events_mixin
        - Automatically called when barcode is scanned
        - Supports GS1, UPC, EAN nomenclature via barcode.nomenclature
        - Works with mobile barcode app and USB/Bluetooth scanners
        
        Args:
            barcode (str): Scanned barcode value (processed through nomenclature rules)
        
        Returns:
            dict: Action to open the scanned container's form view
        
        Raises:
            UserError: If barcode not found or multiple matches exist
        
        Workflow:
            1. Search for container by physical barcode (primary)
            2. Fallback to temp_barcode if physical barcode not assigned
            3. Open container form view
            4. Post chatter message for audit trail
        
        Example Usage:
            - Scan barcode in Inventory app → Container opens
            - Scan barcode in Barcode app → Container details displayed
            - Mobile app scanning → Instant container lookup
        """
        # Search by physical barcode first (preferred)
        container = self.env['records.container'].search([
            ('barcode', '=', barcode),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        # Fallback to temp barcode if physical barcode not assigned yet
        if not container:
            container = self.env['records.container'].search([
                ('temp_barcode', '=', barcode),
                ('company_id', '=', self.env.company.id)
            ], limit=1)

        if not container:
            raise UserError(_('No container found with barcode: %s') % barcode)

        # Post audit message
        container.message_post(
            body=_('Container scanned via barcode: %s') % barcode,
            message_type='notification'
        )

        # Return action to open container form
        return {
            'type': 'ir.actions.act_window',
            'name': _('Container: %s') % container.name,
            'res_model': 'records.container',
            'res_id': container.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'create': False},
        }

    # ============================================================================
    # ENHANCED STOCK INTEGRATION METHODS
    # ============================================================================

    def get_stock_summary(self):
        """
        Customer-friendly stock summary for portal display.
        Returns comprehensive stock status and location information.
        """
        self.ensure_one()

        # Get stock quant information
        quant_data = {}
        if self.quant_id:
            quant_data = {
                'quantity': self.quant_id.quantity,
                'location': self.quant_id.location_id.complete_name,
                'last_update': self.quant_id.write_date,
                'owner': self.quant_id.owner_id.name if self.quant_id.owner_id else None,
            }

        # Get movement summary
        movement_summary = self._get_movement_summary()

        return {
            'container_name': self.name,
            'barcode': self.barcode or self.temp_barcode,
            'current_location': self.current_location_id.complete_name if self.current_location_id else 'Unknown',
            'state': self.state,
            'quant_data': quant_data,
            'movement_summary': movement_summary,
            'partner_name': self.partner_id.name,
        }

    def _get_movement_summary(self):
        """Get movement summary statistics"""
        total_movements = len(self.movement_ids)
        recent_movements = self.movement_ids.filtered(
            lambda m: m.movement_date and
            (fields.Datetime.now() - m.movement_date).days <= 30
        )

        return {
            'total_movements': total_movements,
            'recent_movements': len(recent_movements),
            'last_movement_date': self.last_movement_date,
            'last_movement_location': self.last_movement_location,
        }

    def move_to_location(self, location, reason=None, movement_type='location_change'):
        """
        Move container to new location with comprehensive tracking.
        
        Args:
            location: stock.location record
            reason: optional reason for the movement
            movement_type: type of movement (default: 'location_change')
        
        Returns:
            records.stock.movement record
        """
        self.ensure_one()

        # Create movement record
        movement = self.create_movement(
            to_location=location,
            movement_type=movement_type,
            reason=reason
        )

        # Confirm the movement (updates quant and location)
        movement.action_confirm()

        return movement

    def sync_with_stock_quant(self):
        """
        Synchronize container location with stock quant location.
        Called automatically when quant location changes.
        """
        self.ensure_one()

        if not self.quant_id:
            return

        # Check if locations are out of sync
        if self.location_id != self.quant_id.location_id:
            old_location = self.location_id
            new_location = self.quant_id.location_id

            # Update container location to match quant
            self.write({'location_id': new_location.id})

            # Create automatic movement record
            self.env['records.stock.movement'].sudo().create_movement(
                container=self,
                to_location=new_location,
                movement_type='adjustment',
                reason=f'Auto-sync with stock system. Previous location: {old_location.complete_name if old_location else "Unknown"}',
            )

            # Log the sync
            self.message_post(
                body=_("Location automatically synchronized with stock system: %s → %s") % (
                    old_location.complete_name if old_location else 'Unknown',
                    new_location.complete_name
                ),
                message_type='notification'
            )

    @api.model
    def sync_all_containers_with_stock(self):
        """
        Batch synchronization of all containers with their stock quants.
        Can be called via cron job for regular sync maintenance.
        """
        containers = self.search([('quant_id', '!=', False)])
        synced_count = 0

        for container in containers:
            if container.location_id != container.quant_id.location_id:
                container.sync_with_stock_quant()
                synced_count += 1

        if synced_count > 0:
            _logger.info(f"Synchronized {synced_count} containers with stock system")

        return synced_count

    def get_stock_movement_history(self, limit=None, movement_type=None):
        """
        Get formatted movement history for this container.
        
        Args:
            limit: maximum number of records (default: all)
            movement_type: filter by movement type (optional)
        
        Returns:
            list of formatted movement data
        """
        self.ensure_one()
        if not self.id:
            return []

        domain = [('container_id', '=', self.id)]
        if movement_type:
            domain.append(('movement_type', '=', movement_type))

        movements = self.env['records.stock.movement'].search(
            domain,
            order='movement_date desc',
            limit=limit
        )

        return movements.get_portal_movements(self.partner_id)['movements']

    # ============================================================================
    # LABEL PRINTING METHODS (ZPL + Labelary API)
    # ============================================================================
    
    def action_print_barcode_label(self):
        """
        Generate and download a professional barcode label for this container.
        
        Enhanced features:
        - Checks if barcode was previously printed (requires signature for reprint)
        - Logs print action in chatter with timestamp and user
        - Attaches PDF to record for easy reprinting
        - Uses ZPL + Labelary API for professional output
        
        Label size: 4" x 1.33" (standard Avery-compatible sheet, 14 per page)
        """
        self.ensure_one()
        
        barcode = self.barcode or self.temp_barcode
        if not barcode:
            raise UserError(_("Container must have a barcode before printing labels."))
        
        # Check if this barcode was previously printed
        previous_print = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'container_label'),
        ], limit=1)
        
        if previous_print:
            # Require signature for reprint
            return {
                'name': _('Confirm Barcode Reprint'),
                'type': 'ir.actions.act_window',
                'res_model': 'barcode.reprint.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_container_id': self.id,
                    'default_barcode': barcode,
                    'default_previous_print_date': previous_print.create_date,
                    'default_record_type': 'container',
                }
            }
        
        # Generate label using ZPL service
        generator = self.env['zpl.label.generator']
        result = generator.generate_container_label(self)
        
        # Create attachment for download and easy reprinting
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
            'description': f"Container barcode label printed by {self.env.user.name}",
        })
        
        # Log in chatter
        self.message_post(
            body=_("Container barcode label printed by %s<br/>Barcode: <strong>%s</strong>") % (
                self.env.user.name,
                barcode
            ),
            subject=_("Barcode Label Printed"),
            attachment_ids=[attachment.id],
        )
        
        # Return download action
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def action_print_qr_label(self):
        """
        Generate QR code label that links to customer portal login.
        
        Label size: 1" x 1.25" (49 per sheet)
        QR code directs users to portal where they can log in and view container details.
        Logs print action in chatter.
        """
        self.ensure_one()
        
        generator = self.env['zpl.label.generator']
        result = generator.generate_qr_label(self, record_type='container')
        
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
            'description': f"QR code label printed by {self.env.user.name}",
        })
        
        # Log in chatter
        self.message_post(
            body=_("QR code label printed by %s") % self.env.user.name,
            subject=_("QR Label Printed"),
            attachment_ids=[attachment.id],
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    @api.model
    def action_print_batch_labels(self, container_ids=None):
        """
        Print barcode labels for multiple containers in a single PDF.
        
        Enhanced features:
        - Handles errors gracefully (missing barcodes, API failures)
        - Allows retry on partial failures
        - Logs each container's print in its chatter
        - Attaches PDF to a batch tracking record
        
        Args:
            container_ids (list): List of container IDs to print labels for.
                                 If None, uses active_ids from context.
        
        Returns:
            Action to download multi-page PDF with all labels, or wizard for errors.
        """
        if container_ids is None:
            container_ids = self.env.context.get('active_ids', [])
        
        if not container_ids:
            raise UserError(_("No containers selected for batch label printing."))
        
        containers = self.browse(container_ids)
        
        # Check for containers without barcodes
        missing_barcodes = containers.filtered(lambda c: not c.barcode and not c.temp_barcode)
        if missing_barcodes:
            return {
                'name': _('Containers Missing Barcodes'),
                'type': 'ir.actions.act_window',
                'res_model': 'batch.label.error.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_container_ids': [(6, 0, container_ids)],
                    'default_missing_barcode_ids': [(6, 0, missing_barcodes.ids)],
                    'default_error_type': 'missing_barcode',
                }
            }
        
        # Check for previously printed barcodes
        previously_printed = []
        for container in containers:
            prev = self.env['ir.attachment'].search([
                ('res_model', '=', 'records.container'),
                ('res_id', '=', container.id),
                ('name', 'ilike', 'container_label'),
            ], limit=1)
            if prev:
                previously_printed.append(container.id)
        
        if previously_printed:
            # Require signature for batch reprint
            return {
                'name': _('Confirm Batch Barcode Reprint'),
                'type': 'ir.actions.act_window',
                'res_model': 'barcode.batch.reprint.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_container_ids': [(6, 0, container_ids)],
                    'default_reprint_ids': [(6, 0, previously_printed)],
                    'default_record_type': 'container',
                }
            }
        
        # Generate batch labels
        try:
            generator = self.env['zpl.label.generator']
            result = generator.generate_batch_container_labels(containers)
            
            # Create batch tracking record
            batch_record = self.env['barcode.batch.print'].create({
                'record_type': 'container',
                'record_count': len(containers),
                'printed_by_id': self.env.user.id,
                'print_date': fields.Datetime.now(),
            })
            
            attachment = self.env['ir.attachment'].create({
                'name': result['filename'],
                'type': 'binary',
                'datas': result['pdf_data'],
                'res_model': batch_record._name,
                'res_id': batch_record.id,
                'mimetype': 'application/pdf',
                'description': f"Batch print of {len(containers)} container labels",
            })
            
            batch_record.attachment_id = attachment.id
            
            # Log in each container's chatter
            for container in containers:
                container.message_post(
                    body=_("Included in batch label print by %s<br/>Batch: %s<br/>Total labels: %s") % (
                        self.env.user.name,
                        batch_record.name,
                        len(containers)
                    ),
                    subject=_("Batch Label Printed"),
                )
            
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{attachment.id}?download=true',
                'target': 'new',
            }
        except Exception as e:
            raise UserError(_("Error generating batch labels: %s") % str(e))

    # ============================================================================
    # BILLING & WORK ORDER AUTOMATION METHODS
    # ============================================================================
    
    def _create_destruction_charges(self):
        """
        Create invoice charges for container destruction.
        
        Destruction includes:
        - Per-item removal fee
        - Per-item shredding fee
        
        Creates 2 invoice line items.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Cannot create destruction charges: No customer assigned to container %s") % (self.barcode or self.name))
        
        # Get or create draft invoice for customer
        invoice = self._get_or_create_draft_invoice()
        
        # Get product for removal fee
        removal_product = self._get_removal_fee_product()
        shredding_product = self._get_shredding_fee_product()
        
        # Create invoice lines
        invoice_line_vals = [
            {
                'product_id': removal_product.id,
                'name': _('Container Removal Fee - %s') % (self.barcode or self.name),
                'quantity': 1,
                'price_unit': removal_product.list_price,
                'move_id': invoice.id,
            },
            {
                'product_id': shredding_product.id,
                'name': _('Container Shredding Fee - %s') % (self.barcode or self.name),
                'quantity': 1,
                'price_unit': shredding_product.list_price,
                'move_id': invoice.id,
            }
        ]
        
        self.env['account.move.line'].create(invoice_line_vals)
        
        # Log charge creation
        self.message_post(
            body=_("Destruction charges created:<br/>• Removal fee: %s<br/>• Shredding fee: %s<br/>Total: %s") % (
                removal_product.list_price,
                shredding_product.list_price,
                removal_product.list_price + shredding_product.list_price
            ),
            subject=_("Destruction Charges Created")
        )
        
        return invoice
    
    def _create_removal_charges(self):
        """
        Create invoice charges for permanent removal (perm-out).
        
        Perm-Out includes:
        - Per-item removal fee ONLY (no shredding)
        
        Creates 1 invoice line item.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Cannot create removal charges: No customer assigned to container %s") % (self.barcode or self.name))
        
        # Get or create draft invoice for customer
        invoice = self._get_or_create_draft_invoice()
        
        # Get product for removal fee
        removal_product = self._get_removal_fee_product()
        
        # Create invoice line
        invoice_line_vals = {
            'product_id': removal_product.id,
            'name': _('Container Removal Fee (Perm-Out) - %s') % (self.barcode or self.name),
            'quantity': 1,
            'price_unit': removal_product.list_price,
            'move_id': invoice.id,
        }
        
        self.env['account.move.line'].create(invoice_line_vals)
        
        # Log charge creation
        self.message_post(
            body=_("Removal charges created (Perm-Out):<br/>• Removal fee: %s") % removal_product.list_price,
            subject=_("Perm-Out Charges Created")
        )
        
        return invoice
    
    def _get_or_create_draft_invoice(self):
        """Get existing draft invoice or create new one for customer"""
        # Find existing draft invoice for this customer
        invoice = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft'),
        ], limit=1)
        
        if not invoice:
            # Create new draft invoice
            invoice = self.env['account.move'].create({
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
            })
        
        return invoice
    
    def _get_removal_fee_product(self):
        """Get or create product for removal fees"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-REMOVAL-FEE'),
        ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Container Removal Fee',
                'default_code': 'RM-REMOVAL-FEE',
                'type': 'service',
                'list_price': 15.00,  # Default price - configurable
                'invoice_policy': 'order',
                'description': 'Per-container removal fee for destruction or perm-out services',
            })
        
        return product
    
    def _get_shredding_fee_product(self):
        """Get or create product for shredding fees"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-SHREDDING-FEE'),
        ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Container Shredding Fee',
                'default_code': 'RM-SHREDDING-FEE',
                'type': 'service',
                'list_price': 25.00,  # Default price - configurable
                'invoice_policy': 'order',
                'description': 'Per-container shredding fee for destruction services',
            })
        
        return product
    
    def _check_and_close_destruction_work_order(self):
        """Check if all containers on destruction work order are destroyed, close if complete"""
        # Find associated destruction work order
        work_order = self.env['container.destruction.work.order'].search([
            ('container_ids', 'in', self.id),
            ('state', 'not in', ('completed', 'cancelled')),
        ], limit=1)
        
        if work_order:
            # Check if all containers are destroyed
            all_destroyed = all(c.state == 'destroyed' for c in work_order.container_ids)
            
            if all_destroyed:
                work_order.write({
                    'state': 'completed',
                    'actual_destruction_date': fields.Datetime.now(),
                })
                
                work_order.message_post(
                    body=_("All containers destroyed. Work order auto-completed."),
                    subject=_("Work Order Completed")
                )
    
    def _check_and_close_perm_out_work_order(self):
        """Check if all containers on perm-out work order are processed, close if complete"""
        # Find associated work order (could be retrieval or custom perm-out type)
        work_order = self.env['file.retrieval.work.order'].search([
            ('container_ids', 'in', self.id),
            ('state', 'not in', ('completed', 'cancelled')),
        ], limit=1)
        
        if work_order:
            # Check if all containers are perm_out
            all_perm_out = all(c.state == 'perm_out' for c in work_order.container_ids)
            
            if all_perm_out:
                work_order.write({
                    'state': 'completed',
                })
                
                work_order.message_post(
                    body=_("All containers permanently removed. Work order auto-completed."),
                    subject=_("Work Order Completed")
                )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("partner_id", "department_id")
    def _check_department_partner(self):
        """Ensure department belongs to the same partner"""
        for record in self:
            if record.department_id and record.department_id.partner_id != record.partner_id:
                raise ValidationError(_("Department must belong to the selected customer."))

    @api.constrains("weight")
    def _check_positive_values(self):
        for record in self:
            if record.weight and record.weight < 0:
                raise ValidationError(_("Weight must be a positive value."))

    @api.constrains("storage_start_date", "destruction_due_date")
    def _check_date_consistency(self):
        for record in self:
            if (
                record.storage_start_date
                and record.destruction_due_date
                and record.storage_start_date > record.destruction_due_date
            ):
                raise ValidationError(_("Destruction date cannot be before storage start date"))

    # =========================================================================
    # DEFAULT VIEW FALLBACK (Test Support)
    # =========================================================================
    def _get_default_tree_view(self):  # Odoo core still asks for 'tree' in some test helpers
        """Provide a minimal fallback list (tree) view structure for automated tests.

        Odoo 19 uses <list/> arch tag, but internal test utilities may still request
        a default 'tree' view for x2many placeholders when no explicit list view is
        preloaded. Returning a valid list arch prevents UserError during base tests.
        """
        from lxml import etree
        arch = etree.fromstring(
            "<list string='Records Containers'>"
            "<field name='display_name'/>"
            "<field name='state'/>"
            "<field name='partner_id'/>"
            "<field name='location_id'/>"
            "</list>"
        )
        return arch

    # =========================================================================
    # DYNAMIC FIELD LABELS
    # =========================================================================
    @api.model
    def fields_get(self, allfields=None, attributes=None):
        """Override to apply custom field labels based on user's partner configuration.
        
        This allows different customers to see their preferred terminology:
        - Healthcare: 'Chart Box', 'Medical Records', 'HIPAA Level'
        - Legal: 'Matter Box', 'Case Materials', 'Privilege Level'
        - Corporate: 'Box Number', 'Contents', 'Classification'
        """
        result = super().fields_get(allfields=allfields, attributes=attributes)
        
        # Get the current user's partner for label customization
        try:
            partner_id = self.env.user.partner_id.id if self.env.user.partner_id else None
            
            # Check if there's a commercial partner (company) that might have config
            if self.env.user.partner_id and self.env.user.partner_id.commercial_partner_id:
                partner_id = self.env.user.partner_id.commercial_partner_id.id
            
            label_config = self.env['field.label.customization'].sudo()
            custom_labels = label_config.get_labels_dict(partner_id)
            
            # Apply custom labels to field definitions
            for field_name, custom_label in custom_labels.items():
                if field_name in result and custom_label:
                    result[field_name]['string'] = custom_label
        except Exception:
            # Don't break the view if label customization fails
            pass
        
        return result
    
    # =========================================================================
    # LOCATION COUNT UPDATES
    # =========================================================================
    def _update_location_counts(self):
        """Location counts are handled via native quant_ids relationship - method kept for compatibility"""
        pass
