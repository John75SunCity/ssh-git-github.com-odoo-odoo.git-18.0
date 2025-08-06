# -*- coding: utf-8 -*-
"""
Records Document Management Module

This module provides comprehensive document lifecycle management for the Records Management System.
It implements complete document tracking from creation through destruction with full NAID AAA
compliance and enterprise-grade security features.

Key Features:
- Complete document lifecycle management (draft → active → archived → destroyed)
- Advanced retention policy automation with computed destruction dates
- Permanent flag system for legal holds and litigation support
- Multi-media support (paper, digital, microfilm, mixed media)
- Security classification with granular access controls (public to top secret)
- Location and container tracking with full audit trails
- Parent-child document relationships for version control
- Integration with destruction and retrieval workflow systems

Business Processes:
1. Document Registration: Create documents with metadata and classification
2. Storage Management: Assign containers and locations with tracking
3. Retention Compliance: Apply retention policies with automated scheduling
4. Security Classification: Implement security controls and access restrictions
5. Legal Hold Management: Apply permanent flags for legal and compliance requirements
6. Destruction Processing: Schedule and execute NAID-compliant destruction
7. Retrieval Services: Process document access requests with audit logging
8. Version Control: Manage document relationships and version tracking

Retention & Compliance:
- Automated retention period calculation based on document date and policy
- Permanent flag system preventing inadvertent destruction
- NAID AAA compliant audit trails with encrypted signatures
- Chain of custody tracking for legal and regulatory compliance
- Integration with destruction certificate generation systems

Security Features:
- Multi-level security classification (Public, Internal, Confidential, Restricted, Top Secret)
- Customer-specific data isolation with secure domain filtering
- Audit logging for all document access and modification events
- Integration with enterprise authentication and authorization systems

Technical Implementation:
- Modern Odoo 18.0 patterns with comprehensive mail.thread integration
- Computed fields with proper @api.depends decorators for performance
- Comprehensive validation with business rule enforcement
- Secure relationship management preventing data leakage
- Enterprise-grade error handling and user notifications

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class RecordsDocument(models.Model):
    _name = "records.document"
    _description = "Records Document Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "document_number desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Document Name", required=True, tracking=True, index=True)
    document_number = fields.Char(
        string="Document Number", index=True, tracking=True, copy=False
    )
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Document Manager",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("archived", "Archived"),
            ("destroyed", "Destroyed"),
            ("pending_destruction", "Pending Destruction"),
        ],
        string="Document Status",
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT CLASSIFICATION & METADATA
    # ============================================================================
    document_type_id = fields.Many2one(
        "records.document.type",
        string="Document Type",
        required=True,
        tracking=True,
        index=True,
    )

    category = fields.Selection(
        [
            ("financial", "Financial"),
            ("legal", "Legal"),
            ("medical", "Medical"),
            ("personal", "Personal"),
            ("business", "Business"),
            ("government", "Government"),
            ("hr", "Human Resources"),
            ("technical", "Technical"),
        ],
        string="Document Category",
        tracking=True,
    )

    classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Classification",
        default="internal",
        tracking=True,
    )

    media_type = fields.Selection(
        [
            ("paper", "Paper"),
            ("digital", "Digital"),
            ("microfilm", "Microfilm"),
            ("mixed", "Mixed Media"),
        ],
        string="Media Type",
        default="paper",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT PROPERTIES
    # ============================================================================
    file_format = fields.Char(
        string="File Format", help="Document file format (PDF, DOC, XLS, etc.)"
    )
    file_size_mb = fields.Float(string="File Size (MB)", tracking=True, digits=(10, 2))
    page_count = fields.Integer(string="Page Count", help="Number of pages in document")
    weight_kg = fields.Float(
        string="Weight (kg)", digits=(8, 3), help="Physical weight of document"
    )
    dimensions = fields.Char(
        string="Dimensions", help="Physical dimensions (L x W x H)"
    )

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    document_date = fields.Date(
        string="Document Date",
        required=True,
        tracking=True,
        help="Date the document was created/issued",
    )
    received_date = fields.Date(
        string="Received Date", default=fields.Date.context_today, tracking=True
    )
    scan_date = fields.Date(string="Scan Date")

    # Retention Management
    retention_period = fields.Integer(
        string="Retention Period (Years)",
        default=7,
        help="Number of years to retain this document",
    )
    retention_end_date = fields.Date(
        string="Retention End Date",
        compute="_compute_retention_end_date",
        store=True,
        help="Date when document can be destroyed",
    )
    days_until_destruction = fields.Integer(
        string="Days Until Destruction",
        compute="_compute_days_until_destruction",
        help="Number of days until scheduled destruction",
    )

    # Permanent Flag System
    permanent_flag = fields.Boolean(
        string="Permanent Flag",
        default=False,
        tracking=True,
        help="Flag to prevent destruction (legal hold, etc.)",
    )
    permanent_flag_reason = fields.Char(
        string="Permanent Flag Reason", help="Reason for permanent retention"
    )
    permanent_flag_date = fields.Datetime(
        string="Permanent Flag Date", help="When permanent flag was applied"
    )
    permanent_flag_user_id = fields.Many2one(
        "res.users", string="Flagged By", help="User who applied permanent flag"
    )

    # ============================================================================
    # LOCATION & STORAGE
    # ============================================================================
    location_id = fields.Many2one(
        "records.location", string="Storage Location", tracking=True, index=True
    )
    box_id = fields.Many2one(
        "records.box", string="Storage Box", tracking=True, index=True
    )
    shelf_position = fields.Char(
        string="Shelf Position", help="Specific position within storage location"
    )

    # Digital Storage
    file_path = fields.Char(string="File Path", help="Path to digital file")
    checksum = fields.Char(string="File Checksum", help="Digital integrity checksum")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Related Customer",
        index=True,
        help="Customer this document relates to",
    )

    tag_ids = fields.Many2many(
        "records.tag", "document_tag_rel", "document_id", "tag_id", string="Tags"
    )

    # Related Documents
    parent_document_id = fields.Many2one(
        "records.document",
        string="Parent Document",
        help="Parent document if this is a child/version",
    )
    child_document_ids = fields.One2many(
        "records.document", "parent_document_id", string="Child Documents"
    )

    # Workflow Relationships
    destruction_request_ids = fields.One2many(
        "records.destruction.request", "document_id", string="Destruction Requests"
    )
    retrieval_request_ids = fields.One2many(
        "records.retrieval.request", "document_id", string="Retrieval Requests"
    )

    # Retention Policy (NEW RELATIONSHIP)
    retention_policy_id = fields.Many2one(
        "records.retention.policy",
        string="Retention Policy",
        help="Applied retention policy for this document",
    )

    # Mail Framework Fields (SECURE)
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        auto_join=True,
        groups="base.group_user",
    )
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers", groups="base.group_user"
    )
    message_ids = fields.One2many(
        "mail.message", "res_id", string="Messages", groups="base.group_user"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("document_date", "retention_period")
    def _compute_retention_end_date(self):
        """Compute when document retention period ends"""
        for record in self:
            if record.document_date and record.retention_period:
                record.retention_end_date = record.document_date + relativedelta(
                    years=record.retention_period
                )
            else:
                record.retention_end_date = False

    @api.depends("retention_end_date", "permanent_flag")
    def _compute_days_until_destruction(self):
        """Compute days remaining until scheduled destruction"""
        for record in self:
            if record.permanent_flag:
                record.days_until_destruction = -1  # Permanent
            elif record.retention_end_date:
                today = fields.Date.today()
                end_date = record.retention_end_date
                if hasattr(end_date, "date"):
                    end_date = end_date.date()
                delta = end_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = 0

    @api.depends("name", "document_number")
    def _compute_display_name(self):
        """Compute display name"""
        for record in self:
            if record.document_number:
                record.display_name = f"[{record.document_number}] {record.name}"
            else:
                record.display_name = record.name

    @api.depends("child_document_ids")
    def _compute_child_count(self):
        """Compute number of child documents"""
        for record in self:
            record.child_count = len(record.child_document_ids)

    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    child_count = fields.Integer(
        string="Child Documents", compute="_compute_child_count"
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("document_date", "received_date")
    def _check_dates(self):
        for record in self:
            if record.document_date and record.received_date:
                if record.document_date > record.received_date:
                    raise ValidationError(
                        _("Document date cannot be after received date")
                    )

    @api.constrains("retention_period")
    def _check_retention_period(self):
        for record in self:
            if record.retention_period < 0:
                raise ValidationError(_("Retention period cannot be negative"))
            if record.retention_period > 100:
                raise ValidationError(_("Retention period cannot exceed 100 years"))

    @api.constrains("file_size_mb")
    def _check_file_size(self):
        for record in self:
            if record.file_size_mb and record.file_size_mb < 0:
                raise ValidationError(_("File size cannot be negative"))

    @api.constrains("page_count")
    def _check_page_count(self):
        for record in self:
            if record.page_count and record.page_count < 0:
                raise ValidationError(_("Page count cannot be negative"))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _check_destruction_eligibility(self):
        """Check if document is eligible for destruction"""
        self.ensure_one()

        if self.permanent_flag:
            return False, _("Document has permanent flag")

        if not self.retention_end_date:
            return False, _("No retention end date set")

        if self.retention_end_date > fields.Date.today():
            return False, _("Retention period not yet expired")

        if self.state == "destroyed":
            return False, _("Document already destroyed")

        return True, _("Document eligible for destruction")

    def _update_checksum(self):
        """Update file checksum for digital documents.

        This method must be implemented for production use to ensure file integrity.
        """
        raise NotImplementedError(
            "Checksum calculation must be implemented for production use."
        )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate document"""
        for record in self:
            if record.state != "draft":
                raise UserError(_("Only draft documents can be activated"))
            record.write({"state": "active"})
            record.message_post(body=_("Document activated"))

    def action_archive(self):
        """Archive document"""
        for record in self:
            if record.state == "destroyed":
                raise UserError(_("Cannot archive destroyed documents"))
            record.write({"state": "archived"})
            record.message_post(body=_("Document archived"))

    def action_flag_permanent(self):
        """Apply permanent flag to prevent destruction"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Apply Permanent Flag"),
            "res_model": "records.permanent.flag.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_document_ids": [(6, 0, self.ids)],
                "default_operation_type": "apply",
            },
        }

    def action_remove_permanent_flag(self):
        """Remove permanent flag"""
        for record in self:
            if not record.permanent_flag:
                raise UserError(_("Document does not have permanent flag"))
            record.write(
                {
                    "permanent_flag": False,
                    "permanent_flag_reason": False,
                    "permanent_flag_date": False,
                    "permanent_flag_user_id": False,
                }
            )
            record.message_post(body=_("Permanent flag removed"))

    def action_request_destruction(self):
        """Request document destruction"""
        for record in self:
            eligible, message = record._check_destruction_eligibility()
            if not eligible:
                raise UserError(message)

        return {
            "type": "ir.actions.act_window",
            "name": _("Request Destruction"),
            "res_model": "records.destruction.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_ids": [(6, 0, self.ids)]},
        }

    def action_request_retrieval(self):
        """Request document retrieval"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Request Retrieval"),
            "res_model": "records.retrieval.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_ids": [(6, 0, self.ids)]},
        }

    def action_move_location(self):
        """Move document to new location"""
        return {
            "type": "ir.actions.act_window",
            "name": _("Move Document"),
            "res_model": "records.move.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_ids": [(6, 0, self.ids)]},
        }

    def action_view_child_documents(self):
        """View child documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Child Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("parent_document_id", "=", self.id)],
            "context": {"default_parent_document_id": self.id},
        }

    def action_generate_barcode(self):
        """Generate barcode for document"""
        self.ensure_one()
        if not self.document_number:
            raise UserError(
                _("Document must have a document number to generate barcode")
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Generate Barcode"),
            "res_model": "records.barcode.generator.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_document_id": self.id},
        }

    def action_audit_trail(self):
        """View complete audit trail"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Document Audit Trail"),
            "res_model": "naid.audit.log",
            "view_mode": "tree,form",
            "domain": [
                ("resource_type", "=", "records.document"),
                ("resource_id", "=", self.id),
            ],
        }

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model
    def create(self, vals):
        """Override create to set document number"""
        if not vals.get("document_number"):
            vals["document_number"] = (
                self.env["ir.sequence"].next_by_code("records.document") or "/"
            )
        return super().create(vals)

    def write(self, vals):
        """Override write to track important changes"""
        # Track location changes
        if "location_id" in vals:
            for record in self:
                old_location = record.location_id.name if record.location_id else "None"
                location_val = vals["location_id"]
                if isinstance(location_val, int):
                    new_location = (
                        self.env["records.location"].browse(location_val).name
                    )
                elif (
                    isinstance(location_val, (list, tuple))
                    and location_val
                    and isinstance(location_val[0], int)
                ):
                    new_location = (
                        self.env["records.location"].browse(location_val[0]).name
                    )
                else:
                    new_location = "None"
                record.message_post(
                    body=_("Location changed from %s to %s")
                    % (old_location, new_location)
                )
        # Track state changes
        if "state" in vals:
            for record in self:
                state_selection = dict(record._fields["state"].selection)
                old_state = state_selection.get(record.state, record.state)
                new_state = state_selection.get(vals["state"], vals["state"])
                record.message_post(
                    body=_("Status changed from %s to %s") % (old_state, new_state)
                )

        return super().write(vals)
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of active documents"""
        if any(record.state == "active" for record in self):
            raise UserError(
                _("Cannot delete active documents. Please archive them first.")
            )
        return super().unlink()
