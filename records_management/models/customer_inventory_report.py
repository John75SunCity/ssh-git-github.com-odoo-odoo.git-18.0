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
    # === COMPREHENSIVE MISSING FIELDS ===
    sequence = fields.Integer(string='Sequence', default=10, tracking=True)
    created_date = fields.Date(string='Date', default=fields.Date.today, tracking=True)
    updated_date = fields.Date(string='Date', tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    customer_id = fields.Many2one('res.partner', string='Customer', tracking=True)
    document_count = fields.Integer(string='Document Count', default=0)
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    # Customer Inventory Report Fields
    active_locations = fields.Integer('Active Locations', default=0)
    container_ids = fields.Many2many('records.container', string='Containers')
    document_ids = fields.Many2many('records.document', string='Documents')
    document_type_id = fields.Many2one('records.document.type', 'Document Type')
    location_id = fields.Many2one('records.location', 'Location')
    archived_document_count = fields.Integer('Archived Document Count', default=0)
    compliance_status_summary = fields.Text('Compliance Status Summary')
    destruction_eligible_count = fields.Integer('Destruction Eligible Count', default=0)
    last_inventory_audit_date = fields.Date('Last Inventory Audit Date')
    pending_retrieval_count = fields.Integer('Pending Retrieval Count', default=0)
    retention_policy_violations = fields.Integer('Retention Policy Violations', default=0)
    total_storage_cost = fields.Monetary('Total Storage Cost', currency_field='currency_id')
    # Customer Inventory Report Fields



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
            "res_model": "records.container",
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
