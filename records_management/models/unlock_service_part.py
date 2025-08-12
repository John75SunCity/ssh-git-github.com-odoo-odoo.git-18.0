# -*- coding: utf-8 -*-
from odoo import models, fields


class UnlockServicePart(models.Model):
    _name = "unlock.service.part"
    _description = "Unlock Service Part"

    service_history_id = fields.Many2one(
        "unlock.service.history",
        string="Service History",
        required=True,
        ondelete="cascade",
    )
    product_id = fields.Many2one(
        "product.product", string="Product", required=True
    )
    quantity = fields.Float(string="Quantity", default=1.0)
    name = fields.Char(related="product_id.name", readonly=True)
