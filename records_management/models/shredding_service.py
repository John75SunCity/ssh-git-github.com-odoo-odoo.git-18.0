# -*- coding: utf-8 -*-

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
        string="Service Order #", required=True, tracking=True, index=True
    reference = fields.Char(string="Reference", index=True, tracking=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    active = fields.Boolean(string="Active", default=True)

    # ============================================================================
    # FRAMEWORK FIELDS
    # ============================================================================

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    user_id = fields.Many2one(
        "res.users",
        string="Service Technician",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================

    state = fields.Selection(
        [
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
    )

    # ============================================================================
    # CUSTOMER & SERVICE RELATIONSHIPS
    # ============================================================================

    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    contact_id = fields.Many2one("res.partner", string="Contact Person")
    location_id = fields.Many2one("records.location", string="Service Location")

    # ============================================================================
    # SERVICE CONFIGURATION
    # ============================================================================

    service_type = fields.Selection(
        [
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
    material_type = fields.Selection(
        [
            ("paper", "Paper Documents"),
            ("hard_drives", "Hard Drives"),
            ("media", "Electronic Media"),
            ("mixed", "Mixed Materials"),
        ],
        string="Material Type",
        default="paper",
        required=True,
    )

    # ============================================================================
    # SCHEDULING
    # ============================================================================

    service_date = fields.Date(string="Scheduled Date", required=True, tracking=True)
    service_time = fields.Float(string="Scheduled Time", help="Time in 24h format")
    estimated_duration = fields.Float(string="Estimated Duration (Hours)", default=2.0)
    priority = fields.Selection(
        [
            ("low", "Low"),
            ("normal", "Normal"),
            ("high", "High"),
            ("urgent", "Urgent"),
        ],
        string="Priority",
        default="normal",
        tracking=True,
    )

    # ============================================================================
    # TEAM & RESOURCES
    # ============================================================================

    team_id = fields.Many2one("shredding.team", string="Assigned Team")
    technician_ids = fields.Many2many("hr.employee", string="Technicians")
    vehicle_id = fields.Many2one("records.vehicle", string="Service Vehicle")
    equipment_ids = fields.Many2many("maintenance.equipment", string="Equipment")
    equipment_id = fields.Many2one("maintenance.equipment", string="Primary Equipment")
    recycling_bale_id = fields.Many2one("paper.bale.recycling", string="Recycling Bale")

    # ============================================================================
    # MATERIAL DETAILS
    # ============================================================================

    estimated_volume = fields.Float(
        string="Estimated Volume (Cubic Feet)", digits="Stock Weight", default=0.0
    estimated_weight = fields.Float(
        string="Estimated Weight (lbs)", digits="Stock Weight", default=0.0
    actual_volume = fields.Float(
        string="Actual Volume (Cubic Feet)", digits="Stock Weight", default=0.0
    actual_weight = fields.Float(
        string="Actual Weight (lbs)", digits="Stock Weight", default=0.0
    )

    # Container Information
    container_ids = fields.Many2many("records.container", string="Containers")
    bin_ids = fields.Many2many("shredding.bin", string="Shredding Bins")

    # ============================================================================
    # PRICING & BILLING
    # ============================================================================

    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    unit_price = fields.Float(string="Unit Price", digits="Product Price", default=0.0)
    total_amount = fields.Float(
        string="Total Amount",
        digits="Product Price",
        compute="_compute_total_amount",
        store=True,
    )

    # Additional Charges
    travel_charge = fields.Float(
        string="Travel Charge", digits="Product Price", default=0.0
    emergency_charge = fields.Float(
        string="Emergency Charge", digits="Product Price", default=0.0
    equipment_charge = fields.Float(
        string="Equipment Charge", digits="Product Price", default=0.0
    )

    # ============================================================================
    # COMPLIANCE & CERTIFICATES
    # ============================================================================

    requires_certificate = fields.Boolean(string="Certificate Required", default=True)
    certificate_type = fields.Selection(
        [
            ("standard", "Standard Certificate"),
            ("detailed", "Detailed Certificate"),
            ("chain_of_custody", "Chain of Custody"),
        ],
        string="Certificate Type",
        default="standard",
    certificate_id = fields.Many2one("shredding.certificate", string="Certificate")
    compliance_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("naid_aaa", "NAID AAA"),
            ("dod_5220", "DoD 5220.22-M"),
            ("custom", "Custom"),
        ],
        string="Compliance Level",
        default="standard",
    )

    # ============================================================================
    # SPECIAL INSTRUCTIONS
    # ============================================================================

    special_instructions = fields.Text(string="Special Instructions")
    access_requirements = fields.Text(string="Access Requirements")
    security_clearance = fields.Boolean(string="Security Clearance Required")
    witness_required = fields.Boolean(string="Witness Required")

    # ============================================================================
    # COMPLETION TRACKING
    # ============================================================================

    actual_start_time = fields.Datetime(string="Actual Start Time", readonly=True)
    actual_end_time = fields.Datetime(string="Actual End Time", readonly=True)
    completion_notes = fields.Text(string="Completion Notes")
    customer_signature = fields.Binary(string="Customer Signature")
    photos = fields.One2many("shredding.service.photo", "service_id", string="Photos")

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
        self.message_post(body=_("Service scheduled for %s") % self.service_date)

    def action_start_service(self):
        """Start the shredding service"""
        self.ensure_one()
        if self.state != "scheduled":
            raise UserError(_("Only scheduled services can be started"))

        self.write(
            {
                "state": "in_progress",
                "actual_start_time": fields.Datetime.now(),
            }
        )
        self.message_post(body=_("Service started"))

    def action_complete_service(self):
        """Complete the shredding service"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only in-progress services can be completed"))

        self._validate_completion_requirements()
        self.write(
            {
                "state": "completed",
                "actual_end_time": fields.Datetime.now(),
            }
        )

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

        certificate = self.env["shredding.certificate"].create(certificate_vals)
        self.certificate_id = certificate.id

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    @api.depends(
        "unit_price",
        "actual_volume",
        "actual_weight",
        "travel_charge",
        "emergency_charge",
        "equipment_charge",
    def _compute_total_amount(self):
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

    duration_hours = fields.Float(
        string="Actual Duration (Hours)",
        compute="_compute_duration_hours",
        store=True,
    )

    @api.depends("actual_start_time", "actual_end_time")
    def _compute_duration_hours(self):
        for service in self:
            if service.actual_start_time and service.actual_end_time:
                delta = service.actual_end_time - service.actual_start_time
                service.duration_hours = delta.total_seconds() / 3600.0
            else:
                service.duration_hours = 0.0

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================

    @api.constrains("service_date")
    def _check_service_date(self):
        for record in self:
            if record.service_date < fields.Date.today():
                raise ValidationError(_("Service date cannot be in the past"))

    @api.constrains("estimated_volume", "estimated_weight")
    def _check_estimates(self):
        for record in self:
            if record.estimated_volume < 0 or record.estimated_weight < 0:
                raise ValidationError(_("Estimated values cannot be negative"))

    @api.constrains("actual_start_time", "actual_end_time")
    def _check_actual_times(self):
        for record in self:
            if record.actual_start_time and record.actual_end_time:
                if record.actual_end_time <= record.actual_start_time:
                    raise ValidationError(_("End time must be after start time"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name") or vals["name"] == "/":
                vals["name"] = (
                    self.env["ir.sequence"].next_by_code("shredding.service") or "NEW"
                )
        return super().create(vals_list)

class ShreddingServicePhoto(models.Model):
    _name = "shredding.service.photo"
    _description = "Shredding Service Photo"
    _order = "sequence, id"

    service_id = fields.Many2one(
        "shredding.service", string="Service", required=True, ondelete="cascade"
    sequence = fields.Integer(string="Sequence", default=10)
    name = fields.Char(string="Photo Name", required=True)
    description = fields.Text(string="Description")
    photo = fields.Binary(string="Photo", required=True)
    taken_date = fields.Datetime(string="Taken Date", default=fields.Datetime.now))
