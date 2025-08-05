# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    """Extend Odoo's standard maintenance.equipment for Records Management"""

    _inherit = "maintenance.equipment"

    # ============================================================================
    # RECORDS MANAGEMENT EXTENSIONS
    # ============================================================================

    # Equipment Classification for Records Management
    equipment_category = fields.Selection(
        [
            ("shredding", "Shredding Equipment"),
            ("scanning", "Scanning Equipment"),
            ("storage", "Storage Equipment"),
            ("transport", "Transport Equipment"),
            ("security", "Security Equipment"),
            ("general", "General Equipment"),
        ],
        string="Records Equipment Category",
        default="general",
    )

    # Shredding-specific fields
    shredding_capacity = fields.Float(
        string="Shredding Capacity (lbs/hour)",
        digits="Stock Weight",
        help="Maximum shredding capacity per hour",
    )
    security_level = fields.Selection(
        [
            ("level_1", "Level 1 - Strip Cut"),
            ("level_2", "Level 2 - Cross Cut"),
            ("level_3", "Level 3 - Micro Cut"),
            ("level_4", "Level 4 - High Security"),
            ("level_5", "Level 5 - NSA/CSS EPL"),
            ("level_6", "Level 6 - EAL4+ Certified"),
        ],
        string="Security Level",
        help="Security level for shredding equipment",
    )

    # Integration with Records Management
    location_id = fields.Many2one("records.location", string="Records Location")
    shredding_service_ids = fields.Many2many(
        "shredding.service",
        string="Related Shredding Services",
        help="Services that use this equipment",
    )

    # NAID Compliance
    naid_certification = fields.Selection(
        [
            ("none", "Not Certified"),
            ("a", "NAID A"),
            ("aa", "NAID AA"),
            ("aaa", "NAID AAA"),
        ],
        string="NAID Certification",
        default="none",
    )

    certification_expiry = fields.Date(string="Certification Expiry Date")
    calibration_required = fields.Boolean(string="Requires Calibration", default=False)
    last_calibration_date = fields.Date(string="Last Calibration Date")
    next_calibration_date = fields.Date(string="Next Calibration Date")


class MaintenanceRequest(models.Model):
    """Extend Odoo's standard maintenance.request for Records Management"""

    _inherit = "maintenance.request"

    # ============================================================================
    # RECORDS MANAGEMENT EXTENSIONS
    # ============================================================================

    # Service Integration
    shredding_service_id = fields.Many2one(
        "shredding.service",
        string="Related Shredding Service",
        help="Shredding service that triggered this maintenance request",
    )

    # Customer Impact Assessment
    customer_impact = fields.Selection(
        [
            ("none", "No Customer Impact"),
            ("low", "Low Impact"),
            ("medium", "Medium Impact"),
            ("high", "High Impact"),
            ("critical", "Critical - Service Disruption"),
        ],
        string="Customer Impact",
        default="none",
    )

    # Compliance Requirements
    requires_certification = fields.Boolean(
        string="Requires Re-certification",
        help="Equipment needs re-certification after maintenance",
    )
    compliance_notes = fields.Text(string="Compliance Notes")

    # Cost Tracking
    parts_cost = fields.Float(string="Parts Cost", digits="Product Price")
    labor_cost = fields.Float(string="Labor Cost", digits="Product Price")
    external_cost = fields.Float(string="External Service Cost", digits="Product Price")
    total_maintenance_cost = fields.Float(
        string="Total Cost", compute="_compute_total_cost", store=True
    )

    @api.depends("parts_cost", "labor_cost", "external_cost")
    def _compute_total_cost(self):
        for request in self:
            request.total_maintenance_cost = (
                request.parts_cost + request.labor_cost + request.external_cost
            )


class MaintenanceTeam(models.Model):
    """Extend Odoo's standard maintenance.team for Records Management"""

    _inherit = "maintenance.team"

    # ============================================================================
    # RECORDS MANAGEMENT EXTENSIONS
    # ============================================================================

    # Specialization
    specialization = fields.Selection(
        [
            ("shredding", "Shredding Equipment"),
            ("scanning", "Document Scanning"),
            ("storage", "Storage Systems"),
            ("transport", "Transport Equipment"),
            ("security", "Security Systems"),
            ("general", "General Maintenance"),
        ],
        string="Team Specialization",
        default="general",
    )

    # Service Area
    service_locations = fields.Many2many(
        "records.location",
        string="Service Locations",
        help="Locations this team can service",
    )

    # Certifications
    naid_certified = fields.Boolean(string="NAID Certified Team", default=False)
    certification_level = fields.Selection(
        [("a", "NAID A"), ("aa", "NAID AA"), ("aaa", "NAID AAA")],
        string="Team Certification Level",
    )

    # Performance Metrics
    average_response_time = fields.Float(
        string="Avg Response Time (hours)", compute="_compute_performance_metrics"
    )
    average_resolution_time = fields.Float(
        string="Avg Resolution Time (hours)", compute="_compute_performance_metrics"
    )

    @api.depends("request_ids.create_date", "request_ids.close_date")
    def _compute_performance_metrics(self):
        for team in self:
            completed_requests = team.request_ids.filtered(lambda r: r.close_date)
            if completed_requests:
                total_resolution_time = sum(
                    [
                        (r.close_date - r.create_date).total_seconds() / 3600
                        for r in completed_requests
                    ]
                )
                team.average_resolution_time = total_resolution_time / len(
                    completed_requests
                )
                # Add response time calculation if needed
            else:
                team.average_response_time = 0.0
                team.average_resolution_time = 0.0
