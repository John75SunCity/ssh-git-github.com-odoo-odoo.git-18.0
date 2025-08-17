from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Portal Customer Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Request #', required=True, tracking=True)
    reference = fields.Char(string='Reference')
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active')
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    state = fields.Selection()
    approval_status = fields.Selection()
    activity_state = fields.Selection()
    message_count = fields.Integer()
    request_type = fields.Selection()
    priority = fields.Selection()
    urgency_reason = fields.Text(string='Urgency Reason')
    internal_notes = fields.Text(string='Internal Notes')
    public_notes = fields.Text(string='Public Notes')
    partner_id = fields.Many2one()
    contact_person = fields.Char(string='Contact Person')
    contact_email = fields.Char(string='Contact Email')
    contact_phone = fields.Char(string='Contact Phone')
    notification_email = fields.Char(string='Notification Email')
    assigned_to = fields.Char(string='Assigned To')
    requested_date = fields.Datetime(string='Requested Date')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    deadline = fields.Datetime(string='Deadline')
    completion_date = fields.Datetime(string='Completion Date')
    actual_completion = fields.Datetime()
    due_date = fields.Date(string='Due Date')
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')
    completion_notes = fields.Text()
    customer_contact_info = fields.Text()
    chain_of_custody_id = fields.Many2one()
    currency_id = fields.Many2one()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary()
    billing_status = fields.Selection()
    document_count = fields.Integer(string='Document Count')
    box_count = fields.Integer(string='Box Count')
    weight_estimate = fields.Float(string='Weight Estimate (lbs)')
    service_location = fields.Char(string='Service Location')
    access_instructions = fields.Text(string='Access Instructions')
    special_requirements = fields.Text(string='Special Requirements')
    approval_required = fields.Boolean(string='Approval Required')
    approved_by_id = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    rejection_reason = fields.Text(string='Rejection Reason')
    signature_required = fields.Boolean(string='Signature Required')
    customer_signature = fields.Binary(string='Customer Signature')
    customer_signature_date = fields.Datetime(string='Customer Signature Date')
    technician_signature = fields.Binary(string='Technician Signature')
    technician_signature_date = fields.Datetime(string='Technician Signature Date')
    signed_document = fields.Binary(string='Signed Document')
    requires_naid_compliance = fields.Boolean()
    compliance_notes = fields.Text(string='Compliance Notes')
    audit_trail = fields.Text(string='Audit Trail')
    certificate_of_destruction = fields.Binary(string='Certificate of Destruction')
    service_item_id = fields.Many2one('service.item')
    shredding_service_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    work_order_id = fields.Many2one()
    parent_request_id = fields.Many2one('portal.request')
    child_request_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    child_request_count = fields.Integer()
    attachment_count = fields.Integer()
    attachment_ids = fields.Many2many()
    is_overdue = fields.Boolean()
    time_variance = fields.Float()
    estimated_completion = fields.Datetime(string='Estimated Completion')
    processing_notes = fields.Text(string='Processing Notes')
    special_instructions = fields.Text(string='Special Instructions')
    requires_approval = fields.Boolean(string='Requires Approval')
    urgency_level = fields.Selection(string='Urgency')
    customer_feedback = fields.Text(string='Customer Feedback')
    related_tasks_count = fields.Integer(string='Related Tasks')
    staff_signature = fields.Binary(string='Staff Signature')
    naid_audit_required = fields.Boolean(string='NAID Audit Required')
    action_approve = fields.Char(string='Action Approve')
    action_reject = fields.Char(string='Action Reject')
    action_reset_to_draft = fields.Char(string='Action Reset To Draft')
    action_submit = fields.Char(string='Action Submit')
    action_view_related_documents = fields.Char(string='Action View Related Documents')
    approved = fields.Boolean(string='Approved')
    button_box = fields.Char(string='Button Box')
    context = fields.Char(string='Context')
    customer = fields.Char(string='Customer')
    domain = fields.Char(string='Domain')
    draft = fields.Char(string='Draft')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    my_requests = fields.Char(string='My Requests')
    overdue = fields.Char(string='Overdue')
    rejected = fields.Char(string='Rejected')
    request_date = fields.Date(string='Request Date')
    res_model = fields.Char(string='Res Model')
    submitted = fields.Char(string='Submitted')
    user = fields.Char(string='User')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_related_tasks_count(self):
            """Compute Related Tasks Count"""
            for record in self:
                # TODO: Implement business logic for related_tasks_count:
                record.related_tasks_count = 0  # Default value


    def _compute_attachment_count(self):
            """Compute the number of attachments for this portal request.""":
            for record in self:
                if record.id:
                    record.attachment_count = self.env["ir.attachment").search_count(]
                        [("res_model", "=", self._name), ("res_id", "=", record.id)]

                else:
                    record.attachment_count = 0


    def _compute_activity_state(self):
            """Compute activity state for mail thread compatibility""":
            for record in self:
                if not record.activity_ids:
                    record.activity_state = False
                    continue

                # Get the closest activity

    def _compute_message_count(self):
            """Compute message count for mail thread compatibility""":
            for record in self:
                record.message_count = len(record.message_ids)


    def _compute_is_overdue(self):
            """Compute whether the portal request is overdue based on due date and current state."""
            for record in self:
                if record.due_date and record.state not in ("completed", "cancelled"):

    def _compute_time_variance(self):
            """Compute time variance percentage between estimated and actual hours."""
            for record in self:
                if (:)
                    record.estimated_hours
                    and record.actual_hours
                    and record.estimated_hours > 0

                    record.time_variance = ()
                        (record.actual_hours - record.estimated_hours)
                        / record.estimated_hours

                else:
                    record.time_variance = 0.0


    def _compute_child_request_count(self):
            """Compute the number of child requests."""
            for record in self:
                record.child_request_count = len(record.child_request_ids)


    def _compute_attachment_ids(self):
            """Compute attachment IDs for this portal request.""":
            for record in self:
                if record.id:
                    record.attachment_ids = ()
                        self.env["ir.attachment"]
                        .search()
                            [("res_model", "=", self._name), ("res_id", "=", record.id)]

                        .ids

                else:
                    record.attachment_ids = []

        # ============================================================================
            # DEFAULT & SEQUENCE METHODS
        # ============================================================================

    def create(self, vals_list):
            for vals in vals_list:
                if not vals.get("name"):
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("portal.request") or "REQ/"

            return super(PortalRequest, self).create(vals_list)


    def _default_portal_request_values(self):
            """Return default values for portal request creation.""":
            return {}
                "state": "draft",
                "priority": "1",
                "request_type": "other",
                "active": True,


        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_submit(self):
            """Submit the portal request for processing.""":
            self.ensure_one()
            self._check_required_fields()
            self.write({"state": "submitted", "requested_date": fields.Datetime.now()})
            self._send_submission_notification()


    def action_review(self):
            """Set the portal request to under review state."""

            self.ensure_one()
            if self.state != "submitted":
                raise UserError(_("Only submitted requests can be reviewed."))
            self.write({"state": "under_review"})


    def action_approve(self):
            """Approve the portal request and create associated work order."""

            self.ensure_one()
            self.write()
                {}
                    "state": "approved",
                    "approved_by_id": self.env.user.id,
                    "approval_date": fields.Datetime.now(),


            self._create_work_order()
            self._send_approval_notification()


    def action_reject(self):
            """Reject the portal request."""

            self.ensure_one()
            self.write({"state": "rejected"})
            self._send_rejection_notification()


    def action_start_progress(self):
            """Start processing the approved portal request."""

            self.ensure_one()
            if self.state != "approved":
                raise UserError(_("Only approved requests can be started."))
            self.write({"state": "in_progress"})


    def action_complete(self):
            """Complete the portal request and finalize billing."""

            self.ensure_one()
            self.write({"state": "completed", "completion_date": fields.Datetime.now()})
            self._finalize_billing()
            self._send_completion_notification()


    def action_cancel(self):
            """Cancel the portal request if not already completed.""":
            self.ensure_one()
            if self.state in ["completed"]:
                raise UserError(_("Completed requests cannot be cancelled."))
            self.write({"state": "cancelled"})


    def action_duplicate(self):
            """Create a duplicate of the portal request in draft state."""

            self.ensure_one()
            return self.copy({"name": False, "state": "draft"})


    def action_view_attachments(self):
            """Open the attachments view for this portal request.""":
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": "Attachments",
                "res_model": "ir.attachment",
                "view_mode": "tree,form",
                "domain": [("res_model", "=", self._name), ("res_id", "=", self.id)],
                "context": {"default_res_model": self._name, "default_res_id": self.id},



    def action_start_processing(self):
            """Start Processing - State management action"""

            self.ensure_one()

            # Validate current state allows processing to start
            if self.state not in ["submitted", "under_review", "approved"]:
                state_name = dict(self._fields["state"].selection).get(self.state)
                raise UserError()
                    _()
                        "Cannot start processing. Request must be in 'Submitted', "
                        "'Under Review', or 'Approved' state. Current state: %s",
                        state_name,


            # Validate required fields for processing:
            if not self.partner_id:
                raise UserError(_("Customer is required to start processing."))
            if not self.request_type:
                raise UserError(_("Request type is required to start processing."))

            # Update state to in_progress
            self.write()
                {}
                    "state": "in_progress",
                    "user_id": self.env.user.id,  # Assign current user as processor



            # Create activity for tracking:
            request_type_name = dict(self._fields["request_type").selection).get(]
                self.request_type

            self.activity_schedule()
                "mail.mail_activity_data_todo",
                summary=_("Process Request: %s", self.name),
                note=_("Request processing has started. Type: %s", request_type_name),
                user_id=self.user_id.id,

            # Post message to chatter
            self.message_post()
                body=_("Processing started by %s", self.env.user.name),
                message_type="notification",

            # Auto-create work order if needed:
            if (:)
                self.request_type in ["destruction", "retrieval", "shredding"]
                and not self.work_order_id

                self._create_work_order()

            return True


    def action_escalate(self):
            """Escalate - Action method"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Escalate"),
                "res_model": "portal.request",
                "view_mode": "form",
                "target": "new",
                "context": self.env.context,


        # ============================================================================
            # NOTIFICATION METHODS
        # ============================================================================

    def _send_submission_notification(self):
            """Send email notification when request is submitted."""
            template = self.env.ref()
                "records_management.email_template_portal_request_submitted",
                raise_if_not_found=False,
            if template:
                template.send_mail(self.id, force_send=True)


    def _send_approval_notification(self):
            """Send email notification when request is approved."""
            template = self.env.ref()
                "records_management.email_template_portal_request_approved",
                raise_if_not_found=False,
            if template:
                template.send_mail(self.id, force_send=True)


    def _send_rejection_notification(self):
            """Send email notification when request is rejected."""
            template = self.env.ref()
                "records_management.email_template_portal_request_rejected",
                raise_if_not_found=False,
            if template:
                template.send_mail(self.id, force_send=True)


    def _send_completion_notification(self):
            """Send email notification when request is completed."""
            template = self.env.ref()
                "records_management.email_template_portal_request_completed",
                raise_if_not_found=False,
            if template:
                template.send_mail(self.id, force_send=True)

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def _check_required_fields(self):
            """Validate that required fields are populated before submission."""
            required_fields = ["partner_id", "request_type"]
            for field in required_fields:
                if not getattr(self, field):
                    field_name = self._fields[field].string
                    raise UserError()
                        _("Field '%s' is required before submission.", field_name)



    def _create_work_order(self):
            """Create a work order for service-type requests.""":
            if self.request_type in ["destruction", "retrieval", "shredding"]:
                work_order_name = "WO-%s" % self.name
                work_order = self.env["file.retrieval.work.order").create(]
                    {}
                        "name": work_order_name,
                        "partner_id": self.partner_id.id,
                        "request_type": self.request_type,
                        "portal_request_id": self.id,
                        "estimated_hours": self.estimated_hours,


                self.work_order_id = work_order.id


    def _finalize_billing(self):
            """Finalize billing status when request is completed."""
            if self.billing_status == "to_bill" and self.actual_cost > 0:
                self.billing_status = "billed"

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def _onchange_partner_id(self):
            """Update contact fields when partner changes"""
            if self.partner_id:
                self.contact_email = self.partner_id.email
                self.contact_phone = self.partner_id.phone
                if self.partner_id.child_ids:
                    # Get primary contact if available:
                    primary_contact = self.partner_id.child_ids.filtered()
                        lambda c: not c.is_company

                    if primary_contact:
                        self.contact_person = primary_contact.name
                        self.contact_email = primary_contact.email or self.partner_id.email
                        self.contact_phone = primary_contact.phone or self.partner_id.phone


    def _onchange_request_type(self):
            """Set default values based on request type"""
            if self.request_type == "destruction":
                self.requires_naid_compliance = True
                self.signature_required = True
            elif self.request_type in ["retrieval", "pickup"]:
                self.signature_required = True

            # Set default priority based on request type
            priority_mapping = {}
                "destruction": "2",  # High
                "audit": "3",  # Urgent
                "consultation": "0",  # Low
                "other": "1",  # Normal

            self.priority = priority_mapping.get(self.request_type, "1")


    def _onchange_priority(self):
            """Require urgency reason for high priority requests""":
            if self.priority in ["2", "3"] and not self.urgency_reason:
                return {}
                    "warning": {}
                        "title": _("High Priority Request"),
                        "message": _()
                            "Please provide an urgency reason for high priority requests.":





    def _get_mail_template_by_state(self):
            """Get appropriate email template based on current state"""
            template_mapping = {}
                "submitted": "records_management.email_template_portal_request_submitted",
                "approved": "records_management.email_template_portal_request_approved",
                "rejected": "records_management.email_template_portal_request_rejected",
                "completed": "records_management.email_template_portal_request_completed",

            template_ref = template_mapping.get(self.state)
            if template_ref:
                return self.env.ref(template_ref, raise_if_not_found=False)
            return False


    def _auto_assign_user(self):
            """Auto-assign user based on request type and workload"""
            if self.user_id:
                return  # Already assigned

            # Define user assignment rules by request type
            assignment_rules = {}
                "destruction": "records_management.group_records_manager",
                "audit": "records_management.group_compliance_officer",
                "retrieval": "records_management.group_records_user",
                "pickup": "records_management.group_field_technician",
                "shredding": "records_management.group_shredding_technician",


            group_ref = assignment_rules.get(self.request_type)
            if group_ref:
                group = self.env.ref(group_ref, raise_if_not_found=False)
                if group and group.users:
                    # Assign to user with least active requests
                    users = group.users
                    workload = {}
                    for user in users:
                        active_requests = self.search_count()
                            []
                                ("user_id", "=", user.id),
                                ()
                                    "state",
                                    "in",
                                    []
                                        "submitted",
                                        "under_review",
                                        "approved",
                                        "in_progress",

                        workload[user.id] = active_requests

                    # Find user with minimum workload
                    min_workload_user_id = min(workload.keys(), key=lambda k: workload[k])
                    self.user_id = min_workload_user_id


    def _check_overdue_requests(self):
            """Cron job to check and escalate overdue requests"""
            overdue_requests = self.search()
                []
                    ("deadline", "<", fields.Datetime.now()),
                    ()
                        "state",
                        "in",
                        ["submitted", "under_review", "approved", "in_progress"],
                    ("is_overdue", "=", False),  # Not already marked as overdue



            for request in overdue_requests:
                # Create escalation activity
                request.activity_schedule()
                    "mail.mail_activity_data_call",
                    summary=_("Overdue Request: %s", request.name),
                    note=_("This request is overdue. Deadline was: %s", request.deadline),
                    user_id=request.user_id.id or self.env.user.id,
                    date_deadline=fields.Date.today(),

                # Send escalation notification
                if request.partner_id and request.partner_id.email:
                    template = self.env.ref()
                        "records_management.email_template_portal_request_overdue",
                        raise_if_not_found=False,
                    if template:
                        template.send_mail(request.id, force_send=True)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_deadline_dates(self):
            """Validate that deadline is not before requested date."""
            for record in self:
                if (:)
                    record.deadline
                    and record.requested_date
                    and record.deadline < record.requested_date

                    raise ValidationError()
                        _("Deadline cannot be before the requested date.")



    def _check_cost_values(self):
            """Validate that costs are not negative."""
            for record in self:
                if record.estimated_cost < 0 or record.actual_cost < 0:
                    raise ValidationError(_("Costs cannot be negative."))


    def _check_hour_values(self):
            """Validate that hours are not negative."""
            for record in self:
                if record.estimated_hours < 0 or record.actual_hours < 0:
                    raise ValidationError(_("Hours cannot be negative."))

