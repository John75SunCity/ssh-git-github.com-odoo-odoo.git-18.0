# -*- coding: utf-8 -*-
"""
HR Employee NAID Compliance Extension Module

This module extends HR Employee functionality with NAID (National Association for 
Information Destruction) compliance features, security clearance tracking, and 
records management access controls for the Records Management System.
"""

from odoo import models, fields, _
import datetime


class HREmployeeNAID(models.Model):
    """
    HR Employee NAID Compliance Extension
    
    Extends hr.employee with NAID security clearance levels, records management
    access permissions, and compliance tracking for document destruction services.
    """

    _name = "hr.employee.naid"
    _description = "HR Employee NAID Compliance Extension"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    
    name = fields.Char(
        string="Employee NAID Profile", 
        required=True, 
        tracking=True,
        help="NAID compliance profile name for this employee"
    ),
    company_id = fields.Many2one(
        'res.company', 
        string="Company",
        default=lambda self: self.env.company,
        required=True
    ),
    user_id = fields.Many2one(
        'res.users', 
        string="User",
        default=lambda self: self.env.user,
        tracking=True
    ),
    active = fields.Boolean(
        string="Active", 
        default=True,
        help="Uncheck to archive this NAID profile"
    ),

    # ============================================================================
    # EMPLOYEE RELATIONSHIP
    # ============================================================================
    
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        required=True,
        ondelete='cascade',
        tracking=True,
        help="Related HR employee record"
    ),

    # ============================================================================
    # NAID COMPLIANCE FIELDS
    # ============================================================================
    
    naid_security_clearance = fields.Selection([
        ('none', 'No Clearance'),
        ('basic', 'Basic Security'),
        ('advanced', 'Advanced Security'),
        ('certified', 'NAID Certified'),
        ('aaa_certified', 'NAID AAA Certified')
    ], string="NAID Security Clearance", 
       default='none', 
       tracking=True,
       help="Current NAID security clearance level"),

    clearance_date = fields.Date(
        string="Clearance Date",
        tracking=True,
        help="Date when security clearance was granted"
    ),
    clearance_expiry = fields.Date(
        string="Clearance Expiry",
        tracking=True,
        help="Date when security clearance expires"
    ),
    background_check_completed = fields.Boolean(
        string="Background Check Completed",
        default=False,
        tracking=True,
        help="Background screening completed for NAID compliance"
    ),
    training_completed = fields.Boolean(
        string="NAID Training Completed",
        default=False,
        tracking=True,
        help="Required NAID training completed"
    ),

    # ============================================================================
    # RECORDS ACCESS MANAGEMENT
    # ============================================================================
    
    records_access_level = fields.Selection([
        ('none', 'No Access'),
        ('read', 'Read Only'),
        ('write', 'Read/Write'),
        ('admin', 'Administrator'),
        ('compliance', 'Compliance Officer')
    ], string="Records Access Level",
       default='none',
       tracking=True,
       help="Access level for records management system"),

    records_department_ids = fields.Many2many(
        'records.department',
        string="Authorized Departments",
        help="Departments this employee can access"
    ),
    can_witness_destruction = fields.Boolean(
        string="Can Witness Destruction",
        default=False,
        tracking=True,
        help="Authorized to witness document destruction"
    ),
    can_transport_documents = fields.Boolean(
        string="Can Transport Documents",
        default=False,
        tracking=True,
        help="Authorized to transport secure documents"
    ),

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('active', 'Active'),
        ('suspended', 'Suspended'),
        ('expired', 'Expired')
    ], string='Status', 
       default='draft', 
       tracking=True,
       help="Current status of NAID compliance profile"),

    # ============================================================================
    # DOCUMENTATION FIELDS
    # ============================================================================
    
    description = fields.Text(
        string="Description",
        help="Additional details about employee's NAID profile"
    ),
    notes = fields.Text(
        string="Internal Notes",
        help="Internal notes and observations"
    ),
    compliance_notes = fields.Text(
        string="Compliance Notes",
        help="Notes related to NAID compliance and certifications"
    ),

    # ============================================================================
    # DATES & TRACKING
    # ============================================================================
    
    profile_date = fields.Date(
        string="Profile Date",
        default=fields.Date.today,
        required=True,
        help="Date when NAID profile was created"
    ),
    last_review_date = fields.Date(
        string="Last Review Date",
        tracking=True,
        help="Date of last compliance review"
    ),
    next_review_date = fields.Date(
        string="Next Review Date",
        tracking=True,
        help="Date when next compliance review is due"
    ),

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    
    activity_ids = fields.One2many(
        "mail.activity", 
        "res_id", 
        string="Activities",
        auto_join=True,
        groups="base.group_user"
    )
    message_follower_ids = fields.One2many(
        "mail.followers", 
        "res_id", 
        string="Followers", 
        groups="base.group_user"
    )
    message_ids = fields.One2many(
        "mail.message", 
        "res_id", 
        string="Messages", 
        groups="base.group_user"
    ),

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    
    def action_submit_for_approval(self):
        """Submit NAID profile for approval"""
        self.ensure_one()
        if self.state != 'draft':
            return
        self.write({'state': 'pending_approval'})
        self.message_post(body="NAID profile submitted for approval")

    def action_approve_profile(self):
        """Approve NAID compliance profile"""
        self.ensure_one()
        if self.state != 'pending_approval':
            return
        self.write({
            'state': 'active',
            'last_review_date': fields.Date.today()
        })
        self.message_post(body="NAID profile approved and activated")

    def action_suspend_profile(self):
        """Suspend NAID compliance profile"""
        self.ensure_one()
        if self.state not in ['active', 'pending_approval']:
            return
        self.write({'state': 'suspended'})
        self.message_post(body="NAID profile suspended - access revoked")

    def action_reactivate_profile(self):
        """Reactivate suspended NAID profile"""
        self.ensure_one()
        if self.state != 'suspended':
            return
        self.write({'state': 'active'})
        self.message_post(body="NAID profile reactivated")

    def action_expire_profile(self):
        """Mark NAID profile as expired"""
        self.ensure_one()
        self.write({'state': 'expired'})
        self.message_post(body="NAID profile expired - renewal required")

    def action_schedule_review(self):
        """Schedule next compliance review"""
        self.ensure_one()
        
        # Calculate next review date (typically annual)
        import datetime
        next_review = fields.Date.today() + datetime.timedelta(days=365)
        
        self.write({'next_review_date': next_review})
        
        # Create activity for review
        self.activity_schedule(
            'mail.mail_activity_data_todo',
            summary=f"NAID Compliance Review - {self.name}",
            note=f"Annual NAID compliance review for {self.employee_id.name}",
            user_id=self.user_id.id,
            date_deadline=next_review
        )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    
    def _compute_display_name(self):
        """Compute display name with employee context"""
        for record in self:
            if record.employee_id:
                record.display_name = f"NAID Profile - {record.employee_id.name}"
            else:
                record.display_name = record.name or "New NAID Profile"

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True
    )

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    
    def _check_clearance_dates(self):
        """Validate clearance date logic"""
        for record in self:
            if record.clearance_date and record.clearance_expiry:
                if record.clearance_date >= record.clearance_expiry:
                    from odoo.exceptions import ValidationError
                    raise ValidationError(
                        "Clearance date must be before expiry date"
                    )

    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================
    
    def create(self, vals_list):
        records = super().create(vals_list)
        
        for record in records:
            # Create initial activity for profile setup
            today_date = fields.Date.to_date(fields.Date.today())
            deadline_date = today_date + datetime.timedelta(days=7)
            record.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=f"Complete NAID Profile Setup - {record.name}",
                note="Complete NAID compliance profile setup and documentation",
                user_id=record.user_id.id,
                date_deadline=deadline_date
            )
            
            record.message_post(
                body=_(
                    "NAID compliance profile created for %s",
                    record.employee_id.name if record.employee_id else 'employee'
                )
            )
        
        return records

    def write(self, vals):
        """Override write to track important changes"""
        # Track clearance level changes
        if 'naid_security_clearance' in vals:
            for record in self:
                old_level = record.naid_security_clearance
                new_level = vals['naid_security_clearance']
                if old_level != new_level:
                    record.message_post(
                        body=_("NAID security clearance changed from %s to %s", old_level, new_level)
                    )
        
        # Track access level changes  
        if 'records_access_level' in vals:
            for record in self:
                old_access = record.records_access_level
                new_access = vals['records_access_level']
                if old_access != new_access:
                    record.message_post(
                        body=_("Records access level changed from %s to %s", old_access, new_access)
                    )
        
        return super().write(vals)