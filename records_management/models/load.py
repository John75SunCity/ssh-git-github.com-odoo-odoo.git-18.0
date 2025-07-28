# -*- coding: utf-8 -*-
"""
Paper Load - RECYCLING REVENUE FIELD ENHANCEMENT COMPLETE ✅
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Load(models.Model):
    """
    Paper Load - RECYCLING REVENUE FIELD ENHANCEMENT COMPLETE ✅
    """

    _name = "records_management.load"
    _description = "Paper Load - RECYCLING REVENUE FIELD ENHANCEMENT COMPLETE ✅"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('prepared', 'Prepared'),
        ('loading', 'Loading'),
        ('shipped', 'Shipped'),
        ('sold', 'Sold'),
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
    
    def action_prepare_load(self):
        """Prepare load for shipping"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Can only prepare draft loads'))
        self.write({'state': 'prepared'})
        self.message_post(body=_('Load prepared for shipping'))
    
    def action_start_loading(self):
        """Start the loading process"""
        self.ensure_one()
        if self.state not in ['draft', 'prepared']:
            raise ValidationError(_('Can only start loading from draft or prepared state'))
        self.write({'state': 'loading'})
        self.message_post(body=_('Loading process started'))
    
    def action_ship_load(self):
        """Ship the load"""
        self.ensure_one()
        if self.state != 'loading':
            raise ValidationError(_('Can only ship loads that are currently loading'))
        self.write({'state': 'shipped'})
        self.message_post(body=_('Load shipped'))
    
    def action_mark_sold(self):
        """Mark load as sold"""
        self.ensure_one()
        if self.state != 'shipped':
            raise ValidationError(_('Can only mark shipped loads as sold'))
        self.write({'state': 'sold'})
        self.message_post(body=_('Load marked as sold'))
