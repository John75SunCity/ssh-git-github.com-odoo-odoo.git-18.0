# -*- coding: utf-8 -*-
from odoo import models, fields, api

class RecordsUserInvitationWizard(models.TransientModel):
    _name = 'records.user.invitation.wizard'
    _description = 'Records User Invitation Wizard'

    name = fields.Char(string='Name', default='User Invitation')
    user_ids = fields.Many2many('res.users', string='Users to Invite')

    def action_invite_users(self):
        # Placeholder for invitation logic
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}
