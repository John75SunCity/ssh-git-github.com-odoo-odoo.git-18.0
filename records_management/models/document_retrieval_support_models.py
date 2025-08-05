# -*- coding: utf-8 -*-
# Supporting Models for Document Retrieval Work Order System

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class DocumentRetrievalItem(models.Model):
    _inherit = [\'mail.thread\', \'mail.activity.mixin\']
    """Individual items in a document retrieval work order"""

    _name = "document.retrieval.item"
    _description = "Document Retrieval Item"
    _order = "work_order_id, sequence"
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )


    work_order_id = fields.Many2one(
        "document.retrieval.work.order",
        string="Work Order",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", default=10)

    document_id = fields.Many2one("records.document", string="Document")
    container_id = fields.Many2one("records.container", string="Container")
    location_id = fields.Many2one("records.location", string="Storage Location")

    item_type = fields.Selection(
        [
            ("document", "Single Document"),
            ("folder", "Document Folder"),
            ("container", "Full Container"),
            ("box", "Storage Box"),
        ],
        string="Item Type",
        required=True,
        default="document",
    )

    description = fields.Text(string="Item Description")
    barcode = fields.Char(string="Barcode/ID")

    # Status Tracking
    status = fields.Selection(
        [
            ("pending", "Pending"),
            ("located", "Located"),
            ("retrieved", "Retrieved"),
            ("scanned", "Scanned"),
            ("delivered", "Delivered"),
            ("not_found", "Not Found"),
        ],
        string="Status",
        default="pending",
    )

    # Effort Tracking
    estimated_time = fields.Float(string="Estimated Time (hours)", digits=(5, 2))
    actual_time = fields.Float(string="Actual Time (hours)", digits=(5, 2))
    difficulty_level = fields.Selection(
        [
            ("easy", "Easy"),
            ("medium", "Medium"),
            ("hard", "Hard"),
            ("very_hard", "Very Hard"),
        ],
        string="Difficulty",
        default="medium",
    )

    # Processing Details
    retrieval_date = fields.Datetime(string="Retrieved Date")
    retrieved_by = fields.Many2one("hr.employee", string="Retrieved By")
    condition_notes = fields.Text(string="Condition Notes")
    special_handling = fields.Boolean(string="Special Handling Required", default=False)

    # Quality Control
    quality_checked = fields.Boolean(string="Quality Checked", default=False)
    quality_issues = fields.Text(string="Quality Issues")
    completeness_verified = fields.Boolean(
        string="Completeness Verified", default=False
    )


class DocumentRetrievalTeam(models.Model):
    _inherit = [\'mail.thread\', \'mail.activity.mixin\']
    """Teams responsible for document retrieval operations"""

    _name = "document.retrieval.team"
    _description = "Document Retrieval Team"
    _order = "name"

    name = fields.Char(string="Team Name", required=True)
    team_lead_id = fields.Many2one("hr.employee", string="Team Lead")
    member_ids = fields.Many2many("hr.employee", string="Team Members")

    # Specializations
    specialization = fields.Selection(
        [
            ("general", "General Retrieval"),
            ("legal", "Legal Documents"),
            ("medical", "Medical Records"),
            ("financial", "Financial Documents"),
            ("digital", "Digital Conversion"),
            ("urgent", "Urgent Requests"),
        ],
        string="Specialization",
        default="general",
    )

    # Performance Metrics
    active_orders_count = fields.Integer(
        string="Active Orders", compute="_compute_order_counts"
    )
    completed_orders_count = fields.Integer(
        string="Completed Orders", compute="_compute_order_counts"
    )
    average_completion_time = fields.Float(
        string="Avg Completion Time (days)",
        digits=(5, 2),
        compute="_compute_performance",
    )
    efficiency_rating = fields.Float(
        string="Efficiency Rating (%)", digits=(5, 2), compute="_compute_performance"
    )

    # Capacity Management
    max_concurrent_orders = fields.Integer(string="Max Concurrent Orders", default=10)
    current_workload = fields.Float(
        string="Current Workload (%)", compute="_compute_workload"
    )

    # Availability
    available_from = fields.Float(
        string="Available From (Hours)",
        help="Available from time in 24-hour format (e.g., 9.5 for 9:30 AM)",
    )
    available_to = fields.Float(
        string="Available To (Hours)",
        help="Available to time in 24-hour format (e.g., 17.5 for 5:30 PM)",
    )
    working_days = fields.Selection(
        [
            ("weekdays", "Monday to Friday"),
            ("all_days", "All Days"),
            ("custom", "Custom Schedule"),
        ],
        string="Working Days",
        default="weekdays",
    )

    @api.depends("member_ids")
    def _compute_order_counts(self):
        """Compute order counts for the team"""
        for team in self:
            # Count active orders assigned to team members
            team_member_ids = team.member_ids.mapped("user_id.id")
            active_count = self.env["document.retrieval.work.order"].search_count(
                [("user_id", "in", team_member_ids), ("state", "=", "active")]
            )
            completed_count = self.env["document.retrieval.work.order"].search_count(
                [("user_id", "in", team_member_ids), ("state", "=", "inactive")]
            )

            team.active_orders_count = active_count
            team.completed_orders_count = completed_count

    @api.depends("member_ids")
    def _compute_performance(self):
        """Compute performance metrics"""
        for team in self:
            if team.member_ids:
                # Calculate average completion time and efficiency
                team_member_ids = team.member_ids.mapped("user_id.id")
                completed_orders = self.env["document.retrieval.work.order"].search(
                    [
                        ("user_id", "in", team_member_ids),
                        ("state", "=", "inactive"),
                        ("completion_date", "!=", False),
                    ]
                )

                if completed_orders:
                    # Calculate average completion time
                    total_days = 0
                    efficiency_scores = []

                    for order in completed_orders:
                        if order.requested_date and order.completion_date:
                            completion_days = (
                                order.completion_date.date() - order.requested_date
                            ).days
                            total_days += completion_days

                        if order.estimated_hours and order.actual_hours:
                            efficiency = (
                                order.estimated_hours / order.actual_hours
                            ) * 100
                            efficiency_scores.append(
                                min(efficiency, 200)
                            )  # Cap at 200%

                    team.average_completion_time = total_days / len(completed_orders)
                    team.efficiency_rating = (
                        sum(efficiency_scores) / len(efficiency_scores)
                        if efficiency_scores
                        else 0
                    )
                else:
                    team.average_completion_time = 0
                    team.efficiency_rating = 0
            else:
                team.average_completion_time = 0
                team.efficiency_rating = 0

    @api.depends("active_orders_count", "max_concurrent_orders")
    def _compute_workload(self):
        """Compute current workload percentage"""
        for team in self:
            if team.max_concurrent_orders > 0:
                team.current_workload = (
                    team.active_orders_count / team.max_concurrent_orders
                ) * 100
            else:
                team.current_workload = 0


class DocumentRetrievalPricing(models.Model):
    _inherit = [\'mail.thread\', \'mail.activity.mixin\']
    """Pricing rules for document retrieval services"""

    _name = "document.retrieval.pricing"
    _description = "Document Retrieval Pricing"
    _order = "service_type, priority_level"

    name = fields.Char(string="Pricing Rule Name", required=True)
    service_type = fields.Selection(
        [
            ("permanent", "Permanent Retrieval"),
            ("temporary", "Temporary Retrieval"),
            ("copy", "Copy Request"),
            ("scan", "Scan to Digital"),
            ("rush", "Rush Service"),
        ],
        string="Service Type",
        required=True,
    )

    # Pricing Structure
    base_fee = fields.Monetary(string="Base Fee", currency_field="currency_id")
    per_document_fee = fields.Monetary(
        string="Per Document Fee", currency_field="currency_id"
    )
    per_hour_fee = fields.Monetary(string="Per Hour Fee", currency_field="currency_id")
    per_box_fee = fields.Monetary(string="Per Box Fee", currency_field="currency_id")

    # Volume Discounts
    volume_threshold = fields.Integer(string="Volume Threshold")
    volume_discount_percent = fields.Float(string="Volume Discount (%)", digits=(5, 2))

    # Priority Pricing
    priority_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("expedited", "Expedited"),
            ("urgent", "Urgent"),
            ("critical", "Critical"),
        ],
        string="Priority Level",
        default="standard",
    )
    priority_multiplier = fields.Float(
        string="Priority Multiplier", default=1.0, digits=(3, 2)
    )

    # Delivery Pricing
    delivery_included = fields.Boolean(string="Delivery Included", default=False)
    delivery_fee = fields.Monetary(string="Delivery Fee", currency_field="currency_id")
    delivery_radius_km = fields.Float(string="Delivery Radius (km)", digits=(5, 2))

    # Digital Services Pricing
    scanning_fee = fields.Monetary(string="Scanning Fee", currency_field="currency_id")
    ocr_fee = fields.Monetary(string="OCR Fee", currency_field="currency_id")
    digital_delivery_fee = fields.Monetary(
        string="Digital Delivery Fee", currency_field="currency_id"
    )

    # Time-based Pricing
    same_day_multiplier = fields.Float(
        string="Same Day Multiplier", default=2.0, digits=(3, 2)
    )
    next_day_multiplier = fields.Float(
        string="Next Day Multiplier", default=1.5, digits=(3, 2)
    )

    # Validity
    valid_from = fields.Date(string="Valid From", default=fields.Date.today)
    valid_to = fields.Date(string="Valid To")
    active = fields.Boolean(string="Active", default=True)

    # Customer Specific
    customer_id = fields.Many2one("res.partner", string="Specific Customer")
    customer_tier = fields.Selection(
        [
            ("bronze", "Bronze"),
            ("silver", "Silver"),
            ("gold", "Gold"),
            ("platinum", "Platinum"),
        ],
        string="Customer Tier",
    )

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )


