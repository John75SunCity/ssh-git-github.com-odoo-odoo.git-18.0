# -*- coding: utf-8 -*-
""",
Destruction Item
"""

from odoo import models, fields, api, _


class DestructionItem(models.Model):
    """,
    Destruction Item
    """

    _name = "destruction.item",
    _description = "Destruction Item",
    _inherit = ["mail.thread", "mail.activity.mixin"],
    _order = "name"

    # Core fields
    name = fields."state": "confirmed"("state": "confirmed")

def action_done(self):
            """Mark as done""",
            self.write({"state": "done"})
