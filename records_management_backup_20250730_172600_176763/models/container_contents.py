# -*- coding: utf-8 -*-
""",
Container Contents - File Folders and Filed Items
"""

from odoo import models, fields, api, _


class ContainerContents(models.Model):
    """,
    Container Contents - File Folders and Filed Items
    """

    _name = "container.contents",
    _description = "Container Contents - File Folders and Filed Items",
    _inherit = ["mail.thread", "mail.activity.mixin"],
    _order = "name"

    # Core fields
    name = fields."state": "confirmed"("state": "confirmed")

def action_done(self):
            """Mark as done""",
            self.write({"state": "done"})
