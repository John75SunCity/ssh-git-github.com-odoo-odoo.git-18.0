# -*- coding: utf-8 -*-
"""Action placeholder methods for document.retrieval.team."""
from odoo import models


class DocumentRetrievalTeam(models.Model):
    _inherit = 'document.retrieval.team'

    def action_view_team_members(self):
        self.ensure_one()
        return False

    def action_view_performance_metrics(self):
        self.ensure_one()
        return False

    def action_view_work_orders(self):
        self.ensure_one()
        return False
