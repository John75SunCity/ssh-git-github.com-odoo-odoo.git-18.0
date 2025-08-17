from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError


class WorkOrderCoordinator(models.Model):
    _name = 'work.order.integration.mixin'
    _description = 'Work Order Integration Capabilities'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    partner_id = fields.Many2one()
    container_retrieval_ids = fields.One2many()
    file_retrieval_ids = fields.One2many()
    scan_retrieval_ids = fields.One2many()
    destruction_ids = fields.One2many()
    access_ids = fields.One2many()
    total_work_orders = fields.Integer()
    completed_work_orders = fields.Integer()
    coordination_progress = fields.Float()
    scheduled_date = fields.Datetime()
    priority = fields.Selection()
    coordination_type = fields.Selection()
    vehicle_ids = fields.Many2many()
    employee_ids = fields.Many2many()
    fsm_project_id = fields.Many2one()
    fsm_task_ids = fields.One2many()
    portal_request_id = fields.Many2one()
    customer_visible = fields.Boolean()
    consolidated_billing = fields.Boolean()
    invoice_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    active_work_orders = fields.Integer(string='Active Work Orders')
    assigned_equipment_ids = fields.Many2many('maintenance.equipment')
    average_completion_time = fields.Float(string='Avg Completion Time (Hours)')
    certification_count = fields.Integer(string='Certifications Count')
    certification_ids = fields.One2many('hr.employee.certification')
    current_work_order_ids = fields.One2many('file.retrieval.work.order')
    department_id = fields.Many2one('records.department')
    email = fields.Char(string='Email')
    emergency_contact = fields.Char(string='Emergency Contact')
    emergency_phone = fields.Char(string='Emergency Phone')
    employee_id = fields.Many2one('hr.employee')
    equipment_authorizations = fields.Text(string='Equipment Authorizations')
    is_active = fields.Boolean(string='Currently Active')
    last_login = fields.Datetime(string='Last Login')
    last_maintenance_date = fields.Date(string='Last Maintenance Training')
    last_performance_review = fields.Date(string='Last Performance Review')
    mobile = fields.Char(string='Mobile Phone')
    next_maintenance_due = fields.Date(string='Next Maintenance Due')
    next_training_date = fields.Date(string='Next Training Date')
    on_time_completion_rate = fields.Float(string='On-Time Completion Rate (%)')
    overtime_approved = fields.Boolean(string='Overtime Approved')
    pending_assignments = fields.Integer(string='Pending Assignments')
    phone = fields.Char(string='Work Phone')
    safety_incidents = fields.Integer(string='Safety Incidents')
    time_zone = fields.Selection(string='Time Zone')
    tool_certifications = fields.Text(string='Tool Certifications')
    total_hours_logged = fields.Float(string='Total Hours Logged')
    training_completed = fields.Date(string='Initial Training Completed')
    vehicle_access = fields.Boolean(string='Vehicle Access')
    weekend_availability = fields.Boolean(string='Weekend Availability')
    work_order_type = fields.Selection(string='Specialization')
    work_schedule = fields.Selection(string='Work Schedule')
    coordinator_type = fields.Selection(string='Coordinator Type')
    certification_type = fields.Selection(string='Certification Type')
    skill_level = fields.Selection(string='Skill Level')
    specialization = fields.Selection(string='Specialization')
    naid_certified = fields.Boolean(string='NAID Certified')
    background_check_date = fields.Date(string='Background Check Date')
    safety_training_date = fields.Date(string='Safety Training Date')
    productivity_score = fields.Float(string='Productivity Score')
    quality_score = fields.Float(string='Quality Score')
    customer_satisfaction = fields.Float(string='Customer Satisfaction')
    years_experience = fields.Integer(string='Years Experience')
    action_set_available = fields.Char(string='Action Set Available')
    action_set_busy = fields.Char(string='Action Set Busy')
    action_set_unavailable = fields.Char(string='Action Set Unavailable')
    action_view_certifications = fields.Char(string='Action View Certifications')
    action_view_completed_orders = fields.Char(string='Action View Completed Orders')
    action_view_work_orders = fields.Char(string='Action View Work Orders')
    active = fields.Boolean(string='Active')
    archived = fields.Char(string='Archived')
    audit_info = fields.Char(string='Audit Info')
    audit_tracking = fields.Char(string='Audit Tracking')
    availability = fields.Char(string='Availability')
    available = fields.Char(string='Available')
    busy = fields.Char(string='Busy')
    button_box = fields.Char(string='Button Box')
    certified = fields.Char(string='Certified')
    contact_info = fields.Char(string='Contact Info')
    context = fields.Char(string='Context')
    coordinator_info = fields.Char(string='Coordinator Info')
    create_date = fields.Date(string='Create Date')
    domain = fields.Char(string='Domain')
    equipment_access = fields.Char(string='Equipment Access')
    equipment_tools = fields.Char(string='Equipment Tools')
    equipment_type = fields.Selection(string='Equipment Type')
    expiry_date = fields.Date(string='Expiry Date')
    group_company = fields.Char(string='Group Company')
    group_department = fields.Char(string='Group Department')
    group_priority = fields.Selection(string='Group Priority')
    group_specialization = fields.Char(string='Group Specialization')
    group_state = fields.Selection(string='Group State')
    group_type = fields.Selection(string='Group Type')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    id = fields.Char(string='Id')
    issue_date = fields.Date(string='Issue Date')
    performance_metrics = fields.Char(string='Performance Metrics')
    res_model = fields.Char(string='Res Model')
    safety = fields.Char(string='Safety')
    serial_number = fields.Char(string='Serial Number')
    skills = fields.Char(string='Skills')
    skills_certifications = fields.Char(string='Skills Certifications')
    state = fields.Selection(string='State', tracking=True)
    success_rate = fields.Float(string='Success Rate')
    tracking_info = fields.Char(string='Tracking Info')
    type = fields.Selection(string='Type')
    unavailable = fields.Char(string='Unavailable')
    user_id = fields.Many2one('res.users', string='User Id')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    work_orders = fields.Char(string='Work Orders')
    workload_stats = fields.Char(string='Workload Stats')
    write_date = fields.Date(string='Write Date')
    coordinator_id = fields.Many2one()
    prerequisite_work_order_ids = fields.Many2many()
    fsm_task_id = fields.Many2one()
    portal_visible = fields.Boolean()
    invoice_line_ids = fields.One2many()

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name'] = self.env['ir.sequence'].next_by_code()
                        'work.order.coordinator') or _('New'
            return super().create(vals_list)


    def _compute_coordination_metrics(self):
            for record in self:
                all_orders = (record.container_retrieval_ids +)
                                record.file_retrieval_ids +
                                record.scan_retrieval_ids +
                                record.destruction_ids +
                                record.access_ids

                record.total_work_orders = len(all_orders)

                completed = all_orders.filtered()
                    lambda wo: wo.state in ['completed', 'closed', 'done']
                record.completed_work_orders = len(completed)

                if record.total_work_orders > 0:
                    record.coordination_progress = ()
                        record.completed_work_orders / record.total_work_orders * 100
                else:
                    record.coordination_progress = 0.0

        # ============================================================================
            # INTEGRATION ACTION METHODS
        # ============================================================================

    def action_coordinate_all(self):
            """Start coordination of all work orders"""
            self.ensure_one()

            # Update all work orders with shared resources
            all_orders = self._get_all_work_orders()

            for order in all_orders:
                if hasattr(order, 'coordinator_id'):
                    order.coordinator_id = self.id
                if hasattr(order, 'vehicle_ids') and self.vehicle_ids:
                    order.vehicle_ids = [(6, 0, self.vehicle_ids.ids)]
                if hasattr(order, 'employee_ids') and self.employee_ids:
                    order.employee_ids = [(6, 0, self.employee_ids.ids)]

            self.message_post()
                body=_("Coordination started for %s work orders", len(all_orders)):



    def action_create_fsm_tasks(self):
            """Create FSM tasks for all work orders""":
            self.ensure_one()

            if not self.fsm_project_id:
                # Create FSM project if not exists:
                project_vals = {}
                    'name': _("Records Management - %s", self.partner_id.name),
                    'is_fsm': True,
                    'partner_id': self.partner_id.id,
                    'allow_timesheets': True,

                self.fsm_project_id = self.env['project.project'].create(project_vals)

            # Create FSM tasks for each work order type:
            task_count = 0
            for order in self._get_all_work_orders():
                if hasattr(order, 'create_fsm_task'):
                    order.create_fsm_task(self.fsm_project_id.id)
                    task_count += 1

            self.message_post()
                body=_("Created %s FSM tasks for coordinated work orders", task_count):



    def action_consolidate_billing(self):
            """Create consolidated invoice for all work orders""":
            self.ensure_one()

            if not self.consolidated_billing:
                raise UserError(_("Consolidated billing is not enabled"))

            if self.invoice_id:
                raise UserError(_("Consolidated invoice already exists"))

            # Create invoice
            invoice_vals = {}
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'ref': self.name,

            invoice = self.env['account.move'].create(invoice_vals)

            # Add invoice lines from all work orders
            line_count = 0
            for order in self._get_all_work_orders():
                if hasattr(order, 'create_invoice_lines'):
                    lines = order.create_invoice_lines(invoice.id)
                    line_count += len(lines)

            self.invoice_id = invoice.id
            self.message_post()
                body=_("Consolidated invoice created with %s lines", line_count)


            return {}
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice.id,
                'view_mode': 'form',
                'target': 'current',


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def _get_all_work_orders(self):
            """Get all work orders managed by this coordinator"""
            return (self.container_retrieval_ids +)
                    self.file_retrieval_ids +
                    self.scan_retrieval_ids +
                    self.destruction_ids +
                    self.access_ids


    def get_next_available_slot(self, duration_hours=2):
            """Find next available time slot considering all work orders"""
            self.ensure_one()

            # Logic to find optimal scheduling slot
            base_date = self.scheduled_date or fields.Datetime.now()

            if self.coordination_type == 'sequential':
                # Sequential: each starts after previous completes
                current_date = base_date
                for order in self._get_all_work_orders().sorted('priority', reverse=True):
                    order.scheduled_date = current_date
                    if hasattr(order, 'estimated_duration_hours'):
                        current_date += timedelta(hours=order.estimated_duration_hours or 2)
                    else:
                        current_date += timedelta(hours=duration_hours)

            elif self.coordination_type == 'parallel':
                # Parallel: all start at same time
                for order in self._get_all_work_orders():
                    order.scheduled_date = base_date

            # Mixed coordination handled case by case


    def create_customer_notification(self):
            """Create customer notification for coordination status""":
            self.ensure_one()

            # Create portal notification or email
            template = self.env.ref('records_management.email_template_work_order_coordination',
                                    raise_if_not_found=False
            if template:
                template.send_mail(self.id, force_send=True)


    def create_invoice_lines(self, invoice_id):
            """Create invoice lines for this work order""":
            lines = []

            # Get billing rates based on work order type
            if hasattr(self, '_get_billing_lines'):
                billing_lines = self._get_billing_lines()
                for line_vals in billing_lines:
                    line_vals.update({)}
                        'move_id': invoice_id,
                        'work_order_id': self.id,

                    line = self.env['account.move.line'].create(line_vals)
                    lines.append(line)

            return lines


    def _check_prerequisites(self):
            """Check if prerequisite work orders are completed""":
            for prereq in self.prerequisite_work_order_ids:
                if prereq.state not in ['completed', 'done', 'closed']:
                    raise UserError()
                        _("Cannot start %s until prerequisite work order %s is completed",
                            self.display_name, prereq.name



    def notify_customer_update(self):
            """Send customer notification about work order update"""
            if self.portal_visible and self.partner_id:
                # Send portal notification
                self.message_notify()
                    partner_ids=self.partner_id.ids,
                    subject=_("Update: %s", self.display_name),
                    body=_('Your work order %s has been updated. Status: %s',
                            self.display_name, self.state

