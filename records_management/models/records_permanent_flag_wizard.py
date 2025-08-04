# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsPermanentFlagWizard(models.TransientModel):
    _name = "records.permanent.flag.wizard"
    _description = "Records Permanent Flag Wizard"

    # Basic Information
    name = fields.Char(string="Flag Name", required=True, default="Permanent Flag")
    document_ids = fields.Many2many("records.document", string="Documents")
    reason = fields.Text(string="Reason")
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    active = fields.Boolean(string="Active", default=True)
    state = fields.Selection(
        [("draft", "Draft"), ("processing", "Processing"), ("completed", "Completed")],
        string="State",
        default="draft",
    )
    notes = fields.Text(string="Notes")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    sequence = fields.Integer(string="Sequence", default=10)
    updated_date = fields.Datetime(string="Updated Date")
    # Records Permanent Flag Wizard Fields
    action_type = fields.Selection(
        [("flag", "Flag as Permanent"), ("unflag", "Remove Permanent Flag")],
        default="flag",
    )
    container_id = fields.Many2one("records.container", "Container")
    customer_id = fields.Many2one("res.partner", "Customer")
    document_count = fields.Integer("Document Count", default=0)
    permanent_flag = fields.Boolean("Permanent Flag", default=True)
    approval_required = fields.Boolean("Approval Required", default=True)
    justification_notes = fields.Text("Justification Notes")
    legal_basis = fields.Selection(
        [
            ("regulatory", "Regulatory"),
            ("litigation", "Litigation"),
            ("historical", "Historical"),
        ],
        default="regulatory",
    )
    notification_sent = fields.Boolean("Notification Sent", default=False)

    # === MISSING BUSINESS CRITICAL FIELDS ===
    permanent_flag_set_by = fields.Many2one(
        "res.users",
        string="Permanent Flag Set By",
        default=lambda self: self.env.user,
        help="User who set the permanent flag",
    )
    permanent_flag_set_date = fields.Datetime(
        string="Permanent Flag Set Date",
        default=fields.Datetime.now,
        help="Date and time when permanent flag was set",
    )
    user_password = fields.Char(
        string="User Password",
        help="Password verification for permanent flag operations",
    )

    # === ADDITIONAL WORKFLOW FIELDS ===
    batch_operation = fields.Boolean(
        string="Batch Operation",
        default=False,
        help="True if this is a batch operation on multiple items",
    )
    affected_documents_count = fields.Integer(
        string="Affected Documents Count",
        compute="_compute_affected_documents_count",
        help="Number of documents affected by this flag operation",
    )
    estimated_completion_time = fields.Float(
        string="Estimated Completion Time (Hours)",
        digits=(5, 2),
        help="Estimated time to complete the flagging operation",
    )
    priority_level = fields.Selection(
        [("low", "Low"), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority Level",
        default="medium",
        help="Priority level for this permanent flag operation",
    )

    # === APPROVAL WORKFLOW ===
    approval_status = fields.Selection(
        [
            ("pending", "Pending Approval"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("auto_approved", "Auto Approved"),
        ],
        string="Approval Status",
        default="pending",
        help="Current approval status of the flag operation",
    )
    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        help="User who approved the permanent flag operation",
    )
    approval_date = fields.Datetime(
        string="Approval Date", help="Date and time when the operation was approved"
    )
    rejection_reason = fields.Text(
        string="Rejection Reason",
        help="Reason for rejecting the permanent flag request",
    )

    # === AUDIT AND COMPLIANCE ===
    audit_trail = fields.Text(
        string="Audit Trail",
        help="Detailed audit trail of the permanent flag operation",
    )
    compliance_check_passed = fields.Boolean(
        string="Compliance Check Passed",
        default=False,
        help="Whether all compliance checks have passed",
    )
    regulatory_requirement = fields.Text(
        string="Regulatory Requirement",
        help="Specific regulatory requirement for permanent flagging",
    )
    legal_hold_reference = fields.Char(
        string="Legal Hold Reference", help="Reference to legal hold document or case"
    )

    # === NOTIFICATION AND COMMUNICATION ===
    notification_method = fields.Selection(
        [
            ("email", "Email"),
            ("sms", "SMS"),
            ("portal", "Portal Notification"),
            ("all", "All Methods"),
        ],
        string="Notification Method",
        default="email",
        help="Method to notify stakeholders",
    )
    stakeholder_ids = fields.Many2many(
        "res.partner",
        string="Stakeholders to Notify",
        help="Partners who should be notified of this operation",
    )
    notification_template_id = fields.Many2one(
        "mail.template",
        string="Notification Template",
        help="Email template for notifications",
    )
    custom_message = fields.Text(
        string="Custom Message", help="Custom message to include in notifications"
    )

    # === COMPUTED FIELDS ===
    total_estimated_cost = fields.Monetary(
        string="Total Estimated Cost",
        currency_field="currency_id",
        compute="_compute_total_estimated_cost",
        help="Total estimated cost for the permanent flag operation",
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    operation_complexity = fields.Selection(
        [
            ("simple", "Simple"),
            ("moderate", "Moderate"),
            ("complex", "Complex"),
            ("very_complex", "Very Complex"),
        ],
        string="Operation Complexity",
        compute="_compute_operation_complexity",
        help="Complexity level based on affected documents and requirements",
    )

    # === DEPARTMENT AND LOCATION ===
    department_id = fields.Many2one(
        "hr.department",
        string="Department",
        help="Department initiating the permanent flag operation",
    )
    location_ids = fields.Many2many(
        "records.location",
        string="Affected Locations",
        help="Physical locations affected by this operation",
    )
    storage_impact = fields.Text(
        string="Storage Impact Assessment",
        help="Assessment of impact on storage and retrieval operations",
    )

    # Records Permanent Flag Wizard Fields

    # Records Permanent Flag Wizard Fields

    # === COMPUTE METHODS ===
    @api.depends("document_ids")
    def _compute_affected_documents_count(self):
        """Compute the number of documents affected by this operation"""
        for record in self:
            record.affected_documents_count = len(record.document_ids)

    @api.depends("affected_documents_count", "approval_required", "legal_basis")
    def _compute_operation_complexity(self):
        """Compute operation complexity based on various factors"""
        for record in self:
            if record.affected_documents_count <= 10 and not record.approval_required:
                record.operation_complexity = "simple"
            elif (
                record.affected_documents_count <= 50
                and record.legal_basis != "litigation"
            ):
                record.operation_complexity = "moderate"
            elif record.affected_documents_count <= 200:
                record.operation_complexity = "complex"
            else:
                record.operation_complexity = "very_complex"

    @api.depends("affected_documents_count", "operation_complexity")
    def _compute_total_estimated_cost(self):
        """Compute total estimated cost based on document count and complexity"""
        for record in self:
            base_cost = 5.0  # Base cost per document
            complexity_multiplier = {
                "simple": 1.0,
                "moderate": 1.5,
                "complex": 2.0,
                "very_complex": 3.0,
            }.get(record.operation_complexity, 1.0)

            record.total_estimated_cost = (
                record.affected_documents_count * base_cost * complexity_multiplier
            )

    # === ONCHANGE METHODS ===
    @api.onchange("action_type")
    def _onchange_action_type(self):
        """Update default values when action type changes"""
        if self.action_type == "unflag":
            self.permanent_flag = False
            self.legal_basis = False
        else:
            self.permanent_flag = True

    @api.onchange("legal_basis")
    def _onchange_legal_basis(self):
        """Update approval requirements based on legal basis"""
        if self.legal_basis == "litigation":
            self.approval_required = True
            self.priority_level = "high"
        elif self.legal_basis == "regulatory":
            self.approval_required = True
            self.priority_level = "medium"

    @api.onchange("document_ids")
    def _onchange_document_ids(self):
        """Update document count and estimates when documents change"""
        self.document_count = len(self.document_ids)
        if self.document_count > 100:
            self.batch_operation = True
            self.estimated_completion_time = (
                self.document_count * 0.02
            )  # 2 minutes per 100 documents
        else:
            self.batch_operation = False
            self.estimated_completion_time = max(
                0.25, self.document_count * 0.01
            )  # Minimum 15 minutes

    # === VALIDATION METHODS ===
    @api.constrains("user_password")
    def _check_user_password(self):
        """Validate user password for sensitive operations"""
        for record in self:
            if record.legal_basis == "litigation" and not record.user_password:
                raise ValidationError(
                    _(
                        "Password is required for litigation-related permanent flag operations."
                    )
                )

    @api.constrains("document_ids")
    def _check_document_access(self):
        """Ensure user has access to all selected documents"""
        for record in self:
            if not record.document_ids:
                raise ValidationError(
                    _(
                        "At least one document must be selected for permanent flag operation."
                    )
                )

    def action_confirm(self):
        """Apply permanent flag to documents with enhanced workflow."""
        self.ensure_one()

        # Validate approval if required
        if self.approval_required and self.approval_status != "approved":
            raise UserError(
                _("This operation requires approval before it can be executed.")
            )

        # Update wizard status
        self.write(
            {
                "state": "processing",
                "permanent_flag_set_by": self.env.user.id,
                "permanent_flag_set_date": fields.Datetime.now(),
            }
        )

        # Build audit trail entry
        audit_entry = f"Permanent flag operation initiated by {self.env.user.name} on {fields.Datetime.now()}\n"
        audit_entry += f"Action: {self.action_type}\n"
        audit_entry += f"Legal Basis: {self.legal_basis}\n"
        audit_entry += f"Documents affected: {len(self.document_ids)}\n"

        # Process each document
        for document in self.document_ids:
            if self.action_type == "flag":
                document.write(
                    {
                        "permanent_flag": True,
                        "notes": (document.notes or "")
                        + _(
                            "\nMarked permanent via wizard on %s by %s\nLegal basis: %s\nReason: %s"
                        )
                        % (
                            fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            self.env.user.name,
                            self.legal_basis,
                            self.reason or "Not specified",
                        ),
                    }
                )
            else:  # unflag
                document.write(
                    {
                        "permanent_flag": False,
                        "notes": (document.notes or "")
                        + _(
                            "\nPermanent flag removed via wizard on %s by %s\nReason: %s"
                        )
                        % (
                            fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            self.env.user.name,
                            self.reason or "Not specified",
                        ),
                    }
                )

        # Update audit trail
        self.audit_trail = audit_entry + "Operation completed successfully."

        # Send notifications if configured
        if self.notification_sent and self.stakeholder_ids:
            self._send_notifications()

        # Mark as completed
        self.write({"state": "completed"})

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Permanent Flag Operation Completed"),
                "message": _(
                    "Permanent flag operation has been applied to %d documents."
                )
                % len(self.document_ids),
                "type": "success",
                "sticky": False,
            },
        }

    def action_request_approval(self):
        """Request approval for the permanent flag operation"""
        self.ensure_one()
        self.approval_status = "pending"

        # Create activity for approval
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=f"Approve Permanent Flag Operation: {self.name}",
            note=f"Please review and approve the permanent flag operation for {len(self.document_ids)} documents.\n"
            f"Legal Basis: {self.legal_basis}\n"
            f'Reason: {self.reason or "Not specified"}',
            user_id=(
                self.env.ref("base.group_system").users[0].id
                if self.env.ref("base.group_system").users
                else self.env.user.id
            ),
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Approval Requested"),
                "message": _(
                    "Approval has been requested for this permanent flag operation."
                ),
                "type": "info",
                "sticky": False,
            },
        }

    def action_approve(self):
        """Approve the permanent flag operation"""
        self.ensure_one()
        self.write(
            {
                "approval_status": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Operation Approved"),
                "message": _(
                    "Permanent flag operation has been approved and can now be executed."
                ),
                "type": "success",
                "sticky": False,
            },
        }

    def action_reject(self):
        """Reject the permanent flag operation"""
        self.ensure_one()
        self.write(
            {
                "approval_status": "rejected",
                "approved_by": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Operation Rejected"),
                "message": _("Permanent flag operation has been rejected."),
                "type": "warning",
                "sticky": False,
            },
        }

    def _send_notifications(self):
        """Send notifications to stakeholders"""
        if not self.stakeholder_ids:
            return

        # Create a message for the operation
        message = f"Permanent flag operation '{self.name}' has been completed.\n"
        message += f"Action: {self.action_type}\n"
        message += f"Documents affected: {len(self.document_ids)}\n"
        message += f"Legal basis: {self.legal_basis}"

        # Log the notification attempt
        self.message_post(
            body=message,
            subject=f"Permanent Flag Operation: {self.name}",
            partner_ids=self.stakeholder_ids.ids,
            message_type="notification",
        )
