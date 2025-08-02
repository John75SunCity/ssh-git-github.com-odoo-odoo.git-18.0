# -*- coding: utf-8 -*-
"""
Customer Inventory Report
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class CustomerInventoryReport(models.Model):
    """
    Customer Inventory Report
    """

    _name = "customer.inventory.report"
    _description = "Customer Inventory Report"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm_report(self):
        """Confirm inventory report for processing."""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft reports can be confirmed."))

        # Update state and notes
        self.write(
            {
                "state": "confirmed",
                "notes": (self.notes or "")
                + _("\nReport confirmed on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create confirmation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory report confirmed: %s") % self.name,
            note=_(
                "Customer inventory report has been confirmed and is ready for processing."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Inventory report confirmed: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Report Confirmed"),
                "message": _(
                    "Inventory report %s has been confirmed and is ready for processing."
                )
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_generate_pdf_report(self):
        """Generate PDF version of inventory report."""
        self.ensure_one()

        # Create PDF generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("PDF report generated: %s") % self.name,
            note=_(
                "PDF version of inventory report has been generated and is ready for distribution."
            ),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("PDF report generated: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.customer_inventory_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_send_to_customer(self):
        """Send inventory report to customer."""
        self.ensure_one()
        if self.state != "confirmed":
            raise UserError(_("Only confirmed reports can be sent to customers."))

        # Update state and notes
        self.write(
            {
                "state": "done",
                "notes": (self.notes or "")
                + _("\nSent to customer on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create send activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Report sent to customer: %s") % self.name,
            note=_("Inventory report has been successfully sent to the customer."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Inventory report sent to customer: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Send Report"),
            "res_model": "mail.compose.message",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_model": "customer.inventory.report",
                "default_res_id": self.id,
                "default_composition_mode": "comment",
                "default_subject": _("Inventory Report: %s") % self.name,
                "default_body": _("Please find attached your inventory report."),
            },
        }

    def action_view_boxes(self):
        """View all boxes included in this inventory report."""
        self.ensure_one()

        # Create activity to track box viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory boxes reviewed: %s") % self.name,
            note=_("All boxes included in this inventory report have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Boxes: %s") % self.name,
            "res_model": "records.box",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_location": True,
            },
        }

    def action_view_documents(self):
        """View all documents included in this inventory report."""
        self.ensure_one()

        # Create activity to track document viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Inventory documents reviewed: %s") % self.name,
            note=_(
                "All documents included in this inventory report have been reviewed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Documents: %s") % self.name,
            "res_model": "records.document",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_type": True,
            },
        }

    def action_view_locations(self):
        """View all locations included in this inventory report."""
        self.ensure_one()

        # Create activity to track location viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Inventory locations reviewed: %s") % self.name,
            note=_(
                "All locations included in this inventory report have been reviewed."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Inventory Locations: %s") % self.name,
            "res_model": "records.location",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("inventory_report_id", "=", self.id)],
            "context": {
                "default_inventory_report_id": self.id,
                "search_default_inventory_report_id": self.id,
                "search_default_group_by_zone": True,
            },
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
