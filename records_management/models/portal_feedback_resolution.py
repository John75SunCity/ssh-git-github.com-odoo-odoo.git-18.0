from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class PortalFeedbackResolution(models.Model):
    _name = 'portal.feedback.resolution'
    _description = 'Portal Feedback Resolution'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    feedback_id = fields.Many2one()
    resolved_by_id = fields.Many2one()
    resolution_date = fields.Datetime()
    resolution_type = fields.Selection()
    description = fields.Html()
    internal_notes = fields.Text()
    status = fields.Selection()
    customer_satisfaction = fields.Selection()
    follow_up_required = fields.Boolean()
    follow_up_date = fields.Date()
    follow_up_notes = fields.Text()
    resolution_time_hours = fields.Float()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_resolution_time(self):
            """Calculate resolution time in hours"""
            for record in self:
                if record.feedback_id and record.feedback_id.create_date and record.resolution_date:
                    delta = record.resolution_date - record.feedback_id.create_date
                    record.resolution_time_hours = delta.total_seconds() / 3600
                else:
                    record.resolution_time_hours = 0.0

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_implement_resolution(self):
            """Mark resolution as implemented"""
            self.ensure_one()
            if self.status != 'draft':
                raise UserError(_('Can only implement draft resolutions'))

            self.write({'status': 'implemented'})
            self.message_post(body=_('Resolution implemented'))


    def action_verify_resolution(self):
            """Mark resolution as verified"""
            self.ensure_one()
            if self.status != 'implemented':
                raise UserError(_('Can only verify implemented resolutions'))

            self.write({'status': 'verified'})
            self.message_post(body=_('Resolution verified'))


    def action_notify_customer(self):
            """Notify customer of resolution"""
            self.ensure_one()
            if self.status not in ('implemented', 'verified'):
                raise UserError(_('Can only notify customer after implementation'))

            # Send notification to customer
            self.feedback_id.partner_id.message_post()
                body=_('Your feedback has been addressed: %s') % self.name,
                subject=_('Feedback Resolution: %s') % self.feedback_id.name


            self.write({'status': 'customer_notified'})
            self.message_post(body=_('Customer notified of resolution'))


    def action_close_resolution(self):
            """Close the resolution"""
            self.ensure_one()
            if self.status != 'customer_notified':
                raise UserError(_('Must notify customer before closing'))

            self.write({'status': 'closed'})
            self.message_post(body=_('Resolution closed'))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_follow_up_date(self):
            """Validate follow-up date"""
            for record in self:
                if record.follow_up_required and not record.follow_up_date:
                    raise ValidationError(_('Follow-up date is required when follow-up is needed'))

    def _onchange_follow_up_required(self):
            """Clear follow-up fields when not required"""
            if not self.follow_up_required:
                self.follow_up_date = False
                self.follow_up_notes = False
