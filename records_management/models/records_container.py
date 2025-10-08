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
    # Temporary barcode assigned at portal/customer creation time before a physical barcode is applied by technicians.
    # Remains immutable once a physical barcode is assigned. Searchable and billable reference.
    temp_barcode = fields.Char(
        string="Temporary Barcode",
        copy=False,
        index=True,
        tracking=True,
        help="System-generated temporary tracking barcode assigned when the customer creates the container in the portal.")
    barcode_assigned = fields.Boolean(
        string="Physical Barcode Assigned",
        compute="_compute_barcode_assigned",
        store=True,
        help="Indicates a physical warehouse barcode has been assigned (barcode field set).")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        default=lambda self: self.env.user.partner_id.id,
        help="Defaults to the current user's partner to ensure minimal record creation works in tests and quick operations.",
    )
    department_id = fields.Many2one("records.department", string="Department", tracking=True)
    location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        domain="[('active', '=', True), ('state', '=', 'active')]",
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
    content_date_from = fields.Date(
        string="Content Date From",
        help="Earliest relevant content date contained in this container.",
    )
    content_date_to = fields.Date(
        string="Content Date To",
        help="Latest relevant content date contained in this container.",
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
    barcode_company_uniq = models.Constraint("unique(barcode, company_id)", _("The barcode must be unique per company."))
    temp_barcode_company_uniq = models.Constraint("unique(temp_barcode, company_id)", _("The temporary barcode must be unique per company."))

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
            # Assign a sequence if name is left to default "New"
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code("records.container") or _("New")
            # Ensure a safe default container type to satisfy NOT NULL constraints in tests/runtime
            if not vals.get("container_type_id"):
                default_type_id = self._get_default_container_type_id()
                if default_type_id:
                    vals["container_type_id"] = default_type_id
            # Assign a temp barcode if not provided and no physical barcode yet
            if not vals.get("temp_barcode") and not vals.get("barcode"):
                # Set context flag so helper can optionally audit log
                temp_code = self.with_context(creating_temp_barcode_log=True)._generate_temp_barcode(vals)
                vals["temp_barcode"] = temp_code
            # Billing starts at portal creation → if storage_start_date is empty set today
            if not vals.get("storage_start_date"):
                vals["storage_start_date"] = fields.Date.today()
        return super().create(vals_list)

    def write(self, vals):
        if any(key in vals for key in ["location_id", "state"]) and "last_access_date" not in vals:
            vals["last_access_date"] = fields.Date.today()
        # Prevent changing temp_barcode after physical barcode assigned unless superuser context flag
        if "temp_barcode" in vals and any(rec.barcode for rec in self) and not self.env.context.get("allow_temp_barcode_edit"):
            vals.pop("temp_barcode")
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

    @api.depends("alpha_range_start", "alpha_range_end")
    def _compute_alpha_range_display(self):
        for rec in self:
            start = (rec.alpha_range_start or "").strip()
            end = (rec.alpha_range_end or "").strip()
            if start and end:
                if start.upper() == end.upper():
                    rec.alpha_range_display = start.upper()
                else:
                    rec.alpha_range_display = "%s - %s" % (start.upper(), end.upper())
            elif start:
                rec.alpha_range_display = start.upper()
            elif end:
                rec.alpha_range_display = end.upper()
            else:
                rec.alpha_range_display = False

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

    def action_assign_physical_barcode(self, barcode_value):
        """Assign a physical (warehouse) barcode, preserving the temporary barcode.

        Contract:
        - Fails if a physical barcode already exists unless context 'force_reassign' set.
        - Validates uniqueness via SQL constraint.
        - Posts chatter message with both refs.
        - Leaves temp_barcode unchanged and immutable after assignment.
        """
        self.ensure_one()
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
    def name_search(self, name='', args=None, operator='ilike', limit=100):  # type: ignore[override]
        args = list(args or [])
        if name:
            # Expand search to include temp_barcode and barcode
            domain = ['|', '|', ('name', operator, name), ('barcode', operator, name), ('temp_barcode', operator, name)]
            records = self.search(domain + args, limit=limit)
            return records.name_get()
        return super().name_search(name=name, args=args, operator=operator, limit=limit)

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
