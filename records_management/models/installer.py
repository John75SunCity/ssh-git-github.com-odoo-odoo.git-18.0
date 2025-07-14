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
        stock_module = self.env['ir.module.module'].search([
            ('name', '=', 'stock'),
            ('state', '=', 'installed')
        ])
        if not stock_module:
            raise UserError(_(
                'The Inventory module must be installed before installing '
                'Records Management.\nPlease go to Apps, search for '
                '"Inventory", install it, and then try again.'
            ))
        return True

    def install_required_modules(self) -> Dict:
        """Install required modules automatically."""
        stock_module = self.env['ir.module.module'].search([
            ('name', '=', 'stock'),
            ('state', 'in', ['uninstalled', 'to install'])
        ])
        if stock_module:
            stock_module.button_immediate_install()
        return {'type': 'ir.actions.client', 'tag': 'reload'}
