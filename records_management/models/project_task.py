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

    def action_view_improvement_action(self):
        """View related improvement action"""
        self.ensure_one()
        if self.improvement_action_id:
    pass
            return {
                'name': _('Improvement Action'),
                'type': 'ir.actions.act_window',
                'res_model': 'survey.improvement.action',
                'res_id': self.improvement_action_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_view_feedback(self):
        """View original feedback"""
        self.ensure_one()
        if self.feedback_id:
    pass
            return {
                'name': _('Original Feedback'),
                'type': 'ir.actions.act_window',
                'res_model': 'survey.user_input',
                'res_id': self.feedback_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_complete_improvement(self):
        """Complete improvement task"""
        self.ensure_one()
        return {
            'name': _('Complete Improvement'),
            'type': 'ir.actions.act_window',
            'res_model': 'improvement.completion.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_task_id': self.id},
        }
