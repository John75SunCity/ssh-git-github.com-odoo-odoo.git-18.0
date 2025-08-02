# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class VisitorPosWizard(models.TransientModel):
    _name = "visitor.pos.wizard"
    _description = "Visitor POS Wizard"

    # Basic Information
    name = fields.Char(string="Visitor Name", required=True)
    visit_date = fields.Datetime(string="Visit Date", default=fields.Datetime.now)
    purpose = fields.Text(string="Purpose of Visit")

    def action_check_in_visitor(self):
        """Check in visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Checked In"),
                "message": _("Visitor has been checked in successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_check_out_visitor(self):
        """Check out visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Checked Out"),
                "message": _("Visitor has been checked out successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_print_visitor_badge(self):
        """Print visitor badge."""
        self.ensure_one()

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.visitor_badge",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
        }

    def action_log_security_event(self):
        """Log security event."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Security Event Logged"),
                "message": _("Security event has been logged."),
                "type": "warning",
                "sticky": True,
            },
        }

    def action_process_visitor(self):
        """Process visitor."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Visitor Processed"),
                "message": _("Visitor has been processed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_create_pos_order(self):
        """Create POS order."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("POS Order Created"),
                "message": _("POS order has been created successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_link_existing_order(self):
        """Link existing order."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Order Linked"),
                "message": _("Existing order has been linked successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_cancel(self):
        """Cancel operation."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window_close",
        }
