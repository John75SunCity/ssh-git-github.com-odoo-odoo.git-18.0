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

Maintenance Workflows:
- Preventive maintenance scheduling based on usage hours and manufacturer recommendations
- Corrective maintenance workflows with priority-based service request management
- Spare parts inventory management and automatic reorder point systems
- Maintenance technician assignment and skill-based task allocation
- Maintenance cost tracking and budget management with variance analysis
- Equipment downtime tracking and impact assessment on service delivery

Performance Analytics:
- Real-time equipment utilization and efficiency monitoring
- Capacity planning and optimization recommendations
- Maintenance cost analysis and equipment ROI calculations
- Equipment performance benchmarking and comparative analysis
- Predictive maintenance recommendations based on usage patterns
- Integration with operational dashboards and reporting systems

Technical Implementation:
- Extension of Odoo's standard maintenance module with Records Management customizations
- Integration with destruction service workflows and certificate generation
- Real-time monitoring capabilities with IoT sensor integration support
- Performance optimized for high-volume destruction operations
- Comprehensive audit logging and compliance documentation systems

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api
from datetime import timedelta


class MaintenanceEquipment(models.Model):
    """
    Extend Odoo's standard maintenance.equipment for Records Management shredding equipment.
    This provides enterprise-grade maintenance workflow with Records Management customizations.
    """

    _inherit = "maintenance.equipment"

    # ============================================================================
    # RECORDS MANAGEMENT SPECIFIC FIELDS
    # ============================================================================
    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    ),
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True),
    equipment_category = fields.Selection(
        [
            ("paper_shredder", "Paper Shredder"),
            ("hard_drive_crusher", "Hard Drive Crusher"),
            ("media_destroyer", "Media Destroyer"),
            ("industrial_shredder", "Industrial Shredder"),
            ("other", "Other"),
        ]),
        string="Equipment Category",
        default="paper_shredder",
    )

    )

    security_level = fields.Selection(
        [
            ("level_1", "Level 1"),
            ("level_2", "Level 2"),
            ("level_3", "Level 3"),
            ("level_4", "Level 4"),
            ("level_5", "Level 5"),
            ("level_6", "Level 6"),
        ]),
        string="Security Level",
        default="level_3",
    )

    capacity_per_hour = fields.Float(
        string="Capacity per Hour (lbs)",
        digits="Stock Weight",
        default=0.0,
        help="Processing capacity in pounds per hour",
    )

    # NAID Compliance fields
    )
    naid_certified = fields.Boolean(string="NAID Certified", default=False),
    naid_certification_number = fields.Char(string="NAID Certification Number")
    naid_certification_expiry = fields.Date(string="NAID Certification Expiry"),
    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut"),
            ("strip_cut", "Strip Cut"),
            ("pulverize", "Pulverize"),
            ("crush", "Crush"),
            ("degauss", "Degauss"),
        ]),
        string="Destruction Method",
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    )
    shredding_service_ids = fields.One2many(
        "shredding.service", "equipment_id", string="Shredding Services"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
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

    certification_status = fields.Selection(
        [
            ("none", "No Certification"),
            ("valid", "Valid"),
            ("expiring", "Expiring Soon"),
            ("expired", "Expired"),
        ]),
        string="Certification Status",
        compute="_compute_certification_status",
        store=True,
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_renew_certification(self):
        """Action to renew NAID certification"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Renew NAID Certification",
            "res_model": "maintenance.request",
            "view_mode": "form",
            "context": {
                "default_equipment_id": self.id,
                "default_name": f"NAID Certification Renewal - {self.name}",
                "default_request_type": "certification",
                "default_priority": "2",
            },
            "target": "new",
        }

    def action_schedule_maintenance(self):
        """Schedule maintenance request for this equipment"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": "Schedule Maintenance",
            "res_model": "maintenance.request",
            "view_mode": "form",
            "context": {
                "default_equipment_id": self.id,
                "default_name": f"Maintenance - {self.name}",
                "default_request_type": "preventive",
            },
            "target": "new",
        })
