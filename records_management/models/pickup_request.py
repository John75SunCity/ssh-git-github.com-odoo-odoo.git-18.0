from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class PickupRequest(models.Model):
    _name = 'pickup.schedule.wizard'
    _description = 'Pickup Schedule Wizard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'pickup_request_id, sequence, id'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    partner_id = fields.Many2one()
    contact_person = fields.Char()
    contact_phone = fields.Char()
    contact_email = fields.Char()
    pickup_location_id = fields.Many2one()
    pickup_address = fields.Text()
    pickup_instructions = fields.Text()
    access_requirements = fields.Text()
    request_date = fields.Datetime()
    preferred_pickup_date = fields.Date()
    scheduled_pickup_date = fields.Datetime()
    completed_pickup_date = fields.Datetime()
    urgency_level = fields.Selection()
    pickup_type = fields.Selection()
    service_type = fields.Selection()
    recurring_pickup = fields.Boolean()
    frequency = fields.Selection()
    state = fields.Selection()
    approval_required = fields.Boolean()
    approved_by_id = fields.Many2one()
    approval_date = fields.Datetime()
    estimated_quantity = fields.Integer()
    estimated_weight = fields.Float()
    estimated_volume = fields.Float()
    special_handling = fields.Boolean()
    confidential_items = fields.Boolean()
    chain_of_custody_required = fields.Boolean()
    fsm_task_id = fields.Many2one()
    assigned_technician_id = fields.Many2one()
    vehicle_id = fields.Many2one()
    route_id = fields.Many2one()
    fsm_route_id = fields.Many2one()
    description = fields.Text()
    customer_notes = fields.Text()
    internal_notes = fields.Text()
    completion_notes = fields.Text()
    billable = fields.Boolean()
    estimated_cost = fields.Monetary()
    actual_cost = fields.Monetary()
    currency_id = fields.Many2one()
    pickup_item_ids = fields.One2many()
    related_container_ids = fields.Many2many()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    priority = fields.Selection()
    total_items = fields.Integer()
    is_overdue = fields.Boolean()
    days_until_pickup = fields.Integer()
    shred_bin_id = fields.Many2one('shred.bin')
    route_optimized = fields.Boolean(string='Route Optimized')
    gps_coordinates = fields.Char(string='GPS Coordinates')
    access_instructions = fields.Text(string='Access Instructions')
    loading_dock_available = fields.Boolean(string='Loading Dock Available')
    equipment_needed = fields.Text(string='Special Equipment Needed')
    hazardous_materials = fields.Boolean(string='Hazardous Materials')
    weekend_pickup = fields.Boolean(string='Weekend Pickup Available')
    after_hours_pickup = fields.Boolean(string='After Hours Pickup')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    scheduled_dt = fields.Datetime()
    pickup_request_id = fields.Many2one()
    sequence = fields.Integer(string='Sequence')
    item_type = fields.Selection()
    container_id = fields.Many2one()
    description = fields.Text(string='Description')
    estimated_quantity = fields.Integer(string='Estimated Quantity')
    actual_quantity = fields.Integer(string='Actual Quantity')
    estimated_weight = fields.Float(string='Estimated Weight (lbs)')
    actual_weight = fields.Float(string='Actual Weight (lbs)')
    special_handling = fields.Boolean(string='Special Handling')
    notes = fields.Text(string='Notes')
    pickup_request_id = fields.Many2one()
    scheduled_date = fields.Datetime()
    assigned_technician_id = fields.Many2one('res.users', string='Assigned Technician')
    vehicle_id = fields.Many2one()
    route_id = fields.Many2one()
    notes = fields.Text()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_priority(self):
            """Compute priority based on urgency and item type"""
            priority_map = {}
                "emergency": "4",
                "urgent": "3",
                "high": "3",
                "normal": "2",
                "low": "1",


            for record in self:
                base_priority = priority_map.get(record.urgency_level, "2")

                # Increase priority for confidential items:
                if record.confidential_items:
                    base_priority = str(min(int(base_priority) + 1, 4))

                # Increase priority for emergency retrieval:
                if record.pickup_type == "emergency_retrieval":
                    base_priority = "4"

                record.priority = base_priority


    def _compute_total_items(self):
            """Compute total number of pickup items"""
            for record in self:
                record.total_items = len(record.pickup_item_ids)


    def _compute_overdue_status(self):
            """Determine if pickup is overdue""":
            for record in self:
                if record.scheduled_pickup_date and record.state not in [:]
                    "completed",
                    "cancelled",
                    record.is_overdue = record.scheduled_pickup_date < fields.Datetime.now()
                else:
                    record.is_overdue = False


    def _compute_days_until_pickup(self):
            """Calculate days until scheduled pickup"""
            for record in self:
                if record.scheduled_pickup_date:

    def create(self, vals_list):
            """Override create to set sequence and defaults"""
            for vals in vals_list:
                if not vals.get("name") or vals.get("name") == "/":
                    vals["name") = (]
                        self.env["ir.sequence"].next_by_code("pickup.request") or "PR-NEW"


            return super().create(vals_list)


    def write(self, vals):
            """Override write for state change tracking""":
            if "state" in vals:
                for record in self:
                    old_state = record.state
                    new_state = vals["state"]
                    if old_state != new_state:
                        record.message_post()
                            body=_("Pickup request status changed from %s to %s", old_state, new_state)


            return super().write(vals)

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_submit(self):
            """Submit pickup request for processing""":
            self.ensure_one()
            if self.state != "draft":
                raise UserError(_("Only draft requests can be submitted"))

            self.write()
                {}
                    "state": "submitted",
                    "request_date": fields.Datetime.now(),



            self.message_post(body=_("Pickup request submitted for processing")):

    def action_confirm(self):
            """Confirm pickup request"""

            self.ensure_one()
            if self.state not in ["draft", "submitted"]:
                raise UserError(_("Only draft or submitted requests can be confirmed"))

            self.write({"state": "confirmed"})
            self.message_post(body=_("Pickup request confirmed"))


    def action_schedule(self):
            """Schedule pickup request"""

            self.ensure_one()
            if self.state != "confirmed":
                raise UserError(_("Only confirmed requests can be scheduled"))

            return {}
                "type": "ir.actions.act_window",
                "name": _("Schedule Pickup"),
                "res_model": "pickup.schedule.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_pickup_request_id": self.id},



    def action_start_pickup(self):
            """Start pickup process"""

            self.ensure_one()
            if self.state != "scheduled":
                raise UserError(_("Only scheduled pickups can be started"))

            self.write({"state": "in_progress"})
            self.message_post(body=_("Pickup started by %s", self.env.user.name))


    def action_complete(self):
            """Complete pickup request"""

            self.ensure_one()
            if self.state != "in_progress":
                raise UserError(_("Only in-progress pickups can be completed"))

            self.write()
                {}
                    "state": "completed",
                    "completed_pickup_date": fields.Datetime.now(),



            self.message_post(body=_("Pickup completed successfully"))


    def action_cancel(self):
            """Cancel pickup request"""

            self.ensure_one()
            if self.state in ["completed"]:
                raise UserError(_("Completed pickups cannot be cancelled"))

            self.write({"state": "cancelled"})
            self.message_post(body=_("Pickup request cancelled"))


    def action_reset_to_draft(self):
            """Reset pickup to draft state"""

            self.ensure_one()
            if self.state in ["completed"]:
                raise UserError(_("Completed pickups cannot be reset"))

            self.write({"state": "draft"})
            self.message_post(body=_("Pickup request reset to draft"))


    def action_create_fsm_task(self):
            """Create field service task for pickup""":
            self.ensure_one()

            if self.fsm_task_id:
                raise UserError(_("FSM task already exists for this pickup")):
            task_vals = {}
                "name": _("Pickup: %s", self.name),
                "project_id": self.env.ref("records_management.project_pickup_requests").id,
                "partner_id": self.partner_id.id,
                "description": self.description,
                "date_deadline": self.preferred_pickup_date,

            if self.assigned_technician_id:
                task_vals["user_ids"] = [(6, 0, [self.assigned_technician_id.id])]

            task = self.env["fsm.task"].create(task_vals)
            self.fsm_task_id = task.id

            self.message_post(body=_("Field service task created: %s", task.name))

            return {}
                "type": "ir.actions.act_window",
                "name": _("Field Service Task"),
                "res_model": "fsm.task",
                "res_id": task.id,
                "view_mode": "form",



    def action_view_pickup_items(self):
            """View pickup items"""

            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Pickup Items"),
                "res_model": "pickup.request.item",
                "view_mode": "tree,form",
                "domain": [("pickup_request_id", "=", self.id)],
                "context": {"default_pickup_request_id": self.id},



    def action_generate_pickup_label(self):
            """Generate pickup label"""

            self.ensure_one()
            return self.env.ref()
                "records_management.action_report_pickup_label"
            ).report_action(self

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def calculate_estimated_cost(self):
            """Calculate estimated cost based on pickup type and quantity"""
            self.ensure_one()

            # Base rates (these would come from configuration)
            base_rates = {}
                "document_boxes": 15.0,
                "file_folders": 5.0,
                "equipment": 25.0,
                "storage_media": 10.0,
                "mixed": 20.0,
                "bulk_collection": 50.0,
                "emergency_retrieval": 100.0,


            base_cost = base_rates.get(self.pickup_type, 20.0)
            quantity_multiplier = max(1, self.estimated_quantity or 1)

            # Add urgency surcharge
            urgency_multipliers = {}
                "emergency": 2.0,
                "urgent": 1.5,
                "high": 1.25,
                "normal": 1.0,
                "low": 1.0,

            urgency_mult = urgency_multipliers.get(self.urgency_level, 1.0)

            estimated_cost = base_cost * quantity_multiplier * urgency_mult

            # Add special handling surcharge
            if self.special_handling:
                estimated_cost *= 1.2

            # Add confidential handling surcharge
            if self.confidential_items:
                estimated_cost *= 1.3

            return estimated_cost


    def create_pickup_items_from_containers(self, container_ids):
            """Create pickup items from selected containers"""
            self.ensure_one()

            containers = self.env["records.container"].browse(container_ids)

            for container in containers:
                self.env["pickup.request.item").create(]
                    {}
                        "pickup_request_id": self.id,
                        "container_id": container.id,
                        "item_type": "container",
                        "description": _("Container: %s", container.name),
                        "estimated_quantity": 1,



            self.related_container_ids = [(6, 0, container_ids)]


    def get_pickup_summary(self):
            """Get pickup request summary for reporting""":
            self.ensure_one()
            return {}
                "request_number": self.name,
                "customer": self.partner_id.name,
                "pickup_type": self.pickup_type,
                "urgency": self.urgency_level,
                "status": self.state,
                "scheduled_date": self.scheduled_pickup_date,
                "total_items": self.total_items,
                "estimated_cost": self.estimated_cost,


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_pickup_date(self):
            """Validate pickup date is not in the past"""
            for record in self:
                if (:)
                    record.preferred_pickup_date
                    and record.preferred_pickup_date < fields.Date.today()

                    raise ValidationError(_("Preferred pickup date cannot be in the past"))


    def _check_estimates(self):
            """Validate estimation values are positive"""
            for record in self:
                if record.estimated_quantity and record.estimated_quantity < 0:
                    raise ValidationError(_("Estimated quantity must be positive"))

                if record.estimated_weight and record.estimated_weight < 0:
                    raise ValidationError(_("Estimated weight must be positive"))

                if record.estimated_volume and record.estimated_volume < 0:
                    raise ValidationError(_("Estimated volume must be positive"))


    def _check_email_format(self):
            """Validate email format"""
            for record in self:
                if record.contact_email:
                    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
                    if not re.match(email_pattern, record.contact_email):
                        raise ValidationError(_("Invalid email format"))

        # ============================================================================
            # DISPLAY AND SEARCH METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = record.name
                if record.partner_id:
                    name = _("%s - %s", record.name, record.partner_id.name)
                if record.pickup_type:
                    pickup_type_label = dict(record._fields["pickup_type"].selection)[]
                        record.pickup_type

                    name = _("%s (%s)", name, pickup_type_label)
                result.append((record.id, name))
            return result


    def _search_name(self, name, args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name, customer, or pickup type"""
            args = args or []
            domain = []
            if name:
                domain = []
                    "|",
                    "|",
                    ("name", operator, name),
                    ("partner_id.name", operator, name),
                    ("description", operator, name),
            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def _check_quantities(self):
            """Validate quantities are positive"""
            for record in self:
                if record.estimated_quantity and record.estimated_quantity < 0:
                    raise ValidationError(_("Estimated quantity must be positive"))

                if record.actual_quantity and record.actual_quantity < 0:
                    raise ValidationError(_("Actual quantity must be positive"))


    def action_schedule_pickup(self):
            """Schedule the pickup request"""

            self.ensure_one()

            self.pickup_request_id.write()
                {}
                    "state": "scheduled",
                    "scheduled_pickup_date": self.scheduled_date,
                    "assigned_technician": self.assigned_technician.id,
                    "vehicle_id": self.vehicle_id.id,
                    "route_id": self.route_id.id,



            if self.notes:
                self.pickup_request_id.message_post()
                    body=_("Pickup scheduled: %s", self.notes)

            else:
                self.pickup_request_id.message_post()
                    body=_("Pickup scheduled for %s", self.scheduled_date):


            return {"type": "ir.actions.act_window_close"}

