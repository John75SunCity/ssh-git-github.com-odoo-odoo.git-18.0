# -*- coding: utf-8 -*-
"""
Work Order Bin Assignment Wizard
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WorkOrderBinAssignmentWizard(models.TransientModel):
    """
    Work Order Bin Assignment Wizard
    Wizard for assigning bins to work orders efficiently
    """

    _name = "work.order.bin.assignment.wizard"
    _description = "Work Order Bin Assignment Wizard"

    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string="Assignment Reference", default="Bin Assignment")
    work_order_id = fields.Many2one(
        "work.order.shredding", string="Work Order", required=True
    )
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="work_order_id.customer_id",
        readonly=True,
    )

    # ==========================================
    # ASSIGNMENT CONFIGURATION
    # ==========================================
    assignment_type = fields.Selection(
        [
            ("manual", "Manual Selection"),
            ("auto", "Automatic Assignment"),
            ("bulk", "Bulk Assignment"),
            ("criteria", "Criteria-Based"),
        ],
        string="Assignment Type",
        default="manual",
        required=True,
    )

    # ==========================================
    # BIN SELECTION CRITERIA
    # ==========================================
    location_ids = fields.Many2many("records.location", string="Filter by Locations")
    department_ids = fields.Many2many(
        "records.department", string="Filter by Departments"
    )

    bin_state = fields.Selection(
        [
            ("any", "Any State"),
            ("stored", "Stored Only"),
            ("retrieved", "Retrieved Only"),
            ("pending", "Pending Destruction"),
        ],
        string="Bin State Filter",
        default="stored",
    )

    date_from = fields.Date(string="From Date")
    date_to = fields.Date(string="To Date")

    priority_level = fields.Selection(
        [
            ("low", "Low Priority"),
            ("normal", "Normal Priority"),
            ("high", "High Priority"),
            ("urgent", "Urgent"),
        ],
        string="Priority Level",
        default="normal",
    )

    # ==========================================
    # SELECTION RESULTS
    # ==========================================
    available_bin_ids = fields.Many2many(
        "records.container",
        "wizard_available_bins_rel",
        string="Available Bins",
        help="Bins matching selection criteria",
    )
    selected_bin_ids = fields.Many2many(
        "records.container",
        "wizard_selected_bins_rel",
        string="Selected Bins",
        help="Bins selected for assignment",
    )

    # ==========================================
    # STATISTICS
    # ==========================================
    total_available = fields.Integer(
        string="Total Available", compute="_compute_statistics"
    )
    total_selected = fields.Integer(
        string="Total Selected", compute="_compute_statistics"
    )
    estimated_weight = fields.Float(
        string="Estimated Weight", compute="_compute_statistics"
    )
    estimated_volume = fields.Float(
        string="Estimated Volume", compute="_compute_statistics"
    )

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    @api.depends("available_bin_ids", "selected_bin_ids")
    def _compute_statistics(self):
        """Compute assignment statistics"""
        for wizard in self:
            wizard.total_available = len(wizard.available_bin_ids)
            wizard.total_selected = len(wizard.selected_bin_ids)

            # Calculate estimated totals for selected bins
            selected_bins = wizard.selected_bin_ids
            wizard.estimated_weight = sum(selected_bins.mapped("weight"))
            # Assuming volume calculation if available
            wizard.estimated_volume = len(selected_bins) * 2.0  # Rough estimate

    # ==========================================
    # ONCHANGE METHODS
    # ==========================================
    @api.onchange("work_order_id")
    def _onchange_work_order(self):
        """Update customer when work order changes"""
        if self.work_order_id:
            self.customer_id = self.work_order_id.customer_id

    @api.onchange(
        "assignment_type",
        "location_ids",
        "department_ids",
        "bin_state",
        "date_from",
        "date_to",
    )
    def _onchange_criteria(self):
        """Update available bins when criteria change"""
        self._update_available_bins()

    # ==========================================
    # ACTION METHODS
    # ==========================================
    def action_search_bins(self):
        """Search for bins based on criteria"""
        self._update_available_bins()
        return self._return_wizard()

    def action_select_all(self):
        """Select all available bins"""
        self.selected_bin_ids = [(6, 0, self.available_bin_ids.ids)]
        return self._return_wizard()

    def action_clear_selection(self):
        """Clear selected bins"""
        self.selected_bin_ids = [(5, 0, 0)]
        return self._return_wizard()

    def action_auto_assign(self):
        """Automatically assign bins based on work order requirements"""
        if not self.work_order_id:
            raise UserError(_("Please select a work order first"))

        # Auto-assignment logic based on work order requirements
        domain = self._build_search_domain()

        # Limit to work order capacity if specified
        limit = None
        if hasattr(self.work_order_id, "max_bins"):
            limit = self.work_order_id.max_bins

        available_bins = self.env["records.container"].search(domain, limit=limit)
        self.available_bin_ids = [(6, 0, available_bins.ids)]
        self.selected_bin_ids = [(6, 0, available_bins.ids)]

        return self._return_wizard()

    def action_assign_bins(self):
        """Assign selected bins to work order"""
        if not self.selected_bin_ids:
            raise UserError(_("Please select at least one bin"))

        if not self.work_order_id:
            raise UserError(_("Work order is required"))

        # Check if work order can accept more bins
        current_bin_count = len(self.work_order_id.box_ids)
        new_bin_count = len(self.selected_bin_ids)

        # Assign bins to work order
        for bin_record in self.selected_bin_ids:
            # Update bin state if needed
            if bin_record.state not in ["retrieved", "pending"]:
                bin_record.write({"state": "retrieved"})

            # Create relationship (assuming work order has box_ids field)
            if hasattr(self.work_order_id, "box_ids"):
                self.work_order_id.write({"box_ids": [(4, bin_record.id)]})

        # Log assignment
        message = _("Assigned %d bins to work order") % len(self.selected_bin_ids)
        self.work_order_id.message_post(body=message)

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Success"),
                "message": message,
                "sticky": False,
            },
        }

    # ==========================================
    # HELPER METHODS
    # ==========================================
    def _build_search_domain(self):
        """Build search domain for bins"""
        domain = []

        # Customer filter
        if self.customer_id:
            domain.append(("customer_id", "=", self.customer_id.id))

        # Location filter
        if self.location_ids:
            domain.append(("location_id", "in", self.location_ids.ids))

        # Department filter
        if self.department_ids:
            domain.append(("department_id", "in", self.department_ids.ids))

        # State filter
        if self.bin_state != "any":
            if self.bin_state == "stored":
                domain.append(("state", "=", "stored"))
            elif self.bin_state == "retrieved":
                domain.append(("state", "=", "retrieved"))
            elif self.bin_state == "pending":
                domain.append(("state", "in", ["retrieved", "pending"]))

        # Date filters
        if self.date_from:
            domain.append(("received_date", ">=", self.date_from))
        if self.date_to:
            domain.append(("received_date", "<=", self.date_to))

        return domain

    def _update_available_bins(self):
        """Update available bins based on current criteria"""
        domain = self._build_search_domain()
        available_bins = self.env["records.container"].search(domain)
        self.available_bin_ids = [(6, 0, available_bins.ids)]

    def _return_wizard(self):
        """Return action to keep wizard open"""
        return {
            "type": "ir.actions.act_window",
            "res_model": self._name,
            "res_id": self.id,
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }

    # ==========================================
    # VALIDATION
    # ==========================================
    @api.constrains("date_from", "date_to")
    def _check_dates(self):
        """Validate date range"""
        for wizard in self:
            if wizard.date_from and wizard.date_to:
                if wizard.date_from > wizard.date_to:
                    raise ValidationError(_("From date cannot be after To date"))
