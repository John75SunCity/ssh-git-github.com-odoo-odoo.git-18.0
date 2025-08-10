# -*- coding: utf-8 -*-
"""
Service Item Management Module

This module provides comprehensive service item management functionality for the Records
Management System. It handles equipment, vehicles, tools, and personnel resources used
in records management operations with complete lifecycle tracking, maintenance scheduling,
and performance monitoring.

Key Features:
- Multi-category service item management (equipment, vehicles, tools, personnel)
- Complete lifecycle tracking from purchase to retirement
- Maintenance scheduling with interval-based alerts
- Capacity and performance monitoring with utilization tracking
- Financial tracking with purchase cost and depreciation
- Integration with service requests and operational workflows

Business Processes:
1. Item Registration: Register new service items with specifications and financial data
2. Assignment Management: Assign items to users, departments, and locations
3. Maintenance Scheduling: Automated maintenance alerts and service tracking
4. Performance Monitoring: Track utilization rates and efficiency ratings
5. Lifecycle Management: Manage item states from draft to retirement
6. Service Integration: Link items to service requests and operational tasks

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ServiceItem(models.Model):
    _name = "service.item"
    _description = "Service Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Service Item Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for this service item",
    )
    description = fields.Text(
        string="Description", help="Detailed description of the service item"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this service item",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # Partner Relationship
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Under Maintenance"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the service item",
    )

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    service_type = fields.Selection(
        [
            ("pickup", "Pickup Service"),
            ("shredding", "Shredding Service"),
            ("destruction", "Destruction Service"),
            ("storage", "Storage Service"),
            ("retrieval", "Document Retrieval"),
            ("transport", "Transport Service"),
            ("scanning", "Scanning Service"),
            ("consultation", "Consultation Service"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
        help="Type of service this item supports",
    )

    category = fields.Selection(
        [
            ("equipment", "Equipment"),
            ("vehicle", "Vehicle"),
            ("container", "Container"),
            ("tool", "Tool"),
            ("software", "Software"),
            ("personnel", "Personnel"),
        ],
        string="Category",
        required=True,
        tracking=True,
        help="Category classification of the service item",
    )

    # ============================================================================
    # ITEM SPECIFICATIONS
    # ============================================================================
    model_number = fields.Char(string="Model Number", help="Manufacturer model number")
    serial_number = fields.Char(
        string="Serial Number",
        index=True,
        help="Unique serial number for identification",
    )
    manufacturer = fields.Char(
        string="Manufacturer", help="Equipment or item manufacturer"
    )
    purchase_date = fields.Date(
        string="Purchase Date", tracking=True, help="Date of purchase or acquisition"
    )
    warranty_expiry = fields.Date(
        string="Warranty Expiry", tracking=True, help="Warranty expiration date"
    )

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    )
    purchase_cost = fields.Monetary(
        string="Purchase Cost",
        currency_field="currency_id",
        help="Original purchase cost",
    )
    current_value = fields.Monetary(
        string="Current Value",
        currency_field="currency_id",
        help="Current estimated value",
    )
    maintenance_cost = fields.Monetary(
        string="Total Maintenance Cost",
        currency_field="currency_id",
        help="Cumulative maintenance costs",
    )
    depreciation_rate = fields.Float(
        string="Annual Depreciation Rate %",
        default=10.0,
        help="Annual depreciation percentage",
    )

    # ============================================================================
    # OPERATIONAL STATUS
    # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        help="Current physical location",
    )
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        tracking=True,
        help="User currently assigned to this item",
    )
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        tracking=True,
        help="Department responsible for this item",
    )

    # ============================================================================
    # MAINTENANCE TRACKING
    # ============================================================================
    last_maintenance = fields.Date(
        string="Last Maintenance",
        tracking=True,
        help="Date of last maintenance service",
    )
    next_maintenance = fields.Date(
        string="Next Maintenance",
        compute="_compute_next_maintenance",
        store=True,
        help="Calculated next maintenance date",
    )
    maintenance_interval = fields.Integer(
        string="Maintenance Interval (days)",
        default=90,
        help="Number of days between maintenance services",
    )
    maintenance_due = fields.Boolean(
        string="Maintenance Due",
        compute="_compute_maintenance_due",
        store=True,
        help="Whether maintenance is currently due",
    )

    # ============================================================================
    # CAPACITY & PERFORMANCE
    # ============================================================================
    capacity = fields.Float(
        string="Capacity", help="Maximum capacity of the service item"
    )
    capacity_unit = fields.Selection(
        [
            ("kg", "Kilograms"),
            ("pieces", "Pieces"),
            ("hours", "Hours"),
            ("boxes", "Boxes"),
            ("pages", "Pages"),
            ("liters", "Liters"),
            ("cubic_meters", "Cubic Meters"),
        ],
        string="Capacity Unit",
        default="pieces",
        help="Unit of measurement for capacity",
    )
    utilization_rate = fields.Float(
        string="Utilization Rate %",
        default=0.0,
        digits=(5, 2),
        help="Current utilization percentage",
    )
    efficiency_rating = fields.Selection(
        [
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        ],
        string="Efficiency Rating",
        default="good",
        help="Performance efficiency rating",
    )

    # ============================================================================
    # COMPUTED STATUS FIELDS
    # ============================================================================
    warranty_status = fields.Selection(
        [
            ("active", "Active"),
            ("expired", "Expired"),
            ("unknown", "Unknown"),
        ],
        string="Warranty Status",
        compute="_compute_warranty_status",
        store=True,
        help="Current warranty status",
    )
    age_months = fields.Integer(
        string="Age (Months)",
        compute="_compute_age",
        store=True,
        help="Age of the item in months",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    service_request_ids = fields.One2many(
        "portal.request",
        "service_item_id",
        string="Service Requests",
        help="Service requests using this item",
    )
    maintenance_request_ids = fields.One2many(
        "maintenance.request",
        "equipment_id",
        string="Maintenance Requests",
        help="Maintenance requests for this item",
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    specifications = fields.Text(
        string="Technical Specifications", help="Detailed technical specifications"
    )
    operating_instructions = fields.Text(
        string="Operating Instructions", help="Instructions for operating the item"
    )
    safety_notes = fields.Text(
        string="Safety Notes", help="Important safety considerations"
    )
    notes = fields.Text(string="Internal Notes", help="Internal notes and comments")

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("purchase_date", "warranty_expiry")
    def _compute_warranty_status(self):
        """Compute warranty status based on expiry date"""
        today = fields.Date.today()
        for item in self:
            if item.warranty_expiry:
                if item.warranty_expiry >= today:
                    item.warranty_status = "active"
                else:
                    item.warranty_status = "expired"
            else:
                item.warranty_status = "unknown"

    @api.depends("last_maintenance", "maintenance_interval")
    def _compute_next_maintenance(self):
        """Calculate next maintenance date"""
        for item in self:
            if item.last_maintenance and item.maintenance_interval:
                item.next_maintenance = item.last_maintenance + timedelta(
                    days=item.maintenance_interval
                )
            else:
                item.next_maintenance = False

    @api.depends("next_maintenance")
    def _compute_maintenance_due(self):
        """Check if maintenance is due"""
        today = fields.Date.today()
        for item in self:
            if item.next_maintenance:
                item.maintenance_due = item.next_maintenance <= today
            else:
                item.maintenance_due = False

    @api.depends("purchase_date")
    def _compute_age(self):
        """Calculate age in months"""
        today = fields.Date.today()
        for item in self:
            if item.purchase_date:
                # Calculate difference in months
                months = (today.year - item.purchase_date.year) * 12 + (
                    today.month - item.purchase_date.month
                )
                item.age_months = max(0, months)  # Ensure non-negative
            else:
                item.age_months = 0

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with category and model"""
        result = []
        for record in self:
            name = record.name
            if record.category:
                category_name = dict(self._fields["category"].selection).get(
                    record.category
                )
                name = _("%s (%s)", name, category_name)
            if record.model_number:
                name = _("%s - %s", name, record.model_number)
            result.append((record.id, name))
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_available(self):
        """Mark service item as available"""
        self.ensure_one()
        if self.state not in ["draft", "maintenance"]:
            raise UserError(_("Cannot mark item as available from current state"))

        self.write({"state": "available"})
        self.message_post(body=_("Service item marked as available"))

    def action_mark_in_use(self):
        """Mark service item as in use"""
        self.ensure_one()
        if self.state != "available":
            raise UserError(_("Only available items can be marked as in use"))

        self.write({"state": "in_use"})
        self.message_post(body=_("Service item marked as in use"))

    def action_send_to_maintenance(self):
        """Send service item to maintenance"""
        self.ensure_one()

        self.write({"state": "maintenance"})

        # Create maintenance request if maintenance module is available
        if "maintenance.request" in self.env:
            maintenance_request = self.env["maintenance.request"].create(
                {
                    "name": _("Maintenance - %s", self.name),
                    "equipment_id": self.id,
                    "request_type": (
                        "corrective" if self.maintenance_due else "preventive"
                    ),
                    "description": _("Maintenance required for %s", self.name),
                }
            )

            self.message_post(
                body=_("Service item sent to maintenance. Request created: %s", maintenance_request.name)
            )

            return {
                "type": "ir.actions.act_window",
                "name": _("Maintenance Request"),
                "res_model": "maintenance.request",
                "res_id": maintenance_request.id,
                "view_mode": "form",
                "target": "current",
            }
        else:
            self.message_post(body=_("Service item sent to maintenance"))

    def action_schedule_maintenance(self):
        """Schedule preventive maintenance"""
        self.ensure_one()

        if "maintenance.request" in self.env:
            return {
                "type": "ir.actions.act_window",
                "name": _("Schedule Maintenance - %s", self.name),
                "res_model": "maintenance.request",
                "view_mode": "form",
                "target": "new",
                "context": {
                    "default_name": _("Scheduled Maintenance - %s", self.name),
                    "default_equipment_id": self.id,
                    "default_request_type": "preventive",
                    "default_description": _("Scheduled maintenance for %s", self.name),
                },
            }
        else:
            raise UserError(_("Maintenance module not available"))

    def action_retire_item(self):
        """Retire service item"""
        self.ensure_one()

        if self.state == "in_use":
            raise UserError(_("Cannot retire item that is currently in use"))

        self.write({"state": "retired", "active": False})
        self.message_post(body=_("Service item retired"))

    def action_view_service_requests(self):
        """View service requests for this item"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Service Requests - %s", self.name),
            "res_model": "portal.request",
            "view_mode": "tree,form",
            "domain": [("service_item_id", "=", self.id)],
            "context": {"default_service_item_id": self.id},
        }

    def action_view_maintenance_history(self):
        """View maintenance history"""
        self.ensure_one()

        if "maintenance.request" in self.env:
            return {
                "type": "ir.actions.act_window",
                "name": _("Maintenance History - %s", self.name),
                "res_model": "maintenance.request",
                "view_mode": "tree,form",
                "domain": [("equipment_id", "=", self.id)],
                "context": {"default_equipment_id": self.id},
            }
        else:
            raise UserError(_("Maintenance module not available"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("maintenance_interval")
    def _check_maintenance_interval(self):
        """Validate maintenance interval is reasonable"""
        for record in self:
            if record.maintenance_interval < 1 or record.maintenance_interval > 3650:
                raise ValidationError(
                    _("Maintenance interval must be between 1 and 3650 days")
                )

    @api.constrains("utilization_rate")
    def _check_utilization_rate(self):
        """Validate utilization rate is within valid range"""
        for record in self:
            if record.utilization_rate < 0 or record.utilization_rate > 100:
                raise ValidationError(_("Utilization rate must be between 0% and 100%"))

    @api.constrains("capacity")
    def _check_capacity(self):
        """Validate capacity is positive"""
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_("Capacity cannot be negative"))

    @api.constrains("purchase_cost", "current_value", "maintenance_cost")
    def _check_financial_values(self):
        """Validate financial values are not negative"""
        for record in self:
            if any(
                val < 0
                for val in [
                    record.purchase_cost or 0,
                    record.current_value or 0,
                    record.maintenance_cost or 0,
                ]
            ):
                raise ValidationError(_("Financial values cannot be negative"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_utilization_summary(self):
        """Get utilization summary for reporting"""
        self.ensure_one()

        return {
            "item_name": self.name,
            "category": self.category,
            "service_type": self.service_type,
            "utilization_rate": self.utilization_rate,
            "efficiency_rating": self.efficiency_rating,
            "state": self.state,
            "maintenance_due": self.maintenance_due,
            "age_months": self.age_months,
        }

    def calculate_depreciated_value(self):
        """Calculate current depreciated value"""
        self.ensure_one()

        if not self.purchase_cost or not self.purchase_date:
            return 0.0

        age_years = self.age_months / 12.0
        depreciation_amount = (
            self.purchase_cost * (self.depreciation_rate / 100.0) * age_years
        )
        depreciated_value = max(0.0, self.purchase_cost - depreciation_amount)

        return depreciated_value

    @api.model
    def get_maintenance_due_items(self):
        """Get all items with maintenance due"""
        return self.search([("maintenance_due", "=", True), ("state", "!=", "retired")])

    @api.model
    def _check_maintenance_schedules(self):
        """Cron job to check maintenance schedules and create activities"""
        overdue_items = self.search(
            [
                ("maintenance_due", "=", True),
                ("state", "not in", ["maintenance", "retired"]),
            ]
        )

        for item in overdue_items:
            # Determine assigned user
            assigned_user_id = item.user_id.id or item.assigned_user_id.id

            if not assigned_user_id:
                # Skip items without assigned users or log warning
                continue

            # Create maintenance activity
            try:
                item.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Maintenance Due: %s", item.name),
                    note=_(
                        "Service item maintenance is due based on the scheduled interval."
                    ),
                    user_id=assigned_user_id,
                    date_deadline=fields.Date.today(),
                )
            except Exception:
                # Continue processing other items if activity creation fails
                continue
