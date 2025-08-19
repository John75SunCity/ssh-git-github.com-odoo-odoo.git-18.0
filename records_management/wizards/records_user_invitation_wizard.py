from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsUserInvitationWizard(models.TransientModel):
    _name = 'records.user.invitation.wizard'
    _description = 'Records User Invitation Wizard'

    # ============================================================================
    # FIELDS
    # ============================================================================
    user_ids = fields.Many2many(
        'res.users', 
        string="Users to Invite", 
        required=True,
        help="Select users to grant portal access and send an invitation."
    )
    
    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_invite_users(self):
        """
        Grants portal access to the selected users and sends them an invitation email.
        This leverages the core Odoo portal wizard functionality.
        """
        self.ensure_one()
        if not self.user_ids:
            raise UserError(_("Please select at least one user to invite."))

        # Filter out users who are already portal users or inactive
        internal_users = self.user_ids.filtered(lambda user: not user.has_group('base.group_portal') and user.active)
        if not internal_users:
            raise UserError(_("All selected users are already portal users or are inactive."))

        # Use the core Odoo portal wizard to handle the invitation logic
        portal_wizard = self.env['portal.wizard'].create({})
        
        for user in internal_users:
            portal_wizard_user = self.env['portal.wizard.user'].create({
                'wizard_id': portal_wizard.id,
                'user_id': user.id,
                'email': user.email,
                'in_portal': True, # Grant portal access
            })

        # Trigger the action that sends the invitation emails
        portal_wizard.action_apply()

        self.env['records.security.audit'].create({
            'name': _('Portal Invitation Sent'),
            'event_type': 'access_grant',
            'user_id': self.env.user.id,
            'description': _('Invited %s users to the portal.', len(internal_users)),
        })

        return {'type': 'ir.actions.act_window_close'}