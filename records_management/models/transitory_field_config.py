# -*- coding: utf-8 -*-
from odoo import models, fields, api

class TransitoryFieldConfig(models.Model):
    _name = 'transitory.field.config'
    _description = 'Transitory Field Config'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'
    
    # Core fields
    name = fields.Char(string='Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="Assigned User", default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    
    # State management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Documentation
    notes = fields.Text(string='Notes')
    
    # Computed fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    # === BUSINESS CRITICAL FIELDS ===
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    sequence = fields.Integer(string='Sequence', default=10)
    created_date = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    updated_date = fields.Datetime(string='Updated Date')
    # === COMPREHENSIVE MISSING FIELDS ===
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    workflow_state = fields.Selection([('draft', 'Draft'), ('in_progress', 'In Progress'), ('completed', 'Completed'), ('cancelled', 'Cancelled')], string='Workflow State', default='draft')
    next_action_date = fields.Date(string='Next Action Date')
    deadline_date = fields.Date(string='Deadline')
    completion_date = fields.Datetime(string='Completion Date')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    assigned_team_id = fields.Many2one('hr.department', string='Assigned Team')
    supervisor_id = fields.Many2one('res.users', string='Supervisor')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_score = fields.Float(string='Quality Score', digits=(3, 2))
    validation_required = fields.Boolean(string='Validation Required')
    validated_by_id = fields.Many2one('res.users', string='Validated By')
    validation_date = fields.Datetime(string='Validation Date')
    reference_number = fields.Char(string='Reference Number')
    external_reference = fields.Char(string='External Reference')
    documentation_complete = fields.Boolean(string='Documentation Complete')
    attachment_ids = fields.One2many('ir.attachment', 'res_id', string='Attachments')
    performance_score = fields.Float(string='Performance Score', digits=(5, 2))
    efficiency_rating = fields.Selection([('poor', 'Poor'), ('fair', 'Fair'), ('good', 'Good'), ('excellent', 'Excellent')], string='Efficiency Rating')
    last_review_date = fields.Date(string='Last Review Date')
    next_review_date = fields.Date(string='Next Review Date')


    
    @api.depends('name')
    def _compute_display_name(self):
        for record in self:
            record.display_name = record.name or 'New'
    
    # Action methods
    def action_confirm(self):
        self.write({'state': 'confirmed'})
    
    def action_cancel(self):
        self.write({'state': 'cancelled'})
    
    def action_reset_to_draft(self):
        self.write({'state': 'draft'})
