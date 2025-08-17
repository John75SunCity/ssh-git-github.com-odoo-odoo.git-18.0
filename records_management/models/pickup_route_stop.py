from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class PickupRouteStop(models.Model):
    _name = 'pickup.route.stop'
    _description = 'Pickup Route Stop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_id, sequence, planned_arrival'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    route_id = fields.Many2one()
    partner_id = fields.Many2one()
    pickup_request_id = fields.Many2one()
    sequence = fields.Integer()
    planned_arrival = fields.Datetime()
    planned_departure = fields.Datetime()
    actual_arrival = fields.Datetime(string='Actual Arrival')
    actual_departure = fields.Datetime()
    address = fields.Text()
    gps_latitude = fields.Float(string='GPS Latitude')
    gps_longitude = fields.Float(string='GPS Longitude')
    distance = fields.Float()
    state = fields.Selection()
    completion_status = fields.Selection()
    planned_duration = fields.Float()
    actual_duration = fields.Float()
    delay_minutes = fields.Float()
    notes = fields.Text(string='Stop Notes')
    completion_notes = fields.Text()
    special_instructions = fields.Text()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    contact_person = fields.Char(string='Contact Person')
    contact_phone = fields.Char(string='Contact Phone')
    contact_email = fields.Char(string='Contact Email')
    access_instructions = fields.Text(string='Access Instructions')
    estimated_duration = fields.Float(string='Estimated Duration (hours)')
    estimated_weight = fields.Float(string='Estimated Weight (lbs)')
    actual_weight = fields.Float(string='Actual Weight (lbs)')
    delivery_instructions = fields.Text(string='Delivery Instructions')
    customer_signature = fields.Binary(string='Customer Signature')
    driver_signature = fields.Binary(string='Driver Signature')
    photos_taken = fields.Integer(string='Photos Taken')
    verification_code = fields.Char(string='Verification Code')
    access_info = fields.Char(string='Access Info')
    action_complete_stop = fields.Char(string='Action Complete Stop')
    action_reset_to_pending = fields.Char(string='Action Reset To Pending')
    action_skip_stop = fields.Char(string='Action Skip Stop')
    action_start_stop = fields.Char(string='Action Start Stop')
    action_view_pickup_request = fields.Char(string='Action View Pickup Request')
    action_view_route = fields.Char(string='Action View Route')
    activities_overdue = fields.Char(string='Activities Overdue')
    activities_today = fields.Char(string='Activities Today')
    activities_upcoming_all = fields.Char(string='Activities Upcoming All')
    actual_boxes = fields.Char(string='Actual Boxes')
    actual_time = fields.Float(string='Actual Time')
    address_info = fields.Char(string='Address Info')
    barcode_scanned = fields.Char(string='Barcode Scanned')
    basic_info = fields.Char(string='Basic Info')
    button_box = fields.Char(string='Button Box')
    city = fields.Char(string='City')
    color = fields.Char(string='Color')
    company = fields.Char(string='Company')
    completed = fields.Boolean(string='Completed')
    completion = fields.Char(string='Completion')
    completion_info = fields.Char(string='Completion Info')
    contact_info = fields.Char(string='Contact Info')
    context = fields.Char(string='Context')
    country_id = fields.Many2one('country')
    create_date = fields.Date(string='Create Date')
    create_uid = fields.Char(string='Create Uid')
    domain = fields.Char(string='Domain')
    estimated_boxes = fields.Char(string='Estimated Boxes')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    in_progress = fields.Char(string='In Progress')
    items_info = fields.Char(string='Items Info')
    latitude = fields.Char(string='Latitude')
    location = fields.Char(string='Location')
    location_accuracy = fields.Char(string='Location Accuracy')
    location_coordinates = fields.Char(string='Location Coordinates')
    longitude = fields.Char(string='Longitude')
    my_stops = fields.Char(string='My Stops')
    name = fields.Char(string='Name')
    overdue = fields.Char(string='Overdue')
    partner = fields.Char(string='Partner')
    pending = fields.Char(string='Pending')
    pickup_details = fields.Char(string='Pickup Details')
    pickup_route = fields.Char(string='Pickup Route')
    pickup_route_id = fields.Many2one('pickup.route')
    res_model = fields.Char(string='Res Model')
    scheduled_date = fields.Date(string='Scheduled Date')
    scheduled_month = fields.Char(string='Scheduled Month')
    scheduled_time = fields.Float(string='Scheduled Time')
    scheduled_week = fields.Char(string='Scheduled Week')
    skipped = fields.Char(string='Skipped')
    special_requirements = fields.Char(string='Special Requirements')
    state_id = fields.Many2one('state')
    stop_sequence = fields.Char(string='Stop Sequence')
    system_info = fields.Char(string='System Info')
    this_week = fields.Char(string='This Week')
    timing = fields.Char(string='Timing')
    today = fields.Char(string='Today')
    tracking = fields.Char(string='Tracking')
    type = fields.Selection(string='Type')
    urgent = fields.Char(string='Urgent')
    user = fields.Char(string='User')
    user_id = fields.Many2one('res.users', string='User Id')
    verification = fields.Char(string='Verification')
    view_mode = fields.Char(string='View Mode')
    write_date = fields.Date(string='Write Date')
    write_uid = fields.Char(string='Write Uid')
    zip = fields.Char(string='Zip')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            for stop in self:
                if stop.pickup_request_id:
                    stop.display_name = _()
                        "Stop %s: %s (%s)",
                        stop.sequence,
                        stop.partner_id.name,
                        stop.pickup_request_id.name,

                else:
                    stop.display_name = _()
                        "Stop %s: %s", stop.sequence, stop.partner_id.name



    def _compute_actual_duration(self):
            for stop in self:
                if stop.actual_arrival and stop.actual_departure:
                    delta = stop.actual_departure - stop.actual_arrival
                    stop.actual_duration = ()
                        delta.total_seconds() / 60.0

                else:
                    stop.actual_duration = 0.0


    def _compute_delay(self):
            for stop in self:
                if stop.planned_arrival and stop.actual_arrival:
                    delta = stop.actual_arrival - stop.planned_arrival
                    stop.delay_minutes = ()
                        delta.total_seconds() / 60.0

                else:
                    stop.delay_minutes = 0.0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_mark_in_transit(self):
            """Mark stop as in transit"""
            self.ensure_one()
            if self.state != "planned":
                raise UserError(_("Can only mark planned stops as in transit"))

            self.write({"state": "in_transit"})
            self.message_post(body=_("Stop marked as in transit"))


    def action_mark_arrived(self):
            """Mark arrival at stop"""
            self.ensure_one()
            if self.state not in ["planned", "in_transit"]:
                raise UserError(_("Invalid state transition to arrived"))

            self.write()
                {"state": "arrived", "actual_arrival": fields.Datetime.now()}

            self.message_post(body=_("Arrived at stop"))


    def action_complete_stop(self):
            """Complete the stop"""
            self.ensure_one()
            if self.state != "arrived":
                raise UserError(_("Must arrive at stop before completing"))

            self.write()
                {}
                    "state": "completed",
                    "actual_departure": fields.Datetime.now(),
                    "completion_status": "successful",



            # Update associated pickup request
            if self.pickup_request_id:
                self.pickup_request_id.action_mark_completed()

            self.message_post(body=_("Stop completed successfully"))


    def action_skip_stop(self):
            """Skip this stop"""
            self.ensure_one()
            if self.state in ["completed"]:
                raise UserError(_("Cannot skip completed stops"))

            self.write({"state": "skipped", "completion_status": "failed"})
            self.message_post(body=_("Stop skipped"))


    def action_reschedule_stop(self):
            """Reschedule this stop"""
            self.ensure_one()
            self.write({"state": "planned", "completion_status": "rescheduled"})
            self.message_post(body=_("Stop rescheduled"))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_planned_times(self):
            for stop in self:
                if stop.planned_arrival and stop.planned_departure:
                    if stop.planned_arrival >= stop.planned_departure:
                        raise ValidationError()
                            _("Planned departure must be after arrival")



    def _check_actual_times(self):
            for stop in self:
                if stop.actual_arrival and stop.actual_departure:
                    if stop.actual_arrival >= stop.actual_departure:
                        raise ValidationError()
                            _("Actual departure must be after arrival")



    def _check_gps_latitude(self):
            for stop in self:
                if stop.gps_latitude and not (-90 <= stop.gps_latitude <= 90):
                    raise ValidationError()
                        _("GPS latitude must be between -90 and 90 degrees")



    def _check_gps_longitude(self):
            for stop in self:
                if stop.gps_longitude and not (-180 <= stop.gps_longitude <= 180):
                    raise ValidationError()
                        _("GPS longitude must be between -180 and 180 degrees")


        # ============================================================================
            # OVERRIDE METHODS
        # ============================================================================

    def create(self, vals_list):
            stops = super().create(vals_list)

            # Auto-populate address from partner if not provided:
            for stop in stops:
                if not stop.address and stop.partner_id:
                    stop.address = stop.partner_id.contact_address

            return stops

