# -*- coding: utf-8 -*-
"""
Shredding Inventory Item Management Module

This module provides comprehensive inventory item management for the shredding and destruction
workflow within the Records Management System. It handles individual items that need to be
shredded or destroyed, with complete tracking from identification to destruction certificate
generation.

Key Features:
- Individual item tracking with barcode and serial number support
- Multi-type item support (documents, containers, hard drives, media)
- Complete workflow management from draft to destruction
- NAID compliance with chain of custody tracking
- Automated certificate generation and audit trails
- Cost tracking and billing integration
- Quality assurance and verification workflows

Business Processes:
1. Item Registration: Initial item setup with classification and details
2. Approval Workflow: Customer and supervisor approval processes
3. Retrieval Management: Item pickup and transport tracking
4. Destruction Processing: Secure destruction with method verification
5. Certificate Generation: Automated destruction certificate creation
6. Audit and Compliance: Complete audit trails and compliance verification

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta


class ShreddingInventoryItem(models.Model):
    _name = "shredding.inventory.item"
    _description = "Shredding Inventory Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for this inventory item",
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Computed display name with context",
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Order sequence for sorting"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this item",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # ITEM CLASSIFICATION
    # ============================================================================
    item_type = fields.Selection(
        [
            ("document", "Document"),
            ("container", "Container"),
            ("hard_drive", "Hard Drive"),
            ("media", "Media"),
            ("electronic", "Electronic Device"),
            ("paper", "Paper Records"),
        ],
        string="Item Type",
        default="document",
        required=True,
        tracking=True,
        help="Classification of the item being processed",
    )
    item_classification = fields.Selection(
        [
            ("paper", "Paper"),
            ("media", "Media"),
            ("electronic", "Electronic"),
            ("confidential", "Confidential"),
            ("public", "Public"),
        ],
        string="Classification",
        default="paper",
        tracking=True,
        help="Security classification of the item",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    container_id = fields.Many2one(
        "records.container",
        string="Container",
        tracking=True,
        help="Barcoded container being shredded",
    )
    document_id = fields.Many2one(
        "records.document",
        string="Document",
        tracking=True,
        help="Specific document being shredded",
    )
    work_order_id = fields.Many2one(
        "work.order.shredding",
        string="Work Order",
        tracking=True,
        help="Associated work order",
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer who owns this item",
    )

    # ============================================================================
    # LOCATION TRACKING
    # ============================================================================
    current_location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        help="Current physical location of the item",
    )
    original_location_id = fields.Many2one(
        "records.location",
        string="Original Location",
        tracking=True,
        help="Original location before retrieval",
    )

    # ============================================================================
    # WORKFLOW STATUS FIELDS
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Processing State",
        default="draft",
        tracking=True,
        help="Current processing state",
    )
    status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending_pickup", "Pending Pickup"),
            ("retrieved", "Retrieved"),
            ("destroyed", "Destroyed"),
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current workflow status",
    )

    # ============================================================================
    # QUANTITY AND MEASUREMENTS
    # ============================================================================
    quantity = fields.Float(
        string="Quantity", default=1.0, digits=(10, 2), help="Quantity of items"
    )
    weight = fields.Float(
        string="Weight (kg)", digits=(10, 2), help="Weight of the item in kilograms"
    )
    document_count = fields.Integer(
        string="Document Count", default=0, help="Number of documents in this item"
    )

    # ============================================================================
    # FINANCIAL FIELDS
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        help="Total cost for processing this item",
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        help="Total billable amount",
    )
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost",
        currency_field="currency_id",
        help="Cost for retrieval service",
    )
    storage_cost = fields.Monetary(
        string="Storage Cost",
        currency_field="currency_id",
        help="Cost for storage before destruction",
    )
    transport_cost = fields.Monetary(
        string="Transport Cost",
        currency_field="currency_id",
        help="Cost for transporting item",
    )
    shredding_cost = fields.Monetary(
        string="Shredding Cost",
        currency_field="currency_id",
        help="Cost for shredding service",
    )
    permanent_removal_cost = fields.Monetary(
        string="Permanent Removal Cost",
        currency_field="currency_id",
        help="Cost for permanent removal",
    )

    # ============================================================================
    # DATE FIELDS
    # ============================================================================
    date = fields.Date(
        string="Inventory Date", default=fields.Date.today, required=True, tracking=True
    )
    created_date = fields.Date(
        string="Created Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when record was created",
    )
    updated_date = fields.Date(
        string="Updated Date", tracking=True, help="Date when record was last updated"
    )
    retrieved_date = fields.Date(
        string="Retrieved Date", tracking=True, help="Date when item was retrieved"
    )
    destruction_date = fields.Date(
        string="Destruction Date", tracking=True, help="Date when item was destroyed"
    )
    approval_date = fields.Date(
        string="Approval Date", tracking=True, help="Date when item was approved"
    )

    # ============================================================================
    # APPROVAL FIELDS
    # ============================================================================
    customer_approved = fields.Boolean(
        string="Customer Approved",
        default=False,
        tracking=True,
        help="Whether customer has approved this item",
    )
    supervisor_approved = fields.Boolean(
        string="Supervisor Approved",
        default=False,
        tracking=True,
        help="Whether supervisor has approved this item",
    )

    # ============================================================================
    # PERSONNEL FIELDS
    # ============================================================================
    retrieved_by = fields.Many2one(
        "hr.employee",
        string="Retrieved By",
        tracking=True,
        help="Employee who retrieved the item",
    )
    destroyed_by = fields.Many2one(
        "hr.employee",
        string="Destroyed By",
        tracking=True,
        help="Employee who performed the destruction",
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT FIELDS
    # ============================================================================
    audit_trail_enabled = fields.Boolean(
        string="Audit Trail Enabled",
        default=True,
        help="Enable audit trail for this item",
    )
    last_audit_date = fields.Date(
        string="Last Audit Date", tracking=True, help="Date of last audit"
    )
    chain_of_custody_number = fields.Char(
        string="Chain of Custody Number",
        tracking=True,
        help="Unique chain of custody identifier",
    )

    # ============================================================================
    # DESTRUCTION CERTIFICATE FIELDS
    # ============================================================================
    destruction_certificate_number = fields.Char(
        string="Destruction Certificate Number",
        tracking=True,
        help="Certificate number for destruction event",
    )
    destruction_certificate_issued = fields.Boolean(
        string="Certificate Issued",
        default=False,
        tracking=True,
        help="Whether destruction certificate has been issued",
    )
    destruction_certificate_date = fields.Date(
        string="Certificate Date",
        tracking=True,
        help="Date when certificate was issued",
    )
    destruction_certificate_file = fields.Binary(
        string="Certificate File", help="PDF file of the destruction certificate"
    )

    # ============================================================================
    # VERIFICATION FIELDS
    # ============================================================================
    contamination_check_completed = fields.Boolean(
        string="Contamination Check Completed",
        default=False,
        tracking=True,
        help="Whether contamination check has been completed",
    )
    destruction_method_verified = fields.Boolean(
        string="Destruction Method Verified",
        default=False,
        tracking=True,
        help="Whether destruction method has been verified",
    )
    quality_verification_completed = fields.Boolean(
        string="Quality Verification Completed",
        default=False,
        tracking=True,
        help="Whether quality verification has been completed",
    )
    security_level_verified = fields.Boolean(
        string="Security Level Verified",
        default=False,
        tracking=True,
        help="Whether security level has been verified",
    )
    witness_verification_required = fields.Boolean(
        string="Witness Verification Required",
        default=False,
        help="Whether witness verification is required",
    )

    # ============================================================================
    # PROCESSING FIELDS
    # ============================================================================
    batch_processing_required = fields.Boolean(
        string="Batch Processing Required",
        default=False,
        help="Whether this item requires batch processing",
    )
    certificate_generation_required = fields.Boolean(
        string="Certificate Generation Required",
        default=True,
        help="Whether certificate generation is required",
    )

    # ============================================================================
    # RETENTION POLICY
    # ============================================================================
    retention_policy = fields.Selection(
        [
            ("1year", "1 Year"),
            ("3years", "3 Years"),
            ("5years", "5 Years"),
            ("7years", "7 Years"),
            ("permanent", "Permanent"),
        ],
        string="Retention Policy",
        default="7years",
        tracking=True,
        help="Retention policy for this item",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    days_since_destruction = fields.Integer(
        string="Days Since Destruction",
        compute="_compute_days_since_destruction",
        store=True,
        help="Number of days since destruction",
    )
    is_overdue_for_destruction = fields.Boolean(
        string="Overdue for Destruction",
        compute="_compute_is_overdue_for_destruction",
        store=True,
        help="Whether item is overdue for destruction",
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of the item"
    )
    notes = fields.Text(string="Notes", help="Additional notes and comments")
    retrieval_notes = fields.Text(
        string="Retrieval Notes", help="Notes about retrieval process"
    )
    destruction_notes = fields.Text(
        string="Destruction Notes", help="Notes about destruction process"
    )
    compliance_notes = fields.Text(
        string="Compliance Notes", help="Compliance-related notes"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "container_id", "document_id")
    def _compute_display_name(self):
        """Compute display name with context information"""
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

    @api.depends("destruction_date")
    def _compute_days_since_destruction(self):
        """Calculate days since destruction"""
        today = fields.Date.today()
        for record in self:
            if record.destruction_date:
                record.days_since_destruction = (today - record.destruction_date).days
            else:
                record.days_since_destruction = 0

    @api.depends("destruction_date", "created_date")
    def _compute_is_overdue_for_destruction(self):
        """Check if item is overdue for destruction"""
        today = fields.Date.today()
        for record in self:
            if record.destruction_date:
                record.is_overdue_for_destruction = False
            elif record.created_date:
                overdue_threshold = timedelta(days=30)
                overdue = (today - record.created_date) > overdue_threshold
                record.is_overdue_for_destruction = overdue
            else:
                record.is_overdue_for_destruction = False

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    def write(self, vals):
        """Override write to update timestamp"""
        if vals:
            vals["updated_date"] = fields.Date.today()
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_approve_item(self):
        """Approve item for destruction"""
        self.ensure_one()
        self.write(
            {
                "status": "pending_pickup",
                "approval_date": fields.Date.today(),
                "customer_approved": True,
            }
        )

        self.message_post(body=_("Item approved for destruction"))

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
        """Mark item as retrieved"""
        self.ensure_one()
        self.write(
            {
                "status": "retrieved",
                "retrieved_date": fields.Date.today(),
                "state": "in_progress",
            }
        )

        self.message_post(body=_("Item marked as retrieved"))

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
        """Mark item as destroyed"""
        self.ensure_one()
        self.write(
            {
                "status": "destroyed",
                "destruction_date": fields.Date.today(),
                "state": "completed",
            }
        )

        self.message_post(body=_("Item marked as destroyed"))

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

    def action_mark_not_found(self):
        """Mark item as not found"""
        self.ensure_one()
        self.write({"status": "not_found"})

        self.message_post(body=_("Item marked as not found"))

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

    def action_issue_certificate(self):
        """Issue destruction certificate"""
        self.ensure_one()
        if not self.destruction_date:
            raise UserError(_("Cannot issue certificate before destruction."))

        if not self.destruction_certificate_number:
            # Generate certificate number
            sequence = self.env["ir.sequence"].next_by_code("destruction.certificate")
            if not sequence:
                today = fields.Date.today().strftime("%Y%m%d")
                count = (
                    self.search_count([("destruction_certificate_number", "!=", False)])
                    + 1
                )
                sequence = f"CERT-{today}-{count:04d}"
            self.destruction_certificate_number = sequence

        self.write(
            {
                "destruction_certificate_issued": True,
                "destruction_certificate_date": fields.Date.today(),
            }
        )

        self.message_post(
            body=_("Destruction certificate issued: %s")
            % self.destruction_certificate_number
        )

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
        """Audit this shredding inventory item"""
        self.ensure_one()
        self.write({"last_audit_date": fields.Date.today()})

        self.message_post(body=_("Audit completed for this item"))

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

    def action_track_chain_of_custody(self):
        """Track chain of custody"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("item_id", "=", self.id)],
            "context": {"default_item_id": self.id},
        }

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.destruction_certificate",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_audit_compliance(self):
        """Audit compliance status"""
        self.ensure_one()

        self.write({"last_audit_date": fields.Date.today()})
        self.message_post(body=_("Compliance audit completed"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Audited"),
                "message": _("Compliance status has been audited."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_supervisor_approve(self):
        """Supervisor approval action"""
        self.ensure_one()

        self.write(
            {
                "supervisor_approved": True,
                "approval_date": fields.Date.today(),
            }
        )

        self.message_post(body=_("Item approved by supervisor"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Supervisor Approval"),
                "message": _("Item has been approved by supervisor."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_verify_destruction_method(self):
        """Verify destruction method"""
        self.ensure_one()

        self.write({"destruction_method_verified": True})
        self.message_post(body=_("Destruction method verified"))

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Method Verified"),
                "message": _("Destruction method has been verified."),
                "type": "success",
                "sticky": False,
            },
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("quantity", "weight")
    def _check_positive_values(self):
        """Validate quantity and weight are non-negative"""
        for record in self:
            if record.quantity < 0:
                raise ValidationError(_("Quantity must be non-negative."))
            if record.weight < 0:
                raise ValidationError(_("Weight must be non-negative."))

    @api.constrains("destruction_date", "created_date")
    def _check_destruction_date(self):
        """Validate destruction date is not before creation date"""
        for record in self:
            if (
                record.destruction_date
                and record.created_date
                and record.destruction_date < record.created_date
            ):
                raise ValidationError(
                    _("Destruction date cannot be before creation date.")
                )

    @api.constrains("retrieved_date", "created_date")
    def _check_retrieved_date(self):
        """Validate retrieved date is not before creation date"""
        for record in self:
            if (
                record.retrieved_date
                and record.created_date
                and record.retrieved_date < record.created_date
            ):
                raise ValidationError(
                    _("Retrieved date cannot be before creation date.")
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_destruction_summary(self):
        """Get destruction summary for reporting"""
        self.ensure_one()

        return {
            "item_name": self.name,
            "item_type": self.item_type,
            "customer": self.customer_id.name if self.customer_id else "",
            "destruction_date": self.destruction_date,
            "certificate_number": self.destruction_certificate_number,
            "total_cost": self.total_cost,
            "status": self.status,
            "state": self.state,
            "certificate_issued": self.destruction_certificate_issued,
            "weight": self.weight,
            "quantity": self.quantity,
        }

    @api.model
    def get_pending_destruction_items(self):
        """Get items pending destruction"""
        return self.search(
            [
                ("status", "in", ["pending_pickup", "retrieved"]),
                ("destruction_date", "=", False),
            ]
        )

    @api.model
    def get_overdue_items(self):
        """Get overdue items for destruction"""
        return self.search([("is_overdue_for_destruction", "=", True)])

    def create_chain_of_custody_entry(self, event_type, notes=""):
        """Create chain of custody entry"""
        self.ensure_one()

        if "custody.log" in self.env:
            self.env["custody.log"].create(
                {
                    "item_id": self.id,
                    "event_type": event_type,
                    "event_date": fields.Datetime.now(),
                    "user_id": self.env.user.id,
                    "notes": notes,
                }
            )
