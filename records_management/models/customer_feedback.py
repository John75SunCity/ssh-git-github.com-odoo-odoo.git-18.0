# New file: Extension for customer feedback using Odoo's 'survey' module. This is optional and not strictly needed since the core feedback uses built-in surveys (as per manifest 'survey' dependency)—it provides custom hooks for NAID AAA-compliant logging (auto-audit trails on submissions), sentiment analysis (innovative: basic keyword-based, extendable to AI via torch in code_execution tool), and integration with portal requests (e.g., link feedback to services for continuous improvement per ISO 15489). Accomplishes structured feedback with clean backend views/analytics, user-friendly submission (no extra UI bloat). If unused, remove from __init__.py to keep module simple.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
import re  # For basic sentiment (positive/negative keywords)

class CustomerFeedback(models.Model):
    _name = 'customer.feedback'
    _description = 'Customer Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'submitted_date desc'

    name = fields.Char(string='Subject', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True, tracking=True)
    feedback_type = fields.Selection([
        ('suggestion', 'Suggestion'),
        ('concern', 'Concern'),
        ('compliment', 'Compliment'),
        ('general', 'General'),
    ], string='Feedback Type', required=True, tracking=True)
    
    # Core feedback fields
    rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Rating', tracking=True)
    
    comments = fields.Text(string='Comments', tracking=True)
    service_area = fields.Char(string='Service Area', default='portal', tracking=True)
    submitted_date = fields.Datetime(string='Submitted Date', default=fields.Datetime.now, readonly=True)
    
    # AI-ready sentiment analysis
    sentiment_score = fields.Float(string='Sentiment Score', compute='_compute_sentiment', store=True, 
                                 help="Sentiment score from -1 (negative) to 1 (positive)")
    sentiment_category = fields.Selection([
        ('positive', 'Positive'),
        ('neutral', 'Neutral'),
        ('negative', 'Negative')
    ], string='Sentiment', compute='_compute_sentiment', store=True)
    
    # NAID compliance and workflow
    state = fields.Selection([
        ('new', 'New'),
        ('reviewed', 'Reviewed'),
        ('responded', 'Responded'),
        ('closed', 'Closed')
    ], string='Status', default='new', tracking=True)
    
    response = fields.Text(string='Management Response', tracking=True)
    response_date = fields.Datetime(string='Response Date', tracking=True)
    response_user_id = fields.Many2one('res.users', string='Responded By', tracking=True)
    
    # Integration fields
    linked_request_id = fields.Many2one('portal.request', string='Linked Request', 
                                      help="Link to related portal service request")
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    # Phase 3: Customer Feedback Analytics
    
    # Satisfaction Analytics
    satisfaction_trend_score = fields.Float(
        string='Satisfaction Trend Score',
        compute='_compute_satisfaction_analytics',
        store=True,
        help='Trending satisfaction score for this customer'
    )
    
    response_effectiveness_rating = fields.Float(
        string='Response Effectiveness Rating',
        compute='_compute_satisfaction_analytics',
        store=True,
        help='Effectiveness of management response'
    )
    
    # Pattern Analytics
    feedback_frequency_indicator = fields.Selection([
        ('first_time', 'First Time'),
        ('occasional', 'Occasional'),
        ('frequent', 'Frequent'),
        ('power_user', 'Power User')
    ], string='Feedback Frequency',
       compute='_compute_pattern_analytics',
       store=True,
       help='Customer feedback frequency pattern')
    
    service_improvement_potential = fields.Float(
        string='Service Improvement Potential',
        compute='_compute_pattern_analytics',
        store=True,
        help='Potential for service improvements based on feedback'
    )

    @api.depends('comments', 'rating')
    def _compute_sentiment(self):
        """Basic sentiment analysis using keyword matching"""
        positive_keywords = ['great', 'excellent', 'awesome', 'good', 'love', 'perfect', 'amazing', 
                           'outstanding', 'wonderful', 'fantastic', 'satisfied', 'happy', 'pleased']
        negative_keywords = ['bad', 'terrible', 'awful', 'poor', 'hate', 'horrible', 'disappointing',
                           'frustrated', 'angry', 'unsatisfied', 'problem', 'issue', 'concern', 'complaint']
        
        for rec in self:
            text = (rec.comments or '').lower()
            
            # Count positive and negative keywords
            pos_count = sum(1 for word in positive_keywords if re.search(r'\b' + word + r'\b', text))
            neg_count = sum(1 for word in negative_keywords if re.search(r'\b' + word + r'\b', text))
            
            # Consider rating in sentiment calculation
            rating_score = 0
            if rec.rating:
                rating_val = int(rec.rating)
                if rating_val >= 4:
                    pos_count += 2
                elif rating_val <= 2:
                    neg_count += 2
                else:
                    pos_count += 1  # Neutral but slightly positive
            
            # Calculate sentiment score (-1 to 1)
            total_words = max(1, pos_count + neg_count)
            rec.sentiment_score = (pos_count - neg_count) / total_words
            
            # Categorize sentiment
            if rec.sentiment_score > 0.2:
                rec.sentiment_category = 'positive'
            elif rec.sentiment_score < -0.2:
                rec.sentiment_category = 'negative'
            else:
                rec.sentiment_category = 'neutral'
    
    @api.depends('rating', 'sentiment_score', 'response', 'state')
    def _compute_satisfaction_analytics(self):
        """Compute customer satisfaction analytics"""
        for record in self:
            # Satisfaction trend based on customer's feedback history
            customer_feedbacks = self.search([
                ('partner_id', '=', record.partner_id.id),
                ('submitted_date', '<=', record.submitted_date)
            ], order='submitted_date desc', limit=5)
            
            if len(customer_feedbacks) > 1:
                # Calculate trend from recent feedbacks
                ratings = []
                for feedback in customer_feedbacks:
                    if feedback.rating:
                        ratings.append(int(feedback.rating))
                
                if ratings:
                    avg_rating = sum(ratings) / len(ratings)
                    # Convert to 0-100 scale
                    trend_score = (avg_rating - 1) * 25  # 1-5 scale to 0-100
                    
                    # Boost for positive sentiment
                    if record.sentiment_score > 0:
                        trend_score += record.sentiment_score * 10
                else:
                    trend_score = 50  # Neutral if no ratings
            else:
                # First feedback - base on current rating and sentiment
                if record.rating:
                    trend_score = (int(record.rating) - 1) * 25
                    if record.sentiment_score > 0:
                        trend_score += record.sentiment_score * 10
                else:
                    trend_score = 60 if record.sentiment_score > 0 else 40
            
            record.satisfaction_trend_score = min(max(trend_score, 0), 100)
            
            # Response effectiveness rating
            effectiveness = 60  # Base effectiveness
            
            if record.state == 'responded' and record.response:
                effectiveness += 20  # Response provided
                
                # Response quality (length and keywords)
                response_length = len(record.response.strip()) if record.response else 0
                if response_length > 100:
                    effectiveness += 10
                elif response_length > 50:
                    effectiveness += 5
                
                # Response timeliness
                if record.response_date and record.submitted_date:
                    response_time = (record.response_date - record.submitted_date).total_seconds() / 3600
                    if response_time <= 24:  # Within 24 hours
                        effectiveness += 10
                    elif response_time <= 72:  # Within 3 days
                        effectiveness += 5
            elif record.state == 'closed':
                effectiveness += 10  # Issue resolved
            
            record.response_effectiveness_rating = min(max(effectiveness, 0), 100)
    
    @api.depends('partner_id', 'feedback_type', 'submitted_date')
    def _compute_pattern_analytics(self):
        """Compute feedback pattern analytics"""
        for record in self:
            # Feedback frequency analysis
            total_feedbacks = self.search_count([('partner_id', '=', record.partner_id.id)])
            
            if total_feedbacks >= 10:
                record.feedback_frequency_indicator = 'power_user'
            elif total_feedbacks >= 5:
                record.feedback_frequency_indicator = 'frequent'
            elif total_feedbacks >= 2:
                record.feedback_frequency_indicator = 'occasional'
            else:
                record.feedback_frequency_indicator = 'first_time'
            
            # Service improvement potential
            improvement_score = 50  # Base potential
            
            # Negative feedback indicates high improvement potential
            if record.sentiment_score < -0.2:
                improvement_score += 30
            elif record.sentiment_score < 0:
                improvement_score += 15
            
            # Specific feedback types indicate actionable improvements
            actionable_types = ['suggestion', 'concern']
            if record.feedback_type in actionable_types:
                improvement_score += 20
            
            # Detailed comments indicate specific improvement areas
            if record.comments and len(record.comments.strip()) > 100:
                improvement_score += 10
            
            # Frequent customers provide valuable improvement insights
            if record.feedback_frequency_indicator in ['frequent', 'power_user']:
                improvement_score += 5
            
            record.service_improvement_potential = min(max(improvement_score, 0), 100)

    @api.model_create_multi
    def create(self, vals_list):
        """Create feedback with NAID audit logging"""
        res = super().create(vals_list)
        
        # NAID audit logging
        for record in res:
            self.env['naid.audit.log'].sudo().create({
                'user_id': self.env.user.id,
                'partner_id': record.partner_id.id,
                'action': 'feedback_submission',
                'resource_type': 'customer_feedback',
                'resource_id': record.id,
                'access_date': fields.Datetime.now(),
                'ip_address': self.env.context.get('ip_address'),
                'user_agent': self.env.context.get('user_agent'),
                'details': f'Feedback submitted: {record.feedback_type} - Rating: {record.rating}'
            })
        
        # Post message for tracking
        res.message_post(
            body=_('Customer feedback submitted by %s (ID: %s) - NAID Audit Log', 
                  res.partner_id.name, res.partner_id.id),
            message_type='notification',
        )
        
        # Auto-assign priority based on sentiment and rating
        if res.sentiment_category == 'negative' or (res.rating and int(res.rating) <= 2):
            res.priority = 'high'
        elif res.sentiment_category == 'positive' and res.rating and int(res.rating) >= 4:
            res.priority = 'low'
        
        return res

    def action_mark_reviewed(self):
        """Mark feedback as reviewed"""
        self.write({
            'state': 'reviewed',
        })
        self.message_post(body=_('Feedback marked as reviewed by %s', self.env.user.name))

    def action_respond(self):
        """Mark feedback as responded"""
        self.write({
            'state': 'responded',
            'response_date': fields.Datetime.now(),
            'response_user_id': self.env.user.id,
        })
        self.message_post(body=_('Response provided by %s', self.env.user.name))

    def action_close(self):
        """Close feedback"""
        self.write({'state': 'closed'})
        self.message_post(body=_('Feedback closed by %s', self.env.user.name))

    def action_escalate(self):
        """Escalate feedback to management"""
        self.write({'state': 'escalated'})
        self.message_post(body=_('Feedback escalated by %s', self.env.user.name))

    def action_reopen(self):
        """Reopen closed feedback"""
        self.write({'state': 'new'})
        self.message_post(body=_('Feedback reopened by %s', self.env.user.name))

    def action_view_customer_history(self):
        """View customer's feedback history"""
        self.ensure_one()
        return {
            'name': _('Customer Feedback History'),
            'type': 'ir.actions.act_window',
            'res_model': 'customer.feedback',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }

    def action_view_related_tickets(self):
        """View related tickets/requests"""
        self.ensure_one()
        return {
            'name': _('Related Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'portal.request',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.partner_id.id)],
            'context': {'default_customer_id': self.partner_id.id},
        }

    def action_view_improvement_actions(self):
        """View improvement actions related to this feedback"""
        self.ensure_one()
        return {
            'name': _('Improvement Actions'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form',
            'domain': [('name', 'ilike', self.name)],
            'context': {'default_name': 'Improvement: %s' % self.name},
        }

    @api.constrains('rating')
    def _check_rating(self):
        """Validate rating values"""
        for rec in self:
            if rec.rating and int(rec.rating) not in range(1, 6):
                raise ValidationError(_('Rating must be between 1 and 5.'))
