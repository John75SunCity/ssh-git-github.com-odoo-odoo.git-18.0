# -*- coding: utf-8 -*-
"""
Hard Drive Destruction Management Module

This module provides comprehensive hard drive destruction management functionality for the Records
Management System. It handles secure hard drive destruction with NAID compliance, chain of custody
tracking, and complete audit trails for regulatory requirements.

Key Features:
- Comprehensive hard drive destruction lifecycle management
- NAID AAA compliance with secure destruction verification
- Chain of custody tracking from pickup to destruction
- Multiple destruction methods (shredding, crushing, degaussing, pulverization)
- Customer location scanning and verification
- Forensic analysis and data classification support
- NIST and DoD compliance standards

Business Processes:
1. Hard Drive Registration: Initial registration with serial numbers and asset tags
2. Customer Location Scanning: On-site verification and barcode scanning
3. Chain of Custody: Secure transport and custody verification
4. Destruction Processing: Physical destruction using certified methods
5. Certificate Generation: NAID compliant destruction certificates
6. Audit Documentation: Complete audit trail for compliance

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

import secrets
from datetime import datetime, timedelta

from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError
import hashlib




class ShreddingHardDrive(models.Model):
    _name = "shredding.hard_drive"
    _description = "Hard Drive Destruction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc, destruction_date desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Reference Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        help="Unique hard drive destruction reference",
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
        help="User responsible for this destruction",
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("scanned", "Scanned at Customer"),
            ("transported", "In Transit"),
            ("received", "Received at Facility"),
            ("analyzed", "Forensic Analysis"),
            ("destroyed", "Destroyed"),
            ("certified", "Certified"),
            ("archived", "Archived"),
        ],
        string="Status",
        default="draft",
        tracking=True,
        required=True,
        help="Current processing status",
    )

    # ============================================================================
    # HARDWARE IDENTIFICATION
    # ============================================================================
    serial_number = fields.Char(
        string="Serial Number",
        required=True,
        tracking=True,
        index=True,
        help="Hardware serial number of the hard drive",
    )
    asset_tag = fields.Char(
        string="Asset Tag", 
        tracking=True, 
        index=True,
        help="Customer asset tag or identifier"
    )
    make_model = fields.Char(
        string="Make/Model",
        tracking=True,
        help="Manufacturer and model of the hard drive",
    )
    capacity_gb = fields.Float(
        string="Capacity (GB)", 
        digits=(10, 2), 
        help="Storage capacity in gigabytes"
    )
    hashed_serial = fields.Char(
        string="Hashed Serial Number",
        compute="_compute_hashed_serial",
        store=True,
        help="Cryptographically hashed serial for security",
    )
    barcode = fields.Char(
        string="Barcode",
        copy=False,
        index=True,
        help="Unique barcode for tracking"
    )

    # ============================================================================
    # CUSTOMER INFORMATION
    # ============================================================================
    customer_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        help="Customer who owns the hard drive",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner", 
        related="customer_id",
        store=True,
        help="Related partner field for One2many relationships compatibility"
    )
    customer_location_id = fields.Many2one(
        "records.location",
        string="Customer Location",
        help="Specific customer location where drive was collected"
    )
    customer_location_notes = fields.Text(
        string="Customer Location Notes",
        help="Notes about customer location and pickup conditions",
    )
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        help="Department responsible for this hard drive"
    )

    # ============================================================================
    # SCANNING AND VERIFICATION
    # ============================================================================
    scanned_at_customer = fields.Boolean(
        string="Scanned at Customer Location",
        default=False,
        tracking=True,
        help="Whether the hard drive was scanned at customer location",
    )
    scanned_at_customer_by_id = fields.Many2one(
        "res.users",
        string="Scanned by (Customer)",
        tracking=True,
        help="User who performed scanning at customer location",
    )
    scanned_at_customer_date = fields.Datetime(
        string="Customer Scan Date",
        tracking=True,
        help="Date and time when scanned at customer location",
    )
    verification_code = fields.Char(
        string="Verification Code",
        help="Unique verification code for scanning"
    )

    # ============================================================================
    # PHYSICAL CONDITION
    # ============================================================================
    physical_condition = fields.Selection(
        [
            ("excellent", "Excellent"),
            ("good", "Good"),
            ("fair", "Fair"),
            ("poor", "Poor"),
            ("damaged", "Damaged"),
            ("inoperable", "Inoperable"),
        ],
        string="Physical Condition",
        default="good",
        tracking=True,
        help="Physical condition assessment",
    )
    condition_notes = fields.Text(
        string="Condition Notes",
        help="Detailed notes about physical condition"
    )
    facility_verification_notes = fields.Text(
        string="Facility Verification Notes",
        help="Notes from facility verification and inspection",
    )
    photos_taken = fields.Boolean(
        string="Photos Taken",
        default=False,
        help="Whether photos were taken for documentation"
    )

    # ============================================================================
    # SECURITY AND CLASSIFICATION
    # ============================================================================
    data_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("secret", "Secret"),
            ("top_secret", "Top Secret"),
        ],
        string="Data Classification",
        default="internal",
        required=True,
        tracking=True,
        help="Security classification of data on drive",
    )
    encryption_level = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic (AES-128)"),
            ("standard", "Standard (AES-256)"),
            ("advanced", "Advanced"),
            ("military", "Military Grade"),
            ("full_disk", "Full Disk Encryption"),
        ],
        string="Encryption Level",
        default="none",
        tracking=True,
        help="Level of encryption on the drive",
    )
    security_level = fields.Selection(
        [
            ("standard", "Standard"),
            ("high", "High Security"),
            ("classified", "Classified"),
            ("top_secret", "Top Secret"),
        ],
        string="Security Level",
        compute="_compute_security_level",
        store=True,
        help="Computed security level based on classification"
    )

    # ============================================================================
    # DESTRUCTION DETAILS
    # ============================================================================
    destruction_method = fields.Selection(
        [
            ("shred", "Physical Shredding"),
            ("crush", "Crushing"),
            ("pulverize", "Pulverization"),
            ("degauss", "Degaussing"),
            ("incineration", "Incineration"),
            ("disintegration", "Disintegration"),
            ("secure_erase", "Secure Digital Erase"),
        ],
        string="Destruction Method",
        tracking=True,
        help="Method used for physical destruction",
    )
    destruction_date = fields.Datetime(
        string="Destruction Date",
        tracking=True,
        help="Date and time when destruction was completed",
    )
    destruction_technician_id = fields.Many2one(
        "res.users",
        string="Destruction Technician",
        help="Technician who performed the destruction"
    )
    destruction_witness_required = fields.Boolean(
        string="Destruction Witness Required",
        compute="_compute_witness_required",
        store=True,
        help="Whether witness is required for destruction",
    )
    destruction_witness_id = fields.Many2one(
        "res.users",
        string="Destruction Witness",
        help="User who witnessed the destruction"
    )
    destruction_method_verified = fields.Boolean(
        string="Destruction Method Verified",
        default=False,
        tracking=True,
        help="Whether destruction method has been verified",
    )
    destroyed = fields.Boolean(
        string="Destroyed",
        default=False,
        tracking=True,
        help="Whether the hard drive has been destroyed",
    )
    particle_size = fields.Char(
        string="Particle Size",
        help="Maximum particle size after destruction (e.g., 2mm)"
    )

    # ============================================================================
    # COMPLIANCE AND STANDARDS
    # ============================================================================
    sanitization_standard = fields.Selection(
        [
            ("dod_5220", "DoD 5220.22-M"),
            ("nist_800_88", "NIST 800-88"),
            ("nsa_css", "NSA/CSS EPL"),
            ("iso_27040", "ISO/IEC 27040"),
            ("cesg", "CESG Higher Level"),
            ("custom", "Custom Standard"),
        ],
        string="Sanitization Standard",
        default="nist_800_88",
        tracking=True,
        required=True,
        help="Applied sanitization standard",
    )
    physical_destruction_level = fields.Selection(
        [
            ("level_1", "Level 1 - Basic Destruction"),
            ("level_2", "Level 2 - Enhanced Destruction"),
            ("level_3", "Level 3 - High Security Destruction"),
            ("level_4", "Level 4 - Top Secret Destruction"),
            ("level_5", "Level 5 - Maximum Security"),
        ],
        string="Physical Destruction Level",
        default="level_2",
        tracking=True,
        help="Level of physical destruction required",
    )
    nist_compliance_verified = fields.Boolean(
        string="NIST Compliance Verified",
        default=False,
        tracking=True,
        help="Whether NIST compliance has been verified",
    )
    degaussing_required = fields.Boolean(
        string="Degaussing Required",
        compute="_compute_degaussing_required",
        store=True,
        help="Whether degaussing is required before destruction",
    )
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        default=False,
        tracking=True,
        help="Whether chain of custody has been verified",
    )
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes related to compliance requirements"
    )

    # ============================================================================
    # PROCESSING AND ANALYSIS
    # ============================================================================
    forensic_analysis_required = fields.Boolean(
        string="Forensic Analysis Required",
        compute="_compute_forensic_analysis_required",
        store=True,
        help="Whether forensic analysis is required"
    )
    forensic_analysis_completed = fields.Boolean(
        string="Forensic Analysis Completed",
        default=False,
        tracking=True,
        help="Whether forensic analysis has been completed",
    )
    forensic_analysis_notes = fields.Text(
        string="Forensic Analysis Notes", 
        help="Detailed notes from forensic analysis"
    )
    forensic_analyst_id = fields.Many2one(
        "res.users",
        string="Forensic Analyst",
        help="User who performed forensic analysis"
    )
    data_found = fields.Boolean(
        string="Data Found",
        default=False,
        help="Whether recoverable data was found during analysis"
    )
    data_classification_confirmed = fields.Boolean(
        string="Data Classification Confirmed",
        default=False,
        help="Whether data classification was confirmed during analysis"
    )

    # ============================================================================
    # CERTIFICATE AND DOCUMENTATION
    # ============================================================================
    certificate_id = fields.Many2one(
        "naid.certificate",
        string="NAID Certificate",
        help="Associated NAID destruction certificate"
    )
    certificate_number = fields.Char(
        string="Certificate Number",
        tracking=True,
        copy=False,
        help="Associated destruction certificate number",
    )
    certificate_line_text = fields.Text(
        string="Certificate Line Text",
        help="Text that appears on the destruction certificate",
    )
    included_in_certificate = fields.Boolean(
        string="Included in Certificate",
        default=True,
        tracking=True,
        help="Whether this hard drive is included in the destruction certificate",
    )
    certificate_generated = fields.Boolean(
        string="Certificate Generated",
        default=False,
        tracking=True,
        help="Whether destruction certificate has been generated"
    )

    # ============================================================================
    # SERVICE AND WORKFLOW
    # ============================================================================
    service_request_id = fields.Many2one(
        "shredding.service",
        string="Service Request",
        tracking=True,
        ondelete="cascade",
        help="Related shredding service request",
    )
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="Related pickup request"
    )
    approved_by_id = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who approved the destruction",
    )
    approval_date = fields.Datetime(
        string="Approval Date",
        tracking=True,
        help="Date and time of approval"
    )
    completed = fields.Boolean(
        string="Process Completed",
        default=False,
        tracking=True,
        help="Whether the complete process has been finished",
    )
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
        help="Processing priority"
    )

    # ============================================================================
    # OPERATIONAL DETAILS
    # ============================================================================
    weight = fields.Float(
        string="Weight (lbs)", 
        digits=(10, 3), 
        help="Weight of the hard drive in pounds"
    )
    sequence = fields.Integer(
        string="Sequence", 
        default=10, 
        help="Sequence for ordering records"
    )
    created_date = fields.Date(
        string="Created Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when record was created",
    )
    updated_date = fields.Date(
        string="Updated Date", 
        tracking=True, 
        help="Date when record was last updated"
    )
    scheduled_destruction_date = fields.Date(
        string="Scheduled Destruction Date",
        help="Planned date for destruction"
    )
    days_since_received = fields.Integer(
        string="Days Since Received",
        compute="_compute_days_since_received",
        help="Number of days since received at facility"
    )

    # ============================================================================
    # FINANCIAL TRACKING
    # ============================================================================
    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field="currency_id",
        help="Estimated cost for destruction"
    )
    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field="currency_id",
        help="Actual cost for destruction"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id
    )
    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this destruction is billable to customer"
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description", 
        help="Detailed description of the hard drive"
    )
    notes = fields.Text(
        string="Internal Notes", 
        help="Internal notes and comments"
    )
    customer_notes = fields.Text(
        string="Customer Notes",
        help="Notes from customer about the hard drive"
    )
    destruction_requirements = fields.Text(
        string="Destruction Requirements",
        help="Special requirements for destruction process"
    )

    # ============================================================================
    # CHAIN OF CUSTODY TRACKING
    # ============================================================================
    custody_events_ids = fields.One2many(
        "naid.custody.event",
        "hard_drive_id",
        string="Custody Events",
        help="Chain of custody events"
    )
    current_custodian_id = fields.Many2one(
        "res.users",
        string="Current Custodian",
        compute="_compute_current_custodian",
        store=True,
        help="Current person responsible for custody"
    )
    custody_location_id = fields.Many2one(
        "records.location",
        string="Current Custody Location",
        help="Current physical location"
    )

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
    @api.depends("serial_number")
    def _compute_hashed_serial(self):
        """Generate cryptographic hash of serial number"""
        for record in self:
            if record.serial_number:
                # Use SHA-256 with salt for security
                salt = self.env["ir.config_parameter"].sudo().get_param(
                    "records.serial.salt", "default_salt_2024"
                )
                hash_input = f"{record.serial_number}{salt}"
                record.hashed_serial = hashlib.sha256(hash_input.encode()).hexdigest()
            else:
                record.hashed_serial = False

    @api.depends("data_classification", "encryption_level")
    def _compute_security_level(self):
        """Compute security level based on classification and encryption"""
        for record in self:
            if record.data_classification in ["secret", "top_secret"]:
                record.security_level = "top_secret"
            elif record.data_classification == "confidential":
                record.security_level = "classified"
            elif record.encryption_level in ["advanced", "military", "full_disk"]:
                record.security_level = "high"
            else:
                record.security_level = "standard"

    @api.depends("data_classification", "security_level")
    def _compute_witness_required(self):
        """Determine if witness is required for destruction"""
        for record in self:
            record.destruction_witness_required = record.data_classification in [
                "confidential", "restricted", "secret", "top_secret"
            ] or record.security_level in ["classified", "top_secret"]

    @api.depends("data_classification", "encryption_level")
    def _compute_degaussing_required(self):
        """Determine if degaussing is required"""
        for record in self:
            record.degaussing_required = (
                record.data_classification in ["secret", "top_secret"] or
                record.encryption_level in ["military", "full_disk"]
            )

    @api.depends("data_classification", "customer_id")
    def _compute_forensic_analysis_required(self):
        """Determine if forensic analysis is required"""
        for record in self:
            # Forensic analysis required for classified data or specific customers
            record.forensic_analysis_required = (
                record.data_classification in ["confidential", "restricted", "secret", "top_secret"] or
                (record.customer_id and record.customer_id.is_government)
            )

    @api.depends("state", "created_date")
    def _compute_days_since_received(self):
        """Calculate days since received at facility"""
        today = fields.Date.today()
        for record in self:
            if record.state in ["received", "analyzed", "destroyed", "certified"]:
                # Find when state changed to 'received'
                received_date = record.created_date
                # Try to find the actual received date from tracking
                tracking_values = self.env["mail.tracking.value"].search([
                    ("mail_message_id.model", "=", self._name),
                    ("mail_message_id.res_id", "=", record.id),
                    ("field", "=", "state"),
                    ("new_value_char", "=", "received"),
                ], limit=1)
                if tracking_values:
                    received_date = tracking_values.mail_message_id.date.date()
                
                record.days_since_received = (today - received_date).days
            else:
                record.days_since_received = 0

    @api.depends("custody_events_ids", "custody_events_ids.custodian_id")
    def _compute_current_custodian(self):
        """Compute current custodian from latest custody event"""
        for record in self:
            latest_event = record.custody_events_ids.sorted("event_date", reverse=True)
            if latest_event:
                record.current_custodian_id = latest_event[0].custodian_id
            else:
                record.current_custodian_id = record.user_id

    # ============================================================================
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with serial number and customer"""
        result = []
        for record in self:
            name = record.name
            if record.serial_number:
                name = f"{name} - {record.serial_number}"
            if record.customer_id:
                name = f"{name} ({record.customer_id.name})"
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate reference numbers and barcodes"""
        for vals in vals_list:
            if not vals.get("name"):
                # Generate reference number
                sequence = self.env["ir.sequence"].next_by_code("shredding.hard_drive")
                if not sequence:
                    # Fallback sequence generation
                    today = fields.Date.today().strftime("%Y%m%d")
                    count = self.search_count([]) + 1
                    sequence = f"HD-{today}-{count:04d}"
                vals["name"] = sequence

            # Generate barcode if not provided
            if not vals.get("barcode"):
                vals["barcode"] = f"HD{secrets.randbelow(1000000):06d}"

            # Generate verification code
            if not vals.get("verification_code"):
                vals["verification_code"] = secrets.token_hex(8).upper()

            vals["created_date"] = fields.Date.today()

        records = super().create(vals_list)
        
        # Create initial custody event
        for record in records:
            self.env["naid.custody.event"].create({
                "hard_drive_id": record.id,
                "event_type": "created",
                "custodian_id": record.user_id.id,
                "location_id": record.custody_location_id.id if record.custody_location_id else False,
                "event_date": fields.Datetime.now(),
                "notes": _("Hard drive record created"),
            })
        
        return records

    def write(self, vals):
        """Override write to update timestamp and track custody changes"""
        if vals:
            vals["updated_date"] = fields.Date.today()
            
            # Track custody changes
            if "current_custodian_id" in vals or "custody_location_id" in vals:
                for record in self:
                    self.env["naid.custody.event"].create({
                        "hard_drive_id": record.id,
                        "event_type": "custody_change",
                        "custodian_id": vals.get("current_custodian_id", record.current_custodian_id.id),
                        "location_id": vals.get("custody_location_id", record.custody_location_id.id),
                        "event_date": fields.Datetime.now(),
                        "notes": _("Custody transferred"),
                    })
        
        return super().write(vals)

    def copy(self, default=None):
        """Override copy to clear unique fields"""
        if default is None:
            default = {}
        default.update({
            "name": _("%s (Copy)", self.name),
            "serial_number": False,
            "barcode": False,
            "certificate_number": False,
            "verification_code": False,
            "state": "draft",
            "destroyed": False,
            "completed": False,
        })
        return super().copy(default)

    # ============================================================================
    # STATE MANAGEMENT METHODS
    # ============================================================================
    def action_scan_at_customer(self):
        """Mark as scanned at customer location"""

        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only scan items in draft state"))

        self.write({
            "state": "scanned",
            "scanned_at_customer": True,
            "scanned_at_customer_by_id": self.env.user.id,
            "scanned_at_customer_date": fields.Datetime.now(),
        })

        # Create custody event
        self._create_custody_event("scanned_customer", _("Scanned at customer location"))
        
        self.message_post(
            body=_("Hard drive scanned at customer location by %s", self.env.user.name),
            subtype_xmlid="mail.mt_note"
        )

    def action_mark_transported(self):
        """Mark as in transit"""

        self.ensure_one()
        if self.state not in ["scanned"]:
            raise UserError(_("Can only transport scanned items"))

        self.write({"state": "transported"})
        
        # Create custody event
        self._create_custody_event("transport", _("Hard drive in transit to facility"))
        
        self.message_post(
            body=_("Hard drive marked as in transit"),
            subtype_xmlid="mail.mt_note"
        )

    def action_receive_at_facility(self):
        """Mark as received at facility"""

        self.ensure_one()
        if self.state not in ["transported"]:
            raise UserError(_("Can only receive transported items"))

        self.write({
            "state": "received",
            "chain_of_custody_verified": True,
        })

        # Create custody event
        self._create_custody_event("received_facility", _("Received at destruction facility"))
        
        self.message_post(
            body=_("Hard drive received at facility and chain of custody verified"),
            subtype_xmlid="mail.mt_comment"
        )
        
        # Create activity for forensic analysis if required
        if self.forensic_analysis_required:
            self.activity_schedule(
                "records_management.mail_activity_forensic_analysis",
                summary=_("Forensic analysis required for %s", self.display_name),
                note=_("This hard drive requires forensic analysis due to its classification level."),
            )

    def action_start_forensic_analysis(self):
        """Start forensic analysis process"""

        self.ensure_one()
        if self.state not in ["received"]:
            raise UserError(_("Can only start forensic analysis for received items"))

        if not self.forensic_analysis_required:
            raise UserError(_("Forensic analysis is not required for this item"))

        self.write({
            "state": "analyzed",
            "forensic_analyst_id": self.env.user.id,
        })

        # Create custody event
        self._create_custody_event("forensic_start", _("Forensic analysis started"))
        
        self.message_post(
            body=_("Forensic analysis started by %s", self.env.user.name),
            subtype_xmlid="mail.mt_comment"
        )

    def action_complete_forensic_analysis(self):
        """Complete forensic analysis"""

        self.ensure_one()
        if self.state not in ["analyzed"]:
            raise UserError(_("Can only complete analysis for items in analysis state"))

        if not self.forensic_analysis_notes:
            raise UserError(_("Please provide forensic analysis notes before completing"))

        self.write({
            "forensic_analysis_completed": True,
            "data_classification_confirmed": True,
        })

        # Create custody event
        self._create_custody_event("forensic_complete", _("Forensic analysis completed"))
        
        self.message_post(
            body=_("Forensic analysis completed. Data classification confirmed as %s", 
                   dict(self._fields["data_classification"].selection).get(self.data_classification)),
            subtype_xmlid="mail.mt_comment"
        )
        
        # Mark activity as done
        activities = self.activity_ids.filtered(
            lambda a: a.activity_type_id.xml_id == "records_management.mail_activity_forensic_analysis"
        )
        activities.action_done()

    def action_complete_destruction(self):
        """Complete the destruction process"""

        self.ensure_one()
        if self.state not in ["received", "analyzed"]:
            raise UserError(_("Can only destroy items received at facility or analyzed"))

        if not self.destruction_method:
            raise UserError(_("Destruction method must be specified"))

        if self.destruction_witness_required and not self.destruction_witness_id:
            raise UserError(_("Destruction witness is required but not specified"))

        # Validate destruction requirements based on classification
        self._validate_destruction_requirements()

        self.write({
            "state": "destroyed",
            "destroyed": True,
            "destruction_date": fields.Datetime.now(),
            "destruction_method_verified": True,
            "destruction_technician_id": self.env.user.id,
        })

        # Create custody event
        method_label = dict(self._fields["destruction_method"].selection).get(
            self.destruction_method, self.destruction_method
        )
        self._create_custody_event(
            "destroyed", 
            _("Physical destruction completed using %s", method_label)
        )
        
        self.message_post(
            body=_("Hard drive destruction completed using %s by technician %s", 
                   method_label, self.env.user.name),
            subtype_xmlid="mail.mt_comment"
        )
        
        # Create NAID audit log
        self._create_naid_audit_log("hard_drive_destroyed")

    def action_generate_certificate(self):
        """Generate destruction certificate"""

        self.ensure_one()
        if self.state not in ["destroyed"]:
            raise UserError(_("Can only generate certificates for destroyed items"))

        # Generate certificate number if not exists
        if not self.certificate_number:
            sequence = self.env["ir.sequence"].next_by_code("destruction.certificate")
            if not sequence:
                today = fields.Date.today().strftime("%Y%m%d")
                count = self.search_count([("certificate_number", "!=", False)]) + 1
                sequence = f"CERT-HD-{today}-{count:04d}"

            self.certificate_number = sequence

        # Generate certificate line text
        self._generate_certificate_line_text()

        self.write({
            "state": "certified",
            "completed": True,
            "certificate_generated": True,
        })

        # Create custody event
        self._create_custody_event("certified", _("Destruction certificate generated"))
        
        self.message_post(
            body=_("Destruction certificate generated: %s", self.certificate_number),
            subtype_xmlid="mail.mt_comment"
        )
        
        # Create NAID audit log
        self._create_naid_audit_log("certificate_generated")

    def action_archive_record(self):
        """Archive the record"""

        self.ensure_one()
        if self.state != "certified":
            raise UserError(_("Can only archive certified records"))

        self.write({"state": "archived"})
        
        # Create custody event
        self._create_custody_event("archived", _("Record archived"))
        
        self.message_post(
            body=_("Hard drive record archived"),
            subtype_xmlid="mail.mt_note"
        )

    # ============================================================================
    # COMPLIANCE AND VERIFICATION METHODS
    # ============================================================================
    def action_verify_chain_of_custody(self):
        """Verify chain of custody"""

        self.ensure_one()

        # Check custody events
        if len(self.custody_events_ids) < 2:
            raise UserError(_("Insufficient custody events for verification"))

        self.write({"chain_of_custody_verified": True})
        
        self.message_post(
            body=_("Chain of custody verified with %d custody events", len(self.custody_events_ids)),
            subtype_xmlid="mail.mt_note"
        )

    def action_verify_nist_compliance(self):
        """Verify NIST compliance"""

        self.ensure_one()

        if not self.destroyed:
            raise UserError(_("Cannot verify NIST compliance before destruction"))

        # Check compliance requirements
        compliance_checks = self._check_nist_compliance()
        
        if not all(compliance_checks.values()):
            failed_checks = [k for k, v in compliance_checks.items() if not v]
            raise UserError(_("NIST compliance verification failed: %s", ", ".join(failed_checks)))

        self.write({"nist_compliance_verified": True})
        
        self.message_post(
            body=_("NIST compliance verified for standard %s", 
                   dict(self._fields["sanitization_standard"].selection).get(self.sanitization_standard)),
            subtype_xmlid="mail.mt_comment"
        )

    def action_verify_destruction_method(self):
        """Verify destruction method"""

        self.ensure_one()

        if not self.destruction_method:
            raise UserError(_("Destruction method must be specified first"))

        # Validate method against security requirements
        required_methods = self._get_required_destruction_methods()
        if self.destruction_method not in required_methods:
            raise UserError(
                _("Destruction method %s is not approved for security level %s. Approved methods: %s",
                  dict(self._fields["destruction_method"].selection).get(self.destruction_method),
                  self.security_level,
                  ", ".join([dict(self._fields["destruction_method"].selection).get(m) for m in required_methods])
                )
            )

        self.write({"destruction_method_verified": True})
        
        method_label = dict(self._fields["destruction_method"].selection).get(
            self.destruction_method, self.destruction_method
        )
        self.message_post(
            body=_("Destruction method verified: %s", method_label),
            subtype_xmlid="mail.mt_note"
        )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("serial_number", "customer_id")
    def _check_serial_number_unique(self):
        """Ensure serial numbers are unique per customer"""
        for record in self:
            if record.serial_number and record.customer_id:
                duplicate = self.search([
                    ("id", "!=", record.id),
                    ("serial_number", "=", record.serial_number),
                    ("customer_id", "=", record.customer_id.id),
                ])
                if duplicate:
                    raise ValidationError(
                        _("Serial number %s already exists for customer %s", 
                          record.serial_number, record.customer_id.name)
                    )

    @api.constrains("capacity_gb", "weight")
    def _check_positive_values(self):
        """Ensure capacity and weight are positive"""
        for record in self:
            if record.capacity_gb < 0:
                raise ValidationError(_("Capacity cannot be negative"))
            if record.weight < 0:
                raise ValidationError(_("Weight cannot be negative"))

    @api.constrains("destruction_date", "scanned_at_customer_date")
    def _check_date_sequence(self):
        """Validate date sequence"""
        for record in self:
            if (
                record.destruction_date
                and record.destruction_date > fields.Datetime.now()
            ):
                raise ValidationError(_("Destruction date cannot be in the future"))
            
            if (
                record.scanned_at_customer_date and record.destruction_date
                and record.scanned_at_customer_date > record.destruction_date
            ):
                raise ValidationError(_("Customer scan date cannot be after destruction date"))

    @api.constrains("barcode")
    def _check_barcode_unique(self):
        """Ensure barcode is unique"""
        for record in self:
            if record.barcode:
                duplicate = self.search([
                    ("id", "!=", record.id),
                    ("barcode", "=", record.barcode),
                ])
                if duplicate:
                    raise ValidationError(_("Barcode %s already exists", record.barcode))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def _create_custody_event(self, event_type, notes):
        """Create a custody event"""
        self.ensure_one()
        return self.env["naid.custody.event"].create({
            "hard_drive_id": self.id,
            "event_type": event_type,
            "custodian_id": self.env.user.id,
            "location_id": self.custody_location_id.id if self.custody_location_id else False,
            "event_date": fields.Datetime.now(),
            "notes": notes,
        })

    def _create_naid_audit_log(self, action):
        """Create NAID audit log entry"""
        self.ensure_one()
        return self.env["naid.audit.log"].create({
            "name": f"{action.title()}: {self.display_name}",
            "action": action,
            "model_name": self._name,
            "record_id": self.id,
            "user_id": self.env.user.id,
            "partner_id": self.customer_id.id,
            "description": f"Hard drive {action.replace('_', ' ')} for {self.display_name}",
            "compliance_level": "naid_aaa",
        })

    def _validate_destruction_requirements(self):
        """Validate destruction requirements based on classification"""
        self.ensure_one()
        
        # Check degaussing requirement
        if self.degaussing_required and self.destruction_method != "degauss":
            if self.destruction_method not in ["pulverize", "disintegration", "incineration"]:
                raise UserError(
                    _("Degaussing or complete physical destruction required for this security level")
                )

        # Check particle size requirements
        if self.physical_destruction_level in ["level_3", "level_4", "level_5"]:
            if not self.particle_size:
                raise UserError(_("Particle size must be specified for high security destruction"))

    def _get_required_destruction_methods(self):
        """Get list of approved destruction methods for security level"""
        self.ensure_one()
        
        method_map = {
            "standard": ["shred", "crush", "pulverize", "degauss"],
            "high": ["shred", "pulverize", "degauss", "disintegration"],
            "classified": ["pulverize", "degauss", "disintegration", "incineration"],
            "top_secret": ["pulverize", "disintegration", "incineration"],
        }
        
        return method_map.get(self.security_level, ["shred", "crush"])

    def _check_nist_compliance(self):
        """Check NIST compliance requirements"""
        self.ensure_one()
        
        compliance_checks = {
            "destruction_method_verified": self.destruction_method_verified,
            "chain_of_custody": self.chain_of_custody_verified,
            "witness_present": not self.destruction_witness_required or bool(self.destruction_witness_id),
            "destruction_completed": self.destroyed,
            "certificate_requirements": self.physical_destruction_level != "level_1" or self.certificate_number,
        }
        
        return compliance_checks

    def _generate_certificate_line_text(self):
        """Generate text for destruction certificate"""
        self.ensure_one()
        
        method_label = dict(self._fields["destruction_method"].selection).get(
            self.destruction_method, self.destruction_method
        )
        
        certificate_text = _(
            "Hard Drive - Serial: %(serial)s - Make/Model: %(model)s - "
            "Capacity: %(capacity)sGB - Method: %(method)s - Date: %(date)s",
            serial=self.serial_number,
            model=self.make_model or "Unknown",
            capacity=self.capacity_gb or 0,
            method=method_label,
            date=self.destruction_date.strftime("%Y-%m-%d %H:%M") if self.destruction_date else ""
        )
        
        self.certificate_line_text = certificate_text

    def get_destruction_summary(self):
        """Get destruction summary for reporting"""
        self.ensure_one()

        return {
            "reference": self.name,
            "serial_number": self.serial_number,
            "customer": self.customer_id.name,
            "destruction_method": dict(
                self._fields["destruction_method"].selection
            ).get(self.destruction_method),
            "destruction_date": self.destruction_date,
            "certificate_number": self.certificate_number,
            "data_classification": dict(
                self._fields["data_classification"].selection
            ).get(self.data_classification),
            "compliance_verified": self.nist_compliance_verified,
            "status": dict(self._fields["state"].selection).get(self.state),
            "security_level": dict(
                self._fields["security_level"].selection
            ).get(self.security_level),
            "days_in_process": self.days_since_received,
        }

    @api.model
    def get_destruction_statistics(self):
        """Get destruction statistics for dashboard"""
        total_count = self.search_count([])
        destroyed_count = self.search_count([("destroyed", "=", True)])
        certified_count = self.search_count([("state", "=", "certified")])
        pending_analysis = self.search_count([("forensic_analysis_required", "=", True), ("forensic_analysis_completed", "=", False)])

        return {
            "total_drives": total_count,
            "destroyed_drives": destroyed_count,
            "certified_drives": certified_count,
            "pending_destruction": total_count - destroyed_count,
            "pending_analysis": pending_analysis,
            "completion_rate": (
                (destroyed_count / total_count * 100) if total_count > 0 else 0
            ),
            "certification_rate": (
                (certified_count / destroyed_count * 100) if destroyed_count > 0 else 0
            ),
        }

    @api.model
    def create_from_service_request(self, service_id, drive_details):
        """Create hard drive records from service request"""
        service = self.env["shredding.service"].browse(service_id)
        if not service.exists():
            raise UserError(_("Service request not found"))

        drive_data = {
            "customer_id": service.customer_id.id,
            "service_request_id": service.id,
            "serial_number": drive_details.get("serial_number"),
            "asset_tag": drive_details.get("asset_tag"),
            "make_model": drive_details.get("make_model"),
            "capacity_gb": drive_details.get("capacity_gb"),
            "weight": drive_details.get("weight"),
            "data_classification": drive_details.get("data_classification", "internal"),
            "encryption_level": drive_details.get("encryption_level", "none"),
            "physical_condition": drive_details.get("physical_condition", "good"),
            "customer_notes": drive_details.get("notes"),
            "priority": service.priority or "normal",
        }

        return self.create(drive_data)

    @api.model
    def create_bulk_from_scan(self, scan_data):
        """Create multiple hard drive records from bulk scan"""
        records = []
        
        for drive_data in scan_data:
            # Validate required fields
            if not drive_data.get("serial_number"):
                continue
                
            # Check for duplicates
            existing = self.search([
                ("serial_number", "=", drive_data["serial_number"]),
                ("customer_id", "=", drive_data.get("customer_id")),
            ])
            
            if existing:
                # Update existing record
                existing.write({
                    "scanned_at_customer": True,
                    "scanned_at_customer_date": fields.Datetime.now(),
                    "scanned_at_customer_by_id": self.env.user.id,
                })
                records.append(existing)
            else:
                # Create new record
                record = self.create(drive_data)
                records.append(record)
        
        return records

    def generate_qr_code_data(self):
        """Generate QR code data for tracking"""
        self.ensure_one()
        
        qr_data = {
            "type": "hard_drive",
            "id": self.id,
            "serial": self.serial_number,
            "verification": self.verification_code,
            "customer": self.customer_id.id,
            "barcode": self.barcode,
        }
        
        return qr_data
