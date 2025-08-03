# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RecordsLocation(models.Model):
    _name = "records.location"
    _description = "Records Storage Location"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Basic Information
    name = fields.Char(string="Location Name", required=True, tracking=True)
    code = fields.Char(string="Location Code", index=True)
    description = fields.Text(string="Description")
    building = fields.Char(string="Building")
    zone = fields.Char(string="Zone")

    # Location specifications
    location_type = fields.Selection(
        [
            ("warehouse", "Warehouse"),
            ("office", "Office"),
            ("storage", "Storage"),
            ("vault", "Vault"),
        ],
        string="Location Type",
    )
    access_level = fields.Selection(
        [
            ("public", "Public"),
            ("restricted", "Restricted"),
            ("confidential", "Confidential"),
            ("top_secret", "Top Secret"),
        ],
        string="Access Level",
    )
    climate_controlled = fields.Boolean(string="Climate Controlled", default=False)
    max_capacity = fields.Integer(string="Max Capacity")

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

    active = fields.Boolean(string="Active", default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )

    # Physical Properties
    capacity = fields.Float(string="Capacity")
    current_usage = fields.Float(string="Current Usage")

    # Relationships
    container_ids = fields.One2many(
        "records.container", "location_id", string="Containers"
    )
    # === COMPREHENSIVE MISSING FIELDS ===
    active = fields.Boolean(string='Flag', default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    notes = fields.Text(string='Description', tracking=True)
    state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Status', default='draft', tracking=True)
    created_date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string='Date', tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    warehouse_id = fields.Many2one('stock.warehouse', string='Warehouse')
    aisle = fields.Char(string='Aisle')
    rack = fields.Char(string='Rack')
    shelf = fields.Char(string='Shelf')
    utilization = fields.Float(string='Utilization %', digits=(5, 2))
    temperature_controlled = fields.Boolean(string='Temperature Controlled')



    # Action Methods
    def action_location_report(self):
        """Generate location utilization report."""
        self.ensure_one()

        # Create report generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Location report generated: %s") % self.name,
            note=_("Location utilization and capacity report has been generated."),
            user_id=self.env.user.id,
        )

        self.message_post(
            body=_("Location report generated for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.location_utilization_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_view_boxes(self):
        """View all boxes stored in this location."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Boxes in Location: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("location_id", "=", self.id)],
            "context": {
                "default_location_id": self.id,
                "search_default_location_id": self.id,
                "search_default_group_by_status": True,
            },
        }

    def action_set_maintenance(self):
        """Set location to maintenance mode."""
        self.write({"status": "maintenance"})

    def action_set_available(self):
        """Make location available."""
        self.write({"status": "available"})
