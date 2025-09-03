from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingRate(models.Model):
    _name = 'shredding.rate'
    _description = 'Shredding Rate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Rate Name', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    partner_id = fields.Many2one('res.partner', string="Customer", help="Specify a customer for a negotiated rate. Leave empty for a base rate.")
    service_id = fields.Many2one('shredding.service', string="Service", required=True, help="The shredding service this rate applies to.")

    # ============================================================================
    # RATE & PRICING FIELDS
    # ============================================================================
    rate = fields.Float(string="Rate", digits='Product Price', required=True, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency', related='company_id.currency_id', readonly=True)
    uom_id = fields.Many2one('uom.uom', string="Unit of Measure", help="Unit of Measure for the service.")

    # ============================================================================
    # STATUS & LIFECYCLE FIELDS
    # ============================================================================
    active = fields.Boolean(string='Active', default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('expired', 'Expired')
    ], string='Status', default='draft', required=True, tracking=True)

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # ============================================================================
    # COMPUTED & CONSTRAINT METHODS
    # ============================================================================
    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_("The start date cannot be later than the end date."))

    @api.constrains('rate')
    def _check_rate(self):
        for record in self:
            if record.rate < 0:
                raise ValidationError(_("The rate cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        """Activate the rate"""
        self.ensure_one()
        self.write({'state': 'active'})

    def action_expire(self):
        """Mark the rate as expired"""
        self.ensure_one()
        self.write({'state': 'expired'})

    def action_reset_to_draft(self):
        """Reset the rate to draft state"""
        self.ensure_one()
        self.write({'state': 'draft'})

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def get_effective_rate(self, partner_id=None, date=None):
        """
        Get the effective rate for a customer and date

        Args:
            partner_id: Customer ID (optional)
            date: Effective date (optional, defaults to today)

        Returns:
            float: The effective rate
        """
        if not date:
            date = fields.Date.today()

        domain = [
            ('service_id', '=', self.service_id.id),
            ('state', '=', 'active'),
            '|', ('start_date', '<=', date), ('start_date', '=', False),
            '|', ('end_date', '>=', date), ('end_date', '=', False)
        ]

        # First try to find customer-specific rate
        if partner_id:
            customer_domain = domain + [('partner_id', '=', partner_id)]
            customer_rate = self.search(customer_domain, limit=1)
            if customer_rate:
                return customer_rate.rate

        # Fall back to base rate (no customer specified)
        base_domain = domain + [('partner_id', '=', False)]
        base_rate = self.search(base_domain, limit=1)
        if base_rate:
            return base_rate.rate

        return 0.0
