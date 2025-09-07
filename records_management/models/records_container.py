from dateutil.relativedelta import relativedelta  # type: ignore
import base64
from io import BytesIO

from odoo import models, fields, api, _  # pyright: ignore[reportMissingModuleSource, reportAttributeAccessIssue]
from odoo.exceptions import ValidationError, UserError

# Replace direct qrcode import with guarded import (removes unused type: ignore)
try:
    import qrcode  # noqa: F401
except Exception:  # pragma: no cover - optional dependency fallback
    qrcode = None


class RecordsContainer(models.Model):
    _name = "records.container"
    _description = "Records Container Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Container Name", required=True, copy=False, readonly=True, default=lambda self: _("New"))
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, readonly=True
    )
    currency_id = fields.Many2one(related="company_id.currency_id", readonly=True, comodel_name="res.currency")
    user_id = fields.Many2one("res.users", string="Responsible", default=lambda self: self.env.user, tracking=True)
    barcode = fields.Char(string="Barcode", copy=False, index=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer", required=True, tracking=True)
    department_id = fields.Many2one("records.department", string="Department", tracking=True)
    location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        domain="[('active', '=', True), ('state', '=', 'active')]",
    )
    container_type_id = fields.Many2one("records.container.type", string="Container Type", required=True)
    retention_policy_id = fields.Many2one("records.retention.policy", string="Retention Policy")
    temp_inventory_id = fields.Many2one("temp.inventory", string="Temporary Inventory")
    document_type_id = fields.Many2one("records.document.type", string="Document Type")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active/Indexed"),
            ("stored", "In Storage"),
            ("in_transit", "In Transit"),
            ("retrieved", "Retrieved"),
            ("pending_destruction", "Pending Destruction"),
            ("destroyed", "Destroyed"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
    )

    # ============================================================================
    # PHYSICAL & CONTENT DETAILS
    # ============================================================================
    # Contextual label disambiguation (Batch 2): Clarify generic 'Description'
    description = fields.Text(string="Container Description")
    # Batch 3 label disambiguation
    content_description = fields.Text(string="Box Contents")
    dimensions = fields.Char(string="Dimensions", related="container_type_id.dimensions", readonly=True)
    weight = fields.Float(string="Weight (lbs)")
    cubic_feet = fields.Float(string="Cubic Feet", related="container_type_id.cubic_feet", readonly=True)
    is_full = fields.Boolean(string="Container Full", default=False)
    document_ids = fields.One2many("records.document", "container_id", string="Documents")
    document_count = fields.Integer(compute="_compute_document_count", string="Document Count", store=True)

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
    _sql_constraints = [
        ("barcode_company_uniq", "unique(barcode, company_id)", "The barcode must be unique per company."),
    ]

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("records.container") or _("New")
        return super().create(vals_list)

    def write(self, vals):
        if any(key in vals for key in ["location_id", "state"]) and "last_access_date" not in vals:
            vals["last_access_date"] = fields.Date.today()
        return super().write(vals)

    def unlink(self):
        for record in self:
            if record.state not in ("draft", "destroyed"):
                raise UserError(_("You can only delete containers that are in 'Draft' or 'Destroyed' state."))
            if record.document_ids:
                raise UserError(_("Cannot delete a container that has documents linked to it."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & SEARCH METHODS
    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        for container in self:
            container.document_count = len(container.document_ids)

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
                and container.state != "destroyed"
            )

    def _search_due_for_destruction(self, operator, value):
        today = fields.Date.today()
        domain = [
            ("destruction_due_date", "<=", today),
            ("permanent_retention", "=", False),
            ("state", "!=", "destroyed"),
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

    # ============================================================================
    # BUTTON ACTIONS
    # ============================================================================
    def action_activate(self):
        """Activate container for storage"""
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Customer must be specified before activation"))

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
        return {
            "name": _("Documents in Container %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("container_id", "=", self.id)],
            "context": {"default_container_id": self.id},
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
        self.message_post(body=_("Container has been stored."))

    def action_retrieve_container(self):
        """Retrieve container from storage"""
        self.ensure_one()
        if self.state not in ["stored", "active"]:
            raise UserError(_("Only stored or active containers can be retrieved"))
        self.write({"state": "in_transit", "last_access_date": fields.Date.today()})
        self.message_post(body=_("Container retrieved from storage"))

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
        """Generate QR code for the container and return download action."""
        self.ensure_one()
        if qrcode is None:
            raise UserError(_("QR code library not installed. Please install python package 'qrcode'."))
        # Generate QR code data (e.g., container ID or barcode)
        qr_data = f"Container ID: {self.id}\nBarcode: {self.barcode or 'N/A'}"

        # Create QR code image
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill="black", back_color="white")

        # Convert to base64 for download
        buffer = BytesIO()
        img.save(buffer, "PNG")  # Changed: Use positional argument for format to avoid keyword error
        img_str = base64.b64encode(buffer.getvalue()).decode()

        # Return action to download the QR code
        return {
            "type": "ir.actions.act_url",
            "url": f"data:image/png;base64,{img_str}",
            "target": "new",
            "name": f"QR Code - {self.name}",
        }

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
