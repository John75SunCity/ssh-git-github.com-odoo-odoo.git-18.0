try:  # pragma: no cover - consistency with certification model and safe fallback
    from dateutil.relativedelta import relativedelta  # type: ignore  # noqa: F401
except Exception:  # pragma: no cover
    class _RelativedeltaFallback:  # minimal fallback supporting days addition only
        def __init__(self, days=0):
            self.days = days

        def __radd__(self, other):
            if hasattr(other, '__class__') and hasattr(other, 'toordinal'):
                from datetime import timedelta
                return other + timedelta(days=self.days)
            return other

    relativedelta = _RelativedeltaFallback  # fallback: minimal days-only implementation when python-dateutil is unavailable

import logging  # stdlib first
from odoo import models, fields, api, _  # odoo imports

_logger = logging.getLogger(__name__)

class NAIDTrainingSchedule(models.Model):  # noqa: E305 (naming retained per existing codebase style)
    _name = 'naid.training.schedule'
    _description = 'NAID Training Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date'

    # Debug helper to confirm early model registration order during load (safe no-op in production)
    _logger.debug('Loading model naid.training.schedule (fields will be available for One2many inverse resolution)')

    certification_id = fields.Many2one('naid.operator.certification', string='Certification', required=True, ondelete='cascade')
    training_id = fields.Many2one('slide.channel', string='Training Course', required=True)
    scheduled_date = fields.Date(string='Scheduled Date', required=True)
    completed_date = fields.Date(string='Completed Date')
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('missed', 'Missed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', tracking=True)
    notes = fields.Text(string='Notes')
    instructor_id = fields.Many2one('res.users', string='Instructor')
    location = fields.Char(string='Location')
    duration_hours = fields.Float(string='Duration (Hours)')
    reminder_sent = fields.Boolean(string='Reminder Sent', default=False)

    @api.model
    def action_send_training_reminders(self):
        """Send reminders for upcoming trainings"""
        today = fields.Date.context_today(self)
        reminder_date = today + relativedelta(days=7)

        upcoming_trainings = self.search([
            ('scheduled_date', '=', reminder_date),
            ('status', '=', 'scheduled'),
            ('reminder_sent', '=', False)
        ])

        for training in upcoming_trainings:
            # Send reminder notification/email
            training.certification_id.message_post(
                body=_("Reminder: Training '%s' is scheduled for %s") % (training.training_id.name, training.scheduled_date)
            )
            training.reminder_sent = True

    def action_mark_completed(self):
        """Mark training as completed"""
        self.ensure_one()
        self.write({
            'completed_date': fields.Date.context_today(self),
            'status': 'completed'
        })
        # Update certification's completed trainings
        self.certification_id.write({
            'completed_trainings_ids': [(4, self.training_id.id)]
        })
        self.message_post(body=_("Training completed."))

    def action_start_training(self):
        """Mark training as in progress"""
        self.ensure_one()
        self.write({'status': 'in_progress'})
        self.message_post(body=_("Training started."))
