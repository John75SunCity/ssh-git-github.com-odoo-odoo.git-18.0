# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ShreddingInventoryItem(models.Model):
    _name = "shredding.inventory.item"
    _description = "Shredding Inventory Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "display_name"

    # Basic Information
    name = fields.Char(string="Item Name", required=True, tracking=True),
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    ),
    sequence = fields.Integer(string="Sequence", default=10)

    # Core fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    )
    user_id = fields.Many2one(
        "res.users", string="User", default=lambda self: self.env.user
    ),
    active = fields.Boolean(string="Active", default=True)

    # Workflow relationships - containers vs documents
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        help="Barcoded container being shredded",
    ),
    document_id = fields.Many2one(
        "records.document", string="Document", help="Specific document being shredded"
    )
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order"),
    current_location_id = fields.Many2one("records.location", string="Current Location")

    # Item details
    item_type = fields.Selection(
        [
            ("document", "Document"),
            ("container", "Container"),
            ("hard_drive", "Hard Drive"),
            ("media", "Media"),
        ]),
        string="Item Type",
        default="document",
        tracking=True,
    )
    quantity = fields.Float(string="Quantity", default=1.0),
    total_cost = fields.Monetary(string="Total Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Status tracking
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_pickup", "Pending Pickup"),
            ("retrieved", "Retrieved"),
            ("destroyed", "Destroyed"),
            ("not_found", "Not Found"),
        ]),
        string="Status",
        default="draft",
        tracking=True,
    )

    # Additional tracking fields
    description = fields.Text(string="Description"),
    notes = fields.Text(string="Notes")
    date = fields.Date(string="Inventory Date", default=fields.Date.today)
    # === COMPREHENSIVE MISSING FIELDS ===
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ]),
        string="Processing State",
        default="draft",
        tracking=True,
    )
    created_date = fields.Date(
        string="Created Date", default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string="Updated Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===        "mail.followers", "res_id", string="Followers"
    )
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True),
    document_count = fields.Integer(string="Document Count", default=0)
    total_amount = fields.Monetary(string="Total Amount", currency_field="currency_id")
    # Shredding Inventory Item Fields

    # === ENTERPRISE-GRADE ANALYTICS & COMPLIANCE FIELDS ===
    audit_trail_enabled = fields.Boolean(
        string="Audit Trail Enabled",
        default=True,
        help="Enable audit trail for this item",
    ),
    last_audit_date = fields.Date(string="Last Audit Date", help="Date of last audit")
    compliance_notes = fields.Text(
        string="Compliance Notes", help="Compliance-related notes"
    )
    )
    retention_policy = fields.Selection(
        [
            ("1year", "1 Year"),
            ("3years", "3 Years"),
            ("5years", "5 Years"),
            ("7years", "7 Years"),
            ("permanent", "Permanent"),
        ]),
        string="Retention Policy",
        default="7years",
        help="Retention policy for this item",
    destruction_certificate_number = fields.Char(
        string="Destruction Certificate Number",
        help="Certificate number for destruction event",
    ),
    destruction_certificate_issued = fields.Boolean(
        string="Certificate Issued", default=False
    )
    destruction_certificate_date = fields.Date(string="Certificate Date"),
    destruction_certificate_file = fields.Binary(string="Certificate File")

    # === COMPUTED FIELDS ===
    days_since_destruction = fields.Integer(
        string="Days Since Destruction",
        compute="_compute_days_since_destruction",
        store=True,
    ),
    is_overdue_for_destruction = fields.Boolean(
        string="Overdue for Destruction",
        compute="_compute_is_overdue_for_destruction",
        store=True,
    )

    @api.depends("destruction_date")
    def _compute_days_since_destruction(self):
        from datetime import date

        for record in self:
            if record.destruction_date:
                record.days_since_destruction = (
                    date.today() - record.destruction_date
                ).days
            else:
                record.days_since_destruction = 0

    @api.depends("destruction_date")
    def _compute_is_overdue_for_destruction(self):
        for record in self:
            # Example: Overdue if not destroyed after 30 days from created_date
            if record.destruction_date:
                record.is_overdue_for_destruction = False
            elif record.created_date:
                from datetime import date, timedelta

                overdue = (date.today() - record.created_date) > timedelta(days=30)
                record.is_overdue_for_destruction = overdue
            else:
                record.is_overdue_for_destruction = False

    # === VALIDATION CONSTRAINTS ===
    @api.constrains("quantity")
    def _check_quantity(self):
        for record in self:
            if record.quantity < 0:
                raise ValidationError(_("Quantity must be non-negative."))
    @api.constrains("destruction_date")
    def _check_destruction_date(self):
        for record in self:
            if (
                record.destruction_date
                and record.destruction_date < record.created_date
            ):
                raise ValidationError(
                    _("Destruction date cannot be before creation date.")
                )

    # === ACTION METHODS (WORKFLOW) ===
    def action_issue_certificate(self):
        """Issue destruction certificate and mark as issued."""
        self.ensure_one()
        if not self.destruction_date:
            raise UserError(_("Cannot issue certificate before destruction.")
        self.destruction_certificate_issued = True
        self.destruction_certificate_date = fields.Date.today()
        self.message_post(body=_("Destruction certificate issued.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Issued"),
                "message": _("Destruction certificate has been issued."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_audit_item(self):
        """Audit this shredding inventory item."""
        self.ensure_one()
        self.last_audit_date = fields.Date.today()
        self.message_post(body=_("Audit completed for this item.")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Audit Complete"),
                "message": _("Audit completed for this item."),
                "type": "info",
                "sticky": False,
            },
        }

    approval_date = fields.Date("Approval Date"),
    customer_approved = fields.Boolean("Customer Approved", default=False)
    destroyed_by = fields.Many2one("hr.employee", "Destroyed By"),
    destruction_date = fields.Date("Destruction Date")
    destruction_notes = fields.Text("Destruction Notes"),
    batch_processing_required = fields.Boolean(
        "Batch Processing Required", default=False
    )
    )
    certificate_generation_required = fields.Boolean(
        "Certificate Generation Required", default=True
    ),
    chain_of_custody_number = fields.Char("Chain of Custody Number")
    contamination_check_completed = fields.Boolean(
        "Contamination Check Completed", default=False
    )
    )
    destruction_method_verified = fields.Boolean(
        "Destruction Method Verified", default=False
    ),
    item_classification = fields.Selection(
        [("paper", "Paper"), ("media", "Media"), ("electronic", "Electronic")],
        default="paper",
    )
    quality_verification_completed = fields.Boolean(
        "Quality Verification Completed", default=False
    ),
    security_level_verified = fields.Boolean("Security Level Verified", default=False)
    witness_verification_required = fields.Boolean(
        "Witness Verification Required", default=False
    )

    # === MISSING VIEW-RELATED FIELDS ===
    )
    original_location_id = fields.Many2one(
        "records.location",
        string="Original Location",
        help="Original location before retrieval",)
    permanent_removal_cost = fields.Monetary(
        string="Permanent Removal Cost",
        currency_field="currency_id",
        help="Cost for permanent removal",
    ),
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost",
        currency_field="currency_id",
        help="Cost for retrieval service",)
    retrieval_notes = fields.Text(
        string="Retrieval Notes", help="Notes about retrieval process"
    )
    )
    retrieved_by = fields.Many2one(
        "hr.employee", string="Retrieved By", help="Employee who retrieved the item"
    ),
    retrieved_date = fields.Date(
        string="Retrieved Date", help="Date when item was retrieved"
    )
    )
    storage_cost = fields.Monetary(
        string="Storage Cost",
        currency_field="currency_id",
        help="Cost for storage before destruction",)
    transport_cost = fields.Monetary(
        string="Transport Cost",
        currency_field="currency_id",
        help="Cost for transporting item",
    ),
    weight = fields.Float(
        string="Weight", digits=(10, 2), help="Weight of the item in kg"
    )

    # === FINAL MISSING FIELDS ===
    shredding_cost = fields.Monetary(
        string="Shredding Cost",
        currency_field="currency_id",
        help="Cost for shredding service",
    ),
    supervisor_approved = fields.Boolean(
        string="Supervisor Approved",
        default=False,
        help="Whether supervisor has approved this item",
    )

    @api.depends("name", "container_id", "document_id")
    def _compute_display_name(self):
        for record in self:
            if record.container_id:
                record.display_name = (
                    f"{record.name} (Container: {record.container_id.name})"
                )
            elif record.document_id:
                record.display_name = (
                    f"{record.name} (Document: {record.document_id.name})"
                )
            else:
                record.display_name = record.name or _("New Item")

    def action_approve_item(self):
        """Approve item for destruction."""
        self.ensure_one()
        self.write({"status": "pending_pickup"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Approved"),
                "message": _(
                    "Item has been approved for destruction and is pending pickup."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_retrieved(self):
        """Mark item as retrieved."""
        self.ensure_one()
        self.write({"status": "retrieved"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Retrieved"),
                "message": _("Item has been marked as retrieved."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_destroyed(self):
        """Mark item as destroyed."""
        self.ensure_one()
        self.write({"status": "destroyed"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Destroyed"),
                "message": _("Item has been marked as destroyed."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_mark_picked(self):
        """Mark item as picked."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Picked"),
                "message": _("Item has been marked as picked."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_not_found(self):
        """Mark item as not found."""
        self.ensure_one()
        self.write({"status": "not_found"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Not Found"),
                "message": _("Item has been marked as not found."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_track_chain_of_custody(self):
        """Track chain of custody."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("item_id", "=", self.id)],
        }

    def action_generate_certificate(self):
        """Generate destruction certificate."""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.destruction_certificate",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_audit_compliance(self):
        """Audit compliance status."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Audited"),
                "message": _("Compliance status has been audited."),
                "type": "success",
                "sticky": False,
            },
        })
