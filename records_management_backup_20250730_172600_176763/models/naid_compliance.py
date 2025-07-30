# -*- coding: utf-8 -*-
""",
NAID Compliance Management
"""

from odoo import models, fields, api, _


class NAIDCompliance(models.Model):
    """,
    NAID Compliance Management
    """

    _name = "naid.compliance",
    _description = "NAID Compliance Management",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                                            """Mark as done""",
                                            self.write({'state': 'done'})
