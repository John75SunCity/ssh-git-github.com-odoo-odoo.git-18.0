# -*- coding: utf-8 -*-
""",
Document Retention Policy
"""

from odoo import models, fields, api, _


class RecordsRetentionPolicy(models.Model):
    """,
    Document Retention Policy
    """

    _name = "records.retention.policy",
    _description = "Document Retention Policy",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                                """Mark as done""",
                                self.write({'state': 'done'})
