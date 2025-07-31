# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import datetime, timedelta


class FsmRouteManagement(models.Model):
    _name = "fsm.route.management"
    _description = "FSM Route Management"

    def reschedule_remaining_for_driver(self, driver_id):
        """
        Finds all of today's incomplete tasks for a driver and reschedules them
        for the next business day.
        """
        today = fields.Date.context_today(self)
        tasks_to_reschedule = self.env["fsm.task"].search(
            [
                ("employee_id", "=", driver_id.id),
                ("schedule_date", "=", today),
                ("is_closed", "=", False),
            ]
        )

        next_business_day = self._get_next_business_day(today)

        for task in tasks_to_reschedule:
            task.write(
                {
                    "schedule_date": next_business_day,
                    "reschedule_reason": _("End-of-day reschedule by driver."),
                }
            )
        return True

    def create_follow_up_task(self, original_task):
        """
        Creates a follow-up task for a one-time purge bin pickup, scheduled
        for one week later, avoiding weekends.
        """
        if not original_task.is_one_time_purge:  # Assuming this field exists
            return False

        pickup_date = self._get_next_business_day(
            fields.Date.today() + timedelta(days=7)
        )

        self.env["fsm.task"].create(
            {
                "name": _("Follow-up: Pick up purge bins for %s")
                % original_task.partner_id.name,
                "partner_id": original_task.partner_id.id,
                "schedule_date": pickup_date,
                "project_id": original_task.project_id.id,
                "company_id": original_task.company_id.id,
                "user_id": original_task.user_id.id,
                # Copy other relevant fields from the original task
            }
        )
        return True

    def _get_next_business_day(self, date):
        """Finds the next weekday."""
        next_day = date + timedelta(days=1)
        while next_day.weekday() >= 5:  # Saturday = 5, Sunday = 6
            next_day += timedelta(days=1)
        return next_day
