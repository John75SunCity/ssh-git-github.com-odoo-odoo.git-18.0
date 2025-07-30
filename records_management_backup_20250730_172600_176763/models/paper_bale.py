# -*- coding: utf-8 -*-
""",
Paper Bale
"""

from odoo import models, fields, api, _


class PaperBale(models.Model):
    """,
    Paper Bale
    """

    _name = "paper.bale",
    _description = "Paper Bale",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                                    """Mark as done""",
                                    self.write({'state': 'done'})
