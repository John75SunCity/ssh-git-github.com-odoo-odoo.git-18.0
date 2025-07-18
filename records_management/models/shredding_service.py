# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
import hashlib
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow, NAID/ISO compliance, including hard drives and uniforms."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, name'

    name = fields.Char(string='Service Reference', required=True, default='New', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('invoiced', 'Invoiced'), ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', customer_id)]")  # Added for granular
    service_date = fields.Date(string='Service Date', default=fields.Date.context_today, required=True, tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'), ('box', 'Box Shredding'),
        ('hard_drive', 'Hard Drive Destruction'), ('uniform', 'Uniform Shredding')
    ], string='Service Type', required=True, tracking=True)  # Expanded for new services
    bin_ids = fields.Many2many(
        'stock.lot',
        relation='shredding_service_bin_rel',  # Custom relation to avoid conflict with shredded_box_ids
        column1='service_id',
        column2='lot_id',
        string='Serviced Bins',
        domain="[('product_id.name', '=', 'Shredding Bin')]"
    )
    box_quantity = fields.Integer(string='Number of Boxes', tracking=True)
    shredded_box_ids = fields.Many2many('stock.lot', string='Shredded Boxes', domain="[('customer_id', '!=', False)]", tracking=True)
    hard_drive_quantity = fields.Integer(string='Number of Hard Drives', tracking=True)  # New
    hard_drive_ids = fields.One2many('shredding.hard_drive', 'service_id', string='Hard Drives', tracking=True)  # New: Detailed tracking for NAID compliance
    uniform_quantity = fields.Integer(string='Number of Uniforms', tracking=True)  # New
    total_boxes = fields.Integer(compute='_compute_total_boxes', store=True, tracking=True)
    unit_cost = fields.Float(string='Unit Cost', default=5.0, tracking=True)
    total_cost = fields.Float(compute='_compute_total_cost', store=True, tracking=True)
    notes = fields.Text(string='Notes', tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, tracking=True)
    audit_barcodes = fields.Text(string='Audit Barcodes', help='Barcodes for NAID audit trails', tracking=True)
    total_charge = fields.Float(compute='_compute_total_charge', store=True, tracking=True)
    timestamp = fields.Datetime(default=fields.Datetime.now, readonly=True)
    latitude = fields.Float(string='Latitude (for mobile verification)', digits=(16, 8), tracking=True)
    longitude = fields.Float('Longitude', digits=(16, 8), tracking=True)
    attachment_ids = fields.Many2many('ir.attachment', string='Attachments (e.g., photos, CCTV clips)')
    map_display = fields.Char(compute='_compute_map_display', store=True)
    certificate_id = fields.Many2one('ir.attachment', string='Destruction Certificate', readonly=True)  # New for auto-certificate
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)  # New for auto-invoicing
    bale_ids = fields.One2many('paper.bale', 'shredding_id', string='Generated Bales')  # Link to bales
    pos_session_id = fields.Many2one('pos.session', string='POS Session (Walk-in)', tracking=True)  # New for walk-in
    estimated_bale_weight = fields.Float(compute='_compute_estimated_bale_weight', store=True, help='Predictive weight for recycling efficiency')

    @api.depends('service_type', 'bin_ids', 'shredded_box_ids', 'box_quantity', 'hard_drive_quantity', 'uniform_quantity', 'hard_drive_ids')
    def _compute_total_charge(self):
        for rec in self:
            if rec.service_type == 'bin':
                rec.total_charge = len(rec.bin_ids) * 10.0
            elif rec.service_type == 'box':
                qty = rec.box_quantity or len(rec.shredded_box_ids)
                rec.total_charge = qty * 5.0
            elif rec.service_type == 'hard_drive':
                qty = rec.hard_drive_ids or rec.hard_drive_quantity  # Use detailed if available
                rec.total_charge = len(qty) * 15.0 if isinstance(qty, models.BaseModel) else qty * 15.0
            elif rec.service_type == 'uniform':
                rec.total_charge = rec.uniform_quantity * 8.0
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

    @api.depends('total_boxes', 'unit_cost', 'bin_ids', 'hard_drive_quantity', 'uniform_quantity', 'hard_drive_ids')
    def _compute_total_cost(self):
        for rec in self:
            if rec.service_type == 'bin':
                rec.total_cost = len(rec.bin_ids) * 10.0
            elif rec.service_type == 'box':
                rec.total_cost = rec.total_boxes * rec.unit_cost
            elif rec.service_type == 'hard_drive':
                qty = len(rec.hard_drive_ids) if rec.hard_drive_ids else rec.hard_drive_quantity
                rec.total_cost = qty * 15.0
            elif rec.service_type == 'uniform':
                rec.total_cost = rec.uniform_quantity * 8.0
            else:
                rec.total_cost = 0

    @api.depends('total_boxes', 'box_quantity', 'bin_ids')
    def _compute_estimated_bale_weight(self):
        """Innovative: Simple predictive calculation for bale weight (e.g., avg 20lbs per box; extend with ML for accuracy)."""
        for rec in self:
            qty = len(rec.bin_ids) + rec.total_boxes
            rec.estimated_bale_weight = qty * 20.0  # Placeholder; link to scales via IoT for real-time

    @api.constrains('service_type', 'bin_ids', 'shredded_box_ids', 'box_quantity', 'hard_drive_quantity', 'uniform_quantity', 'hard_drive_ids')
    def _check_quantities(self):
        """Validation for data integrity (ISO 27001)."""
        for rec in self:
            if rec.service_type == 'bin' and not rec.bin_ids:
                raise ValidationError(_("Bin service must have serviced bins."))
            elif rec.service_type == 'box' and not (rec.box_quantity or rec.shredded_box_ids):
                raise ValidationError(_("Box service requires quantity or boxes."))
            elif rec.service_type == 'hard_drive' and not (rec.hard_drive_quantity or rec.hard_drive_ids):
                raise ValidationError(_("Hard drive service requires quantity or details."))
            elif rec.service_type == 'uniform' and not rec.uniform_quantity:
                raise ValidationError(_("Uniform service requires quantity."))

    def action_confirm(self):
        """Confirm the shredding service."""
        self.write({'status': 'confirmed'})
        self.message_post(body=_('Service confirmed; NAID audit trail updated.'))
        return True

    def action_start(self):
        """Start the shredding service."""
        self.write({'status': 'in_progress'})
        return True

    def action_complete(self):
        """Complete service, generate certificate/invoice/bales, ensure compliance."""
        self.write({'status': 'completed'})
        self._generate_certificate()
        self._create_invoice()
        if self.service_type in ('bin', 'box'):
            self._generate_bales()
        self.message_post(body=_('Service completed with ISO data integrity checks.'))
        return True

    def action_cancel(self):
        """Cancel the service."""
        self.write({'status': 'cancelled'})
        return True

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'ShreddingService':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.service') or 'New'
        return super().create(vals_list)

    def _generate_certificate(self):
        """Generate PDF certificate as attachment (NAID requirement)."""
        report = self.env.ref('records_management.report_destruction_certificate')
        pdf, _ = report._render_qweb_pdf(self.ids)
        attachment = self.env['ir.attachment'].create({
            'name': f'Certificate_{self.name}.pdf',
            'type': 'binary',
            'datas': pdf,
            'store_fname': f'certificate_{self.name}.pdf',
            'res_model': self._name,
            'res_id': self.id,
        })
        self.certificate_id = attachment
        self.message_post(body=_('Destruction Certificate generated per NAID standards.'))
        # Portal access for customer
        self.customer_id.message_post(body=_('Your destruction certificate is available in the portal.'), attachment_ids=[attachment.id])

    def _create_invoice(self):
        """Auto-create draft invoice with type-specific products."""
        product_map = {
            'bin': self.env.ref('records_management.product_shredding_service', raise_if_not_found=False),
            'box': self.env.ref('records_management.product_shredding_service', raise_if_not_found=False),
            'hard_drive': self.env.ref('records_management.product_harddrive_service', raise_if_not_found=False),
            'uniform': self.env.ref('records_management.product_uniform_service', raise_if_not_found=False),  # Assume/create this product
        }
        product = product_map.get(self.service_type) or self.env['product.product'].search([('name', '=', 'Shredding Service')], limit=1)
        qty = {
            'bin': len(self.bin_ids),
            'box': self.total_boxes,
            'hard_drive': len(self.hard_drive_ids) if self.hard_drive_ids else self.hard_drive_quantity,
            'uniform': self.uniform_quantity,
        }.get(self.service_type, 1)
        invoice_vals = {
            'partner_id': self.customer_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {
                'product_id': product.id,
                'quantity': qty,
                'price_unit': self.total_charge / qty if qty else self.total_charge,
                'name': f'{self.service_type.capitalize()} Shredding Service {self.name}',
            })],
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice
        self.write({'status': 'invoiced'})
        self.message_post(body=_('Invoice created: %s' % invoice.name))

    def _generate_bales(self):
        """Auto-create bales for recycled paper (recycling feature)."""
        bale_vals = {
            'shredding_id': self.id,
            'paper_type': 'white',  # Default; onchange in view for mixed/white
            'weight': self.estimated_bale_weight,  # Initial estimate; update via scales
        }
        bale = self.env['paper.bale'].create(bale_vals)
        self.bale_ids = [(4, bale.id)]
        self.message_post(body=_('Bale created for recycling; link to trailer load for efficiency.'))

class ShreddingHardDrive(models.Model):
    _name = 'shredding.hard_drive'
    _description = 'Hard Drive Details for Shredding'
    _rec_name = 'serial_number'

    service_id = fields.Many2one('shredding.service', required=True)
    serial_number = fields.Char(string='Serial Number', required=True, help='For NAID tracking')
    hashed_serial = fields.Char(compute='_compute_hashed_serial', store=True, help='Hashed for integrity (ISO 27001)')

    @api.depends('serial_number')
    def _compute_hashed_serial(self):
        for rec in self:
            if rec.serial_number:
                rec.hashed_serial = hashlib.sha256(rec.serial_number.encode()).hexdigest()
            else:
                rec.hashed_serial = False
