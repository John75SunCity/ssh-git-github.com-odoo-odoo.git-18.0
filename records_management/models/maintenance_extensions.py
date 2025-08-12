# -*- coding: utf-8 -*-

from odoo import models, fields, api


class MaintenanceEquipment(models.Model):
    """Extend Odoo's standard maintenance.equipment for Records Management"""

    _inherit = "maintenance.equipment"

    # ============================================================================
    # RECORDS MANAGEMENT EXTENSIONS
    # ============================================================================

    equipment_category = fields.Selection(
        selection_add=[
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

    shredding_capacity = fields.Float(
        string="Shredding Capacity (lbs/hour)",
        digits=(16, 2),
        help="Maximum shredding capacity per hour",
    )
    security_level = fields.Selection(
        selection_add=[
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

    location_id = fields.Many2one("records.location", string="Records Location")
    shredding_service_ids = fields.Many2many(
        "shredding.service",
        string="Related Shredding Services",
        help="Services that use this equipment",
    )

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

    shredding_service_id = fields.Many2one(
        "shredding.service",
        string="Related Shredding Service",
        help="Shredding service that triggered this maintenance request",
    )

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

    requires_certification = fields.Boolean(
        string="Requires Re-certification",
        help="Equipment needs re-certification after maintenance",
    )
    compliance_notes = fields.Text(string="Compliance Notes")

    parts_cost = fields.Float(string="Parts Cost", digits="Product Price")
    labor_cost = fields.Float(string="Labor Cost", digits="Product Price")
    external_cost = fields.Float(string="External Service Cost", digits="Product Price")
    total_maintenance_cost = fields.Float(
        string="Total Cost",
        compute="_compute_total_cost",
        store=True,
        digits="Product Price",
    )

    @api.depends("parts_cost", "labor_cost", "external_cost")
    def _compute_total_cost(self):
        for request in self:
            request.total_maintenance_cost = (
                (request.parts_cost or 0.0)
                + (request.labor_cost or 0.0)
                + (request.external_cost or 0.0)
            )


class MaintenanceTeam(models.Model):
    """Extend Odoo's standard maintenance.team for Records Management"""

    _inherit = "maintenance.team"

    # ============================================================================
    # RECORDS MANAGEMENT EXTENSIONS
    # ============================================================================

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

    service_location_ids = fields.Many2many(
        "records.location",
        string="Service Locations",
        help="Locations this team can service",
    )

    naid_certified = fields.Boolean(string="NAID Certified Team", default=False)
    certification_level = fields.Selection(
        [("a", "NAID A"), ("aa", "NAID AA"), ("aaa", "NAID AAA")],
        string="Team Certification Level",
    )

    average_response_time = fields.Float(
        string="Avg Response Time (hours)", compute="_compute_performance_metrics"
    )
    average_resolution_time = fields.Float(
        string="Avg Resolution Time (hours)", compute="_compute_performance_metrics"
    )

    @api.depends(
        "request_ids.create_date", "request_ids.assign_date", "request_ids.close_date"
    )
    def _compute_performance_metrics(self):
        from datetime import datetime

        for team in self:
            completed_requests = team.request_ids.filtered(lambda r: r.close_date)
            assigned_requests = team.request_ids.filtered(lambda r: r.assign_date)

            # Calculate average resolution time
            if completed_requests:
                total_resolution_time = sum(
                    (r.close_date - r.create_date).total_seconds() / 3600
                    for r in completed_requests
                    if r.close_date
                    and r.create_date
                    and isinstance(r.close_date, datetime)
                    and isinstance(r.create_date, datetime)
                )
                team.average_resolution_time = total_resolution_time / len(
                    completed_requests
                )
            else:
                team.average_resolution_time = 0.0

            # Calculate average response time
            if assigned_requests:
                total_response_time = sum(
                    (r.assign_date - r.create_date).total_seconds() / 3600
                    for r in assigned_requests
                    if r.assign_date
                    and r.create_date
                    and isinstance(r.assign_date, datetime)
                    and isinstance(r.create_date, datetime)
                )
                team.average_response_time = total_response_time / len(
                    assigned_requests
                )
            else:
                team.average_response_time = 0.0
