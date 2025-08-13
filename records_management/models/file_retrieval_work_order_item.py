# -*- coding: utf-8 -*-
"""
File Retrieval Work Order Item Module

Individual file items to be retrieved within a work order.
Handles detailed tracking of specific files through the retrieval process.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class FileRetrievalWorkOrderItem(models.Model):
    """Individual file items to be retrieved within a work order"""

    _name = "file.retrieval.work.order.item"
    _description = "File Retrieval Work Order Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "work_order_id, sequence, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Reference",
        required=True,
        tracking=True,
        index=True,
        help="Reference number or identifier for this specific file",
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name combining reference and description",
    )
    description = fields.Text(
        string="File Description",
        required=True,
        help="Detailed description of the file to be retrieved",
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for processing items",
    )
    company_id = fields.Many2one(
        "res.company",
        related="work_order_id.company_id",
        store=True,
        string="Company",
    )
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # WORK ORDER RELATIONSHIP
    # ============================================================================
    work_order_id = fields.Many2one(
        "file.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
        index=True,
    )
    partner_id = fields.Many2one(
        "res.partner",
        related="work_order_id.partner_id",
        store=True,
        string="Customer",
    )

    # ============================================================================
    # FILE DETAILS AND SPECIFICATIONS
    # ============================================================================
    file_name = fields.Char(
        string="File Name", help="Specific name or title of the file"
    )
    estimated_pages = fields.Integer(
        string="Estimated Pages",
        default=1,
        help="Estimated number of pages in this file",
    )
    actual_pages = fields.Integer(
        string="Actual Pages",
        help="Actual number of pages found during retrieval",
    )
    file_type = fields.Selection(
        [
            ("document", "Document"),
            ("photo", "Photograph"),
            ("blueprint", "Blueprint"),
            ("legal", "Legal Document"),
            ("medical", "Medical Record"),
            ("financial", "Financial Record"),
            ("contract", "Contract"),
            ("correspondence", "Correspondence"),
            ("other", "Other"),
        ],
        string="File Type",
        default="document",
        help="Category of file being retrieved",
    )

    file_format = fields.Selection(
        [
            ("paper", "Paper Document"),
            ("microfiche", "Microfiche"),
            ("microfilm", "Microfilm"),
            ("digital_printout", "Digital Printout"),
            ("other", "Other Format"),
        ],
        string="File Format",
        default="paper",
        help="Physical format of the file",
    )

    # ============================================================================
    # LOCATION AND CONTAINER INFORMATION
    # ============================================================================
    container_id = fields.Many2one(
        "records.container",
        string="Source Container",
        help="Container where this file is stored",
    )
    container_location = fields.Char(
        string="Container Location",
        related="container_id.current_location",
        store=True,
        help="Current location of the source container",
    )
    location_notes = fields.Text(
        string="Location Notes",
        help="Specific notes about where to find this file within the container",
    )
    file_position = fields.Char(
        string="File Position",
        help="Position or folder location within container (e.g., 'Folder A-C, Tab 2')",
    )

    # ============================================================================
    # STATUS AND PROGRESS TRACKING
    # ============================================================================
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("locating", "Locating"),
            ("located", "Located"),
            ("retrieving", "Retrieving"),
            ("retrieved", "Retrieved"),
            ("quality_checked", "Quality Checked"),
            ("packaged", "Packaged"),
            ("not_found", "Not Found"),
            ("damaged", "Damaged"),
        ],
        string="Status",
        default="pending",
        tracking=True,
        help="Current status of this file retrieval",
    )

    # ============================================================================
    # QUALITY AND CONDITION ASSESSMENT
    # ============================================================================
    condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
            ("illegible", "Illegible"),
        ],
        string="Condition",
        help="Physical condition of the file when retrieved",
    )

    quality_notes = fields.Text(
        string="Quality Notes",
        help="Notes about file condition or quality issues",
    )
    quality_approved = fields.Boolean(
        string="Quality Approved",
        help="Whether this file passed quality inspection",
    )
    quality_approved_by = fields.Many2one(
        "res.users",
        string="Quality Approved By",
        help="User who approved the quality of this file",
    )
    quality_approved_date = fields.Datetime(
        string="Quality Approved Date", help="Date when quality was approved"
    )

    # ============================================================================
    # TIMING FIELDS
    # ============================================================================
    date_located = fields.Datetime(
        string="Date Located", help="Date and time when file was located"
    )
    date_retrieved = fields.Datetime(
        string="Date Retrieved", help="Date and time when file was retrieved"
    )
    date_quality_checked = fields.Datetime(
        string="Date Quality Checked",
        help="Date when quality check was performed",
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        domain="[('res_model', '=', 'file.retrieval.work.order.item')]",
        string="Activities",
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        domain="[('res_model', '=', 'file.retrieval.work.order.item')]",
        string="Followers",
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        domain="[('res_model', '=', 'file.retrieval.work.order.item')]",
        string="Messages",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("name", "description")
    def _compute_display_name(self):
        for record in self:
            if record.description:
                # Limit description to 50 characters for display
                short_desc = (
                    record.description[:47] + "..."
                    if len(record.description) > 50
                    else record.description
                )
                record.display_name = _("%s - %s", record.name, short_desc)
            else:
                record.display_name = record.name or _("New Item")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_located(self):
        """Mark item as located"""
        self.ensure_one()
        self.write(
            {"status": "located", "date_located": fields.Datetime.now()}
        )

        # Update work order progress
        self.work_order_id._update_progress_metrics()

        self.message_post(
            body=_("File located successfully"), message_type="notification"
        )
        return True

    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.ensure_one()
        if self.status not in ["located", "retrieving"]:
            raise ValidationError(
                _("Item must be located before it can be retrieved")
            )

        self.write(
            {"status": "retrieved", "date_retrieved": fields.Datetime.now()}
        )

        # Update work order progress
        self.work_order_id._update_progress_metrics()

        self.message_post(
            body=_("File retrieved successfully"), message_type="notification"
        )
        return True

    def action_quality_check(self):
        """Perform quality check on retrieved file"""
        self.ensure_one()
        if self.status != "retrieved":
            raise ValidationError(
                _("Item must be retrieved before quality check")
            )

        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Check"),
            "res_model": "file.quality.check.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_item_id": self.id,
                "default_work_order_id": self.work_order_id.id,
            },
        }

    def action_approve_quality(self):
        """Approve quality for this item"""
        self.ensure_one()
        self.write(
            {
                "status": "quality_checked",
                "quality_approved": True,
                "quality_approved_by": self.env.user.id,
                "quality_approved_date": fields.Datetime.now(),
                "date_quality_checked": fields.Datetime.now(),
            }
        )

        # Update work order progress
        self.work_order_id._update_progress_metrics()

        self.message_post(
            body=_("File quality approved by %s", self.env.user.name),
            message_type="notification",
        )
        return True

    def action_mark_not_found(self):
        """Mark item as not found"""
        self.ensure_one()
        self.write({"status": "not_found"})

        self.message_post(
            body=_("File marked as not found"), message_type="notification"
        )

        # Update work order progress
        self.work_order_id._update_progress_metrics()

        return True

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("estimated_pages", "actual_pages")
    def _check_page_counts(self):
        """Validate page counts are positive"""
        for record in self:
            if record.estimated_pages < 0:
                raise ValidationError(_("Estimated pages cannot be negative"))
            if record.actual_pages and record.actual_pages < 0:
                raise ValidationError(_("Actual pages cannot be negative"))

    @api.constrains("status", "quality_approved")
    def _check_quality_approval_consistency(self):
        """Ensure quality approval is consistent with status"""
        for record in self:
            if record.quality_approved and record.status not in [
                "quality_checked",
                "packaged",
            ]:
                raise ValidationError(
                    _(
                        "Quality can only be approved for quality checked or packaged items"
                    )
                )
