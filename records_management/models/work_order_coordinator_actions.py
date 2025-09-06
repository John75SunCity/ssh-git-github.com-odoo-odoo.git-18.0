# -*- coding: utf-8 -*-
"""Action placeholder methods for work.order.coordinator."""
from odoo import models


class WorkOrderCoordinator(models.Model):
    _inherit = 'work.order.coordinator'

    def action_view_work_orders(self):
        self.ensure_one()
        return False
