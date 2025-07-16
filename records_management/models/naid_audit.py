# -*- coding: utf-8 -*-
"""
NAID AAA Compliance Audit Model
Tracks all security-relevant events and maintains compliance audit trail
"""

from odoo import models, fields, api
from datetime import timedelta
import logging

_logger = logging.getLogger(__name__)


class NAIDAuditLog(models.Model):
    """
    NAID AAA Compliance Audit Log
    Maintains comprehensive audit trail for compliance certification
    """
    _name = 'naid.audit.log'
    _description = 'NAID AAA Compliance Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'event_type'

    # Core audit fields
    timestamp = fields.Datetime(
        string='Event Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    event_type = fields.Selection([
        ('access', 'Facility Access'),
        ('document_intake', 'Document Intake'),
        ('storage_assignment', 'Storage Assignment'),
        ('destruction_start', 'Destruction Process Start'),
        ('destruction_complete', 'Destruction Complete'),
        ('certificate_generated', 'Certificate Generated'),
        ('employee_screening', 'Employee Background Check'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('security_breach', 'Security Incident'),
        ('policy_violation', 'Policy Violation'),
        ('audit_review', 'Audit Review')
    ], string='Event Type', required=True, index=True)
    
    # Related records
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        help='Employee responsible for or involved in the event'
    )
    
    document_id = fields.Many2one(
        'records.document',
        string='Document',
        help='Related document if applicable'
    )
    
    box_id = fields.Many2one(
        'records.box',
        string='Records Box',
        help='Related box if applicable'
    )
    
    bale_id = fields.Many2one(
        'records_management.bale',
        string='Bale',
        help='Related bale if applicable'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Related customer if applicable'
    )
    
    # Audit details
    description = fields.Text(
        string='Event Description',
        required=True,
        help='Detailed description of the event'
    )
    
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ], string='Risk Level', default='low', required=True)
    
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('violation', 'Violation'),
        ('critical', 'Critical Violation')
    ], string='Compliance Status', default='compliant', required=True)
    
    # Technical details
    ip_address = fields.Char(
        string='IP Address',
        help='IP address of the user/system generating the event'
    )
    
    user_agent = fields.Text(
        string='User Agent',
        help='Browser/system information'
    )
    
    session_id = fields.Char(
        string='Session ID',
        help='User session identifier'
    )
    
    # Evidence and documentation
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Evidence Attachments',
        help='Supporting documentation, photos, or evidence'
    )
    
    # Chain of custody
    custody_chain = fields.Text(
        string='Chain of Custody',
        help='Complete chain of custody information'
    )
    
    witness_employee_ids = fields.Many2many(
        'hr.employee',
        'naid_audit_witness_rel',
        'audit_id',
        'employee_id',
        string='Witnesses',
        help='Employees who witnessed this event'
    )
    
    # Compliance tracking
    remediation_required = fields.Boolean(
        string='Remediation Required',
        default=False
    )
    
    remediation_description = fields.Text(
        string='Remediation Description',
        help='Description of required remediation actions'
    )
    
    remediation_deadline = fields.Datetime(
        string='Remediation Deadline'
    )
    
    remediation_completed = fields.Boolean(
        string='Remediation Completed',
        default=False
    )
    
    remediation_completed_date = fields.Datetime(
        string='Remediation Completed Date'
    )
    
    # Review and approval
    reviewed_by = fields.Many2one(
        'hr.employee',
        string='Reviewed By',
        help='Security officer who reviewed this event'
    )
    
    review_date = fields.Datetime(
        string='Review Date'
    )
    
    review_notes = fields.Text(
        string='Review Notes'
    )
    
    # Computed fields
    days_since_event = fields.Integer(
        string='Days Since Event',
        compute='_compute_days_since_event',
        store=True
    )
    
    is_overdue = fields.Boolean(
        string='Remediation Overdue',
        compute='_compute_is_overdue',
        store=True
    )

    @api.depends('timestamp')
    def _compute_days_since_event(self):
        """Calculate days since the event occurred"""
        now = fields.Datetime.now()
        for record in self:
            if record.timestamp:
                delta = now - record.timestamp
                record.days_since_event = delta.days
            else:
                record.days_since_event = 0

    @api.depends('remediation_deadline', 'remediation_completed')
    def _compute_is_overdue(self):
        """Check if remediation is overdue"""
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = (
                record.remediation_required and
                not record.remediation_completed and
                record.remediation_deadline and
                record.remediation_deadline < now
            )

    @api.model
    def log_event(self, event_type, description, **kwargs):
        """
        Utility method to log audit events from other modules
        
        Args:
            event_type: Type of event to log
            description: Description of the event
            **kwargs: Additional field values
        
        Returns:
            Created audit log record
        """
        vals = {
            'event_type': event_type,
            'description': description,
            'ip_address': self.env.context.get('ip_address'),
            'session_id': self.env.context.get('session_id'),
        }
        vals.update(kwargs)
        
        return self.create(vals)

    def action_mark_reviewed(self):
        """Mark the audit log as reviewed"""
        self.write({
            'reviewed_by': self.env.user.employee_id.id,
            'review_date': fields.Datetime.now()
        })

    def action_complete_remediation(self):
        """Mark remediation as completed"""
        self.write({
            'remediation_completed': True,
            'remediation_completed_date': fields.Datetime.now()
        })

    @api.model
    def cleanup_old_logs(self, days=2555):  # 7 years default
        """
        Clean up old audit logs beyond retention period
        NAID AAA requires 7-year retention minimum
        """
        cutoff_date = fields.Datetime.now() - timedelta(days=days)
        old_logs = self.search([('timestamp', '<', cutoff_date)])
        
        if old_logs:
            _logger.info("Archiving %d old audit logs", len(old_logs))
            # Archive instead of delete for compliance
            old_logs.write({'active': False})
        
        return len(old_logs)


