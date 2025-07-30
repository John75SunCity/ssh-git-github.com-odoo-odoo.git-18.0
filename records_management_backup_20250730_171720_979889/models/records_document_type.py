# -*- coding: utf-8 -*-
"""
Record Document Type
"""

from odoo import models, fields, api, _


class RecordsDocumentType(models.Model):
    """
    Record Document Type
    """

    _name = "records.document.type"
    _description = "Record Document Type"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Security and Classification
    security_classification = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Classification', default='internal', tracking=True)
    
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low', tracking=True)

    # Compliance and Audit
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Compliance Status', default='pending', tracking=True)
    
    audit_required = fields.Boolean(string='Audit Required', default=False)
    approval_required = fields.Boolean(string='Approval Required', default=False)
    
    # Regulatory Compliance
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    retention_compliance = fields.Boolean(string='Retention Compliance', default=True)
    compliance_notes = fields.Text(string='Compliance Notes')
    
    # Approval Tracking
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    
    # Analytics and AI Fields
    document_type_utilization = fields.Float(string='Document Type Utilization %', default=0.0)
    growth_trend_indicator = fields.Float(string='Growth Trend Indicator', default=0.0)
    seasonal_pattern_score = fields.Float(string='Seasonal Pattern Score', default=0.0)
    classification_accuracy_score = fields.Float(string='Classification Accuracy Score', default=0.0)
    auto_classification_potential = fields.Float(string='Auto Classification Potential', default=0.0)
    type_complexity_rating = fields.Float(string='Type Complexity Rating', default=0.0)
    regulatory_compliance_score = fields.Float(string='Regulatory Compliance Score', default=0.0)
    audit_readiness_level = fields.Float(string='Audit Readiness Level', default=0.0)
    compliance_risk_assessment = fields.Float(string='Compliance Risk Assessment', default=0.0)

    # Document Count (computed)
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count')

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    action_view_type_documents = fields.Char(string='Action View Type Documents')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    analytics = fields.Char(string='Analytics')
    auto_classification = fields.Char(string='Auto Classification')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    compliance = fields.Char(string='Compliance')
    confidential = fields.Char(string='Confidential')
    group_compliance = fields.Char(string='Group Compliance')
    group_risk = fields.Char(string='Group Risk')
    group_security = fields.Char(string='Group Security')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive', default=False)
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    res_model = fields.Char(string='Res Model')
    view_mode = fields.Char(string='View Mode')

    @api.depends('name')  # You'll need to relate this to actual document records
    def _compute_document_count(self):
        """Compute the number of documents using this type"""
        for record in self:
            # This would need to be connected to actual document records
            # For now, setting to 0
            record.document_count = 0

    def action_view_type_documents(self):
        """Action to view documents of this type"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Documents - {self.name}',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('document_type_id', '=', self.id)],
            'context': {'default_document_type_id': self.id}
        }

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
