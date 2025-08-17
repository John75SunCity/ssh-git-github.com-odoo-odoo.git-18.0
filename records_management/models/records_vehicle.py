from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsVehicle(models.Model):
    _name = 'records.vehicle'
    _description = 'Records Vehicle Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    pickup_route_ids = fields.One2many()
    name = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    status = fields.Selection()
    vin = fields.Char()
    license_plate = fields.Char()
    vehicle_type = fields.Selection()
    fuel_type = fields.Selection()
    total_capacity = fields.Float()
    vehicle_capacity_volume = fields.Float()
    vehicle_capacity_weight = fields.Float()
    max_boxes = fields.Integer()
    length = fields.Float()
    width = fields.Float()
    height = fields.Float()
    driver_id = fields.Many2one()
    driver_contact = fields.Char()
    last_service_date = fields.Date()
    next_service_date = fields.Date()
    maintenance_date = fields.Date()
    service_notes = fields.Text()
    route_date = fields.Date()
    start_time = fields.Datetime()
    pickup_route_ids = fields.One2many()
    created_date = fields.Datetime()
    updated_date = fields.Datetime()
    notes = fields.Text()
    display_name = fields.Char()
    capacity = fields.Float()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    fuel_capacity = fields.Float(string='Fuel Capacity')
    maintenance_due_date = fields.Char(string='Maintenance Due Date')
    insurance_expiry = fields.Char(string='Insurance Expiry')
    registration_number = fields.Char(string='Registration Number')
    Vehicles = fields.Char(string='Vehicles')
    action_set_available = fields.Char(string='Action Set Available')
    action_set_in_use = fields.Char(string='Action Set In Use')
    action_set_maintenance = fields.Char(string='Action Set Maintenance')
    available = fields.Char(string='Available')
    group_driver = fields.Char(string='Group Driver')
    group_status = fields.Selection(string='Group Status')
    group_type = fields.Selection(string='Group Type')
    help = fields.Char(string='Help')
    in_use = fields.Char(string='In Use')
    maintenance = fields.Char(string='Maintenance')
    res_model = fields.Char(string='Res Model')
    routes = fields.Char(string='Routes')
    search_view_id = fields.Many2one('search.view')
    view_mode = fields.Char(string='View Mode')
    timestamp = fields.Datetime()
    timestamp = fields.Datetime()
    timestamp = fields.Datetime()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute formatted display name with license plate"""
            for record in self:
                if record.license_plate:
                    record.display_name = _()
                        "%s [%s]", record.name or "Unknown", record.license_plate

                else:
                    record.display_name = record.name or "New Vehicle"


    def _compute_capacity(self):
            """Compute primary capacity measure"""
            for record in self:
                record.capacity = ()
                    record.total_capacity or record.vehicle_capacity_volume or 0.0


        # ============================================================================
            # ODOO FRAMEWORK METHODS
        # ============================================================================

    def create(self, vals_list):
            """Override create to set default values and generate sequence"""
            for vals in vals_list:
                if not vals.get("name"):
                    sequence = self.env["ir.sequence"].next_by_code("records.vehicle")
                    vals["name"] = sequence or _()
                        "Vehicle-%s", fields.Date.today().strftime("%Y%m%d")


    def write(self, vals):
            """Override write to update modification timestamps"""

    def name_get(self):
            """Custom name display with license plate"""
            result = []
            for record in self:
                name = record.name
                if record.license_plate:
                    name = _("%s [%s]", name, record.license_plate)
                if record.vehicle_type:
                    name = _("%s (%s)", name, record.vehicle_type)
                result.append((record.id, name))
            return result

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_activate(self):
            """Activate the vehicle"""
            self.ensure_one()
            self.write({"state": "active", "status": "available"})
            self.message_post(body=_("Vehicle activated and set to available"))


    def action_deactivate(self):
            """Deactivate the vehicle"""
            self.ensure_one()
            self.write({"state": "inactive", "status": "maintenance"})
            self.message_post(body=_("Vehicle deactivated"))


    def action_archive(self):
            """Archive the vehicle"""
            self.ensure_one()
            self.write({"state": "archived", "active": False})
            self.message_post(body=_("Vehicle archived"))


    def action_set_available(self):
            """Set vehicle status to available"""
            self.ensure_one()
            if self.state == "archived":
                raise UserError(_("Cannot set archived vehicle as available"))

    def action_set_in_service(self):
            """Set vehicle status to in service"""
            self.ensure_one()
            if self.status == "maintenance":
                raise UserError(_("Cannot use vehicle that is under maintenance"))

    def action_set_maintenance(self):
            """Set vehicle status to maintenance"""
            self.ensure_one()

    def action_view_routes(self):
            """View routes assigned to this vehicle"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Vehicle Routes"),
                "res_model": "fsm.route",
                "view_mode": "tree,form",
                "target": "current",
                "domain": [("vehicle_id", "=", self.id)],
                "context": {}
                    "default_vehicle_id": self.id,
                    "search_default_vehicle_id": self.id,



        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_license_plate_unique(self):
            """Ensure license plates are unique per company"""
            for record in self:
                if record.license_plate:
                    existing = self.search()
                        []
                            ("license_plate", "=", record.license_plate),
                            ("company_id", "=", record.company_id.id),
                            ("id", "!=", record.id),


                    if existing:
                        raise ValidationError()
                            _("License plate must be unique within the company")



    def _check_capacity_values(self):
            """Validate capacity values are positive"""
            for record in self:
                if any(:)
                    val < 0
                    for val in [:]
                        record.total_capacity or 0,
                        record.vehicle_capacity_volume or 0,
                        record.vehicle_capacity_weight or 0,
                        record.max_boxes or 0,


                    raise ValidationError(_("Capacity values must be positive"))


    def _check_dimensions(self):
            """Validate vehicle dimensions are positive"""
            for record in self:
                if any(:)
                    val < 0
                    for val in [record.length or 0, record.width or 0, record.height or 0]:

                    raise ValidationError(_("Vehicle dimensions must be positive"))


    def _check_service_dates(self):
            """Validate service date logic"""
            for record in self:
                if (:)
                    record.next_service_date
                    and record.last_service_date
                    and record.next_service_date <= record.last_service_date

                    raise ValidationError()
                        _("Next service date must be after last service date")


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_available_capacity(self):
            """Get available capacity information"""
            self.ensure_one()
            return {}
                "volume": self.vehicle_capacity_volume or self.total_capacity or 0,
                "weight": self.vehicle_capacity_weight or 0,
                "boxes": self.max_boxes or 0,
                "is_available": self.status == "available" and self.state == "active",



    def is_maintenance_due(self):
            """Check if vehicle is due for maintenance""":
            self.ensure_one()
            if not self.next_service_date:
                return False
            return fields.Date.today() >= self.next_service_date


    def cron_check_maintenance_due(self):
            """Cron job to check maintenance schedules and create activities for due vehicles""":
            due_vehicles = self.search()
                []
                    ("next_service_date", "<=", fields.Date.today()),
                    ("status", "!=", "maintenance"),
                    ("state", "=", "active"),


            for vehicle in due_vehicles:
                vehicle.activity_schedule()
                    "mail.mail_activity_data_todo",
                    summary=_("Maintenance Due: %s", vehicle.name),
                    note=_()
                        "Vehicle maintenance is due based on the scheduled service date."

                    user_id=vehicle.user_id.id,
                    date_deadline=fields.Date.today(),



    def _compute_capacity_status(self):
            """Compute vehicle capacity status"""
            for record in self:
                if record.vehicle_capacity_weight:
                    if record.vehicle_capacity_weight >= 10000:
                        record.capacity_status = 'heavy_duty'
                    elif record.vehicle_capacity_weight >= 5000:
                        record.capacity_status = 'medium_duty'
                    else:
                        record.capacity_status = 'light_duty'
                else:
                    record.capacity_status = 'unknown'
