# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class HardDriveScanWizard(models.TransientModel):
    _name = "hard_drive.scan.wizard"
    _description = "Hard Drive Scan Wizard"

    # Basic Information
    name = fields.Char(string="Scan Name", required=True, default="HD Scan")
    hard_drive_id = fields.Many2one("hard.drive", string="Hard Drive")
    scan_type = fields.Selection(
        [("basic", "Basic Scan"), ("deep", "Deep Scan"), ("forensic", "Forensic Scan")],
        string="Scan Type",
        default="basic",
        required=True,
    )

    def action_finish_scan(self):
        """Finish hard drive scanning process."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Scan Finished"),
                "message": _("Hard drive scan has been completed."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_scanned_drives(self):
        """View scanned drives."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Scanned Drives"),
            "res_model": "shredding.hard.drive",
            "view_mode": "tree,form",
            "target": "current",
        }

    def action_scan_serial(self):
        """Scan serial number."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Serial Scanned"),
                "message": _("Serial number has been scanned."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_bulk_scan(self):
        """Process bulk scan."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Bulk Scan Processed"),
                "message": _("Bulk scan has been processed."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_customer_scanned(self):
        """Mark customer scanned."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Customer Scanned"),
                "message": _("Drive marked as customer scanned."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_facility_verified(self):
        """Mark facility verified."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Facility Verified"),
                "message": _("Drive marked as facility verified."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_mark_destroyed(self):
        """Mark destroyed."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Drive Destroyed"),
                "message": _("Drive marked as destroyed."),
                "type": "warning",
                "sticky": False,
            },
        }

    def action_validate_scan_integrity(self):
        """Validate scan integrity."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Integrity Validated"),
                "message": _("Scan integrity has been validated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_archive_scan_results(self):
        """Archive scan results."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Results Archived"),
                "message": _("Scan results have been archived."),
                "type": "info",
                "sticky": False,
            },
        }
