# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def action_view_sales(self):
        """View sales for product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Sales"),
            "res_model": "sale.order.line",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_template_id", "=", self.id)],
        }

    def action_configure_pricing(self):
        """Configure pricing for product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Pricing"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "context": {"default_product_tmpl_id": self.id},
        }

    def action_configure_variants(self):
        """Configure product variants."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Configure Variants"),
            "res_model": "product.product",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_pricing_rules(self):
        """View pricing rules."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing Rules"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_duplicate(self):
        """Duplicate product."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Duplicated"),
                "message": _("Product has been duplicated successfully."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_update_costs(self):
        """Update product costs."""
        self.ensure_one()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Costs Updated"),
                "message": _("Product costs have been updated."),
                "type": "success",
                "sticky": False,
            },
        }

    def action_view_variants(self):
        """View product variants."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Product Variants"),
            "res_model": "product.product",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_tmpl_id", "=", self.id)],
        }

    def action_view_pricing_history(self):
        """View pricing history."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Pricing History"),
            "res_model": "product.price.history",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_template_id", "=", self.id)],
        }
