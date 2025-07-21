# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SurveyImprovementAction(models.Model):
    """Model for tracking improvement actions based on survey feedback"""
    _name = 'survey.improvement.action'
    _description = 'Survey Improvement Action'
    _order = 'priority desc, due_date asc, create_date desc'

    # Basic Information
    name = fields.Char(string='Action Title', required=True)
    description = fields.Text(string='Description', required=True)
    feedback_id = fields.Many2one('survey.user_input', string='Related Feedback', 
                                 required=True, ondelete='cascade')
    
    # Action Classification
    action_type = fields.Selection([
        ('process', 'Process Improvement'),
        ('training', 'Staff Training'),
        ('facility', 'Facility Upgrade'),
        ('service', 'Service Enhancement'),
        ('communication', 'Communication Improvement'),
        ('technology', 'Technology Update'),
        ('policy', 'Policy Change'),
        ('other', 'Other')
    ], string='Action Type', required=True, default='process')
    
    # Priority and Scheduling
    priority = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', required=True, default='medium')
    
    due_date = fields.Date(string='Due Date')
    estimated_effort = fields.Float(string='Estimated Effort (hours)', 
                                   help='Estimated time to complete this action')
    
    # Assignment and Status
    responsible_user_id = fields.Many2one('res.users', string='Responsible User',
                                         help='User responsible for completing this action')
    assigned_team = fields.Many2one('hr.department', string='Assigned Team',
                                   help='Department responsible for this action')
    
    status = fields.Selection([
        ('draft', 'Draft'),
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('on_hold', 'On Hold')
    ], string='Status', default='draft', required=True)
    
    # Progress Tracking
    progress = fields.Float(string='Progress (%)', default=0.0,
                           help='Completion percentage (0-100)')
    start_date = fields.Date(string='Start Date')
    completion_date = fields.Date(string='Completion Date')
    actual_effort = fields.Float(string='Actual Effort (hours)',
                                help='Actual time spent on this action')
    
    # Impact Assessment
    expected_impact = fields.Selection([
        ('low', 'Low Impact'),
        ('medium', 'Medium Impact'),
        ('high', 'High Impact'),
        ('critical', 'Critical Impact')
    ], string='Expected Impact', default='medium')
    
    impact_description = fields.Text(string='Impact Description',
                                   help='Description of expected impact on customer satisfaction')
    
    # Results and Follow-up
    completion_notes = fields.Text(string='Completion Notes')
    effectiveness_rating = fields.Selection([
        ('1', 'Not Effective'),
        ('2', 'Slightly Effective'), 
        ('3', 'Moderately Effective'),
        ('4', 'Very Effective'),
        ('5', 'Extremely Effective')
    ], string='Effectiveness Rating',
       help='Post-completion assessment of action effectiveness')
    
    # Related Records
    task_ids = fields.One2many('project.task', 'improvement_action_id', 
                              string='Related Tasks')
    meeting_ids = fields.Many2many('calendar.event', string='Related Meetings')
    
    # Compliance and Audit
    compliance_required = fields.Boolean(string='Compliance Review Required', default=False)
    compliance_notes = fields.Text(string='Compliance Notes')
    audit_trail = fields.Text(string='Audit Trail', readonly=True)
    
    # Computed Fields
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_is_overdue')
    days_to_due = fields.Integer(string='Days to Due Date', compute='_compute_days_to_due')
    
    @api.depends('due_date', 'status')
    def _compute_is_overdue(self):
        """Check if action is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue = (
                record.due_date and 
                record.due_date < today and 
                record.status not in ['completed', 'cancelled']
            )
    
    @api.depends('due_date')
    def _compute_days_to_due(self):
        """Calculate days until due date"""
        today = fields.Date.today()
        for record in self:
            if record.due_date:
                delta = record.due_date - today
                record.days_to_due = delta.days
            else:
                record.days_to_due = 0
    
    def action_start(self):
        """Mark action as started"""
        self.write({
            'status': 'in_progress',
            'start_date': fields.Date.today()
        })
        self._update_audit_trail('Action started')
    
    def action_complete(self):
        """Mark action as completed"""
        self.write({
            'status': 'completed',
            'completion_date': fields.Date.today(),
            'progress': 100.0
        })
        self._update_audit_trail('Action completed')
        
        # Update feedback record
        if self.feedback_id:
            self.feedback_id.write({
                'improvement_actions_created': True
            })
    
    def action_cancel(self):
        """Cancel the action"""
        self.write({'status': 'cancelled'})
        self._update_audit_trail('Action cancelled')
    
    def action_put_on_hold(self):
        """Put action on hold"""
        self.write({'status': 'on_hold'})
        self._update_audit_trail('Action put on hold')
    
    def _update_audit_trail(self, action):
        """Update audit trail with action"""
        timestamp = fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        user = self.env.user.name
        new_entry = f"[{timestamp}] {user}: {action}"
        
        if self.audit_trail:
            self.audit_trail = f"{self.audit_trail}\n{new_entry}"
        else:
            self.audit_trail = new_entry
    
    @api.model
    def create(self, vals):
        """Override create to add audit trail entry"""
        record = super().create(vals)
        record._update_audit_trail('Action created')
        return record
    
    def write(self, vals):
        """Override write to track changes"""
        result = super().write(vals)
        if 'status' in vals:
            for record in self:
                record._update_audit_trail(f'Status changed to {vals["status"]}')
        return result
