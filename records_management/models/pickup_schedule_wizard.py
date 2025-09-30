from odoo import models, fields, _
from odoo.exceptions import UserError

class PickupScheduleWizard(models.TransientModel):
    _name = 'pickup.schedule.wizard'
    _description = 'Pickup Scheduling Wizard'

    request_id = fields.Many2one(comodel_name='pickup.request', string='Pickup Request', required=True, readonly=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', readonly=True)

    scheduled_date = fields.Datetime(string='Scheduled Date & Time', required=True, default=fields.Datetime.now)
    technician_id = fields.Many2one(comodel_name='res.users', string='Assigned Technician', domain="[('share', '=', False)]")
    notes = fields.Text(string='Scheduling Notes')

    def action_schedule_pickup(self):
        self.ensure_one()
        if not self.request_id:
            raise UserError(_("No pickup request linked to this wizard."))

        self.request_id.write({
            'state': 'scheduled',
            'scheduled_pickup_date': self.scheduled_date,
        })

        # Create FSM Task
        task = self.env["project.task"].create(
            {
                "name": _("Pickup: %s", self.request_id.name),
                "project_id": self.env.ref("industry_fsm.fsm_project").id,  # Or a specific project
                "partner_id": self.request_id.partner_id.id,
                "user_ids": [(6, 0, [self.technician_id.id])] if self.technician_id else [],
                "date_deadline": self.scheduled_date.date(),
                "description": self.request_id.description,
            }
        )

        self.request_id.fsm_task_id = task.id

        log_body = _("Pickup scheduled for %s.", self.scheduled_date)
        if self.technician_id:
            log_body += _(" Assigned to %s.", self.technician_id.name)
        if self.notes:
            log_body += _("<br/>Notes: %s", self.notes)

        self.request_id.message_post(body=log_body)

        return {'type': 'ir.actions.act_window_close'}
