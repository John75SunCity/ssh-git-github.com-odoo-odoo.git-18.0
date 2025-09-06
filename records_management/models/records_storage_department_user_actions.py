# -*- coding: utf-8 -*-
"""Action placeholder methods for records.storage.department.user."""
from odoo import models


class RecordsStorageDepartmentUser(models.Model):
    _inherit = 'records.storage.department.user'

    def action_view_assignments(self):
        self.ensure_one()
        return False
