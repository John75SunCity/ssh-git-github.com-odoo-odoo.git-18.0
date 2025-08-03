# -*- coding: utf-8 -*-
"""
Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class BarcodeProduct(models.Model):
    """
    Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅
    """

    _name = "barcode.product"
    _description = (
        "Barcode Product for Records Management - FIELD ENHANCEMENT COMPLETE ✅"
    )
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Essential Barcode Product Fields (from view analysis)
    product_category = fields.Selection(
        [
            ("container", "Container"),
            ("bin", "Shred Bin"),
            ("folder", "File Folder"),
            ("location", "Location Tag"),
        ],
        string="Product Category",
        required=True,
    )

    barcode_pattern = fields.Char(
        string="Barcode Pattern", help="Pattern for barcode generation"
    )
    barcode_length = fields.Integer(string="Barcode Length", default=10)
    barcode = fields.Char(string="Barcode", tracking=True)

    # Pricing Fields
    storage_rate = fields.Monetary(string="Storage Rate", currency_field="currency_id")
    shred_rate = fields.Monetary(string="Shredding Rate", currency_field="currency_id")
    retrieval_rate = fields.Monetary(
        string="Retrieval Rate", currency_field="currency_id"
    )
    scanning_rate = fields.Monetary(
        string="Scanning Rate", currency_field="currency_id"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Physical Specifications
    box_size = fields.Selection(
        [
            ("letter", "Letter Size"),
            ("legal", "Legal Size"),
            ("banker", "Banker Box"),
            ("archive", "Archive Box"),
            ("custom", "Custom Size"),
        ],
        string="Box Size",
    )

    capacity = fields.Float(string="Storage Capacity (cubic feet)", digits=(10, 2))
    weight_limit = fields.Float(string="Weight Limit (lbs)", digits=(10, 2))
    dimensions = fields.Char(string="Dimensions (L x W x H)")

    # Business Logic Fields
    auto_generate = fields.Boolean(string="Auto Generate Barcode", default=True)
    allowed_characters = fields.Char(string="Allowed Characters", default="0123456789")
    access_frequency = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("yearly", "Yearly"),
            ("permanent", "Permanent Storage"),
        ],
        string="Access Frequency",
        default="monthly",
    )

    # Tracking and Analytics
    average_storage_duration = fields.Float(
        string="Average Storage Duration (days)", compute="_compute_analytics"
    )
    usage_count = fields.Integer(string="Usage Count", default=0)
    last_used_date = fields.Date(string="Last Used Date")

    # Service Configuration
    billing_frequency = fields.Selection(
        [("monthly", "Monthly"), ("quarterly", "Quarterly"), ("annually", "Annually")],
        string="Billing Frequency",
        default="monthly",
    )

    service_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("enterprise", "Enterprise"),
        ],
        string="Service Level",
        default="standard",
    )

    # Compliance and Security
    destruction_required = fields.Boolean(string="Destruction Required", default=False)
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required", default=True
    )
    audit_trail_enabled = fields.Boolean(string="Audit Trail Enabled", default=True)

    # Related Records
    container_ids = fields.One2many(
        "records.container", "product_id", string="Associated Containers"
    )
    document_type_ids = fields.Many2many(
        "records.document.type", string="Allowed Document Types"
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    @api.depends("container_ids", "usage_count", "last_used_date")
    def _compute_analytics(self):
        """Compute analytics for storage duration"""
        for record in self:
            if record.container_ids:
                # Calculate average storage duration from containers
                durations = []
                for container in record.container_ids:
                    if container.created_date and container.last_activity_date:
                        duration = (
                            container.last_activity_date - container.created_date
                        ).days
                        durations.append(duration)

                record.average_storage_duration = (
                    sum(durations) / len(durations) if durations else 0
                )
            else:
                record.average_storage_duration = 0

    def action_activate(self):
        """Activate barcode product for use."""
        self.ensure_one()
        if self.state == "done":
            raise UserError(_("Cannot activate completed barcode product."))

        # Update state and notes
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nActivated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create activation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Barcode product activated: %s") % self.name,
            note=_("Barcode product has been activated and is ready for use."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcode product activated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Activated"),
                "message": _("Barcode product %s is now active and ready for use.")
                % self.name,
                "type": "success",
                "sticky": False,
            },
        }

    def action_deactivate(self):
        """Deactivate barcode product."""
        self.ensure_one()

        # Update state and notes
        self.write(
            {
                "state": "inactive",
                "active": False,
                "notes": (self.notes or "")
                + _("\nDeactivated on %s")
                % fields.Datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

        # Create deactivation activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Barcode product deactivated: %s") % self.name,
            note=_("Barcode product has been deactivated and is no longer in use."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcode product deactivated: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Product Deactivated"),
                "message": _("Barcode product %s has been deactivated.") % self.name,
                "type": "warning",
                "sticky": False,
            },
        }

    def action_generate_barcodes(self):
        """Generate barcodes for this product."""
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active products can generate barcodes."))

        # Create barcode generation activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Barcodes generated: %s") % self.name,
            note=_("Barcode labels have been generated and are ready for printing."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Barcodes generated for: %s") % self.name,
            message_type="notification",
        )

        return {
            "type": "ir.actions.report",
            "report_name": "records_management.barcode_label_report",
            "report_type": "qweb-pdf",
            "data": {"ids": self.ids},
            "context": self.env.context,
        }

    def action_update_pricing(self):
        """Update pricing for barcode product."""
        self.ensure_one()

        # Create pricing update activity
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Pricing updated: %s") % self.name,
            note=_("Pricing information has been updated for this barcode product."),
            user_id=self.user_id.id,
        )

        self.message_post(
            body=_("Pricing updated for: %s") % self.name, message_type="notification"
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Update Pricing"),
            "res_model": "product.pricelist.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
            },
        }

    def action_view_revenue(self):
        """View revenue analytics for this barcode product."""
        self.ensure_one()

        # Create revenue viewing activity
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Revenue reviewed: %s") % self.name,
            note=_("Revenue analytics and performance data has been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Revenue Analytics: %s") % self.name,
            "res_model": "sale.order.line",
            "view_mode": "graph,pivot,tree",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_confirmed_orders": True,
                "group_by": ["order_partner_id"],
            },
        }

    def action_view_shred_bins(self):
        """View shred bins associated with this barcode product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Shred Bins: %s") % self.name,
            "res_model": "shred.bin",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_group_by_location": True,
            },
        }

    def action_view_storage_boxes(self):
        """View storage boxes associated with this barcode product."""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Boxes: %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("product_id", "=", self.id)],
            "context": {
                "default_product_id": self.id,
                "search_default_product_id": self.id,
                "search_default_group_by_customer": True,
            },
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
        self.write({"state": "done"})
