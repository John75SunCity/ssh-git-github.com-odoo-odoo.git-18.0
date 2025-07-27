from odoo import models, fields, api
from datetime import datetime, timedelta

class RecordsPolicyVersion(models.Model):
    _name = 'records.policy.version'
    _description = 'Records Retention Policy Version History'
    _order = 'version_date desc'

    policy_id = fields.Many2one('records.retention.policy', string='Policy', required=True, ondelete='cascade')
    version_number = fields.Char('Version Number', required=True)
    version_date = fields.Datetime('Version Date', required=True, default=fields.Datetime.now)
    changes_summary = fields.Text('Changes Summary', required=True)
    changed_by = fields.Many2one('res.users', string='Changed By', required=True, default=lambda self: self.env.user)
    
    # Policy content fields
    retention_years = fields.Integer('Retention Years')
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('burning', 'Burning'),
        ('pulping', 'Pulping'),
        ('electronic_wipe', 'Electronic Data Wiping'),
        ('secure_disposal', 'Secure Disposal')
), string="Selection Field"
    review_cycle_months = fields.Integer('Review Cycle (Months)')
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
), string="Selection Field"
    approval_status = fields.Selection([
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('superseded', 'Superseded')
), string="Selection Field"
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime('Approval Date')
    
    # Computed fields
    is_current_version = fields.Boolean('Is Current Version', compute='_compute_is_current')
    
    @api.depends('policy_id.policy_version', 'version_number')
    def _compute_is_current(self):
        """Check if this is the current active version"""
        for version in self:
            if version.policy_id and version.policy_id.policy_version:
                version.is_current_version = (version.version_number == version.policy_id.policy_version)
            else:
                version.is_current_version = False
    
    def action_approve(self):
        """Approve this policy version"""
        self.write({
            'approval_status': 'approved',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now()
        }
        
        # Update the main policy to this version
        if self.policy_id:
            self.policy_id.write({
                'policy_version': self.version_number,
                'retention_years': self.retention_years,
                'destruction_method': self.destruction_method,
                'review_cycle_months': self.review_cycle_months,
                'risk_level': self.risk_level
            }
            
            # Mark other versions as superseded
            other_versions = self.search\([
                ('policy_id', '=', self.policy_id.id,
                ('id', '!=', self.id),
                ('approval_status', '=', 'approved')])
            ]
            other_versions.write({'approval_status': 'superseded'})
    
    def action_reject(self):
        """Reject this policy version"""
        self.write({
            'approval_status': 'rejected',
            'approved_by': self.env.user.id,
            'approval_date': fields.Datetime.now()
        }
