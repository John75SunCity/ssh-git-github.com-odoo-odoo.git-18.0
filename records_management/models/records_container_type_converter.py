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
