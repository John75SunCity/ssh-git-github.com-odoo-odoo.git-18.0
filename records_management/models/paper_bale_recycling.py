# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PaperBaleRecycling(models.Model):
    """
    Represents the final stage of a paper bale's lifecycle: recycling.
    This model tracks the processing of a bale at a recycling facility,
    capturing key data such as processing dates, costs, revenues, and
    environmental impact metrics. It provides a comprehensive record of the
    recycling outcome for each bale.
    """
    _name = 'paper.bale.recycling'
    _description = 'Paper Bale Recycling Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'processing_date desc, name desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string="Recycling Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    bale_id = fields.Many2one(
        'paper.bale',
        string='Paper Bale',
        required=True,
        ondelete='restrict',
        index=True,
        help="The specific paper bale that was recycled."
    )
    shipment_id = fields.Many2one(
        'paper.load.shipment',
        string="Shipment",
        related='bale_id.shipment_id',
        store=True,
        help="The shipment that transported this bale to the facility."
    )
    recycling_facility_id = fields.Many2one(
        'res.partner',
        string="Recycling Facility",
        domain="[('is_company', '=', True)]",
        help="The facility where the bale was processed."
    )

    processing_date = fields.Date(string="Processing Date", tracking=True)
    collection_date = fields.Date(string="Collection Date", tracking=True, help="Date when the bale was collected for recycling.")
    bale_weight = fields.Float(string="Bale Weight (kg)", related='bale_id.weight', store=True, help="Weight of the recycled bale.")
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='pending', tracking=True, required=True)

    # Financial Fields
    currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id')
    market_price_per_ton = fields.Monetary(string="Market Price per Ton", currency_field="currency_id", tracking=True)
    total_revenue = fields.Monetary(
        compute="_compute_financials", string="Total Revenue", currency_field="currency_id", store=True
    )
    processing_cost = fields.Monetary(string="Processing Cost", currency_field="currency_id", tracking=True)
    net_profit = fields.Monetary(
        compute="_compute_financials", string="Net Profit", currency_field="currency_id", store=True
    )

    # Environmental Impact Fields
    carbon_footprint_reduction = fields.Float(string="CO2 Reduction (kg)", help="Estimated carbon footprint reduction.")
    water_savings = fields.Float(string="Water Savings (Liters)", help="Estimated water savings.")
    energy_savings = fields.Float(string="Energy Savings (kWh)", help="Estimated energy savings.")

    notes = fields.Text(string="Recycling Notes")
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('bale_id.weight', 'market_price_per_ton', 'processing_cost')
    def _compute_financials(self):
        """
        Calculates the total revenue and net profit for the recycling process.
        Assumes bale weight is in kg and converts it to metric tons.
        """
        for record in self:
            if record.bale_id.weight > 0 and record.market_price_per_ton > 0:
                weight_in_tons = record.bale_id.weight / 1000.0
                revenue = weight_in_tons * record.market_price_per_ton
                record.total_revenue = revenue
                record.net_profit = revenue - record.processing_cost
            else:
                record.total_revenue = 0.0
                record.net_profit = -record.processing_cost

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to assign a unique sequential name."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.recycling') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_process(self):
        """Marks the recycling record as processed."""
        self.ensure_one()
        if self.state != 'pending':
            raise ValidationError(_("Only pending records can be processed."))
        self.write({'state': 'processed'})
        self.message_post(body=_("Recycling record marked as processed."))

    def action_cancel(self):
        """Cancels the recycling record."""
        self.ensure_one()
        if self.state == 'processed':
            raise ValidationError(_("Cannot cancel a record that has already been processed."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Recycling record has been cancelled."))
