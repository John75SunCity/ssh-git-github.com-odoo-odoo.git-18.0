# -*- coding: utf-8 -*-
"""Action placeholder methods for records.retention.policy.version."""
from odoo import models


class RecordsRetentionPolicyVersion(models.Model):
    _inherit = 'records.retention.policy.version'

    def action_compare_versions(self):
        self.ensure_one()
        return False  # Future diff view

    def action_view_audit_trail(self):
        self.ensure_one()
        return False  # Future audit log listing
