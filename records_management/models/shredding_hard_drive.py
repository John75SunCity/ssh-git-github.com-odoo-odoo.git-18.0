# -*- coding: utf-8 -*-
"""
Hard Drive Destruction
"""

from odoo import models, fields, api, _


class ShreddingHardDrive(models.Model):
    """
    Hard Drive Destruction
    """

    _name = "shredding.hard_drive"
    _description = "Hard Drive Destruction"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    # === COMPREHENSIVE MISSING FIELDS ===
    sequence = fields.Integer(string="Sequence", default=10, tracking=True)
    created_date = fields.Date(
        string="Created Date", default=fields.Date.today, tracking=True
    )
    updated_date = fields.Date(string="Updated Date", tracking=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    customer_id = fields.Many2one("res.partner", string="Customer", tracking=True)
    destruction_date = fields.Date(string="Destruction Date")
    certificate_number = fields.Char(string="Certificate Number")
    destruction_method = fields.Selection(
        [("shred", "Shredding"), ("burn", "Burning"), ("pulp", "Pulping")],
        string="Destruction Method",
    )
    weight = fields.Float(string="Weight (lbs)", digits=(10, 2))
    approved_by = fields.Many2one("res.users", string="Approved By")
    completed = fields.Boolean(string="Completed", default=False)
    # Shredding Hard Drive Management Fields
    certificate_line_text = fields.Text("Certificate Line Text")
    customer_location_notes = fields.Text("Customer Location Notes")
    destroyed = fields.Boolean("Destroyed", default=False)
    facility_verification_notes = fields.Text("Facility Verification Notes")
    hashed_serial = fields.Char("Hashed Serial Number")
    chain_of_custody_verified = fields.Boolean(
        "Chain of Custody Verified", default=False
    )
    data_classification = fields.Selection(
        [
            ("public", "Public"),
            ("internal", "Internal"),
            ("confidential", "Confidential"),
            ("top_secret", "Top Secret"),
        ],
        default="internal",
    )
    degaussing_required = fields.Boolean("Degaussing Required", default=False)
    destruction_method_verified = fields.Boolean(
        "Destruction Method Verified", default=False
    )
    destruction_witness_required = fields.Boolean(
        "Destruction Witness Required", default=False
    )
    encryption_level = fields.Selection(
        [
            ("none", "None"),
            ("basic", "Basic"),
            ("advanced", "Advanced"),
            ("military", "Military Grade"),
        ],
        default="none",
    )
    forensic_analysis_completed = fields.Boolean(
        "Forensic Analysis Completed", default=False
    )
    nist_compliance_verified = fields.Boolean("NIST Compliance Verified", default=False)
    physical_destruction_level = fields.Selection(
        [("level_1", "Level 1"), ("level_2", "Level 2"), ("level_3", "Level 3")],
        default="level_2",
    )
    sanitization_standard = fields.Selection(
        [
            ("dod_5220", "DoD 5220.22-M"),
            ("nist_800_88", "NIST 800-88"),
            ("custom", "Custom"),
        ],
        default="nist_800_88",
    )

    # ============================================================================
    # MISSING FIELDS FROM SMART GAP ANALYSIS - SHREDDING HARD DRIVE ENHANCEMENT
    # ============================================================================

    # Certificate and Compliance Tracking
    included_in_certificate = fields.Boolean(
        string="Included in Certificate",
        default=True,
        tracking=True,
        help="Whether this hard drive is included in the destruction certificate",
    )

    # Customer Scanning Tracking
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

    # Hardware Identification
    serial_number = fields.Char(
        string="Serial Number",
        tracking=True,
        help="Hardware serial number of the hard drive",
    )

    # Asset and Model Information
    asset_tag = fields.Char(
        string="Asset Tag", tracking=True, help="Customer asset tag or identifier"
    )

    make_model = fields.Char(
        string="Make/Model",
        tracking=True,
        help="Manufacturer and model of the hard drive",
    )

    # Capacity and Technical Details
    capacity_gb = fields.Float(
        string="Capacity (GB)", digits=(10, 2), help="Storage capacity in gigabytes"
    )

    # Physical Condition Assessment
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
    )

    # Service and Processing
    service_request_id = fields.Many2one(
        "shredding.service",
        string="Service Request",
        tracking=True,
        help="Related shredding service request",
    )

    def action_confirm(self):
        """Confirm the record"""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark as done"""
        self.write({"state": "done"})
