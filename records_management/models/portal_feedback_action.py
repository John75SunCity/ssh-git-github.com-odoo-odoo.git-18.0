from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError


class PortalFeedbackAction(models.Model):
    _name = 'portal.feedback.action'
    _description = 'Portal Feedback Action'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'feedback_id, priority desc, due_date'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Action Name', required=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    feedback_id = fields.Many2one()
    description = fields.Text(string='Action Description')
    action_type = fields.Selection()
    assigned_to_id = fields.Many2one()
    due_date = fields.Date(string='Due Date', required=True)
    priority = fields.Selection()
    status = fields.Selection()
    completion_date = fields.Date(string='Completion Date')
    completion_notes = fields.Text(string='Completion Notes')
    estimated_hours = fields.Float(string='Estimated Hours')
    actual_hours = fields.Float(string='Actual Hours')
    is_overdue = fields.Boolean()
    days_remaining = fields.Integer()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_is_overdue(self):
            """Check if action is overdue""":

    def _compute_days_remaining(self):
            """Calculate days remaining until due date"""

    def action_start(self):
            """Start working on the action"""
            self.ensure_one()
            if self.status != "not_started":
                raise UserError(_("Can only start actions that haven't been started yet."))'

            self.write({"status": "in_progress"})
            self.message_post()
                body=_("Action has been started."), message_type="notification"



    def action_complete(self):
            """Mark action as completed"""
            self.ensure_one()
            if self.status == "completed":
                raise UserError(_("Action is already completed."))

            self.write({"status": "completed", "completion_date": fields.Date.today()})
            self.message_post()
                body=_("Action has been completed."), message_type="notification"



    def action_cancel(self):
            """Cancel the action"""
            self.ensure_one()
            if self.status == "completed":
                raise UserError(_("Cannot cancel a completed action."))

            self.write({"status": "cancelled"})
            self.message_post()
                body=_("Action has been cancelled."), message_type="notification"


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_hours(self):
            """Validate hour fields"""
            for record in self:
                if record.estimated_hours < 0:
                    raise ValidationError(_("Estimated hours cannot be negative."))
                if record.actual_hours < 0:
                    raise ValidationError(_("Actual hours cannot be negative."))


    def _check_due_date(self):
            """Validate due date is not in the past for new actions""":
            for record in self:
                if (:)
                    record.due_date
                    and record.due_date < fields.Date.today()
                    and record.status == "not_started"

                    raise ValidationError()
                        _("Due date cannot be in the past for new actions."):

