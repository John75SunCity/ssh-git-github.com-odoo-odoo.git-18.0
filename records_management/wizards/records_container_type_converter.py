# -*- coding: utf-8 -*-
"""
Records Container Type Converter Wizard
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsContainerTypeConverter(models.TransientModel):
    """
    Records Container Type Converter Wizard
    """

    _name = "records.container.type.converter"
    _description = "Records Container Type Converter Wizard"

    # Core fields
    name = fields.Char(string="Converter Name", default="Container Type Converter")
    container_ids = fields.Many2many('records.container', string='Containers to Convert')
    from_type = fields.Selection([
        ('01', 'Type 01 - Standard Container'),
        ('03', 'Type 03 - Map Container'),
        ('04', 'Type 04 - Pallet/Wide Containers'),
        ('05', 'Type 05 - Pathology'),
        ('06', 'Type 06 - Specialty Container')
    ], string='From Container Type', required=True)
    to_type = fields.Selection([
        ('01', 'Type 01 - Standard Container'),
        ('03', 'Type 03 - Map Container'),
        ('04', 'Type 04 - Pallet/Wide Containers'),
        ('05', 'Type 05 - Pathology'),
        ('06', 'Type 06 - Specialty Container')
    ], string='To Container Type', required=True)
    reason = fields.Text(string='Reason for Conversion', required=True)
    update_billing = fields.Boolean(string='Update Billing Rates', default=True, 
                                   help='Update billing rates based on new container type')

    def action_convert_containers(self):
        """Convert the selected containers to new type with rate adjustments"""
        self.ensure_one()
        
        if self.from_type == self.to_type:
            raise UserError(_('From Type and To Type cannot be the same'))
            
        converted_count = 0
        for container in self.container_ids:
            # Only convert containers that match the from_type
            if container.container_type == self.from_type:
                # Update container type
                container.write({
                    'container_type': self.to_type,
                    'conversion_reason': self.reason,
                    'conversion_date': fields.Datetime.now(),
                    'converted_from_type': self.from_type
                })
                
                # Update billing rates if requested
                if self.update_billing and hasattr(container, 'monthly_rate'):
                    new_rate = self._get_rate_for_container_type(self.to_type)
                    if new_rate:
                        container.write({'monthly_rate': new_rate})
                
                converted_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Conversion Complete',
                'message': f'Converted {converted_count} containers from Type {self.from_type} to Type {self.to_type}',
                'type': 'success'
            }
        }
    
    def _get_rate_for_container_type(self, container_type):
        """Get billing rate for specific container type"""
        # Rate mapping based on actual container types in the system
        rate_mapping = {
            '01': 2.50,   # Type 01 - Standard Container (Default - 90% of containers)
            '03': 3.25,   # Type 03 - Map Container
            '04': 5.00,   # Type 04 - Pallet/Wide Container  
            '05': 4.75,   # Type 05 - Pathology Container
            '06': 3.75    # Type 06 - Specialty Container
        }
        return rate_mapping.get(container_type, 2.50)  # Default to standard rate
