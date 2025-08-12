# -*- coding: utf-8 -*-
"""
Customer Inventory Management Module

This module provides comprehensive customer inventory tracking and reporting capabilities
for the Records Management System. It enables real-time visibility into customer assets,
automated reporting, and advanced analytics with complete audit trails.
"""

import logging

from odoo import api, fields, models, _

from odoo.exceptions import UserError, ValidationError



_logger = logging.getLogger(__name__)


class CustomerInventory(models.Model):
    """
    Customer Inventory Management with Real-time Tracking

    Provides comprehensive inventory visibility and reporting for customer assets
    including containers, documents, and location-based analytics.
    """

    _name = "customer.inventory"
    _description = "Customer Inventory"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "report_date desc, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Inventory Report Name", required=True, tracking=True, index=True
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # CUSTOMER INFORMATION FIELDS
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )

    # ============================================================================
    # INVENTORY STATUS FIELDS
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("in_progress", "In Progress"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),
        ],
        string="State",
        default="draft",
        tracking=True,
        required=True,
    )

    status = fields.Selection(
        [("new", "New"), ("in_progress", "In Progress"), ("completed", "Completed")],
        string="Status",
        default="new",
        tracking=True,
    )

    # ============================================================================
    # REPORT CONFIGURATION FIELDS
    # ============================================================================
    report_date = fields.Date(
        string="Report Date", default=fields.Date.today, required=True, tracking=True
    )
    created_date = fields.Date(
        string="Created Date", default=fields.Date.today, tracking=True
    )
    stored_date = fields.Date(string="Stored Date", tracking=True)

    # ============================================================================
    # FILTERING AND GROUPING FIELDS
    # ============================================================================
    document_type_id = fields.Many2one(
        "records.document.type",
        string="Document Type Filter",
        help="Filter inventory by specific document type",
    )
    location_id = fields.Many2one(
        "records.location",
        string="Location Filter",
        help="Filter inventory by specific location",
    )

    group_by_status = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("pending", "Pending"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
        ],
        string="Group By Status",
        default="draft",
    )

    group_by_date = fields.Date(string="Group By Date")

    # ============================================================================
    # VOLUME CATEGORIZATION FIELDS
    # ============================================================================
    volume_category = fields.Selection(
        [
            ("small", "Small Volume"),
            ("medium", "Medium Volume"),
            ("large", "Large Volume"),
            ("very_large", "Very Large Volume"),
        ],
        string="Volume Category",
        compute="_compute_volume_category",
        store=True,
    )

    # ============================================================================
    # INVENTORY STATISTICS FIELDS
    # ============================================================================
    total_boxes = fields.Integer(
        string="Total Boxes",
        compute="_compute_inventory_totals",
        store=True,
        help="Total number of containers for this customer",
    )
    total_documents = fields.Integer(
        string="Total Documents",
        compute="_compute_inventory_totals",
        store=True,
        help="Total number of documents for this customer",
    )
    active_locations = fields.Integer(
        string="Active Locations", compute="_compute_location_stats", store=True
    )

    # ============================================================================
    # WORKFLOW STATUS FIELDS
    # ============================================================================
    confirmed = fields.Boolean(string="Confirmed", default=False, tracking=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    container_ids = fields.One2many(
        "records.container",
        "partner_id",
        string="Containers",
        help="Containers belonging to this customer",
        readonly=True,
    )
    document_ids = fields.One2many(
        "records.document",
        "partner_id",
        string="Documents",
        help="Documents belonging to this customer",
        readonly=True,
    )

    # ============================================================================
    # NOTES AND DOCUMENTATION FIELDS
    # ============================================================================
    notes = fields.Text(string="Notes", tracking=True)

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("container_ids", "document_ids")
    def _compute_inventory_totals(self):
        """Calculate total boxes and documents for the customer"""
        for record in self:
            if record.customer_id:
                # Get all containers for this customer
                containers = self.env["records.container"].search(
                    [("partner_id", "=", record.customer_id.id)]
                )
                # Get all documents for this customer
                documents = self.env["records.document"].search(
                    [("partner_id", "=", record.customer_id.id)]
                )
                record.total_boxes = len(containers)
                record.total_documents = len(documents)
            else:
                record.total_boxes = 0
                record.total_documents = 0

    @api.depends("total_boxes")
    def _compute_volume_category(self):
        """Categorize customers by volume"""
        for record in self:
            if record.total_boxes <= 50:
                record.volume_category = "small"
            elif record.total_boxes <= 200:
                record.volume_category = "medium"
            elif record.total_boxes <= 1000:
                record.volume_category = "large"
            else:
                record.volume_category = "very_large"

    @api.depends("customer_id")
    def _compute_location_stats(self):
        """Calculate active location count for customer"""
        for record in self:
            if record.customer_id:
                # Count unique locations where customer has containers
                locations = (
                    self.env["records.container"]
                    .search(
                        [
                            ("partner_id", "=", record.customer_id.id),
                            ("location_id", "!=", False),
                        ]
                    )
                    .mapped("location_id")
                )
                record.active_locations = len(locations)
            else:
                record.active_locations = 0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm_report(self):
        """Confirm the inventory report"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft reports can be confirmed"))
        self.write({"state": "confirmed", "confirmed": True})
        self.message_post(body=_("Inventory report confirmed"))

    def action_generate_pdf_report(self):
        """Generate PDF inventory report"""

        self.ensure_one()
        return self.env.ref(
            "records_management.action_customer_inventory_report"
        ).report_action(self)

    def action_send_to_customer(self):
        """Send inventory report to customer"""

        self.ensure_one()
        if not self.customer_id.email:
            raise UserError(_("Customer has no email address"))

        # Generate and send report
        template = self.env.ref(
            "records_management.email_template_inventory_report", False
        )
        if template:
            template.send_mail(self.id)
        self.message_post(body=_("Inventory report sent to customer"))

    def action_view_boxes(self):
        """View customer containers"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Containers"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.customer_id.id)],
            "context": {"default_partner_id": self.customer_id.id},
        }

    def action_view_documents(self):
        """View customer documents"""

        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("partner_id", "=", self.customer_id.id)],
            "context": {"default_partner_id": self.customer_id.id},
        }

    def action_view_locations(self):
        """View customer locations"""

        self.ensure_one()
        container_locations = (
            self.env["records.container"]
            .search(
                [("partner_id", "=", self.customer_id.id), ("location_id", "!=", False)]
            )
            .mapped("location_id")
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Customer Locations"),
            "res_model": "records.location",
            "view_mode": "tree,form",
            "domain": [("id", "in", container_locations.ids)],
        }

    def action_refresh_data(self):
        """Refresh inventory data"""

        self.ensure_one()
        # Force recompute of all computed fields
        self._compute_inventory_totals()
        self._compute_volume_category()
        self._compute_location_stats()
        self.message_post(body=_("Inventory data refreshed"))

    # ============================================================================
    # OVERRIDE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create inventory records with auto-generated sequence numbers"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "customer.inventory"
                ) or _("New")
        return super().create(vals_list)

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("report_date")
    def _check_report_date(self):
        """Validate report date is not in the future"""
        for record in self:
            if record.report_date and record.report_date > fields.Date.today():
                raise ValidationError(_("Report date cannot be in the future"))

    @api.constrains("customer_id")
    def _check_customer_id(self):
        """Validate customer is set"""
        for record in self:
            if not record.customer_id:
                raise ValidationError(_("Customer must be specified"))
