from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class FSMRoute(models.Model):
    _name = 'fsm.route'
    _description = 'FSM Route'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'route_date desc, sequence'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    sequence = fields.Integer()
    route_date = fields.Date()
    driver_id = fields.Many2one()
    vehicle_id = fields.Many2one()
    start_location = fields.Char()
    end_location = fields.Char()
    state = fields.Selection()
    estimated_distance = fields.Float()
    actual_distance = fields.Float()
    estimated_duration = fields.Float()
    actual_duration = fields.Float()
    pickup_ids = fields.One2many()
    notification_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    pickup_count = fields.Integer()
    distance_variance = fields.Float()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_pickup_count(self):
            """Count pickups assigned to this route"""
            for record in self:
                record.pickup_count = len(record.pickup_ids)


    def _compute_distance_variance(self):
            """Calculate distance variance"""
            for record in self:
                if record.estimated_distance:
                    variance = record.actual_distance - record.estimated_distance
                    record.distance_variance = (variance / record.estimated_distance) * 100
                else:
                    record.distance_variance = 0.0


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

    def _check_route_date(self):
            """Validate route date is not in the past"""
            for record in self:
                if record.route_date and record.route_date < fields.Date.today():
                    if record.state == 'draft':
                        raise ValidationError(_('Route date cannot be in the past for new routes')):

    def _check_distances(self):
            """Validate distances are positive"""
            for record in self:
                if record.estimated_distance and record.estimated_distance < 0:
                    raise ValidationError(_('Estimated distance cannot be negative'))
                if record.actual_distance and record.actual_distance < 0:
                    raise ValidationError(_('Actual distance cannot be negative'))
