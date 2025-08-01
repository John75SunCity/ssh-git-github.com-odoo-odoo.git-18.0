# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class UnlockServiceHistory(models.Model):
    _name = 'unlock.service.history'
    _description = 'Unlock Service History'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date_created desc'
    _rec_name = 'service_type'

    # Related Partner Bin Key (the inverse field that was missing)
    partner_bin_key_id = fields.Many2one(
        'partner.bin.key', 
        string='Partner Bin Key', 
        required=True, 
        ondelete='cascade',
        tracking=True
    )

    # Service details
    service_type = fields.Selection([
        ('unlock', 'Unlock Service'),
        ('reset', 'Reset Service'),
        ('maintenance', 'Maintenance Service'),
        ('emergency', 'Emergency Access')
    ], string='Service Type', required=True, tracking=True)

    # User who performed the service
    user_id = fields.Many2one(
        'res.users', 
        string='Service User', 
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    # Timestamps
    date_created = fields.Datetime(
        string='Service Date', 
        default=fields.Datetime.now,
        required=True
    )

    # Service details
    notes = fields.Text(string='Service Notes')
    success = fields.Boolean(string='Service Successful', default=True)
    cost = fields.Float(string='Service Cost')

    # Company
    company_id = fields.Many2one(
        'res.company', 
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    # Control fields
    active = fields.Boolean(default=True)

    # Computed fields
    display_name = fields.Char(
        string='Display Name', 
        compute='_compute_display_name', 
        store=True
    )

    @api.depends('service_type', 'date_created', 'partner_bin_key_id')
    def _compute_display_name(self):
        """Compute display name for service history records."""
        for record in self:
            if record.service_type and record.date_created:
                service_display = dict(record._fields['service_type'].selection).get(record.service_type, '')
                date_str = record.date_created.strftime('%Y-%m-%d %H:%M')
                record.display_name = f"{service_display} - {date_str}"
            else:
                record.display_name = _('New Service Entry')
