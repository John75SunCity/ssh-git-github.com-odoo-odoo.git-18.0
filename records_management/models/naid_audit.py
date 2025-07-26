# -*- coding: utf-8 -*-
"""
NAID AAA Compliance Audit Model
Tracks all security-relevant events and maintains compliance audit trail
"""

from odoo import models, fields, api, _
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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'timestamp desc'
    _rec_name = 'event_type'

    # Core audit fields
    timestamp = fields.Datetime(
        string='Event Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True
    
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
    
    # Related records
    employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        help='Employee responsible for or involved in the event'
    
    document_id = fields.Many2one(
        'records.document',
        string='Document',
        help='Related document if applicable'
    
    box_id = fields.Many2one(
        'records.box',
        string='Records Box',
        help='Related box if applicable'
    
    bale_id = fields.Many2one(
        'paper.bale',
        string='Bale',
        help='Related bale if applicable'
    
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Related customer if applicable'
    
    # Audit details
    description = fields.Text(
        string='Event Description',
        required=True,
        help='Detailed description of the event'
    
    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('warning', 'Warning'),
        ('violation', 'Violation'),
        ('critical', 'Critical Violation')
    
    # Technical details
    ip_address = fields.Char(
        string='IP Address',
        help='IP address of the user/system generating the event'
    
    user_agent = fields.Text(
        string='User Agent',
        help='Browser/system information'
    
    session_id = fields.Char(
        string='Session ID',
        help='User session identifier'
    
    # Evidence and documentation
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Evidence Attachments',
        help='Supporting documentation, photos, or evidence'
    
    # Chain of custody
    custody_chain = fields.Text(
        string='Chain of Custody',
        help='Complete chain of custody information'
    
    witness_employee_ids = fields.Many2many(
        'hr.employee',
        'naid_audit_witness_rel',
        'audit_id',
        'employee_id',
        string='Witnesses',
        help='Employees who witnessed this event'
    
    # Compliance tracking
    remediation_required = fields.Boolean(
        string='Remediation Required',
        default=False
    
    remediation_description = fields.Text(
        string='Remediation Description',
        help='Description of required remediation actions'
    
    remediation_deadline = fields.Datetime(
        string='Remediation Deadline'
    
    remediation_completed = fields.Boolean(
        string='Remediation Completed',
        default=False
    
    remediation_completed_date = fields.Datetime(
        string='Remediation Completed Date'
    
    # Review and approval
    reviewed_by = fields.Many2one(
        'hr.employee',
        string='Reviewed By',
        help='Security officer who reviewed this event'
    
    review_date = fields.Datetime(
        string='Review Date'
    
    review_notes = fields.Text(
        string='Review Notes'
    
    # Computed fields
    days_since_event = fields.Integer(
        string='Days Since Event',
        compute='_compute_days_since_event',
        store=True

    # Phase 3: Analytics & Computed Fields (8 fields)
    audit_criticality_score = fields.Float(
        string='Criticality Score (0-100)',
        compute='_compute_audit_analytics',
        store=True,
        help='Audit event criticality assessment score'
    compliance_impact_rating = fields.Float(
        string='Compliance Impact Rating',
        compute='_compute_audit_analytics',
        store=True,
        help='Impact rating on overall compliance posture'
    remediation_urgency = fields.Float(
        string='Remediation Urgency (0-10)',
        compute='_compute_audit_analytics',
        store=True,
        help='Urgency level for required remediation'
    risk_exposure_level = fields.Float(
        string='Risk Exposure Level',
        compute='_compute_audit_analytics',
        store=True,
        help='Calculated risk exposure from this event'
    audit_trend_indicator = fields.Char(
        string='Trend Indicator',
        compute='_compute_audit_analytics',
        store=True,
        help='Trend analysis indicator'
    compliance_recovery_time = fields.Float(
        string='Recovery Time (Days)',
        compute='_compute_audit_analytics',
        store=True,
        help='Estimated time to resolve compliance issues'
    audit_insights = fields.Text(
        string='Audit Insights',
        compute='_compute_audit_analytics',
        store=True,
        help='AI-generated insights and recommendations'
    analytics_timestamp = fields.Datetime(
        string='Analytics Updated',
        compute='_compute_audit_analytics',
        store=True,
        help='Last analytics computation timestamp'
    
    is_overdue = fields.Boolean(
        string='Remediation Overdue',
        compute='_compute_is_overdue',
        store=True

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
        for record in self:
            record.is_overdue = (
                record.remediation_required and
                not record.remediation_completed and
                record.remediation_deadline and
                record.remediation_deadline < now

    @api.depends('event_type', 'risk_level', 'compliance_status', 'days_since_event',
                 'remediation_required', 'remediation_completed', 'witness_employee_ids')
    def _compute_audit_analytics(self):
        """Compute comprehensive analytics for audit events"""
        for audit in self:
            # Update timestamp
            
            # Audit criticality score
            criticality = 20.0  # Base score
            
            # Event type impact
            event_criticality = {
                'security_breach': 40.0,
                'policy_violation': 30.0,
                'destruction_complete': 15.0,
                'destruction_start': 10.0,
                'document_intake': 5.0,
                'access': 5.0,
                'storage_assignment': 3.0,
                'equipment_maintenance': 5.0,
                'employee_screening': 10.0,
                'certificate_generated': 2.0,
                'audit_review': 8.0
            }
            criticality += event_criticality.get(audit.event_type, 10.0)
            
            # Risk level impact
            risk_multipliers = {
                'low': 1.0,
                'medium': 1.5,
                'high': 2.0,
                'critical': 3.0
            }
            criticality *= risk_multipliers.get(audit.risk_level, 1.0)
            
            # Compliance status impact
            compliance_multipliers = {
                'compliant': 0.8,
                'warning': 1.2,
                'violation': 1.8,
                'critical': 2.5
            }
            criticality *= compliance_multipliers.get(audit.compliance_status, 1.0)
            
            audit.audit_criticality_score = min(100, criticality)
            
            # Compliance impact rating
            impact = 50.0  # Base impact
            
            if audit.compliance_status in ['violation', 'critical']:
                impact += 30.0
            elif audit.compliance_status == 'warning':
                impact += 15.0
            
            if audit.event_type in ['security_breach', 'policy_violation']:
                impact += 20.0
            
            audit.compliance_impact_rating = min(100, impact)
            
            # Remediation urgency
            urgency = 3.0  # Base urgency
            
            if audit.remediation_required:
                urgency += 3.0
                
                if audit.risk_level == 'critical':
                    urgency += 4.0
                elif audit.risk_level == 'high':
                    urgency += 2.0
                
                # Increase urgency if overdue
                if audit.is_overdue:
                    urgency += 2.0
            
            audit.remediation_urgency = min(10, urgency)
            
            # Risk exposure level
            exposure = 25.0  # Base exposure
            
            # Time factor - older unresolved issues increase exposure
            if audit.days_since_event > 30 and not audit.remediation_completed:
                exposure += (audit.days_since_event - 30) * 0.5
            
            # Event type exposure
            if audit.event_type == 'security_breach':
                exposure += 40.0
            elif audit.event_type == 'policy_violation':
                exposure += 25.0
            
            audit.risk_exposure_level = min(100, exposure)
            
            # Trend indicator
            recent_similar = self.search_count([
                ('event_type', '=', audit.event_type),
                ('timestamp', '>=', fields.Datetime.now() - timedelta(days=30)),
                ('id', '!=', audit.id)
            ])
            
            if recent_similar >= 5:
                audit.audit_trend_indicator = '📈 Increasing Frequency'
            elif recent_similar >= 2:
                audit.audit_trend_indicator = '⚠️ Pattern Detected'
            else:
                audit.audit_trend_indicator = '✅ Isolated Event'
            
            # Compliance recovery time
            if audit.remediation_required and not audit.remediation_completed:
                base_time = 7.0  # Base 7 days
                
                if audit.risk_level == 'critical':
                    base_time = 1.0  # 1 day for critical
                elif audit.risk_level == 'high':
                    base_time = 3.0  # 3 days for high
                elif audit.risk_level == 'medium':
                    base_time = 5.0  # 5 days for medium
                
                audit.compliance_recovery_time = base_time
            else:
                audit.compliance_recovery_time = 0.0
            
            # Audit insights
            insights = []
            
            if audit.audit_criticality_score > 80:
                insights.append("🚨 High criticality event requiring immediate attention")
            
            if audit.compliance_impact_rating > 75:
                insights.append("📋 Significant compliance impact - review procedures")
            
            if audit.remediation_urgency > 7:
                insights.append("⚡ Urgent remediation required")
            
            if audit.risk_exposure_level > 70:
                insights.append("🔒 High risk exposure - implement controls")
            
            if 'Increasing Frequency' in audit.audit_trend_indicator:
                insights.append("📊 Trending issue - root cause analysis needed")
            
            if audit.is_overdue:
                insights.append("⏰ Remediation overdue - escalate immediately")
            
            if len(audit.witness_employee_ids) > 0:
                insights.append("👥 Witnessed event - good documentation practices")
            
            if not insights:
                insights.append("✅ Standard audit event - routine monitoring")
            
            audit.audit_insights = "\n".join(insights)

    @api.depends('remediation_deadline', 'remediation_completed')
    def _compute_is_overdue(self):
        """Check if remediation is overdue"""
        for record in self:
            record.is_overdue = (
                record.remediation_required and
                not record.remediation_completed and
                record.remediation_deadline and
                record.remediation_deadline < now

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

    def action_start_audit(self):
        """Start NAID audit process"""
        self.ensure_one()
        return {
            'name': _('Start Audit'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.audit.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_audit_id': self.id},
        }

    def action_view_findings(self):
        """View audit findings"""
        self.ensure_one()
        return {
            'name': _('Audit Findings'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.audit.finding',
            'view_mode': 'tree,form',
            'domain': [('audit_id', '=', self.id)],
            'context': {'default_audit_id': self.id},
        }

    def action_generate_audit_report(self):
        """Generate audit report"""
        self.ensure_one()
        return {
            'name': _('Generate Report'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.naid_audit_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.naid_audit_report',
            'context': {'active_ids': [self.id]},
        }

    def action_create_remediation_plan(self):
        """Create remediation plan"""
        self.ensure_one()
        return {
            'name': _('Create Remediation Plan'),
            'type': 'ir.actions.act_window',
            'res_model': 'remediation.plan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_audit_id': self.id},
        }

    def action_schedule_followup(self):
        """Schedule follow-up audit"""
        self.ensure_one()
        return {
            'name': _('Schedule Follow-up'),
            'type': 'ir.actions.act_window',
            'res_model': 'audit.followup.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_parent_audit_id': self.id},
        }

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
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    name = fields.Char(
        string='Policy Name',
        required=True
    
    sequence = fields.Integer(
        string='Sequence',
        default=10
    
    
    policy_type = fields.Selection([
        ('access_control', 'Access Control'),
        ('document_handling', 'Document Handling'),
        ('destruction_process', 'Destruction Process'),
        ('employee_screening', 'Employee Screening'),
        ('facility_security', 'Facility Security'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('audit_requirements', 'Audit Requirements')
    
    active = fields.Boolean(
        string='Active',
        default=True
    
    # Compliance requirements
    mandatory = fields.Boolean(
        string='Mandatory',
        default=True,
        help='Whether this policy is mandatory for NAID compliance'
    
    automated_check = fields.Boolean(
        string='Automated Check',
        default=False,
        help='Whether compliance with this policy can be automatically verified'
    
    check_frequency = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    
    # Implementation details
    implementation_notes = fields.Text(
        string='Implementation Notes',
        help='How to implement this policy'
    
    violation_consequences = fields.Text(
        string='Violation Consequences',
        help='What happens when this policy is violated'
    
    # Related records
    responsible_employee_ids = fields.Many2many(
        'hr.employee',
        string='Responsible Employees',
        help='Employees responsible for ensuring compliance with this policy'
    
    # Tracking
    last_review_date = fields.Date(
        string='Last Review Date'
    
    next_review_date = fields.Date(
        string='Next Review Date'
    
    review_frequency_months = fields.Integer(
        string='Review Frequency (Months)',
        default=12

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
