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

    @api.constrains('rating')
    def _check_rating(self):
        """Validate rating values"""
        for rec in self:
            if rec.rating and int(rec.rating) not in range(1, 6):
                raise ValidationError(_('Rating must be between 1 and 5.'))
