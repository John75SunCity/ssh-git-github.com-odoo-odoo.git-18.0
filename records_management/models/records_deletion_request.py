# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class RecordsDeletionRequest(models.Model):
    """Model for managing deletion requests from customers via portal"""
    _name = 'records.deletion.request'
    _description = 'Records Deletion Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'request_date desc'

    name = fields.Char(string='Request Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    request_date = fields.Date(string='Request Date', required=True, default=fields.Date.today, tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True)
    requested_by = fields.Many2one('res.users', string='Requested By', required=True, default=lambda self: self.env.user, tracking=True)
    
    # Request details
    description = fields.Text(string='Description', required=True)
    urgency = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    
    # Items to delete), string="Selection Field")
    box_ids = fields.Many2many('records.box', string='Boxes to Delete')
    document_ids = fields.Many2many('records.document', string='Documents to Delete')
    
    # Status tracking
    state = fields.Selection([
        ('draft', 'Draft',
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    
    # Approval workflow), string="Selection Field")
    approved_by = fields.Many2one('res.users', string='Approved By', tracking=True)
    approval_date = fields.Datetime(string='Approval Date', tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    completion_date = fields.Date(string='Completion Date', tracking=True)
    
    # Notes and comments
    internal_notes = fields.Text(string='Internal Notes')
    customer_notes = fields.Text(string='Customer Notes')
    
    # Related destruction service
    shredding_service_id = fields.Many2one('shredding.service', string='Related Shredding Service')
    
    # Computed fields
    box_count = fields.Integer(string='Box Count', compute='_compute_counts', store=True)
    document_count = fields.Integer(string='Document Count', compute='_compute_counts', store=True)
    
    @api.depends('box_ids', 'document_ids')
    def _compute_counts(self):
        for record in self:
            record.box_count = len(record.box_ids)
            record.document_count = len(record.document_ids)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('records.deletion.request') or _('New')
        return super().create(vals)

    def action_submit(self):
        self.state = 'submitted'
        
    def action_approve(self):
        self.state = 'approved'
        self.approved_by = self.env.user
        
    def action_schedule(self):
        self.state = 'scheduled'
        
    def action_start(self):
        self.state = 'in_progress'
        
    def action_complete(self):
        self.state = 'completed'
        
    def action_cancel(self):
        self.state = 'cancelled'
