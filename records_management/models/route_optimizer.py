import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RouteOptimizer(models.Model):
    """
    The RouteOptimizer model is responsible for managing and optimizing delivery or pickup routes.
    It provides functionality to define optimization parameters, execute optimization algorithms,
    and generate optimized routes based on selected criteria such as distance, time, or cost.

    Key Features:
    - Define optimization parameters like max routes, stops per route, and vehicle capacity.
    - Execute optimization algorithms and store results in JSON format.
    - Generate and manage optimized routes, including assigning pickup requests.
    - Track analytics such as total distance, time, cost, and efficiency scores.
    - Provide actions to run, apply, cancel, or reset optimizations.
    """

    _name = 'route.optimizer'
    _description = 'Route Optimizer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'optimization_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Optimization Name", required=True, default=lambda self: _('New'))
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        readonly=True
    )
    active = fields.Boolean(default=True)
    status = fields.Selection([
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('applied', 'Applied'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # OPTIMIZATION PARAMETERS
    # ============================================================================
    optimization_date = fields.Date(
        string="Optimization Date",
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    optimization_type = fields.Selection([
        ('distance', 'Shortest Distance'),
        ('time', 'Fastest Time'),
        ('cost', 'Lowest Cost'),
    ], string="Optimization Type", default='distance', required=True, tracking=True)
    max_routes = fields.Integer(
        string="Max Routes",
        default=10,
        help="Maximum number of routes to generate."
    )
    max_stops_per_route = fields.Integer(
        string="Max Stops per Route",
        default=20,
        help="Maximum number of stops allowed in a single route."
    )
    vehicle_capacity = fields.Float(
        string="Default Vehicle Capacity (m³)",
        default=15.0,
        help="Default capacity for vehicles if not specified on the vehicle itself."
    )
    starting_location = fields.Char(
        string="Starting Depot/Location",
        help="Address or name of the starting point for all routes."
    )
    pickup_request_ids = fields.Many2many(
        comodel_name='project.task',
        relation='route_optimizer_fsm_order_rel',
        column1='optimizer_id',
        column2='order_id',
        string="Pickup Requests",
        domain="[('stage_id.is_closed', '=', False)]"
    )

    # ============================================================================
    # EXECUTION & RESULTS
    # ============================================================================
    start_time = fields.Datetime(string="Start Time", readonly=True)
    completion_time = fields.Datetime(string="Completion Time", readonly=True)
    execution_time_seconds = fields.Integer(
        string="Execution Time (s)",
        compute='_compute_execution_time',
        store=True
    )
    optimization_results = fields.Text(string="Optimization Results (JSON)", readonly=True)
    routes_generated_count = fields.Integer(
        string="Routes Generated",
        compute='_compute_routes_generated_count',
        store=True
    )

    # ============================================================================
    # ANALYTICS & SAVINGS
    # ============================================================================
    total_distance = fields.Float(string="Total Optimized Distance (km)", readonly=True)
    total_time = fields.Float(string="Total Optimized Time (hours)", readonly=True)
    total_cost = fields.Monetary(
        string="Total Estimated Cost",
        currency_field='currency_id',
        readonly=True
    )
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='company_id.currency_id'
    )
    efficiency_score = fields.Float(
        string="Efficiency Score (%)",
        compute='_compute_efficiency_score',
        store=True
    )
    distance_savings = fields.Float(string="Distance Savings (%)", readonly=True)
    time_savings = fields.Float(string="Time Savings (%)", readonly=True)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('max_routes', 'max_stops_per_route', 'vehicle_capacity')
    def _check_optimization_limits(self):
        """
        Validates that the optimization parameters are greater than zero.
        Raises:
            ValidationError: If any parameter is less than or equal to zero.
        """
        for record in self:
            if record.max_routes <= 0:
                raise ValidationError(_('Maximum routes must be greater than 0.'))
            if record.max_stops_per_route <= 0:
                raise ValidationError(_('Maximum stops per route must be greater than 0.'))
            if record.vehicle_capacity <= 0:
                raise ValidationError(_('Vehicle capacity must be greater than 0.'))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('start_time', 'completion_time')
    def _compute_execution_time(self):
        """
        Computes the execution time of the optimization in seconds.
        If either start_time or completion_time is missing, the execution time is set to zero.
        """
        for record in self:
            if record.start_time and record.completion_time:
                delta = record.completion_time - record.start_time
                record.execution_time_seconds = int(delta.total_seconds())
            else:
                record.execution_time_seconds = 0

    @api.depends('distance_savings', 'time_savings')
    def _compute_efficiency_score(self):
        """
        Computes the efficiency score as the average of distance savings and time savings.
        """
        for record in self:
            record.efficiency_score = (record.distance_savings + record.time_savings) / 2

    @api.depends('optimization_results')
    def _compute_routes_generated_count(self):
        """
        Computes the number of routes generated based on the optimization results.
        Parses the JSON results to count the number of routes.
        """
        for record in self:
            if record.optimization_results:
                try:
                    results = json.loads(record.optimization_results)
                    record.routes_generated_count = len(results.get('routes', []))
                except (json.JSONDecodeError, TypeError):
                    record.routes_generated_count = 0
            else:
                record.routes_generated_count = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_run_optimization(self):
        """
        Initiates the route optimization process.
        - Validates that the record is in draft status and has pickup requests.
        - Updates the status to 'running' and records the start time.
        - Executes the optimization algorithm and updates the status to 'completed' upon success.
        Raises:
            UserError: If the record is not in draft status or has no pickup requests.
        """
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only run optimization on draft records.'))
        if not self.pickup_request_ids:
            raise UserError(_('Please select pickup requests to optimize.'))

        self.write({
            'status': 'running',
            'start_time': fields.Datetime.now()
        })
        self.message_post(body=_('Route optimization started...'))

        try:
            self.action_perform_optimization()
            self.write({
                'status': 'completed',
                'completion_time': fields.Datetime.now()
            })
            self.message_post(body=_('Route optimization completed successfully.'))
        except Exception as exc:
            self.write({'status': 'failed'})
            self.message_post(body=_("Route optimization failed: %s", str(exc)))
            raise UserError(_("Optimization failed: %s", str(exc)))

    def action_apply_optimization(self):
        """
        Applies the optimization results by creating pickup routes.
        - Validates that the optimization is completed.
        - Parses the optimization results and creates routes and assigns pickup requests.
        Raises:
            UserError: If the optimization is not completed or results cannot be parsed.
        """
        self.ensure_one()
        if self.status != 'completed':
            raise UserError(_('Can only apply completed optimizations.'))

        try:
            self._create_optimized_routes()
            self.write({'status': 'applied'})
            self.message_post(body=_('Optimization results applied - routes created.'))
        except Exception as exc:
            raise UserError(_("Failed to apply optimization: %s", str(exc)))

    def action_cancel_optimization(self):
        """
        Cancels the optimization process.
        - Updates the status to 'cancelled'.
        - Prevents cancellation if the optimization is already applied or cancelled.
        Raises:
            UserError: If the optimization is already applied or cancelled.
        """
        self.ensure_one()
        if self.status in ('applied', 'cancelled'):
            raise UserError(_('Cannot cancel applied or already cancelled optimizations.'))
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Optimization cancelled.'))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_perform_optimization(self):
        """
        Executes the optimization algorithm to generate routes.
        - Simulates route generation for demonstration purposes.
        - Calculates total distance, time, and estimated cost.
        - Stores the results in JSON format.
        Raises:
            UserError: If no pickup requests are selected.
        """
        self.ensure_one()
        pickup_requests = self.pickup_request_ids

        if not pickup_requests:
            raise UserError(_('No pickup requests selected for optimization.'))

        # Simulate results for demonstration
        results = {
            'routes': [],
            'total_distance': 0,
            'total_time': 0,
            'optimization_method': self.optimization_type
        }

        # Simple simulation: create one route per 5 requests
        chunk_size = min(self.max_stops_per_route, 5)
        request_count = len(pickup_requests)

        for i in range(0, request_count, chunk_size):
            chunk = pickup_requests[i:i + chunk_size]
            route_number = (i // chunk_size) + 1

            # Break if we've reached max routes
            if route_number > self.max_routes:
                break

            route_data = {
                'route_number': route_number,
                'stops': chunk.ids,
                'distance': 25.5 * len(chunk),  # Simulated distance per stop
                'time': 2.5 * len(chunk),       # Simulated time per stop
            }
            results['routes'].append(route_data)
            results['total_distance'] += route_data['distance']
            results['total_time'] += route_data['time']

        # Calculate estimated cost based on distance
        estimated_cost = results['total_distance'] * 2.5  # $2.50 per km

        self.write({
            'optimization_results': json.dumps(results, indent=2),
            'total_distance': results['total_distance'],
            'total_time': results['total_time'],
            'total_cost': estimated_cost,
            'distance_savings': 15.0,  # Simulated 15% savings
            'time_savings': 12.0       # Simulated 12% savings
        })

    def _create_optimized_routes(self):
        """
        Creates pickup routes based on the stored optimization results.
        - Parses the JSON results and creates routes in the system.
        - Assigns pickup requests to the created routes.
        - Rolls back created routes if an error occurs during the process.
        Raises:
            UserError: If results cannot be parsed or route creation fails.
        """
        self.ensure_one()
        if not self.optimization_results:
            raise UserError(_('No optimization results available to apply.'))

        try:
            results = json.loads(self.optimization_results)
        except (json.JSONDecodeError, TypeError) as exc:
            raise UserError(_("Could not parse optimization results. Please re-run the optimization.")) from exc

        PickupRoute = self.env['pickup.route']
        PickupRequest = self.env['project.task']

        created_routes = []

        for route_data in results.get('routes', []):
            try:
                route_name = _('Optimized Route %s - %s',
                    route_data['route_number'],
                    self.optimization_date.strftime('%Y-%m-%d')
                )

                route = PickupRoute.create({
                    'name': route_name,
                    'route_date': self.optimization_date,
                    'total_distance': route_data.get('distance', 0),
                    'estimated_duration': route_data.get('time', 0),
                    'state': 'draft',
                    'optimization_id': self.id,
                })

                created_routes.append(route)

                # Assign pickup requests to the route
                pickup_ids = route_data.get('stops', [])
                if pickup_ids:
                    requests = PickupRequest.browse(pickup_ids)
                    # Update the requests to reference this route
                    requests.write({'pickup_route_id': route.id})

            except Exception as exc:
                # Clean up any routes created so far
                for created_route in created_routes:
                    created_route.unlink()
                raise UserError(_('Failed to create route %s: %s',
                    route_data.get('route_number', 'Unknown'), str(exc)
                )) from exc

        if created_routes:
            self.message_post(body=_("Created %s optimized routes successfully.", len(created_routes)))
        else:
            raise UserError(_('No routes were created from optimization results.'))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def action_view_created_routes(self):
        """
        Opens a view displaying the routes created from the optimization.
        Returns:
            dict: An action dictionary to open the routes in a tree and form view.
        """
        self.ensure_one()

        routes = self.env['pickup.route'].search([('optimization_id', '=', self.id)])

        return {
            'type': 'ir.actions.act_window',
            'name': _('Optimized Routes'),
            'res_model': 'pickup.route',
            'view_mode': 'tree,form',
            'domain': [('optimization_id', '=', self.id)],
            'context': {
                'default_optimization_id': self.id,
                'search_default_group_by_state': 1,
            }
        }

    def action_reset_to_draft(self):
        """
        Resets the optimization record to draft state.
        - Clears all results and resets analytics fields.
        - Prevents reset if the optimization is applied and routes exist.
        Raises:
            UserError: If routes exist for an applied optimization.
        """
        self.ensure_one()
        if self.status == 'applied':
            # Check if there are routes that need to be handled
            routes = self.env['pickup.route'].search([('optimization_id', '=', self.id)])
            if routes:
                raise UserError(_('Cannot reset to draft: optimization has been applied and routes exist. Please delete the routes first.'))

        self.write({
            'status': 'draft',
            'start_time': False,
            'completion_time': False,
            'optimization_results': False,
            'total_distance': 0,
            'total_time': 0,
            'total_cost': 0,
            'distance_savings': 0,
            'time_savings': 0,
        })
        self.message_post(body=_('Optimization reset to draft state.'))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """
        Overrides the create method to assign a sequence to the 'name' field.
        Args:
            vals_list (list): List of dictionaries containing field values for new records.
        Returns:
            recordset: The created records.
        """
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence_code = 'route.optimizer'
                vals['name'] = self.env['ir.sequence'].next_by_code(sequence_code) or _('New')

        return super().create(vals_list)

    def unlink(self):
        """
        Overrides the unlink method to prevent deletion of applied optimizations with existing routes.
        Raises:
            UserError: If routes exist for an applied optimization.
        """
        for record in self:
            if record.status == 'applied':
                routes = self.env['pickup.route'].search([('optimization_id', '=', record.id)])
                if routes:
                    raise UserError(_('Cannot delete applied optimization with existing routes. Please delete the routes first.'))
        return super().unlink()
