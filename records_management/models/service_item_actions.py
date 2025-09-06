# -*- coding: utf-8 -*-
"""Action placeholder methods for service.item."""
from odoo import models


class ServiceItem(models.Model):
    _inherit = 'service.item'

    def action_view_related_requests(self):
        self.ensure_one()
        return False

    def action_view_pricing_history(self):
        self.ensure_one()
        return False
