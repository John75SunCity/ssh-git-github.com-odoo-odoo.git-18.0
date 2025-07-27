# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import Dict
from odoo import models, api, _
from odoo.exceptions import UserError

class RecordsManagementInstaller(models.TransientModel):
    """Transient model for records management installation helper."""
    _name = 'records.management.installer'
    _description = 'Records Management Installation Helper'

    @api.model
    def check_dependencies(self) -> bool:
        """
        Check if required modules are installed before installing
        records_management.
        """
        required_modules = ['stock', 'account', 'sale', 'point_of_sale']
        for module_name in required_modules:
            module = self.env['ir.module.module'].search([
                ('name', '=', module_name),
                ('state', '=', 'installed')
            ])
            if not module:
                raise UserError(_(
                    f'The {module_name.capitalize()} module must be '
                    'installed before installing Records Management.'
                ))
        return True

    def install_required_modules(self) -> Dict:
        """Install required modules automatically."""
        required_modules = ['stock', 'account', 'sale', 'point_of_sale']
        for module_name in required_modules:
            module = self.env['ir.module.module'].search([
                ('name', '=', module_name),
                ('state', 'in', ['uninstalled', 'to install'])
            ])
            if module:
                module.button_immediate_install()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