class DocumentRetrievalEquipment(models.Model):
    _inherit = [\'mail.thread\', \'mail.activity.mixin\']
    """Equipment used for document retrieval operations"""

    _name = "document.retrieval.equipment"
    _description = "Document Retrieval Equipment"
    _order = "name"

    name = fields.Char(string="Equipment Name", required=True)
    equipment_type = fields.Selection(
        [
            ("scanner", "Document Scanner"),
            ("cart", "Transport Cart"),
            ("ladder", "Storage Ladder"),
            ("tablet", "Mobile Tablet"),
            ("camera", "Digital Camera"),
            ("vehicle", "Transport Vehicle"),
            ("tools", "Hand Tools"),
            ("safety", "Safety Equipment"),
        ],
        string="Equipment Type",
        required=True,
    )

    # Status and Availability
    status = fields.Selection(
        [
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Under Maintenance"),
            ("retired", "Retired"),
        ],
        string="Status",
        default="available",
    )

    location_id = fields.Many2one("records.location", string="Current Location")
    assigned_to = fields.Many2one("hr.employee", string="Assigned To")

    # Specifications
    model = fields.Char(string="Model")
    serial_number = fields.Char(string="Serial Number")
    purchase_date = fields.Date(string="Purchase Date")
    warranty_expiry = fields.Date(string="Warranty Expiry")

    # Maintenance
    last_maintenance = fields.Date(string="Last Maintenance")
    next_maintenance = fields.Date(string="Next Maintenance")
    maintenance_notes = fields.Text(string="Maintenance Notes")

    # Usage Tracking
    usage_hours = fields.Float(string="Total Usage Hours", digits=(10, 2))
    current_work_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Current Work Order"
    )


