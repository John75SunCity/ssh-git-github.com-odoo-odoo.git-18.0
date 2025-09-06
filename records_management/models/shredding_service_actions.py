# -*- coding: utf-8 -*-
"""Action placeholder methods for shredding.service."""
from odoo import models


class ShreddingService(models.Model):
    _inherit = 'shredding.service'

    def action_view_destruction_items(self):
        self.ensure_one()
        return False
