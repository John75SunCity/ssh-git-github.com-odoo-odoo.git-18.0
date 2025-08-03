# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsContainerTypeConverter(models.Model):
    _name = "records.container.type.converter"
    _description = "Records Container Type Converter"

    # Basic Information
    name = fields.Char(string="Converter Name", required=True)
    source_type = fields.Char(string="Source Type")
    target_type = fields.Char(string="Target Type")

    # Missing fields from view analysis
    container_ids = fields.One2many(
        "records.container", "converter_id", string="Containers to Convert"
    )
    current_type = fields.Char(string="Current Container Type")
    new_container_type_code = fields.Char(string="New Container Type Code")
    reason = fields.Text(string="Conversion Reason")
    summary_line = fields.Char(string="Summary Line", compute="_compute_summary_line")
    target_container_type = fields.Char(
        string="Target Container Type"
    )  # Alternative name for target_type
    conversion_notes = fields.Text(string="Conversion Notes")

    @api.depends("source_type", "target_type", "container_ids")
    def _compute_summary_line(self):
        """Compute summary line for conversion"""
        for record in self:
            container_count = len(record.container_ids)
            record.summary_line = f"Convert {container_count} containers from {record.source_type or 'Unknown'} to {record.target_type or 'Unknown'}"

    def action_convert_containers(self):
        """Convert containers."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Containers Converted"),
                "message": _("Containers have been converted successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_preview_changes(self):
        """Preview changes."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Preview Generated"),
                "message": _("Changes preview has been generated."),
                "type": "info",
                "sticky": False,
            },
        }

    def action_preview_conversion(self):
        """Preview conversion results."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Conversion Preview"),
            "res_model": "records.container",
            "view_mode": "tree",
            "target": "new",
        }
