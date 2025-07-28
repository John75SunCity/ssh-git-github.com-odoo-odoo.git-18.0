# -*- coding: utf-8 -*-
"""
Document Retrieval Rates
"""

from odoo import models, fields, api, _


class FileRetrievalRates(models.Model):
    """
    File Retrieval Rates Model - Manages pricing for file retrieval services
    """

    _name = "file.retrieval.rates"
    _description = "File Retrieval Rates"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "effective_date desc, name"

    # Core fields
    name = fields.Char(string="Rate Plan Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)
    effective_date = fields.Date(string="Effective Date", default=fields.Date.today, required=True)

    # Base rates
    base_retrieval_rate = fields.Float(string="Base Retrieval Rate", default=0.0, digits=(12, 2))
    base_delivery_rate = fields.Float(string="Base Delivery Rate", default=0.0, digits=(12, 2))

    # Priority rates - per item
    rush_end_of_day_item = fields.Float(string="Rush End of Day (per item)", default=0.0, digits=(12, 2))
    rush_4_hours_item = fields.Float(string="Rush 4 Hours (per item)", default=0.0, digits=(12, 2))
    emergency_1_hour_item = fields.Float(string="Emergency 1 Hour (per item)", default=0.0, digits=(12, 2))
    weekend_item = fields.Float(string="Weekend (per item)", default=0.0, digits=(12, 2))
    holiday_item = fields.Float(string="Holiday (per item)", default=0.0, digits=(12, 2))

    # Priority rates - per work order
    rush_end_of_day_order = fields.Float(string="Rush End of Day (per order)", default=0.0, digits=(12, 2))
    rush_4_hours_order = fields.Float(string="Rush 4 Hours (per order)", default=0.0, digits=(12, 2))
    emergency_1_hour_order = fields.Float(string="Emergency 1 Hour (per order)", default=0.0, digits=(12, 2))
    weekend_order = fields.Float(string="Weekend (per order)", default=0.0, digits=(12, 2))
    holiday_order = fields.Float(string="Holiday (per order)", default=0.0, digits=(12, 2))

    # Working hours
    working_hours_start = fields.Float(string="Working Hours Start", default=8.0)
    working_hours_end = fields.Float(string="Working Hours End", default=17.0)

    # State management
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string='State', default='draft', tracking=True)

    # Description and notes
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")

    @api.model
    def get_current_rates(self):
        """Get the currently active rate plan"""
        return self.search([
            ('state', '=', 'active'),
            ('effective_date', '<=', fields.Date.today())
        ], limit=1, order='effective_date desc')

    def action_activate(self):
        """Activate this rate plan and deactivate others"""
        # Deactivate all other rate plans
        other_rates = self.search([('id', '!=', self.id), ('state', '=', 'active')])
        other_rates.write({'state': 'archived'})
        
        # Activate this one
        self.write({'state': 'active'})
        
        return True

    def action_archive(self):
        """Archive this rate plan"""
        self.write({'state': 'archived'})

    def action_draft(self):
        """Set to draft"""
        self.write({'state': 'draft'})

    @api.depends('name', 'effective_date')
    def _compute_display_name(self):
        for record in self:
            if record.effective_date:
                record.display_name = f"{record.name} ({record.effective_date})"
            else:
                record.display_name = record.name
