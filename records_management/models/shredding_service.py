# -*- coding: utf-8 -*-
from odoo import models, fields, api

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Shredding Service'
    _inherit = 'fsm.order'

    # This model inherits all the fields and methods from fsm.order.
    # We can add fields here that are specific to shredding services.
    # For now, we will leave it as a direct inheritance to establish the model.

    # Example of a field that could be added:
    is_certified_destruction = fields.Boolean(string="Certified Destruction", default=True)
