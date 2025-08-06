# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PortalRequest(models.Model):
    _name = "portal.request"
    _description = "Portal Customer Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, create_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Request #", required=True, tracking=True, index=True)
    reference = fields.Char(string="Reference", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("under_review", "Under Review"),
            ("approved", "Approved"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("rejected", "Rejected"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        required=True,
        tracking=True,
        index=True,
    )

    # ============================================================================
    # REQUEST DETAILS
    # ============================================================================
    request_type = fields.Selection(
        [
            ("destruction", "Document Destruction"),
            ("retrieval", "Document Retrieval"),
            ("storage", "Document Storage"),
            ("pickup", "Document Pickup"),
            ("shredding", "On-Site Shredding"),
            ("consultation", "Consultation"),
            ("audit", "Compliance Audit"),
            ("other", "Other"),
        ],
        string="Request Type",
        required=True,
        tracking=True,
        index=True,
    )

    priority = fields.Selection(
        [("0", "Low"), ("1", "Normal"), ("2", "High"), ("3", "Urgent")],
        string="Priority",
        default="1",
        tracking=True,
        index=True,
    )

    urgency_reason = fields.Text(string="Urgency Reason")
    internal_notes = fields.Text(string="Internal Notes")
    public_notes = fields.Text(string="Public Notes", tracking=True)

    # ============================================================================
    # CUSTOMER & CONTACT INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True, index=True
    )
    contact_person = fields.Char(string="Contact Person", tracking=True)
    contact_email = fields.Char(string="Contact Email", tracking=True)
    contact_phone = fields.Char(string="Contact Phone", tracking=True)
    notification_email = fields.Char(string="Notification Email")

    # ============================================================================
    # SCHEDULING & TIMING
    # ============================================================================
    requested_date = fields.Datetime(string="Requested Date", tracking=True)
    scheduled_date = fields.Datetime(string="Scheduled Date", tracking=True)
    deadline = fields.Datetime(string="Deadline", tracking=True)
    completion_date = fields.Datetime(string="Completion Date", tracking=True)
    estimated_hours = fields.Float(string="Estimated Hours")
    actual_hours = fields.Float(string="Actual Hours")

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )
    estimated_cost = fields.Monetary(
        string="Estimated Cost", currency_field="currency_id", tracking=True
    )
    actual_cost = fields.Monetary(
        string="Actual Cost", currency_field="currency_id", tracking=True
    )
    billing_status = fields.Selection(
        [
            ("not_billable", "Not Billable"),
            ("to_bill", "To Bill"),
            ("billed", "Billed"),
            ("paid", "Paid"),
        ],
        string="Billing Status",
        default="not_billable",
        tracking=True,
    )

    # ============================================================================
    # DOCUMENT & SERVICE SPECIFICATIONS
    # ============================================================================
    document_count = fields.Integer(string="Document Count")
    box_count = fields.Integer(string="Box Count")
    weight_estimate = fields.Float(string="Weight Estimate (lbs)")
    service_location = fields.Char(string="Service Location")
    access_instructions = fields.Text(string="Access Instructions")
    special_requirements = fields.Text(string="Special Requirements")

    # ============================================================================
    # APPROVAL & WORKFLOW
    # ============================================================================
    approval_required = fields.Boolean(string="Approval Required", default=False)
    approved_by = fields.Many2one("res.users", string="Approved By", tracking=True)
    approval_date = fields.Datetime(string="Approval Date", tracking=True)
    rejection_reason = fields.Text(string="Rejection Reason", tracking=True)

    # ============================================================================
    # E-SIGNATURE FIELDS
    # ============================================================================
    signature_required = fields.Boolean(string="Signature Required", default=False)
    customer_signature = fields.Binary(string="Customer Signature")
    customer_signature_date = fields.Datetime(string="Customer Signature Date")
    technician_signature = fields.Binary(string="Technician Signature")
    technician_signature_date = fields.Datetime(string="Technician Signature Date")
    signed_document = fields.Binary(string="Signed Document")

    # ============================================================================
    # COMPLIANCE & TRACKING
    # ============================================================================
    requires_naid_compliance = fields.Boolean(
        string="NAID Compliance Required", default=False
    )
    compliance_notes = fields.Text(string="Compliance Notes")
    audit_trail = fields.Text(string="Audit Trail")
    certificate_of_destruction = fields.Binary(string="Certificate of Destruction")
    tracking_number = fields.Char(string="Tracking Number", index=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # Missing inverse field for service.item One2many relationship
    service_item_id = fields.Many2one("service.item", string="Service Item")

    # ============================================================================
    # Service connections
    shredding_service_id = fields.Many2one(
        "shredding.service", string="Related Shredding Service"
    )
    pickup_request_id = fields.Many2one(
        "pickup.request", string="Related Pickup Request"
    )
    work_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Related Work Order"
    )

    # Document attachments
    attachment_ids = fields.One2many(
        "ir.attachment",
        "res_id",
        string="Attachments",
        domain=[("res_model", "=", "portal.request")],
    )

    # Child requests
    parent_request_id = fields.Many2one("portal.request", string="Parent Request")
    child_request_ids = fields.One2many(
        "portal.request", "parent_request_id", string="Child Requests"
    )

    # Mail framework fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends("child_request_ids")
    def _compute_child_request_count(self):
        for record in self:
            record.child_request_count = len(record.child_request_ids)

    @api.depends("attachment_ids")
    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    @api.depends("state", "deadline")
    def _compute_is_overdue(self):
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = (
                record.deadline
                and record.deadline < now
                and record.state not in ["completed", "cancelled"]
            )

    @api.depends("actual_hours", "estimated_hours")
    def _compute_time_variance(self):
        for record in self:
            if record.estimated_hours:
                record.time_variance = (
                    (record.actual_hours - record.estimated_hours)
                    / record.estimated_hours
                ) * 100
            else:
                record.time_variance = 0.0

    child_request_count = fields.Integer(
        compute="_compute_child_request_count", string="Child Request Count"
    )
    attachment_count = fields.Integer(
        compute="_compute_attachment_count", string="Request Attachments"
    )
    is_overdue = fields.Boolean(compute="_compute_is_overdue", string="Overdue")
    time_variance = fields.Float(
        compute="_compute_time_variance", string="Time Variance (%)"
    )

    # ============================================================================
    # DEFAULT & SEQUENCE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("portal.request") or "REQ/"
                )
        return super().create(vals_list)

    def _get_default_values(self):
        return {
            "state": "draft",
            "priority": "1",
            "request_type": "other",
            "active": True,
        }

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self._check_required_fields()
        self.write({"state": "submitted", "requested_date": fields.Datetime.now()})
        self._send_submission_notification()

    def action_review(self):
        self.ensure_one()
        if self.state != "submitted":
            raise UserError(_("Only submitted requests can be reviewed."))
        self.write({"state": "under_review"})

    def action_approve(self):
        self.ensure_one()
        self.write(
            {
                "state": "approved",
                "approved_by": self.env.user.id,
                "approval_date": fields.Datetime.now(),
            }
        )
        self._create_work_order()
        self._send_approval_notification()

    def action_reject(self):
        self.ensure_one()
        self.write({"state": "rejected"})
        self._send_rejection_notification()

    def action_start_progress(self):
        self.ensure_one()
        if self.state != "approved":
            raise UserError(_("Only approved requests can be started."))
        self.write({"state": "in_progress"})

    def action_complete(self):
        self.ensure_one()
        self.write({"state": "completed", "completion_date": fields.Datetime.now()})
        self._finalize_billing()
        self._send_completion_notification()

    def action_cancel(self):
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Completed requests cannot be cancelled."))
        self.write({"state": "cancelled"})

    def action_duplicate(self):
        self.ensure_one()
        return self.copy({"name": False, "state": "draft"})

    def action_view_attachments(self):
        return {
            "type": "ir.actions.act_window",
            "name": "Attachments",
            "res_model": "ir.attachment",
            "view_mode": "tree,form",
            "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
            "context": {"default_res_model": self._name, "default_res_id": self.id},
        }

    # ============================================================================
    # NOTIFICATION METHODS
    # ============================================================================
    def _send_submission_notification(self):
        template = self.env.ref(
            "records_management.email_template_portal_request_submitted",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_approval_notification(self):
        template = self.env.ref(
            "records_management.email_template_portal_request_approved",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_rejection_notification(self):
        template = self.env.ref(
            "records_management.email_template_portal_request_rejected",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    def _send_completion_notification(self):
        template = self.env.ref(
            "records_management.email_template_portal_request_completed",
            raise_if_not_found=False,
        )
        if template:
            template.send_mail(self.id, force_send=True)

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def _check_required_fields(self):
        required_fields = ["partner_id", "request_type"]
        for field in required_fields:
            if not getattr(self, field):
                raise UserError(
                    _("Field '%s' is required before submission.")
                    % self._fields[field].string
                )

    def _create_work_order(self):
        if self.request_type in ["destruction", "retrieval", "shredding"]:
            work_order = self.env["document.retrieval.work.order"].create(
                {
                    "name": f"WO-{self.name}",
                    "partner_id": self.partner_id.id,
                    "request_type": self.request_type,
                    "portal_request_id": self.id,
                    "estimated_hours": self.estimated_hours,
                }
            )
            self.work_order_id = work_order.id

    def _finalize_billing(self):
        if self.billing_status == "to_bill" and self.actual_cost > 0:
            self.billing_status = "billed"

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (from comprehensive validation)
    # ============================================================================
    def action_start_processing(self):
        """Start Processing - State management action"""
        self.ensure_one()
        # TODO: Implement action_start_processing business logic
        self.message_post(body=_("Start Processing action executed"))
        return True

    def action_view_related_documents(self):
        """View Related Documents - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Related Documents"),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.ids)],
            "context": self.env.context,
        }

    def action_assign(self):
        """Assign - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Assign"),
            "res_model": "portal.request",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    def action_escalate(self):
        """Escalate - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Escalate"),
            "res_model": "portal.request",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("deadline", "requested_date")
    def _check_dates(self):
        for record in self:
            if (
                record.deadline
                and record.requested_date
                and record.deadline < record.requested_date
            ):
                raise ValidationError(
                    _("Deadline cannot be before the requested date.")
                )

    @api.constrains("estimated_cost", "actual_cost")
    def _check_costs(self):
        for record in self:
            if record.estimated_cost < 0 or record.actual_cost < 0:
                raise ValidationError(_("Costs cannot be negative."))

    @api.constrains("estimated_hours", "actual_hours")
    def _check_hours(self):
        for record in self:
            if record.estimated_hours < 0 or record.actual_hours < 0:
                raise ValidationError(_("Hours cannot be negative."))
