# -*- coding: utf-8 -*-

FSM Route Model

Field Service Management route planning and execution.


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FSMRoute(models.Model):
    """Field Service Management Route"""

    _name = "fsm.route"
    _description = "FSM Route"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "route_date desc, sequence"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Route Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or code for this route":
            pass
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this route"
    

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for route ordering":
    

        # ============================================================================
    # ROUTE DETAILS
        # ============================================================================
    route_date = fields.Date(
        string="Route Date",
        required=True,
        default=fields.Date.today,
        tracking=True,
        help="Date for this route execution":
    

    driver_id = fields.Many2one(
        "hr.employee",
        string="Driver",
        tracking=True,
        help="Driver assigned to this route"
    

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle",
        tracking=True,
        help="Vehicle assigned to this route"
    

    start_location = fields.Char(
        string="Start Location",
        help="Starting location for the route":
    

    end_location = fields.Char(
        string="End Location",
        help="Ending location for the route":
    

        # ============================================================================
    # STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([)]
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    

        # ============================================================================
    # ROUTE METRICS
        # ============================================================================
    estimated_distance = fields.Float(
        string="Estimated Distance (km)",
        help="Estimated total distance for the route":
    

    actual_distance = fields.Float(
        string="Actual Distance (km)",
        help="Actual distance traveled"
    

    estimated_duration = fields.Float(
        string="Estimated Duration (hours)",
        help="Estimated time to complete the route"
    

    actual_duration = fields.Float(
        string="Actual Duration (hours)",
        help="Actual time taken to complete the route"
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    pickup_ids = fields.One2many(
        "pickup.request",
        "fsm_route_id",
        string="Pickup Requests",
        help="Pickup requests assigned to this route"
    

    notification_ids = fields.One2many(
        "fsm.notification",
        "route_id",
        string="Notifications",
        help="Notifications sent for this route":
    

        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('pickup_ids')
    def _compute_pickup_count(self):
        """Count pickups assigned to this route"""
        for record in self:
            record.pickup_count = len(record.pickup_ids)

    pickup_count = fields.Integer(
        string="Pickup Count",
        compute='_compute_pickup_count',
        help="Number of pickups in this route"
    

    @api.depends('actual_distance', 'estimated_distance')
    def _compute_distance_variance(self):
        """Calculate distance variance"""
        for record in self:
            if record.estimated_distance:
                variance = record.actual_distance - record.estimated_distance
                record.distance_variance = (variance / record.estimated_distance) * 100
            else:
                record.distance_variance = 0.0

    distance_variance = fields.Float(
        string="Distance Variance (%)",
        compute='_compute_distance_variance',
        help="Percentage variance between estimated and actual distance"
    

        # ============================================================================
    # ACTION METHODS
        # ============================================================================
    def action_plan_route(self):
        """Plan the route"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only plan routes in draft state'))
        
        self.write({'state': 'planned'})
        self.message_post(body=_('Route planned'))

    def action_start_route(self):
        """Start route execution"""
        self.ensure_one()
        if self.state != 'planned':
            raise UserError(_('Can only start planned routes'))
        
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Route started'))

    def action_complete_route(self):
        """Complete the route"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete routes in progress'))
        
        self.write({'state': 'completed'})
        self.message_post(body=_('Route completed'))

    def action_cancel_route(self):
        """Cancel the route"""
        self.ensure_one()
        if self.state in ('completed', 'cancelled'):
            raise UserError(_('Cannot cancel completed or already cancelled routes'))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Route cancelled'))

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('route_date')
    def _check_route_date(self):
        """Validate route date is not in the past"""
        for record in self:
            if record.route_date and record.route_date < fields.Date.today():
                if record.state == 'draft':
                    raise ValidationError(_('Route date cannot be in the past for new routes')):
    @api.constrains('estimated_distance', 'actual_distance')
    def _check_distances(self):
        """Validate distances are positive"""
        for record in self:
            if record.estimated_distance and record.estimated_distance < 0:
                raise ValidationError(_('Estimated distance cannot be negative'))
            if record.actual_distance and record.actual_distance < 0:
                raise ValidationError(_('Actual distance cannot be negative'))
