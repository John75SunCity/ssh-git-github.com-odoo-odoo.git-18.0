# -*- coding: utf-8 -*-
"""Action placeholder methods for naid.certificate."""
from odoo import models


class NaidCertificate(models.Model):
    _inherit = 'naid.certificate'

    def action_conduct_audit(self):
        self.ensure_one()
        return False

    def action_renew_certificate(self):
        self.ensure_one()
        return False

    def action_view_audit_history(self):
        self.ensure_one()
        return False

    def action_view_destruction_records(self):
        self.ensure_one()
        return False
