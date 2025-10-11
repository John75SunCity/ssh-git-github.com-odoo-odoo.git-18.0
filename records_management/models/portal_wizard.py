from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PortalWizard(models.TransientModel):
    _inherit = 'portal.wizard'

    def action_apply(self):
        """Override to handle user type conflicts and ensure proper portal setup"""
        # First, prevent any user type conflicts
        self.env['res.users']._prevent_user_type_conflicts()
        
        # Then proceed with standard portal creation
        result = super().action_apply()
        
        # After portal creation, clean up any conflicts again
        self.env['res.users']._prevent_user_type_conflicts()
        
        return result


class PortalWizardUser(models.TransientModel):
    _inherit = 'portal.wizard.user'

    @api.model_create_multi
    def create(self, vals_list):
        """Ensure portal user creation doesn't create conflicts"""
        records = super().create(vals_list)
        
        # Prevent conflicts after wizard user creation
        self.env['res.users']._prevent_user_type_conflicts()
        
        return records

    def action_grant_access(self):
        """Override to handle group conflicts during portal access grant"""
        # Clean up conflicts before granting access
        self.env['res.users']._prevent_user_type_conflicts()
        
        # Proceed with standard access grant
        result = super().action_grant_access()
        
        # Clean up conflicts after granting access
        self.env['res.users']._prevent_user_type_conflicts()
        
        return result

    def action_revoke_access(self):
        """Override to handle group conflicts during portal access revoke"""
        # Clean up conflicts before revoking access
        self.env['res.users']._prevent_user_type_conflicts()
        
        # Proceed with standard access revoke
        result = super().action_revoke_access()
        
        # Clean up conflicts after revoking access
        self.env['res.users']._prevent_user_type_conflicts()
        
        return result
