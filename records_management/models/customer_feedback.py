# -*- coding: utf-8 -*-
"""
Customer Feedback Management
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class CustomerFeedback(models.Model):
    """
    Customer Feedback Management
    Handles customer feedback and satisfaction tracking
    """
    
    _name = 'customer.feedback'
    _description = 'Customer Feedback'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'feedback_date desc, name'
    _rec_name = "name"
    
    # ==========================================
    # CORE FIELDS
    # ==========================================
    name = fields.Char(string='Feedback Reference', required=True, tracking=True,
                      default=lambda self: _('New'), copy=False)
    description = fields.Text(string='Feedback Details', tracking=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', 
                                default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Assigned User', 
                             default=lambda self: self.env.user, tracking=True)
    
    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', 
                                 required=True, tracking=True,
                                 domain=[('is_company', '=', True)])
    contact_person = fields.Many2one('res.partner', string='Contact Person',
                                   domain=[('is_company', '=', False)], tracking=True)
    
    # ==========================================
    # FEEDBACK DETAILS
    # ==========================================
    feedback_date = fields.Date(string='Feedback Date', 
                               default=fields.Date.today, required=True, tracking=True)
    feedback_type = fields.Selection([
        ('compliment', 'Compliment'),
        ('complaint', 'Complaint'),
        ('suggestion', 'Suggestion'),
        ('question', 'Question'),
        ('general', 'General Feedback')
    ], string='Feedback Type', required=True, tracking=True)
    
    service_area = fields.Selection([
        ('pickup', 'Pickup Service'),
        ('storage', 'Storage Service'),
        ('destruction', 'Destruction Service'),
        ('customer_service', 'Customer Service'),
        ('billing', 'Billing'),
        ('general', 'General')
    ], string='Service Area', tracking=True)
    
    # ==========================================
    # RATING AND SATISFACTION
    # ==========================================
    rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Rating', tracking=True)
    
    satisfaction_level = fields.Selection([
        ('very_dissatisfied', 'Very Dissatisfied'),
        ('dissatisfied', 'Dissatisfied'),
        ('neutral', 'Neutral'),
        ('satisfied', 'Satisfied'),
        ('very_satisfied', 'Very Satisfied')
    ], string='Satisfaction Level', tracking=True)
    
    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('new', 'New'),
        ('acknowledged', 'Acknowledged'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed')
    ], string='Status', default='new', tracking=True, required=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    # ==========================================
    # RESPONSE TRACKING
    # ==========================================
    response_required = fields.Boolean(string='Response Required', default=True)
    response_deadline = fields.Date(string='Response Deadline', tracking=True)
    response_date = fields.Date(string='Response Date', tracking=True)
    response_notes = fields.Text(string='Response Notes', tracking=True)
    
    # ==========================================
    # WORKFLOW METHODS
    # ==========================================
    def action_acknowledge(self):
        """Acknowledge feedback"""
        self.ensure_one()
        if self.state != 'new':
            raise UserError(_('Only new feedback can be acknowledged'))
        
        self.write({'state': 'acknowledged'})
        self.message_post(body=_('Feedback acknowledged'))
    
    def action_start_progress(self):
        """Start working on feedback"""
        self.ensure_one()
        if self.state != 'acknowledged':
            raise UserError(_('Only acknowledged feedback can be started'))
        
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Started working on feedback'))
    
    def action_resolve(self):
        """Mark feedback as resolved"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Only in-progress feedback can be resolved'))
        
        self.write({
            'state': 'resolved',
            'response_date': fields.Date.today()
        })
        self.message_post(body=_('Feedback resolved'))
    
    def action_close(self):
        """Close feedback"""
        self.ensure_one()
        if self.state != 'resolved':
            raise UserError(_('Only resolved feedback can be closed'))
        
        self.write({'state': 'closed'})
        self.message_post(body=_('Feedback closed'))
    
    @api.model
    def create(self, vals):
        """Override create to set sequence number"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('customer.feedback') or _('New')
        return super().create(vals)
