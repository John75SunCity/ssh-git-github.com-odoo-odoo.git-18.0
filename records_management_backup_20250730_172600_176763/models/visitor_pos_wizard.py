# -*- coding: utf-8 -*-
""",
Wizard to Link POS Transaction to Visitor
"""

from odoo import models, fields, api, _


class VisitorPosWizard(models.Model):
    """,
    Wizard to Link POS Transaction to Visitor
    """

    _name = "visitor.pos.wizard",
    _description = "Wizard to Link POS Transaction to Visitor",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                                                    """Mark as done""",
                                                    self.write({'state': 'done'})
