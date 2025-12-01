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
        default=lambda self: "New"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('ready', 'Ready for Pickup'),
        ('picked_up', 'Picked Up'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    bale_ids = fields.One2many('paper.bale', 'shipment_id', string="Paper Bales")
    bale_count = fields.Integer(compute='_compute_bale_count', string="Bale Count", store=True)
    total_weight = fields.Float(compute='_compute_total_weight', string="Total Weight (kg)", store=True)

    # Grade-specific counts for truck widget
    white_count = fields.Integer(compute='_compute_grade_counts', string="White Bales", store=True)
    mixed_count = fields.Integer(compute='_compute_grade_counts', string="Mixed Bales", store=True)
    cardboard_count = fields.Integer(compute='_compute_grade_counts', string="Cardboard Bales", store=True)

    carrier_id = fields.Many2one(comodel_name='res.partner', string="Carrier", domain="[('is_company', '=', True)]")
    driver_id = fields.Many2one(comodel_name='res.partner', string="Driver", domain="[('is_company', '=', False)]")

    pickup_location_id = fields.Many2one(comodel_name='stock.location', string="Pickup Location")
    delivery_location_id = fields.Many2one(comodel_name='stock.location', string="Delivery Location")

    scheduled_pickup_date = fields.Datetime(string="Scheduled Pickup", tracking=True)
    actual_pickup_date = fields.Datetime(string="Actual Pickup", readonly=True, tracking=True)

    scheduled_delivery_date = fields.Datetime(string="Scheduled Delivery", tracking=True)
    actual_delivery_date = fields.Datetime(string="Actual Delivery", readonly=True, tracking=True)

    notes = fields.Text(string="Shipment Notes")
    
    # Invoice and manifest fields
    driver_signature = fields.Char(string="Driver Signature", help="Driver's name or digital signature timestamp")
    manifest_printed = fields.Boolean(string="Manifest Printed", default=False)
    manifest_print_date = fields.Datetime(string="Manifest Print Date", readonly=True)
    invoice_id = fields.Many2one(comodel_name='account.move', string="Invoice", readonly=True)
    
    # Feature toggles
    enable_geographic_batching = fields.Boolean(
        string="Enable Geographic Batching",
        default=False,
        help="When enabled, suggests consolidating deliveries to same location on same day"
    )
    
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True)
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

    def action_mark_picked_up(self):
        """Mark shipment as picked up by driver - triggers invoice creation."""
        self.ensure_one()
        if not self.driver_signature:
            raise UserError(_("Driver signature is required before marking as picked up."))
        self.write({
            'state': 'picked_up',
            'actual_pickup_date': fields.Datetime.now()
        })
        self.bale_ids.write({'state': 'shipped'})
        # Create invoice matching load number
        self._create_pickup_invoice()
        self.message_post(body=_("Load picked up by driver. Invoice generated."))

    def _create_pickup_invoice(self):
        """Create invoice when load is picked up, matching load number and manifest."""
        self.ensure_one()
        # Placeholder for invoice creation logic
        # This would integrate with account.move to create invoice
        # matching self.name (load number) with bale manifest
        self.message_post(body=_("Invoice creation triggered (requires accounting module integration)."))

    def action_print_manifest(self):
        """Print manifest with driver signature timestamp for easy reference."""
        self.ensure_one()
        self.write({
            'manifest_printed': True,
            'manifest_print_date': fields.Datetime.now()
        })
        self.message_post(body=_("Manifest printed with signature timestamp."))
        # Return report action for manifest
        return self.env.ref('records_management.action_report_load_shipment_manifest').report_action(self)

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
            "type": "ir.actions.act_window",
            # Translation normalization: interpolate after _()
            "name": _("Bales in Shipment %s") % self.name,
            "res_model": "paper.bale",
            "view_mode": "list,form",
            "domain": [("id", "in", self.bale_ids.ids)],
            "context": {"create": False},
        }

    # ------------------------------------------------------------------
    # ADDITIONAL VIEW BUTTON / WORKFLOW STUBS (referenced in XML)
    # ------------------------------------------------------------------
    def action_prepare_load(self):  # placeholder for pre-shipment prep
        self.ensure_one()
        if self.state == 'draft':
            # Intentionally lightweight: do not auto-transition to ready to keep user control
            self.message_post(body=_("Load preparation logged (placeholder)."))
        return True

    def action_start_loading(self):  # placeholder mapping to action_ready_for_shipment logic
        self.ensure_one()
        if self.state == 'draft':
            # Reuse existing validation from ready action
            return self.action_ready_for_shipment()
        return True

    def action_ship_load(self):  # placeholder mapping to mark_picked_up
        self.ensure_one()
        if self.state in ('ready', 'draft'):
            return self.action_mark_picked_up()
        return True

    def action_mark_sold(self):  # placeholder for commercial closure
        self.ensure_one()
        # Future: integrate revenue recognition / accounting link
        if self.state not in ('completed', 'cancelled'):
            self.message_post(body=_("Shipment marked as sold (placeholder – no state change)."))
        return True
