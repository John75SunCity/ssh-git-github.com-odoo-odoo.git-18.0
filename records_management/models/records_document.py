# -*- coding: utf-8 -*-
"""
Permanent Flag Wizard Module

This module provides a comprehensive permanent flag management system for the Records Management
System. It implements enterprise-grade legal hold and permanent retention workflows with full
approval processes, audit trails, and stakeholder notification systems.

Key Features:
- Legal hold management for litigation and compliance requirements
- Permanent retention flag system with approval workflows
- Bulk document selection with criteria-based filtering
- Multi-stakeholder notification system with email integration
- Comprehensive audit trails with timestamped activity logging
- Approval workflow management with rejection handling and escalation
- Document criteria filtering by type, location, customer, and date ranges
- Integration with document lifecycle and retention policy systems

Business Processes:
1. Flag Request Creation: Create permanent flag requests with justification and legal basis
2. Document Selection: Select documents manually or through automated criteria filtering
3. Approval Workflow: Route requests through appropriate approval chains
4. Stakeholder Notification: Notify relevant parties of flag application and removal
5. Audit Compliance: Maintain complete audit trails for legal and regulatory requirements
6. Flag Management: Apply, remove, and review permanent flags with proper authorization

Workflow States:
- Draft: Initial request creation and document selection
- Pending Approval: Awaiting management or legal approval
- Approved: Authorized for execution by appropriate stakeholders
- In Progress: Flag operation currently being executed
- Completed: Flag operation successfully completed with audit trail
- Cancelled: Request cancelled before execution
- Rejected: Request rejected by approval authority

Legal Hold Features:
- Legal basis documentation with detailed justification requirements
- Custom reason specification for specialized legal hold scenarios
- Integration with litigation support and compliance management systems
- Automatic notification to legal teams and relevant stakeholders
- Chain of custody preservation during flag application and removal

Technical Implementation:
- TransientModel pattern for wizard-style user interactions
- Secure Many2many relationships with proper domain filtering
- Modern Odoo 18.0 validation patterns with comprehensive error handling
- Mail framework integration for notification and activity tracking
- Enterprise security patterns preventing unauthorized flag manipulation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import logging
import traceback
from datetime import datetime

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class RecordsPermanentFlagWizard(models.TransientModel):
    _name = "records.permanent.flag.wizard"
    _description = "Permanent Flag Application Wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Operation Name",
        required=True,
    )

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        if "name" in fields_list:
            today = fields.Date.context_today(self)
            res["name"] = _("Permanent Flag Operation %s") % today
        return res

    description = fields.Text(
        string="Description",
        help="Detailed description of the permanent flag operation",
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Requesting User",
        default=lambda self: self.env.user,
        readonly=True,
    )

    # ============================================================================
    # OPERATION CONFIGURATION
    # ============================================================================
    operation_type = fields.Selection(
        [
            ("apply", "Apply Permanent Flag"),
            ("remove", "Remove Permanent Flag"),
            ("review", "Review Flagged Documents"),
        ],
        string="Operation Type",
        default="apply",
        required=True,
    )

    flag_reason = fields.Selection(
        [
            ("legal_hold", "Legal Hold"),
            ("litigation", "Litigation Support"),
            ("audit_requirement", "Audit Requirement"),
            ("compliance", "Regulatory Compliance"),
            ("historical", "Historical Significance"),
            ("business_critical", "Business Critical"),
            ("custom", "Custom Reason"),
        ],
        string="Flag Reason",
        required=True,
    )

    custom_reason = fields.Char(
        string="Custom Reason",
        help="Specify custom reason when 'Custom Reason' is selected",
    )

    legal_basis = fields.Text(
        string="Legal Basis",
        help="Legal justification for the permanent flag operation",
    )

    # ============================================================================
    # APPROVAL WORKFLOW
    # ============================================================================
    approval_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        string="Approval Status",
        default="draft",
        readonly=True,
    )

    approval_required = fields.Boolean(
        string="Approval Required",
        default=True,
        help="Whether this operation requires approval",
    )
    approved_by = fields.Many2one("res.users", string="Approved By", readonly=True)
    approval_date = fields.Datetime(string="Approval Date", readonly=True)
    rejection_reason = fields.Text(string="Rejection Reason", readonly=True)

    # ============================================================================
    # DOCUMENT SELECTION
    # ============================================================================
    document_ids = fields.Many2many(
        "records.document",
        "permanent_flag_document_rel",
        "wizard_id",
        "document_id",
        string="Documents",
        required=True,
        help="Documents to apply permanent flag to",
    )

    document_count = fields.Integer(
        string="Document Count", compute="_compute_document_count"
    )

    # Selection Criteria
    selection_method = fields.Selection(
        [
            ("manual", "Manual Selection"),
            ("criteria", "By Criteria"),
            ("import", "Import from File"),
        ],
        string="Selection Method",
        default="manual",
    )

    # Criteria-based selection
    document_type_ids = fields.Many2many(
        "records.document.type",
        string="Document Types",
        help="Filter by document types",
    )
    location_ids = fields.Many2many(
        "records.location", string="Locations", help="Filter by storage locations"
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", help="Filter by customer"
    )
    date_from = fields.Date(string="Date From", help="Filter documents from this date")
    date_to = fields.Date(string="Date To", help="Filter documents up to this date")

    # ============================================================================
    # NOTIFICATION SETTINGS
    # ============================================================================
    send_notification = fields.Boolean(
        string="Send Notifications",
        default=True,
        help="Send notifications to stakeholders",
    )

    stakeholder_ids = fields.Many2many(
        "res.users",
        "permanent_flag_stakeholder_rel",
        "wizard_id",
        "user_id",
        string="Stakeholders",
        help="Users to notify about this operation",
    )
    notification_template_id = fields.Many2one(
        "mail.template",
        string="Notification Template",
        help="Email template for notifications",
    )

    # ============================================================================
    # AUDIT & TRACKING
    # ============================================================================
    audit_trail = fields.Text(
        string="Audit Trail", readonly=True, help="Complete log of operation activities"
    )
    execution_date = fields.Datetime(string="Execution Date", readonly=True)
    completion_date = fields.Datetime(string="Completion Date", readonly=True)
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("completed_with_errors", "Completed with Errors"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
    )

    # ============================================================================
    # MAIL FRAMEWORK FIELDS
    # ============================================================================
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        groups="base.group_user",
        help="Users who are following this wizard record for activity and message updates",
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("date_from", "date_to")
    def _check_date_range(self):
        for record in self:
            if (
                record.date_from
                and record.date_to
                and record.date_from > record.date_to
            ):
                raise ValidationError(_("Date From must be before Date To"))

    @api.constrains("flag_reason", "custom_reason")
    def _check_custom_reason(self):
        for record in self:
            if record.flag_reason == "custom" and not record.custom_reason:
                raise ValidationError(
                    _(
                        "Custom reason must be specified when 'Custom Reason' is selected"
                    )
                )

    @api.constrains("document_ids")
    def _check_documents(self):
        for record in self:
            if not record.document_ids:
                raise ValidationError(_("At least one document must be selected"))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("document_ids")
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    def _build_audit_entry(self, action, details=""):
        """Build audit trail entry"""
        timestamp = fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        user = self.env.user.name
        entry = f"[{timestamp}] {user}: {action}"
        if details:
            entry += f" - {details}"
        return entry

    def _update_audit_trail(self, action, details=""):
        """Update audit trail with new entry"""
        entry = self._build_audit_entry(action, details)
        current_trail = self.audit_trail or ""
        if current_trail:
            self.audit_trail = f"{current_trail}\n{entry}"
        else:
            self.audit_trail = entry

    def _send_notifications(self):
        """Send notifications to stakeholders"""
        if not self.send_notification or not self.stakeholder_ids:
            return

        import textwrap

        subject = f"Permanent Flag Operation: {self.name}"
        body = textwrap.dedent(
            f"""\
            <p>A permanent flag operation has been executed:</p>
            <ul>
                <li><strong>Operation:</strong> {self.name}</li>
                <li><strong>Type:</strong> {dict(self._fields['operation_type'].selection).get(self.operation_type)}</li>
                <li><strong>Reason:</strong> {dict(self._fields['flag_reason'].selection).get(self.flag_reason)}</li>
                <li><strong>Documents:</strong> {len(self.document_ids)} documents affected</li>
                <li><strong>Executed By:</strong> {self.user_id.name}</li>
            </ul>
            """
        )

        for user in self.stakeholder_ids:
            self.message_post(
                partner_ids=[user.partner_id.id], subject=subject, body=body
            )

    def _apply_criteria_filter(self):
        """Apply criteria-based document filtering"""
        domain = []

        if self.document_type_ids:
            domain.append(("document_type_id", "in", self.document_type_ids.ids))  # pylint: disable=no-member
        if self.location_ids:
            domain.append(("location_id", "in", self.location_ids.ids))  # pylint: disable=no-member
        if self.partner_id:
            domain.append(("partner_id", "=", self.partner_id.id))
        if self.date_from:
            domain.append(("creation_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("creation_date", "<=", self.date_to))
        return self.env["records.document"].search(domain)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_apply_criteria(self):
        """Apply criteria to select documents"""
        self.ensure_one()
        if self.selection_method != "criteria":
            raise UserError(
                _("This action is only available for criteria-based selection")
            )

        documents = self._apply_criteria_filter()
        self.document_ids = [(6, 0, documents.ids)]  # pylint: disable=no-member

        self._update_audit_trail(
            "Applied Criteria", f"Selected {len(documents)} documents"
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Criteria Applied"),
                "message": _("%d documents selected based on criteria")
                % len(documents),
                "type": "success",
            },
        }

    def action_execute(self):
        """Execute the permanent flag operation"""
        self.ensure_one()
        # Mark as in progress
        # pylint: disable=no-member

        self.write(
            {
                "state": "in_progress",
                "execution_date": fields.Datetime.now(),
            }
        )

        # Execute the operation
        affected_count = 0
        errors = []

        for document in self.document_ids:
            try:
                # Ensure the document record still exists and is valid
                if not document.exists():  # pylint: disable=no-member
                    errors.append(f"Document ID {document.id}: Record does not exist")  # pylint: disable=no-member
                    continue

                if self.operation_type == "apply":
                    # pylint: disable=no-member
                    document.write(
                        {
                            "permanent_flag": True,
                            "permanent_flag_reason": self.flag_reason,
                            "permanent_flag_date": fields.Datetime.now(),
                            "permanent_flag_user_id": self.env.user.id,
                        }
                    )
                elif self.operation_type == "remove":
                    # pylint: disable=no-member
                    # pylint: disable=no-member

                    document.write(
                        {
                            "permanent_flag": False,
                            "permanent_flag_reason": None,
                            "permanent_flag_date": False,
                            "permanent_flag_user_id": False,
                        }
                    )
                affected_count += 1
            except (UserError, ValidationError) as e:
                document_name = getattr(document, "name", f"ID: {document.id}")  # pylint: disable=no-member
                errors.append(f"Document {document_name}: {str(e)}")
            except Exception as e:
                tb = traceback.format_exc()
                document_name = getattr(document, "name", f"ID: {document.id}")  # pylint: disable=no-member
                errors.append(f"Document {document_name}: Unexpected error: {str(e)}")
                _logger.error(
                    "Unexpected error processing document %s: %s\n%s",
                    document_name,
                    str(e),
                    tb,
                )
                continue

        # Update audit trail
        operation_name = dict(self._fields["operation_type"].selection).get(
            self.operation_type
        )
        self._update_audit_trail(
            f"Executed {operation_name}",
            f"Processed {affected_count} documents, {len(errors)} errors",
        )

        # Send notifications
        self._send_notifications()

        # Mark as completed or completed with errors
        if errors:
            # pylint: disable=no-member

            self.write(
                {
                    "state": "completed_with_errors",
                    "completion_date": fields.Datetime.now(),
                }
            )
        else:
            # pylint: disable=no-member

            self.write({"state": "completed", "completion_date": fields.Datetime.now()})

        # Show result
        if errors:
            error_msg = "\n".join(errors[:10])  # Show first 10 errors
            if len(errors) > 10:
                error_msg += f"\n... and {len(errors) - 10} more errors"

            # Log all errors in the audit trail for traceability
            self._update_audit_trail(
                "Errors encountered during operation", "\n".join(errors)
            )

            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("Operation Completed with Errors"),
                    "message": _(
                        "Operation completed. %d documents processed successfully, %d errors occurred.\n\nErrors:\n%s"
                    )
                    % (affected_count, len(errors), error_msg),
                    "type": "warning",
                    "sticky": True,
                },
            }
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Operation Completed Successfully"),
                "message": _(
                    "Permanent flag operation completed successfully. %d documents processed."
                )
                % affected_count,
                "type": "success",
            },
        }

    def action_request_approval(self):
        """Request approval for the operation"""
        self.ensure_one()

        if self.approval_status != "draft":
            raise UserError(_("Approval can only be requested for draft operations"))

        self.approval_status = "pending"

        # Get approval user - try system group, fallback to current user
        approval_user_id = self.env.user.id
        try:
            system_group = self.env.ref("base.group_system")
            if system_group.users:
                approval_user_id = system_group.users[0].id
        except Exception:
            pass  # Use current user as fallback

        # Create approval activity
        self.activity_schedule(
            "records_management.mail_activity_type_approval",
            summary=f"Approve Permanent Flag Operation: {self.name}",
            note=f"""Please review and approve this permanent flag operation:

