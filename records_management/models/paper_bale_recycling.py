# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PaperBaleRecycling(models.Model):
    _name = 'paper.bale.recycling'
    _description = 'Paper Bale Recycling'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'
    
    # Basic Information
    name = fields.Char(string='Name', required=True, tracking=True, index=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)
    
    # State Management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived')
    ], string='Status', default='draft', tracking=True)
    
    # Company and User
    company_id = fields.Many2one('res.company', string='Company', 
                                 default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Responsible User', 
                              default=lambda self: self.env.user)
    
    # Timestamps
    date_created = fields.Datetime(string='Created Date', default=fields.Datetime.now)
    date_modified = fields.Datetime(string='Modified Date')
    
    # Control Fields
    active = fields.Boolean(string='Active', default=True)
    notes = fields.Text(string='Internal Notes')
    
    # Computed Fields
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    
    @api.depends('name')
    def _compute_display_name(self):
        """Compute display name."""
        for record in self:
            record.display_name = record.name or _('New')
    
    def write(self, vals):
        """Override write to update modification date."""
        vals['date_modified'] = fields.Datetime.now()
        return super().write(vals)
    
    def action_activate(self):
        """Activate the record."""
        self.write({'state': 'active'})
    
    def action_deactivate(self):
        """Deactivate the record."""
        self.write({'state': 'inactive'})
    
    def action_archive(self):
        """Archive the record."""
        self.write({'state': 'archived', 'active': False})
    
    @api.model
    def create(self, vals):
        """Override create to set default values."""
        if not vals.get('name'):
            vals['name'] = _('New Record')
        return super().create(vals)
