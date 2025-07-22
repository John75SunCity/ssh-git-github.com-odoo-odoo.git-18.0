# New file: Extend FSM (project.task) for portal-generated field services. Auto-notify on creation, link to requests for compliance.

from odoo import models, fields, api, _


class FSMTask(models.Model):
    _inherit = 'project.task'

    portal_request_id = fields.Many2one('portal.request', string='Portal Request')
    # Auto-create from portal_request.action_submit

    def action_start_task(self):
        """Start the FSM task"""
        self.write({'stage_id': self._get_stage_by_name('In Progress')})
        self.message_post(body=_('Task started by %s') % self.env.user.name)

    def action_complete_task(self):
        """Complete the FSM task"""
        self.write({'stage_id': self._get_stage_by_name('Done')})
        self.message_post(body=_('Task completed by %s') % self.env.user.name)

    def action_pause_task(self):
        """Pause the FSM task"""
        self.write({'stage_id': self._get_stage_by_name('Paused')})
        self.message_post(body=_('Task paused by %s') % self.env.user.name)

    def action_reschedule(self):
        """Reschedule the FSM task"""
        self.ensure_one()
        return {
            'name': _('Reschedule Task: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_view_location(self):
        """View task location"""
        self.ensure_one()
        if self.partner_id:
            return {
                'name': _('Customer Location'),
                'type': 'ir.actions.act_window',
                'res_model': 'res.partner',
                'res_id': self.partner_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_contact_customer(self):
        """Contact customer"""
        self.ensure_one()
        if self.partner_id:
            return {
                'name': _('Contact Customer'),
                'type': 'ir.actions.act_window',
                'res_model': 'mail.compose.message',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_partner_ids': [(6, 0, [self.partner_id.id])],
                    'default_subject': _('FSM Task: %s') % self.name,
                },
            }
        return False

    def action_mobile_app(self):
        """Open mobile app link"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_url',
            'url': '/web#id=%s&model=project.task&view_type=form' % self.id,
            'target': 'self',
        }

    def action_view_time_logs(self):
        """View time logs for this task"""
        self.ensure_one()
        return {
            'name': _('Time Logs: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'tree,form',
            'domain': [('task_id', '=', self.id)],
            'context': {'default_task_id': self.id},
        }

    def action_view_materials(self):
        """View materials used for this task"""
        self.ensure_one()
        return {
            'name': _('Materials: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move',
            'view_mode': 'tree,form',
            'domain': [('origin', '=', self.name)],
            'context': {'default_origin': self.name},
        }

    def _get_stage_by_name(self, stage_name):
        """Get stage ID by name"""
        stage = self.env['project.task.type'].search([
            ('name', '=', stage_name),
            ('project_ids', 'in', [self.project_id.id])
        ], limit=1)
        return stage.id if stage else False
