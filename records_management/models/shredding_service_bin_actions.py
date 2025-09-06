# -*- coding: utf-8 -*-
"""Action placeholder methods for shredding.service.bin."""
from odoo import models


class ShreddingServiceBin(models.Model):
    _inherit = 'shredding.service.bin'

    def action_view_work_orders(self):
        self.ensure_one()
        return False
