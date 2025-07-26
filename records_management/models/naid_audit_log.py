# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class NAIDAuditLog(models.Model):
    """Model for NAID compliance audit logging."""
    _name = 'naid.audit.log'
    _description = 'NAID Audit Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'log_datetime desc'

    # Core fields
    name = fields.Char('Log Reference', required=True, default='/')
    description = fields.Text('Log Description')
    
    # Compliance relationship - CRITICAL for NAID compliance tracking
    compliance_id = fields.Many2one('naid.compliance', string='NAID Compliance Record',
                                    help='Associated NAID compliance record for this audit log entry')
    
    # Employee relationship
    employee_id = fields.Many2one('hr.employee', string='Employee', 
                                  help='Employee associated with this audit log entry')
    
    # Audit details
    audit_type = fields.Selection([
        ('access', 'Access Control'),
        ('security', 'Security Check'),
        ('compliance', 'Compliance Verification'),
        ('training', 'Training Record'),
        ('certification', 'Certification Update'),
        ('incident', 'Security Incident'),
        ('procedure', 'Procedure Execution'),
        ('system', 'System Activity'),
        ('manual', 'Manual Entry')
    
    log_datetime = fields.Datetime('Log Date/Time', required=True, 
                                  default=fields.Datetime.now, tracking=True)
    
    # NAID compliance categories
    naid_category = fields.Selection([
        ('physical_security', 'Physical Security'),
        ('personnel_security', 'Personnel Security'),
        ('information_security', 'Information Security'),
        ('chain_of_custody', 'Chain of Custody'),
        ('destruction_methods', 'Destruction Methods'),
        ('facility_operations', 'Facility Operations'),
        ('equipment_maintenance', 'Equipment Maintenance'),
        ('training_compliance', 'Training Compliance')
    
    # Severity and impact
    severity_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    
    impact_assessment = fields.Text('Impact Assessment')
    
    # Personnel involved
    responsible_user_id = fields.Many2one('res.users', string='Responsible User', 
                                         required=True, tracking=True)
    authorized_by = fields.Many2one('res.users', string='Authorized By')
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    
    # Location and context
    facility_location = fields.Many2one('records.location', string='Facility Location')
    work_area = fields.Char('Work Area/Zone')
    equipment_involved = fields.Char('Equipment Involved')
    
    # Compliance verification
    compliance_status = fields.Selection([
        ('compliant', 'Compliant'),
        ('minor_deviation', 'Minor Deviation'),
        ('major_deviation', 'Major Deviation'),
        ('non_compliant', 'Non-Compliant'),
        ('under_review', 'Under Review')
    
    # Corrective actions
    corrective_action_required = fields.Boolean('Corrective Action Required', default=False)
    corrective_action_description = fields.Text('Corrective Action Description')
    corrective_action_deadline = fields.Date('Corrective Action Deadline')
    corrective_action_completed = fields.Boolean('Corrective Action Completed', default=False)
    completion_date = fields.Date('Completion Date')
    
    # Documentation
    supporting_documents = fields.Text('Supporting Documents')
    external_references = fields.Text('External References')
    regulatory_requirements = fields.Text('Regulatory Requirements Met')
    
    # Follow-up tracking
    follow_up_required = fields.Boolean('Follow-up Required', default=False)
    follow_up_date = fields.Date('Follow-up Date')
    follow_up_completed = fields.Boolean('Follow-up Completed', default=False)
    
    # Risk assessment
    risk_level = fields.Selection([
        ('minimal', 'Minimal Risk'),
        ('low', 'Low Risk'),
        ('moderate', 'Moderate Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    
    risk_mitigation = fields.Text('Risk Mitigation Measures')
    
    # Status and workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('logged', 'Logged'),
        ('under_review', 'Under Review'),
        ('action_required', 'Action Required'),
        ('completed', 'Completed'),
        ('archived', 'Archived')
    
    # Audit trail
    created_by = fields.Many2one('res.users', string='Created By', 
                                default=lambda self: self.env.user, readonly=True)
    reviewed_date = fields.Datetime('Reviewed Date')
    archived_date = fields.Datetime('Archived Date')
    
    # Company context
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    active = fields.Boolean('Active', default=True)
    
    # Computed fields
    days_since_logged = fields.Integer('Days Since Logged', compute='_compute_days_since_logged')
    overdue_action = fields.Boolean('Overdue Action', compute='_compute_overdue_status')
    days_until_deadline = fields.Integer('Days Until Deadline', compute='_compute_days_until_deadline')
    
    @api.depends('log_datetime')
    def _compute_days_since_logged(self):
        """Compute days since the log entry was created"""
        for record in self:
            if record.log_datetime:
                delta = fields.Datetime.now() - record.log_datetime
                record.days_since_logged = delta.days
            else:
                record.days_since_logged = 0
    
    @api.depends('corrective_action_deadline', 'corrective_action_completed')
    def _compute_overdue_status(self):
        """Determine if corrective actions are overdue"""
        for record in self:
            if record.corrective_action_required and record.corrective_action_deadline:
                record.overdue_action = (
                    not record.corrective_action_completed and 
                    record.corrective_action_deadline < fields.Date.today()
            else:
                record.overdue_action = False
    
    @api.depends('corrective_action_deadline')
    def _compute_days_until_deadline(self):
        """Compute days until corrective action deadline"""
        for record in self:
            if record.corrective_action_deadline:
                delta = record.corrective_action_deadline - fields.Date.today()
                record.days_until_deadline = delta.days
            else:
                record.days_until_deadline = 0
    
    @api.model
    def create(self, vals):
        """Generate sequence for log reference"""
        if vals.get('name', '/') == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('naid.audit.log') or '/'
        return super().create(vals)
    
    @api.constrains('corrective_action_deadline', 'follow_up_date')
    def _check_dates(self):
        """Validate deadline dates"""
        for record in self:
            if record.corrective_action_deadline and record.corrective_action_deadline < fields.Date.today():
                if record.state == 'draft':
                    continue  # Allow past dates for draft records
            if record.follow_up_date and record.follow_up_date < fields.Date.today():
                if not record.follow_up_completed:
                    record.message_post(
                        body=_('Follow-up date has passed. Please update status.'),
                        message_type='notification'
    
    def action_log_entry(self):
        """Log the audit entry"""
        self.ensure_one()
        self.write({'state': 'logged'})
    
    def action_require_review(self):
        """Mark as requiring review"""
        self.ensure_one()
        self.write({'state': 'under_review'})
    
    def action_complete(self):
        """Mark audit log as completed"""
        self.ensure_one()
        vals = {'state': 'completed'}
        if self.corrective_action_required and not self.corrective_action_completed:
            vals['corrective_action_completed'] = True
            vals['completion_date'] = fields.Date.today()
        self.write(vals)
