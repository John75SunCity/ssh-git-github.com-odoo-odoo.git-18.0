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

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingHardDrive(models.Model):
    _name = "shredding.hard_drive"
    _description = "Hard Drive Destruction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Reference Number",
        required=True,
        tracking=True,
        index=True,
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
            ("destroyed", "Destroyed"),
            ("certified", "Certified"),
        ],
        string="Status",
        default="draft",
        tracking=True,
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
        string="Asset Tag", tracking=True, help="Customer asset tag or identifier"
    )
    make_model = fields.Char(
        string="Make/Model",
        tracking=True,
        help="Manufacturer and model of the hard drive",
    )
    capacity_gb = fields.Float(
        string="Capacity (GB)", digits=(10, 2), help="Storage capacity in gigabytes"
    )
    hashed_serial = fields.Char(
        string="Hashed Serial Number",
        help="Cryptographically hashed serial for security",
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
    customer_location_notes = fields.Text(
        string="Customer Location Notes",
        help="Notes about customer location and pickup conditions",
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
    scanned_at_customer_by = fields.Many2one(
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
        ],
        string="Physical Condition",
        default="good",
        tracking=True,
        help="Physical condition assessment",
    )
    facility_verification_notes = fields.Text(
        string="Facility Verification Notes",
        help="Notes from facility verification and inspection",
    )

    # ============================================================================
    # SECURITY AND CLASSIFICATION
    # ============================================================================
    data_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
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
            ("basic", "Basic"),
            ("advanced", "Advanced"),
            ("military", "Military Grade"),
        ],
        string="Encryption Level",
        default="none",
        tracking=True,
        help="Level of encryption on the drive",
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
        ],
        string="Destruction Method",
        tracking=True,
        help="Method used for physical destruction",
    )
    destruction_date = fields.Date(
        string="Destruction Date",
        tracking=True,
        help="Date when destruction was completed",
    )
    destruction_witness_required = fields.Boolean(
        string="Destruction Witness Required",
        default=False,
        help="Whether witness is required for destruction",
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

    # ============================================================================
    # COMPLIANCE AND STANDARDS
    # ============================================================================
    sanitization_standard = fields.Selection(
        [
            ("dod_5220", "DoD 5220.22-M"),
            ("nist_800_88", "NIST 800-88"),
            ("nsa_css", "NSA/CSS EPL"),
            ("custom", "Custom Standard"),
        ],
        string="Sanitization Standard",
        default="nist_800_88",
        tracking=True,
        help="Applied sanitization standard",
    )
    physical_destruction_level = fields.Selection(
        [
            ("level_1", "Level 1 - Basic"),
            ("level_2", "Level 2 - Enhanced"),
            ("level_3", "Level 3 - High Security"),
            ("level_4", "Level 4 - Top Secret"),
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
        default=False,
        help="Whether degaussing is required before destruction",
    )
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        default=False,
        tracking=True,
        help="Whether chain of custody has been verified",
    )

    # ============================================================================
    # PROCESSING AND ANALYSIS
    # ============================================================================
    forensic_analysis_completed = fields.Boolean(
        string="Forensic Analysis Completed",
        default=False,
        tracking=True,
        help="Whether forensic analysis has been completed",
    )
    forensic_analysis_notes = fields.Text(
        string="Forensic Analysis Notes", help="Detailed notes from forensic analysis"
    )

    # ============================================================================
    # CERTIFICATE AND DOCUMENTATION
    # ============================================================================
    certificate_number = fields.Char(
        string="Certificate Number",
        tracking=True,
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

    # ============================================================================
    # SERVICE AND WORKFLOW
    # ============================================================================
    service_request_id = fields.Many2one(
        "shredding.service",
        string="Service Request",
        tracking=True,
        help="Related shredding service request",
    )
    approved_by = fields.Many2one(
        "res.users",
        string="Approved By",
        tracking=True,
        help="User who approved the destruction",
    )
    completed = fields.Boolean(
        string="Process Completed",
        default=False,
        tracking=True,
        help="Whether the complete process has been finished",
    )

    # ============================================================================
    # OPERATIONAL DETAILS
    # ============================================================================
    weight = fields.Float(
        string="Weight (lbs)", digits=(10, 2), help="Weight of the hard drive in pounds"
    )
    sequence = fields.Integer(
        string="Sequence", default=10, help="Sequence for ordering records"
    )
    created_date = fields.Date(
        string="Created Date",
        default=fields.Date.today,
        tracking=True,
        help="Date when record was created",
    )
    updated_date = fields.Date(
        string="Updated Date", tracking=True, help="Date when record was last updated"
    )

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    description = fields.Text(
        string="Description", help="Detailed description of the hard drive"
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
    # ODOO FRAMEWORK METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with serial number and customer"""
        result = []
        for record in self:
            name = record.name
            if record.serial_number:
                name = _("%s - %s"
            if record.customer_id:
                name = _("%s (%s)"
            result.append((record.id, name))
        return result

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate reference numbers"""
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

            vals["created_date"] = fields.Date.today()

        return super().create(vals_list)

    def write(self, vals):
        """Override write to update timestamp"""
        if vals:
            vals["updated_date"] = fields.Date.today()
        return super().write(vals)

    # ============================================================================
    # STATE MANAGEMENT METHODS
    # ============================================================================
    def action_scan_at_customer(self):
        """Mark as scanned at customer location"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Can only scan items in draft state"))

        self.write(
            {
                "state": "scanned",
                "scanned_at_customer": True,
                "scanned_at_customer_by": self.env.user.id,
                "scanned_at_customer_date": fields.Datetime.now(),
            }
        )

        self.message_post(body=_("Hard drive scanned at customer location"))

    def action_mark_transported(self):
        """Mark as in transit"""
        self.ensure_one()
        if self.state not in ["scanned"]:
            raise UserError(_("Can only transport scanned items"))

        self.write({"state": "transported"})
        self.message_post(body=_("Hard drive marked as in transit"))

    def action_receive_at_facility(self):
        """Mark as received at facility"""
        self.ensure_one()
        if self.state not in ["transported"]:
            raise UserError(_("Can only receive transported items"))

        self.write(
            {
                "state": "received",
                "chain_of_custody_verified": True,
            }
        )

        self.message_post(body=_("Hard drive received at facility"))

    def action_complete_destruction(self):
        """Complete the destruction process"""
        self.ensure_one()
        if self.state not in ["received"]:
            raise UserError(_("Can only destroy items received at facility"))

        if not self.destruction_method:
            raise UserError(_("Destruction method must be specified"))

        self.write(
            {
                "state": "destroyed",
                "destroyed": True,
                "destruction_date": fields.Date.today(),
                "destruction_method_verified": True,
            }
        )

        self.message_post(
            body=_("Hard drive destruction completed using %s", dict(self._fields["destruction_method"].selection)).get(
                self.destruction_method
            )
        )

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

        self.write(
            {
                "state": "certified",
                "completed": True,
            }
        )

        self.message_post(
            body=_("Destruction certificate generated: %s", self.certificate_number)
        )

    # ============================================================================
    # COMPLIANCE AND VERIFICATION METHODS
    # ============================================================================
    def action_verify_chain_of_custody(self):
        """Verify chain of custody"""
        self.ensure_one()

        self.write({"chain_of_custody_verified": True})
        self.message_post(body=_("Chain of custody verified"))

    def action_complete_forensic_analysis(self):
        """Complete forensic analysis"""
        self.ensure_one()

        self.write({"forensic_analysis_completed": True})
        self.message_post(body=_("Forensic analysis completed"))

    def action_verify_nist_compliance(self):
        """Verify NIST compliance"""
        self.ensure_one()

        self.write({"nist_compliance_verified": True})
        self.message_post(body=_("NIST compliance verified"))

    def action_verify_destruction_method(self):
        """Verify destruction method"""
        self.ensure_one()

        if not self.destruction_method:
            raise UserError(_("Destruction method must be specified first"))

        self.write({"destruction_method_verified": True})
        self.message_post(
            body=_("Destruction method verified: %s", dict(self._fields["destruction_method"].selection)).get(
                self.destruction_method
            )
        )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains("serial_number")
    def _check_serial_number_unique(self):
        """Ensure serial numbers are unique per customer"""
        for record in self:
            if record.serial_number:
                duplicate = self.search(
                    [
                        ("id", "!=", record.id),
                        ("serial_number", "=", record.serial_number),
                        ("customer_id", "=", record.customer_id.id),
                    ]
                )
                if duplicate:
                    raise ValidationError(
                        _("Serial number %s already exists for customer %s", (record.serial_number), record.customer_id.name)
                    )

    @api.constrains("capacity_gb", "weight")
    def _check_positive_values(self):
        """Ensure capacity and weight are positive"""
        for record in self:
            if record.capacity_gb < 0:
                raise ValidationError(_("Capacity cannot be negative"))
            if record.weight < 0:
                raise ValidationError(_("Weight cannot be negative"))

    @api.constrains("destruction_date")
    def _check_destruction_date(self):
        """Validate destruction date"""
        for record in self:
            if (
                record.destruction_date
                and record.destruction_date > fields.Date.today()
            ):
                raise ValidationError(_("Destruction date cannot be in the future"))

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
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
        }

    @api.model
    def get_destruction_statistics(self):
        """Get destruction statistics for dashboard"""
        total_count = self.search_count([])
        destroyed_count = self.search_count([("destroyed", "=", True)])
        certified_count = self.search_count([("state", "=", "certified")])

        return {
            "total_drives": total_count,
            "destroyed_drives": destroyed_count,
            "certified_drives": certified_count,
            "pending_destruction": total_count - destroyed_count,
            "completion_rate": (
                (destroyed_count / total_count * 100) if total_count > 0 else 0
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
            "data_classification": drive_details.get("data_classification", "internal"),
            "encryption_level": drive_details.get("encryption_level", "none"),
        }

        return self.create(drive_data)
        return self.create(drive_data)
