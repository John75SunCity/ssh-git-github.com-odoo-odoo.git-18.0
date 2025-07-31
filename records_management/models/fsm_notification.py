# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class FsmNotification(models.Model):
    _name = "fsm.notification"
    _description = "FSM Notification Manager"

    def send_day_of_service_notification(self):
        """
        Sends a "Day of Service" notification to all customers with a task scheduled for today.
        This is intended to be run by a scheduled action.
        """
        today = fields.Date.context_today(self)
        tasks = self.env["fsm.task"].search([("schedule_date", "=", today)])
        template = self.env.ref(
            "records_management.mail_template_fsm_day_of_service",
            raise_if_not_found=False,
        )
        if not template:
            return
        for task in tasks:
            if task.partner_id.email:
                template.send_mail(task.id, force_send=True)

    def send_driver_nearby_notification(self, task):
        """
        Sends a "Driver Nearby" notification for a specific task.
        This is intended to be triggered manually or by a future GPS integration.
        """
        self.ensure_one()
        template = self.env.ref(
            "records_management.mail_template_fsm_driver_nearby",
            raise_if_not_found=False,
        )
        if not template or not task.partner_id.email:
            return
        template.send_mail(task.id, force_send=True)
