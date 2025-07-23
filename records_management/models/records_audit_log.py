# -*- coding: utf-8 -*-
"""
Records Audit Log Model
General audit logging for records management activities
"""

from odoo import models, fields, api, _


class RecordsAuditLog(models.Model):
    """
    General Audit Log Model
    Tracks all audit-related activities in records management
    """
    _name = 'records.audit.log'
    _description = 'Records Audit Log'
    _order = 'timestamp desc'
    _rec_name = 'event_description'

    # Core audit information
    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    event_type = fields.Selection([
        ('access', 'Access Event'),
        ('modification', 'Modification Event'),
        ('creation', 'Creation Event'),
        ('deletion', 'Deletion Event'),
        ('security', 'Security Event'),
        ('compliance', 'Compliance Event'),
        ('system', 'System Event')
    ], string='Event Type', required=True, index=True)
    
    event_description = fields.Char(
        string='Event Description',
        required=True
    )
    
    # Related entities
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )
    
    document_id = fields.Many2one(
        'records.document',
        string='Document',
        help='Related document if applicable'
    )
    
    box_id = fields.Many2one(
        'records.box',
        string='Box',
        help='Related box if applicable'
    )
    
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service',
        help='Related shredding service if applicable'
    )
    
    # Audit details
    details = fields.Text(
        string='Details',
        help='Detailed information about the audit event'
    )
    
    ip_address = fields.Char(
        string='IP Address',
        help='IP address from which the event originated'
    )
    
    session_id = fields.Char(
        string='Session ID',
        help='User session identifier'
    )
    
    # Risk assessment
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    
    # Status tracking
    reviewed = fields.Boolean(
        string='Reviewed',
        default=False
    )
    
    reviewer_id = fields.Many2one(
        'res.users',
        string='Reviewer'
    )
    
    review_date = fields.Datetime(
        string='Review Date'
    )
    
    review_notes = fields.Text(
        string='Review Notes'
    )
    
    def action_mark_reviewed(self):
        """Mark audit log entry as reviewed"""
        self.ensure_one()
        self.write({
            'reviewed': True,
            'reviewer_id': self.env.user.id,
            'review_date': fields.Datetime.now()
        })
        self.env['mail.message'].create({
            'body': _('Audit log entry reviewed by %s') % self.env.user.name,
            'model': self._name,
            'res_id': self.id,
        })
    
    def action_escalate(self):
        """Escalate audit log entry for further review"""
        self.ensure_one()
        return {
            'name': _('Escalate Audit Entry'),
            'type': 'ir.actions.act_window',
            'res_model': 'audit.escalation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_audit_log_id': self.id},
        }
