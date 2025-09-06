# -*- coding: utf-8 -*-
"""Paper Bale Action Placeholders

Provides safe stubs for UI buttons (weighting, loading, source docs, trailer
info, history). Each returns False until real logic is implemented. Keep
method names stable to avoid breaking existing XML button definitions.
"""
from odoo import models


class PaperBale(models.Model):
    _inherit = 'paper.bale'

    def action_weigh_bale(self):
        self.ensure_one()
        return False

    def action_load_trailer(self):
        self.ensure_one()
        return False

    def action_view_source_documents(self):
        self.ensure_one()
        return False

    def action_view_trailer_info(self):
        self.ensure_one()
        return False

    def action_view_weight_history(self):
        self.ensure_one()
        return False
