# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError

class PaperLoadShipment(models.Model):
    """
    Manages the shipment of multiple paper bales, typically to a recycling facility.
    This model acts as a container for bales being transported, tracking key details
    like the carrier, destination, dates, and total weight. It serves as the
    primary record for logistical and financial aspects of paper recycling.
    """
    _name = 'paper.load.shipment'
    _description = 'Paper Load Shipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_delivery_date desc, name desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(
        string="Shipment Reference",
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready for Shipment'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    bale_ids = fields.One2many('paper.bale', 'shipment_id', string="Paper Bales")
    bale_count = fields.Integer(compute='_compute_bale_count', string="Bale Count", store=True)
    total_weight = fields.Float(compute='_compute_total_weight', string="Total Weight (kg)", store=True)

    # Grade-specific counts for truck widget
    white_count = fields.Integer(compute='_compute_grade_counts', string="White Bales", store=True)
    mixed_count = fields.Integer(compute='_compute_grade_counts', string="Mixed Bales", store=True)
    cardboard_count = fields.Integer(compute='_compute_grade_counts', string="Cardboard Bales", store=True)

    carrier_id = fields.Many2one('res.partner', string="Carrier", domain="[('is_company', '=', True)]")
    driver_id = fields.Many2one('res.partner', string="Driver", domain="[('is_company', '=', False)]")

    pickup_location_id = fields.Many2one('stock.location', string="Pickup Location")
    delivery_location_id = fields.Many2one('stock.location', string="Delivery Location")

    scheduled_pickup_date = fields.Datetime(string="Scheduled Pickup", tracking=True)
    actual_pickup_date = fields.Datetime(string="Actual Pickup", readonly=True, tracking=True)

    scheduled_delivery_date = fields.Datetime(string="Scheduled Delivery", tracking=True)
    actual_delivery_date = fields.Datetime(string="Actual Delivery", readonly=True, tracking=True)

    notes = fields.Text(string="Shipment Notes")
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('bale_ids')
    def _compute_bale_count(self):
        for shipment in self:
            shipment.bale_count = len(shipment.bale_ids)

    @api.depends('bale_ids.weight')
    def _compute_total_weight(self):
        for shipment in self:
            shipment.total_weight = sum(bale.weight for bale in shipment.bale_ids)

    @api.depends('bale_ids.paper_grade')
    def _compute_grade_counts(self):
        """Compute counts by paper grade for truck widget visualization."""
        for shipment in self:
            bales = shipment.bale_ids
            shipment.white_count = len(bales.filtered(lambda b: b.paper_grade == 'wht'))
            shipment.mixed_count = len(bales.filtered(lambda b: b.paper_grade == 'mix'))
            shipment.cardboard_count = len(bales.filtered(lambda b: b.paper_grade == 'occ'))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Overrides create to assign a unique sequential name."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.load.shipment') or _('New')
        return super().create(vals_list)

    def unlink(self):
        """
        Prevents deletion of shipments that are not in a draft or cancelled state.
        Also unlinks bales from the shipment before deletion.
        """
        for shipment in self:
            if shipment.state not in ('draft', 'cancelled'):
                raise UserError(_("You can only delete shipments that are in draft or cancelled state."))
            shipment.bale_ids.write({'shipment_id': False})
        return super().unlink()

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_ready_for_shipment(self):
        self.ensure_one()
        if not self.bale_ids:
            raise UserError(_("You cannot mark a shipment as ready without any bales."))
        self.write({'state': 'ready'})
        self.message_post(body=_("Shipment is now ready."))

    def action_start_transit(self):
        self.ensure_one()
        self.write({
            'state': 'in_transit',
            'actual_pickup_date': fields.Datetime.now()
        })
        self.bale_ids.write({'state': 'shipped'})
        self.message_post(body=_("Shipment is now in transit."))

    def action_deliver(self):
        self.ensure_one()
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Datetime.now()
        })
        self.message_post(body=_("Shipment has been delivered."))

    def action_complete(self):
        """
        Marks the shipment as completed and updates the state of all associated
        bales to 'recycled'.
        """
        self.ensure_one()
        self.write({'state': 'completed'})
        self.bale_ids.write({'state': 'recycled'})
        self.message_post(body=_("Shipment completed. All bales marked as recycled."))

    def action_cancel(self):
        """
        Cancels the shipment and unlinks all associated bales, returning them
        to the 'in_stock' state.
        """
        self.ensure_one()
        self.bale_ids.write({'state': 'in_stock', 'shipment_id': False})
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Shipment cancelled. Bales have been returned to stock."))

    def action_view_bales(self):
        """Returns an action to view the bales associated with this shipment."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Bales in Shipment %s') % self.name,
            'res_model': 'paper.bale',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.bale_ids.ids)],
            'context': {'create': False},
        }
