from odoo import models, fields, api, _

class CustomerBillingProfile(models.Model):
    _name = 'customer.billing.profile'
    _description = 'Customer Billing Profile'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Profile Name', compute='_compute_name', store=True, help='Computed name based on customer and profile type')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    profile_type = fields.Selection([
        ('standard', 'Standard Billing'),
        ('prepaid', 'Prepaid'),
        ('contract', 'Contract Based'),
        ('custom', 'Custom Billing')
    ], string='Profile Type', default='standard', required=True, tracking=True)

    @api.depends('partner_id.name', 'profile_type')
    def _compute_name(self):
        for profile in self:
            if profile.partner_id and profile.profile_type:
                type_label = dict(profile._fields['profile_type'].selection).get(profile.profile_type, 'Billing')
                profile.name = _("%s - %s Profile") % (profile.partner_id.name, type_label)
            elif profile.partner_id:
                profile.name = _("%s - Billing Profile") % profile.partner_id.name
            else:
                profile.name = _("New Billing Profile")
