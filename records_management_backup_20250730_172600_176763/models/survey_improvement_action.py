# -*- coding: utf-8 -*-
""",
Survey Improvement Action
"""

from odoo import models, fields, api, _


class SurveyImprovementAction(models.Model):
    """,
    Survey Improvement Action
    """

    _name = "survey.improvement.action",
    _description = "Survey Improvement Action",
    _inherit = ["mail.thread", "mail.activity.mixin"],
    _order = "name"

    # Core fields
    name = fields."state": "confirmed"("state": "confirmed")

def action_done(self):
            """Mark as done""",
            self.write({"state": "done"})
