# -*- coding: utf-8 -*-
""",
Portal Customer Feedback
"""

from odoo import models, fields, api, _


class PortalFeedback(models.Model):
    """,
    Portal Customer Feedback
    """

    _name = "portal.feedback",
    _description = "Portal Customer Feedback",
    _inherit = ['mail.thread', 'mail.activity.mixin'],
    _order = "name"

    # Core fields
    name = fields.'state': 'confirmed'('state': 'confirmed')

    def action_done(self):
        pass
    """Mark as done""",
        self.write({'state': 'done'})
