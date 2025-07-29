# -*- coding: utf-8 -*-
"""
Transitory Items Management - Pre-Pickup Customer Inventory
Handles customer-declared inventory before physical pickup and barcoding
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TransitoryItems(models.Model):
    """
    Transitory Items - Customer-declared inventory awaiting pickup

    Tracks managed records containers, files, and items that customers add to their account
    before we physically pick them up and assign barcodes. These items should be
    charged the same as regular inventory and count toward storage capacity planning.
    """

    _name = "transitory.items"
    _description = "Transitory Items - Pre-Pickup Customer Inventory"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "creation_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(
        string="Item Description",
        required=True,
        tracking=True,
        help="Customer description of the item/container/file",
    )
    reference = fields.Char(
        string="Customer Reference",
        tracking=True,
        help="Customer's internal reference number",
    )

    # Customer container numbering system
    container_number = fields.Char(
        string="Container Number",
        tracking=True,
        help="Customer's internal container reference (e.g., 0010, HR0010)",
    )
    container_set_suffix = fields.Char(
        string="Set Suffix",
        tracking=True,
        help="Auto-generated suffix for duplicate container numbers (A, B, C)",
    )
    full_container_reference = fields.Char(
        string="Full Container Reference",
        compute="_compute_full_container_reference",
        store=True,
        help="Complete container reference including suffix",
    )

    # Barcode for transitory tracking
    transitory_barcode = fields.Char(
        string="Transitory Barcode",
        copy=False,
        readonly=True,
        help="Temporary barcode until converted to records container",
    )

    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    customer_contact_id = fields.Many2one(
        "res.partner",
        string="Customer Contact",
        domain="[('parent_id', '=', customer_id)]",
    )
    department_id = fields.Many2one(
        "records.department", string="Department", tracking=True
    )

    # ==========================================
    # ITEM DETAILS
    # ==========================================
    item_type = fields.Selection(
        [
            ("records_container", "Records Container"),
            ("file_folder", "File/Folder"),
            ("document_set", "Document Set"),
            ("media", "Media (Tapes/Disks)"),
            ("equipment", "Equipment/Hardware"),
            ("other", "Other Item"),
        ],
        string="Item Type",
        required=True,
        tracking=True,
        default="records_container",
    )

    # Hierarchical structure for file folders
    parent_container_id = fields.Many2one(
        "transitory.items",
        string="Parent Container",
        domain="[('item_type', '=', 'records_container'), ('customer_id', '=', customer_id)]",
        tracking=True,
        help="Which container this file/folder belongs to",
    )
    child_folder_ids = fields.One2many(
        "transitory.items",
        "parent_container_id",
        string="Files/Folders in this Container",
        domain="[('item_type', '!=', 'records_container')]",
    )
    folder_level = fields.Integer(
        string="Folder Level",
        compute="_compute_folder_level",
        store=True,
        help="Depth level: 0=Container, 1=Folder in Container, 2=Subfolder, etc.",
    )

    # Display helpers for hierarchy
    parent_container_reference = fields.Char(
        related="parent_container_id.name", string="Container Reference", readonly=True
    )
    hierarchy_display = fields.Char(
        string="Hierarchy Path",
        compute="_compute_hierarchy_display",
        help="Full path: Container > Folder > Subfolder",
    )

    quantity = fields.Integer(
        string="Quantity",
        default=1,
        required=True,
        tracking=True,
        help="Number of items (containers, files, etc.)",
    )
    estimated_weight = fields.Float(
        string="Estimated Weight (lbs)",
        tracking=True,
        help="Customer's estimate - will be verified at pickup",
    )
    content_description = fields.Text(
        string="Content Description",
        tracking=True,
        help="Description of what's inside the item",
    )

    # Size estimates for storage planning
    estimated_cubic_feet = fields.Float(
        string="Estimated Size (cubic feet)",
        tracking=True,
        help="For storage capacity planning",
    )

    # ==========================================
    # BUSINESS RECORD FIELDS (Configurable)
    # ==========================================
    # Date ranges
    date_from = fields.Date(
        string="Records From Date",
        tracking=True,
        help="Start date of records in this container",
    )
    date_to = fields.Date(
        string="Records To Date",
        tracking=True,
        help="End date of records in this container",
    )

    # Sequence ranges for document numbering
    sequence_from = fields.Char(
        string="Sequence From",
        tracking=True,
        help="Starting sequence number (e.g., 001, A001)",
    )
    sequence_to = fields.Char(
        string="Sequence To",
        tracking=True,
        help="Ending sequence number (e.g., 250, Z999)",
    )

    # Destruction information
    scheduled_destruction_date = fields.Date(
        string="Scheduled Destruction Date",
        tracking=True,
        help="When these records should be destroyed",
    )
    destruction_required = fields.Boolean(
        string="Destruction Required",
        tracking=True,
        help="Records require certified destruction",
    )
    retention_period_years = fields.Integer(
        string="Retention Period (Years)",
        tracking=True,
        help="Legal retention requirement in years",
    )

    # Business categorization
    record_type = fields.Selection(
        [
            ("financial", "Financial Records"),
            ("hr", "Human Resources"),
            ("legal", "Legal Documents"),
            ("medical", "Medical Records"),
            ("tax", "Tax Documents"),
            ("contracts", "Contracts"),
            ("correspondence", "Correspondence"),
            ("invoices", "Invoices/Billing"),
            ("other", "Other"),
        ],
        string="Record Type",
        tracking=True,
        help="Category of records",
    )

    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Use"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Confidentiality Level",
        default="internal",
        tracking=True,
    )

    # Additional business fields
    project_code = fields.Char(
        string="Project Code", tracking=True, help="Project or job reference code"
    )
    client_reference = fields.Char(
        string="Client Reference",
        tracking=True,
        help="Reference to specific client or matter",
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        tracking=True,
        help="Special compliance or legal requirements",
    )

    # File/folder organization
    total_file_count = fields.Integer(
        string="Number of Files",
        tracking=True,
        help="Approximate number of individual files",
    )
    filing_system = fields.Char(
        string="Filing System",
        tracking=True,
        help="How files are organized (alphabetical, chronological, etc.)",
    )

    # Additional metadata
    created_by_department = fields.Char(
        string="Created by Department",
        tracking=True,
        help="Which department created these records",
    )
    authorized_by = fields.Char(
        string="Authorized By", tracking=True, help="Name of person authorizing storage"
    )
    special_handling = fields.Text(
        string="Special Handling Instructions",
        tracking=True,
        help="Any special requirements or instructions",
    )

    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection(
        [
            ("declared", "Customer Declared"),
            ("scheduled", "Pickup Scheduled"),
            ("collected", "Collected/Converted"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="declared",
        tracking=True,
        required=True,
    )

    # ==========================================
    # PICKUP AND CONVERSION TRACKING
    # ==========================================
    creation_date = fields.Datetime(
        string="Declaration Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
    )
    scheduled_pickup_date = fields.Date(string="Scheduled Pickup Date", tracking=True)
    actual_pickup_date = fields.Date(string="Actual Pickup Date", tracking=True)

    pickup_request_id = fields.Many2one(
        "pickup.request", string="Related Pickup Request", tracking=True
    )

    # Conversion to real inventory
    converted_to_container_id = fields.Many2one(
        "records.container",
        string="Converted to Records Container",
        tracking=True,
        readonly=True,
    )
    converted_date = fields.Datetime(
        string="Conversion Date", tracking=True, readonly=True
    )
    converted_by_id = fields.Many2one(
        "res.users", string="Converted By", tracking=True, readonly=True
    )

    # ==========================================
    # BILLING FIELDS
    # ==========================================
    billable = fields.Boolean(
        string="Billable",
        default=True,
        tracking=True,
        help="Should be charged same as regular inventory",
    )
    monthly_storage_rate = fields.Float(
        string="Monthly Storage Rate",
        tracking=True,
        help="Monthly storage charge per item",
    )
    total_storage_value = fields.Float(
        string="Total Storage Value",
        compute="_compute_storage_values",
        store=True,
        help="Total value for capacity planning",
    )

    # Billing relationship
    billing_account_id = fields.Many2one(
        "advanced.billing",
        string="Billing Account",
        related="customer_id.billing_account_id",
        store=True,
    )

    # ==========================================
    # ADMIN AND IMPORT FIELDS
    # ==========================================
    created_by_admin = fields.Boolean(
        string="Created by Admin",
        default=False,
        help="Item was created by records management staff",
    )
    import_batch_id = fields.Char(
        string="Import Batch ID", help="Batch ID for bulk imported items"
    )
    import_source = fields.Selection(
        [
            ("manual", "Manual Entry"),
            ("csv_import", "CSV Import"),
            ("excel_import", "Excel Import"),
            ("api_import", "API Import"),
            ("admin_created", "Admin Created"),
        ],
        string="Import Source",
        default="manual",
        tracking=True,
    )

    # Admin notes and overrides
    admin_notes = fields.Text(
        string="Admin Notes",
        tracking=True,
        help="Internal notes from records management staff",
    )
    admin_override_billing = fields.Boolean(
        string="Admin Override Billing",
        help="Admin has overridden default billing settings",
    )
    admin_priority = fields.Boolean(
        string="Admin Priority", tracking=True, help="Marked as priority by admin"
    )

    # Field visibility controls (for customer portal)
    field_config_id = fields.Many2one(
        "transitory.field.config",
        related="customer_id.transitory_field_config_id",
        string="Field Configuration",
        help="Controls which fields are visible/required for this customer",
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    days_in_system = fields.Integer(
        string="Days in System",
        compute="_compute_days_in_system",
        help="Days since customer declared this item",
    )
    is_overdue_pickup = fields.Boolean(
        string="Pickup Overdue",
        compute="_compute_pickup_status",
        help="Scheduled pickup date has passed",
    )
    storage_impact = fields.Float(
        string="Storage Impact",
        compute="_compute_storage_values",
        store=True,
        help="Storage space impact for capacity planning",
    )

    @api.depends("container_number", "container_set_suffix")
    def _compute_full_container_reference(self):
        """Compute full container reference including set suffix"""
        for record in self:
            if record.container_number:
                if record.container_set_suffix:
                    record.full_container_reference = (
                        f"{record.container_number}-{record.container_set_suffix}"
                    )
                else:
                    record.full_container_reference = record.container_number
            else:
                record.full_container_reference = False

    @api.depends("parent_container_id")
    def _compute_folder_level(self):
        """Compute hierarchy level (0=Container, 1=Folder, 2=Subfolder, etc.)"""
        for record in self:
            if record.item_type == "records_container":
                record.folder_level = 0
            elif record.parent_container_id:
                record.folder_level = record.parent_container_id.folder_level + 1
            else:
                record.folder_level = 0

    @api.depends("parent_container_id", "name", "item_type")
    def _compute_hierarchy_display(self):
        """Compute full hierarchy path for display"""
        for record in self:
            if record.item_type == "records_container":
                record.hierarchy_display = record.full_container_reference or record.name
            elif record.parent_container_id:
                parent_path = (
                    record.parent_container_id.hierarchy_display
                    or record.parent_container_id.name
                )
                record.hierarchy_display = f"{parent_path} > {record.name}"
            else:
                record.hierarchy_display = record.name

    @api.depends("creation_date")
    def _compute_days_in_system(self):
        """Calculate days since item was declared"""
        today = fields.Date.today()
        for record in self:
            if record.creation_date:
                creation_date = record.creation_date.date()
                record.days_in_system = (today - creation_date).days
            else:
                record.days_in_system = 0

    @api.depends("scheduled_pickup_date", "state")
    def _compute_pickup_status(self):
        """Check if pickup is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue_pickup = (
                record.state in ("declared", "scheduled")
                and record.scheduled_pickup_date
                and record.scheduled_pickup_date < today
            )

    @api.depends("quantity", "estimated_cubic_feet", "monthly_storage_rate")
    def _compute_storage_values(self):
        """Calculate storage impact and billing values"""
        for record in self:
            # Storage impact for capacity planning
            record.storage_impact = record.quantity * (
                record.estimated_cubic_feet or 1.0
            )

            # Total storage value for billing
            record.total_storage_value = record.quantity * record.monthly_storage_rate

    # ==========================================
    # BULK IMPORT AND ADMIN METHODS
    # ==========================================
    @api.model
    def bulk_create_from_list(
        self, items_data, customer_id, created_by_admin=False, parent_container_id=None
    ):
        """Bulk create transitory items from list data

        Args:
            items_data: List of dictionaries with item data
            customer_id: Customer ID
            created_by_admin: Whether created by admin
            parent_container_id: Parent container ID for file folders

        Returns:
            List of created record IDs and barcodes
        """
        import uuid

        batch_id = str(uuid.uuid4())[:8]  # Short unique batch ID
        created_items = []

        for item_data in items_data:
            vals = {
                "customer_id": customer_id,
                "created_by_admin": created_by_admin,
                "import_batch_id": batch_id,
                "import_source": "admin_created" if created_by_admin else "csv_import",
            }

            # If creating folders in a container, set parent
            if parent_container_id and item_data.get("item_type") != "records_container":
                vals["parent_container_id"] = parent_container_id
                vals["item_type"] = "file_folder"  # Default for items in containers

            # Map common fields
            field_mapping = {
                "name": "name",
                "description": "content_description",
                "container_number": "container_number",
                "item_type": "item_type",
                "quantity": "quantity",
                "estimated_weight": "estimated_weight",
                "date_from": "date_from",
                "date_to": "date_to",
                "sequence_from": "sequence_from",
                "sequence_to": "sequence_to",
                "record_type": "record_type",
                "confidentiality_level": "confidentiality_level",
                "project_code": "project_code",
                "client_reference": "client_reference",
                "filing_system": "filing_system",
                "total_file_count": "total_file_count",
            }

            for api_field, model_field in field_mapping.items():
                if api_field in item_data:
                    vals[model_field] = item_data[api_field]

            # Create the item
            try:
                new_item = self.create(vals)
                created_items.append(
                    {
                        "id": new_item.id,
                        "barcode": new_item.transitory_barcode,
                        "name": new_item.name,
                        "full_reference": new_item.full_container_reference,
                        "hierarchy_display": new_item.hierarchy_display,
                        "success": True,
                    }
                )
            except Exception as e:
                created_items.append(
                    {
                        "name": item_data.get("name", "Unknown"),
                        "error": str(e),
                        "success": False,
                    }
                )

        return {
            "batch_id": batch_id,
            "created_items": created_items,
            "success_count": len([i for i in created_items if i.get("success")]),
            "error_count": len([i for i in created_items if not i.get("success")]),
        }

    @api.model
    def create_folders_for_container(self, container_id, folder_list):
        """Create multiple file folders for a specific container

        Args:
            container_id: ID of the parent container
            folder_list: List of folder data

        Returns:
            Created folder records
        """
        container = self.browse(container_id)
        if not container.exists() or container.item_type != "records_container":
            raise UserError(_("Invalid container specified"))

        folder_data = []
        for folder_info in folder_list:
            folder_data.append(
                {
                    "name": folder_info.get("name"),
                    "content_description": folder_info.get("description", ""),
                    "item_type": "file_folder",
                    "sequence_from": folder_info.get("sequence_from"),
                    "sequence_to": folder_info.get("sequence_to"),
                    "date_from": folder_info.get("date_from"),
                    "date_to": folder_info.get("date_to"),
                    "total_file_count": folder_info.get("file_count", 0),
                    "record_type": folder_info.get("record_type"),
                    "confidentiality_level": folder_info.get(
                        "confidentiality_level", "internal"
                    ),
                }
            )

        return self.bulk_create_from_list(
            folder_data,
            container.customer_id.id,
            created_by_admin=self.env.user.has_group(
                "records_management.group_records_manager"
            ),
            parent_container_id=container_id,
        )

    @api.model
    def admin_create_for_customer(self, customer_id, item_data, department_id=None):
        """Admin method to create items for any customer

        Args:
            customer_id: Target customer ID
            item_data: Item data dictionary
            department_id: Optional department ID

        Returns:
            Created item record
        """
        # Only allow records management staff
        if not self.env.user.has_group("records_management.group_records_manager"):
            raise UserError(
                _("Only records management staff can create items for customers")
            )

        vals = item_data.copy()
        vals.update(
            {
                "customer_id": customer_id,
                "created_by_admin": True,
                "import_source": "admin_created",
                "user_id": self.env.user.id,
            }
        )

        if department_id:
            vals["department_id"] = department_id

        return self.create(vals)

    @api.model
    def get_customer_containers_for_folders(self, customer_id, department_id=None):
        """Get available containers for adding folders

        Args:
            customer_id: Customer ID
            department_id: Optional department filter

        Returns:
            List of available containers
        """
        domain = [
            ("customer_id", "=", customer_id),
            ("item_type", "=", "records_container"),
            ("state", "in", ("declared", "scheduled")),
        ]

        if department_id:
            domain.append(("department_id", "=", department_id))

        containers = self.search(domain)

        result = []
        for container in containers:
            folder_count = len(container.child_folder_ids)
            result.append(
                {
                    "id": container.id,
                    "name": container.name,
                    "container_number": container.container_number,
                    "full_reference": container.full_container_reference,
                    "folder_count": folder_count,
                    "barcode": container.transitory_barcode,
                    "description": container.content_description,
                    "state": container.state,
                    "creation_date": (
                        container.creation_date.strftime("%Y-%m-%d %H:%M")
                        if container.creation_date
                        else ""
                    ),
                }
            )

        return sorted(result, key=lambda x: x["creation_date"], reverse=True)

    @api.model
    def process_csv_import(self, csv_data, customer_id, created_by_admin=False):
        """Process CSV import for bulk creation

        Args:
            csv_data: CSV string data
            customer_id: Customer ID
            created_by_admin: Whether import is done by admin

        Returns:
            Import results
        """
        import csv
        import io

        # Parse CSV
        csv_file = io.StringIO(csv_data)
        reader = csv.DictReader(csv_file)

        items_data = []
        for row in reader:
            # Clean and validate data
            item = {}
            for key, value in row.items():
                if value and value.strip():
                    # Convert field names to match model
                    clean_key = key.lower().replace(" ", "_").replace("-", "_")
                    item[clean_key] = value.strip()

            if item.get("name"):  # Must have a name
                items_data.append(item)

        if not items_data:
            raise UserError(_("No valid data found in CSV"))

        return self.bulk_create_from_list(items_data, customer_id, created_by_admin)

    def action_admin_edit_settings(self):
        """Open admin view for editing customer settings"""
        if not self.env.user.has_group("records_management.group_records_manager"):
            raise UserError(
                _("Only records management staff can edit customer settings")
            )

        return {
            "type": "ir.actions.act_window",
            "name": "Admin: Edit Customer Settings",
            "view_mode": "form",
            "res_model": "res.partner",
            "res_id": self.customer_id.id,
            "target": "new",
            "context": {"admin_edit_mode": True},
        }

    @api.model
    def get_container_number_suggestions(
        self, customer_id, department_id=None, search_term=""
    ):
        """Get container number suggestions for autocomplete"""
        domain = [("customer_id", "=", customer_id)]
        if department_id:
            domain.append(("department_id", "=", department_id))

        # Search both transitory items and actual containers
        transitory_containers = self.search(domain)
        actual_containers = self.env["records.container"].search(domain)

        suggestions = []

        # Get existing container numbers
        for item in transitory_containers:
            if item.container_number and (
                not search_term or search_term.lower() in item.container_number.lower()
            ):
                suggestions.append(
                    {
                        "container_number": item.container_number,
                        "full_reference": item.full_container_reference,
                        "description": item.name,
                        "source": "transitory",
                    }
                )

        for container in actual_containers:
            if (
                hasattr(container, "customer_container_number")
                and container.customer_container_number
            ):
                if (
                    not search_term
                    or search_term.lower() in container.customer_container_number.lower()
                ):
                    suggestions.append(
                        {
                            "container_number": container.customer_container_number,
                            "full_reference": container.customer_container_number,
                            "description": container.description or container.name,
                            "source": "records_container",
                        }
                    )

        # Remove duplicates and sort
        unique_suggestions = []
        seen_numbers = set()
        for suggestion in suggestions:
            if suggestion["container_number"] not in seen_numbers:
                unique_suggestions.append(suggestion)
                seen_numbers.add(suggestion["container_number"])

        return sorted(unique_suggestions, key=lambda x: x["container_number"])

    @api.model
    def check_container_number_exists(self, customer_id, container_number, department_id=None):
        """Check if container number already exists and suggest alternatives"""
        domain = [("customer_id", "=", customer_id), ("container_number", "=", container_number)]
        if department_id:
            domain.append(("department_id", "=", department_id))

        existing_transitory = self.search(domain)
        existing_containers = self.env["records.container"].search([
            ("customer_id", "=", customer_id),
            ("customer_container_number", "=", container_number)
        ])

        result = {
            "exists": bool(existing_transitory or existing_containers),
            "existing_items": [],
            "suggested_alternatives": [],
        }

        if existing_transitory:
            for item in existing_transitory:
                result["existing_items"].append(
                    {
                        "type": "transitory",
                        "name": item.name,
                        "full_reference": item.full_container_reference,
                        "state": item.state,
                    }
                )

        if existing_containers:
            for container in existing_containers:
                result["existing_items"].append(
                    {
                        "type": "records_container",
                        "name": container.name,
                        "full_reference": getattr(
                            container, "customer_container_number", container.name
                        ),
                        "state": getattr(container, "state", "active"),
                    }
                )

        if result["exists"]:
            # Generate suffix suggestions
            existing_suffixes = []
            for item in existing_transitory:
                if item.container_set_suffix:
                    existing_suffixes.append(item.container_set_suffix)

            # Generate next suffix (A, B, C, etc.)
            alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
            for letter in alphabet:
                if letter not in existing_suffixes:
                    result["suggested_alternatives"].append(
                        {
                            "full_reference": f"{container_number}-{letter}",
                            "suffix": letter,
                            "type": "set_suffix",
                        }
                    )
                    break

            # Also suggest next numeric sequence
            numeric_suggestions = self._get_next_numeric_suggestions(
                customer_id, container_number, department_id
            )
            result["suggested_alternatives"].extend(numeric_suggestions)

        return result

    def _get_next_numeric_suggestions(
        self, customer_id, base_number, department_id=None
    ):
        """Generate next numeric sequence suggestions"""
        import re

        # Extract numeric part and prefix
        match = re.match(r"([A-Za-z]*)(\d+)", base_number)
        if not match:
            return []

        prefix = match.group(1)
        number = int(match.group(2))
        number_length = len(match.group(2))

        suggestions = []
        for i in range(1, 6):  # Suggest next 5 numbers
            next_number = number + i
            padded_number = str(next_number).zfill(number_length)
            next_container_number = f"{prefix}{padded_number}"

            # Check if this number exists
            domain = [
                ("customer_id", "=", customer_id),
                ("container_number", "=", next_container_number),
            ]
            if department_id:
                domain.append(("department_id", "=", department_id))

            if not self.search(domain) and not self.env["records.container"].search(
                [('customer_container_number', '=', next_container_number)]
            ):
                suggestions.append(
                    {
                        "full_reference": next_container_number,
                        "suffix": None,
                        "type": "next_number",
                    }
                )
                break  # Only suggest the first available number

        return suggestions

    def _generate_transitory_barcode(self, prefix="TI"):
        """Generate unique barcode for transitory item

        Args:
            prefix: Barcode prefix (TC=Container, TF=Folder, TI=Item)
        """
        sequence = self.env["ir.sequence"].next_by_code("transitory.items.barcode")
        if not sequence:
            # Fallback if sequence doesn't exist
            import time

            sequence = f"{int(time.time())}"[-6:]  # Last 6 digits of timestamp
        return f"{prefix}-{sequence}"

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_schedule_pickup(self):
        """Schedule pickup for transitory items"""
        for record in self:
            if record.state != "declared":
                raise UserError(_("Only declared items can be scheduled for pickup"))

            if not record.scheduled_pickup_date:
                raise UserError(_("Please set a pickup date before scheduling"))

            record.write({"state": "scheduled"})
            record.message_post(
                body=_("Pickup scheduled for %s") % record.scheduled_pickup_date,
                message_type="notification",
            )

    def action_convert_to_records_container(self):
        """Convert transitory item to actual records container after pickup"""
        self.ensure_one()

        if self.state != "scheduled":
            raise UserError(_("Only scheduled items can be converted"))

        if self.converted_to_container_id:
            raise UserError(_("This item has already been converted"))

        # Create actual records container
        container_vals = {
            "name": f"Container from {self.name}",
            "customer_id": self.customer_id.id,
            "department_id": self.department_id.id,
            "description": self.content_description,
            "estimated_weight": self.estimated_weight,
            "state": "received",
            "source_transitory_id": self.id,
        }

        # Add location if we have a default intake location
        default_location = self.env["records.location"].search(
            [("location_type", "=", "intake")], limit=1
        )
        if default_location:
            container_vals["location_id"] = default_location.id

        new_container = self.env["records.container"].create(container_vals)

        self.write(
            {
                "state": "collected",
                "converted_to_container_id": new_container.id,
                "converted_date": fields.Datetime.now(),
                "converted_by_id": self.env.user.id,
                "actual_pickup_date": fields.Date.today(),
            }
        )

        self.message_post(
            body=_("Converted to Records Container: %s") % new_container.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": "Created Records Container",
            "view_mode": "form",
            "res_model": "records.container",
            "res_id": new_container.id,
        }

    def action_cancel_item(self):
        """Cancel transitory item"""
        for record in self:
            if record.state == "collected":
                raise UserError(
                    _("Cannot cancel items that have already been collected")
                )

            record.write({"state": "cancelled"})
            record.message_post(
                body=_("Item cancelled by %s") % self.env.user.name,
                message_type="notification",
            )

    def action_create_pickup_request(self):
        """Create pickup request for these items"""
        self.ensure_one()

        pickup_vals = {
            "customer_id": self.customer_id.id,
            "requested_date": self.scheduled_pickup_date or fields.Date.today(),
            "description": f"Pickup for transitory items: {self.name}",
            "special_instructions": f"Collect item: {self.content_description}",
            "state": "draft",
        }

        pickup_request = self.env["pickup.request"].create(pickup_vals)

        # Link this item to the pickup request
        self.write({"pickup_request_id": pickup_request.id})

        return {
            "type": "ir.actions.act_window",
            "name": "Pickup Request",
            "view_mode": "form",
            "res_model": "pickup.request",
            "res_id": pickup_request.id,
            "target": "current",
        }

    # ==========================================
    # BILLING INTEGRATION METHODS
    # ==========================================
    def create_monthly_storage_charges(self):
        """Create monthly storage charges for transitory items
        Called by scheduled action to bill for storage space reservation"""

        items_to_bill = self.search(
            [
                ("state", "in", ("declared", "scheduled")),
                ("billable", "=", True),
                ("monthly_storage_rate", ">", 0),
            ]
        )

        for item in items_to_bill:
            if item.billing_account_id:
                # Create billing line for storage
                billing_line_vals = {
                    "billing_id": item.billing_account_id.id,
                    "product_id": self.env.ref(
                        "records_management.product_storage_transitory"
                    ).id,
                    "quantity": item.quantity,
                    "unit_price": item.monthly_storage_rate,
                    "description": f"Transitory storage for {item.name}",
                    "date": fields.Date.today(),
                    "source_model": "transitory.items",
                    "source_id": item.id,
                }

                self.env["advanced.billing.line"].create(billing_line_vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default storage rates and generate barcodes"""
        for vals in vals_list:
            # Generate transitory barcode
            if not vals.get("transitory_barcode"):
                # Different barcode prefixes for different types
                item_type = vals.get("item_type", "records_container")
                if item_type == "records_container":
                    prefix = "TC"  # Transitory Container
                elif item_type == "file_folder":
                    prefix = "TF"  # Transitory Folder
                else:
                    prefix = "TI"  # Transitory Item

                vals["transitory_barcode"] = self._generate_transitory_barcode(prefix)

            # Handle container number and suffix logic (only for containers)
            if (
                vals.get("container_number")
                and vals.get("customer_id")
                and vals.get("item_type") == "records_container"
            ):
                existing_check = self.check_container_number_exists(
                    vals["customer_id"], vals["container_number"], vals.get("department_id")
                )

                # If container number exists and no suffix provided, auto-generate suffix
                if existing_check["exists"] and not vals.get("container_set_suffix"):
                    if existing_check["suggested_alternatives"]:
                        first_suggestion = existing_check["suggested_alternatives"][0]
                        if first_suggestion["type"] == "set_suffix":
                            vals["container_set_suffix"] = first_suggestion["suffix"]

            # Set default storage rate based on item type
            if not vals.get("monthly_storage_rate") and vals.get("item_type"):
                item_type = vals["item_type"]
                if item_type == "records_container":
                    vals["monthly_storage_rate"] = 1.50  # Same as regular container storage
                elif item_type in ("file_folder", "document_set"):
                    vals["monthly_storage_rate"] = 0.75
                elif item_type == "media":
                    vals["monthly_storage_rate"] = 2.00
                else:
                    vals["monthly_storage_rate"] = 1.00

            # Handle admin creation
            if vals.get("created_by_admin"):
                vals["admin_notes"] = f"Created by admin: {self.env.user.name}"

            # Validate parent container relationship
            if (
                vals.get("parent_container_id")
                and vals.get("item_type") == "records_container"
            ):
                raise UserError(
                    _("Records containers cannot be inside other containers")
                )

            # Ensure file folders have a parent container (unless created by admin)
            if (
                vals.get("item_type") == "file_folder"
                and not vals.get("parent_container_id")
                and not vals.get("created_by_admin")
            ):
                raise UserError(_("File folders must be assigned to a container"))

        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains("quantity")
    def _check_quantity(self):
        """Validate quantity is positive"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than zero"))

    @api.constrains("scheduled_pickup_date")
    def _check_pickup_date(self):
        """Validate pickup date is not in the past"""
        for record in self:
            if (
                record.scheduled_pickup_date
                and record.scheduled_pickup_date < fields.Date.today()
            ):
                if record.state == "declared":  # Only check for new items
                    raise ValidationError(_("Pickup date cannot be in the past"))

    @api.constrains("estimated_weight", "estimated_cubic_feet")
    def _check_estimates(self):
        """Validate estimates are reasonable"""
        for record in self:
            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_("Estimated weight cannot be negative"))
            if record.estimated_cubic_feet and record.estimated_cubic_feet < 0:
                raise ValidationError(_("Estimated size cannot be negative"))

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})

    # ==========================================
    # FIELD LABEL CUSTOMIZATION METHODS
    # ==========================================
    def get_portal_field_config(self):
        """Get field configuration for portal display including custom labels"""
        if self.customer_id:
            config = self.customer_id.get_transitory_field_config()
            # Add custom labels
            labels = self.env["field.label.customization"].get_labels_for_context(
                customer_id=self.customer_id.id,
                department_id=None,  # Can be enhanced for department-specific labels
            )
            config["field_labels"] = labels
            return config
        return {"visible_fields": {}, "required_fields": {}, "field_labels": {}}

    @api.model
    def get_field_label(self, field_name, customer_id=None, department_id=None):
        """Get custom label for a specific field"""
        return self.env["field.label.customization"].get_label_for_field(
            field_name, customer_id, department_id
        )

    def get_customer_field_labels(self):
        """Get all custom field labels for this item's customer"""
        self.ensure_one()
        if self.customer_id:
            return self.env["field.label.customization"].get_labels_for_context(
                customer_id=self.customer_id.id
            )
        return {}