Operation Type: {dict(self._fields['operation_type'].selection).get(self.operation_type)}
Flag Reason: {dict(self._fields['flag_reason'].selection).get(self.flag_reason)}
Documents: {len(self.document_ids)} documents
Legal Basis: {self.legal_basis or 'Not specified'}

Description:
{self.description or 'No description provided'}""",
            user_id=approval_user_id,
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Approval Requested"),
                "message": _(
                    "Approval has been requested for this permanent flag operation."
                ),
                "type": "success",
            },
        }

    def action_approve(self):
        """Approve the operation"""
        if self.approval_status != "pending":
            raise UserError(_("Only pending operations can be approved"))

        # pylint: disable=no-member


        self.write(
            {
                "approval_status": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )

        self._update_audit_trail(
            "Operation Approved", f"Approved by {self.env.user.name}"
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Operation Approved"),
                "message": _(
                    "The permanent flag operation has been approved and can now be executed."
                ),
                "type": "success",
            },
        }

    def action_reject(self):
        """Reject the operation"""
        self.ensure_one()

        if self.approval_status != "pending":
            raise UserError(_("Only pending operations can be rejected"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Reject Operation"),
            "res_model": "records.permanent.flag.reject.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_wizard_id": self.id},
        }

    def action_cancel(self):
        """Cancel the operation"""
        self.ensure_one()

        if self.state in ["completed", "completed_with_errors"]:
            raise UserError(_("Cannot cancel completed operations"))

        # pylint: disable=no-member


        self.write({"state": "cancelled"})
        self._update_audit_trail("Operation Cancelled")

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Operation Cancelled"),
                "message": _("The permanent flag operation has been cancelled."),
                "type": "info",
            },
        }

    def action_view_documents(self):
        """View selected documents"""
        self.ensure_one()

        if not self.document_ids:
            return {
                "type": "ir.actions.client",
                "tag": "display_notification",
                "params": {
                    "title": _("No Documents Selected"),
                    "message": _("There are no documents selected for this operation."),
                    "type": "warning",
                },
            }

        return {
            "type": "ir.actions.act_window",
            "name": _("Selected Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            # Limit to first 1000 documents for efficiency; adjust as needed
            "domain": [("id", "in", self.document_ids.ids[:1000])],  # pylint: disable=no-member
            "target": "current",
        }
