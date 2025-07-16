# New file: Extend FSM (project.task) for portal-generated field services. Auto-notify on creation, link to requests for compliance.

from odoo import models, fields, api, _


class FSMTask(models.Model):
    _inherit = 'project.task'

    portal_request_id = fields.Many2one('portal.request', string='Portal Request')
    # Auto-create from portal_request.action_submit
