# -*- coding: utf-8 -*-
"""
Bin Key Management
"""

from odoo import models, fields, api, _


class BinKeyManagement(models.Model):
    """
    Bin Key Management
    """

    _name = "bin.key.management"
    _description = "Bin Key Management"
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
        ('confirmed', 'Confirmed'),
        ('done', 'Done')
    ], string='State', default='draft', tracking=True)

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    action_create_invoice = fields.Char(string='Action Create Invoice')
    action_mark_completed = fields.Boolean(string='Action Mark Completed', default=False)
    action_mark_lost = fields.Char(string='Action Mark Lost')
    action_replace_key = fields.Char(string='Action Replace Key')
    action_return_key = fields.Char(string='Action Return Key')
    action_view_unlock_services = fields.Char(string='Action View Unlock Services')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    billable = fields.Boolean(string='Billable', default=False)
    bin_location = fields.Char(string='Bin Location')
    bin_locations = fields.Char(string='Bin Locations')
    button_box = fields.Char(string='Button Box')
    charge_amount = fields.Float(string='Charge Amount', digits=(12, 2))
    completed = fields.Boolean(string='Completed', default=False)
    context = fields.Char(string='Context')
    emergency_contact = fields.Char(string='Emergency Contact')
    expected_return_date = fields.Date(string='Expected Return Date')
    help = fields.Char(string='Help')
    invoice_created = fields.Char(string='Invoice Created')
    issue_date = fields.Date(string='Issue Date')
    issue_location = fields.Char(string='Issue Location')
    items_retrieved = fields.Char(string='Items Retrieved')
    key_holder_id = fields.Many2one('key.holder', string='Key Holder Id')
    key_number = fields.Char(string='Key Number')
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    partner_company = fields.Char(string='Partner Company')
    partner_id = fields.Many2one('res.partner', string='Partner Id')
    photo_ids = fields.One2many('photo', 'bin_key_management_id', string='Photo Ids')
    reason_description = fields.Char(string='Reason Description')
    replaced_by_id = fields.Many2one('replaced.by', string='Replaced By Id')
    replacement_of_id = fields.Many2one('replacement.of', string='Replacement Of Id')
    res_model = fields.Char(string='Res Model')
    return_date = fields.Date(string='Return Date')
    service_date = fields.Date(string='Service Date')
    service_number = fields.Char(string='Service Number')
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress'), ('completed', 'Completed')], string='Status', default='new')
    technician_id = fields.Many2one('technician', string='Technician Id')
    unlock_reason = fields.Char(string='Unlock Reason')
    unlock_service_count = fields.Integer(string='Unlock Service Count', compute='_compute_unlock_service_count', store=True)
    unlock_service_ids = fields.One2many('unlock.service', 'bin_key_management_id', string='Unlock Service Ids')
    view_mode = fields.Char(string='View Mode')

    @api.depends('unlock_service_ids')
    def _compute_unlock_service_count(self):
        for record in self:
            record.unlock_service_count = len(record.unlock_service_ids)

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
