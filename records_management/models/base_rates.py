from odoo import fields, models, api

class BaseRates(models.Model):
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
    currency_id = fields.Many2one('res.currency', string='Currency',
                                 default=lambda self: self.env.company.currency_id, required=True)
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
    effective_date = fields.Date(string='Effective Date', required=True, default=fields.Date.context_today, tracking=True)
    expiry_date = fields.Date(string='Expiry Date', tracking=True)
    minimum_charge = fields.Float(string='Minimum Charge', default=0.0)
    maximum_charge = fields.Float(string='Maximum Charge')

    # Additional fields
    description = fields.Text(string='Description')
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
