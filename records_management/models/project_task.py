# -*- coding: utf-8 -*-
"""
Temporary Model
"""

from odoo import models, fields, api, _


class ProjectTask(models.Model):
    """
    Extends the core Project Task model to add fields and functionality
    for records management operations, such as linking tasks to containers
    and pickup requests.
    """
    _inherit = "project.task"

    # Add new fields to the existing project.task model
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Container associated with this task.",
    )
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="The pickup request that generated this task.",
    )
    task_type = fields.Selection(
        selection_add=[
            ("pickup", "Pickup"),
            ("delivery", "Delivery"),
            ("destruction", "Destruction"),
        ],
        string="Records Task Type",
        help="Specific type of records management task.",
    )

    # You can also modify existing fields, for example, to make one required
    @api.model
    def _setup_fields(self):
        super()._setup_fields()
        # Example of modifying an existing field property
        if "user_id" in self._fields:
            self._fields["user_id"].required = True

    # You can add new methods or override existing ones
    def action_view_related_container(self):
        """Action to open the related container's form view."""
        self.ensure_one()
        if not self.container_id:
            return
        return {
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "view_mode": "form",
            "res_id": self.container_id.id,
            "target": "current",
        }