class NAIDCompliancePolicy(models.Model):
    """
    NAID AAA Compliance Policies and Procedures
    Defines compliance requirements and automated checks
    """
    _name = 'naid.compliance.policy'
    _description = 'NAID Compliance Policy'
    _order = 'sequence, name'

    name = fields.Char(
        string='Policy Name',
        required=True
    )
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    )
    
    description = fields.Text(
        string='Policy Description',
        required=True
    )
    
    policy_type = fields.Selection([
        ('access_control', 'Access Control'),
        ('document_handling', 'Document Handling'),
        ('destruction_process', 'Destruction Process'),
        ('employee_screening', 'Employee Screening'),
        ('facility_security', 'Facility Security'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('audit_requirements', 'Audit Requirements')
    ], string='Policy Type', required=True)
    
    active = fields.Boolean(
        string='Active',
        default=True
    )
    
    # Compliance requirements
    mandatory = fields.Boolean(
        string='Mandatory',
        default=True,
        help='Whether this policy is mandatory for NAID compliance'
    )
    
    automated_check = fields.Boolean(
        string='Automated Check',
        default=False,
        help='Whether compliance with this policy can be automatically verified'
    )
    
    check_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Check Frequency')
    
    # Implementation details
    implementation_notes = fields.Text(
        string='Implementation Notes',
        help='How to implement this policy'
    )
    
    violation_consequences = fields.Text(
        string='Violation Consequences',
        help='What happens when this policy is violated'
    )
    
    # Related records
    responsible_employee_ids = fields.Many2many(
        'hr.employee',
        string='Responsible Employees',
        help='Employees responsible for ensuring compliance with this policy'
    )
    
    # Tracking
    last_review_date = fields.Date(
        string='Last Review Date'
    )
    
    next_review_date = fields.Date(
        string='Next Review Date'
    )
    
    review_frequency_months = fields.Integer(
        string='Review Frequency (Months)',
        default=12
    )

    @api.model
    def check_compliance(self):
        """
        Run automated compliance checks for all applicable policies
        """
        policies = self.search([('automated_check', '=', True)])
        results = []
        
        for policy in policies:
            # This would be extended with specific compliance checks
            # based on the policy type
            result = self._run_policy_check(policy)
            results.append(result)
        
        return results

    def _run_policy_check(self, policy):
        """
        Run a specific policy compliance check
        Override in modules that implement specific checks
        """
        return {
            'policy_id': policy.id,
            'status': 'not_implemented',
            'message': 'Automated check not implemented for this policy'
        }
