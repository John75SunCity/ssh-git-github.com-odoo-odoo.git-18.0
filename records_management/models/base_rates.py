"""
Base Rates Model

Defines the base rates for various records management services such as storage, retrieval,
destruction, transportation, and scanning. Each rate is associated with a unit type, currency,
validity period, and company. This model enables flexible pricing configuration for all core
service types in the Records Management system.
"""

from odoo import api, fields, models, _

class BaseRates(models.Model):
    """
    BaseRates

    Stores the configuration for base rates used in records management billing.
    Supports multiple rate types, unit types, and validity periods. Rates are
    company-specific and can be activated or deactivated as needed.
    """

    _name = 'base.rates'
    _description = 'Base Rates'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char(string='Rate Name', required=True, tracking=True)
    rate_type = fields.Selection([
        ('storage', 'Storage Rate'),
        ('retrieval', 'Retrieval Rate'),
        ('destruction', 'Destruction Rate'),
        ('transportation', 'Transportation Rate'),
        ('scanning', 'Scanning Rate'),
        ('other', 'Other')
    ], string='Rate Type', required=True, default='storage', tracking=True)

    # Rate values
    base_rate = fields.Float(string='Base Rate', required=True, tracking=True)
    currency_id = fields.Many2one(
        comodel_name='res.currency', 
        string='Currency',
        default=lambda self: self.env.company.currency_id, 
        required=True
    )
    unit_type = fields.Selection([
        ('per_box', 'Per Box'),
        ('per_cubic_foot', 'Per Cubic Foot'),
        ('per_hour', 'Per Hour'),
        ('per_day', 'Per Day'),
        ('per_month', 'Per Month'),
        ('per_year', 'Per Year'),
        ('per_item', 'Per Item'),
        ('flat_rate', 'Flat Rate')
    ], string='Unit Type', required=True, default='per_box', tracking=True)

    # Validity and conditions
    effective_date = fields.Date(
        string='Effective Date', 
        required=True, 
        default=fields.Date.context_today, 
        tracking=True
    )
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    minimum_charge = fields.Float(string='Minimum Charge', default=0.0)
    maximum_charge = fields.Float(string='Maximum Charge')

    # Additional fields
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name='res.company', 
        string='Company', 
        default=lambda self: self.env.company, 
        required=True
    )

    @api.constrains('effective_date', 'expiry_date')
    def _check_date_validity(self):
        """Ensure expiry date is after effective date"""
        for record in self:
            if record.expiry_date and record.effective_date:
                if record.expiry_date <= record.effective_date:
                    raise ValueError(_("Expiry date must be after effective date"))

    @api.constrains('base_rate', 'minimum_charge', 'maximum_charge')
    def _check_rate_values(self):
        """Validate rate values are positive and logical"""
        for record in self:
            if record.base_rate < 0:
                raise ValueError(_("Base rate must be positive"))
            if record.minimum_charge < 0:
                raise ValueError(_("Minimum charge must be positive"))
            if record.maximum_charge and record.maximum_charge < record.minimum_charge:
                raise ValueError(_("Maximum charge must be greater than minimum charge"))

    def name_get(self):
        """Return descriptive name for selection fields"""
        result = []
        for record in self:
            name = "%s (%s)" % (record.name, dict(record._fields['rate_type'].selection).get(record.rate_type))
            result.append((record.id, name))
        return result
