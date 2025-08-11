# -*- coding: utf-8 -*-
"""
Unlock Service Parts Module

This module manages parts and materials used in unlock services within the Records
Management System. It provides detailed tracking of components, costs, and usage
for comprehensive service documentation and billing integration.

Key Features:
- Complete parts and materials tracking
- Cost calculation with unit and total pricing
- Product integration with inventory management
- Service history integration
- Usage documentation and notes

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _


class UnlockServicePart(models.Model):
    """Parts and materials used in unlock services"""

    _name = "unlock.service.part"
    _description = "Unlock Service Part"
    _rec_name = "product_id"

    service_history_id = fields.Many2one(
        "unlock.service.history",
        string="Service",
        required=True,
        ondelete="cascade",
        help="Related service history",
    )
    
    product_id = fields.Many2one(
        "product.product",
        string="Product",
        required=True,
        help="Product used in service",
    )
    
    quantity = fields.Float(
        string="Quantity", 
        default=1.0, 
        required=True, 
        help="Quantity used"
    )
    
    unit_price = fields.Float(
        string="Unit Price", 
        help="Unit price of the part"
    )
    
    total_price = fields.Float(
        string="Total Price",
        compute="_compute_total_price",
        store=True,
        help="Total price (quantity * unit price)",
    )
    
    notes = fields.Text(
        string="Notes", 
        help="Additional notes about part usage"
    )

    @api.depends("quantity", "unit_price")
    def _compute_total_price(self):
        """Compute total price"""
        for record in self:
            record.total_price = record.quantity * record.unit_price

    @api.onchange("product_id")
    def _onchange_product_id(self):
        """Set unit price when product changes"""
        if self.product_id:
            self.unit_price = self.product_id.list_price
