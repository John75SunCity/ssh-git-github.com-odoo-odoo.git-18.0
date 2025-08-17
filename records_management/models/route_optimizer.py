from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RouteOptimizer(models.Model):
    _name = 'route.optimizer'
    _description = 'Route Optimizer'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'optimization_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    optimization_date = fields.Date()
    optimization_type = fields.Selection()
    max_routes = fields.Integer()
    max_stops_per_route = fields.Integer()
    vehicle_capacity = fields.Float()
    status = fields.Selection()
    start_time = fields.Datetime()
    completion_time = fields.Datetime()
    execution_time_seconds = fields.Integer()
    pickup_request_ids = fields.Many2many()
    route_management_id = fields.Many2one()
    starting_location = fields.Char()
    total_distance = fields.Float()
    total_time = fields.Float()
    total_cost = fields.Float()
    routes_generated = fields.Integer()
    optimization_results = fields.Text()
    efficiency_score = fields.Float()
    distance_savings = fields.Float()
    time_savings = fields.Float()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_efficiency_score(self):
            """Calculate overall efficiency score"""
            for record in self:
                if record.distance_savings or record.time_savings:
                    record.efficiency_score = (record.distance_savings + record.time_savings) / 2
                else:
                    record.efficiency_score = 0.0


    def _compute_execution_time(self):
            """Calculate execution time in seconds"""
            for record in self:
                if record.start_time and record.completion_time:
                    delta = record.completion_time - record.start_time
                    record.execution_time_seconds = int(delta.total_seconds())
                else:
                    record.execution_time_seconds = 0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_run_optimization(self):
            """Run the route optimization"""
            self.ensure_one()
            if self.status != 'draft':
                raise UserError(_('Can only run optimization on draft records'))

            if not self.pickup_request_ids:
                raise UserError(_('Please select pickup requests to optimize'))

            # Start optimization
            self.write({)}
                'status': 'running',
                'start_time': fields.Datetime.now()


            try:
                # Run optimization algorithm
                self._perform_optimization()

                # Mark as completed
                self.write({)}
                    'status': 'completed',
                    'completion_time': fields.Datetime.now()


                self.message_post(body=_('Route optimization completed successfully'))

            except Exception as e
                # Mark as failed
                self.write({'status': 'failed'})
                self.message_post(body=_('Route optimization failed: %s') % str(e))
                raise


    def action_apply_optimization(self):
            """Apply optimization results to create actual routes"""
            self.ensure_one()
            if self.status != 'completed':
                raise UserError(_('Can only apply completed optimizations'))

            # Create FSM routes based on optimization results
            self._create_optimized_routes()
            self.message_post(body=_('Optimization results applied - routes created'))


    def action_cancel_optimization(self):
            """Cancel the optimization"""
            self.ensure_one()
            if self.status in ('completed', 'cancelled'):
                raise UserError(_('Cannot cancel completed or already cancelled optimizations'))

            self.write({'status': 'cancelled'})
            self.message_post(body=_('Optimization cancelled'))

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def _perform_optimization(self):
            """Perform the actual route optimization"""
            # Placeholder for optimization algorithm:
            # In a real implementation, this would use algorithms like
            # - Nearest Neighbor
            # - Genetic Algorithm
            # - Simulated Annealing
            # - Vehicle Routing Problem (VRP) solver

            pickup_requests = self.pickup_request_ids
            results = {}
                'routes': [],
                'total_distance': 0,
                'total_time': 0,
                'optimization_method': self.optimization_type


            # Simple nearest neighbor algorithm simulation
            for i, request in enumerate(pickup_requests):
                route_data = {}
                    'route_number': i + 1,
                    'stops': [request.id],
                    'distance': 25.5,  # Simulated
                    'time': 2.5,       # Simulated
                    'capacity_used': request.total_volume

                results['routes'].append(route_data)
                results['total_distance'] += route_data['distance']
                results['total_time'] += route_data['time']

            # Update results
            self.write({)}
                'optimization_results': json.dumps(results),
                'total_distance': results['total_distance'],
                'total_time': results['total_time'],
                'routes_generated': len(results['routes']),
                'distance_savings': 15.0,  # Simulated 15% savings
                'time_savings': 12.0       # Simulated 12% savings



    def _create_optimized_routes(self):
            """Create FSM routes from optimization results"""
            if not self.optimization_results:
                return

            results = json.loads(self.optimization_results)

            for route_data in results['routes']:
                route = self.env['fsm.route'].create({)}
                    'name': _('Optimized Route %s - %s') % (route_data['route_number'], self.optimization_date),
                    'route_date': self.optimization_date,
                    'estimated_distance': route_data['distance'],
                    'estimated_duration': route_data['time'],
                    'state': 'planned'


                # Assign pickup requests to the route
                pickup_ids = route_data['stops']
                self.env['pickup.request'].browse(pickup_ids).write({)}
                    'fsm_route_id': route.id


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_optimization_limits(self):
            """Validate optimization parameters"""
            for record in self:
                if record.max_routes <= 0:
                    raise ValidationError(_('Maximum routes must be greater than 0'))
                if record.max_stops_per_route <= 0:
                    raise ValidationError(_('Maximum stops per route must be greater than 0'))


    def _check_vehicle_capacity(self):
            """Validate vehicle capacity"""
            for record in self:
                if record.vehicle_capacity <= 0:
                    raise ValidationError(_('Vehicle capacity must be greater than 0'))
