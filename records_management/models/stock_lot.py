# -*- coding: utf-8 -*-
"""
Stock Lot Extensions for Records Management

This module extends the stock.lot model to provide enhanced tracking capabilities
for records management operations, including document counting, quality status
tracking, and destruction eligibility management.

Key Features:
- Records-specific tracking capabilities
- Document count computation and tracking
- Quality status management with approval workflow
- Destruction eligibility tracking for compliance
- Enhanced movement and location tracking
- Quality check integration and scheduling

Business Processes:
1. Lot Creation: Initial lot setup with records tracking enabled
2. Document Association: Link documents to lots for tracking
3. Quality Management: Approve or reject lots based on quality criteria
4. Destruction Planning: Mark lots eligible for secure destruction
5. Movement Tracking: Complete audit trail of lot movements
6. Location Management: Real-time location tracking and reporting

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class StockLot(models.Model):
    """Stock Lot Extensions for Records Management"""

    _inherit = "stock.lot"

    # ============================================================================
    # RECORDS MANAGEMENT SPECIFIC FIELDS
    # ============================================================================
    records_tracking = fields.Boolean(
        string="Records Tracking",
        default=False,
        help="Enable records management tracking for this lot",
    )
    document_count = fields.Integer(
        string="Document Count",
        compute="_compute_document_count",
        store=True,
        help="Number of documents associated with this lot",
    )
    destruction_eligible = fields.Boolean(
        string="Eligible for Destruction",
        default=False,
        tracking=True,
        help="Whether this lot is eligible for secure destruction",
    )
    quality_status = fields.Selection(
        [
            ("pending", "Pending Review"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Quality Status",
        default="pending",
        tracking=True,
        help="Quality approval status for records management",
    )

    # ============================================================================
    # ADDITIONAL TRACKING FIELDS
    # ============================================================================
    retention_date = fields.Date(
        string="Retention Date", help="Date when retention period expires"
    )
    destruction_date = fields.Date(
        string="Scheduled Destruction Date",
        help="Scheduled date for secure destruction",
    )
    compliance_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("confidential", "Confidential"),
            ("classified", "Classified"),
        ],
        string="Compliance Level",
        default="standard",
        help="Security classification level",
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required",
        default=False,
        help="Whether chain of custody tracking is required",
    )
    last_audit_date = fields.Date(
        string="Last Audit Date", help="Date of last compliance audit"
    )
    audit_notes = fields.Text(string="Audit Notes", help="Notes from compliance audits")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    document_ids = fields.One2many(
        "records.document",
        "lot_id",
        string="Associated Documents",
        help="Documents linked to this lot",
    )
    quality_check_ids = fields.One2many(
        "quality.check",
        "lot_id",
        string="Quality Checks",
        help="Quality checks performed on this lot",
    )
    custody_event_ids = fields.One2many(
        "naid.custody.event",
        "lot_id",
        string="Custody Events",
        help="Chain of custody events for this lot",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        """Compute number of documents associated with this lot"""
        for record in self:
            record.document_count = len(record.document_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_print_label(self):
        """Print lot identification label"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.stock_lot_label_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    def action_schedule_quality_check(self):
        """Schedule quality check for this lot"""
        self.ensure_one()

        # Create quality check activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Quality Check: %s") % self.name,
            note=_("Perform quality assessment including condition review and compliance verification."),
            user_id=self.env.user.id,
        )

        self.message_post(body=_("Quality check scheduled for %s") % self.name)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Quality Check Scheduled"),
                "message": _("Quality check has been scheduled for this lot."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_approve_quality(self):
        """Approve lot quality status"""
        self.ensure_one()
        if self.quality_status == "approved":
            raise UserError(_("Lot is already approved."))

        self.write(
            {
                "quality_status": "approved",
                "last_audit_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Lot quality approved"))

    def action_reject_quality(self):
        """Reject lot quality status"""
        self.ensure_one()
        if self.quality_status == "rejected":
            raise UserError(_("Lot is already rejected."))

        self.write(
            {
                "quality_status": "rejected",
                "destruction_eligible": False,
                "last_audit_date": fields.Date.today(),
            }
        )
        self.message_post(body=_("Lot quality rejected"))

    def action_mark_destruction_eligible(self):
        """Mark lot as eligible for destruction"""
        self.ensure_one()
        if self.quality_status != "approved":
            raise UserError(_("Only approved lots can be marked for destruction."))

        self.write({"destruction_eligible": True})
        self.message_post(body=_("Lot marked eligible for destruction"))

    def action_schedule_destruction(self):
        """Schedule destruction for this lot"""
        self.ensure_one()
        if not self.destruction_eligible:
            raise UserError(_("Lot must be eligible for destruction."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Destruction"),
            "res_model": "shredding.service",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_lot_id": self.id,
                "default_material_type": "mixed",
                "default_service_type": "offsite",
            },
        }

    def action_track_history(self):
        """View movement history of this lot"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Lot Movement History"),
            "res_model": "stock.move.line",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "search_default_lot_id": self.id,
                "group_by": "date",
            },
        }

    def action_view_location(self):
        """View current location of this lot"""
        self.ensure_one()
        quants = self.env["stock.quant"].search(
            [("lot_id", "=", self.id), ("quantity", ">", 0)]
        )

        if not quants:
            raise UserError(_("No current location found for this lot."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Current Location"),
            "res_model": "stock.location",
            "res_id": quants[0].location_id.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_view_documents(self):
        """View associated documents"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Associated Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {"default_lot_id": self.id},
        }

    def action_open_quality_checks(self):
        """View quality checks for this lot"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Checks"),
            "res_model": "quality.check",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "default_lot_id": self.id,
                "search_default_lot_id": self.id,
            },
        }

    def action_view_custody_events(self):
        """View chain of custody events"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody Events"),
            "res_model": "naid.custody.event",
            "view_mode": "tree,form",
            "domain": [("lot_id", "=", self.id)],
            "context": {
                "default_lot_id": self.id,
                "search_default_lot_id": self.id,
            },
        }

    def action_create_custody_event(self):
        """Create new chain of custody event"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Custody Event"),
            "res_model": "naid.custody.event",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_lot_id": self.id,
                "default_event_type": "transfer",
            },
        }

    def action_generate_compliance_report(self):
        """Generate compliance report for this lot"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.lot_compliance_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _check_retention_compliance(self):
        """Check if lot is compliant with retention policies"""
        self.ensure_one()

        if not self.retention_date:
            return {"compliant": True, "message": "No retention date set"}

        today = fields.Date.today()
        if self.retention_date < today:
            return {
                "compliant": False,
                "message": f"Retention period expired on {self.retention_date}",
            }

        return {"compliant": True, "message": "Within retention period"}

    def get_lot_summary(self):
        """Get summary information for this lot"""
        self.ensure_one()
        return {
            "name": self.name,
            "product": self.product_id.name if self.product_id else None,
            "records_tracking": self.records_tracking,
            "document_count": self.document_count,
            "quality_status": self.quality_status,
            "destruction_eligible": self.destruction_eligible,
            "compliance_level": self.compliance_level,
            "retention_date": self.retention_date,
            "last_audit_date": self.last_audit_date,
        }

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains("retention_date", "destruction_date")
    def _check_dates(self):
        """Validate retention and destruction dates"""
        for record in self:
            if record.retention_date and record.destruction_date:
                if record.destruction_date < record.retention_date:
                    raise UserError(
                        _("Destruction date cannot be before retention date.")
                    )
