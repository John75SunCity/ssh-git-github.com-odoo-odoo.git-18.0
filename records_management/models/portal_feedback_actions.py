# -*- coding: utf-8 -*-
"""Action placeholder methods for portal.feedback."""
from odoo import models


class PortalFeedback(models.Model):
    _inherit = 'portal.feedback'

    def action_view_related_records(self):
        self.ensure_one()
        return False
