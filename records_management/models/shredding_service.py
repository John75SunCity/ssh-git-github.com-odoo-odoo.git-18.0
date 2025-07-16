# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow - Odoo 18.0 optimized."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, name'

    # Core Fields (cleaned and optimized)
    name = fields.Char(string='Service Reference', required=True, default='New', tracking=True)
    status = fields.Selection([
        ('draft', 'Draft'), ('confirmed', 'Confirmed'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True, index=True)  # Added index for performance
    service_date = fields.Date(string='Service Date', default=fields.Date.today, tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    
    # Enhanced Service Types (per review)
    service_type = fields.Selection([
        ('bin', 'Bin Shredding'), 
        ('box', 'Box Shredding'),
        ('hard_drive', 'Hard Drive Destruction'), 
        ('uniform', 'Uniform Shredding'),
        ('walk_in', 'Walk-in Service')  # New for POS integration
    ], string='Service Type', required=True, tracking=True)
    
    # Service Details (consolidated and improved)
    bin_ids = fields.Many2many('stock.lot', 'shredding_bin_rel', 'service_id', 'lot_id', 
                               string='Serviced Bins', domain="[('product_id.name', '=', 'Shredding Bin')]")
    box_quantity = fields.Integer(string='Number of Boxes')
    shredded_box_ids = fields.Many2many('stock.lot', 'shredding_box_rel', 'service_id', 'lot_id',
                                        string='Shredded Boxes', domain="[('customer_id', '!=', False)]")
    hard_drive_quantity = fields.Integer(string='Number of Hard Drives')
    uniform_quantity = fields.Integer(string='Number of Uniforms')
    
    # Financial (enhanced per review)
    unit_cost = fields.Float(string='Unit Cost', default=5.0)
    total_charge = fields.Float(compute='_compute_total_charge', store=True, tracking=True)
    certificate_id = fields.Many2one('ir.attachment', string='Destruction Certificate', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    
    # Integration Fields (new per review)
    pos_session_id = fields.Many2one('pos.session', string='POS Session')  # Walk-in services
    bale_ids = fields.One2many('records_management.bale', 'service_id', string='Generated Bales')  # Link to bales
    
    # Audit and Compliance
    notes = fields.Text(string='Notes')
    audit_barcodes = fields.Text(string='Audit Barcodes')
    timestamp = fields.Datetime(default=fields.Datetime.now)
    latitude = fields.Float(string='GPS Latitude')
    longitude = fields.Float(string='GPS Longitude')
    attachment_ids = fields.Many2many('ir.attachment', string='Supporting Documents')
    
    # Computed Fields
    total_boxes = fields.Integer(compute='_compute_total_boxes', store=True)
    total_cost = fields.Float(compute='_compute_total_cost', store=True)
    map_display = fields.Char(compute='_compute_map_display')
    
    # Company
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)

    # Computed Methods (enhanced for Odoo 18.0)
    @api.depends('box_quantity', 'hard_drive_quantity', 'uniform_quantity', 'bin_ids')
    def _compute_total_boxes(self) -> None:
        """Compute total items across all service types."""
        for record in self:
            record.total_boxes = (
                record.box_quantity + 
                record.hard_drive_quantity + 
                record.uniform_quantity + 
                len(record.bin_ids)
            )

    @api.depends('total_boxes', 'unit_cost')
    def _compute_total_cost(self) -> None:
        """Compute base cost before taxes."""
        for record in self:
            record.total_cost = record.total_boxes * record.unit_cost

    @api.depends('total_cost')
    def _compute_total_charge(self) -> None:
        """Compute final charge including taxes and fees."""
        for record in self:
            # Apply company tax rate
            tax_rate = 0.10  # 10% standard rate
            record.total_charge = record.total_cost * (1 + tax_rate)

    @api.depends('latitude', 'longitude')
    def _compute_map_display(self) -> None:
        """Generate Google Maps link for service location."""
        for record in self:
            if record.latitude and record.longitude:
                record.map_display = f"https://www.google.com/maps?q={record.latitude},{record.longitude}"
            else:
                record.map_display = False

    # Validation & Constraints
    @api.constrains('service_date', 'scheduled_date')
    def _check_dates(self) -> None:
        """Validate service dates are logical."""
        for record in self:
            if record.scheduled_date and record.service_date:
                if record.scheduled_date > record.service_date:
                    raise ValidationError(_("Scheduled date cannot be after service date."))

    @api.constrains('latitude', 'longitude')
    def _check_coordinates(self) -> None:
        """Validate GPS coordinates are within valid ranges."""
        for record in self:
            if record.latitude and not (-90 <= record.latitude <= 90):
                raise ValidationError(_("Latitude must be between -90 and 90 degrees."))
            if record.longitude and not (-180 <= record.longitude <= 180):
                raise ValidationError(_("Longitude must be between -180 and 180 degrees."))

    # Model Lifecycle Methods (modern patterns)
    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'ShreddingService':
        """Enhanced create with auto-sequence and audit logging."""
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.service') or 'New'
        
        records = super().create(vals_list)
        for record in records:
            record.message_post(
                body=_("Shredding service %s created for %s") % (record.name, record.customer_id.name),
                subtype_xmlid='mail.mt_note'
            )
        return records

    def write(self, vals: dict) -> bool:
        """Enhanced write with auto-workflow triggers."""
        result = super().write(vals)
        
        # Trigger auto-workflows on status change
        if 'status' in vals:
            for record in self:
                if record.status == 'completed':
                    record._auto_generate_certificate()
                    record._auto_create_invoice()
                elif record.status == 'confirmed':
                    record._schedule_notification()
        
        return result

    # Action Methods (enhanced per review)
    def action_confirm(self) -> None:
        """Confirm service and schedule notifications."""
        for record in self:
            record.status = 'confirmed'
            record.message_post(
                body=_("Service confirmed for %s") % record.service_date,
                subtype_xmlid='mail.mt_comment'
            )

    def action_start_service(self) -> None:
        """Mark service as in progress."""
        for record in self:
            record.status = 'in_progress'
            record.timestamp = fields.Datetime.now()

    def action_complete_service(self) -> None:
        """Complete service with auto-certificate and invoicing."""
        for record in self:
            record.status = 'completed'
            record._auto_generate_certificate()
            record._auto_create_invoice()
            record._create_bales_if_applicable()

    # Auto-workflow Methods (new per review)
    def _auto_generate_certificate(self) -> None:
        """Generate destruction certificate automatically."""
        if self.certificate_id:
            return  # Already generated
        
        try:
            report = self.env.ref('records_management.action_report_destruction_certificate')
            pdf_content, _ = report._render_qweb_pdf(self.ids)
            
            certificate = self.env['ir.attachment'].create({
                'name': f'Destruction Certificate - {self.name}.pdf',
                'type': 'binary',
                'datas': pdf_content,
                'res_model': self._name,
                'res_id': self.id,
                'mimetype': 'application/pdf'
            })
            
            self.certificate_id = certificate.id
            self.message_post(
                body=_("Destruction certificate generated"),
                attachment_ids=[certificate.id],
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            self.message_post(
                body=_("Failed to generate certificate: %s") % str(e),
                subtype_xmlid='mail.mt_note'
            )

    def _auto_create_invoice(self) -> None:
        """Create invoice automatically when service is completed."""
        if self.invoice_id or not self.total_charge:
            return  # Already invoiced or no charge
        
        try:
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': self.customer_id.id,
                'invoice_date': fields.Date.today(),
                'invoice_line_ids': [(0, 0, {
                    'name': f'Shredding Service - {self.service_type.replace("_", " ").title()}',
                    'quantity': self.total_boxes,
                    'price_unit': self.unit_cost,
                    'tax_ids': [(6, 0, self.customer_id.property_account_position_id.tax_ids.ids)]
                })]
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice.id
            
            self.message_post(
                body=_("Invoice %s created automatically") % invoice.name,
                subtype_xmlid='mail.mt_comment'
            )
        except Exception as e:
            self.message_post(
                body=_("Failed to create invoice: %s") % str(e),
                subtype_xmlid='mail.mt_note'
            )

    def _create_bales_if_applicable(self) -> None:
        """Create paper bales from shredded materials."""
        if self.service_type in ('box', 'uniform') and self.total_boxes > 0:
            # Estimate weight (100 boxes = 1 bale at 500 lbs)
            estimated_weight = (self.total_boxes / 100) * 500
            
            if estimated_weight >= 100:  # Minimum bale size
                bale_vals = {
                    'customer_id': self.customer_id.id,
                    'paper_type': 'mixed',  # Shredded material is mixed
                    'weight': estimated_weight,
                    'service_id': self.id,
                    'notes': f'Generated from shredding service {self.name}'
                }
                
                bale = self.env['records_management.bale'].create(bale_vals)
                self.message_post(
                    body=_("Paper bale %s created from shredded materials") % bale.name,
                    subtype_xmlid='mail.mt_comment'
                )

    def _schedule_notification(self) -> None:
        """Schedule service reminder notification."""
        if self.scheduled_date:
            reminder_date = self.scheduled_date - fields.timedelta(days=1)
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                date_deadline=reminder_date,
                summary=f'Shredding service reminder for {self.customer_id.name}',
                note=f'Service scheduled for {self.scheduled_date}'
            )

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
