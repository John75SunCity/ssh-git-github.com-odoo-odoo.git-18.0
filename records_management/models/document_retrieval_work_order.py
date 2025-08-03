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
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
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
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
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
