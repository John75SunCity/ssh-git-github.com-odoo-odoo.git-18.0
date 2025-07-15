# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow, including hard drives and uniforms."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, name'

    name = fields.Char(string='Service Reference', required=True, default='New', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    service_date = fields.Date(string='Service Date', default=fields.Date.today, tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'), ('box', 'Box Shredding'),
        ('hard_drive', 'Hard Drive Destruction'), ('uniform', 'Uniform Shredding')
    ], string='Service Type', required=True, tracking=True)  # Expanded for new services
    bin_ids = fields.Many2many('stock.lot', string='Serviced Bins', domain="[('product_id.name', '=', 'Shredding Bin')]")
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many('stock.lot', string='Shredded Boxes', domain="[('customer_id', '!=', False)]")
    hard_drive_quantity = fields.Integer(string='Number of Hard Drives')  # New
    uniform_quantity = fields.Integer(string='Number of Uniforms')  # New
    total_boxes = fields.Integer(compute='_compute_total_boxes', store=True)
    unit_cost = fields.Float(string='Unit Cost', default=5.0)
    total_cost = fields.Float(compute='_compute_total_cost', store=True)
    notes = fields.Text(string='Notes')
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    audit_barcodes = fields.Text(string='Audit Barcodes')
    total_charge = fields.Float(compute='_compute_total_charge', store=True)
    timestamp = fields.Datetime(default=fields.Datetime.now)
    latitude = fields.Float()
    longitude = fields.Float()
    attachment_ids = fields.Many2many('ir.attachment')
    map_display = fields.Char(compute='_compute_map_display')
    certificate_id = fields.Many2one('ir.attachment', string='Destruction Certificate', readonly=True)  # New for auto-certificate
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)  # New for auto-invoicing
    bale_ids = fields.One2many('paper.bale', 'shredding_id', string='Generated Bales')  # New link to bales
    pos_session_id = fields.Many2one('pos.session', string='POS Session')  # New for walk-in

    @api.depends('service_type', 'bin_ids', 'shredded_box_ids', 'box_quantity', 'hard_drive_quantity', 'uniform_quantity')
    def _compute_total_charge(self):
        for rec in self:
            if rec.service_type == 'bin':
                rec.total_charge = len(rec.bin_ids) * 10.0
            elif rec.service_type == 'box':
                qty = rec.box_quantity or len(rec.shredded_box_ids)
                rec.total_charge = qty * 5.0
            elif rec.service_type == 'hard_drive':
                rec.total_charge = rec.hard_drive_quantity * 15.0  # Example pricing
            elif rec.service_type == 'uniform':
                rec.total_charge = rec.uniform_quantity * 8.0  # Example pricing
            else:
                rec.total_charge = 0

    @api.depends('latitude', 'longitude')
    def _compute_map_display(self):
        for rec in self:
            if rec.latitude and rec.longitude:
                rec.map_display = f"{rec.latitude},{rec.longitude}"
            else:
                rec.map_display = ''

    @api.depends('box_quantity', 'shredded_box_ids')
    def _compute_total_boxes(self):
        for rec in self:
            if rec.service_type == 'box':
                rec.total_boxes = rec.box_quantity or len(rec.shredded_box_ids)
            else:
                rec.total_boxes = 0

    @api.depends('total_boxes', 'unit_cost', 'bin_ids', 'hard_drive_quantity', 'uniform_quantity')
    def _compute_total_cost(self):
        for rec in self:
            if rec.service_type == 'bin':
                rec.total_cost = len(rec.bin_ids) * 10.0
            elif rec.service_type == 'box':
                rec.total_cost = rec.total_boxes * rec.unit_cost
            elif rec.service_type == 'hard_drive':
                rec.total_cost = rec.hard_drive_quantity * 15.0
            elif rec.service_type == 'uniform':
                rec.total_cost = rec.uniform_quantity * 8.0
            else:
                rec.total_cost = 0

    def action_confirm(self):
        """Confirm the shredding service"""
        self.write({'status': 'confirmed'})
        return True

    def action_start(self):
        """Start the shredding service"""
        self.write({'status': 'in_progress'})
        return True

    def action_complete(self):
        """Complete the shredding service, generate certificate, invoice, and bales."""
        self.write({'status': 'completed'})
        self._generate_certificate()
        self._create_invoice()
        if self.service_type in ('bin', 'box'):
            self._generate_bales()  # Auto-create bales for paper recycling
        return True

    def action_cancel(self):
        """Cancel the shredding service"""
        self.write({'status': 'cancelled'})
        return True

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'ShreddingService':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.service') or 'New'
        return super().create(vals_list)

    def _generate_certificate(self):
        """Generate PDF certificate as attachment."""
        report = self.env.ref('records_management.report_destruction_certificate')
        pdf = report._render_qweb_pdf(self.ids)[0]
        attachment = self.env['ir.attachment'].create({
            'name': f'Certificate_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf,
            'res_model': self._name,
            'res_id': self.id,
        })
        self.certificate_id = attachment
        self.message_post(body=_('Destruction Certificate generated.'))
        # Make available in portal
        self.customer_id.message_post(body=_('Certificate available in portal.'), attachment_ids=[attachment.id])

    def _create_invoice(self):
        """Auto-create draft invoice."""
        product_id = self.env.ref('records_management.product_shredding_service').id if self.service_type in ('bin', 'box') else self.env.ref('records_management.product_harddrive_service').id  # Assume products exist
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product_id,
                'quantity': 1,  # Adjust based on type
                'price_unit': self.total_charge,
                'name': f'Shredding Service {self.name}',
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice
        self.message_post(body=_('Invoice created: %s') % invoice.name)

    def _generate_bales(self):
        """Auto-create bales for recycled paper."""
        bale_vals = {
            'shredding_id': self.id,
            'paper_type': 'white',  # Default, can be onchange based on service
            'weight': 0.0,  # To be updated when weighed
        }
        bale = self.env['paper.bale'].create(bale_vals)
        self.bale_ids = [(4, bale.id)]
        self.message_post(body=_('Bale created for recycling.'))
