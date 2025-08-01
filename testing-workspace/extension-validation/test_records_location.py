# -*- coding: utf-8 -*-
# TEST FILE - Extension Validation for records.location model
# TESTING WORKSPACE - DO NOT USE IN PRODUCTION

from odoo import models, fields, api, _


class RecordsLocationTest(models.Model):
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Basic Information
    name = fields.Char(string="Location Name", required=True, tracking=True)
    code = fields.Char(string="Location Code", index=True)
    description = fields.Text(string="Description")

    # Status and Control
    status = fields.Selection(
        [
            ("available", "Available"),
            ("full", "Full"),
            ("maintenance", "Maintenance"),
            ("restricted", "Restricted"),
        ],
        string="Status",
        default="available",
        tracking=True,
    )

    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("storage", "Storage Facility"),
            ("archive", "Archive"),
            ("vault", "Secure Vault"),
        ],
        string="Location Type",
        default="storage",
        tracking=True,
    )

    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    # Physical Properties and Location Details
    building = fields.Char(string="Building", tracking=True)
    zone = fields.Char(string="Zone", tracking=True)
    climate_controlled = fields.Boolean(string="Climate Controlled", default=False)
    access_level = fields.Selection(
        [
            ("public", "Public"),
            ("restricted", "Restricted"),
            ("secure", "Secure"),
            ("high_security", "High Security"),
        ],
        string="Access Level",
        default="restricted",
        tracking=True,
    )
    max_capacity = fields.Float(string="Maximum Capacity")
    capacity = fields.Float(string="Capacity")
    current_usage = fields.Float(string="Current Usage")

    # Relationships
    container_ids = fields.One2many(
        "records.container", "location_id", string="Containers"
    )

    # Action Methods
    def action_set_maintenance(self):
        """Set location to maintenance mode."""
        self.write({"status": "maintenance"})

    def action_set_available(self):
        """Make location available."""
        self.write({"status": "available"})
