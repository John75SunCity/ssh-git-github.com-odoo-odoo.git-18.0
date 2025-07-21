# -*- coding: utf-8 -*-
from odoo import models, fields, api

class SurveyFeedbackTheme(models.Model):
    """Model for categorizing feedback themes for AI analysis"""
    _name = 'survey.feedback.theme'
    _description = 'Survey Feedback Theme'
    _order = 'name'

    name = fields.Char(string='Theme Name', required=True, 
                       help='Name of the feedback theme (e.g., "Service Quality", "Response Time")')
    description = fields.Text(string='Description', 
                             help='Detailed description of this theme')
    color = fields.Integer(string='Color', 
                          help='Color for kanban view and tags')
    active = fields.Boolean(string='Active', default=True)
    
    # AI Classification fields
    keywords = fields.Text(string='Keywords', 
                          help='Comma-separated keywords for AI theme detection')
    category = fields.Selection([
        ('service', 'Service Quality'),
        ('communication', 'Communication'),
        ('pricing', 'Pricing'),
        ('product', 'Product Quality'),
        ('support', 'Customer Support'),
        ('process', 'Process Improvement'),
        ('other', 'Other')
    ], string='Category', default='other')
    
    # Usage tracking
    usage_count = fields.Integer(string='Usage Count', default=0,
                                help='Number of times this theme was identified')
    
    _sql_constraints = [
        ('name_unique', 'UNIQUE(name)', 'Theme name must be unique'),
    ]

    def action_view_feedback(self):
        """View feedback entries tagged with this theme"""
        return {
            'type': 'ir.actions.act_window',
            'name': f'Feedback: {self.name}',
            'res_model': 'survey.user_input',
            'view_mode': 'tree,form',
            'domain': [('key_themes', 'in', [self.id])],
            'context': {'default_key_themes': [(6, 0, [self.id])]},
        }
