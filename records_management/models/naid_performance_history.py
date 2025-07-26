# -*- coding: utf-8 -*-
"""
NAID Performance History Management
Tracks performance metrics and compliance history
"""

from odoo import models, fields, api

class NAIDPerformanceHistory(models.Model):
    _name = 'naid.performance.history'
    _description = 'NAID Performance History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'performance_date desc, name'
    _rec_name = 'name'

    # Core identification
    name = fields.Char('Performance Record Name', required=True, tracking=True)
    performance_period = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually')
    ], string='Performance Period', required=True, tracking=True)
    
    # NAID compliance relationship
    compliance_id = fields.Many2one('naid.compliance', string='NAID Compliance Record', tracking=True)
    
    # Performance details
    performance_date = fields.Date('Performance Date', required=True, default=fields.Date.today, tracking=True)
    period_start = fields.Date('Period Start', required=True, tracking=True)
    period_end = fields.Date('Period End', required=True, tracking=True)
    
    # Performance metrics
    compliance_score = fields.Float('Compliance Score', tracking=True)
    audit_score = fields.Float('Audit Score', tracking=True)
    customer_satisfaction = fields.Float('Customer Satisfaction', tracking=True)
    efficiency_rating = fields.Float('Efficiency Rating', tracking=True)
    
    # Service metrics
    services_completed = fields.Integer('Services Completed', tracking=True)
    services_on_time = fields.Integer('Services On Time', tracking=True)
    on_time_percentage = fields.Float('On Time %', compute='_compute_percentages', store=True)
    
    incidents_reported = fields.Integer('Incidents Reported', tracking=True)
    incidents_resolved = fields.Integer('Incidents Resolved', tracking=True)
    resolution_percentage = fields.Float('Resolution %', compute='_compute_percentages', store=True)
    
    # Quality metrics
    quality_checks_passed = fields.Integer('Quality Checks Passed', tracking=True)
    quality_checks_total = fields.Integer('Total Quality Checks', tracking=True)
    quality_percentage = fields.Float('Quality %', compute='_compute_percentages', store=True)
    
    # Status and assessment
    performance_status = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('satisfactory', 'Satisfactory'),
        ('needs_improvement', 'Needs Improvement'),
        ('poor', 'Poor')
    ], string='Performance Status', compute='_compute_performance_status', store=True, tracking=True)
    
    # Personnel
    assessed_by = fields.Many2one('res.users', string='Assessed By', tracking=True)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By', tracking=True)
    
    # Company and user context
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    
    # Additional details
    description = fields.Text('Description')
    notes = fields.Text('Notes')
    improvement_areas = fields.Text('Areas for Improvement')
    corrective_actions = fields.Text('Corrective Actions')
    
    @api.depends('services_completed', 'services_on_time', 'incidents_reported', 'incidents_resolved',
                 'quality_checks_passed', 'quality_checks_total')
    def _compute_percentages(self):
        """Compute various performance percentages"""
        for record in self:
            # On-time percentage
            if record.services_completed > 0:
                record.on_time_percentage = (record.services_on_time / record.services_completed) * 100
            else:
                record.on_time_percentage = 0.0
                
            # Resolution percentage  
            if record.incidents_reported > 0:
                record.resolution_percentage = (record.incidents_resolved / record.incidents_reported) * 100
            else:
                record.resolution_percentage = 100.0 if record.incidents_resolved == 0 else 0.0
                
            # Quality percentage
            if record.quality_checks_total > 0:
                record.quality_percentage = (record.quality_checks_passed / record.quality_checks_total) * 100
            else:
                record.quality_percentage = 0.0
    
    @api.depends('compliance_score', 'on_time_percentage', 'quality_percentage', 'customer_satisfaction')
    def _compute_performance_status(self):
        """Compute overall performance status based on metrics"""
        for record in self:
            # Calculate average of all metrics
            metrics = [
                record.compliance_score or 0,
                record.on_time_percentage or 0,
                record.quality_percentage or 0,
                record.customer_satisfaction or 0
            ]
            
            if all(metric == 0 for metric in metrics):
                record.performance_status = 'needs_improvement'
                continue
                
            average_score = sum(metrics) / len([m for m in metrics if m > 0])
            
            if average_score >= 90:
                record.performance_status = 'excellent'
            elif average_score >= 80:
                record.performance_status = 'good'
            elif average_score >= 70:
                record.performance_status = 'satisfactory'
            elif average_score >= 60:
                record.performance_status = 'needs_improvement'
            else:
                record.performance_status = 'poor'
