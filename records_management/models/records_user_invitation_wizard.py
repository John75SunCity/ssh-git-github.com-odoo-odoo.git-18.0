from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api


class GeneratedModel(models.Model):
    _name = 'records.user.invitation.wizard'
    _description = 'Records User Invitation Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name')
    user_ids = fields.Many2many('res.users')

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_invite_users(self):
            # Placeholder for invitation logic:
                pass
            self.ensure_one()
            return {'type': 'ir.actions.act_window_close'}

