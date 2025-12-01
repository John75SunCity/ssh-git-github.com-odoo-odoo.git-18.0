# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FSMWorksheetWizard(models.TransientModel):
    """Wizard to add worksheet to FSM task"""
    _name = 'fsm.worksheet.wizard'
    _description = 'Add Worksheet to FSM Task'

    task_id = fields.Many2one(
        comodel_name='project.task',
        string='FSM Task',
        required=True,
        readonly=True,
        default=lambda self: self.env.context.get('active_id')
    )
    template_id = fields.Many2one(
        comodel_name='fsm.worksheet.template',
        string='Worksheet Template',
        required=True,
        domain="[('active', '=', True)]"
    )
    service_type = fields.Selection(
        related='template_id.service_type',
        string='Service Type',
        readonly=True
    )

    @api.model
    def default_get(self, fields_list):
        """Pre-select template based on linked work order"""
        res = super().default_get(fields_list)
        task_id = self.env.context.get('active_id')
        if task_id:
            task = self.env['project.task'].browse(task_id)
            service_type = self._get_service_type_from_task(task)
            if service_type:
                template = self.env['fsm.worksheet.template'].search([
                    ('service_type', '=', service_type),
                    ('active', '=', True)
                ], limit=1)
                if template:
                    res['template_id'] = template.id
        return res

    def _get_service_type_from_task(self, task):
        """Determine service type from linked work orders"""
        if task.shredding_work_order_id:
            shredding_type = task.shredding_work_order_id.shredding_service_type
            if shredding_type == 'on_site':
                return 'shredding_onsite'
            elif shredding_type == 'off_site':
                return 'shredding_offsite'
            elif shredding_type == 'hard_drive':
                return 'hard_drive'
            else:
                return 'destruction'
        elif task.destruction_work_order_id:
            return 'destruction'
        elif task.retrieval_work_order_id or task.retrieval_work_order_wo_id:
            return 'retrieval'
        elif task.pickup_request_id:
            return 'pickup'
        elif task.access_work_order_id:
            return 'access'
        return False

    def action_create_worksheet(self):
        """Create worksheet instance from selected template"""
        self.ensure_one()
        if not self.template_id:
            raise UserError(_("Please select a worksheet template."))

        worksheet = self.env['fsm.worksheet.instance'].create({
            'task_id': self.task_id.id,
            'template_id': self.template_id.id,
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Worksheet'),
            'res_model': 'fsm.worksheet.instance',
            'res_id': worksheet.id,
            'view_mode': 'form',
            'target': 'current',
        }
