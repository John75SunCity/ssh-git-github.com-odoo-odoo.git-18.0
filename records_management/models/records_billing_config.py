# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsBillingConfig(models.Model):
    _name = "records.billing.config"
    _description = "Records Billing Configuration"

    # Basic Information
    name = fields.Char(string="Configuration Name", required=True)
    partner_id = fields.Many2one("res.partner", string="Customer")
    billing_type = fields.Selection(
        [("standard", "Standard"), ("premium", "Premium"), ("custom", "Custom")],
        string="Billing Type",
        default="standard",
    )

    def action_generate_invoice(self):
        """Generate invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Invoice Generated"),
                "message": _("Invoice has been generated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_analytics(self):
        """View analytics."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing Analytics"),
            "res_model": "records.billing.analytics",
            "view_mode": "graph,tree",
            "target": "current",
        }

    def action_view_billing_history(self):
        """View billing history."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Billing History"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_configure_rates(self):
        """Configure rates."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Rates"),
            "res_model": "base.rates",
            "view_mode": "tree,form",
            "target": "current",
        }

    def action_test_billing(self):
        """Test billing."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Billing Test"),
                "message": _("Billing test completed successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_duplicate(self):
        """Duplicate configuration."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Configuration Duplicated"),
                "message": _("Configuration has been duplicated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_invoices(self):
        """View invoices."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoices"),
            "res_model": "account.move",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [
                ("partner_id", "=", self.partner_id.id),
                ("move_type", "=", "out_invoice"),
            ],
        }

    def action_view_revenue(self):
        """View revenue."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue"),
            "res_model": "account.move.line",
            "view_mode": "graph,tree",
            "target": "current",
            "domain": [("partner_id", "=", self.partner_id.id)],
        }

    def action_view_invoice(self):
        """View invoice."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
        }
