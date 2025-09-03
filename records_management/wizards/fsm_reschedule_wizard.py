# -*- coding: utf-8 -*-
# FSM Reschedule Wizard - Temporarily disabled until industry_fsm is available

import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


# Temporarily create a placeholder wizard that doesn't use fsm.task
# This prevents the "Model 'fsm.task' does not exist in registry" error
class FsmRescheduleWizardPlaceholder(models.TransientModel):
    _name = "fsm.reschedule.wizard.placeholder"
    _description = "Placeholder for FSM Reschedule Wizard"

    # Simple placeholder field to make this a valid model
    name = fields.Char("Placeholder Name", default="FSM Reschedule Wizard Placeholder")

    @api.model
    def _log_fsm_disabled(self):
        """Log that FSM features are disabled"""
        _logger.info(
            "FSM Reschedule Wizard is disabled - industry_fsm module not available"
        )

    # NOTE: When industry_fsm is available, restore the original FSM reschedule wizard code
    # The code includes task_id Many2one field and action_confirm_reschedule method

    def _compute_route_impact(self):
        """Analyze impact on routes and other scheduled tasks"""
        for record in self:
            impact_notes = []

            if record.new_date and record.task_id:
                # Find other tasks on the same day
                same_day_tasks = self.env['fsm.task'].search([
                    ('planned_date_begin', '>=', record.new_date.replace(hour=0, minute=0, second=0)),
                    ('planned_date_begin', '<', record.new_date.replace(hour=23, minute=59, second=59)),
                    ('id', '!=', record.task_id.id),
                    ('stage_id.is_closed', '=', False)
                ])

                if same_day_tasks:
                    impact_notes.append(_("Found %d other tasks on the same day") % len(same_day_tasks))

                # Check for route optimization impact
                if record.task_id.partner_id:
                    # Fix: Use task parameter instead of cell variable
                    nearby_tasks = same_day_tasks.filtered(
                        lambda task, record=record: task.partner_id and task.partner_id.city == record.task_id.partner_id.city
                    )
                    if nearby_tasks:
                        impact_notes.append(_("Route optimization possible with %d nearby tasks") % len(nearby_tasks))

            record.route_impact = "\n".join(impact_notes) if impact_notes else _("No significant route impact identified")

    def action_reject_request(self):
        """Reject the reschedule request"""
        self.ensure_one()

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can reject reschedule requests."))

        self.write({'state': 'rejected'})

        # Notify requester of rejection
        self.message_post(body=_("Reschedule request has been rejected by %s", self.env.user.name))

        return {'type': 'ir.actions.act_window_close'}

    def action_execute_reschedule(self):
        """Execute the reschedule action"""
        self.ensure_one()

        original_date = self.task_id.planned_date_begin

        # Update task details
        task_updates = {
            'planned_date_begin': self.new_date,
            'planned_date_end': self.new_date,
            'reschedule_count': self.task_id.reschedule_count + 1,
            'last_reschedule_date': fields.Datetime.now(),
            'state': 'scheduled',
        }

        # Add custom field if it exists
        if hasattr(self.task_id, 'reschedule_reason'):
            reason_label = dict(self._fields['reason'].selection)[self.reason]
            task_updates['reschedule_reason'] = _("%s: %s") % (reason_label, self.reason_details)

        self.task_id.write(task_updates)

        # Post message on task
        reason_label = dict(self._fields['reason'].selection)[self.reason]
        self.task_id.message_post(
            body=_("Task rescheduled from %s to %s. Reason: %s - %s") % (
                original_date, self.new_date, reason_label, self.reason_details)
        )

        self.write({'state': 'completed'})

        return {'type': 'ir.actions.act_window_close'}

    def _send_customer_notification(self, original_date):
        """Send notification to customer about the reschedule"""
        self.ensure_one()

        if not self.partner_id:
            return

        subject = _("Service Appointment Rescheduled - %s") % self.task_id.name

        # Format dates properly for email
        formatted_original_date = original_date.strftime('%m/%d %I:%M %p') if original_date else _("Not specified")
        formatted_new_date = self.new_date.strftime('%m/%d %I:%M %p')

        # Email body with proper translation
        email_body = _(
            """
            Dear Customer,

            We would like to inform you that your service appointment has been rescheduled.

            Original Date: %s
            New Date: %s

            Reason: %s - %s

            If you have any questions, feel free to contact us.

            Best regards,
            Your Service Team
        """
        ) % (formatted_original_date, formatted_new_date, subject, self.reason_details)

        # Send email
        self.partner_id.message_post(
            subject=subject,
            body=email_body,
            subtype_xmlid='mail.mt_note',
            partner_ids=[self.partner_id.id]
        )

        # Send SMS if configured
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            sms_body = _("Service appointment rescheduled to %s. Details: %s. Contact us with questions.") % (
                self.new_date.strftime('%m/%d %I:%M %p'), self.task_id.name)
            self.partner_id._send_sms(sms_body)

    def _create_fsm_notification(self):
        """Create FSM notification for the reschedule"""
        self.ensure_one()

        if not hasattr(self.env, 'fsm.notification.manager'):
            return

        notification_data = {
            "name": _("Reschedule Notification - %s") % self.task_id.name,
            "notification_type": "reschedule",
            "partner_id": self.partner_id.id,
            "task_id": self.task_id.id,
            "delivery_method": self.notification_method,
            "subject": _("Service Rescheduled - %s") % self.task_id.name,
            "message_body": _("Your service appointment has been rescheduled to %s") % self.new_date,
            "service_date": self.new_date.date(),
            "state": "sent",
            "sent_datetime": fields.Datetime.now(),
        }

        self.env['fsm.notification.manager'].create(notification_data)

    def _create_audit_log(self, original_date):
        """Create comprehensive audit log for the reschedule"""
        self.ensure_one()

        reason_label = dict(self._fields['reason'].selection)[self.reason]
        audit_data = {
            "name": _("FSM Task Reschedule - %s") % self.task_id.name,
            "model_name": "fsm.task",
            "record_id": self.task_id.id,
            "action_type": "reschedule",
            "user_id": self.env.user.id,
            "partner_id": self.partner_id.id,
            "description": _("Task rescheduled from %s to %s") % (original_date, self.new_date),
            "old_value": str(original_date) if original_date else "",
            "new_value": str(self.new_date),
            "reason": _("%s: %s") % (reason_label, self.reason_details),
            "compliance_notes": self.compliance_notes,
        }

        # Create audit log if the model exists
        if hasattr(self.env, 'audit.log'):
            self.env['audit.log'].create(audit_data)

    def _create_approval_activity(self):
        """Create activity for manager approval"""
        self.ensure_one()

        managers = self.env['res.users'].search([
            ('groups_id', 'in', self.env.ref('records_management.group_records_manager').id)
        ])

        if managers:
            note_content = _("Please review and approve the reschedule for task: %s") % self.task_id.name

            self.activity_schedule(
                "mail.mail_activity_data_todo",
                summary=_("Approve FSM Reschedule: %s") % self.task_id.name,
                note=note_content,
                user_id=managers[0].id,
            )

    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New Reschedule Request')) == _('New Reschedule Request'):
                vals['name'] = self.env['ir.sequence'].next_by_code('fsm.reschedule.wizard') or _('New Reschedule Request')
        return super().create(vals_list)

    def unlink(self):
        """Prevent deletion of completed reschedule records"""
        for record in self:
            if record.state == 'completed':
                raise UserError(_("Cannot delete completed reschedule records. They are required for audit trail."))
        return super().unlink()
