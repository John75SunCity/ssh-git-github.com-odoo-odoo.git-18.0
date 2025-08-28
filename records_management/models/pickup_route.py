from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class PickupRoute(models.Model):
    """
    Records Management Pickup Route

    Specialized route management for records pickup operations.
    Integrates with FSM (project.task) for standard task management while
    maintaining specialized route optimization and pickup logic.

    Architecture:
    - pickup.route: Route planning, optimization, stops management
    - project.task: FSM task for each route (created automatically)
    - This provides both specialized route logic + standard Odoo FSM workflows
    """
    _name = 'pickup.route'
    _description = 'Pickup Route Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE FIELDS (Enhanced with FSM Integration)
    # ============================================================================
    name = fields.Char(string='Route Name', required=True, default='New')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Route Driver', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)

    # Enhanced date/time management leveraging FSM scheduling
    route_date = fields.Date(string='Route Date', required=True, default=fields.Date.today)
    planned_start_time = fields.Datetime(string='Planned Start Time')
    planned_end_time = fields.Datetime(string='Planned End Time')
    actual_start_time = fields.Datetime(string='Actual Start Time')
    actual_end_time = fields.Datetime(string='Actual End Time')

    # Leverage fleet.vehicle (already updated)
    vehicle_id = fields.Many2one('fleet.vehicle', string='Vehicle')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')

    # ============================================================================
    # FSM INTEGRATION - Link to project.task for standard workflows
    # ============================================================================
    fsm_task_id = fields.Many2one(
        'project.task',
        string='FSM Task',
        help='Automatically created FSM task for this route',
        readonly=True,
        copy=False
    )

    # Related FSM fields for convenience
    fsm_state = fields.Char(
        related='fsm_task_id.stage_id.name',
        string='FSM Status',
        store=True,
        readonly=True
    )

    fsm_project_id = fields.Many2one(
        related='fsm_task_id.project_id',
        string='FSM Project',
        store=True,
        readonly=True
    )

    # ============================================================================
    # SPECIALIZED ROUTE FIELDS (Records business logic)
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')
    pickup_request_ids = fields.One2many('pickup.request', 'route_id', string='Pickup Requests')
    route_stop_ids = fields.One2many('pickup.route.stop', 'route_id', string='Route Stops')
    total_distance = fields.Float(string='Total Distance (km)', compute='_compute_route_metrics', store=True)
    estimated_duration = fields.Float(string='Estimated Duration (hours)', compute='_compute_route_metrics', store=True)
    actual_duration = fields.Float(string='Actual Duration (hours)', compute='_compute_actual_duration', store=True)
    fuel_cost = fields.Monetary(string='Fuel Cost', compute='_compute_costs', store=True)
    total_cost = fields.Monetary(string='Total Cost', compute='_compute_costs', store=True)
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    request_count = fields.Integer(string='Request Count', compute='_compute_request_count')
    completion_percentage = fields.Float(string='Completion %', compute='_compute_completion_percentage')
    efficiency_score = fields.Float(string='Efficiency Score', compute='_compute_efficiency_score')
    notes = fields.Text(string='Route Notes')
    special_instructions = fields.Text(string='Special Instructions')

    # ============================================================================
    # CONSOLIDATED FIELDS (migrated from fsm.route.management)
    # ============================================================================
    route_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('mixed', 'Mixed')
    ], string='Route Type', default='pickup')

    max_stops_per_route = fields.Integer(string='Max Stops', default=50)
    max_driving_hours = fields.Float(string='Max Driving Hours', default=8.0)

    service_area_ids = fields.Many2many('res.country.state', string='Service Areas')
    customer_instructions = fields.Text(string='Customer Instructions')

    backup_driver_id = fields.Many2one('res.users', string='Backup Driver')

    # Remove all the incorrect field definitions and keep only proper computed fields
    container_count = fields.Integer(string='Container Count', compute='_compute_container_count')
    pickup_count = fields.Integer(string='Pickup Count', compute='_compute_pickup_count')
    total_stops = fields.Integer(string='Total Stops', compute='_compute_total_stops')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('pickup_request_ids')
    def _compute_container_count(self):
        for record in self:
            # Assuming containers are linked through pickup requests
            container_count = 0
            for request in record.pickup_request_ids:
                if hasattr(request, 'container_ids'):
                    container_count += len(request.container_ids)
            record.container_count = container_count

    @api.depends('pickup_request_ids')
    def _compute_pickup_count(self):
        for record in self:
            record.pickup_count = len(record.pickup_request_ids)

    @api.depends('route_stop_ids')
    def _compute_total_stops(self):
        for record in self:
            record.total_stops = len(record.route_stop_ids)

    @api.depends('pickup_request_ids')
    def _compute_request_count(self):
        for route in self:
            route.request_count = len(route.pickup_request_ids)

    @api.depends('route_stop_ids.distance')
    def _compute_route_metrics(self):
        for route in self:
            total_distance = sum(route.route_stop_ids.mapped("distance"))
            route.total_distance = total_distance

            # Estimate duration based on distance and average speed
            average_speed = 40  # km/hour
            if total_distance > 0:
                route.estimated_duration = total_distance / average_speed
            else:
                route.estimated_duration = 0.0

    @api.depends('actual_start_time', 'actual_end_time')
    def _compute_actual_duration(self):
        for route in self:
            if route.actual_start_time and route.actual_end_time:
                delta = route.actual_end_time - route.actual_start_time
                route.actual_duration = delta.total_seconds() / 3600.0  # Convert to hours
            else:
                route.actual_duration = 0.0

    @api.depends('total_distance', 'vehicle_id')
    def _compute_costs(self):
        for route in self:
            fuel_cost = 0.0
            if route.total_distance and route.vehicle_id:
                # Example calculation - adjust based on actual vehicle fuel efficiency
                fuel_per_km = 0.08  # 8 liters per 100km = 0.08 L/km
                fuel_price = 1.50   # Price per liter
                fuel_cost = route.total_distance * fuel_per_km * fuel_price

            route.fuel_cost = fuel_cost
            route.total_cost = fuel_cost  # Add other costs as needed

    @api.depends('pickup_request_ids.state')
    def _compute_completion_percentage(self):
        for route in self:
            if not route.pickup_request_ids:
                route.completion_percentage = 0.0
                continue

            completed_requests = route.pickup_request_ids.filtered(
                lambda r: r.state in ["completed", "delivered"]
            )

            total_requests = len(route.pickup_request_ids)
            route.completion_percentage = (len(completed_requests) / total_requests) * 100

    @api.depends('estimated_duration', 'actual_duration', 'completion_percentage')
    def _compute_efficiency_score(self):
        for route in self:
            score = 0.0
            if route.estimated_duration > 0 and route.actual_duration > 0:
                # Time efficiency (50% weight)
                time_efficiency = min(route.estimated_duration / route.actual_duration, 1.0) * 50

                # Completion efficiency (50% weight)
                completion_efficiency = route.completion_percentage * 0.5

                score = time_efficiency + completion_efficiency

            route.efficiency_score = min(score, 100.0)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_plan_route(self):
        """Plan the route and set to planned state"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only plan draft routes"))

        if not self.pickup_request_ids:
            raise UserError(_("Cannot plan route without pickup requests"))

        # Auto-generate route stops based on pickup requests
        self._generate_route_stops()

        self.write({"state": "planned"})
        self.message_post(body=_("Route planned with %s stops") % len(self.route_stop_ids))

    def action_start_route(self):
        """Start route execution"""
        self.ensure_one()
        if self.state != "planned":
            raise UserError(_("Can only start planned routes"))

        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now()
        })
        self.message_post(body=_("Route started by %s") % self.env.user.name)

    def action_complete_route(self):
        """Complete the route"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Can only complete routes in progress"))

        # Check if all requests are completed
        incomplete_requests = self.pickup_request_ids.filtered(
            lambda r: r.state not in ["completed", "delivered", "cancelled"]
        )

        if incomplete_requests:
            raise UserError(_(
                "Cannot complete route with incomplete requests: %s",
                ", ".join(incomplete_requests.mapped("name"))
            ))

        self.write({
            "state": "completed",
            "actual_end_time": fields.Datetime.now()
        })
        self.message_post(body=_("Route completed"))

    def action_cancel_route(self):
        """Cancel the route"""
        self.ensure_one()
        if self.state in ["completed"]:
            raise UserError(_("Cannot cancel completed routes"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Route cancelled"))

    def action_view_pickup_requests(self):
        """View pickup requests for this route"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Pickup Requests'),
            'res_model': 'pickup.request',
            'view_mode': 'tree,form',
            'domain': [('route_id', '=', self.id)],
            'context': {'default_route_id': self.id}
        }

    def action_optimize_route(self):
        """Optimize route order for efficiency"""
        self.ensure_one()
        self._optimize_stop_order()
        return True

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _generate_route_stops(self):
        """Generate route stops based on pickup requests"""
        self.ensure_one()
        # Clear existing stops
        self.route_stop_ids.unlink()

        # Create stops from pickup requests
        for request in self.pickup_request_ids:
            self.env['pickup.route.stop'].create({
                'route_id': self.id,
                'pickup_request_id': request.id,
                'sequence': len(self.route_stop_ids) + 1,
                'location': request.pickup_address,
            })

    def _optimize_stop_order(self):
        """Optimize the order of route stops"""
        self.ensure_one()
        # Simple optimization - sort by distance or address
        # In a real implementation, you would use a proper routing algorithm
        stops = self.route_stop_ids.sorted('sequence')
        for index, stop in enumerate(stops):
            stop.sequence = index + 1

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('actual_start_time', 'actual_end_time')
    def _check_actual_times(self):
        for route in self:
            if route.actual_start_time and route.actual_end_time:
                if route.actual_start_time >= route.actual_end_time:
                    raise ValidationError(_("Actual end time must be after start time"))

    @api.constrains('pickup_request_ids')
    def _check_pickup_requests_same_date(self):
        for route in self:
            if route.pickup_request_ids:
                request_dates = route.pickup_request_ids.mapped("pickup_date")
                if len(set(request_dates)) > 1:
                    raise ValidationError(_(
                        "All pickup requests on a route must have the same pickup date"
                    ))

    # ============================================================================
    # ORM METHODS (Enhanced with FSM Integration)
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", "New") == "New":
                vals["name"] = self.env["ir.sequence"].next_by_code("pickup.route") or "New"

        routes = super().create(vals_list)

        # Auto-create FSM tasks for each route
        for route in routes:
            route._create_fsm_task()

        return routes

    def write(self, vals):
        result = super().write(vals)

        # Sync important changes to FSM task
        if any(field in vals for field in ['name', 'route_date', 'user_id', 'planned_start_time', 'planned_end_time', 'state']):
            for route in self:
                if route.fsm_task_id:
                    route._sync_to_fsm_task()

        return result

    # ============================================================================
    # FSM INTEGRATION METHODS
    # ============================================================================
    def _create_fsm_task(self):
        """Create corresponding FSM task for route management."""
        self.ensure_one()

        if self.fsm_task_id:
            return  # Already has FSM task

        # Find or create FSM project for routes
        fsm_project = self._get_or_create_fsm_project()

        # Create FSM task
        task_vals = {
            'name': f"Pickup Route: {self.name}",
            'project_id': fsm_project.id,
            'user_ids': [(6, 0, [self.user_id.id])] if self.user_id else [],
            'date_start': self.planned_start_time,
            'date_end': self.planned_end_time,
            'partner_id': self.route_stop_ids[0].partner_id.id if self.route_stop_ids else False,
            'description': f"""
                Pickup Route Details:
                - Route Date: {self.route_date}
                - Vehicle: {self.vehicle_id.license_plate if self.vehicle_id else 'TBD'}
                - Stops: {len(self.route_stop_ids)}
                - Notes: {self.notes or 'No special notes'}
            """,
            'is_fsm': True,  # Mark as field service task
        }

        fsm_task = self.env['project.task'].create(task_vals)
        self.write({'fsm_task_id': fsm_task.id})

        return fsm_task

    def _sync_to_fsm_task(self):
        """Sync route changes to FSM task."""
        self.ensure_one()

        if not self.fsm_task_id:
            return

        sync_vals = {
            'name': f"Pickup Route: {self.name}",
            'date_start': self.planned_start_time,
            'date_end': self.planned_end_time,
        }

        # Sync state changes
        if self.state == 'in_progress':
            # Find "In Progress" stage
            stage = self.env['project.task.type'].search([
                ('project_ids', 'in', self.fsm_task_id.project_id.id),
                ('name', 'ilike', 'progress')
            ], limit=1)
            if stage:
                sync_vals['stage_id'] = stage.id
        elif self.state == 'completed':
            # Find "Done" stage
            stage = self.env['project.task.type'].search([
                ('project_ids', 'in', self.fsm_task_id.project_id.id),
                ('fold', '=', True)  # Done stages are typically folded
            ], limit=1)
            if stage:
                sync_vals['stage_id'] = stage.id

        self.fsm_task_id.write(sync_vals)

    def _get_or_create_fsm_project(self):
        """Get or create FSM project for pickup routes."""
        project = self.env['project.project'].search([
            ('name', '=', 'Records Pickup Routes'),
            ('is_fsm', '=', True)
        ], limit=1)

        if not project:
            project = self.env['project.project'].create({
                'name': 'Records Pickup Routes',
                'is_fsm': True,
                'allow_task_dependencies': True,
                'company_id': self.company_id.id,
            })

        return project

    def action_view_fsm_task(self):
        """Open the related FSM task."""
        self.ensure_one()

        if not self.fsm_task_id:
            self._create_fsm_task()

        return {
            'type': 'ir.actions.act_window',
            'name': 'FSM Task',
            'res_model': 'project.task',
            'res_id': self.fsm_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # BUSINESS LOGIC HELPERS (consolidated from fsm.route.management)
    # ============================================================================
    def _get_next_business_day(self, current_date):
        """Get next business day (Monday-Friday)"""
        from datetime import timedelta
        next_date = current_date + timedelta(days=1)
        while next_date.weekday() > 4:  # Saturday=5, Sunday=6
            next_date += timedelta(days=1)
        return next_date

    # ============================================================================
    # CONSTRAINTS (enhanced from fsm.route.management)
    # ============================================================================
    @api.constrains('planned_start_time', 'planned_end_time')
    def _check_time_logic(self):
        for record in self:
            if (record.planned_start_time and record.planned_end_time and
                record.planned_start_time >= record.planned_end_time):
                raise ValidationError(_("Start time must be before end time."))

    @api.constrains('route_date')
    def _check_route_date(self):
        for record in self:
            if record.route_date and record.route_date < fields.Date.today():
                raise ValidationError(_("Cannot schedule routes in the past."))

    @api.constrains('pickup_request_ids')
    def _check_max_stops(self):
        for record in self:
            if len(record.pickup_request_ids) > record.max_stops_per_route:
                raise ValidationError(
                    _("Route exceeds maximum stops limit (%s/%s)") % (
                        len(record.pickup_request_ids), record.max_stops_per_route
                    )
                )
