# -*- coding: utf-8 -*-
"""
Shredding Equipment Management Module

This module extends Odoo's standard maintenance equipment functionality to provide comprehensive
management of document shredding and destruction equipment within the Records Management System.
It implements specialized maintenance workflows, NAID compliance tracking, and performance monitoring.

Key Features:
- Comprehensive shredding equipment lifecycle management with NAID compliance
- Specialized maintenance workflows for secure destruction equipment
- Equipment performance monitoring and capacity tracking
- NAID AAA compliance verification and certification management
- Preventive maintenance scheduling with automated alerts and notifications
- Equipment utilization analytics and efficiency reporting
- Integration with destruction services and certificate generation

Business Processes:
1. Equipment Registration: Initial equipment setup with NAID specifications and capabilities
2. Maintenance Scheduling: Preventive and corrective maintenance planning and execution
3. Performance Monitoring: Real-time tracking of equipment efficiency and capacity utilization
4. Compliance Verification: NAID AAA compliance checking and certification maintenance
5. Utilization Optimization: Equipment allocation and scheduling for maximum efficiency
6. Maintenance Documentation: Complete maintenance history and compliance documentation
7. Replacement Planning: Equipment lifecycle management and replacement planning

Equipment Types:
- Paper Shredders: High-capacity paper shredding equipment with various security levels
- Media Destroyers: Specialized equipment for electronic media destruction (CDs, drives, tapes)
- Hard Drive Shredders: Industrial equipment for secure hard drive and SSD destruction
- Mobile Shredders: Truck-mounted shredding equipment for on-site destruction services
- Granulators: Secondary processing equipment for further material reduction
- Balers: Equipment for compacting shredded materials for recycling and disposal

NAID Compliance Features:
- NAID AAA specification compliance verification and tracking
- Equipment certification management with renewal scheduling
- Security level verification and documentation for different destruction requirements
- Chain of custody integration for equipment-based destruction processes
- Compliance reporting and audit trail maintenance for regulatory requirements
- Integration with NAID member verification and certification systems

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
    """
    Extend Odoo's standard maintenance.equipment for Records Management shredding equipment.
    This provides enterprise-grade maintenance workflow with Records Management customizations.
    """
    _inherit = "maintenance.equipment"

    # Efficiency rating mapping for analytics calculations
    EFFICIENCY_RATING_MAP = {
        "poor": 1,
        "fair": 2,
        "good": 3,
        "excellent": 4,
    }

    # ============================================================================
    # RECORDS MANAGEMENT SPECIFIC FIELDS
    # ============================================================================
    equipment_category = fields.Selection(
        [
            ("paper_shredder", "Paper Shredder"),
            ("hard_drive_crusher", "Hard Drive Crusher"),
            ("media_destroyer", "Media Destroyer"),
            ("industrial_shredder", "Industrial Shredder"),
            ("mobile_shredder", "Mobile Shredder"),
            ("granulator", "Granulator"),
            ("baler", "Baler"),
            ("other", "Other"),
        ],
        string="Equipment Category",
        default="paper_shredder",
        tracking=True,
        help="Type of shredding equipment",
    )

    security_level = fields.Selection(
        [
            ("level_1", "Level 1 - Strip Cut"),
            ("level_2", "Level 2 - Cross Cut"),
            ("level_3", "Level 3 - Micro Cut"),
            ("level_4", "Level 4 - High Security"),
            ("level_5", "Level 5 - NSA/CSS EPL"),
            ("level_6", "Level 6 - Disintegration"),
            ("level_7", "Level 7 - Pulverization"),
        ],
        string="Security Level",
        default="level_3",
        tracking=True,
        help="Document destruction security level per NAID standards",
    )

    capacity_per_hour = fields.Float(
        string="Capacity per Hour (lbs)",
        digits="Stock Weight",
        default=0.0,
        tracking=True,
        help="Processing capacity in pounds per hour",
    )

    # ============================================================================
    # NAID COMPLIANCE FIELDS
    # ============================================================================
    naid_certified = fields.Boolean(
        string="NAID Certified",
        default=False,
        tracking=True,
        help="Whether equipment is NAID certified",
    )
    naid_certification_number = fields.Char(
        string="NAID Certification Number",
        tracking=True,
        help="NAID certification identification number",
    )
    naid_certification_expiry = fields.Date(
        string="NAID Certification Expiry",
        tracking=True,
        help="Date when NAID certification expires",
    )
    naid_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
        ],
        string="NAID Level",
        default="aaa",
        tracking=True,
        help="NAID compliance level",
    )

    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("pulverize", "Pulverization"),
            ("crush", "Crushing"),
            ("degauss", "Degaussing"),
            ("incineration", "Incineration"),
            ("disintegration", "Disintegration"),
        ],
        string="Destruction Method",
        tracking=True,
        help="Primary method of material destruction",
    )

    # ============================================================================
    # OPERATIONAL SPECIFICATIONS
    # ============================================================================
    max_sheet_capacity = fields.Integer(
        string="Max Sheet Capacity",
        default=0,
        help="Maximum sheets that can be processed at once",
    )
    throat_width = fields.Float(
        string="Throat Width (inches)",
        digits=(5, 1),
        help="Width of equipment intake opening",
    )
    bin_capacity = fields.Float(
        string="Bin Capacity (cubic feet)",
        digits=(6, 2),
        help="Waste bin capacity in cubic feet",
    )
    power_rating = fields.Float(
        string="Power Rating (HP)",
        digits=(5, 1),
        help="Motor power rating in horsepower",
    )
    voltage_requirement = fields.Char(
        string="Voltage Requirement", help="Electrical voltage requirements"
    )

    # ============================================================================
    # PERFORMANCE TRACKING
    # ============================================================================
    total_hours_operated = fields.Float(
        string="Total Hours Operated",
        default=0.0,
        tracking=True,
        help="Cumulative operating hours",
    )
    total_weight_processed = fields.Float(
        string="Total Weight Processed (lbs)",
        digits="Stock Weight",
        default=0.0,
        tracking=True,
        help="Cumulative weight of materials processed",
    )
    average_throughput = fields.Float(
        string="Average Throughput (lbs/hr)",
        compute="_compute_average_throughput",
        store=True,
        digits="Stock Weight",
        help="Average processing rate",
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
        tracking=True,
        help="Overall equipment efficiency assessment",
    )

    # ============================================================================
    # MAINTENANCE FIELDS
    # ============================================================================
    last_blade_change = fields.Date(
        string="Last Blade Change",
        tracking=True,
        help="Date of last blade/cutting element replacement",
    )
    blade_change_interval = fields.Integer(
        string="Blade Change Interval (hours)",
        default=100,
        help="Operating hours between blade changes",
    )
    next_blade_change = fields.Date(
        string="Next Blade Change",
        compute="_compute_next_blade_change",
        store=True,
        help="Calculated next blade change date",
    )
    lubrication_schedule = fields.Selection(
        [
            ("daily", "Daily"),
            ("weekly", "Weekly"),
            ("monthly", "Monthly"),
            ("quarterly", "Quarterly"),
        ],
        string="Lubrication Schedule",
        default="monthly",
        help="Required lubrication frequency",
    )
    last_lubrication = fields.Date(
        string="Last Lubrication",
        tracking=True,
        help="Date of last lubrication service",
    )

    # ============================================================================
    # COMPUTED STATUS FIELDS
    # ============================================================================
    certification_status = fields.Selection(
        [
            ("none", "No Certification"),
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
        ],
        string="Certification Status",
        compute="_compute_certification_status",
        store=True,
        help="Current NAID certification status",
    )
    maintenance_due = fields.Boolean(
        string="Maintenance Due",
        compute="_compute_maintenance_due",
        store=True,
        help="Whether maintenance is currently due",
    )
    operational_status = fields.Selection(
        [
            ("operational", "Operational"),
            ("maintenance", "Under Maintenance"),
            ("repair", "Needs Repair"),
            ("retired", "Retired"),
        ],
        string="Operational Status",
        default="operational",
        tracking=True,
        help="Current operational status",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    shredding_service_ids = fields.One2many(
        "shredding.service",
        "equipment_id",
        string="Shredding Services",
        help="Services performed with this equipment",
    )
    destruction_certificate_ids = fields.One2many(
        "shredding.certificate",
        "equipment_id",
        string="Destruction Certificates",
        help="Certificates issued for services using this equipment",
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends("total_weight_processed", "total_hours_operated")
    def _compute_average_throughput(self):
        """Calculate average processing throughput"""
        for equipment in self:
            if equipment.total_hours_operated > 0:
                equipment.average_throughput = (
                    equipment.total_weight_processed / equipment.total_hours_operated
                )
            else:
                equipment.average_throughput = 0.0

    @api.depends("naid_certification_expiry")
    def _compute_certification_status(self):
        """Compute NAID certification status"""
        today = fields.Date.today()
        for equipment in self:
            if equipment.naid_certification_expiry:
                if equipment.naid_certification_expiry < today:
                    equipment.certification_status = "expired"
                elif equipment.naid_certification_expiry <= today + timedelta(days=30):
                    equipment.certification_status = "expiring"
                else:
                    equipment.certification_status = "valid"
            else:
                equipment.certification_status = "none"

    @api.depends("last_blade_change", "blade_change_interval", "total_hours_operated")
    def _compute_next_blade_change(self):
        """Calculate next blade change date"""
        for equipment in self:
            if equipment.last_blade_change and equipment.blade_change_interval > 0:
                # Estimate based on average daily usage
                if equipment.total_hours_operated > 0:
                    days_since_purchase = (
                        fields.Date.today()
                        - (
                            equipment.create_date.date()
                            if equipment.create_date
                            else fields.Date.today()
                        )
                    ).days
                    if days_since_purchase > 0:
                        daily_usage = (
                            equipment.total_hours_operated / days_since_purchase
                        )
                        days_to_next_change = equipment.blade_change_interval / max(
                            daily_usage, 0.1
                        )
                        equipment.next_blade_change = (
                            equipment.last_blade_change
                            + timedelta(days=int(days_to_next_change))
                        )
                    else:
                        equipment.next_blade_change = (
                            equipment.last_blade_change + timedelta(days=30)
                        )
                else:
                    equipment.next_blade_change = (
                        equipment.last_blade_change + timedelta(days=30)
                    )
            else:
                equipment.next_blade_change = False

    @api.depends("next_blade_change", "naid_certification_expiry", "last_lubrication")
    def _compute_maintenance_due(self):
        """Check if any maintenance is due"""
        today = fields.Date.today()
        for equipment in self:
            maintenance_due = False

            # Check blade change
            if equipment.next_blade_change and equipment.next_blade_change <= today:
                maintenance_due = True

            # Check certification expiry
            if (
                equipment.naid_certification_expiry
                and equipment.naid_certification_expiry <= today + timedelta(days=30)
            ):
                maintenance_due = True

            # Check lubrication schedule
            if equipment.last_lubrication and equipment.lubrication_schedule:
                days_mapping = {"daily": 1, "weekly": 7, "monthly": 30, "quarterly": 90}
                interval_days = days_mapping.get(equipment.lubrication_schedule, 30)
                if equipment.last_lubrication + timedelta(days=interval_days) <= today:
                    maintenance_due = True

            equipment.maintenance_due = maintenance_due

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with equipment category"""
        result = []
        for record in self:
            name = record.name
            if record.equipment_category:
                category_name = dict(self._fields["equipment_category"].selection).get(
                    record.equipment_category
                )
                name = f"{name} ({category_name})"
            if record.security_level:
                level_name = dict(self._fields["security_level"].selection).get(
                    record.security_level
                )
                name = f"{name} - {level_name}"
            result.append((record.id, name))
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_renew_certification(self):
        """Action to renew NAID certification"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Renew NAID Certification"),
            "res_model": "maintenance.request",
            "view_mode": "form",
            "context": {
                "default_equipment_id": self.id,
                "default_name": f"NAID Certification Renewal - {self.name}",
                "default_request_type": "corrective",
                "default_priority": "2",
                "default_description": f"NAID certification renewal required for {self.name}. Current certification expires: {self.naid_certification_expiry}",
            },
            "target": "new",
        }

    def action_schedule_maintenance(self):
        """Schedule maintenance request for this equipment"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Maintenance"),
            "res_model": "maintenance.request",
            "view_mode": "form",
            "context": {
                "default_equipment_id": self.id,
                "default_name": f"Maintenance - {self.name}",
                "default_request_type": "preventive",
                "default_description": f"Scheduled maintenance for {self.name}",
            },
            "target": "new",
        }

    def action_record_usage(self):
        """Record equipment usage statistics"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Record Equipment Usage"),
            "res_model": "equipment.usage.wizard",
            "view_mode": "form",
            "context": {
                "default_equipment_id": self.id,
            },
            "target": "new",
        }

    def action_blade_change_complete(self):
        """Mark blade change as completed"""
        self.ensure_one()

        self.write(
            {
                "last_blade_change": fields.Date.today(),
            }
        )

        self.message_post(body=_("Blade change completed on %s") % fields.Date.today())

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Blade Change Recorded"),
                "message": _("Blade change has been recorded for %s") % self.name,
                "type": "success",
            },
        }

    def action_lubrication_complete(self):
        """Mark lubrication as completed"""
        self.ensure_one()

        self.write(
            {
                "last_lubrication": fields.Date.today(),
            }
        )

        self.message_post(body=_("Lubrication completed on %s") % fields.Date.today())

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Lubrication Recorded"),
                "message": _("Lubrication has been recorded for %s") % self.name,
                "type": "success",
            },
        }

    def action_view_services(self):
        """View shredding services performed with this equipment"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Services - %s") % self.name,
            "res_model": "shredding.service",
            "view_mode": "tree,form",
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id},
        }

    def action_view_certificates(self):
        """View destruction certificates for this equipment"""
        self.ensure_one()

        return {
            "type": "ir.actions.act_window",
            "name": _("Certificates - %s") % self.name,
            "res_model": "shredding.certificate",
            "view_mode": "tree,form",
            "domain": [("equipment_id", "=", self.id)],
            "context": {"default_equipment_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains(
        "capacity_per_hour", "max_sheet_capacity", "throat_width", "bin_capacity"
    )
    def _check_equipment_specifications(self):
        """Validate equipment specifications are positive"""
        for record in self:
            if any(
                val < 0
                for val in [
                    record.capacity_per_hour,
                    record.max_sheet_capacity,
                    record.throat_width,
                    record.bin_capacity,
                ]
            ):
                raise ValidationError(_("Equipment specifications cannot be negative"))

    @api.constrains("blade_change_interval")
    def _check_blade_change_interval(self):
        """Validate blade change interval is reasonable"""
        for record in self:
            if record.blade_change_interval < 1 or record.blade_change_interval > 10000:
                raise ValidationError(
                    _("Blade change interval must be between 1 and 10,000 hours")
                )

    @api.constrains("naid_certification_expiry")
    def _check_certification_expiry(self):
        """Validate certification expiry date"""
        for record in self:
            if (
                record.naid_certification_expiry
                and record.naid_certification_expiry
                < fields.Date.today() - timedelta(days=365 * 10)
            ):
                raise ValidationError(
                    _(
                        "Certification expiry date cannot be more than 10 years in the past"
                    )
                )

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def update_usage_statistics(self, hours_operated, weight_processed):
        """Update equipment usage statistics"""
        self.ensure_one()

        self.write(
            {
                "total_hours_operated": self.total_hours_operated + hours_operated,
                "total_weight_processed": self.total_weight_processed
                + weight_processed,
            }
        )

        self.message_post(
            body=_("Usage updated: +%.2f hours, +%.2f lbs processed")
            % (hours_operated, weight_processed)
        )

    def get_performance_summary(self):
        """Get equipment performance summary for reporting"""
        self.ensure_one()

        return {
            "equipment_name": self.name,
            "category": self.equipment_category,
            "security_level": self.security_level,
            "total_hours": self.total_hours_operated,
            "total_weight": self.total_weight_processed,
            "average_throughput": self.average_throughput,
            "efficiency_rating": self.efficiency_rating,
            "certification_status": self.certification_status,
            "operational_status": self.operational_status,
            "maintenance_due": self.maintenance_due,
        }

    @api.model
    def get_maintenance_due_equipment(self):
        """Get all equipment with maintenance due"""
        return self.search(
            [("maintenance_due", "=", True), ("operational_status", "!=", "retired")]
        )

    @api.model
    def check_maintenance_schedules(self):
        """Cron job to check maintenance schedules and create activities"""
        overdue_equipment = self.search(
            [
                ("maintenance_due", "=", True),
                ("operational_status", "in", ["operational"]),
            ]
        )
        for equipment in overdue_equipment:
            # Create maintenance activity
            try:
                equipment.activity_schedule(
                    "mail.mail_activity_data_todo",
                    summary=_("Equipment Maintenance Due: %s") % equipment.name,
                    note=_(
                        "Equipment maintenance is due based on the scheduled intervals."
                    ),
                    user_id=(
                        equipment.technician_user_id.id
                        if equipment.technician_user_id
                        else equipment.owner_user_id.id
                    ),
                    date_deadline=fields.Date.today(),
                )
            except Exception as e:
                _logger.error(
                    f"Failed to create maintenance activity for equipment {equipment.name}: {str(e)}"
                )
                # Continue processing other equipment if activity creation fails
                continue

    @api.model
    def get_equipment_analytics(self):
        """Get analytics data for equipment dashboard"""
        equipment_data = self.search([("operational_status", "!=", "retired")])

        analytics = {
            "total_equipment": len(equipment_data),
            "operational_count": len(
                equipment_data.filtered(lambda e: e.operational_status == "operational")
            ),
            "maintenance_due_count": len(equipment_data.filtered("maintenance_due")),
            "certification_expired_count": len(
                equipment_data.filtered(lambda e: e.certification_status == "expired")
            ),
            "total_hours_operated": sum(equipment_data.mapped("total_hours_operated")),
            "total_weight_processed": sum(
                equipment_data.mapped("total_weight_processed")
            ),
            "average_efficiency": (
                sum(
                    self.EFFICIENCY_RATING_MAP.get(e.efficiency_rating, 2)
                    for e in equipment_data
                )
                / len(equipment_data)
                if equipment_data
                else 0
            ),
            "equipment_by_category": {
                category[0]: len(
                    equipment_data.filtered(
                        lambda e: e.equipment_category == category[0]
                    )
                )
                for category in self._fields["equipment_category"].selection
            },
            "naid_certified_count": len(equipment_data.filtered("naid_certified")),
        }

        return analytics
