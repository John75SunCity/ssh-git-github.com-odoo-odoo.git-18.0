# -*- coding: utf-8 -*-
"""
Partner Extensions for Records Management
"""

from odoo import models, fields, api, _


class ResPartner(models.Model):
    """
    Extend Partner for Records Management functionality
    """

    _inherit = "res.partner"

    # ==========================================
    # RECORDS MANAGEMENT FIELDS
    # ==========================================
    # Transitory items field configuration
    transitory_field_config_id = fields.Many2one(
        'transitory.field.config',
        string='Transitory Fields Configuration',
        help='Controls which fields are visible/required when this customer adds transitory items'
    )
    
    # Customer portal settings
    allow_transitory_items = fields.Boolean(
        string='Allow Transitory Items',
        default=True,
        help='Allow this customer to create transitory items in portal'
    )
    
    max_transitory_items = fields.Integer(
        string='Max Transitory Items',
        default=1000,
        help='Maximum number of transitory items this customer can create'
    )
    
    # Billing account for records management
    billing_account_id = fields.Many2one(
        'advanced.billing',
        string='Billing Account',
        help='Default billing account for this customer'
    )
    
    # Records management statistics
    total_transitory_items = fields.Integer(
        string='Total Transitory Items',
        compute='_compute_transitory_stats',
        help='Total number of transitory items created'
    )
    
    active_transitory_items = fields.Integer(
        string='Active Transitory Items',
        compute='_compute_transitory_stats',
        help='Number of active transitory items awaiting pickup'
    )
    
    total_records_boxes = fields.Integer(
        string='Total Records Boxes',
        compute='_compute_records_stats',
        help='Total number of records boxes in storage'
    )

    @api.depends()
    def _compute_transitory_stats(self):
        """Compute transitory items statistics"""
        for partner in self:
            if partner.is_company:
                transitory_items = self.env['transitory.items'].search([
                    ('customer_id', '=', partner.id)
                ])
                partner.total_transitory_items = len(transitory_items)
                partner.active_transitory_items = len(transitory_items.filtered(
                    lambda x: x.state in ('declared', 'scheduled')
                ))
            else:
                partner.total_transitory_items = 0
                partner.active_transitory_items = 0

    @api.depends()
    def _compute_records_stats(self):
        """Compute records boxes statistics"""
        for partner in self:
            if partner.is_company:
                records_boxes = self.env['records.box'].search([
                    ('customer_id', '=', partner.id)
                ])
                partner.total_records_boxes = len(records_boxes)
            else:
                partner.total_records_boxes = 0

    def action_view_transitory_items(self):
        """Open transitory items for this customer"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Transitory Items - {self.name}',
            'view_mode': 'tree,form',
            'res_model': 'transitory.items',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
            'target': 'current',
        }

    def action_view_records_boxes(self):
        """Open records boxes for this customer"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Records Boxes - {self.name}',
            'view_mode': 'tree,form',
            'res_model': 'records.box',
            'domain': [('customer_id', '=', self.id)],
            'context': {'default_customer_id': self.id},
            'target': 'current',
        }

    def get_transitory_field_config(self):
        """Get field configuration for transitory items"""
        self.ensure_one()
        if self.transitory_field_config_id:
            return self.transitory_field_config_id.get_portal_config()
        else:
            # Return default configuration
            return self.env['transitory.field.config'].get_default_config()

    def action_setup_transitory_config(self):
        """Setup transitory field configuration for this customer"""
        self.ensure_one()
        
        if self.transitory_field_config_id:
            config = self.transitory_field_config_id
        else:
            # Create new configuration
            config = self.env['transitory.field.config'].create({
                'name': f"Config for {self.name}",
                'description': f"Field configuration for {self.name}",
            })
            self.transitory_field_config_id = config.id
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Transitory Items Configuration',
            'view_mode': 'form',
            'res_model': 'transitory.field.config',
            'res_id': config.id,
            'target': 'new',
        }
