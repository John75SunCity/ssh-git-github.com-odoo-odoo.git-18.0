from odoo import models, fields, api

class PickupLocation(models.Model):
    _name = 'pickup.location'
    _description = 'Pickup Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Location Name', 
        required=True, 
        tracking=True,
        help="Name of the pickup location"
    )
    address = fields.Char(
        string='Address',
        help="Street address of the pickup location"
    )
    city = fields.Char(string='City')
    state_id = fields.Many2one(
        comodel_name='res.country.state', 
        string='State'
    )
    zip = fields.Char(string='ZIP / Postal Code')
    country_id = fields.Many2one(
        comodel_name='res.country', 
        string='Country',
        default=lambda self: self.env.company.country_id
    )
    
    # Status and Management
    active = fields.Boolean(
        default=True,
        help="Uncheck to hide this location without deleting it"
    )
    company_id = fields.Many2one(
        comodel_name='res.company', 
        string='Company', 
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        comodel_name='res.users', 
        string='Location Manager', 
        default=lambda self: self.env.user,
        tracking=True
    )
    notes = fields.Text(string='Notes')
    
    # Computed Fields
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )
    
    @api.depends('name', 'city', 'state_id')
    def _compute_display_name(self):
        """Compute a user-friendly display name.

        Robust against new (unsaved) records where fields may be empty so that
        core tests (TestEveryModel.test_display_name_new_record) do not fail.
        Fallback order:
          1. name (+ optional city/state components)
          2. city/state if name absent
          3. Generic translated label.
        """
        for record in self:
            base = record.name or ''
            parts = []
            if base:
                parts.append(base)
            if record.city:
                parts.append(record.city)
            if record.state_id:
                parts.append(record.state_id.code or record.state_id.name)

            if not parts:
                record.display_name = _('Pickup Location')
            else:
                record.display_name = ', '.join(parts)
    
    @api.onchange('country_id')
    def _onchange_country_id(self):
        """Clear state when country changes"""
        if self.country_id and self.state_id.country_id != self.country_id:
            self.state_id = False
    
    # Deprecated name_get: rely on computed display_name for Odoo 18
