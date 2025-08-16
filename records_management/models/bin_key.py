# -*- coding: utf-8 -*-
"""
Bin Access Key Management Module

This module provides comprehensive management of physical access keys used    #     # ============================================================================
    # OWNERSHIP & ASSIGNMENT
    # ============================================================================
    # 'assigned_to_id' refers to the partner (department, company, or external entity) responsible for the key.
    assigned_to_id = fields.Many2one("res.partner", string="Assigned To")
    # 'current_holder_id' refers to the internal user (employee) who currently possesses the key.
    current_holder_id = fields.Many2one("res.users", string="Current Holder")=====================================================================
    # OWNERSHIP & ASSIGNMENT
    # ============================================================================
    # 'assigned_to_id' refers to the partner (department, company, or external entity) responsible for the key.
    assigned_to_id = fields.Many2one("res.partner", string="Assigned To")
    # 'current_holder_id' refers to the internal user (employee) who currently possesses the key.
    current_holder_id = fields.Many2one("res.users", string="Current Holder")cure containers,
bins, and storage locations within the Records Management System. It implements complete key
lifecycle management with security tracking, access control, and audit trail maintenance.

Key Features:
- Complete key lifecycle management from issuance to retirement
- Security classification and access level management for keys
- Key assignment tracking with employee and location relationships
- Lost key reporting and replacement workflow management
- Key audit trails with comprehensive security logging
- Integration with container and location security systems
- Master key and duplicate key management with hierarchy tracking

Business Processes:
1. Key Issuance: New key creation and assignment to authorized personnel
2. Access Management: Key permissions and security level assignment
3. Location Assignment: Key association with specific containers and locations
4. Usage Tracking: Complete audit trail of key usage and access events
5. Lost Key Handling: Reporting, deactivation, and replacement procedures
6. Key Retirement: Secure key decommissioning and destruction processes
7. Security Auditing: Regular key inventory and access permission reviews

Key Types:
- Master Keys: High-security keys with access to multiple containers
- Container Keys: Individual container and bin access keys
- Location Keys: Area and facility access keys
- Emergency Keys: Emergency access keys with special protocols
- Temporary Keys: Limited-time access keys for contractors and visitors

Security Features:
- Multi-level security classification with clearance requirements
- Key duplication tracking and authorization controls
- Lost key immediate deactivation with security notifications
- Access attempt logging and unauthorized usage alerts
- Integration with NAID AAA compliance and audit requirements
- Encrypted key information storage with tamper detection

Integration Points:
- Container Management: Direct integration with container security systems
- Location Tracking: Key association with storage locations and access points
- Employee Management: Key assignment to authorized personnel with security clearance
- Audit System: Complete integration with NAID compliance and audit trail systems
- Security Monitoring: Real-time alerts for unauthorized access attempts

Technical Implementation:
- Modern Odoo 18.0 patterns with comprehensive security frameworks
- Mail thread integration for activity tracking and notifications
- Secure data storage with encryption for sensitive key information
- Performance optimized key lookup and validation systems
- Integration with Records Management security and access control

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields




class BinKey(models.Model):
    _name = "bin.key"
    _description = "Bin Access Key"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Key Number", required=True, tracking=True, index=True)
    company_id = fields.Many2one(
        "res.company", default=lambda self: self.env.company, required=True
    )
    user_id = fields.Many2one(
        "res.users", default=lambda self: self.env.user, tracking=True
    )
    active = fields.Boolean(string="Active", default=True)

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        help="Associated partner for this record"
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("active", "Active"),
            ("lost", "Lost"),
            ("damaged", "Damaged"),
            ("retired", "Retired"),
        ],
        default="draft",
        tracking=True,
    )

    # ============================================================================
    # KEY SPECIFICATIONS
    # ============================================================================
    key_code = fields.Char(string="Key Code", index=True, tracking=True)
    description = fields.Text(
        string="Description",
        help="Provide detailed information about the key, such as physical characteristics, security features, or any special handling instructions.",
    )
    key_type = fields.Selection(
        [
            ("physical", "Physical Key"),
            ("electronic", "Electronic Key"),
            ("master", "Master Key"),
            ("backup", "Backup Key"),
        ],
        string="Key Type",
        default="physical",
    )

    # ============================================================================
    # ACCESS CONTROL
    # ============================================================================
    access_level = fields.Selection(
        [
            ("basic", "Basic Access"),
            ("supervisor", "Supervisor Access"),
            ("manager", "Manager Access"),
            ("admin", "Admin Access"),
        ],
        string="Access Level",
        default="basic",
    )

    valid_from = fields.Date(
        string="Valid From", default=lambda self: fields.Date.today()
    )
    valid_to = fields.Date(string="Valid To")

    # ============================================================================
    # OWNERSHIP & ASSIGNMENT
    # ============================================================================
    # 'assigned_to' refers to the partner (department, company, or external entity) responsible for the key.
    assigned_to_id = fields.Many2one("res.partner", string="Assigned To")
    # 'current_holder' refers to the internal user (employee) who currently possesses the key.
    current_holder_id = fields.Many2one("res.users", string="Current Holder")

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    unlock_service_ids = fields.One2many(
        "bin.unlock.service", "key_id", string="Unlock Services"
    )
    bin_ids = fields.Many2many("shred.bin", string="Accessible Shred Bins")

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many(
        "mail.followers", "res_id", string="Followers"
    )
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
    key_number = fields.Char(string="Key Number", required=True, index=True)
    bin_location = fields.Char(string="Bin Location")
    assigned_to = fields.Many2one("res.partner", string="Assigned To")
    issue_date = fields.Date(string="Issue Date")
    return_date = fields.Date(string="Return Date")
    security_deposit_required = fields.Boolean(string="Security Deposit Required", default=False)
    security_deposit_amount = fields.Monetary(string="Security Deposit Amount", currency_field="currency_id")
    emergency_access = fields.Boolean(string="Emergency Access", default=False)
    last_maintenance_date = fields.Date(string="Last Maintenance Date")
    next_maintenance_due = fields.Date(string="Next Maintenance Due")
