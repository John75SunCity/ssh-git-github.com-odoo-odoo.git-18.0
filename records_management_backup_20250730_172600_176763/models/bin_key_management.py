# -*- coding: utf-8 -*-
""",
Bin Key Management
"""

from odoo import models, fields, api, _


class BinKeyManagement(models.Model):
    """,
    Bin Key Management
    """

    _name = "bin.key.management",
    _description = "Bin Key Management",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                    """Mark as done""",
                    self.write({'state': 'done'})
