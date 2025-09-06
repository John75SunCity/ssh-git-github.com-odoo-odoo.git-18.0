# -*- coding: utf-8 -*-
"""Stock Lot Action Placeholders

Lightweight, safe navigation helpers for buttons in lot views.
Each method may be extended with real business logic later without
altering stable button object names in XML.
"""
from odoo import models, _


class StockProductionLot(models.Model):
    _inherit = 'stock.lot'

    def action_view_quants(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Quants'),
            'res_model': 'stock.quant',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'target': 'current',
        }

    def action_view_stock_moves(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Stock Moves'),
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.id)],
            'target': 'current',
        }
