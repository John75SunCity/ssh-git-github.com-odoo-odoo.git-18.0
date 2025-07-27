# -*- coding: utf-8 -*-
"""
Records Security Audit Model
Tracks security audits for locations and other security-related activities
"""

from odoo import models, fields, api, _

class RecordsSecurityAudit(models.Model):
    """
    Security Audit Model for Records Management
    Tracks security assessments and audits for various entities
    """
    _name = 'records.security.audit'
    _description = 'Records Security Audit'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'audit_date desc'
    _rec_name = 'name'

    # Basic audit information
    name = fields.Char(
        string='Audit Reference',
        required=True,
        default='New'

    audit_date = fields.Date(
        string='Audit Date',
        default=fields.Date.context_today,
        required=True
    
    audit_type = fields.Selection([
        ('location', 'Location Security Audit',
        ('access', 'Access Control Audit'),
        ('document', 'Document Security Audit'),
        ('personnel', 'Personnel Security Audit'),
        ('system', 'System Security Audit'),
        ('compliance', 'Compliance Audit')
    
    # Related entities), string="Selection Field"
    location_id = fields.Many2one(
        'records.location',
        string='Location',
        help='Location being audited',
    auditor_id = fields.Many2one(
        'res.users',
        string='Auditor',
        default=lambda self: self.env.user,
        required=True
    
    # Audit status and results
    status = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled')
), string="Selection Field"
    result = fields.Selection([
        ('pass', 'Pass'),
        ('fail', 'Fail'),
        ('conditional', 'Conditional Pass'),
        ('pending', 'Pending Review')
    
    # Security assessment scores), string="Selection Field"
    security_score = fields.Float(
        string='Security Score (0-100)',
        help='Overall security assessment score',
    compliance_score = fields.Float(
        string='Compliance Score (0-100)',
        help='Compliance assessment score'
    
    # Audit details
    findings = fields.Text(
        string='Audit Findings',
        help='Detailed findings from the security audit',
    recommendations = fields.Text(
        string='Recommendations',
        help='Security recommendations based on audit findings',
    corrective_actions = fields.Text(
        string='Corrective Actions',
        help='Required corrective actions'
    
    # Follow-up information
    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        default=False

    follow_up_date = fields.Date(
        string='Follow-up Date'

    next_audit_date = fields.Date(
        string='Next Audit Date',
        compute='_compute_next_audit_date',
        store=True
    
    # Evidence and documentation
    evidence_attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Evidence Attachments',
        help='Supporting documentation and evidence'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('records.security.audit') or 'SA-' + str(self.env['ir.sequence'].next_by_code('records.security.audit.simple') or '001')
        return super().create(vals_list)
    
    @api.depends('audit_date', 'audit_type')
    def _compute_next_audit_date(self):
        """Compute next audit date based on audit type and current date"""
        for audit in self:
            if audit.audit_date:
                # Standard audit intervals
                intervals = {
                    'location': 90,      # Quarterly
                    'access': 30,        # Monthly
                    'document': 180,     # Semi-annually
                    'personnel': 365,    # Annually
                    'system': 60,        # Bi-monthly
                    'compliance': 365    # Annually
                }
                
                days_to_add = intervals.get(audit.audit_type, 90
                audit.next_audit_date = audit.audit_date + fields.Date.from_string('1970-01-01').replace(day=days_to_add)
            else:
                audit.next_audit_date = False
    
    def action_start_audit(self):
        """Start the security audit"""
        self.ensure_one()
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Security audit started by %s') % self.env.user.name)
    
    def action_complete_audit(self):
        """Complete the security audit"""
        self.ensure_one()
        self.write({'status': 'completed'})
        self.message_post(body=_('Security audit completed by %s') % self.env.user.name)
    
    def action_schedule_follow_up(self):
        """Schedule follow-up audit"""
        self.ensure_one()
        return {
            'name': _('Schedule Follow-up Audit'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.security.audit',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_audit_type': self.audit_type,
                'default_location_id': self.location_id.id if self.location_id else False,
                'default_follow_up_date': self.follow_up_date,
            },
        }
    
    def action_view_evidence(self):
        """View audit evidence"""
        self.ensure_one()
        return {
            'name': _('Audit Evidence'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.evidence_attachment_ids.ids)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }
