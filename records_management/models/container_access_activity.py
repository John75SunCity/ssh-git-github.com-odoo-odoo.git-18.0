from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ContainerAccessActivity(models.Model):
    _name = 'container.access.activity'
    _description = 'Container Access Activity'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'activity_time desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean()
    visitor_id = fields.Many2one()
    work_order_id = fields.Many2one()
    container_id = fields.Many2one()
    location_id = fields.Many2one()
    activity_type = fields.Selection()
    activity_time = fields.Datetime()
    duration_minutes = fields.Integer()
    description = fields.Text()
    findings = fields.Text()
    issues_found = fields.Boolean()
    issue_description = fields.Text()
    authorized_by_id = fields.Many2one()
    supervised_by_id = fields.Many2one()
    approval_required = fields.Boolean()
    approved = fields.Boolean()
    approved_by_id = fields.Many2one()
    approval_date = fields.Datetime()
    photo_taken = fields.Boolean()
    documents_created = fields.Boolean()
    report_generated = fields.Boolean()
    status = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_start_activity(self):
            """Start the activity"""
            self.ensure_one()
            if self.status != 'planned':
                raise UserError(_('Can only start planned activities'))

            self.write({)}
                'status': 'in_progress',
                'activity_time': fields.Datetime.now()

            self.message_post(body=_('Activity started'))


    def action_complete_activity(self):
            """Complete the activity"""
            self.ensure_one()
            if self.status != 'in_progress':
                raise UserError(_('Can only complete activities in progress'))

            if self.approval_required:
                self.write({'status': 'pending_approval'})
                self.message_post(body=_('Activity completed, pending approval'))
            else:
                self.write({'status': 'completed'})
                self.message_post(body=_('Activity completed'))


    def action_approve_activity(self):
            """Approve the activity"""
            self.ensure_one()
            if self.status != 'pending_approval':
                raise UserError(_('Can only approve activities pending approval'))

            self.write({)}
                'status': 'completed',
                'approved': True,
                'approved_by_id': self.env.user.id,
                'approval_date': fields.Datetime.now()

            self.message_post(body=_('Activity approved and completed'))


    def action_cancel_activity(self):
            """Cancel the activity"""
            self.ensure_one()
            if self.status in ('completed', 'cancelled'):
                raise UserError(_('Cannot cancel completed or already cancelled activities'))

            self.write({'status': 'cancelled'})
            self.message_post(body=_('Activity cancelled'))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_approval(self):
            """Validate approval requirements"""
            for record in self:
                if record.approval_required and record.status == 'completed' and not record.approved:
                    raise ValidationError(_('Activity requiring approval must be approved before completion'))


    def _check_issue_description(self):
            """Validate issue description when issues are found"""
            for record in self:
                if record.issues_found and not record.issue_description:
                    raise ValidationError(_('Issue description is required when issues are found'))


    def _onchange_approval_required(self):
            """Clear approval fields when not required"""
            if not self.approval_required:
                self.approved = False
                self.approved_by_id = False
                self.approval_date = False


    def _onchange_issues_found(self):
            """Clear issue description when no issues"""
            if not self.issues_found:
                self.issue_description = False
