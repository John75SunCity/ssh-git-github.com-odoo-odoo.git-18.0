# -*- coding: utf-8 -*-

Pickup Request Management Module

This module provides comprehensive pickup request management for the Records:
    pass
Management System. It handles customer document and equipment pickup requests
with complete workflow management from submission to completion.

Key Features
- Complete pickup request lifecycle management
- Customer portal integration with self-service requests
- Route optimization and scheduling
- Equipment and document pickup tracking
- Field service management integration
- Automated notifications and status updates

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


import re

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError

class PickupRequest(models.Model):

        Pickup Request Management - Customer document and equipment pickup requests
    Handles complete pickup workflows from submission to completion


    _name = "pickup.request"
    _description = "Pickup Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "request_date desc, priority desc, name"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Request Number",
        required=True,
        tracking=True,
        index=True,
        help="Unique pickup request identifier",
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this pickup request",:
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Active status of pickup request",

    # ============================================================================
        # CUSTOMER AND BUSINESS RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer requesting the pickup",

    contact_person = fields.Char(
        string="Contact Person", help="Primary contact person for pickup":


    contact_phone = fields.Char(
        string="Contact Phone", help="Phone number for pickup coordination":


    contact_email = fields.Char(
        string="Contact Email", help="Email address for pickup notifications":


        # ============================================================================
    # PICKUP LOCATION AND LOGISTICS
        # ============================================================================
    pickup_location_id = fields.Many2one(
        "records.location",
        string="Pickup Location",
        tracking=True,
        help="Primary pickup location",

    pickup_address = fields.Text(
        string="Pickup Address",
        help="Detailed pickup address if different from location",:
    pickup_instructions = fields.Text(
        string="Pickup Instructions", help="Special instructions for pickup team":


    access_requirements = fields.Text(
        string="Access Requirements",
        help="Special access requirements or security procedures",

    # ============================================================================
        # REQUEST TIMING AND SCHEDULING
    # ============================================================================
    request_date = fields.Datetime(
        string="Request Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date when pickup was requested",

    preferred_pickup_date = fields.Date(
        string="Preferred Pickup Date",
        tracking=True,
        help="Customer's preferred pickup date",'

    scheduled_pickup_date = fields.Datetime(
        string="Scheduled Pickup Date",
        tracking=True,
        help="Actual scheduled pickup date and time",

    completed_pickup_date = fields.Datetime(
        string="Completed Pickup Date",
        tracking=True,
        help="Date when pickup was completed",

    ,
    urgency_level = fields.Selection(
        [)
            ("low", "Low Priority"),
            ("normal", "Normal Priority"),
            ("high", "High Priority"),
            ("urgent", "Urgent"),
            ("emergency", "Emergency"),
        string="Urgency Level",
        default="normal",
        tracking=True,
        help="Priority level for pickup scheduling",:
    # ============================================================================
        # PICKUP TYPE AND CONFIGURATION
    # ============================================================================
    pickup_type = fields.Selection(
        [)
            ("document_boxes", "Document Boxes"),
            ("file_folders", "File Folders"),
            ("equipment", "Equipment"),
            ("storage_media", "Storage Media"),
            ("mixed", "Mixed Items"),
            ("bulk_collection", "Bulk Collection"),
            ("emergency_retrieval", "Emergency Retrieval"),
        string="Pickup Type",
        required=True,
        tracking=True,
        help="Type of items to be picked up",

    service_type = fields.Selection(
        [)
            ("regular", "Regular Pickup"),
            ("scheduled", "Scheduled Service"),
            ("on_demand", "On-Demand Service"),
            ("emergency", "Emergency Service"),
        string="Service Type",
        default="regular",
        help="Type of pickup service requested",

    recurring_pickup = fields.Boolean(
        string="Recurring Pickup",
        default=False,
        help="Whether this is a recurring pickup schedule",

    ,
    frequency = fields.Selection(
        [)
            ("weekly", "Weekly"),
            ("biweekly", "Bi-weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        string="Frequency",
        help="Frequency for recurring pickups",:
    # ============================================================================
        # WORKFLOW AND STATUS MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [)
            ("draft", "Draft"),
            ("submitted", "Submitted"),
            ("confirmed", "Confirmed"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of pickup request",

    approval_required = fields.Boolean(
        string="Approval Required",
        default=False,
        help="Whether this pickup requires management approval",

    approved_by_id = fields.Many2one(
            "res.users", string="Approved By", help="User who approved the pickup request"

    approval_date = fields.Datetime(
        string="Approval Date", help="Date when pickup was approved"


        # ============================================================================
    # PICKUP DETAILS AND SPECIFICATIONS
        # ============================================================================
    estimated_quantity = fields.Integer(
        string="Estimated Quantity", help="Estimated number of items for pickup":


    estimated_weight = fields.Float(
        ,
    string="Estimated Weight (lbs)", help="Estimated total weight of items"


    estimated_volume = fields.Float(
        ,
    string="Estimated Volume (cubic feet)", help="Estimated volume of items"


    special_handling = fields.Boolean(
        string="Special Handling Required",
        default=False,
        help="Whether items require special handling",

    confidential_items = fields.Boolean(
        string="Confidential Items",
        default=False,
        help="Whether pickup includes confidential materials",

    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required",
        default=False,
        help="Whether pickup requires chain of custody documentation",

    # ============================================================================
        # FIELD SERVICE INTEGRATION
    # ============================================================================
    fsm_task_id = fields.Many2one(
        "fsm.task",
        string="Field Service Task",
        help="Associated field service task",

    assigned_technician_id = fields.Many2one(
        "res.users",
        string="Assigned Technician",
        tracking=True,
        help="Technician assigned to handle pickup",

    vehicle_id = fields.Many2one(
            "records.vehicle", string="Assigned Vehicle", help="Vehicle assigned for pickup":

    route_id = fields.Many2one(
            "pickup.route", string="Pickup Route", help="Route assignment for pickup":

    fsm_route_id = fields.Many2one(
        "fsm.route.management",
        string="FSM Route",
        help="FSM route assignment for pickup",:
    # ============================================================================
        # DOCUMENTATION AND COMMUNICATION
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of pickup requirements"


    customer_notes = fields.Text(
        string="Customer Notes", help="Notes from customer regarding pickup"


    internal_notes = fields.Text(
        string="Internal Notes", help="Internal notes for pickup team":


    completion_notes = fields.Text(
        string="Completion Notes", help="Notes from technician upon completion"


        # ============================================================================
    # BILLING AND FINANCIAL
        # ============================================================================
    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this pickup is billable to customer",

    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost of pickup service",

    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost of pickup service",

    currency_id = fields.Many2one(
            "res.currency", string="Currency", related="company_id.currency_id", store=True

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    pickup_item_ids = fields.One2many(
        "pickup.request.item",
        "pickup_request_id",
        string="Pickup Items",
        help="Items to be picked up",

    related_container_ids = fields.Many2many(
        "records.container",
        string="Related Containers",
        help="Containers associated with this pickup",

    # ============================================================================
        # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name)),

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name)),

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name)),

    # ============================================================================
        # COMPUTED FIELDS
    # ============================================================================
    priority = fields.Selection(
        [)
            ("0", "Very Low"),
            ("1", "Low"),
            ("2", "Normal"),
            ("3", "High"),
            ("4", "Very High"),
        string="Priority",
        compute="_compute_priority",
        store=True,
        help="Computed priority based on urgency and other factors",

    total_items = fields.Integer(
        string="Total Items",
        compute="_compute_total_items",
        store=True,
        help="Total number of pickup items",

    is_overdue = fields.Boolean(
        string="Overdue",
        compute="_compute_overdue_status",
        help="Whether pickup is overdue",

    days_until_pickup = fields.Integer(
        string="Days Until Pickup",
        compute="_compute_days_until_pickup",
        help="Number of days until scheduled pickup",

    shred_bin_id = fields.Many2one("shred.bin",,
    string="Shred Bin")
        # Added by Safe Business Fields Fixer
    route_optimized = fields.Boolean(string="Route Optimized",,
    default=False)

        # Added by Safe Business Fields Fixer
    gps_coordinates = fields.Char(string="GPS Coordinates")

        # Added by Safe Business Fields Fixer
    access_instructions = fields.Text(string="Access Instructions")

        # Added by Safe Business Fields Fixer
    loading_dock_available = fields.Boolean(string="Loading Dock Available",,
    default=False)

        # Added by Safe Business Fields Fixer
    equipment_needed = fields.Text(string="Special Equipment Needed")

        # Added by Safe Business Fields Fixer
    hazardous_materials = fields.Boolean(string="Hazardous Materials",,
    default=False)

        # Added by Safe Business Fields Fixer
    weekend_pickup = fields.Boolean(string="Weekend Pickup Available",,
    default=False)

        # Added by Safe Business Fields Fixer
    after_hours_pickup = fields.Boolean(string="After Hours Pickup",,
    default=False),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    view_mode = fields.Char(string='View Mode'),
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends("urgency_level", "pickup_type", "confidential_items")
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

    @api.depends("pickup_item_ids")
    def _compute_total_items(self):
        """Compute total number of pickup items"""
        for record in self:
            record.total_items = len(record.pickup_item_ids)

    @api.depends("scheduled_pickup_date", "state")
    def _compute_overdue_status(self):
        """Determine if pickup is overdue""":
        for record in self:
            if record.scheduled_pickup_date and record.state not in [:)
                "completed",
                "cancelled",
                record.is_overdue = record.scheduled_pickup_date < fields.Datetime.now()
            else:
                record.is_overdue = False

    @api.depends("scheduled_pickup_date")
    def _compute_days_until_pickup(self):
        """Calculate days until scheduled pickup"""
        for record in self:
            if record.scheduled_pickup_date:
    scheduled_dt = fields.Datetime.from_string(record.scheduled_pickup_date)
                delta = scheduled_dt.date() - fields.Date.today()
                record.days_until_pickup = delta.days
            else:
                record.days_until_pickup = 0

    # ============================================================================
        # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
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
    @api.constrains("preferred_pickup_date")
    def _check_pickup_date(self):
        """Validate pickup date is not in the past"""
        for record in self:
            if (:)
                record.preferred_pickup_date
                and record.preferred_pickup_date < fields.Date.today()

                raise ValidationError(_("Preferred pickup date cannot be in the past"))

    @api.constrains("estimated_quantity", "estimated_weight", "estimated_volume")
    def _check_estimates(self):
        """Validate estimation values are positive"""
        for record in self:
            if record.estimated_quantity and record.estimated_quantity < 0:
                raise ValidationError(_("Estimated quantity must be positive"))

            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_("Estimated weight must be positive"))

            if record.estimated_volume and record.estimated_volume < 0:
                raise ValidationError(_("Estimated volume must be positive"))

    @api.constrains("contact_email")
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

    @api.model
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

class PickupRequestItem(models.Model):
    """Individual items within a pickup request"""

    _name = "pickup.request.item"
    _description = "Pickup Request Item"
    _order = "pickup_request_id, sequence, id"

    pickup_request_id = fields.Many2one(
            "pickup.request", string="Pickup Request", required=True, ondelete="cascade"

    sequence = fields.Integer(string="Sequence",,
    default=10),
    item_type = fields.Selection(
        [)
            ("container", "Document Container"),
            ("box", "File Box"),
            ("folder", "File Folder"),
            ("equipment", "Equipment"),
            ("media", "Storage Media"),
            ("other", "Other Item"),
        string="Item Type",
        required=True,

    container_id = fields.Many2one(
            "records.container", string="Container", help="Related container if applicable":

    description = fields.Text(string="Description",,
    required=True),
    estimated_quantity = fields.Integer(string="Estimated Quantity",,
    default=1),
    actual_quantity = fields.Integer(string="Actual Quantity"),
    estimated_weight = fields.Float(string="Estimated Weight (lbs)")
    actual_weight = fields.Float(string="Actual Weight (lbs)")
    special_handling = fields.Boolean(string="Special Handling",,
    default=False),
    notes = fields.Text(string="Notes"),
    @api.constrains("estimated_quantity", "actual_quantity")
    def _check_quantities(self):
        """Validate quantities are positive"""
        for record in self:
            if record.estimated_quantity and record.estimated_quantity < 0:
                raise ValidationError(_("Estimated quantity must be positive"))

            if record.actual_quantity and record.actual_quantity < 0:
                raise ValidationError(_("Actual quantity must be positive"))

class PickupScheduleWizard(models.TransientModel):
    """Wizard for scheduling pickup requests""":
    _name = "pickup.schedule.wizard"
    _description = "Pickup Schedule Wizard"

    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        required=True


    scheduled_date = fields.Datetime(
        string="Scheduled Date",
        required=True,
        default=fields.Datetime.now


    assigned_technician_id = fields.Many2one( "res.users", string="Assigned Technician",,
    required=True ),
    vehicle_id = fields.Many2one(
        "records.vehicle",
        string="Vehicle"


    route_id = fields.Many2one(
        "pickup.route",
        string="Route"


    notes = fields.Text(
        ,
    string="Scheduling Notes"


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

)))))))))))))))))))))))))))))))))))))))))))))))))
