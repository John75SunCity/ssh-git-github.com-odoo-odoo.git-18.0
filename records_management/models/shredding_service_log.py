# -*- coding: utf-8 -*-
"""
Shredding Service Log Model
Detailed logging for shredding service activities
"""

from odoo import models, fields, api, _


class ShreddingServiceLog(models.Model):
    """
    Shredding Service Activity Log Model
    Tracks all activities related to shredding services
    """
    _name = 'shredding.service.log'
    _description = 'Shredding Service Log'
    _order = 'timestamp desc'
    _rec_name = 'activity_description'

    # Core log information
    timestamp = fields.Datetime(
        string='Timestamp',
        default=fields.Datetime.now,
        required=True,
        index=True
    )
    
    activity_type = fields.Selection([
        ('scheduled', 'Service Scheduled'),
        ('started', 'Service Started'),
        ('completed', 'Service Completed'),
        ('cancelled', 'Service Cancelled'),
        ('incident', 'Incident Reported'),
        ('quality_check', 'Quality Check'),
        ('compliance_check', 'Compliance Check')
    ], string='Activity Type', required=True, index=True)
    
    activity_description = fields.Char(
        string='Activity Description',
        required=True
    )
    
    # Related entities
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service',
        required=True,
        ondelete='cascade'
    )
    
    user_id = fields.Many2one(
        'res.users',
        string='User',
        default=lambda self: self.env.user,
        required=True
    )
    
    # Service details
    documents_count = fields.Integer(
        string='Documents Processed',
        help='Number of documents processed in this activity'
    )
    
    weight_processed = fields.Float(
        string='Weight Processed (kg)',
        help='Weight of materials processed'
    )
    
    duration_minutes = fields.Integer(
        string='Duration (minutes)',
        help='Duration of the activity in minutes'
    )
    
    # Quality and compliance
    quality_score = fields.Float(
        string='Quality Score',
        help='Quality assessment score (0-100)'
    )
    
    compliance_verified = fields.Boolean(
        string='Compliance Verified',
        default=False
    )
    
    # Status and notes
    status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('requires_attention', 'Requires Attention')
    ], string='Status', default='pending')
    
    notes = fields.Text(
        string='Notes',
        help='Additional notes about this activity'
    )
    
    # File attachments
    attachment_ids = fields.Many2many(
        'ir.attachment',
        string='Attachments',
        help='Photos, certificates, or other documentation'
    )
    
    # Computed fields for analytics
    efficiency_score = fields.Float(
        string='Efficiency Score',
        compute='_compute_efficiency_score',
        store=True,
        help='Calculated efficiency based on time and volume'
    )
    
    @api.depends('duration_minutes', 'documents_count', 'weight_processed')
    def _compute_efficiency_score(self):
        """Calculate efficiency score based on processing metrics"""
        for record in self:
            if record.duration_minutes and (record.documents_count or record.weight_processed):
                base_score = 50
                
                # Documents per minute factor
                if record.documents_count:
                    docs_per_min = record.documents_count / record.duration_minutes
                    base_score += min(docs_per_min * 10, 30)
                
                # Weight per minute factor
                if record.weight_processed:
                    weight_per_min = record.weight_processed / record.duration_minutes
                    base_score += min(weight_per_min * 5, 20)
                
                record.efficiency_score = min(base_score, 100)
            else:
                record.efficiency_score = 0
    
    def action_mark_completed(self):
        """Mark activity as completed"""
        self.ensure_one()
        self.write({
            'status': 'completed',
            'activity_description': f"{self.activity_description} (Completed)"
        })
    
    def action_flag_issue(self):
        """Flag activity for attention"""
        self.ensure_one()
        self.write({
            'status': 'requires_attention'
        })
        
        # Create notification
        self.env['mail.message'].create({
            'body': _('Shredding service activity flagged for attention: %s') % self.activity_description,
            'model': self._name,
            'res_id': self.id,
        })
