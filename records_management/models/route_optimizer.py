# -*- coding: utf-8 -*-

Route Optimizer Model

Optimization engine for pickup and delivery routes.:
    pass


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import json


class RouteOptimizer(models.Model):
    """Route Optimizer"""

    _name = "route.optimizer"
    _description = "Route Optimizer"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "optimization_date desc"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Optimization Name",
        required=True,
        tracking=True,
        index=True,
        help="Name for this optimization run":


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this optimization"


        # ============================================================================
    # OPTIMIZATION PARAMETERS
        # ============================================================================
    optimization_date = fields.Date(
        string="Optimization Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date for route optimization":


    ,
    optimization_type = fields.Selection([))
        ('distance', 'Minimize Distance'),
        ('time', 'Minimize Time'),
        ('cost', 'Minimize Cost'),
        ('stops', 'Minimize Stops'),
        ('balanced', 'Balanced Optimization')


    max_routes = fields.Integer(
        string="Maximum Routes",
        default=10,
        help="Maximum number of routes to generate"


    max_stops_per_route = fields.Integer(
        string="Max Stops per Route",
        default=20,
        help="Maximum stops allowed per route"


    vehicle_capacity = fields.Float(
        ,
    string="Vehicle Capacity (CF)",
        default=100.0,
        help="Vehicle capacity in cubic feet"


        # ============================================================================
    # OPTIMIZATION RESULTS
        # ============================================================================
    status = fields.Selection([))
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')


    start_time = fields.Datetime(
        string="Start Time",
        help="When optimization started"


    completion_time = fields.Datetime(
        string="Completion Time",
        help="When optimization completed"


    execution_time_seconds = fields.Integer(
        ,
    string="Execution Time (seconds)",
        help="Time taken for optimization":


        # ============================================================================
    # INPUT DATA
        # ============================================================================
    pickup_request_ids = fields.Many2many(
        "pickup.request",
        string="Pickup Requests",
        help="Pickup requests to optimize"


    route_management_id = fields.Many2one(
        "fsm.route.management",
        string="Route Management",
        help="Related FSM route management"


    starting_location = fields.Char(
        string="Starting Location",
        default="Warehouse",
        help="Starting point for all routes":


        # ============================================================================
    # RESULTS DATA
        # ============================================================================
    total_distance = fields.Float(
        ,
    string="Total Distance (km)",
        help="Total optimized distance"


    total_time = fields.Float(
        ,
    string="Total Time (hours)",
        help="Total optimized time"


    total_cost = fields.Float(
        string="Total Cost",
        help="Total estimated cost"


    routes_generated = fields.Integer(
        string="Routes Generated",
        help="Number of routes generated"


    optimization_results = fields.Text(
        string="Optimization Results",
        help="Detailed optimization results in JSON format"


        # ============================================================================
    # EFFICIENCY METRICS
        # ============================================================================
    efficiency_score = fields.Float(
        ,
    string="Efficiency Score (%)",
        compute='_compute_efficiency_score',
        help="Overall efficiency score"


    distance_savings = fields.Float(
        ,
    string="Distance Savings (%)",
        help="Distance savings vs unoptimized routes"


    time_savings = fields.Float(
        ,
    string="Time Savings (%)",
        help="Time savings vs unoptimized routes"


        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('distance_savings', 'time_savings')
    def _compute_efficiency_score(self):
        """Calculate overall efficiency score"""
        for record in self:
            if record.distance_savings or record.time_savings:
                record.efficiency_score = (record.distance_savings + record.time_savings) / 2
            else:
                record.efficiency_score = 0.0

    @api.depends('start_time', 'completion_time')
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
            'routes': [),
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
    @api.constrains('max_routes', 'max_stops_per_route')
    def _check_optimization_limits(self):
        """Validate optimization parameters"""
        for record in self:
            if record.max_routes <= 0:
                raise ValidationError(_('Maximum routes must be greater than 0'))
            if record.max_stops_per_route <= 0:
                raise ValidationError(_('Maximum stops per route must be greater than 0'))

    @api.constrains('vehicle_capacity')
    def _check_vehicle_capacity(self):
        """Validate vehicle capacity"""
        for record in self:
            if record.vehicle_capacity <= 0:
                raise ValidationError(_('Vehicle capacity must be greater than 0'))
))))))))))))))))))
