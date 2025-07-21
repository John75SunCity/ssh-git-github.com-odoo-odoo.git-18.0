# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class SurveyUserInput(models.Model):
    _inherit = 'survey.user_input'

    # Sentiment Analysis Fields
    sentiment_score = fields.Float(
        string='Sentiment Score', 
        compute='_compute_sentiment_score', 
        store=True,
        help='Sentiment score from 0.0 (negative) to 1.0 (positive)'
    )
    
    # Priority and Categorization
    priority_level = fields.Selection([
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ], string='Priority Level', default='normal')
    
    feedback_category = fields.Selection([
        ('service', 'Service Quality'),
        ('staff', 'Staff Performance'),
        ('facility', 'Facility'),
        ('process', 'Process Improvement'),
        ('billing', 'Billing'),
        ('other', 'Other'),
    ], string='Feedback Category')
    
    # Follow-up and Review Fields
    follow_up_required = fields.Boolean(string='Follow-up Required', default=False)
    admin_reviewed = fields.Boolean(string='Admin Reviewed', default=False)
    reviewed_by = fields.Many2one('res.users', string='Reviewed By')
    review_date = fields.Datetime(string='Review Date')
    assigned_to = fields.Many2one('res.users', string='Assigned To')
    
    # Analytics Fields
    response_count = fields.Integer(string='Response Count', compute='_compute_response_count', store=True)
    completion_time = fields.Float(string='Completion Time (minutes)', compute='_compute_completion_time', store=True)
    response_summary = fields.Text(string='Response Summary', compute='_compute_response_summary', store=True)
    
    # Improvement Tracking
    improvement_actions_created = fields.Boolean(string='Improvement Actions Created', default=False)
    sentiment_analysis = fields.Text(string='Sentiment Analysis Details')

    @api.depends('user_input_line_ids')
    def _compute_sentiment_score(self):
        """Compute sentiment score based on survey responses"""
        for record in self:
            if not record.user_input_line_ids:
                record.sentiment_score = 0.5
                continue
                
            # Simple sentiment analysis based on text responses
            positive_keywords = ['excellent', 'great', 'good', 'satisfied', 'happy', 'pleased', 'amazing', 'perfect']
            negative_keywords = ['poor', 'bad', 'terrible', 'unsatisfied', 'disappointed', 'awful', 'horrible']
            
            total_score = 0
            response_count = 0
            
            for line in record.user_input_line_ids:
                # Check for text responses using correct field names
                text_value = None
                if hasattr(line, 'value_text_box') and line.value_text_box:
                    text_value = line.value_text_box.lower()
                elif hasattr(line, 'value_char_box') and line.value_char_box:
                    text_value = line.value_char_box.lower()
                
                if text_value:
                    score = 0.5  # neutral
                    
                    positive_count = sum(1 for word in positive_keywords if word in text_value)
                    negative_count = sum(1 for word in negative_keywords if word in text_value)
                    
                    if positive_count > negative_count:
                        score = min(1.0, 0.5 + (positive_count * 0.1))
                    elif negative_count > positive_count:
                        score = max(0.0, 0.5 - (negative_count * 0.1))
                    
                    total_score += score
                    response_count += 1
                elif hasattr(line, 'value_numerical') and line.value_numerical:
                    # Normalize numerical responses (assuming 1-5 scale)
                    normalized = (line.value_numerical - 1) / 4.0
                    total_score += normalized
                    response_count += 1
            
            record.sentiment_score = total_score / response_count if response_count > 0 else 0.5

    @api.depends('user_input_line_ids')
    def _compute_response_count(self):
        """Count the number of responses"""
        for record in self:
            record.response_count = len(record.user_input_line_ids)

    @api.depends('create_date', 'state')
    def _compute_completion_time(self):
        """Calculate completion time in minutes"""
        for record in self:
            if record.state == 'done' and record.create_date:
                # If we had a finish date, we'd use that. For now, estimate based on response count
                record.completion_time = record.response_count * 0.5  # Estimate 30 seconds per response
            else:
                record.completion_time = 0.0

    @api.depends('user_input_line_ids')
    def _compute_response_summary(self):
        """Create a summary of text responses"""
        for record in self:
            text_responses = []
            for line in record.user_input_line_ids:
                # Check for different text field types in survey.user_input.line
                text_value = None
                if hasattr(line, 'value_text_box') and line.value_text_box:
                    text_value = line.value_text_box.strip()
                elif hasattr(line, 'value_char_box') and line.value_char_box:
                    text_value = line.value_char_box.strip()
                elif hasattr(line, 'suggested_answer_id') and line.suggested_answer_id:
                    text_value = line.suggested_answer_id.value
                
                if text_value and len(text_value) > 0:
                    text_responses.append(text_value)
            
            if text_responses:
                # Create a summary of first 100 characters of each response
                summary_parts = []
                for response in text_responses[:3]:  # First 3 responses
                    if len(response) > 100:
                        summary_parts.append(response[:97] + "...")
                    else:
                        summary_parts.append(response)
                
                record.response_summary = " | ".join(summary_parts)
                if len(text_responses) > 3:
                    record.response_summary += f" (and {len(text_responses) - 3} more responses)"
            else:
                record.response_summary = "No text responses"

    def action_mark_reviewed(self):
        """Mark feedback as reviewed by current user"""
        self.write({
            'admin_reviewed': True,
            'reviewed_by': self.env.user.id,
            'review_date': fields.Datetime.now()
        })

    def action_assign_to_user(self):
        """Open wizard to assign feedback to a user"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Feedback',
            'res_model': 'survey.feedback.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_feedback_id': self.id}
        }

    def action_review_feedback(self):
        """Action to review feedback - marks as reviewed and opens detailed view"""
        self.write({
            'admin_reviewed': True,
            'reviewed_by': self.env.user.id,
            'review_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Review Feedback',
            'res_model': 'survey.user_input',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_mark_follow_up(self):
        """Mark feedback as requiring follow-up"""
        self.write({
            'follow_up_required': True,
            'follow_up_date': fields.Datetime.now()
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Follow-up Marked',
                'message': f'Feedback has been marked for follow-up.',
                'type': 'success'
            }
        }

    def action_assign_follow_up(self):
        """Action to assign follow-up to a specific user"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Assign Follow-up',
            'res_model': 'survey.feedback.assign.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_feedback_id': self.id,
                'default_assign_type': 'follow_up',
                'default_follow_up_required': True
            }
        }

    def action_create_quick_task(self):
        """Create a quick improvement task based on feedback"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Quick Task',
            'res_model': 'project.task',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_name': f'Quick Fix: {self.partner_id.name or "Anonymous"} Feedback',
                'default_description': f'Quick improvement task based on feedback from {self.partner_id.name or "Anonymous"}:\n\n{self.response_summary or "No summary available"}',
                'default_priority': '1' if self.priority_level == 'urgent' else '0',
                'default_tag_ids': [(6, 0, [])],  # Add improvement tags if available
            }
        }

    def action_create_strategic_improvement_plan(self):
        """Create comprehensive strategic improvement plan"""
        self.write({
            'improvement_actions_created': True,
        })
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Create Strategic Improvement Plan',
            'res_model': 'survey.improvement.plan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_feedback_id': self.id,
                'default_feedback_summary': self.response_summary,
                'default_sentiment_score': self.sentiment_score,
                'default_priority_level': self.priority_level,
                'default_plan_type': 'strategic'
            }
        }

    def action_schedule_follow_up(self):
        """Schedule follow-up action with calendar event"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Schedule Follow-up',
            'res_model': 'calendar.event',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_name': f'Follow-up: {self.partner_id.name or "Anonymous"} Feedback',
                'default_description': f'Follow-up on feedback:\n\n{self.response_summary or "No summary available"}',
                'default_partner_ids': [(6, 0, [self.partner_id.id] if self.partner_id else [])],
                'default_duration': 1.0,  # 1 hour default
            }
        }
