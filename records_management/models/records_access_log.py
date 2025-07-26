from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsAccessLog(models.Model):
    _name = 'records.access.log'
    _description = 'Records Access Log'
    _order = 'access_timestamp desc'

    document_id = fields.Many2one('records.document', string='Document', ondelete='cascade')
    task_id = fields.Many2one('project.task', string='FSM Task', help='Related FSM task if applicable')
    access_timestamp = fields.Datetime('Access Time', required=True, default=fields.Datetime.now)
    user_id = fields.Many2one('res.users', string='User', required=True, default=lambda self: self.env.user)
    
    access_type = fields.Selection([
        ('view', 'View'),
        ('download', 'Download'),
        ('print', 'Print'),
        ('edit', 'Edit'),
        ('share', 'Share'),
        ('copy', 'Copy'),
        ('export', 'Export')
    
    ip_address = fields.Char('IP Address')
    user_agent = fields.Text('User Agent')
    session_id = fields.Char('Session ID')
    
    # Access context
    access_reason = fields.Text('Access Reason')
    department_id = fields.Many2one('records.department', string='Department')
    location_id = fields.Many2one('records.location', string='Access Location')
    
    # Security information
    authentication_method = fields.Selection([
        ('password', 'Password'),
        ('two_factor', 'Two Factor Authentication'),
        ('certificate', 'Digital Certificate'),
        ('biometric', 'Biometric'),
        ('token', 'Security Token')
    
    security_level = fields.Selection([
        ('low', 'Low Security'),
        ('medium', 'Medium Security'),
        ('high', 'High Security'),
        ('critical', 'Critical Security')
    
    # Additional tracking
    duration_seconds = fields.Integer('Access Duration (seconds)')
    actions_performed = fields.Text('Actions Performed')
    files_accessed = fields.Text('Files Accessed')
    
    # Compliance flags
    authorized_access = fields.Boolean('Authorized Access', default=True)
    compliance_reviewed = fields.Boolean('Compliance Reviewed', default=False)
    flagged_for_review = fields.Boolean('Flagged for Review', default=False)
    
    # Analytics
    risk_score = fields.Float('Risk Score', compute='_compute_risk_score', store=True)
    
    @api.depends('access_type', 'security_level', 'authorized_access', 'user_id')
    def _compute_risk_score(self):
        """Compute access risk score"""
        for log in self:
            base_score = 30
            
            # Access type risk
            type_risk = {
                'view': 10,
                'download': 25,
                'print': 30,
                'edit': 50,
                'share': 60,
                'copy': 55,
                'export': 65
            }
            base_score += type_risk.get(log.access_type, 20)
            
            # Security level adjustment
            security_multiplier = {
                'low': 0.8,
                'medium': 1.0,
                'high': 1.3,
                'critical': 1.6
            }
            base_score *= security_multiplier.get(log.security_level, 1.0)
            
            # Authorization check
            if not log.authorized_access:
                base_score += 40
            
            log.risk_score = min(max(base_score, 0), 100)
    
    def action_flag_for_review(self):
        """Flag this access for compliance review"""
        self.write({
            'flagged_for_review': True,
            'compliance_reviewed': False
        })
    
    def action_mark_reviewed(self):
        """Mark this access as compliance reviewed"""
        self.write({
            'compliance_reviewed': True,
            'flagged_for_review': False
        })
