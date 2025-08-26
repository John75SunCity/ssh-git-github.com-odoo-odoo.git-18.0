import json
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RouteOptimizer(models.Model):
    _name = 'route.optimizer'
    _description = 'Route Optimizer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'optimization_date desc, id desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Optimization Name", required=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
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
    optimization_date = fields.Date(string="Optimization Date", default=fields.Date.context_today, required=True, tracking=True)
    optimization_type = fields.Selection([
        ('distance', 'Shortest Distance'),
        ('time', 'Fastest Time'),
        ('cost', 'Lowest Cost'),
    ], string="Optimization Type", default='distance', required=True, tracking=True)
    max_routes = fields.Integer(string="Max Routes", default=10, help="Maximum number of routes to generate.")
    max_stops_per_route = fields.Integer(string="Max Stops per Route", default=20, help="Maximum number of stops allowed in a single route.")
    vehicle_capacity = fields.Float(string="Default Vehicle Capacity (m³)", default=15.0, help="Default capacity for vehicles if not specified on the vehicle itself.")
    starting_location = fields.Char(string="Starting Depot/Location", help="Address or name of the starting point for all routes.")
    pickup_request_ids = fields.Many2many('project.task', 'route_optimizer_fsm_order_rel', 'optimizer_id', 'order_id', string="Pickup Requests", domain="[('stage_id.is_closed', '=', False)]")

    # ============================================================================
    # EXECUTION & RESULTS
    # ============================================================================
    start_time = fields.Datetime(string="Start Time", readonly=True)
    completion_time = fields.Datetime(string="Completion Time", readonly=True)
    execution_time_seconds = fields.Integer(string="Execution Time (s)", compute='_compute_execution_time', store=True)
    optimization_results = fields.Text(string="Optimization Results (JSON)", readonly=True)
    routes_generated_count = fields.Integer(string="Routes Generated", compute='_compute_routes_generated_count', store=True)

    # ============================================================================
    # ANALYTICS & SAVINGS
    # ============================================================================
    total_distance = fields.Float(string="Total Optimized Distance (km)", readonly=True)
    total_time = fields.Float(string="Total Optimized Time (hours)", readonly=True)
    total_cost = fields.Monetary(string="Total Estimated Cost", currency_field='currency_id', readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id')
    efficiency_score = fields.Float(string="Efficiency Score (%)", compute='_compute_efficiency_score', store=True)
    distance_savings = fields.Float(string="Distance Savings (%)", readonly=True)
    time_savings = fields.Float(string="Time Savings (%)", readonly=True)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('max_routes', 'max_stops_per_route', 'vehicle_capacity')
    def _check_optimization_limits(self):
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
        for record in self:
            if record.start_time and record.completion_time:
                delta = record.completion_time - record.start_time
                record.execution_time_seconds = int(delta.total_seconds())
            else:
                record.execution_time_seconds = 0

    @api.depends('distance_savings', 'time_savings')
    def _compute_efficiency_score(self):
        for record in self:
            record.efficiency_score = (record.distance_savings + record.time_savings) / 2

    @api.depends('optimization_results')
    def _compute_routes_generated_count(self):
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
            self._perform_optimization()
            self.write({
                'status': 'completed',
                'completion_time': fields.Datetime.now()
            })
            self.message_post(body=_('Route optimization completed successfully.'))
        except Exception as e:
            self.write({'status': 'failed'})
            self.message_post(body=_('Route optimization failed: %s') % str(e))
            raise

    def action_apply_optimization(self):
        self.ensure_one()
        if self.status != 'completed':
            raise UserError(_('Can only apply completed optimizations.'))

        self._create_optimized_routes()
        self.write({'status': 'applied'})
        self.message_post(body=_('Optimization results applied - routes created.'))

    def action_cancel_optimization(self):
        self.ensure_one()
        if self.status in ('applied', 'cancelled'):
            raise UserError(_('Cannot cancel applied or already cancelled optimizations.'))
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Optimization cancelled.'))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _perform_optimization(self):
        """
        Placeholder for a real optimization algorithm.
        In a production environment, this would call an external API (like Google OR-Tools, OSRM)
        or use a sophisticated internal library to solve the Vehicle Routing Problem (VRP).
        """
        self.ensure_one()
        pickup_requests = self.pickup_request_ids

        # Simulate results for demonstration
        results = {
            'routes': [],
            'total_distance': 0,
            'total_time': 0,
            'optimization_method': self.optimization_type
        }

        # Simple simulation: create one route per 5 requests
        chunk_size = 5
        for i in range(0, len(pickup_requests), chunk_size):
            chunk = pickup_requests[i:i + chunk_size]
            route_data = {
                'route_number': (i // chunk_size) + 1,
                'stops': chunk.ids,
                'distance': 25.5 * len(chunk),  # Simulated
                'time': 2.5 * len(chunk),       # Simulated
            }
            results['routes'].append(route_data)
            results['total_distance'] += route_data['distance']
            results['total_time'] += route_data['time']

        self.write({
            'optimization_results': json.dumps(results, indent=2),
            'total_distance': results['total_distance'],
            'total_time': results['total_time'],
            'distance_savings': 15.0,  # Simulated 15% savings
            'time_savings': 12.0       # Simulated 12% savings
        })

    def _create_optimized_routes(self):
        """Create FSM routes from the stored optimization results."""
        self.ensure_one()
        if not self.optimization_results:
            return

        try:
            results = json.loads(self.optimization_results)
        except (json.JSONDecodeError, TypeError):
            raise UserError(_("Could not parse optimization results. Please re-run the optimization."))

        FsmRoute = self.env['fsm.route']
        FsmOrder = self.env['project.task']

        for route_data in results.get('routes', []):
            route = FsmRoute.create({
                'name': _('Optimized Route %s - %s') % (route_data['route_number'], self.optimization_date.strftime('%Y-%m-%d')),
                'date': self.optimization_date,
                'estimated_distance': route_data.get('distance', 0),
                'estimated_duration': route_data.get('time', 0),
                'state': 'draft',
            })

            pickup_ids = route_data.get('stops', [])
            if pickup_ids:
                orders = FsmOrder.browse(pickup_ids)
                orders.write({'fsm_route_id': route.id})
