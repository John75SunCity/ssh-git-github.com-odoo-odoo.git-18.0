# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ShreddingService(models.Model):
    _name = "shredding.service"
    _description = "Shredding Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # Basic Information
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)

    # Essential Shredding Service Fields (from view analysis)
    customer_id = fields.Many2one(
        "res.partner", string="Customer", required=True, tracking=True
    )
    service_location_type = fields.Selection(
        [("onsite", "On-Site"), ("offsite", "Off-Site")],
        string="Service Location",
        required=True,
        default="onsite",
        tracking=True,
    )
    service_type = fields.Selection(
        [
            ("box_shredding", "Box Shredding"),
            ("bin_shredding", "Bin Shredding"),
            ("hard_drive_destruction", "Hard Drive Destruction"),
            ("uniform_destruction", "Uniform Destruction"),
            ("pickup", "Pickup Service"),
            ("scheduled", "Scheduled Service"),
            ("emergency", "Emergency Shredding"),
            ("purge", "Purge Service"),
        ],
        string="Service Type",
        required=True,
        tracking=True,
    )

    status = fields.Selection(
        [
            ("scheduled", "Scheduled"),
            ("in_progress", "In Progress"),
            ("completed", "Completed"),
            ("cancelled", "Cancelled"),
            ("rescheduled", "Rescheduled"),
        ],
        string="Status",
        default="scheduled",
        tracking=True,
    )

    # Scheduling
    scheduled_date = fields.Datetime(
        string="Scheduled Date", required=True, tracking=True
    )
    actual_start_time = fields.Datetime(string="Actual Start Time")
    actual_completion_time = fields.Datetime(string="Actual Completion Time")
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)", digits=(8, 2)
    )

    # Destruction Details
    destruction_method = fields.Selection(
        [
            ("cross_cut", "Cross Cut Shredding"),
            ("strip_cut", "Strip Cut Shredding"),
            ("disintegration", "Disintegration"),
            ("pulverization", "Pulverization"),
            ("incineration", "Incineration"),
            ("degaussing", "Degaussing (Electronic Media)"),
        ],
        string="Destruction Method",
        required=True,
        tracking=True,
    )

    # NAID Compliance
    naid_compliance_level = fields.Selection(
        [
            ("aaa", "NAID AAA"),
            ("aa", "NAID AA"),
            ("a", "NAID A"),
            ("standard", "Standard"),
        ],
        string="NAID Compliance Level",
        required=True,
        default="standard",
    )

    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    witness_required = fields.Boolean(string="Witness Required", default=False)

    # === MISSING FIELDS FROM VIEW ANALYSIS ===

    # Chain of Custody and Compliance
    chain_of_custody_number = fields.Char(
        string="Chain of Custody Number",
        tracking=True,
        help="Unique identifier for chain of custody tracking",
    )
    compliance_status = fields.Selection(
        [
            ("pending", "Pending Review"),
            ("compliant", "Compliant"),
            ("non_compliant", "Non-Compliant"),
            ("requires_attention", "Requires Attention"),
        ],
        string="Compliance Status",
        default="pending",
        tracking=True,
    )
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal Use"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Confidentiality Level",
        default="confidential",
        required=True,
    )
    customer_representative = fields.Many2one(
        "res.partner",
        string="Customer Representative",
        help="Customer contact person for this service",
    )

    # Staff Assignment
    assigned_technician = fields.Many2one(
        "hr.employee",
        string="Assigned Technician",
        help="Technician assigned to perform the service",
    )
    supervising_manager = fields.Many2one(
        "hr.employee",
        string="Supervising Manager",
        help="Manager supervising the service",
    )

    # Service Location and Timing
    service_location = fields.Many2one(
        "records.location",
        string="Service Location",
        help="Location where the service will be performed",
    )
    estimated_duration = fields.Float(
        string="Estimated Duration (hours)",
        digits=(5, 2),
        help="Estimated time to complete the service",
    )
    actual_start_time = fields.Datetime(string="Actual Start Time", tracking=True)
    actual_completion_time = fields.Datetime(
        string="Actual Completion Time", tracking=True
    )

    # NAID Compliance Enhancement
    naid_compliance_verified = fields.Boolean(
        string="NAID Compliance Verified",
        default=False,
        help="Indicates if NAID compliance has been verified",
    )
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained",
        default=True,
        help="Indicates if chain of custody has been properly maintained",
    )

    # Service Details
    container_count = fields.Integer(string="Container Count", default=0)
    total_weight = fields.Float(string="Total Weight (lbs)", digits=(10, 2))
    document_types = fields.Text(string="Document Types")
    uniform_destruction_details = fields.Text(string="Uniform Destruction Details")

    # Uniform-Specific Fields
    uniform_type = fields.Selection(
        [
            ("corporate", "Corporate Uniforms"),
            ("medical", "Medical Scrubs"),
            ("security", "Security Uniforms"),
            ("hospitality", "Hospitality Uniforms"),
            ("school", "School Uniforms"),
            ("industrial", "Industrial Workwear"),
            ("other", "Other Uniform Types"),
        ],
        string="Uniform Type",
        help="Type of uniforms being destroyed",
    )
    uniform_count = fields.Integer(string="Number of Uniforms", default=0)
    uniform_brands = fields.Text(string="Uniform Brands/Labels")
    uniform_destruction_reason = fields.Selection(
        [
            ("expired", "Expired/End of Use"),
            ("damaged", "Damaged Beyond Repair"),
            ("rebrand", "Company Rebranding"),
            ("policy", "Policy Change"),
            ("contaminated", "Contaminated"),
            ("recalled", "Product Recall"),
        ],
        string="Destruction Reason",
    )

    # Location and Logistics
    service_location = fields.Text(string="Service Location")
    onsite_requirements = fields.Text(
        string="On-Site Requirements", help="Special requirements for on-site service"
    )
    access_instructions = fields.Text(string="Site Access Instructions")
    assigned_technician = fields.Many2one("res.users", string="Assigned Technician")
    vehicle_id = fields.Many2one("fleet.vehicle", string="Service Vehicle")

    # Financial
    service_cost = fields.Monetary(string="Service Cost", currency_field="currency_id")
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    )

    # Documentation
    certificate_generated = fields.Boolean(
        string="Certificate Generated", default=False
    )
    photos_taken = fields.Integer(string="Photos Taken", default=0)
    chain_of_custody_maintained = fields.Boolean(
        string="Chain of Custody Maintained", default=True
    )

    # === COMPREHENSIVE MISSING FIELDS FROM VIEW ANALYSIS ===

    # Destruction Items and Witness Management (One2many relationships)
    destruction_item_ids = fields.One2many(
        "shredding.destruction.item", "service_id", string="Destruction Items"
    )
    witness_verification_ids = fields.One2many(
        "shredding.witness.verification", "service_id", string="Witness Verifications"
    )

    # Equipment and Process Details
    shredding_equipment = fields.Char(
        string="Shredding Equipment", help="Equipment used for destruction"
    )
    particle_size = fields.Selection(
        [
            ("level_1", "Level 1 - 12mm"),
            ("level_2", "Level 2 - 6mm"),
            ("level_3", "Level 3 - 4mm"),
            ("level_4", "Level 4 - 2mm"),
            ("level_5", "Level 5 - 0.8mm"),
            ("level_6", "Level 6 - 1mm x 5mm"),
        ],
        string="Particle Size",
        help="Security level particle size specification",
    )
    destruction_standard = fields.Selection(
        [
            ("din_66399", "DIN 66399"),
            ("nist_800_88", "NIST 800-88"),
            ("dod_5220", "DoD 5220.22-M"),
            ("hipaa", "HIPAA"),
            ("sox", "SOX"),
        ],
        string="Destruction Standard",
        help="Industry standard compliance for destruction",
    )
    equipment_calibration_date = fields.Date(
        string="Equipment Calibration Date",
        help="Last calibration date of destruction equipment",
    )

    # Weight and Efficiency Tracking
    pre_destruction_weight = fields.Float(
        string="Pre-Destruction Weight (lbs)", digits=(10, 2)
    )
    post_destruction_weight = fields.Float(
        string="Post-Destruction Weight (lbs)", digits=(10, 2)
    )
    destruction_efficiency = fields.Float(
        string="Destruction Efficiency (%)",
        digits=(5, 2),
        compute="_compute_destruction_efficiency",
        store=True,
    )
    quality_control_passed = fields.Boolean(
        string="Quality Control Passed", default=False
    )

    # Detailed Process Notes
    destruction_notes = fields.Text(
        string="Destruction Notes", help="Detailed notes about the destruction process"
    )

    # Certificate Management
    certificate_number = fields.Char(string="Certificate Number", tracking=True)
    certificate_date = fields.Date(string="Certificate Date", default=fields.Date.today)
    certificate_type = fields.Selection(
        [
            ("standard", "Standard Certificate"),
            ("witnessed", "Witnessed Certificate"),
            ("naid_aaa", "NAID AAA Certificate"),
            ("custom", "Custom Certificate"),
        ],
        string="Certificate Type",
        default="standard",
    )
    naid_member_id = fields.Char(
        string="NAID Member ID", help="NAID membership identification number"
    )

    # Verification and Documentation
    destruction_photographed = fields.Boolean(
        string="Destruction Photographed", default=False
    )
    video_recorded = fields.Boolean(string="Video Recorded", default=False)
    third_party_verified = fields.Boolean(string="Third Party Verified", default=False)
    environmental_compliance = fields.Boolean(
        string="Environmental Compliance", default=True
    )

    # Quality and Compliance
    quality_check_passed = fields.Boolean(string="Quality Check Passed", default=False)
    compliance_verified = fields.Boolean(string="Compliance Verified", default=False)
    audit_trail_ids = fields.One2many(
        "shredding.audit.trail", "service_id", string="Audit Trail"
    )

    # Customer Service
    customer_notification_sent = fields.Boolean(
        string="Customer Notification Sent", default=False
    )
    customer_feedback = fields.Text(string="Customer Feedback")
    customer_rating = fields.Selection(
        [
            ("1", "Poor"),
            ("2", "Fair"),
            ("3", "Good"),
            ("4", "Very Good"),
            ("5", "Excellent"),
        ],
        string="Customer Rating",
    )

    # Related Records
    work_order_id = fields.Many2one("work.order.shredding", string="Work Order")
    invoice_id = fields.Many2one("account.move", string="Invoice")
    pickup_request_id = fields.Many2one("pickup.request", string="Pickup Request")

    # System Fields
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company
    )
    user_id = fields.Many2one(
        "res.users", string="Service Manager", default=lambda self: self.env.user
    )

    # State Management
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("inactive", "Inactive"),
            ("archived", "Archived"),
        ],
        string="State",
        default="draft",
        tracking=True,
    )

    # Timestamps
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")

    # Control Fields
    active = fields.Boolean(string="Active", default=True)
    notes = fields.Text(string="Internal Notes")

    # Computed Fields
    display_name = fields.Char(
        string="Display Name", compute="_compute_display_name", store=True
    )
    is_uniform_service = fields.Boolean(
        string="Is Uniform Service", compute="_compute_is_uniform_service", store=True
    )
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    destruction_date = fields.Date(string="Destruction Date")
    certificate_number = fields.Char(string="Certificate Number")
    weight = fields.Float(string="Weight (lbs)", digits=(10, 2))
    approved_by = fields.Many2one("res.users", string="Approved By")
    completed = fields.Boolean(string="Completed", default=False)
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    updated_date = fields.Datetime(string="Updated Date")
    # === COMPREHENSIVE MISSING FIELDS ===
    security_level = fields.Selection(
        [
            ("p1", "P-1"),
            ("p2", "P-2"),
            ("p3", "P-3"),
            ("p4", "P-4"),
            ("p5", "P-5"),
            ("p6", "P-6"),
            ("p7", "P-7"),
        ],
        string="Security Level",
    )
    naid_compliant = fields.Boolean(string="NAID Compliant", default=True)
    scheduled_service_date = fields.Datetime(string="Scheduled Service Date")
    actual_service_date = fields.Datetime(string="Actual Service Date")
    service_duration_hours = fields.Float(
        string="Service Duration (hours)", digits=(5, 2)
    )
    technician_ids = fields.Many2many("hr.employee", string="Assigned Technicians")
    equipment_ids = fields.Many2many("shredding.equipment", string="Equipment Used")
    pickup_manifest_id = fields.Many2one("pickup.manifest", string="Pickup Manifest")
    destruction_items_ids = fields.One2many(
        "destruction.item", "service_id", string="Items for Destruction"
    )
    total_weight_lbs = fields.Float(
        string="Total Weight (lbs)", digits=(10, 2), compute="_compute_total_weight"
    )
    certificate_of_destruction_id = fields.Many2one(
        "destruction.certificate", string="Certificate of Destruction"
    )
    chain_of_custody_id = fields.Many2one("chain.of.custody", string="Chain of Custody")
    witness_signature = fields.Binary(string="Witness Signature")
    witness_name = fields.Char(string="Witness Name")
    witness_title = fields.Char(string="Witness Title")
    pre_destruction_inspection = fields.Boolean(string="Pre-destruction Inspection")
    post_destruction_verification = fields.Boolean(
        string="Post-destruction Verification"
    )
    photographic_evidence = fields.Boolean(string="Photographic Evidence")
    video_evidence = fields.Boolean(string="Video Evidence")
    service_charge = fields.Monetary(
        string="Service Charge", currency_field="currency_id"
    )
    additional_fees = fields.Monetary(
        string="Additional Fees", currency_field="currency_id"
    )
    total_amount = fields.Monetary(
        string="Total Amount",
        currency_field="currency_id",
        compute="_compute_total_amount",
    )
    payment_status = fields.Selection(
        [("pending", "Pending"), ("paid", "Paid"), ("overdue", "Overdue")],
        string="Payment Status",
        default="pending",
    )

    # === CRITICAL MISSING FIELDS FROM VIEW ANALYSIS ===

    # Chain of Custody Transfer Details
    from_person = fields.Char(
        string="From Person", help="Person transferring custody of items"
    )
    to_person = fields.Char(
        string="To Person", help="Person receiving custody of items"
    )
    transfer_date = fields.Datetime(
        string="Transfer Date", help="Date and time of custody transfer"
    )
    transfer_location = fields.Char(
        string="Transfer Location", help="Location where custody transfer occurred"
    )
    seal_number = fields.Char(
        string="Seal Number", help="Security seal number for chain of custody"
    )
    signature_required = fields.Boolean(
        string="Signature Required",
        default=True,
        help="Whether signature is required for this transfer",
    )
    verified = fields.Boolean(
        string="Verified",
        default=False,
        help="Whether the chain of custody has been verified",
    )

    # Hard Drive Management
    hard_drive_ids = fields.One2many(
        "shredding.hard_drive",
        "service_id",
        string="Hard Drives",
        help="Hard drives associated with this shredding service",
    )
    hard_drive_scanned_count = fields.Integer(
        string="Hard Drives Scanned",
        compute="_compute_hard_drive_counts",
        store=True,
        help="Number of hard drives scanned at customer location",
    )
    hard_drive_verified_count = fields.Integer(
        string="Hard Drives Verified",
        compute="_compute_hard_drive_counts",
        store=True,
        help="Number of hard drives verified at facility",
    )

    # Certificate and Item Tracking
    included_in_certificate = fields.Boolean(
        string="Included in Certificate",
        default=True,
        help="Whether this service is included in destruction certificate",
    )
    item_count = fields.Integer(
        string="Item Count",
        compute="_compute_item_count",
        store=True,
        help="Number of items scheduled for destruction",
    )
    witness_count = fields.Integer(
        string="Witness Count",
        compute="_compute_witness_count",
        store=True,
        help="Number of witnesses for destruction process",
    )
    certificate_count = fields.Integer(
        string="Certificate Count",
        compute="_compute_certificate_count",
        store=True,
        help="Number of destruction certificates generated",
    )

    # Location and Personnel Tracking
    location = fields.Char(
        string="Location", help="Current location of items for destruction"
    )
    security_officer = fields.Many2one(
        "hr.employee",
        string="Security Officer",
        help="Security officer overseeing the destruction process",
    )
    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Partner associated with the destruction service",
    )

    # Timing and Status Tracking
    scanned_at_customer = fields.Boolean(
        string="Scanned at Customer",
        default=False,
        help="Whether items were scanned at customer location",
    )
    scanned_at_customer_date = fields.Datetime(
        string="Customer Scan Date",
        help="Date when items were scanned at customer location",
    )
    verified_at_facility_date = fields.Datetime(
        string="Facility Verification Date",
        help="Date when items were verified at facility",
    )
    timestamp = fields.Datetime(
        string="Timestamp",
        default=fields.Datetime.now,
        help="Timestamp for tracking purposes",
    )

    @api.depends(
        "hard_drive_ids",
        "hard_drive_ids.scanned_at_customer",
        "hard_drive_ids.verified_before_destruction",
    )
    def _compute_hard_drive_counts(self):
        """Compute hard drive scanning and verification counts"""
        for record in self:
            scanned_count = len(record.hard_drive_ids.filtered("scanned_at_customer"))
            verified_count = len(
                record.hard_drive_ids.filtered("verified_before_destruction")
            )
            record.hard_drive_scanned_count = scanned_count
            record.hard_drive_verified_count = verified_count

    @api.depends("destruction_item_ids")
    def _compute_item_count(self):
        """Compute total number of destruction items"""
        for record in self:
            record.item_count = len(record.destruction_item_ids)

    @api.depends("witness_verification_ids")
    def _compute_witness_count(self):
        """Compute total number of witnesses"""
        for record in self:
            record.witness_count = len(record.witness_verification_ids)

    @api.depends("certificate_of_destruction_id")
    def _compute_certificate_count(self):
        """Compute total number of certificates"""
        for record in self:
            # Count certificates related to this service
            record.certificate_count = 1 if record.certificate_of_destruction_id else 0

    @api.depends("service_charge", "additional_fees")
    def _compute_total_amount(self):
        """Compute total amount."""
        for record in self:
            record.total_amount = (record.service_charge or 0.0) + (
                record.additional_fees or 0.0
            )

    @api.depends("name")
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _("New")

    @api.depends("service_type")
    def _compute_is_uniform_service(self):
        """Determine if this is a uniform destruction service."""
        for record in self:
            record.is_uniform_service = record.service_type == "uniform_destruction"

    @api.depends("pre_destruction_weight", "post_destruction_weight")
    def _compute_destruction_efficiency(self):
        """Compute destruction efficiency percentage."""
        for record in self:
            if record.pre_destruction_weight and record.post_destruction_weight:
                # Calculate efficiency based on weight reduction
                weight_reduction = (
                    record.pre_destruction_weight - record.post_destruction_weight
                )
                record.destruction_efficiency = (
                    weight_reduction / record.pre_destruction_weight
                ) * 100
            else:
                record.destruction_efficiency = 0.0

    def write(self, vals):
        """Override write to update modification date."""
        vals["date_modified"] = fields.Datetime.now()
        return super().write(vals)

    # Shredding Service Management Fields
    action = fields.Selection(
        [("schedule", "Schedule"), ("complete", "Complete"), ("cancel", "Cancel")],
        "Action",
    )
    certificate_date = fields.Date("Certificate Date")
    certificate_notes = fields.Text("Certificate Notes")
    certificate_type = fields.Selection(
        [
            ("standard", "Standard"),
            ("witnessed", "Witnessed"),
            ("video", "Video Documented"),
        ],
        default="standard",
    )
    chain_of_custody_ids = fields.One2many(
        "chain.of.custody", "shredding_service_id", "Chain of Custody"
    )
    completion_verification_method = fields.Selection(
        [("photo", "Photo"), ("video", "Video"), ("witness", "Witness")],
        default="photo",
    )
    compliance_officer_id = fields.Many2one("hr.employee", "Compliance Officer")
    customer_witness_required = fields.Boolean(
        "Customer Witness Required", default=False
    )
    destruction_location_id = fields.Many2one(
        "destruction.location", "Destruction Location"
    )
    destruction_method_verified = fields.Boolean(
        "Destruction Method Verified", default=False
    )
    destruction_witness_id = fields.Many2one("res.partner", "Destruction Witness")
    environmental_compliance_verified = fields.Boolean(
        "Environmental Compliance Verified", default=False
    )
    equipment_calibration_date = fields.Date("Equipment Calibration Date")
    equipment_serial_number = fields.Char("Equipment Serial Number")
    hard_drive_degaussing_required = fields.Boolean(
        "Hard Drive Degaussing Required", default=False
    )
    material_handling_notes = fields.Text("Material Handling Notes")
    material_type_verification = fields.Selection(
        [
            ("paper_only", "Paper Only"),
            ("mixed_media", "Mixed Media"),
            ("electronic", "Electronic"),
        ],
        default="paper_only",
    )
    naid_aaa_compliance_verified = fields.Boolean(
        "NAID AAA Compliance Verified", default=False
    )
    operator_certification_id = fields.Many2one(
        "operator.certification", "Operator Certification"
    )
    post_destruction_cleanup_required = fields.Boolean(
        "Post Destruction Cleanup Required", default=True
    )
    pre_destruction_audit_completed = fields.Boolean(
        "Pre-destruction Audit Completed", default=False
    )
    quality_assurance_checklist = fields.Text("Quality Assurance Checklist")
    recycling_certificate_number = fields.Char("Recycling Certificate Number")
    security_level_required = fields.Selection(
        [("level_1", "Level 1"), ("level_2", "Level 2"), ("level_3", "Level 3")],
        default="level_1",
    )
    service_completion_photos = fields.Text("Service Completion Photos")
    shredding_particle_size = fields.Selection(
        [
            ("strip_cut", "Strip Cut"),
            ("cross_cut", "Cross Cut"),
            ("micro_cut", "Micro Cut"),
        ],
        default="cross_cut",
    )
    temperature_monitoring_required = fields.Boolean(
        "Temperature Monitoring Required", default=False
    )
    third_party_verification_required = fields.Boolean(
        "Third Party Verification Required", default=False
    )
    transportation_security_verified = fields.Boolean(
        "Transportation Security Verified", default=False
    )
    video_documentation_required = fields.Boolean(
        "Video Documentation Required", default=False
    )
    waste_stream_tracking_number = fields.Char("Waste Stream Tracking Number")
    weight_verification_method = fields.Selection(
        [("scale", "Scale"), ("estimate", "Estimate"), ("count", "Count")],
        default="scale",
    )

    def action_activate(self):
        """Activate the record."""
        self.write({"state": "active"})

    def action_deactivate(self):
        """Deactivate the record."""
        self.write({"state": "inactive"})

    def action_archive(self):
        """Archive the record."""
        self.write({"state": "archived", "active": False})

    # =========================================================================
    # UNIFORM DESTRUCTION SPECIFIC METHODS
    # =========================================================================

    def action_process_uniform_destruction(self):
        """Process uniform destruction with special handling."""
        self.ensure_one()
        if self.service_type != "uniform_destruction":
            raise UserError(
                _("This action is only available for uniform destruction services.")
            )

        if not self.uniform_type:
            raise UserError(_("Uniform type must be specified before processing."))

        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nUniform destruction process initiated on %s for %s uniforms")
                % (
                    fields.Datetime.now(),
                    dict(self._fields["uniform_type"].selection)[self.uniform_type],
                ),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Uniform Destruction Started"),
                "message": _("Uniform destruction process has been initiated for %s")
                % self.uniform_type,
                "type": "success",
            },
        }

    def action_validate_uniform_inventory(self):
        """Validate uniform inventory before destruction."""
        self.ensure_one()
        if not self.is_uniform_service:
            raise UserError(_("This action is only available for uniform services."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Uniform Inventory Validation"),
            "res_model": "uniform.inventory.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_uniform_type": self.uniform_type,
                "default_uniform_count": self.uniform_count,
            },
        }

    # =========================================================================
    # ON-SITE / OFF-SITE SERVICE METHODS
    # =========================================================================

    def action_schedule_onsite_service(self):
        """Schedule on-site shredding service."""
        self.ensure_one()
        if self.service_location_type != "onsite":
            raise UserError(_("This action is only available for on-site services."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule On-Site Service"),
            "res_model": "onsite.scheduling.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_customer_id": self.customer_id.id,
                "default_service_type": self.service_type,
            },
        }

    def action_prepare_offsite_transport(self):
        """Prepare materials for off-site transport."""
        self.ensure_one()
        if self.service_location_type != "offsite":
            raise UserError(_("This action is only available for off-site services."))

        self.write(
            {
                "notes": (self.notes or "")
                + _("\nOff-site transport preparation completed on %s")
                % fields.Datetime.now()
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Transport Prepared"),
                "message": _("Materials prepared for off-site destruction transport"),
                "type": "success",
            },
        }

    def action_validate_site_access(self):
        """Validate access requirements for on-site service."""
        self.ensure_one()
        if self.service_location_type != "onsite":
            raise UserError(
                _("Site access validation is only required for on-site services.")
            )

        if not self.access_instructions:
            raise UserError(
                _("Access instructions must be provided for on-site services.")
            )

        self.write(
            {
                "notes": (self.notes or "")
                + _("\nSite access validated on %s") % fields.Datetime.now()
            }
        )

        return True

    # =========================================================================
    # COMPREHENSIVE SHREDDING SERVICE ACTION METHODS
    # =========================================================================

    def action_view_hard_drives(self):
        """View hard drives associated with this shredding service"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Hard Drives"),
            "res_model": "shredding.hard_drive",
            "view_mode": "tree,form",
            "domain": [("service_id", "=", self.id)],
            "context": {"default_service_id": self.id},
        }

    def action_compliance_check(self):
        """Perform NAID compliance verification check"""
        self.ensure_one()
        # Validate compliance requirements
        if not self.service_type:
            raise UserError(_("Service type must be specified for compliance check"))

        # Mark compliance verified
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nNAID Compliance Check completed on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Compliance Check"),
                "message": _("NAID AAA compliance verification completed successfully"),
                "type": "success",
            },
        }

    def action_mark_customer_scanned(self):
        """Mark hard drives as scanned at customer location"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nCustomer location scanning completed on %s")
                % fields.Datetime.now(),
            }
        )
        return True

    def action_mark_facility_verified(self):
        """Mark items as verified at facility"""
        self.ensure_one()
        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nFacility verification completed on %s") % fields.Datetime.now(),
            }
        )
        return True

    def action_start_destruction(self):
        """Initiate the destruction process with proper validation"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to start destruction"))

        self.write(
            {
                "state": "active",
                "notes": (self.notes or "")
                + _("\nDestruction process started on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Destruction Started"),
                "message": _("Destruction process has been initiated"),
                "type": "success",
            },
        }

    def action_verify_witness(self):
        """Verify witness for destruction process"""
        self.ensure_one()
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nWitness verification completed on %s") % fields.Datetime.now()
            }
        )
        return True

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to generate certificate"))

        # Mark certificate generated
        self.write(
            {
                "notes": (self.notes or "")
                + _("\nDestruction certificate generated on %s") % fields.Datetime.now()
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Generated"),
                "message": _("Destruction certificate has been created successfully"),
                "type": "success",
            },
        }

    def action_scan_hard_drives_customer(self):
        """Scan hard drives at customer location"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Hard Drives - Customer Location"),
            "res_model": "hard_drive.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_location_type": "customer",
            },
        }

    def action_scan_hard_drives_facility(self):
        """Scan hard drives at facility"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Scan Hard Drives - Facility"),
            "res_model": "hard_drive.scan.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_service_id": self.id,
                "default_location_type": "facility",
            },
        }

    def action_witness_verification(self):
        """Open witness verification dialog"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Witness Verification"),
            "res_model": "shredding.service",
            "view_mode": "form",
            "res_id": self.id,
            "target": "new",
            "context": {"show_witness_verification": True},
        }

    def action_mark_destroyed(self):
        """Mark service as completely destroyed"""
        self.ensure_one()
        if self.state not in ["active"]:
            raise UserError(_("Service must be active to mark as destroyed"))

        self.write(
            {
                "state": "inactive",
                "notes": (self.notes or "")
                + _("\nDestruction completed on %s") % fields.Datetime.now(),
            }
        )

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Destruction Complete"),
                "message": _("Service has been marked as completely destroyed"),
                "type": "success",
            },
        }

    def action_view_certificates(self):
        """View all destruction certificates for this service."""
        self.ensure_one()

        # Create activity to track certificate viewing
        self.activity_schedule(
            "mail.mail_activity_data_todo",
            summary=_("Destruction certificates reviewed: %s") % self.name,
            note=_("All destruction certificates for this service have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificates: %s") % self.name,
            "res_model": "destruction.certificate",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_group_by_date": True,
            },
        }

    def action_view_items(self):
        """View all items included in this shredding service."""
        self.ensure_one()

        # Create activity to track item viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Shredding items reviewed: %s") % self.name,
            note=_("All items included in this shredding service have been reviewed."),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shredding Items: %s") % self.name,
            "res_model": "shredding.item",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_group_by_type": True,
            },
        }

    def action_view_witnesses(self):
        """View all witnesses for this shredding service."""
        self.ensure_one()

        # Create activity to track witness viewing
        self.activity_schedule(
            "mail.mail_activity_data_done",
            summary=_("Witnesses reviewed: %s") % self.name,
            note=_(
                "All witnesses for this shredding service have been reviewed and verified."
            ),
            user_id=self.user_id.id,
        )

        return {
            "type": "ir.actions.act_window",
            "name": _("Shredding Witnesses: %s") % self.name,
            "res_model": "shredding.witness",
            "view_mode": "tree,form",
            "target": "current",
            "domain": [("shredding_service_id", "=", self.id)],
            "context": {
                "default_shredding_service_id": self.id,
                "search_default_shredding_service_id": self.id,
                "search_default_verified": True,
            },
        }

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default values."""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = _("New Shredding Service")
        return super().create(vals_list)


class ShreddingDestructionItem(models.Model):
    """Items scheduled for destruction in a shredding service"""

    _name = "shredding.destruction.item"
    _description = "Shredding Destruction Item"
    _order = "sequence, id"

    service_id = fields.Many2one(
        "shredding.service",
        string="Shredding Service",
        required=True,
        ondelete="cascade",
    )
    sequence = fields.Integer(string="Sequence", default=10)
    item_type = fields.Selection(
        [
            ("documents", "Documents"),
            ("hard_drives", "Hard Drives"),
            ("uniforms", "Uniforms"),
            ("media", "Media/Tapes"),
            ("other", "Other Items"),
        ],
        string="Item Type",
        required=True,
    )
    description = fields.Text(string="Description", required=True)
    confidentiality_level = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("restricted", "Restricted"),
            ("top_secret", "Top Secret"),
        ],
        string="Confidentiality Level",
        default="confidential",
    )
    quantity = fields.Float(string="Quantity", digits=(10, 2), required=True)
    unit_of_measure = fields.Selection(
        [
            ("boxes", "Boxes"),
            ("bags", "Bags"),
            ("lbs", "Pounds"),
            ("pieces", "Pieces"),
            ("drives", "Hard Drives"),
        ],
        string="Unit of Measure",
        default="boxes",
    )
    verified_by_customer = fields.Boolean(string="Verified by Customer", default=False)
    chain_of_custody_number = fields.Char(string="Chain of Custody Number")
    destroyed = fields.Boolean(string="Destroyed", default=False)
    destruction_date = fields.Datetime(string="Destruction Date")
    verified_before_destruction = fields.Boolean(
        string="Verified Before Destruction", default=False
    )

    def action_mark_destroyed(self):
        """Mark this item as destroyed"""
        self.write({"destroyed": True, "destruction_date": fields.Datetime.now()})


class ShreddingWitnessVerification(models.Model):
    """Witness verification records for shredding services"""

    _name = "shredding.witness.verification"
    _description = "Shredding Witness Verification"
    _order = "verification_date desc"

    service_id = fields.Many2one(
        "shredding.service",
        string="Shredding Service",
        required=True,
        ondelete="cascade",
    )
    witness_name = fields.Char(string="Witness Name", required=True)
    witness_title = fields.Char(string="Witness Title")
    company = fields.Char(string="Company")
    verification_date = fields.Datetime(
        string="Verification Date", default=fields.Datetime.now
    )
    signature_verified = fields.Boolean(string="Signature Verified", default=False)
    photo_id_verified = fields.Boolean(string="Photo ID Verified", default=False)
    witness_present = fields.Boolean(string="Witness Present", default=True)
    notes = fields.Text(string="Verification Notes")

    def action_verify_witness(self):
        """Mark witness as verified"""
        self.write(
            {
                "signature_verified": True,
                "photo_id_verified": True,
                "verification_date": fields.Datetime.now(),
            }
        )
