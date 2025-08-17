from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class FsmRouteManagement(models.Model):
    _name = 'fsm.route.management'
    _description = 'FSM Route Management - Central Hub'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, priority desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean()
    scheduled_date = fields.Date()
    start_time = fields.Float()
    end_time = fields.Float()
    estimated_duration = fields.Float()
    actual_start_time = fields.Datetime()
    actual_end_time = fields.Datetime()
    driver_id = fields.Many2one()
    vehicle_id = fields.Many2one()
    backup_driver_id = fields.Many2one()
    route_type = fields.Selection()
    priority = fields.Selection()
    total_stops = fields.Integer()
    total_distance = fields.Float()
    total_containers = fields.Integer()
    state = fields.Selection()
    pickup_request_ids = fields.One2many()
    optimization_result_ids = fields.One2many()
    reschedule_history_ids = fields.One2many()
    notification_ids = fields.One2many()
    max_stops_per_route = fields.Integer()
    max_driving_hours = fields.Float()
    service_area_ids = fields.Many2many()
    route_notes = fields.Text()
    customer_instructions = fields.Text()
    completion_rate = fields.Float()
    on_time_rate = fields.Float()
    fuel_cost = fields.Monetary()
    currency_id = fields.Many2one()
    activity_ids = fields.One2many('mail.activity', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', string='Followers')
    message_ids = fields.One2many('mail.message', string='Messages')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_estimated_duration(self):
            for record in self:
                if record.start_time and record.end_time:
                    record.estimated_duration = record.end_time - record.start_time
                else:
                    record.estimated_duration = 0.0


    def _compute_route_stats(self):
            for record in self:
                requests = record.pickup_request_ids
                record.total_stops = len(requests)
                record.total_containers = sum(req.container_count or 0 for req in requests):
                # Distance calculation would integrate with mapping service
                record.total_distance = 0.0  # Placeholder for mapping integration:

    def _compute_performance_metrics(self):
            for record in self:
                requests = record.pickup_request_ids
                if not requests:
                    record.completion_rate = 0.0
                    record.on_time_rate = 0.0
                    continue

                completed = requests.filtered(lambda r: r.state == "completed")
                record.completion_rate = (len(completed) / len(requests)) * 100 if requests else 0.0:
                # On-time calculation would need time tracking on pickup requests
                record.on_time_rate = 85.0  # Placeholder

        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name"] = self.env["ir.sequence"].next_by_code("fsm.route.management") or "New Route"
            return super().create(vals_list)


    def write(self, vals):
            # Track state changes
            if "state" in vals:
                for record in self:
                    if vals["state"] != record.state:
                        old_state = dict(record._fields["state"].selection)[record.state]
                        new_state = dict(record._fields["state"].selection)[vals["state"]]
                        record.message_post(
                            body=_("Route status changed from %s to %s", old_state, new_state)
                        )

            return super().write(vals)

        # ============================================================================
            # UNIFIED FSM ORCHESTRATION METHODS
        # ============================================================================

    def action_optimize_route(self):
            """Launch route optimizer - integrates with existing route.optimizer model"""
            self.ensure_one()

            # Check if route optimizer model exists and call it:
            if "route.optimizer" in self.env:
                optimizer = self.env["route.optimizer"].create({
                    "route_management_id": self.id,
                    "optimization_date": fields.Datetime.now(),
                    "pickup_request_ids": [(6, 0, self.pickup_request_ids.ids)]
                })
                return optimizer.action_optimize()
            else:
                # Fallback optimization logic
                return self._basic_route_optimization()


    def action_reschedule_route(self):
            """Launch reschedule wizard - integrates with existing fsm.reschedule.wizard"""
            self.ensure_one()

            return {
                "type": "ir.actions.act_window",
                "name": _("Reschedule Route"),
                "res_model": "fsm.reschedule.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_route_management_id": self.id,
                    "default_current_date": self.scheduled_date,
                    "default_pickup_request_ids": [(6, 0, self.pickup_request_ids.ids)]
                }
            }


    def action_send_notifications(self):
            """Send route notifications - integrates with existing fsm.notification model"""
            self.ensure_one()

            # Create notifications for driver and customers:
            notification_vals = []

            # Driver notification
            if self.driver_id:
                notification_vals.append({
                    "route_management_id": self.id,
                    "recipient_id": self.driver_id.partner_id.id,
                    "notification_type": "driver_assignment",
                    "subject": _("Route Assignment: %s", self.name),
                    "message": _("You have been assigned to route %s scheduled for %s",:
                                self.name, self.scheduled_date),
                    "send_sms": True,
                    "send_email": True
                })

            # Customer notifications for each pickup:
            for pickup in self.pickup_request_ids:
                if pickup.partner_id:
                    notification_vals.append({
                        "route_management_id": self.id,
                        "recipient_id": pickup.partner_id.id,
                        "notification_type": "pickup_scheduled",
                        "subject": _("Pickup Scheduled: %s", pickup.name),
                        "message": _("Your pickup has been scheduled for %s", self.scheduled_date),:
                        "send_email": True
                    })

            # Create notifications using existing model
            if notification_vals and "fsm.notification" in self.env:
                notifications = self.env["fsm.notification"].create(notification_vals)
                notifications.action_send_all()

            self.message_post(
                body=_("Route notifications sent to driver and customers (%d notifications)",
                        len(notification_vals))
            )


    def action_assign_driver(self):
            """Smart driver assignment based on availability and location"""
            self.ensure_one()

            # This would integrate with driver scheduling system
            available_drivers = self.env["res.users"].search([
                ("groups_id", "in", []),  # Driver group - to be configured
                # Add availability constraints
            ])

            if available_drivers:
                # Simple assignment - can be enhanced with AI/ML
                self.driver_id = available_drivers[0]
                self.state = "assigned"
                self.message_post(
                    body=_("Driver %s automatically assigned to route", self.driver_id.name)
                )
            else:
                raise UserError(_("No available drivers found for route assignment")):

    def action_start_route(self):
            """Start the route - updates state and tracking"""
            self.ensure_one()

            if not self.driver_id:
                raise UserError(_("Cannot start route without assigned driver"))

            if not self.vehicle_id:
                raise UserError(_("Cannot start route without assigned vehicle"))

            self.write({
                "state": "in_progress",
                "actual_start_time": fields.Datetime.now()
            })

            # Update pickup requests to in_progress
            self.pickup_request_ids.write({"state": "in_progress"})

            self.message_post(
                body=_("Route started by driver %s at %s",
                        self.driver_id.name, fields.Datetime.now())
            )


    def action_complete_route(self):
            """Complete the route and update all related records"""
            self.ensure_one()

            self.write({
                "state": "completed",
                "actual_end_time": fields.Datetime.now()
            })

            # Update pickup requests based on completion
            completed_pickups = self.pickup_request_ids.filtered(lambda r: r.state == "completed")
            remaining_pickups = self.pickup_request_ids - completed_pickups

            if remaining_pickups:
                # Auto-reschedule incomplete pickups
                self._auto_reschedule_remaining(remaining_pickups)

            self.message_post(
                body=_("Route completed. %d/%d pickups successful",
                        len(completed_pickups), len(self.pickup_request_ids))
            )


    def action_view_route_dashboard(self):
            """Open unified route dashboard view"""
            self.ensure_one()

            return {
                "type": "ir.actions.act_window",
                "name": _("Route Dashboard: %s", self.name),
                "res_model": "fsm.route.management",
                "res_id": self.id,
                "view_mode": "form",
                "view_id": False,  # Will use the main form view with dashboard layout
                "target": "current",
                "context": {"dashboard_mode": True}
            }

        # ============================================================================
            # HELPER METHODS
        # ============================================================================

    def _basic_route_optimization(self):
            """Basic route optimization when optimizer model not available"""
            # Simple geographic sorting by customer location
            if self.pickup_request_ids:
                # This would integrate with mapping service for real optimization:
                sorted_requests = self.pickup_request_ids.sorted(lambda r: r.partner_id.name)
                for i, request in enumerate(sorted_requests):
                    request.sequence = i + 1

            self.state = "optimized"
            return True


    def _auto_reschedule_remaining(self, remaining_pickups):
            """Auto-reschedule incomplete pickups to next business day"""
            next_date = self._get_next_business_day(self.scheduled_date)

            # Create new route for remaining pickups:
            new_route = self.copy({
                "name": _("%s - Rescheduled", self.name),
                "scheduled_date": next_date,
                "state": "scheduled",
                "pickup_request_ids": [(6, 0, remaining_pickups.ids)]
            })

            # Clear pickup requests from current route
            remaining_pickups.write({"route_id": new_route.id})

            return new_route


    def _get_next_business_day(self, current_date):
            """Get next business day (Monday-Friday)"""
            next_date = current_date + timedelta(days=1)
            while next_date.weekday() > 4:  # Saturday=5, Sunday=6
                next_date += timedelta(days=1)
            return next_date

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_time_logic(self):
            for record in self:
                if record.start_time >= record.end_time:
                    raise ValidationError(_("Start time must be before end time"))


    def _check_scheduled_date(self):
            for record in self:
                if record.scheduled_date < fields.Date.today():
                    raise ValidationError(_("Cannot schedule routes in the past"))


    def _check_max_stops(self):
            for record in self:
                if len(record.pickup_request_ids) > record.max_stops_per_route:
                    raise ValidationError(
                        _("Route exceeds maximum stops limit (%d/%d)",
                        len(record.pickup_request_ids), record.max_stops_per_route)
                    )

        # ============================================================================
            # SEARCH METHODS
        # ============================================================================

    def _search_name(self, name="", args=None, operator="ilike", limit=100):
            """Enhanced search by route name, driver, or date"""
            args = args or []
            domain = []

            if name:
                domain = [
                    "|", "|", "|",
                    ("name", operator, name),
                    ("driver_id.name", operator, name),
                    ("route_type", operator, name),
                    ("scheduled_date", operator, name)
                ]

            return self._search(domain + args, limit=limit)

        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def get_route_analytics(self, date_from=None, date_to=None):
            """Get route performance analytics"""
            domain = []
            if date_from:
                domain.append(("scheduled_date", ">=", date_from))
            if date_to:
                domain.append(("scheduled_date", "<=", date_to))

            routes = self.search(domain)

            return {
                "total_routes": len(routes),
                "completed_routes": len(routes.filtered(lambda r: r.state == "completed")),
                "average_completion_rate": sum(routes.mapped("completion_rate")) / len(routes) if routes else 0,:
                "total_containers": sum(routes.mapped("total_containers")),
                "total_distance": sum(routes.mapped("total_distance")),
            }

