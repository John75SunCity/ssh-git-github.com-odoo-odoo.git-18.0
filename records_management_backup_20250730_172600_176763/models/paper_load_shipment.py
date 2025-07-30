# -*- coding: utf-8 -*-
""",
Paper Load Shipment
"""

from odoo import models, fields, api, _


class PaperLoadShipment(models.Model):
    """,
    Paper Load Shipment
    """

    _name = "paper.load.shipment",
    _description = "Paper Load Shipment",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

def action_done(self):
                                                                """Mark as done""",
                                                                self.write({'state': 'done'})
