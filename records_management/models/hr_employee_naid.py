# -*- coding: utf-8 -*-
"""
HR Employee Extensions for NAID AAA Compliance
Adds background check and security clearance tracking
"""

from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class HREmployeeNAID(models.Model):
    """
    Extends hr.employee with NAID AAA compliance fields
    """
    _inherit = 'hr.employee'

    # NAID Background Check Fields
    background_check_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
        ('renewal_required', 'Renewal Required')
    ], string='Background Check Status', default='pending', tracking=True)
    
    background_check_date = fields.Date(
        string='Background Check Date',
        help='Date when background check was completed'
    )
    
    background_check_expiry = fields.Date(
        string='Background Check Expiry',
        help='Date when background check expires'
    )
    
    background_check_provider = fields.Char(
        string='Background Check Provider',
        help='Company that performed the background check'
    )
    
    background_check_reference = fields.Char(
        string='Background Check Reference',
        help='Reference number from background check provider'
    )
    
    # Security Clearance
    security_clearance_level = fields.Selection([
        ('none', 'No Clearance'),
        ('basic', 'Basic Access'),
        ('confidential', 'Confidential Access'),
        ('secret', 'Secret Access'),
        ('top_secret', 'Top Secret Access')
    ], string='Security Clearance Level', default='none', tracking=True)
    
    security_clearance_date = fields.Date(
        string='Security Clearance Date'
    )
    
    security_clearance_expiry = fields.Date(
        string='Security Clearance Expiry'
    )
    
    # NAID Specific Training
    naid_training_completed = fields.Boolean(
        string='NAID Training Completed',
        default=False,
        tracking=True
    )
    
    naid_training_date = fields.Date(
        string='NAID Training Date'
    )
    
    naid_training_expiry = fields.Date(
        string='NAID Training Expiry'
    )
    
    naid_certification_number = fields.Char(
        string='NAID Certification Number'
    )
    
    # Access Control
    facility_access_level = fields.Selection([
        ('none', 'No Access'),
        ('reception', 'Reception Only'),
        ('warehouse', 'Warehouse Access'),
        ('destruction', 'Destruction Area'),
        ('full', 'Full Facility Access')
    ], string='Facility Access Level', default='none', tracking=True)
    
    access_card_number = fields.Char(
        string='Access Card Number',
        help='Physical access card or key fob number'
    )
    
    access_card_issued_date = fields.Date(
        string='Access Card Issued Date'
    )
    
    access_card_active = fields.Boolean(
        string='Access Card Active',
        default=False,
        tracking=True
    )
    
    # Emergency Contacts (Enhanced)
    emergency_contact_verified = fields.Boolean(
        string='Emergency Contact Verified',
        default=False,
        help='Whether emergency contacts have been verified'
    )
    
    emergency_contact_verification_date = fields.Date(
        string='Emergency Contact Verification Date'
    )
    
    # Compliance Status
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('pending_documentation', 'Pending Documentation'),
        ('training_required', 'Training Required'),
        ('background_check_required', 'Background Check Required'),
        ('non_compliant', 'Non-Compliant'),
        ('suspended', 'Suspended')
    ], string='NAID Compliance Status', compute='_compute_compliance_status', store=True)
    
    compliance_notes = fields.Text(
        string='Compliance Notes',
        help='Notes about compliance status and requirements'
    )
    
    # Audit Trail
    last_compliance_review = fields.Date(
        string='Last Compliance Review'
    )
    
    next_compliance_review = fields.Date(
        string='Next Compliance Review',
        compute='_compute_next_compliance_review',
        store=True
    )
    
    # Related Records
    audit_log_ids = fields.One2many(
        'naid.audit.log',
        'employee_id',
        string='Audit Logs',
        readonly=True
    )
    
    witness_audit_log_ids = fields.Many2many(
        'naid.audit.log',
        'naid_audit_witness_rel',
        'employee_id',
        'audit_id',
        string='Witnessed Events',
        readonly=True
    )
    
    # Computed Fields
    background_check_expires_soon = fields.Boolean(
        string='Background Check Expires Soon',
        compute='_compute_expiry_warnings',
        store=True
    )
    
    training_expires_soon = fields.Boolean(
        string='Training Expires Soon',
        compute='_compute_expiry_warnings',
        store=True
    )
    
    clearance_expires_soon = fields.Boolean(
        string='Clearance Expires Soon',
        compute='_compute_expiry_warnings',
        store=True
    )

    @api.depends(
        'background_check_status', 'background_check_expiry',
        'naid_training_completed', 'naid_training_expiry',
        'security_clearance_level', 'security_clearance_expiry',
        'access_card_active'
    )
    def _compute_compliance_status(self):
        """Compute overall NAID compliance status"""
        today = fields.Date.today()
        
        for employee in self:
            status = 'compliant'
            
            # Check background check
            if employee.background_check_status not in ['approved']:
                status = 'background_check_required'
            elif employee.background_check_expiry and employee.background_check_expiry <= today:
                status = 'background_check_required'
            
            # Check training
            elif not employee.naid_training_completed:
                status = 'training_required'
            elif employee.naid_training_expiry and employee.naid_training_expiry <= today:
                status = 'training_required'
            
            # Check security clearance
            elif employee.security_clearance_level == 'none':
                status = 'pending_documentation'
            elif employee.security_clearance_expiry and employee.security_clearance_expiry <= today:
                status = 'pending_documentation'
            
            # Check access card
            elif not employee.access_card_active:
                status = 'pending_documentation'
            
            employee.compliance_status = status

    @api.depends('last_compliance_review')
    def _compute_next_compliance_review(self):
        """Compute next compliance review date (quarterly)"""
        for employee in self:
            if employee.last_compliance_review:
                employee.next_compliance_review = employee.last_compliance_review + timedelta(days=90)
            else:
                employee.next_compliance_review = fields.Date.today() + timedelta(days=30)

    @api.depends('background_check_expiry', 'naid_training_expiry', 'security_clearance_expiry')
    def _compute_expiry_warnings(self):
        """Compute expiry warning flags"""
        today = fields.Date.today()
        warning_days = 30  # Warn 30 days before expiry
        warning_date = today + timedelta(days=warning_days)
        
        for employee in self:
            # Background check expiry warning
            employee.background_check_expires_soon = (
                employee.background_check_expiry and
                employee.background_check_expiry <= warning_date
            )
            
            # Training expiry warning
            employee.training_expires_soon = (
                employee.naid_training_expiry and
                employee.naid_training_expiry <= warning_date
            )
            
            # Clearance expiry warning
            employee.clearance_expires_soon = (
                employee.security_clearance_expiry and
                employee.security_clearance_expiry <= warning_date
            )

    def action_request_background_check(self):
        """Initiate background check process"""
        self.write({
            'background_check_status': 'in_progress'
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'employee_screening',
            f'Background check requested for employee {self.name}',
            employee_id=self.id,
            risk_level='medium'
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Background Check Request',
            'res_model': 'naid.background.check.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_employee_id': self.id}
        }

    def action_approve_background_check(self):
        """Approve background check"""
        today = fields.Date.today()
        expiry = today + timedelta(days=365)  # 1 year validity
        
        self.write({
            'background_check_status': 'approved',
            'background_check_date': today,
            'background_check_expiry': expiry
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'employee_screening',
            f'Background check approved for employee {self.name}',
            employee_id=self.id,
            risk_level='low',
            compliance_status='compliant'
        )

    def action_complete_naid_training(self):
        """Mark NAID training as completed"""
        today = fields.Date.today()
        expiry = today + timedelta(days=365)  # 1 year validity
        
        self.write({
            'naid_training_completed': True,
            'naid_training_date': today,
            'naid_training_expiry': expiry
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'employee_screening',
            f'NAID training completed for employee {self.name}',
            employee_id=self.id,
            risk_level='low',
            compliance_status='compliant'
        )

    def action_issue_access_card(self):
        """Issue access card to employee"""
        self.write({
            'access_card_active': True,
            'access_card_issued_date': fields.Date.today()
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'access',
            f'Access card issued to employee {self.name}',
            employee_id=self.id,
            risk_level='medium',
            compliance_status='compliant'
        )

    def action_revoke_access_card(self):
        """Revoke access card from employee"""
        self.write({
            'access_card_active': False
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'access',
            f'Access card revoked for employee {self.name}',
            employee_id=self.id,
            risk_level='high',
            compliance_status='compliant'
        )

    def action_conduct_compliance_review(self):
        """Conduct compliance review"""
        self.write({
            'last_compliance_review': fields.Date.today()
        })
        
        # Log the event
        self.env['naid.audit.log'].log_event(
            'audit_review',
            f'Compliance review conducted for employee {self.name}',
            employee_id=self.id,
            risk_level='low',
            compliance_status='compliant'
        )

    @api.model
    def check_expiring_credentials(self):
        """
        Cron job to check for expiring credentials and send notifications
        """
        today = fields.Date.today()
        warning_date = today + timedelta(days=30)
        
        # Find employees with expiring credentials
        expiring_employees = self.search([
            '|', '|', '|',
            ('background_check_expiry', '<=', warning_date),
            ('naid_training_expiry', '<=', warning_date),
            ('security_clearance_expiry', '<=', warning_date),
            ('compliance_status', 'in', ['training_required', 'background_check_required'])
        ])
        
        for employee in expiring_employees:
            # Create audit log for expiring credentials
            self.env['naid.audit.log'].log_event(
                'employee_screening',
                f'Credentials expiring soon for employee {employee.name}',
                employee_id=employee.id,
                risk_level='medium',
                compliance_status='warning',
                remediation_required=True,
                remediation_deadline=fields.Datetime.now() + timedelta(days=30)
            )
        
        return len(expiring_employees)
