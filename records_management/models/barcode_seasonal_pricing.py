from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class BarcodeSeasonalPricing(models.Model):
    _name = 'barcode.seasonal.pricing'
    _description = 'Barcode Seasonal Pricing'
    _order = 'start_date desc'

    name = fields.Char(string='Name', required=True, index=True, help='Display name for this seasonal pricing window.')
    product_id = fields.Many2one(comodel_name='barcode.product', string='Barcode Product', required=True, ondelete='cascade')
    season_name = fields.Char(string='Season Name', required=True, help='Logical label for the season (e.g., Peak Q4, Summer).')
    start_date = fields.Date(string='Start Date', required=True)
    end_date = fields.Date(string='End Date', required=True)
    price_multiplier = fields.Float(string='Price Multiplier', default=1.0, help='Applied against base rate fields during this season.')
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('expired', 'Expired'),
    ], string='Status', default='draft', required=True, tracking=True)
    notes = fields.Text(string='Internal Notes')

    _sql_constraints = [
        ('price_multiplier_positive', 'CHECK(price_multiplier > 0)', 'Multiplier must be greater than zero.'),
    ]

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for rec in self:
            if rec.start_date and rec.end_date and rec.end_date < rec.start_date:
                raise ValidationError(_('End date must be after start date.'))

    def action_confirm(self):
        """Move record to confirmed state."""
        self.ensure_one()
        if self.state != 'confirmed':
            self.state = 'confirmed'
        return True

    def action_expire(self):
        """Manually mark record as expired."""
        self.ensure_one()
        if self.state != 'expired':
            self.state = 'expired'
        return True
