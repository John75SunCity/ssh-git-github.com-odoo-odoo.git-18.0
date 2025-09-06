# -*- coding: utf-8 -*-
"""Product Template Action Placeholders

Keeps stable XML button object targets while deferring heavy business logic.
Safe to extend/override; prefer adding real implementations instead of
renaming methods to avoid breaking existing views.
"""
from odoo import models, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    def action_configure_pricing(self):
        self.ensure_one()
        return False  # Placeholder – future pricing configuration wizard

    def action_view_sales(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Sales Orders'),
            'res_model': 'sale.order.line',
            'view_mode': 'list,form',
            'domain': [('product_id.product_tmpl_id', 'in', self.ids)],
            'target': 'current',
            'context': dict(self.env.context),
        }

    def action_view_pricing_history(self):
        self.ensure_one()
        return False  # Future: open custom pricing change log

    def action_view_variants(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Variants'),
            'res_model': 'product.product',
            'view_mode': 'list,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'target': 'current',
        }
