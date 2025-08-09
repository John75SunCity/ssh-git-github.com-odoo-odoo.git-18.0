# -*- coding: utf-8 -*-
"""
Pickup Request Management Module

See RECORDS_MANAGEMENT_SYSTEM_MANUAL.md - Section 8: Pickup Request Management Module
for comprehensive documentation, business processes, and integration details.:
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _

class PickupRequest(models.Model):
    """
    Pickup Request Management - Customer document and equipment pickup requests
    Handles complete pickup workflows from submission to completion
    """

    _name = "pickup.request"
    _description = "Pickup Request"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True),
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda self: self.env.company
    ),
    user_id = fields.Many2one(
        "res.users", required=True, default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,

    # Common fields
    )
    description = fields.Text(),
    notes = fields.Text()
    date = fields.Date(default=lambda self: fields.Date.today()
    help_text = fields.Char(string="Help"),
    res_model = fields.Char(string="Res Model")
    view_mode = fields.Selection(
        [
            ("form", "Form"),
            ("tree", "List"),
            ("kanban", "Kanban"),
            ("calendar", "Calendar"),
            ("gantt", "Gantt"),
        ]),
        string="View Mode",
        default="form",
        help="Specifies the UI view mode for this pickup request.",

    # Location tracking
    )
    location_id = fields.Many2one(
        "records.location", string="Pickup Location", tracking=True
    )

    def action_confirm(self):
        """
        Confirm the pickup request.

        This method transitions the pickup request from 'draft' to 'confirmed' state,
        indicating that the request has been reviewed and approved for processing.
        Side effects: updates the 'state' field and triggers any associated automation or notifications.
        """
        self.write({"state": "confirmed"})

    def action_done(self):
        """
        Mark the pickup request as done.

        This method updates the state of the pickup request to 'done'.
        Any additional business logic, such as triggering notifications,
        updating related records, or logging completion, should be implemented here.
        """
        self.write({"state": "done"})
        """Mark as done"""
        self.write({"state": "done"})