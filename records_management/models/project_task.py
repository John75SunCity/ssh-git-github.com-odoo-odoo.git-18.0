# -*- coding: utf-8 -*-
from odoo import models, fields

class ProjectTask(models.Model):
    """Extension of project.task to link with improvement actions"""
    _inherit = 'project.task'
    
    improvement_action_id = fields.Many2one('survey.improvement.action', 
                                          string='Related Improvement Action',
                                          help='Improvement action that this task is part of')
    
    feedback_id = fields.Many2one('survey.user_input', 
                                 related='improvement_action_id.feedback_id',
                                 string='Related Feedback', 
                                 store=True, readonly=True,
                                 help='Original feedback that led to this improvement task')
