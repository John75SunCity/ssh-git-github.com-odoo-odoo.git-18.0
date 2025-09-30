from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PickupRouteStop(models.Model):
    _name = 'pickup.route.stop'
    _description = 'Pickup Route Stop'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_id, sequence, planned_arrival'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)
    route_id = fields.Many2one('pickup.route', string='Pickup Route', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    pickup_request_id = fields.Many2one('pickup.request', string='Pickup Request')
    sequence = fields.Integer(string='Sequence', default=10)
    planned_arrival = fields.Datetime(string='Planned Arrival', tracking=True)
    planned_departure = fields.Datetime(string='Planned Departure', tracking=True)
    actual_arrival = fields.Datetime(string='Actual Arrival', tracking=True)
    actual_departure = fields.Datetime(string='Actual Departure', tracking=True)
    address = fields.Text(string='Address')
    gps_latitude = fields.Float(string='GPS Latitude', digits=(10, 6))
    gps_longitude = fields.Float(string='GPS Longitude', digits=(10, 6))
    distance = fields.Float(string='Distance (miles)', digits=(8, 2))
    state = fields.Selection([
        ('planned', 'Planned'),
        ('in_transit', 'In Transit'),
        ('arrived', 'Arrived'),
        ('completed', 'Completed'),
        ('skipped', 'Skipped')
    ], string='State', default='planned', tracking=True)
    completion_status = fields.Selection([
        ('pending', 'Pending'),
        ('successful', 'Successful'),
        ('failed', 'Failed'),
        ('rescheduled', 'Rescheduled')
    ], string='Completion Status', default='pending')
    planned_duration = fields.Float(string='Planned Duration (hours)', digits=(4, 2))
    actual_duration = fields.Float(string='Actual Duration (hours)', compute='_compute_actual_duration', store=True)
    delay_minutes = fields.Float(string='Delay (minutes)', compute='_compute_delay', store=True)
    notes = fields.Text(string='Stop Notes')
    completion_notes = fields.Text(string='Completion Notes')
    special_instructions = fields.Text(string='Special Instructions')
    
    # Contact Information
    contact_person = fields.Char(string='Contact Person')
    contact_phone = fields.Char(string='Contact Phone')
    contact_email = fields.Char(string='Contact Email')
    access_instructions = fields.Text(string='Access Instructions')
    
    # Weight and Duration Tracking
    estimated_duration = fields.Float(string='Estimated Duration (hours)', digits=(4, 2))
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', digits=(8, 2))
    actual_weight = fields.Float(string='Actual Weight (lbs)', digits=(8, 2))
    
    # Service Information
    delivery_instructions = fields.Text(string='Delivery Instructions')
    customer_signature = fields.Binary(string='Customer Signature', copy=False)
    driver_signature = fields.Binary(string='Driver Signature', copy=False)
    photos_taken = fields.Integer(string='Photos Taken', default=0)
    verification_code = fields.Char(string='Verification Code')

    # -------------------------------------------------------------------------
    # SEARCH / FILTER FLAG FIELDS (Replacing dynamic context_today domains)
    # -------------------------------------------------------------------------
    # These booleans allow stable search filters instead of embedding Python date
    # arithmetic in XML view domains. They are computed in batch and also have
    # dedicated _search_* helpers mirroring the pattern used across the module
    # (portal requests, NAID compliance, scan retrieval items, maintenance equip.).
    scheduled_today = fields.Boolean(string='Scheduled Today', compute='_compute_schedule_flags', search='_search_scheduled_today')
    scheduled_recent_7d = fields.Boolean(string='Scheduled Last 7 Days', compute='_compute_schedule_flags', search='_search_scheduled_recent_7d')
    scheduled_overdue = fields.Boolean(string='Overdue (Uncompleted Past)', compute='_compute_schedule_flags', search='_search_scheduled_overdue')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('sequence', 'partner_id.name', 'pickup_request_id.name')
    def _compute_display_name(self):
        for stop in self:
            if stop.pickup_request_id:
                stop.display_name = _(
                    "Stop %s: %s (%s)",
                    stop.sequence,
                    stop.partner_id.name if stop.partner_id else '',
                    stop.pickup_request_id.name
                )
            else:
                stop.display_name = _(
                    "Stop %s: %s", stop.sequence, stop.partner_id.name if stop.partner_id else ''
                )

    @api.depends('actual_arrival', 'actual_departure')
    def _compute_actual_duration(self):
        for stop in self:
            if stop.actual_arrival and stop.actual_departure:
                delta = stop.actual_departure - stop.actual_arrival
                stop.actual_duration = delta.total_seconds() / 3600.0
            else:
                stop.actual_duration = 0.0

    @api.depends('planned_arrival', 'actual_arrival')
    def _compute_delay(self):
        for stop in self:
            if stop.planned_arrival and stop.actual_arrival:
                delta = stop.actual_arrival - stop.planned_arrival
                stop.delay_minutes = delta.total_seconds() / 60.0
            else:
                stop.delay_minutes = 0.0

    # -------------------------------------------------------------------------
    # COMPUTE: Schedule flag booleans
    # -------------------------------------------------------------------------
    @api.depends('planned_arrival', 'state')
    def _compute_schedule_flags(self):
        """Compute boolean flags for date-based search filters.

        Semantics (matching original XML domains):
        - scheduled_today: planned_arrival date == context today
        - scheduled_recent_7d (XML label 'This Week'): planned_arrival >= today - 7 days (rolling window)
        - scheduled_overdue: planned_arrival < today AND state in ['planned','in_transit'] (mapping from legacy pending/in_progress labels)
        """
        today = fields.Date.context_today(self)
        # Pre-calc boundaries
        recent_threshold = today - fields.Date.to_date(str(today)) + today  # placeholder; adjust below
        # Correct recent threshold: date subtraction using datetime / timedelta
        from datetime import timedelta
        recent_threshold = today - timedelta(days=7)
        for rec in self:
            rec_date = rec.planned_arrival.date() if rec.planned_arrival else None
            if rec_date:
                rec.scheduled_today = rec_date == today
                rec.scheduled_recent_7d = rec_date >= recent_threshold
                rec.scheduled_overdue = rec_date < today and rec.state in ['planned', 'in_transit']
            else:
                rec.scheduled_today = False
                rec.scheduled_recent_7d = False
                rec.scheduled_overdue = False

    # -------------------------------------------------------------------------
    # SEARCH HELPERS (Domains equivalent to legacy dynamic expressions)
    # -------------------------------------------------------------------------
    def _search_scheduled_today(self, operator, value):  # noqa: ARG002 (Odoo API signature)
        from datetime import timedelta
        today = fields.Date.context_today(self)
        start_dt = fields.Datetime.to_datetime(str(today))
        next_day = start_dt + timedelta(days=1)
        domain = [('planned_arrival', '>=', start_dt), ('planned_arrival', '<', next_day)]
        if (operator, value) in [('=', False), ('!=', True)]:
            domain = ['!', '&'] + domain  # invert logic
        return domain

    def _search_scheduled_recent_7d(self, operator, value):  # noqa: ARG002
        from datetime import timedelta
        today = fields.Date.context_today(self)
        threshold = fields.Datetime.to_datetime(str(today)) - timedelta(days=7)
        domain = [('planned_arrival', '>=', threshold)]
        if (operator, value) in [('=', False), ('!=', True)]:
            domain = ['!'] + domain
        return domain

    def _search_scheduled_overdue(self, operator, value):  # noqa: ARG002
        today = fields.Date.context_today(self)
        start_of_today = fields.Datetime.to_datetime(str(today))
        domain = ['&', ('planned_arrival', '<', start_of_today), ('state', 'in', ['planned', 'in_transit'])]
        if (operator, value) in [('=', False), ('!=', True)]:
            domain = ['!'] + domain
        return domain

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_in_transit(self):
        """Mark stop as in transit"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Can only mark planned stops as in transit."))

        self.write({"state": "in_transit"})
        self.message_post(body=_("Stop marked as in transit."))

    def action_mark_arrived(self):
        """Mark arrival at stop"""
        self.ensure_one()
        if self.state not in ["planned", "in_transit"]:
            raise UserError(_("Invalid state transition to arrived."))

        self.write({
            "state": "arrived", 
            "actual_arrival": fields.Datetime.now()
        })
        self.message_post(body=_("Arrived at stop."))

    def action_complete_stop(self):
        """Complete the stop"""
        self.ensure_one()
        if self.state != "arrived":
            raise UserError(_("Must arrive at stop before completing."))

        self.write({
            "state": "completed",
            "actual_departure": fields.Datetime.now(),
            "completion_status": "successful",
        })

        # Update associated pickup request
        if self.pickup_request_id and self.pickup_request_id.state != 'completed':
            self.pickup_request_id.action_complete()

        self.message_post(body=_("Stop completed successfully."))

    def action_skip_stop(self):
        """Skip this stop"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot skip completed stops."))

        self.write({"state": "skipped", "completion_status": "failed"})
        self.message_post(body=_("Stop skipped."))

    def action_reschedule_stop(self):
        """Reschedule this stop"""
        self.ensure_one()
        self.write({"state": "planned", "completion_status": "rescheduled"})
        self.message_post(body=_("Stop rescheduled."))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('planned_arrival', 'planned_departure')
    def _check_planned_times(self):
        for stop in self:
            if stop.planned_arrival and stop.planned_departure and stop.planned_arrival >= stop.planned_departure:
                raise ValidationError(_("Planned departure must be after arrival."))

    @api.constrains('actual_arrival', 'actual_departure')
    def _check_actual_times(self):
        for stop in self:
            if stop.actual_arrival and stop.actual_departure and stop.actual_arrival >= stop.actual_departure:
                raise ValidationError(_("Actual departure must be after arrival."))

    @api.constrains('gps_latitude')
    def _check_gps_latitude(self):
        for stop in self:
            if stop.gps_latitude and not (-90 <= stop.gps_latitude <= 90):
                raise ValidationError(_("GPS latitude must be between -90 and 90 degrees."))

    @api.constrains('gps_longitude')
    def _check_gps_longitude(self):
        for stop in self:
            if stop.gps_longitude and not (-180 <= stop.gps_longitude <= 180):
                raise ValidationError(_("GPS longitude must be between -180 and 180 degrees."))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('address') and vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                vals['address'] = partner._get_contact_address()
        return super().create(vals_list)
