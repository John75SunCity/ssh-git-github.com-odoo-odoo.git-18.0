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
    hard_drive_ids = fields.One2many('shredding.hard_drive', 'service_id', string='Hard Drive Details', tracking=True)
    hard_drive_scanned_count = fields.Integer(compute='_compute_hard_drive_counts', store=True, string='Scanned Count')
    hard_drive_verified_count = fields.Integer(compute='_compute_hard_drive_counts', store=True, string='Verified Count')
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

    # Phase 2 Audit & Compliance Fields - Added by automated script
    naid_certificate_id = fields.Many2one('naid.certificate', string='NAID Certificate')
    naid_compliance_level = fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA'), ('a', 'NAID A')], string='NAID Compliance Level')
    destruction_standard = fields.Selection([('dod_5220', 'DoD 5220.22-M'), ('nist_800_88', 'NIST 800-88'), ('iso_27040', 'ISO/IEC 27040'), ('custom', 'Custom Standard')], string='Destruction Standard')
    witness_verification_required = fields.Boolean('Witness Verification Required', default=True)
    photo_documentation_required = fields.Boolean('Photo Documentation Required', default=True)
    video_documentation_required = fields.Boolean('Video Documentation Required', default=False)
    certificate_of_destruction_id = fields.Many2one('records.destruction.certificate', string='Certificate of Destruction')
    audit_trail_ids = fields.One2many('records.audit.log', 'shredding_service_id', string='Audit Trail')
    compliance_documentation_ids = fields.One2many('ir.attachment', 'res_id', string='Compliance Documentation', domain=[('res_model', '=', 'shredding.service')])
    destruction_method_verified = fields.Boolean('Destruction Method Verified', default=False)
    chain_of_custody_maintained = fields.Boolean('Chain of Custody Maintained', default=False)
    environmental_compliance = fields.Boolean('Environmental Compliance Verified', default=False)
    quality_control_performed = fields.Boolean('Quality Control Performed', default=False)
    quality_control_date = fields.Datetime('Quality Control Date')
    quality_control_officer_id = fields.Many2one('res.users', string='Quality Control Officer')
    particle_size_verified = fields.Boolean('Particle Size Verified', default=False)
    contamination_check = fields.Boolean('Contamination Check Performed', default=False)
    equipment_calibration_verified = fields.Boolean('Equipment Calibration Verified', default=False)

    # Phase 2 Audit & Compliance Fields - Added by automated script
    audit_required = fields.Boolean('Audit Required', default=True)
    audit_completed = fields.Boolean('Audit Completed', default=False)
    audit_date = fields.Date('Audit Date')
    auditor_id = fields.Many2one('res.users', string='Auditor')
    compliance_status = fields.Selection([('pending', 'Pending'), ('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant')], string='Compliance Status', default='pending')
    regulatory_approval = fields.Boolean('Regulatory Approval', default=False)
    naid_certification = fields.Boolean('NAID Certification', default=False)
    iso_certification = fields.Boolean('ISO Certification', default=False)
    audit_notes = fields.Text('Audit Notes')
    compliance_notes = fields.Text('Compliance Notes')
    risk_level = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High'), ('critical', 'Critical')], string='Risk Level', default='medium')

    @api.depends('hard_drive_ids', 'hard_drive_ids.scanned_at_customer', 'hard_drive_ids.verified_before_destruction')
    def _compute_hard_drive_counts(self):
        """Compute scanned and verified hard drive counts"""
        for rec in self:
            rec.hard_drive_scanned_count = len(rec.hard_drive_ids.filtered('scanned_at_customer'))
            rec.hard_drive_verified_count = len(rec.hard_drive_ids.filtered('verified_before_destruction'))

    @api.depends('service_type', 'bin_ids', 'shredded_box_ids', 'box_quantity', 'hard_drive_quantity', 'uniform_quantity', 'hard_drive_ids')
    def _compute_total_charge(self):
        for rec in self:
            if rec.service_type == 'bin':
                rec.total_charge = len(rec.bin_ids) * 10.0
            elif rec.service_type == 'box':
                qty = rec.box_quantity or len(rec.shredded_box_ids)
                rec.total_charge = qty * 5.0
            elif rec.service_type == 'hard_drive':
                # Use actual scanned drives count if available, otherwise use manual quantity
                qty = len(rec.hard_drive_ids) if rec.hard_drive_ids else (rec.hard_drive_quantity or 0)
                rec.total_charge = qty * 15.0
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
                # Use actual scanned drives count if available, otherwise use manual quantity
                qty = len(rec.hard_drive_ids) if rec.hard_drive_ids else (rec.hard_drive_quantity or 0)
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
                raise ValidationError(_("Hard drive service requires quantity or scanned drives."))
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

    def action_start_destruction(self):
        """Start the destruction process"""
        self.write({'status': 'in_progress'})
        self.message_post(body=_('Destruction started by %s') % self.env.user.name)

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        return {
            'name': _('Destruction Certificate'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.destruction_certificate',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.destruction_certificate',
            'context': {'active_ids': [self.id]},
        }

    def action_view_items(self):
        """View items in this shredding service"""
        self.ensure_one()
        return {
            'name': _('Shredding Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('shredding_service_id', '=', self.id)],
            'context': {'default_shredding_service_id': self.id},
        }

    def action_witness_verification(self):
        """Witness verification for destruction"""
        self.ensure_one()
        return {
            'name': _('Witness Verification'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.witness.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_shredding_service_id': self.id},
        }

    def action_compliance_check(self):
        """NAID compliance check"""
        self.ensure_one()
        return {
            'name': _('NAID Compliance Check'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.compliance.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_shredding_service_id': self.id},
        }

    def action_view_witnesses(self):
        """View witnesses for this destruction"""
        self.ensure_one()
        return {
            'name': _('Witnesses'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.witness',
            'view_mode': 'tree,form',
            'domain': [('shredding_service_id', '=', self.id)],
            'context': {'default_shredding_service_id': self.id},
        }

    def action_view_certificates(self):
        """View certificates for this destruction"""
        self.ensure_one()
        return {
            'name': _('Certificates'),
            'type': 'ir.actions.act_window',
            'res_model': 'destruction.certificate',
            'view_mode': 'tree,form',
            'domain': [('shredding_service_id', '=', self.id)],
            'context': {'default_shredding_service_id': self.id},
        }

    def action_verify_witness(self):
        """Verify witness signature"""
        # This would be called from context with witness_id
        witness_id = self.env.context.get('witness_id')
        if witness_id:
            witness = self.env['shredding.witness'].browse(witness_id)
            witness.write({'verified': True, 'verified_date': fields.Datetime.now()})
            return True
        return False

    def action_scan_hard_drives_customer(self):
        """Scan hard drives at customer location"""
        self.ensure_one()
        return {
            'name': _('Scan Hard Drives at Customer'),
            'type': 'ir.actions.act_window',
            'res_model': 'hard_drive.scan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_shredding_service_id': self.id,
                'scan_location': 'customer',
            },
        }

    def action_scan_hard_drives_facility(self):
        """Scan hard drives before destruction at facility"""
        self.ensure_one()
        return {
            'name': _('Verify Hard Drives at Facility'),
            'type': 'ir.actions.act_window',
            'res_model': 'hard_drive.scan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_shredding_service_id': self.id,
                'scan_location': 'facility',
            },
        }

    def action_view_hard_drives(self):
        """View scanned hard drives"""
        self.ensure_one()
        return {
            'name': _('Hard Drive Serial Numbers'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.hard_drive',
            'view_mode': 'tree,form',
            'domain': [('service_id', '=', self.id)],
            'context': {'default_service_id': self.id},
        }

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
            'hard_drive': len(self.hard_drive_ids) if self.hard_drive_ids else (self.hard_drive_quantity or 0),
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
    _order = 'scanned_at_customer_date desc, serial_number'

    service_id = fields.Many2one('shredding.service', required=True, ondelete='cascade')
    serial_number = fields.Char(string='Serial Number', required=True, help='Scanned serial number for NAID tracking')
    hashed_serial = fields.Char(compute='_compute_hashed_serial', store=True, help='Hashed for integrity (ISO 27001)')
    
    # Customer location scanning
    scanned_at_customer = fields.Boolean(string='Scanned at Customer', default=False)
    scanned_at_customer_date = fields.Datetime(string='Customer Scan Date')
    scanned_at_customer_by = fields.Many2one('res.users', string='Scanned by (Customer)')
    customer_location_notes = fields.Text(string='Customer Location Notes')
    
    # Facility verification scanning
    verified_before_destruction = fields.Boolean(string='Verified Before Destruction', default=False)
    verified_at_facility_date = fields.Datetime(string='Facility Verification Date')
    verified_at_facility_by = fields.Many2one('res.users', string='Verified by (Facility)')
    facility_verification_notes = fields.Text(string='Facility Verification Notes')
    
    # Destruction tracking
    destroyed = fields.Boolean(string='Destroyed', default=False)
    destruction_date = fields.Datetime(string='Destruction Date')
    destruction_method = fields.Selection([
        ('shred', 'Physical Shredding'),
        ('crush', 'Crushing'),
        ('degauss', 'Degaussing'),
        ('wipe', 'Data Wiping'),
    ], string='Destruction Method')
    
    # Certificate generation fields
    included_in_certificate = fields.Boolean(string='Included in Certificate', default=True)
    certificate_line_text = fields.Char(compute='_compute_certificate_line', store=True, 
                                       help='Text line for certificate')

    @api.depends('serial_number', 'destruction_method', 'destruction_date')
    def _compute_certificate_line(self):
        """Generate certificate line text for each drive"""
        for rec in self:
            if rec.serial_number and rec.destruction_method:
                method_text = dict(rec._fields['destruction_method'].selection)[rec.destruction_method]
                date_text = rec.destruction_date.strftime('%Y-%m-%d %H:%M') if rec.destruction_date else 'Pending'
                rec.certificate_line_text = f"Serial: {rec.serial_number} | Method: {method_text} | Date: {date_text}"
            else:
                rec.certificate_line_text = f"Serial: {rec.serial_number or 'Unknown'} | Status: Pending"

    @api.depends('serial_number')
    def _compute_hashed_serial(self):
        for rec in self:
            if rec.serial_number:
                rec.hashed_serial = hashlib.sha256(rec.serial_number.encode()).hexdigest()
            else:
                rec.hashed_serial = False

    def action_mark_customer_scanned(self):
        """Mark as scanned at customer location"""
        self.write({
            'scanned_at_customer': True,
            'scanned_at_customer_date': fields.Datetime.now(),
            'scanned_at_customer_by': self.env.user.id,
        })
        return True

    def action_mark_facility_verified(self):
        """Mark as verified at facility before destruction"""
        self.write({
            'verified_before_destruction': True,
            'verified_at_facility_date': fields.Datetime.now(),
            'verified_at_facility_by': self.env.user.id,
        })
        return True

    def action_mark_destroyed(self):
        """Mark as destroyed"""
        self.write({
            'destroyed': True,
            'destruction_date': fields.Datetime.now(),
        })
        return True

    @api.model
    def create_from_scan(self, service_id, serial_number, scan_location='customer'):
        """Create hard drive record from barcode scan"""
        vals = {
            'service_id': service_id,
            'serial_number': serial_number,
        }
        
        if scan_location == 'customer':
            vals.update({
                'scanned_at_customer': True,
                'scanned_at_customer_date': fields.Datetime.now(),
                'scanned_at_customer_by': self.env.user.id,
            })
        elif scan_location == 'facility':
            vals.update({
                'verified_before_destruction': True,
                'verified_at_facility_date': fields.Datetime.now(),
                'verified_at_facility_by': self.env.user.id,
            })
        
        return self.create(vals)
