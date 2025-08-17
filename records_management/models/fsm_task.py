from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class FsmTask(models.Model):
    _name = 'fsm.task.service.line'
    _description = 'FSM Task Service Line Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'task_id, sequence'
    _rec_name = 'service_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    description = fields.Text(string='Description')
    task_type = fields.Selection()
    priority = fields.Selection()
    status = fields.Selection()
    scheduled_date = fields.Datetime()
    start_date = fields.Datetime(string='Start Date')
    end_date = fields.Datetime(string='End Date')
    deadline = fields.Date(string='Deadline')
    assigned_technician_id = fields.Many2one('res.users', string='Assigned Technician')
    team_name = fields.Char(string='Service Team')
    customer_id = fields.Many2one()
    customer_location_id = fields.Many2one()
    customer_contact_id = fields.Many2one()
    work_order_coordinator_id = fields.Many2one()
    service_type = fields.Selection()
    confidentiality_level = fields.Selection()
    completion_percentage = fields.Float()
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')
    customer_satisfaction = fields.Selection()
    quality_rating = fields.Selection()
    currency_id = fields.Many2one()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary(string='Actual Cost')
    invoice_status = fields.Selection()
    internal_notes = fields.Text(string='Internal Notes')
    customer_notes = fields.Text(string='Customer Notes')
    completion_notes = fields.Text(string='Completion Notes')
    special_instructions = fields.Text(string='Special Instructions')
    duration_hours = fields.Float()
    is_overdue = fields.Boolean(string='Is Overdue')
    progress_status = fields.Char()
    related_project_task_id = fields.Many2one()
    equipment_ids = fields.Many2many('maintenance.equipment')
    service_line_ids = fields.One2many()
    allow_on_site_additions = fields.Boolean()
    requires_customer_approval = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    container_ids = fields.Many2many('records.container')
    total_cubic_feet = fields.Float(string='Total Cubic Feet')
    total_weight = fields.Float(string='Total Weight (lbs)')
    naid_compliant = fields.Boolean(string='NAID Compliant')
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required')
    destruction_certificate_required = fields.Boolean(string='Destruction Certificate Required')
    customer_signature = fields.Binary(string='Customer Signature')
    technician_signature = fields.Binary(string='Technician Signature')
    compliance_verified = fields.Boolean(string='Compliance Verified')
    partner_id = fields.Many2one('res.partner', string='Customer')
    location_id = fields.Many2one('records.location', string='Task Location')
    container_count = fields.Integer(string='Container Count')
    container_type = fields.Selection(string='Container Type')
    access_instructions = fields.Text(string='Access Instructions')
    actual_start_time = fields.Datetime(string='Actual Start Time')
    actual_end_time = fields.Datetime(string='Actual End Time')
    assigned_date = fields.Date(string='Assigned Date')
    assigned_technician = fields.Many2one('hr.employee', string='Assigned Technician')
    completion_date = fields.Datetime(string='Completion Date')
    estimated_duration = fields.Float(string='Estimated Duration (Hours)')
    event_description = fields.Text(string='Event Description')
    event_timestamp = fields.Datetime(string='Event Timestamp')
    event_type = fields.Selection(string='Event Type')
    follow_up_required = fields.Boolean(string='Follow-up Required')
    location_address = fields.Text(string='Location Address')
    naid_audit_log_ids = fields.One2many('naid.audit.log')
    photos = fields.Many2many('ir.attachment', string='Photos')
    required_skills = fields.Text(string='Required Skills')
    required_tools = fields.Text(string='Required Tools')
    service_location = fields.Char(string='Service Location')
    special_requirements = fields.Text(string='Special Requirements')
    task_status = fields.Selection(string='Task Status')
    volume_cf = fields.Float(string='Volume (CF)')
    weight_lbs = fields.Float(string='Weight (lbs)')
    work_order_count = fields.Integer(string='Work Orders Count')
    work_order_ids = fields.One2many('file.retrieval.work.order')
    work_order_type = fields.Selection()
    action_complete_service = fields.Char(string='Action Complete Service')
    action_start_service = fields.Char(string='Action Start Service')
    action_verify_service = fields.Char(string='Action Verify Service')
    context = fields.Char(string='Context')
    filter_completed = fields.Boolean(string='Filter Completed')
    filter_in_progress = fields.Char(string='Filter In Progress')
    filter_today = fields.Char(string='Filter Today')
    group_employee = fields.Char(string='Group Employee')
    group_service_type = fields.Selection(string='Group Service Type')
    group_status = fields.Selection(string='Group Status')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')
    action_complete_task = fields.Char(string='Action Complete Task')
    action_create_naid_audit = fields.Char(string='Action Create Naid Audit')
    action_reschedule = fields.Char(string='Action Reschedule')
    action_start_task = fields.Char(string='Action Start Task')
    action_view_containers = fields.Char(string='Action View Containers')
    action_view_work_orders = fields.Char(string='Action View Work Orders')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    completed = fields.Boolean(string='Completed')
    context = fields.Char(string='Context')
    custody_required = fields.Boolean(string='Custody Required')
    customer_satisfaction_rating = fields.Char(string='Customer Satisfaction Rating')
    group_customer = fields.Char(string='Group Customer')
    group_date = fields.Date(string='Group Date')
    group_priority = fields.Selection(string='Group Priority')
    group_status = fields.Selection(string='Group Status')
    group_technician = fields.Char(string='Group Technician')
    group_type = fields.Selection(string='Group Type')
    has_containers = fields.Char(string='Has Containers')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    in_progress = fields.Char(string='In Progress')
    medium_priority = fields.Selection(string='Medium Priority')
    my_tasks = fields.Char(string='My Tasks')
    overdue = fields.Char(string='Overdue')
    res_model = fields.Char(string='Res Model')
    scheduled = fields.Char(string='Scheduled')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    task_id = fields.Many2one()
    sequence = fields.Integer(string='Sequence')
    service_name = fields.Char(string='Service Name')
    service_type = fields.Selection()
    description = fields.Text(string='Service Description')
    added_on_site = fields.Boolean(string='Added On-Site')
    added_by_id = fields.Many2one('res.users')
    added_date = fields.Datetime(string='Added Date')
    customer_approved = fields.Boolean(string='Customer Approved')
    approval_method = fields.Selection()
    currency_id = fields.Many2one()
    unit_price = fields.Monetary(string='Unit Price')
    quantity = fields.Float(string='Quantity')
    total_price = fields.Monetary()
    state = fields.Selection()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_duration(self):
            """Calculate task duration in hours"""
            for record in self:
                if record.start_date and record.end_date:
                    delta = record.end_date - record.start_date
                    record.duration_hours = delta.total_seconds() / 3600.0
                else:
                    record.duration_hours = 0.0


    def _compute_overdue(self):
            """Check if task is overdue""":

    def _compute_progress_status(self):
            """Generate readable progress status"""
            for record in self:
                if record.status == "completed":
                    record.progress_status = _("Completed")
                elif record.status == "cancelled":
                    record.progress_status = _("Cancelled")
                else:
                    record.progress_status = _("%s%% Complete", f"{record.completion_percentage:.0f}")

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_start_task(self):
            """Start the task"""

            self.ensure_one()
            if self.status != "scheduled":
                raise UserError(_("Only scheduled tasks can be started"))
            self.write({"status": "in_progress", "start_date": fields.Datetime.now()})
            self.message_post(body=_("Task started"))


    def action_complete_task(self):
            """Complete the task"""

            self.ensure_one()
            if self.status != "in_progress":
                raise UserError(_("Only in-progress tasks can be completed"))
            self.write()
                {}
                    "status": "completed",
                    "end_date": fields.Datetime.now(),
                    "completion_percentage": 100.0,


            self.message_post(body=_("Task completed"))


    def action_cancel_task(self):
            """Cancel the task"""

            self.ensure_one()
            if self.status == "completed":
                raise UserError(_("Cannot cancel completed tasks"))
            self.write({"status": "cancelled"})
            self.message_post(body=_("Task cancelled"))


    def action_reschedule_task(self):
            """Open reschedule wizard"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Reschedule Task"),
                "res_model": "fsm.reschedule.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_task_id": self.id},



    def action_view_work_orders(self):
            """View related work orders"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Work Orders"),
                "res_model": "fsm.work.order",
                "view_mode": "tree,form",
                "domain": [("task_id", "=", self.id)],
                "context": {"default_task_id": self.id},



    def action_add_service_on_site(self):
            """Add service while technician is on-site""":
            self.ensure_one()
            if self.status not in ["scheduled", "in_progress"]:
                raise UserError()
                    _("Can only add services to scheduled or in-progress tasks")


            return {}
                "type": "ir.actions.act_window",
                "name": _("Add Service On-Site"),
                "res_model": "fsm.add.service.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_task_id": self.id,
                    "default_customer_id": self.customer_id.id,
                    "on_site_addition": True,




    def action_modify_service_scope(self):
            """Modify service scope during task execution"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Modify Service Scope"),
                "res_model": "fsm.task.service.line",
                "view_mode": "tree,form",
                "domain": [("task_id", "=", self.id)],
                "context": {"default_task_id": self.id},



    def action_customer_approval_required(self):
            """Request customer approval for additional services""":
            self.ensure_one()
            # Send notification/email to customer for approval:
            template = self.env.ref()
                "records_management.email_template_service_approval", False

            if template:
                template.send_mail(self.id)
            self.message_post(body=_("Customer approval requested for additional services")):

    def _calculate_total_service_cost(self):
            """Calculate total cost including dynamically added services"""
            self.ensure_one()
            base_cost = self.estimated_cost or 0.0
            additional_cost = sum(self.service_line_ids.mapped("total_price"))
            return base_cost + additional_cost

        # ============================================================================
            # OVERRIDE METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create for automatic task numbering""":
            for vals in vals_list:
                if vals.get("name", _("New")) == _("New"):
                    vals["name"] = self.env["ir.sequence").next_by_code("fsm.task") or _(]
                        "New"

            return super().create(vals_list)


    def write(self, vals):
            """Override write for status change tracking""":
            if "status" in vals:
                for record in self:
                    old_status = record.status
                    new_status = vals["status"]
                    if old_status != new_status:
                        record.message_post()
                            body=_("Status changed from %s to %s", old_status, new_status)

            return super().write(vals)


    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = record.name or _("New")
                if record.customer_id:
                    name += _(" - %s", record.customer_id.name)
                if record.task_type:
                    task_type_dict = dict(record._fields["task_type"].selection)
                    name += _(" (%s)", task_type_dict.get(record.task_type))
                result.append((record.id, name))
            return result


    def _search_name():
            self, name="", args=None, operator="ilike", limit=100, name_get_uid=None

            """Enhanced search by name, customer, or task type"""
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    "|",
                    ("name", operator, name),
                    ("customer_id.name", operator, name),
                    ("task_type", operator, name),
                    ("description", operator, name),

            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_dates(self):
            """Validate date consistency"""
            for record in self:
                if record.start_date and record.end_date:
                    if record.start_date > record.end_date:
                        raise ValidationError(_("Start date cannot be after end date"))


    def _check_completion_percentage(self):
            """Validate completion percentage"""
            for record in self:
                if not (0 <= record.completion_percentage <= 100):
                    raise ValidationError()
                        _("Completion percentage must be between 0 and 100")



    def _check_hours(self):
            """Validate hour values"""
            for record in self:
                if record.estimated_hours and record.estimated_hours < 0:
                    raise ValidationError(_("Estimated hours cannot be negative"))
                if record.actual_hours and record.actual_hours < 0:
                    raise ValidationError(_("Actual hours cannot be negative"))


    def _check_schedule(self):
            """Validate schedule consistency"""
            for record in self:
                if record.scheduled_date and record.deadline:
                    if record.scheduled_date.date() > record.deadline:
                        raise ValidationError(_("Scheduled date cannot be after deadline"))


    def _compute_total_price(self):
            """Calculate total price for service line""":
            for line in self:
                line.total_price = line.unit_price * line.quantity

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_request_approval(self):
            """Request customer approval for this service addition""":
            self.ensure_one()
            if self.customer_approved:
                raise UserError(_("Service already approved"))

            # Logic to send approval request
            self.write({"status": "pending"})
            self.task_id.message_post()
                body=_("Approval requested for additional service: %s", self.service_name)



    def action_approve_service(self):
            """Approve the additional service"""

            self.ensure_one()
            self.write({"status": "approved", "customer_approved": True})
            self.task_id.message_post()
                body=_("Additional service approved: %s", self.service_name)


