# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow - Odoo 18.0 optimized."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
    
    # NAID AAA Compliance Methods
    def action_start_destruction(self):
        """Start the destruction process with NAID compliance tracking"""
        self.write({
            'status': 'in_progress',
            'destruction_start_time': fields.Datetime.now()
        })
        
        # Log the start of destruction
        self.env['naid.audit.log'].log_event(
            'destruction_start',
            f'Destruction process started for service {self.name}',
            employee_id=self.env.user.employee_id.id,
            partner_id=self.customer_id.id,
            risk_level='high',
            compliance_status='compliant'
        )
        
        return True

    def action_complete_destruction(self):
        """Complete destruction with full NAID compliance verification"""
        # Ensure required fields are filled
        if not self.destruction_method:
            raise ValidationError(_("Destruction method must be specified for compliance."))
        
        if not self.witness_employee_ids:
            raise ValidationError(_("At least one witness is required for NAID compliance."))
        
        self.write({
            'status': 'completed',
            'destruction_end_time': fields.Datetime.now()
        })
        
        # Create chain of custody record
        self._create_chain_of_custody()
        
        # Log the completion
        self.env['naid.audit.log'].log_event(
            'destruction_complete',
            f'Destruction process completed for service {self.name}. '
            f'Method: {self.destruction_method}, Duration: {self.destruction_duration:.2f} hours',
            employee_id=self.env.user.employee_id.id,
            partner_id=self.customer_id.id,
            risk_level='medium',
            compliance_status='compliant',
            witness_employee_ids=[(6, 0, self.witness_employee_ids.ids)]
        )
        
        return True

    def action_verify_compliance(self):
        """Verify NAID AAA compliance"""
        # Check all compliance requirements
        compliance_issues = self._check_compliance_requirements()
        
        if compliance_issues:
            raise ValidationError(_("Compliance verification failed:\n%s") % '\n'.join(compliance_issues))
        
        self.write({
            'compliance_verified': True,
            'verification_employee_id': self.env.user.employee_id.id,
            'verification_date': fields.Datetime.now()
        })
        
        # Log compliance verification
        self.env['naid.audit.log'].log_event(
            'audit_review',
            f'NAID AAA compliance verified for service {self.name}',
            employee_id=self.env.user.employee_id.id,
            partner_id=self.customer_id.id,
            risk_level='low',
            compliance_status='compliant'
        )
        
        return True

    def _create_chain_of_custody(self):
        """Create chain of custody record for NAID compliance"""
        if not self.chain_of_custody_id:
            custody_vals = {
                'name': f'COC-{self.name}',
                'service_id': self.id,
                'customer_id': self.customer_id.id,
                'start_date': self.destruction_start_time,
                'end_date': self.destruction_end_time,
                'custody_events': [(0, 0, {
                    'event_type': 'destruction',
                    'timestamp': self.destruction_end_time,
                    'employee_id': self.env.user.employee_id.id,
                    'description': f'Materials destroyed using {self.destruction_method}',
                    'witness_employee_ids': [(6, 0, self.witness_employee_ids.ids)]
                })]
            }
            
            custody = self.env['naid.chain.custody'].create(custody_vals)
            self.chain_of_custody_id = custody.id

    def _check_compliance_requirements(self):
        """Check all NAID AAA compliance requirements"""
        issues = []
        
        # Check basic requirements
        if not self.destruction_method:
            issues.append("Destruction method not specified")
        
        if not self.security_level:
            issues.append("Security level not specified")
        
        if not self.equipment_used:
            issues.append("Equipment used not documented")
        
        if not self.witness_employee_ids:
            issues.append("No witnesses documented")
        
        # Check employee compliance
        for witness in self.witness_employee_ids:
            if witness.compliance_status != 'compliant':
                issues.append(f"Witness {witness.name} is not NAID compliant")
        
        # Check destruction times
        if not self.destruction_start_time or not self.destruction_end_time:
            issues.append("Destruction times not properly documented")
        
        # Check weight documentation
        if not self.pre_destruction_weight:
            issues.append("Pre-destruction weight not documented")
        
        return issues