class DocumentRetrievalMetrics(models.Model):
    _inherit = [\'mail.thread\', \'mail.activity.mixin\']
    """Performance metrics for document retrieval operations"""

    _name = "document.retrieval.metrics"
    _description = "Document Retrieval Metrics"
    _order = "date desc"

    name = fields.Char(string="Metric Name", required=True)
    date = fields.Date(string="Date", required=True, default=fields.Date.today)
    work_order_id = fields.Many2one(
        "document.retrieval.work.order", string="Work Order"
    )
    team_id = fields.Many2one("document.retrieval.team", string="Team")
    employee_id = fields.Many2one("hr.employee", string="Employee")

    # Performance Metrics
    documents_retrieved = fields.Integer(string="Documents Retrieved")
    hours_worked = fields.Float(string="Hours Worked", digits=(5, 2))
    accuracy_rate = fields.Float(string="Accuracy Rate (%)", digits=(5, 2))
    customer_satisfaction = fields.Float(
        string="Customer Satisfaction (%)", digits=(5, 2)
    )

    # Efficiency Metrics
    documents_per_hour = fields.Float(
        string="Documents per Hour", digits=(5, 2), compute="_compute_efficiency"
    )
    cost_per_document = fields.Monetary(
        string="Cost per Document", currency_field="currency_id"
    )
    revenue_generated = fields.Monetary(
        string="Revenue Generated", currency_field="currency_id"
    )
    profit_margin = fields.Float(string="Profit Margin (%)", digits=(5, 2))

    # Quality Metrics
    errors_count = fields.Integer(string="Errors Count")
    rework_required = fields.Integer(string="Rework Required")
    on_time_delivery = fields.Boolean(string="On Time Delivery", default=True)

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    @api.depends("documents_retrieved", "hours_worked")
    def _compute_efficiency(self):
        """Compute documents per hour efficiency"""
        for metric in self:
            if metric.hours_worked > 0:
                metric.documents_per_hour = (
                    metric.documents_retrieved / metric.hours_worked
                )
            else:
                metric.documents_per_hour = 0
