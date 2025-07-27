# -*- coding: utf-8 -*-
"""
NAID Compliance Checklist Management
Tracks compliance checklists and verification procedures
"""

from odoo import models, fields, api

class NAIDComplianceChecklist(models.Model):
    _name = 'naid.compliance.checklist'
    _description = 'NAID Compliance Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'checklist_date desc, name'
    _rec_name = 'name'

    # Core identification
    name = fields.Char('Checklist Name', required=True, tracking=True)
    checklist_type = fields.Selection([
        ('daily', 'Daily Checklist'),
        ('weekly', 'Weekly Checklist'),
        ('monthly', 'Monthly Checklist'),
        ('quarterly', 'Quarterly Checklist'),
        ('annual', 'Annual Checklist'),
        ('audit', 'Audit Checklist'),
        ('incident', 'Incident Response Checklist')
    
    # NAID compliance relationship), string="Selection Field"
    compliance_id = fields.Many2one('naid.compliance', string='NAID Compliance Record', tracking=True)
    
    # Checklist details
    checklist_date = fields.Date('Checklist Date', required=True, default=fields.Date.today, tracking=True)
    completed_date = fields.Date('Completed Date', tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    
    # Status and completion
    status = fields.Selection([
        ('pending', 'Pending',
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('overdue', 'Overdue'),
), string="Selection Field"
    completion_percentage = fields.Float('Completion %', compute='_compute_completion', store=True)
    is_overdue = fields.Boolean('Is Overdue', compute='_compute_overdue', store=True)
    
    # Personnel
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    completed_by = fields.Many2one('res.users', string='Completed By', tracking=True)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By', tracking=True)
    
    # Company and user context
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', default=lambda self: self.env.user)
    active = fields.Boolean('Active', default=True)
    
    # Additional details
    description = fields.Text('Description')
    notes = fields.Text('Notes')
    findings = fields.Text('Findings')
    corrective_actions = fields.Text('Corrective Actions Required')
    
    @api.depends('due_date')
    def _compute_overdue(self):
        """Compute if checklist is overdue"""
        today = fields.Date.today()
        for record in self:
    pass
            record.is_overdue = (record.due_date and record.due_date < today and 
                               record.status not in ['completed', 'failed']
    
    @api.depends('status')
    def _compute_completion(self):
        """Compute completion percentage based on status"""
        for record in self:
            if record.status == 'completed':
    pass
                record.completion_percentage = 100.0
            elif record.status == 'in_progress':
    pass
                record.completion_percentage = 50.0
            else:
                record.completion_percentage = 0.0
                
    def action_start_checklist(self):
        """Mark checklist as in progress"""
        self.ensure_one()
        self.write({
            'status': 'in_progress',
            'assigned_to': self.env.user.id
        }
        
    def action_complete_checklist(self):
        """Mark checklist as completed"""
        self.ensure_one()
        self.write({
            'status': 'completed',
            'completed_date': fields.Date.today(),
            'completed_by': self.env.user.id,
            'completion_percentage': 100.0
        }
