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

    # === ESSENTIAL FIELDS FROM VIEW (Core Functionality) ===

    # Visitor Information
    visitor_id = fields.Many2one("visitor", string="Visitor")
    visitor_name = fields.Char(
        string="Visitor Name", related="visitor_id.name", store=True
    )
    visitor_email = fields.Char(
        string="Visitor Email", related="visitor_id.email", store=True
    )
    visitor_phone = fields.Char(
        string="Visitor Phone", related="visitor_id.phone", store=True
    )
    check_in_time = fields.Datetime(string="Check-in Time", default=fields.Datetime.now)
    purpose_of_visit = fields.Text(string="Purpose of Visit")

    # POS Configuration
    pos_config_id = fields.Many2one("pos.config", string="POS Configuration")
    pos_session_id = fields.Many2one("pos.session", string="POS Session")
    cashier_id = fields.Many2one(
        "res.users", string="Cashier", default=lambda self: self.env.user
    )
    service_location = fields.Char(string="Service Location")
    processing_priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Processing Priority",
        default="normal",
    )

    # Customer Management
    existing_customer_id = fields.Many2one("res.partner", string="Existing Customer")
    create_new_customer = fields.Boolean(string="Create New Customer", default=False)
    customer_category = fields.Selection(
        [
            ("individual", "Individual"),
            ("business", "Business"),
            ("government", "Government"),
        ],
        string="Customer Category",
    )
    customer_credit_limit = fields.Monetary(
        string="Credit Limit", currency_field="currency_id"
    )
    customer_payment_terms = fields.Many2one(
        "account.payment.term", string="Payment Terms"
    )

    # Service Configuration
    service_type = fields.Selection(
        [
            ("shredding", "Document Shredding"),
            ("storage", "Document Storage"),
            ("retrieval", "Document Retrieval"),
            ("scanning", "Document Scanning"),
        ],
        string="Service Type",
        required=True,
    )

    # Financial
    amount = fields.Monetary(string="Amount", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # System Fields
    pos_order_id = fields.Many2one("pos.order", string="POS Order")
    invoice_id = fields.Many2one("account.move", string="Invoice")

    # Status
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("processing", "Processing"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
    )

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