class ShreddingService(models.Model):
    """Document Shredding Service with enhanced workflow - Odoo 18.0 optimized."""
    _name = 'shredding.service'
    _description = 'Document Shredding Service'
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
    
    # NAID AAA Compliance Fields
    chain_of_custody_id = fields.Many2one(
        'naid.chain.custody', 
        string='Chain of Custody',
        help='NAID chain of custody record'
    )
    
    witness_employee_ids = fields.Many2many(
        'hr.employee',
        'shredding_witness_rel',
        'service_id',
        'employee_id',
        string='Witnesses',
        help='Employees who witnessed the destruction process'
    )
    
    destruction_method = fields.Selection([
        ('cross_cut', 'Cross-Cut Shredding'),
        ('micro_cut', 'Micro-Cut Shredding'),
        ('pulverization', 'Pulverization'),
        ('incineration', 'Incineration'),
        ('degaussing', 'Degaussing (Magnetic Media)'),
        ('physical_destruction', 'Physical Destruction')
    ], string='Destruction Method', help='Method used for destruction')
    
    security_level = fields.Selection([
        ('p1', 'P-1 (General Documents)'),
        ('p2', 'P-2 (Internal Documents)'),
        ('p3', 'P-3 (Confidential Documents)'),
        ('p4', 'P-4 (Secret Documents)'),
        ('p5', 'P-5 (Top Secret Documents)'),
        ('p6', 'P-6 (Highly Classified Documents)'),
        ('p7', 'P-7 (Maximum Security Documents)')
    ], string='Security Level', help='DIN 66399 security level')
    
    particle_size = fields.Char(
        string='Particle Size',
        help='Maximum particle size after destruction (e.g., 2x15mm)'
    )
    
    equipment_used = fields.Char(
        string='Equipment Used',
        help='Specific equipment used for destruction'
    )
    
    equipment_serial_number = fields.Char(
        string='Equipment Serial Number',
        help='Serial number of destruction equipment'
    )
    
    pre_destruction_weight = fields.Float(
        string='Pre-Destruction Weight (lbs)',
        help='Weight of materials before destruction'
    )
    
    post_destruction_weight = fields.Float(
        string='Post-Destruction Weight (lbs)',
        help='Weight of materials after destruction'
    )
    
    destruction_start_time = fields.Datetime(
        string='Destruction Start Time',
        help='When destruction process began'
    )
    
    destruction_end_time = fields.Datetime(
        string='Destruction End Time',
        help='When destruction process completed'
    )
    
    destruction_duration = fields.Float(
        string='Destruction Duration (Hours)',
        compute='_compute_destruction_duration',
        store=True,
        help='Total time for destruction process'
    )
    
    compliance_verified = fields.Boolean(
        string='Compliance Verified',
        default=False,
        help='Whether NAID compliance has been verified'
    )
    
    verification_employee_id = fields.Many2one(
        'hr.employee',
        string='Verified By',
        help='Employee who verified compliance'
    )
    
    verification_date = fields.Datetime(
        string='Verification Date',
        help='When compliance was verified'
    )
    
    # Audit trail
    audit_log_ids = fields.One2many(
        'naid.audit.log',
        compute='_compute_audit_logs',
        string='Related Audit Logs'
    )
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

    @api.depends('destruction_start_time', 'destruction_end_time')
    def _compute_destruction_duration(self):
        """Compute destruction process duration in hours"""
        for record in self:
            if record.destruction_start_time and record.destruction_end_time:
                delta = record.destruction_end_time - record.destruction_start_time
                record.destruction_duration = delta.total_seconds() / 3600.0
            else:
                record.destruction_duration = 0.0

    def _compute_audit_logs(self):
        """Compute related audit logs for this service"""
        for record in self:
            # Get audit logs that reference this service or its components
            logs = self.env['naid.audit.log'].search([
                '|', '|', '|',
                ('service_id', '=', record.id),
                ('box_id', 'in', record.shredded_box_ids.ids),
                ('bale_id', 'in', record.bale_ids.ids),
                ('partner_id', '=', record.customer_id.id)
            ])
            record.audit_log_ids = logs

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
