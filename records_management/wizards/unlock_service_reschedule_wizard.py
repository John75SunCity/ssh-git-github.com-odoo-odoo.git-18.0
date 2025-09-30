from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class UnlockServiceRescheduleWizard(models.TransientModel):
    _name = 'unlock.service.reschedule.wizard'
    _description = 'Unlock Service Reschedule Wizard'

    service_id = fields.Many2one(comodel_name='bin.unlock.service', string="Service", required=True, readonly=True)
    current_date = fields.Datetime(string="Current Scheduled Date", readonly=True)
    new_date = fields.Datetime(string="New Scheduled Date", required=True, default=fields.Datetime.now)
    reason = fields.Text(string="Reason for Rescheduling", required=True)
    notify_customer = fields.Boolean(string="Notify Customer by Email", default=True)

    @api.constrains('new_date', 'current_date')
    def _check_new_date(self):
        for record in self:
            if record.new_date <= record.current_date:
                raise ValidationError(_("The new date must be after the current scheduled date."))

    def action_reschedule(self):
        """Executes the reschedule action."""
        self.ensure_one()
        # In merged model the scheduled datetime field is 'scheduled_date'
        self.service_id.write({'scheduled_date': self.new_date})

        # Compose message using interpolation after translation per project convention
        log_message = _("Service rescheduled from %s to %s. Reason: %s") % (
            fields.Datetime.to_string(self.current_date),
            fields.Datetime.to_string(self.new_date),
            self.reason
        )
        self.service_id.message_post(body=log_message)

        if self.notify_customer:
            # Assuming a template exists with this xml_id
            template = self.env.ref('records_management.email_template_service_rescheduled', raise_if_not_found=False)
            if template:
                template.send_mail(self.service_id.id, force_send=True)

        return {'type': 'ir.actions.act_window_close'}
