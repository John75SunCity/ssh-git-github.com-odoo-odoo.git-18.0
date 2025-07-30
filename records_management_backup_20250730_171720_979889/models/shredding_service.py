# -*- coding: utf-8 -*-
"""
Shredding Service Management - Enterprise Grade NAID AAA Compliant
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ShreddingService(models.Model):
    """
    Comprehensive Shredding Service Management with NAID AAA Compliance
    Manages on-site and off-site document destruction with complete audit trails
    """

    _name = "shredding.service"
    _description = "Shredding Service Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(
        string="Service Number",
        required=True,
        tracking=True,
        default=lambda self: _("New"),
        copy=False,
    )
    description = fields.Text(string="Service Description", tracking=True)
    active = fields.Boolean(default=True, tracking=True)
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

    # ==========================================
    # CUSTOMER & PARTNER RELATIONSHIPS
    # ==========================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        tracking=True,
        required=True,
        domain=[("is_company", "=", True)],
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Contact Person",
        tracking=True,
        domain="[('parent_id', '=', customer_id)]",
    )

    # ==========================================
    # SERVICE WORKFLOW & STATE MANAGEMENT
    # ==========================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("invoiced", "Invoiced"),
            ("cancelled", "Cancelled"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
    )

    priority = fields.Selection(
        [("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        string="Priority",
        default="normal",
        tracking=True,
    )

    # ==========================================
    # TIMING & SCHEDULING FIELDS
    # ==========================================
    service_date = fields.Date(
        string="Service Date", tracking=True, default=fields.Date.today
    )
    scheduled_start_time = fields.Datetime(string="Scheduled Start Time", tracking=True)
    scheduled_end_time = fields.Datetime(string="Scheduled End Time", tracking=True)
    actual_start_time = fields.Datetime(string="Actual Start Time", tracking=True)
    actual_completion_time = fields.Datetime(
        string="Actual Completion Time", tracking=True
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (Hours)", default=2.0, tracking=True
    )
    actual_duration = fields.Float(
        string="Actual Duration (Hours)", compute="_compute_actual_duration", store=True
    )

    # ==========================================
    # SERVICE TYPE & LOCATION
    # ==========================================
    service_type = fields.Selection(
        [
            ("onsite", "On-Site Shredding"),
            ("offsite", "Off-Site Shredding"),
            ("pickup", "Pickup Only"),
            ("emergency", "Emergency Destruction"),
            ("witnessed", "Witnessed Destruction"),
        ],
        string="Service Type",
        default="onsite",
        required=True,
        tracking=True,
    )

    service_location = fields.Text(string="Service Location", tracking=True)
    customer_site_contact = fields.Char(string="Site Contact Person", tracking=True)
    customer_phone = fields.Char(string="Contact Phone", tracking=True)

    # ==========================================
    # PERSONNEL & ASSIGNMENT FIELDS
    # ==========================================
    assigned_technician = fields.Many2one(
        "res.users", string="Assigned Technician", tracking=True
    )
    backup_technician = fields.Many2one(
        "res.users", string="Backup Technician", tracking=True
    )
    supervising_manager = fields.Many2one(
        "res.users", string="Supervising Manager", tracking=True
    )
    security_officer = fields.Many2one(
        "res.users", string="Security Officer", tracking=True
    )
    customer_representative = fields.Many2one(
        "res.partner",
        string="Customer Representative",
        domain="[('parent_id', '=', customer_id)]",
    )

    # ==========================================
    # DESTRUCTION ITEMS & INVENTORY
    # ==========================================
    destruction_item_ids = fields.One2many(
        "destruction.item", "shredding_service_id", string="Items for Destruction"
    )
    container_ids = fields.Many2many(
        "records.container", string="Containers to Destroy", tracking=True
    )
    document_ids = fields.Many2many(
        "records.document", string="Documents to Destroy", tracking=True
    )

    # ==========================================
    # WEIGHT & QUANTITY TRACKING
    # ==========================================
    estimated_weight = fields.Float(string="Estimated Weight (lbs)", tracking=True)
    actual_weight = fields.Float(string="Actual Weight (lbs)", tracking=True)
    total_weight = fields.Float(
        string="Total Weight", compute="_compute_total_weight", store=True
    )
    container_count = fields.Integer(string="Number of Containers", tracking=True)
    bag_count = fields.Integer(string="Number of Bags", tracking=True)

    # ==========================================
    # VERIFICATION & COMPLIANCE FIELDS
    # ==========================================
    signature_required = fields.Boolean(string="Signature Required", default=True)
    signature_verified = fields.Boolean(string="Signature Verified", tracking=True)
    photo_id_verified = fields.Boolean(string="Photo ID Verified", tracking=True)
    verified = fields.Boolean(string="Service Verified", tracking=True)
    verified_by_customer = fields.Boolean(string="Verified by Customer", tracking=True)
    verification_date = fields.Datetime(string="Verification Date", tracking=True)
    third_party_verified = fields.Boolean(string="Third Party Verified", tracking=True)

    # ==========================================
    # DOCUMENTATION & AUDIT FIELDS
    # ==========================================
    destruction_photographed = fields.Boolean(
        string="Destruction Photographed", tracking=True
    )
    video_recorded = fields.Boolean(string="Video Recorded", tracking=True)
    destruction_notes = fields.Text(string="Destruction Notes", tracking=True)
    special_instructions = fields.Text(string="Special Instructions", tracking=True)
    compliance_notes = fields.Text(string="Compliance Notes", tracking=True)

    # ==========================================
    # CERTIFICATE & REPORTING
    # ==========================================
    certificate_generated = fields.Boolean(
        string="Certificate Generated", tracking=True
    )
    certificate_number = fields.Char(
        string="Certificate Number", tracking=True, copy=False
    )
    certificate_date = fields.Date(string="Certificate Date", tracking=True)
    certificate_id = fields.Many2one(
        "naid.certificate", string="Destruction Certificate"
    )

    # ==========================================
    # BILLING & FINANCIAL FIELDS
    # ==========================================
    billable = fields.Boolean(string="Billable Service", default=True, tracking=True)
    hourly_rate = fields.Float(string="Hourly Rate", tracking=True)
    fixed_rate = fields.Float(string="Fixed Rate", tracking=True)
    total_cost = fields.Float(
        string="Total Cost", compute="_compute_total_cost", store=True, tracking=True
    )
    invoice_id = fields.Many2one(
        "account.move", string="Related Invoice", tracking=True
    )

    # ==========================================
    witness_ids = fields.Many2many("res.users", string="Witnesses")

    # COMPUTED FIELDS
    # ==========================================
    @api.depends("actual_start_time", "actual_completion_time")
    def _compute_actual_duration(self):
        """Calculate actual service duration"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                delta = record.actual_completion_time - record.actual_start_time
                record.actual_duration = delta.total_seconds() / 3600.0
            else:
                record.actual_duration = 0.0

    @api.depends("destruction_item_ids", "destruction_item_ids.weight", "actual_weight")
    def _compute_total_weight(self):
        """Calculate total weight from items or use actual weight"""
        for record in self:
            if record.actual_weight:
                record.total_weight = record.actual_weight
            else:
                record.total_weight = sum(record.destruction_item_ids.mapped("weight"))

    @api.depends("hourly_rate", "actual_duration", "fixed_rate", "billable")
    def _compute_total_cost(self):
        """Calculate total service cost"""
        for record in self:
            if not record.billable:
                record.total_cost = 0.0
            elif record.fixed_rate:
                record.total_cost = record.fixed_rate
            elif record.hourly_rate and record.actual_duration:
                record.total_cost = record.hourly_rate * record.actual_duration
            else:
                record.total_cost = 0.0

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_confirm_service(self):
        """Confirm shredding service"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft services can be confirmed"))

        if self.name == _("New"):
            self.name = self.env["ir.sequence"].next_by_code("shredding.service") or _("New")

        self.write({"state": "confirmed"})
        self.message_post(
            body=_("Shredding service confirmed by %s") % self.env.user.name,
            message_type="notification",
        )

    def action_schedule_service(self):
        """Schedule the shredding service"""
        self.ensure_one()
        if self.state not in ["confirmed"]:
            raise UserError(_("Only confirmed services can be scheduled"))

        if not self.scheduled_start_time:
            raise UserError(_("Please set a scheduled start time"))

        self.write({"state": "scheduled"})
        self.message_post(
            body=_("Service scheduled for %s") % self.scheduled_start_time,
            message_type="notification",
        )

    def action_start_service(self):
        """Start the shredding service"""
        self.ensure_one()
        if self.state not in ["scheduled", "confirmed"]:
            raise UserError(_("Service must be scheduled or confirmed to start"))

        self.write({"state": "in_progress", "actual_start_time": fields.Datetime.now()})
        self.message_post(
            body=_("Service started by %s") % self.env.user.name,
            message_type="notification",
        )

    def action_complete_service(self):
        """Complete the shredding service with verification"""
        self.ensure_one()
        if self.state != "in_progress":
            raise UserError(_("Only services in progress can be completed"))

        # Required verifications for NAID compliance
        if self.signature_required and not self.signature_verified:
            raise UserError(_("Customer signature verification required"))

        if not self.verified_by_customer:
            raise UserError(_("Customer verification required"))

        completion_values = {
            "state": "completed",
            "actual_completion_time": fields.Datetime.now(),
            "verification_date": fields.Datetime.now(),
        }

        # Auto-generate certificate if not exists
        if not self.certificate_id:
            completion_values.update(
                {
                    "certificate_generated": True,
                    "certificate_date": fields.Date.today(),
                    "certificate_number": self._generate_certificate_number(),
                }
            )

        self.write(completion_values)
        self._create_destruction_certificate()
        self.message_post(
            body=_("Service completed with NAID compliance verification"),
            message_type="notification",
        )

    def action_cancel_service(self):
        """Cancel the shredding service"""
        self.ensure_one()
        if self.state in ["completed", "invoiced"]:
            raise UserError(_("Cannot cancel completed or invoiced services"))

        self.write({"state": "cancelled"})
        self.message_post(
            body=_("Service cancelled by %s") % self.env.user.name,
            message_type="notification",
        )

    # ==========================================
    # HELPER METHODS
    # ==========================================
    def _generate_certificate_number(self):
        """Generate unique certificate number"""
        sequence = self.env["ir.sequence"].next_by_code("naid.certificate")
        return f"CERT-{sequence}-{fields.Date.today().strftime('%Y%m%d')}"

    def _create_destruction_certificate(self):
        """Create destruction certificate record"""
        if not self.certificate_id:
            cert_vals = {
                "name": f"Certificate for {self.name}",
                "service_id": self.id,
                "certificate_number": self.certificate_number,
                "destruction_date": self.service_date,
                "customer_id": self.customer_id.id,
                "total_weight": self.total_weight,
                "destruction_method": self.service_type,
                "verified": self.verified_by_customer,
            }
            certificate = self.env["naid.certificate"].create(cert_vals)
            self.write({"certificate_id": certificate.id})

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number"""
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "shredding.service"
                ) or _("New")
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains("scheduled_start_time", "scheduled_end_time")
    def _check_schedule_times(self):
        """Validate schedule times"""
        for record in self:
            if record.scheduled_start_time and record.scheduled_end_time:
                if record.scheduled_end_time <= record.scheduled_start_time:
                    raise ValidationError(_("End time must be after start time"))

    @api.constrains("actual_start_time", "actual_completion_time")
    def _check_actual_times(self):
        """Validate actual service times"""
        for record in self:
            if record.actual_start_time and record.actual_completion_time:
                if record.actual_completion_time <= record.actual_start_time:
                    raise ValidationError(_("Completion time must be after start time"))
