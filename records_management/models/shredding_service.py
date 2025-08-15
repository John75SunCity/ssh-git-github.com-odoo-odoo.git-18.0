# -*- coding: utf-8 -*-
"""
Shredding Service Management Module

This module provides comprehensive shredding service management for the Records
Management System. It handles the complete lifecycle of shredding services from
scheduling to completion, including NAID compliance, certificate generation,
and team management.

Key Features:
- Complete service lifecycle management from draft to invoicing
- Multi-type shredding services (on-site, off-site, mobile, drop-off, emergency)
- Team and equipment management with resource allocation
- NAID AAA compliance with certificate generation
- Real-time tracking with photo documentation
- Advanced billing with multiple charge types

Business Processes:
1. Service Creation: Initial service setup with customer and material details
2. Scheduling: Team assignment and resource allocation
3. Service Execution: Real-time tracking with start/end times
4. Completion: Volume/weight recording and certificate generation
5. Billing Integration: Automated pricing with additional charges
6. Compliance: NAID compliance tracking and documentation

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime, timedelta

from odoo import _, api, fields, models

from odoo.exceptions import UserError, ValidationError


class ShreddingService(models.Model):
    _name = "shredding.service"
    _description = "Shredding Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "priority desc, service_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Service Order #",
        required=True,
        tracking=True,
        index=True,
        help="Unique service order number"
    )
    reference = fields.Char(
        string="Reference",
        index=True,
        tracking=True,
        help="External reference number"
    )
    description = fields.Text(
        string="Description",
        help="Service description and details"
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for sorting"
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Active status of the service"
    )

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Service Technician",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary service technician"
    )
    
    # ============================================================================
    # TEAM & RESOURCE ASSIGNMENT
    # ============================================================================
    
    assigned_technician_id = fields.Many2one(
        'hr.employee',
        string='Assigned Technician',
        tracking=True,
        help="Primary technician assigned to this shredding service",
    )
    
    assigned_team_ids = fields.Many2many(
        'hr.employee',
        string='Assigned Team',
        help="Team members assigned to this shredding service",
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("scheduled", "Scheduled"),
        ("in_progress", "In Progress"),
        ("completed", "Completed"),
        ("invoiced", "Invoiced"),
        ("cancelled", "Cancelled"),
    ],
        string="Status",
        default="draft",
        tracking=True,
        help="Current service status"
    )

    # ============================================================================
    # CUSTOMER & SERVICE RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Service customer"
    )
    contact_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        help="Primary contact for this service"
    )
    location_id = fields.Many2one(
        "records.location",
        string="Service Location",
        help="Location where service will be performed"
    )
    container_type_id = fields.Many2one(
        "records.container.type",
        string="Container Type",
        help="Associated container type for shredding service"
    )

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================
    service_type = fields.Selection([
        ("onsite", "On-Site Shredding"),
        ("offsite", "Off-Site Shredding"),
        ("mobile", "Mobile Shredding"),
        ("drop_off", "Drop-Off Service"),
        ("emergency", "Emergency Shredding"),
    ],
        string="Service Type",
        default="onsite",
        required=True,
        tracking=True,
        help="Type of shredding service"
    )
    material_type = fields.Selection([
        ("paper", "Paper Documents"),
        ("hard_drives", "Hard Drives"),
        ("media", "Electronic Media"),
        ("mixed", "Mixed Materials"),
    ],
        string="Material Type",
        default="paper",
        required=True,
        help="Type of material to be shredded"
    )
    
    # ============================================================================
    # DESTRUCTION & COMPLIANCE CONFIGURATION
    # ============================================================================
    
    destruction_method = fields.Selection([
        ('cross_cut', 'Cross Cut Shredding'),
        ('strip_cut', 'Strip Cut Shredding'),
        ('pulverization', 'Pulverization'),
        ('incineration', 'Incineration'),
        ('degaussing', 'Degaussing (Magnetic Media)'),
        ('physical_destruction', 'Physical Destruction'),
    ],
        string='Destruction Method',
        required=True,
        default='cross_cut',
        tracking=True,
        help="Method used for material destruction",
    )
    
    certificate_required = fields.Boolean(
        string='Certificate Required',
        default=True,
        tracking=True,
        help="Whether a destruction certificate is required for this service",
    )
    
    naid_compliance_required = fields.Boolean(
        string='NAID Compliance Required',
        default=True,
        help="Whether NAID AAA compliance is required",
    )
    
    # ============================================================================
    # CONTAINER & VOLUME TRACKING
    # ============================================================================
    
    container_type = fields.Selection(
        related="container_type_id.standard_type",
        readonly=True,
        store=True,
        string='Container Type',
        help="Standard container type classification",
    )
    
    destruction_item_count = fields.Integer(
        string='Items Count',
        compute='_compute_destruction_items',
        store=True,
        help="Number of items to be destroyed",
    )
    
    estimated_volume = fields.Float(
        string='Estimated Volume (cubic feet)',
        help="Estimated volume of materials to be destroyed",
    )
    
    actual_volume = fields.Float(
        string='Actual Volume (cubic feet)',
        help="Actual volume of materials destroyed",
    )

    # ============================================================================
    # SCHEDULING FIELDS
    # ============================================================================
    service_date = fields.Date(
        string="Scheduled Date",
        required=True,
        tracking=True,
        help="Scheduled service date"
    )
    service_time = fields.Float(
        string="Scheduled Time",
        help="Time in 24h format (e.g., 14.5 for 2:30 PM)"
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (Hours)",
        default=2.0,
        help="Estimated service duration in hours"
    )
    priority = fields.Selection([
        ("low", "Low"),
        ("normal", "Normal"),
        ("high", "High"),
        ("urgent", "Urgent"),
    ],
        string="Priority",
        default="normal",
        tracking=True,
        help="Service priority level"
    )

    # ============================================================================
    # TEAM & RESOURCES
    # ============================================================================
    team_id = fields.Many2one(
        "shredding.team",
        string="Assigned Team",
        help="Shredding team assigned to this service"
    )
    technician_ids = fields.Many2many(
        "hr.employee",
        string="Technicians",
        help="Individual technicians assigned"
    )
    vehicle_id = fields.Many2one(
        "records.vehicle",
        string="Service Vehicle",
        help="Vehicle used for this service"
    )
    equipment_ids = fields.Many2many(
        "maintenance.equipment",
        string="Equipment",
        help="Equipment used for shredding"
    )
    equipment_id = fields.Many2one(
        "maintenance.equipment",
        string="Primary Equipment",
        help="Primary shredding equipment"
    )
    recycling_bale_id = fields.Many2one(
        "paper.bale.recycling",
        string="Recycling Bale",
        help="Associated recycling bale"
    )

    batch_id = fields.Many2one(
        "shredding.inventory.batch",
        string="Inventory Batch",
        help="Associated shredding inventory batch",
        ondelete="set null"
    )

    # ============================================================================
    # MATERIAL DETAILS
    # ============================================================================
    estimated_volume = fields.Float(
        string="Estimated Volume (Cubic Feet)",
        digits="Stock Weight",
        default=0.0,
        help="Estimated volume of materials"
    )
    estimated_weight = fields.Float(
        string="Estimated Weight (lbs)",
        digits="Stock Weight",
        default=0.0,
        help="Estimated weight of materials"
    )
    actual_volume = fields.Float(
        string="Actual Volume (Cubic Feet)",
        digits="Stock Weight",
        default=0.0,
        help="Actual volume processed"
    )
    actual_weight = fields.Float(
        string="Actual Weight (lbs)",
        digits="Stock Weight",
        default=0.0,
        help="Actual weight processed"
    )

    # Container Information
    container_ids = fields.Many2many(
        "records.container",
        string="Containers",
        help="Containers being shredded"
    )
    bin_ids = fields.Many2many(
        "shred.bin", string="Shredding Bins", help="Bins used for shredding"
    )

    # ============================================================================
    # PRICING & BILLING
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )
    unit_price = fields.Float(
        string="Unit Price",
        digits="Product Price",
        default=0.0,
        help="Price per unit (volume or weight)"
    )
    total_amount = fields.Float(
        string="Total Amount",
        digits="Product Price",
        compute="_compute_total_amount",
        store=True,
        help="Total service amount including charges"
    )

    # Additional Charges
    travel_charge = fields.Float(
        string="Travel Charge",
        digits="Product Price",
        default=0.0,
        help="Additional travel charge"
    )
    emergency_charge = fields.Float(
        string="Emergency Charge",
        digits="Product Price",
        default=0.0,
        help="Emergency service surcharge"
    )
    equipment_charge = fields.Float(
        string="Equipment Charge",
        digits="Product Price",
        default=0.0,
        help="Special equipment charge"
    )

    # ============================================================================
    # COMPLIANCE & CERTIFICATES
    # ============================================================================
    requires_certificate = fields.Boolean(
        string="Certificate Required",
        default=True,
        help="Whether destruction certificate is required"
    )
    certificate_type = fields.Selection([
        ("standard", "Standard Certificate"),
        ("detailed", "Detailed Certificate"),
        ("chain_of_custody", "Chain of Custody"),
    ],
        string="Certificate Type",
        default="standard",
        help="Type of certificate to generate"
    )
    certificate_id = fields.Many2one(
        "shredding.certificate",
        string="Certificate",
        help="Generated destruction certificate"
    )
    compliance_level = fields.Selection([
        ("standard", "Standard"),
        ("naid_aaa", "NAID AAA"),
        ("dod_5220", "DoD 5220.22-M"),
        ("custom", "Custom"),
    ],
        string="Compliance Level",
        default="standard",
        help="Required compliance level"
    )

    # ============================================================================
    # SPECIAL INSTRUCTIONS
    # ============================================================================
    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special instructions for the service"
    )
    access_requirements = fields.Text(
        string="Access Requirements",
        help="Special access requirements or procedures"
    )
    security_clearance = fields.Boolean(
        string="Security Clearance Required",
        default=False,
        help="Whether security clearance is required"
    )
    witness_required = fields.Boolean(
        string="Witness Required",
        default=False,
        help="Whether witnessing is required"
    )

    # ============================================================================
    # COMPLETION TRACKING
    # ============================================================================
    actual_start_time = fields.Datetime(
        string="Actual Start Time",
        readonly=True,
        help="When service actually started"
    )
    actual_end_time = fields.Datetime(
        string="Actual End Time",
        readonly=True,
        help="When service was completed"
    )
    completion_notes = fields.Text(
        string="Completion Notes",
        help="Notes from service completion"
    )
    customer_signature = fields.Binary(
        string="Customer Signature",
        help="Customer signature for service completion"
    )
    photo_ids = fields.One2many(
        "shredding.service.photo",
        "shredding_service_id",
        string="Photos",
        help="Photos taken during service",
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    duration_hours = fields.Float(
        string="Actual Duration (Hours)",
        compute="_compute_duration_hours",
        store=True,
        help="Actual service duration in hours",
    )

    shred_bin_id = fields.Many2one("shred.bin", string="Shred Bin")

    # ============================================================================
    # MAIL FRAMEWORK FIELDS (REQUIRED for mail.thread inheritance)
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)]
    )
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id", 
        string="Messages",
        domain=lambda self: [("model", "=", self._name)]
    )
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends(
        "unit_price",
        "actual_volume",
        "actual_weight",
        "travel_charge",
        "emergency_charge",
        "equipment_charge"
    )
    def _compute_total_amount(self):
        """Compute total service amount"""
        for service in self:
            base_amount = service.unit_price * max(
                service.actual_volume, service.actual_weight
            )
            total = (
                base_amount
                + service.travel_charge
                + service.emergency_charge
                + service.equipment_charge
            )
            service.total_amount = total

    @api.depends("actual_start_time", "actual_end_time")
    def _compute_duration_hours(self):
        """Compute actual service duration"""
        for service in self:
            if service.actual_start_time and service.actual_end_time:
                delta = service.actual_end_time - service.actual_start_time
                service.duration_hours = delta.total_seconds() / 3600.0
            else:
                service.duration_hours = 0.0

    @api.depends("inventory_item_ids")
    def _compute_destruction_items(self):
        """Compute number of items to be destroyed"""
        for service in self:
            # Count inventory items if available
            if hasattr(service, 'inventory_item_ids'):
                service.destruction_item_count = len(service.inventory_item_ids)
            else:
                # Fallback to estimated count based on volume
                if service.estimated_volume:
                    # Rough estimate: 1 item per 0.1 cubic feet
                    service.destruction_item_count = int(service.estimated_volume / 0.1)
                else:
                    service.destruction_item_count = 0

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_schedule(self):
        """Schedule the shredding service"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft services can be scheduled"))
        self._validate_scheduling_requirements()
        self.write({"state": "scheduled"})
        self.message_post(body=_("Service scheduled for %s", self.service_date))

    def action_start_service(self):
        """Start the shredding service"""

        self.ensure_one()
        if self.state != "scheduled":
            raise UserError(_("Only scheduled services can be started"))
        self.write({
            "state": "in_progress",
            "actual_start_time": fields.Datetime.now(),
        })
        self.message_post(body=_("Service started"))

    def action_complete_service(self):
        """Complete the shredding service"""

        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress services can be completed"))
        self._validate_completion_requirements()
        self.write({
            "state": "completed",
            "actual_end_time": fields.Datetime.now(),
        })

        # Generate certificate if required
        if self.requires_certificate:
            self._generate_certificate()

        self.message_post(body=_("Service completed"))

    def action_cancel(self):
        """Cancel the shredding service"""

        self.ensure_one()
        if self.state in ("completed", "invoiced"):
            raise UserError(_("Cannot cancel completed or invoiced services"))
        self.write({"state": "cancelled"})
        self.message_post(body=_("Service cancelled"))

    def action_create_invoice(self):
        """Create invoice for the service"""

        self.ensure_one()
        if self.state != "completed":
            raise UserError(_("Only completed services can be invoiced"))

        # Invoice creation logic would go here
        self.write({"state": "invoiced"})
        self.message_post(body=_("Service invoiced"))

    def action_reschedule(self):
        """Reschedule the service"""

        self.ensure_one()
        if self.state not in ("draft", "scheduled"):
            raise UserError(_("Only draft or scheduled services can be rescheduled"))

        return {
            "type": "ir.actions.act_window",
            "name": _("Reschedule Service"),
            "res_model": "shredding.service.reschedule.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_service_id": self.id},
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    def _validate_scheduling_requirements(self):
        """Validate requirements for scheduling"""
        if not self.partner_id:
            raise UserError(_("Customer is required"))
        if not self.service_date:
            raise UserError(_("Service date is required"))
        if not self.team_id and not self.technician_ids:
            raise UserError(_("Team or technicians must be assigned"))

    def _validate_completion_requirements(self):
        """Validate requirements for completion"""
        if not self.actual_volume and not self.actual_weight:
            raise UserError(_("Actual volume or weight must be recorded"))

    def _generate_certificate(self):
        """Generate destruction certificate"""
        certificate_vals = {
            "service_id": self.id,
            "partner_id": self.partner_id.id,
            "certificate_type": self.certificate_type,
            "material_type": self.material_type,
            "volume_destroyed": self.actual_volume,
            "weight_destroyed": self.actual_weight,
            "destruction_date": (
                self.actual_end_time.date()
                if self.actual_end_time
                else fields.Date.today()
            ),
            "compliance_level": self.compliance_level,
        }

        if "shredding.certificate" in self.env:
            certificate = self.env["shredding.certificate"].create(certificate_vals)
            self.certificate_id = certificate.id

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains("service_date")
    def _check_service_date(self):
        """Validate service date is not in the past"""
        for record in self:
            if record.service_date and record.service_date < fields.Date.today():
                if record.state == "draft":  # Allow past dates for completed services
                    raise ValidationError(_("Service date cannot be in the past"))

    @api.constrains("estimated_volume", "estimated_weight")
    def _check_estimates(self):
        """Validate estimated values are non-negative"""
        for record in self:
            if record.estimated_volume < 0 or record.estimated_weight < 0:
                raise ValidationError(_("Estimated values cannot be negative"))

    @api.constrains("actual_start_time", "actual_end_time")
    def _check_actual_times(self):
        """Validate actual start and end times"""
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                if record.actual_end_time <= record.actual_start_time:
                    raise ValidationError(_("End time must be after start time"))

    @api.constrains("unit_price", "travel_charge", "emergency_charge", "equipment_charge")
    def _check_charges(self):
        """Validate charges are non-negative"""
        for record in self:
            charges = [
                record.unit_price,
                record.travel_charge,
                record.emergency_charge,
                record.equipment_charge
            ]
            if any(charge < 0 for charge in charges):
                raise ValidationError(_("All charges must be non-negative"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence numbers"""
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("shredding.service") or "NEW"
                )
        return super().create(vals_list)

    def write(self, vals):
        """Override write to handle state changes"""
        # Log state changes
        if "state" in vals:
            for record in self:
                if record.state != vals["state"]:
                    record.message_post(
                        body=_("State changed from %s to %s",
                            dict(record._fields["state"].selection)[record.state],
                            dict(record._fields["state"].selection)[vals["state"]]
                        )
                    )
        return super().write(vals)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_service_summary(self):
        """Get service summary for reporting"""
        self.ensure_one()
        return {
            "name": self.name,
            "customer": self.partner_id.name,
            "service_type": self.service_type,
            "material_type": self.material_type,
            "service_date": self.service_date,
            "state": self.state,
            "total_amount": self.total_amount,
            "actual_volume": self.actual_volume,
            "actual_weight": self.actual_weight,
            "certificate_required": self.requires_certificate,
            "certificate_generated": bool(self.certificate_id),
        }

    def get_billing_details(self):
        """Get billing details for invoicing"""
        self.ensure_one()
        return {
            "base_amount": self.unit_price * max(self.actual_volume, self.actual_weight),
            "travel_charge": self.travel_charge,
            "emergency_charge": self.emergency_charge,
            "equipment_charge": self.equipment_charge,
            "total_amount": self.total_amount,
            "currency": self.currency_id.name,
        }

    @api.model
    def get_pending_services(self):
        """Get services pending completion"""
        return self.search([
            ("state", "in", ["scheduled", "in_progress"]),
            ("service_date", "<=", fields.Date.today()),
        ])

    @api.model
    def get_overdue_services(self):
        """Get overdue services"""
        return self.search([
            ("state", "in", ["scheduled"]),
            ("service_date", "<", fields.Date.today()),
        ])


class ShreddingServicePhoto(models.Model):
    _name = "shredding.service.photo"
    _description = "Shredding Service Photo"
    _order = "sequence, id"

    service_id = fields.Many2one(
        "shredding.service",
        string="Service",
        required=True,
        ondelete="cascade",
        help="Associated shredding service"
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Photo sequence order"
    )
    name = fields.Char(
        string="Photo Name",
        required=True,
        help="Descriptive name for the photo"
    )
    description = fields.Text(
        string="Description",
        help="Photo description and context"
    )
    photo = fields.Binary(
        string="Photo",
        required=True,
        help="Photo file"
    )
    taken_date = fields.Datetime(
        string="Taken Date",
        default=fields.Datetime.now,
        help="When the photo was taken"
    )
    destruction_item_ids = fields.One2many('destruction.item', 'shredding_service_id', string='Items for Destruction')
    witness_ids = fields.Many2many('res.users', string='Witnesses')
    hourly_rate = fields.Float(string='Hourly Rate', default=75.0)
    photo_type = fields.Selection([
        ("before", "Before Service"),
        ("during", "During Service"),
        ("after", "After Service"),
        ("certificate", "Certificate Documentation"),
    ],
        string="Photo Type",
        default="during",
        help="Type of photo for categorization"
    )
    taken_by_id = fields.Many2one(
        "res.users",
        string="Taken By",
        default=lambda self: self.env.user,
        help="User who took the photo",
    )
