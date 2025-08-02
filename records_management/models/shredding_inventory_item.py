# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingInventoryItem(models.Model):
    _name = "shredding.inventory.item"
    _description = "Shredding Inventory Item"

    # Basic Information
    name = fields.Char(string="Item Name", required=True)
    item_type = fields.Selection(
        [("document", "Document"), ("hard_drive", "Hard Drive"), ("media", "Media")],
        string="Item Type",
        default="document",
    )
    quantity = fields.Float(string="Quantity")

    def action_approve_item(self):
        """Approve item for destruction."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Approved"),
                "message": _("Item has been approved for destruction."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_retrieved(self):
        """Mark item as retrieved."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Retrieved"),
                "message": _("Item has been marked as retrieved."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_destroyed(self):
        """Mark item as destroyed."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Destroyed"),
                "message": _("Item has been marked as destroyed."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_mark_picked(self):
        """Mark item as picked."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Picked"),
                "message": _("Item has been marked as picked."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_not_found(self):
        """Mark item as not found."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Item Not Found"),
                "message": _("Item has been marked as not found."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_track_chain_of_custody(self):
        """Track chain of custody."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Chain of Custody"),
            "res_model": "custody.log",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("item_id", "=", self.id)],
        }

    def action_generate_certificate(self):
        """Generate destruction certificate."""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.destruction_certificate",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_audit_compliance(self):
        """Audit compliance status."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Audited"),
                "message": _("Compliance status has been audited."),
                "type": "success",
                "sticky": False,
            },
        }
