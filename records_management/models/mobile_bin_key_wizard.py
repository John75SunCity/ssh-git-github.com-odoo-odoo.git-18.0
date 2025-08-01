# -*- coding: utf-8 -*-
"""
Mobile Bin Key Management Wizard
"""

from odoo import models, fields, api, _


class MobileBinKeyWizard(models.Model):
    """
    Mobile Bin Key Management Wizard
    """

    _name = "mobile.bin.key.wizard"
    _description = "Mobile Bin Key Management Wizard"
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
    action_execute = fields.Char(string='Action Execute')
    action_type = fields.Selection([], string='Action Type')  # TODO: Define selection options
    billable = fields.Boolean(string='Billable', default=False)
    bin_locations = fields.Char(string='Bin Locations')
    code = fields.Char(string='Code')
    contact_email = fields.Char(string='Contact Email')
    contact_id = fields.Many2one('res.partner', string='Contact')
    contact_mobile = fields.Char(string='Contact Mobile')
    contact_name = fields.Char(string='Contact Name')
    contact_phone = fields.Char(string='Contact Phone')
    contact_title = fields.Char(string='Contact Title')
    context = fields.Char(string='Context')
    create_new_contact = fields.Char(string='Create New Contact')
    customer_company_id = fields.Many2one('res.partner', string='Customer Company')
    emergency_contact = fields.Char(string='Emergency Contact')
    issue_location = fields.Char(string='Issue Location')
    items_retrieved = fields.Char(string='Items Retrieved')
    key_lookup_results = fields.Char(string='Key Lookup Results')
    key_notes = fields.Char(string='Key Notes')
    # model_id = fields.Many2one('model', string='Model Id')  # TODO: Define model or remove
    photo_ids = fields.One2many('photo', 'mobile_bin_key_wizard_id', string='Photo Ids')
    res_model = fields.Char(string='Res Model')
    service_notes = fields.Char(string='Service Notes')
    show_contact_creation = fields.Char(string='Show Contact Creation')
    show_key_assignment = fields.Char(string='Show Key Assignment')
    show_lookup_results = fields.Char(string='Show Lookup Results')
    show_unlock_service = fields.Char(string='Show Unlock Service')
    target = fields.Char(string='Target')
    unlock_bin_location = fields.Char(string='Unlock Bin Location')
    unlock_charge = fields.Char(string='Unlock Charge')
    unlock_reason = fields.Char(string='Unlock Reason')
    unlock_reason_description = fields.Char(string='Unlock Reason Description')
    view_mode = fields.Char(string='View Mode')

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})

    def action_execute(self):
        """Execute the mobile bin key action"""
        self.ensure_one()
        # Implementation based on action_type field
        action_type = getattr(self, 'action_type', 'quick_lookup')

        if action_type == 'quick_lookup':
            # Refresh lookup data
            self.message_post(body=_('Lookup data refreshed'))
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'mobile.bin.key.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        else:
            # Execute other actions
            self.write({'state': 'done'})
            self.message_post(body=_('Mobile bin key action executed'))
            return {'type': 'ir.actions.act_window_close'}
