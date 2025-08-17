from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class WorkOrderShredding(models.Model):
    _name = 'work.order.shredding'
    _description = 'Shredding Work Order Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    customer_id = fields.Many2one()
    partner_id = fields.Many2one()
    shredding_service_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    scheduled_date = fields.Datetime()
    start_date = fields.Datetime(string='Start Date')
    completion_date = fields.Datetime()
    estimated_duration = fields.Float()
    actual_duration = fields.Float()
    priority = fields.Selection()
    work_order_type = fields.Selection()
    urgency_reason = fields.Text()
    assigned_team_id = fields.Many2one()
    team_leader_id = fields.Many2one()
    technician_ids = fields.Many2many()
    equipment_ids = fields.Many2many()
    vehicle_id = fields.Many2one()
    material_type = fields.Selection()
    estimated_weight = fields.Float()
    actual_weight = fields.Float()
    container_count = fields.Integer()
    special_instructions = fields.Text()
    state = fields.Selection()
    service_location_id = fields.Many2one()
    customer_address = fields.Text()
    access_instructions = fields.Text()
    contact_person = fields.Char()
    contact_phone = fields.Char()
    completion_notes = fields.Text()
    customer_signature = fields.Binary()
    customer_satisfaction = fields.Selection()
    quality_check_passed = fields.Boolean()
    supervisor_approval = fields.Boolean()
    certificate_required = fields.Boolean()
    certificate_id = fields.Many2one()
    compliance_level = fields.Selection()
    witness_required = fields.Boolean()
    witness_id = fields.Many2one()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary()
    currency_id = fields.Many2one()
    billable = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    batch_id = fields.Many2one('shredding.inventory.batch')
    access_restrictions = fields.Char(string='Access Restrictions')
    action_bulk_confirm = fields.Char(string='Action Bulk Confirm')
    action_bulk_start = fields.Char(string='Action Bulk Start')
    action_cancel = fields.Char(string='Action Cancel')
    action_complete = fields.Char(string='Action Complete')
    action_confirm = fields.Char(string='Action Confirm')
    action_pause = fields.Char(string='Action Pause')
    action_reset_to_draft = fields.Char(string='Action Reset To Draft')
    action_resume = fields.Char(string='Action Resume')
    action_start = fields.Char(string='Action Start')
    action_view_audit_logs = fields.Char(string='Action View Audit Logs')
    action_view_certificates = fields.Char(string='Action View Certificates')
    action_view_containers = fields.Char(string='Action View Containers')
    action_view_documents = fields.Char(string='Action View Documents')
    assigned_technicians = fields.Char(string='Assigned Technicians')
    audit_log_count = fields.Integer(string='Audit Log Count')
    bin_location_id = fields.Many2one('bin.location')
    button_box = fields.Char(string='Button Box')
    certificate_count = fields.Integer(string='Certificate Count')
    chain_of_custody_id = fields.Many2one('chain.of.custody')
    check_item = fields.Char(string='Check Item')
    completed = fields.Boolean(string='Completed')
    completed_by = fields.Char(string='Completed By')
    completed_date = fields.Date(string='Completed Date')
    completion_percentage = fields.Char(string='Completion Percentage')
    compliance = fields.Char(string='Compliance')
    compliance_checklist_ids = fields.One2many('compliance.checklist')
    confirmed = fields.Boolean(string='Confirmed')
    container_ids = fields.One2many('container')
    container_type = fields.Selection(string='Container Type')
    containers = fields.Char(string='Containers')
    context = fields.Char(string='Context')
    coordinator_id = fields.Many2one('coordinator')
    deadline_date = fields.Date(string='Deadline Date')
    department_id = fields.Many2one('department')
    description = fields.Char(string='Description')
    document_count = fields.Integer(string='Document Count')
    documentation_level = fields.Char(string='Documentation Level')
    domain = fields.Char(string='Domain')
    draft = fields.Char(string='Draft')
    duration = fields.Char(string='Duration')
    equipment = fields.Char(string='Equipment')
    equipment_info = fields.Char(string='Equipment Info')
    equipment_operator_id = fields.Many2one('equipment.operator')
    equipment_status = fields.Selection(string='Equipment Status')
    estimated_volume = fields.Char(string='Estimated Volume')
    event_type = fields.Selection(string='Event Type')
    group_coordinator = fields.Char(string='Group Coordinator')
    group_department = fields.Char(string='Group Department')
    group_partner = fields.Char(string='Group Partner')
    group_priority = fields.Selection(string='Group Priority')
    group_scheduled_date = fields.Date(string='Group Scheduled Date')
    group_shredding_type = fields.Selection(string='Group Shredding Type')
    group_state = fields.Selection(string='Group State')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    in_progress = fields.Char(string='In Progress')
    inactive = fields.Boolean(string='Inactive')
    internal_notes = fields.Char(string='Internal Notes')
    is_completed = fields.Boolean(string='Is Completed')
    is_shredded = fields.Char(string='Is Shredded')
    location_id = fields.Many2one('location')
    maintenance_due_date = fields.Date(string='Maintenance Due Date')
    my_orders = fields.Char(string='My Orders')
    naid_compliant = fields.Char(string='Naid Compliant')
    naid_info = fields.Char(string='Naid Info')
    naid_level = fields.Char(string='Naid Level')
    notes = fields.Char(string='Notes')
    order_info = fields.Char(string='Order Info')
    overdue = fields.Char(string='Overdue')
    priority_row = fields.Char(string='Priority Row')
    progress_info = fields.Char(string='Progress Info')
    res_model = fields.Char(string='Res Model')
    resource_allocation = fields.Char(string='Resource Allocation')
    security_info = fields.Char(string='Security Info')
    security_level = fields.Char(string='Security Level')
    service_location = fields.Char(string='Service Location')
    shredded_date = fields.Date(string='Shredded Date')
    shredding_equipment_id = fields.Many2one('shredding.equipment')
    shredding_priority = fields.Selection(string='Shredding Priority')
    shredding_type = fields.Selection(string='Shredding Type')
    started_date = fields.Date(string='Started Date')
    tag_ids = fields.One2many('tag')
    this_week = fields.Char(string='This Week')
    timeline = fields.Char(string='Timeline')
    timeline_ids = fields.One2many('timeline')
    timestamp = fields.Char(string='Timestamp')
    today = fields.Char(string='Today')
    total_volume = fields.Char(string='Total Volume')
    total_weight = fields.Float(string='Total Weight')
    type = fields.Selection(string='Type')
    urgent = fields.Char(string='Urgent')
    video_recording = fields.Char(string='Video Recording')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    weight = fields.Char(string='Weight')
    witness_name = fields.Char(string='Witness Name')
    witness_signature = fields.Char(string='Witness Signature')
    now = fields.Datetime()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_audit_log_count(self):
            for record in self:
                record.audit_log_count = len(record.audit_log_ids)


    def _compute_certificate_count(self):
            for record in self:
                record.certificate_count = len(record.certificate_ids)


    def _compute_document_count(self):
            for record in self:
                record.document_count = len(record.document_ids)


    def _compute_total_volume(self):
            for record in self:
                record.total_volume = sum(record.line_ids.mapped('amount'))


    def _compute_total_weight(self):
            for record in self:
                record.total_weight = sum(record.line_ids.mapped('amount'))

        # ============================================================================
            # COMPUTED FIELDS
        # ============================================================================

    def _compute_actual_duration(self):
            """Compute actual duration based on start and completion times"""
            for order in self:
                if order.start_date and order.completion_date:
                    delta = order.completion_date - order.start_date
                    order.actual_duration = ()
                        delta.total_seconds() / 3600.0

                else:
                    order.actual_duration = 0.0


    def _compute_display_name(self):
            """Compute display name with status and date information"""
            for order in self:
                parts = [order.name]
                if order.customer_id:
                    parts.append(f"({order.customer_id.name})")
                if order.state:
                    state_label = dict(order._fields["state"].selection)[order.state]
                    parts.append(f"- {state_label}")
                order.display_name = " ".join(parts)    # ============================================================================
        # ORM OVERRIDES
            # ============================================================================

    def create(self, vals_list):
            """Override create to generate sequence number"""
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("work.order.shredding")
                        or "New"

            return super().create(vals_list)


    def write(self, vals):
            """Override write to track important changes"""
            # Log state changes
            if "state" in vals:
                for order in self:
                    if vals["state"] != order.state:
                        old_state = dict(order._fields["state"].selection)[order.state]
                        new_state = dict(order._fields["state"].selection)[vals["state"]]
                        order.message_post()
                            body=_("Work order status changed from %s to %s", (old_state), new_state),
                            message_type="notification",

            # Set start date when work begins
            if vals.get("state") == "in_progress":
                for order in self:
                    if not order.start_date:
                        order.write({"start_date": fields.Datetime.now()})

            # Set completion date when work is completed
            if vals.get("state") == "completed":
                for order in self:
                    if not order.completion_date:
                        order.write({"completion_date": fields.Datetime.now()})

            return super().write(vals)

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_confirm(self):
            """Confirm the work order"""

            self.ensure_one()
            for order in self:
                if order.state != "draft":
                    raise UserError(_("Only draft work orders can be confirmed"))

                order.write({"state": "confirmed"})
                order.message_post(body=_("Work order confirmed"))


    def action_assign_team(self):
            """Assign team to work order"""

            self.ensure_one()
            for order in self:
                if order.state not in ["confirmed"]:
                    raise UserError()
                        _("Work order must be confirmed before team assignment")


                if not order.assigned_team_id:
                    raise UserError(_("Please select a team before assignment"))

                order.write({"state": "assigned"})
                order.message_post()
                    body=_("Team assigned: %s", order.assigned_team_id.name),
                    message_type="notification",


    def action_start_work(self):
            """Start work order execution"""

            self.ensure_one()
            for order in self:
                if order.state != "assigned":
                    raise UserError(_("Work order must be assigned before starting"))

                order.write({"state": "in_progress", "start_date": fields.Datetime.now()})
                order.message_post(body=_("Work order started"))


    def action_complete_work(self):
            """Complete work order"""

            self.ensure_one()
            for order in self:
                if order.state != "in_progress":
                    raise UserError(_("Only in-progress work orders can be completed"))

                order.write()
                    {"state": "completed", "completion_date": fields.Datetime.now()}


                # Generate certificate if required:
                if order.certificate_required and not order.certificate_id:
                    order._generate_destruction_certificate()

                order.message_post(body=_("Work order completed"))


    def action_verify_completion(self):
            """Verify work order completion"""

            self.ensure_one()
            for order in self:
                if order.state != "completed":
                    raise UserError(_("Only completed work orders can be verified"))

                if not order.quality_check_passed:
                    raise UserError(_("Quality check must pass before verification"))

                order.write({"state": "verified"})
                order.message_post()
                    body=_("Work order verified by %s", self.env.user.name),
                    message_type="notification",


    def action_cancel(self):
            """Cancel work order"""

            self.ensure_one()
            for order in self:
                if order.state in ["completed", "verified"]:
                    raise UserError(_("Cannot cancel completed or verified work orders"))

                order.write({"state": "cancelled"})
                order.message_post(body=_("Work order cancelled"))


    def action_reset_to_draft(self):
            """Reset work order to draft"""

            self.ensure_one()
            for order in self:
                if order.state == "verified":
                    raise UserError(_("Cannot reset verified work orders to draft"))

                order.write({"state": "draft"})
                order.message_post(body=_("Work order reset to draft"))


    def action_view_certificate(self):
            """View associated destruction certificate"""

            self.ensure_one()
            if not self.certificate_id:
                raise UserError(_("No certificate associated with this work order"))

            return {}
                "type": "ir.actions.act_window",
                "name": _("Destruction Certificate"),
                "res_model": "naid.certificate",
                "res_id": self.certificate_id.id,
                "view_mode": "form",
                "target": "current",


        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def _generate_destruction_certificate(self):
            """Generate NAID destruction certificate"""
            self.ensure_one()

            if self.certificate_id:
                return self.certificate_id

            certificate_vals = {}
                "name": f"Certificate - {self.name}",
                "certificate_type": "destruction",
                "customer_id": self.customer_id.id,
                "work_order_id": self.id,
                "destruction_date": self.completion_date or fields.Datetime.now(),
                "total_weight": self.actual_weight,
                "material_type": self.material_type,
                "compliance_level": self.compliance_level,
                "witness_id": self.witness_id.id if self.witness_id else None,:


            certificate = self.env["naid.certificate"].create(certificate_vals)
            self.certificate_id = certificate

            return certificate


    def check_team_availability(self):
            """Check if assigned team is available for scheduled date""":
            self.ensure_one()

            if not self.assigned_team_id or not self.scheduled_date:
                return True

            # Check for conflicting work orders:
            conflicting_orders = self.search()
                []
                    ("assigned_team_id", "=", self.assigned_team_id.id),
                    ("scheduled_date", "=", self.scheduled_date),
                    ("state", "in", ["assigned", "in_progress"]),
                    ("id", "!=", self.id),


            return len(conflicting_orders) == 0


    def get_work_order_summary(self):
            """Get summary information for reporting""":
            self.ensure_one()

            return {}
                "name": self.name,
                "customer": self.customer_id.name,
                "state": self.state,
                "scheduled_date": self.scheduled_date,
                "team": self.assigned_team_id.name if self.assigned_team_id else None,:
                "material_type": self.material_type,
                "estimated_weight": self.estimated_weight,
                "actual_weight": self.actual_weight,
                "duration": self.actual_duration,
                "satisfaction": self.customer_satisfaction,


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_scheduled_date(self):

            Validate scheduled date is not in the past.

            Only checks for 'draft' state because scheduling is finalized at confirmation;""":""""
            after confirmation, rescheduling is managed via other business logic.

            for order in self:
                if order.scheduled_date and order.state == "draft":

    def _check_date_sequence(self):
            """Validate date sequence"""
            for order in self:
                if order.start_date and order.completion_date:
                    if order.start_date > order.completion_date:
                        raise ValidationError(_("Completion date must be after start date"))


    def _check_weights(self):
            """Validate weight values"""
            for order in self:
                if order.estimated_weight is not None and order.estimated_weight < 0:
                    raise ValidationError(_("Estimated weight cannot be negative"))
                if order.actual_weight is not None and order.actual_weight < 0:
                    raise ValidationError(_("Actual weight cannot be negative"))


    def name_get(self):
            """Custom name display"""
            result = []
            for order in self:
                name_parts = [order.name]

                if order.customer_id:
                    name_parts.append(f"({order.customer_id.name})")

                if order.state != "draft":
                    state_label = dict(order._fields["state"].selection)[order.state]
                    name_parts.append(f"- {state_label}")

                # Ensure only two elements in tuple: (id, display_name)
                result.append((order.id, " ".join(name_parts)))

            return result


    def _search_name():
            self, name, args=None, operator="ilike", limit=100, name_get_uid=None

            """Enhanced search by name or customer, returns name_get results for consistency""":
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    ("name", operator, name),
                    ("customer_id.name", operator, name),
                    ("portal_request_id.name", operator, name),
            ids = self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)
            return self.browse(ids).name_get()


    def get_priority_work_orders(self):
            """Get high priority work orders requiring attention"""
            return self.search()
                []
                    ("priority", "in", ["2", "3"]),
                    ("state", "in", ["confirmed", "assigned", "in_progress"]),
                order="priority desc, scheduled_date asc",

