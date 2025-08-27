from odoo import models, fields, api, _
from odoo.exceptions import UserError


class Load(models.Model):
    _name = 'load'
    _description = 'Paper Bale Load Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_ship_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Load Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one('res.company', string='Company', required=True, default=lambda self: self.env.company)
    priority = fields.Selection([('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')
    user_id = fields.Many2one('res.users', string='Load Coordinator', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('loading', 'Loading'),
        ('ready_for_pickup', 'Ready for Pickup'),
        ('picked_up', 'Picked Up'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True, copy=False)

    # Logistical Information
    pickup_date = fields.Date(string='Pickup Date')
    driver_name = fields.Char(string="Driver's Name")
    driver_signature = fields.Binary(string="Driver's Signature", attachment=True)

    # Destination
    buyer_id = fields.Many2one('res.partner', string='Buyer/Recycling Center', domain="[('is_company', '=', True)]")

    # Contents
    paper_bale_ids = fields.One2many('paper.bale', 'load_id', string='Paper Bales')
    total_bales = fields.Integer(string='Total Bales', compute='_compute_load_stats', store=True)
    total_weight = fields.Float(string='Total Weight (lbs)', compute='_compute_load_stats', store=True)

    # Computed Weight Totals by Paper Type
    total_weight_wht = fields.Float(string='WHT Weight (lbs)', compute='_compute_weight_by_type', store=True)
    total_weight_mix = fields.Float(string='MIX Weight (lbs)', compute='_compute_weight_by_type', store=True)
    total_weight_occ = fields.Float(string='OCC Weight (lbs)', compute='_compute_weight_by_type', store=True)

    # Financials & Payment
    currency_id = fields.Many2one('res.currency', related='company_id.currency_id', store=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True, copy=False)
    payment_status = fields.Selection(related='invoice_id.payment_state', string="Payment Status", readonly=True, store=True)

    # Attachments
    manifest_document = fields.Binary(string='Load Manifest', readonly=True, copy=False, attachment=True)
    manifest_filename = fields.Char(string="Manifest Filename", readonly=True, copy=False)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale.load') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('paper_bale_ids', 'paper_bale_ids.weight')
    def _compute_load_stats(self):
        for load in self:
            load.total_bales = len(load.paper_bale_ids)
            load.total_weight = sum(load.paper_bale_ids.mapped('weight'))

    @api.depends('paper_bale_ids', 'paper_bale_ids.weight', 'paper_bale_ids.paper_type')
    def _compute_weight_by_type(self):
        for load in self:
            load.total_weight_wht = sum(b.weight for b in load.paper_bale_ids if b.paper_type == 'wht')
            load.total_weight_mix = sum(b.weight for b in load.paper_bale_ids if b.paper_type == 'mix')
            load.total_weight_occ = sum(b.weight for b in load.paper_bale_ids if b.paper_type == 'occ')

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_ready_for_pickup(self):
        self.ensure_one()
        if not self.paper_bale_ids:
            raise UserError(_("You cannot mark a load as ready without any bales."))
        self.write({'state': 'ready_for_pickup'})

    def action_mark_picked_up(self):
        self.ensure_one()
        self.write({'state': 'picked_up', 'pickup_date': fields.Date.context_today(self)})

    def action_generate_manifest(self):
        self.ensure_one()
        # This will be the action to trigger the PDF report
        return self.env.ref('records_management.action_report_load_manifest').report_action(self)

    def action_create_invoice(self):
        self.ensure_one()
        if self.invoice_id:
            raise UserError(_("An invoice has already been created for this load."))
        if not self.buyer_id:
            raise UserError(_("Please select a Buyer/Recycling Center before creating an invoice."))

        invoice_lines = []
        # This is a simplified example. You would likely have products for each paper type.
        product_map = {
            'wht': self.env.ref('records_management.product_paper_wht', raise_if_not_found=False),
            'mix': self.env.ref('records_management.product_paper_mix', raise_if_not_found=False),
            'occ': self.env.ref('records_management.product_paper_occ', raise_if_not_found=False),
        }

        if self.total_weight_wht > 0:
            product = product_map.get('wht')
            if not product: raise UserError(_("Product for 'WHT' paper not found."))
            invoice_lines.append((0, 0, {
                'product_id': product.id,
                'name': _('White Paper Scrap'),
                'quantity': self.total_weight_wht,
                'product_uom_id': product.uom_id.id,
                'price_unit': product.list_price,
            }))

        if self.total_weight_mix > 0:
            product = product_map.get('mix')
            if not product: raise UserError(_("Product for 'MIX' paper not found."))
            invoice_lines.append((0, 0, {
                'product_id': product.id,
                'name': _('Mixed Paper Scrap'),
                'quantity': self.total_weight_mix,
                'product_uom_id': product.uom_id.id,
                'price_unit': product.list_price,
            }))

        if self.total_weight_occ > 0:
            product = product_map.get('occ')
            if not product: raise UserError(_("Product for 'OCC' paper not found."))
            invoice_lines.append((0, 0, {
                'product_id': product.id,
                'name': _('Cardboard/OCC Scrap'),
                'quantity': self.total_weight_occ,
                'product_uom_id': product.uom_id.id,
                'price_unit': product.list_price,
            }))

        if not invoice_lines:
            raise UserError(_("There is nothing to invoice for this load."))

        invoice = self.env['account.move'].create({
            'move_type': 'out_invoice',
            'partner_id': self.buyer_id.id,
            'invoice_date': fields.Date.context_today(self),
            'invoice_line_ids': invoice_lines,
            'ref': self.name,
        })

        self.write({'invoice_id': invoice.id, 'state': 'invoiced'})

        return {
            'type': 'ir.actions.act_window',
            'name': _('Customer Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_cancel(self):
        self.ensure_one()
        if self.invoice_id and self.invoice_id.state != 'cancel':
            raise UserError(_("You must cancel the related invoice first."))
        self.write({'state': 'cancel'})

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
