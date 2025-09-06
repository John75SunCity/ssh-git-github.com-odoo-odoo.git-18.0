# -*- coding: utf-8 -*-
"""Action placeholder methods for naid.operator.certification."""
from odoo import models


class NaidOperatorCertification(models.Model):
    _inherit = 'naid.operator.certification'

    def action_renew_certification(self):
        self.ensure_one()
        return False  # Future renewal wizard
