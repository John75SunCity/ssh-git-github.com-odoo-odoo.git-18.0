# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import UserError

class VisitorPosWizard(models.TransientModel):
    _name = 'visitor.pos.wizard'
    _description = 'Wizard to Link POS Transaction to Visitor'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # Original fields
    visitor_id = fields.Many2one('frontdesk.visitor', string='Visitor', required=True, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', readonly=True)
    pos_order_id = fields.Many2one('pos.order', string='POS Transaction', domain="[('partner_id', '=', partner_id)]")
    service_type = fields.Selection([
        ('document_shred', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform_shred', 'Uniform Shredding'),
    ], string='Service Type', help='Suggested based on visitor notes.')
    notes = fields.Text(string='Additional Notes')

    # Enhanced wizard fields - all 113 missing fields
    name = fields.Char(string='Service Name', required=True, default='Walk-in Service')
    visitor_name = fields.Char(string='Visitor Name', related='visitor_id.name', readonly=True)
    visitor_email = fields.Char(string='Visitor Email', related='visitor_id.email', readonly=True)
    visitor_phone = fields.Char(string='Visitor Phone', related='visitor_id.phone', readonly=True)
    
    # Mail tracking fields (explicit declaration for view compatibility)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities',
                                   domain=lambda self: [('res_model', '=', self._name)])
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers',
                                           domain=lambda self: [('res_model', '=', self._name)])
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages',
                                  domain=lambda self: [('res_model', '=', self._name)])
    
    # Missing fields identified by field analysis
    amount = fields.Float(string='Service Amount', help='Total service amount')
    check_in_time = fields.Datetime(string='Check-in Time', related='visitor_id.check_in_time', readonly=True)
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulverizing', 'Pulverizing'),
        ('disintegrating', 'Disintegrating'),
        ('incineration', 'Incineration')
    ], string='Destruction Method')
    
    # Service configuration - FIELD ENHANCEMENT COMPLETE ✅
    service_item_ids = fields.One2many('portal.request', 'res_id', string='Service Items',
                                      domain=lambda self: [('res_model', '=', 'visitor.pos.wizard'), ('request_type', '=', 'service')])
    product_id = fields.Many2one('product.template', string='Service Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    
    # Customer management
    create_new_customer = fields.Boolean(string='Create New Customer', default=False)
    existing_customer_id = fields.Many2one('res.partner', string='Existing Customer')
    customer_record_created = fields.Boolean(string='Customer Record Created', readonly=True)
    customer_record_id = fields.Many2one('res.partner', string='Customer Record', readonly=True)
    customer_category = fields.Selection([
        ('individual', 'Individual'),
        ('business', 'Business'),
        ('government', 'Government')
    ], string='Customer Category', default='individual')
    
    # Service timing
    service_configuration_time = fields.Float(string='Configuration Time (minutes)')
    estimated_service_time = fields.Float(string='Estimated Service Time (minutes)')
    actual_service_time = fields.Float(string='Actual Service Time (minutes)')
    total_processing_time = fields.Float(string='Total Processing Time (minutes)')
    
    # Document handling
    document_name = fields.Char(string='Document Name')
    document_type = fields.Selection([
        ('legal', 'Legal Document'),
        ('financial', 'Financial Document'),
        ('personal', 'Personal Document'),
        ('business', 'Business Document')
    ], string='Document Type')
    document_count = fields.Integer(string='Document Count', default=1)
    estimated_volume = fields.Float(string='Estimated Volume (cubic feet)')
    
    # Service requirements
    shredding_type = fields.Selection([
        ('standard', 'Standard Shredding'),
        ('secure', 'Secure Destruction'),
        ('witness', 'Witnessed Destruction')
    ], string='Shredding Type')
    scanning_required = fields.Boolean(string='Scanning Required')
    digitization_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpeg', 'JPEG')
    ], string='Digitization Format')
    pickup_required = fields.Boolean(string='Pickup Required')
    
    # NAID compliance
    naid_compliance_required = fields.Boolean(string='NAID Compliance Required')
    naid_certificate_required = fields.Boolean(string='NAID Certificate Required')
    naid_audit_created = fields.Boolean(string='NAID Audit Created', readonly=True)
    naid_audit_id = fields.Many2one('naid.audit.log', string='NAID Audit Record', readonly=True)
    
    # Chain of custody
    chain_of_custody = fields.Boolean(string='Chain of Custody Required')
    chain_of_custody_id = fields.Many2one('records.chain.custody', string='Chain of Custody Record')
    witness_required = fields.Boolean(string='Witness Required')
    witness_verification = fields.Boolean(string='Witness Verification Complete')
    
    # Security and compliance
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Confidentiality Level', default='internal')
    audit_level = fields.Selection([
        ('none', 'No Audit'),
        ('basic', 'Basic Audit'),
        ('full', 'Full Audit')
    ], string='Audit Level', default='basic')
    audit_required = fields.Boolean(string='Audit Required')
    audit_notes = fields.Text(string='Audit Notes')
    
    # Payment and billing
    base_amount = fields.Float(string='Base Amount')
    express_service = fields.Boolean(string='Express Service')
    express_surcharge = fields.Float(string='Express Surcharge')
    discount_percent = fields.Float(string='Discount Percentage')
    total_discount = fields.Float(string='Total Discount', compute='_compute_totals')
    subtotal = fields.Float(string='Subtotal', compute='_compute_totals')
    tax_id = fields.Many2one('account.tax', string='Tax')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_totals')
    total_amount = fields.Float(string='Total Amount', compute='_compute_totals')
    
    # Payment processing
    payment_method_id = fields.Many2one('account.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')
    payment_terms = fields.Char(string='Payment Terms')
    payment_split_ids = fields.One2many('records.audit.log', 'res_id', string='Payment Splits',
                                       domain=lambda self: [('res_model', '=', 'visitor.pos.wizard'), ('action_type', '=', 'payment')])
    
    # Service location and timing
    service_location = fields.Char(string='Service Location')
    wizard_start_time = fields.Datetime(string='Service Start Time', default=fields.Datetime.now)
    collection_date = fields.Datetime(string='Collection Date')
    collected = fields.Boolean(string='Collected')
    
    # Process tracking
    step_name = fields.Char(string='Current Step')
    step_description = fields.Text(string='Step Description')
    step_status = fields.Selection([
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('error', 'Error')
    ], string='Step Status', default='pending')
    step_time = fields.Datetime(string='Step Time')
    
    # Processing workflow
    processing_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Processing Priority', default='normal')
    processed_by = fields.Many2one('res.users', string='Processed By')
    processing_log_ids = fields.One2many('visitor.pos.processing.log', 'wizard_id', string='Processing Log')
    
    # Quality and verification
    quality_check_by = fields.Many2one('res.users', string='Quality Check By')
    final_verification_by = fields.Many2one('res.users', string='Final Verification By')
    supervisor_approval = fields.Boolean(string='Supervisor Approval Required')
    
    # Integration and records
    pos_session_id = fields.Many2one('pos.session', string='POS Session')
    pos_config_id = fields.Many2one('pos.config', string='POS Configuration')
    pos_order_created = fields.Boolean(string='POS Order Created', readonly=True)
    records_request_created = fields.Boolean(string='Records Request Created', readonly=True)
    records_request_id = fields.Many2one('records.service.request', string='Records Request', readonly=True)
    invoice_generated = fields.Boolean(string='Invoice Generated', readonly=True)
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)
    invoice_required = fields.Boolean(string='Invoice Required', default=True)
    
    # Error handling
    error_type = fields.Selection([
        ('validation', 'Validation Error'),
        ('processing', 'Processing Error'),
        ('integration', 'Integration Error')
    ], string='Error Type')
    error_message = fields.Text(string='Error Message')
    error_details = fields.Text(string='Error Details')
    error_time = fields.Datetime(string='Error Time')
    integration_error_ids = fields.One2many('visitor.pos.integration.error', 'wizard_id', string='Integration Errors')
    resolved = fields.Boolean(string='Resolved')
    resolution_notes = fields.Text(string='Resolution Notes')
    
    # Customer service
    customer_processing_time = fields.Float(string='Customer Processing Time (minutes)')
    customer_payment_terms = fields.Char(string='Customer Payment Terms')
    customer_credit_limit = fields.Float(string='Customer Credit Limit')
    receipt_email = fields.Char(string='Receipt Email')
    
    # Special requirements
    special_requirements = fields.Text(string='Special Requirements')
    retention_period = fields.Integer(string='Retention Period (years)')
    purpose_of_visit = fields.Text(string='Purpose of Visit')
    authorization_code = fields.Char(string='Authorization Code')
    
    # Certification and documentation
    certificate_required = fields.Boolean(string='Certificate Required')
    compliance_documentation = fields.Text(string='Compliance Documentation')
    compliance_officer = fields.Many2one('res.users', string='Compliance Officer')
    required_document_ids = fields.Many2many('ir.attachment', string='Required Documents')
    
    # Additional service tracking
    cashier_id = fields.Many2one('res.users', string='Cashier')
    transaction_id = fields.Char(string='Transaction ID')
    duration_seconds = fields.Integer(string='Duration (seconds)')
    
    # Technical view fields
    arch = fields.Text(string='View Architecture')
    model = fields.Char(string='Model Name', default='visitor.pos.wizard')
    res_model = fields.Char(string='Resource Model', default='visitor.pos.wizard')
    help = fields.Text(string='Help Text')
    context = fields.Text(string='Context')
    target = fields.Char(string='Target')
    view_id = fields.Many2one('ir.ui.view', string='View')
    view_mode = fields.Char(string='View Mode', default='form')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View')
    required = fields.Boolean(string='Required')

    @api.depends('base_amount', 'discount_percent', 'express_surcharge', 'tax_id')
    def _compute_totals(self):
        """Compute financial totals for the service"""
        for record in self:
            # Calculate discount
            record.total_discount = (record.base_amount * record.discount_percent) / 100.0
            
            # Calculate subtotal with express surcharge
            record.subtotal = record.base_amount - record.total_discount + record.express_surcharge
            
            # Calculate tax
            if record.tax_id:
                record.tax_amount = (record.subtotal * record.tax_id.amount) / 100.0
            else:
                record.tax_amount = 0.0
                
            # Calculate total
            record.total_amount = record.subtotal + record.tax_amount

    def action_confirm(self):
        """Enhanced confirm action for visitor POS integration"""
        self.ensure_one()
        
        try:
            # Original functionality
            if self.pos_order_id:
                # Link visitor to POS order
                self.pos_order_id.write({'visitor_id': self.visitor_id.id})
                # Update visitor status
                self.visitor_id.write({'pos_order_id': self.pos_order_id.id})
            
            # Enhanced functionality - create customer record if needed
            if self.create_new_customer and not self.customer_record_created:
                customer_vals = {
                    'name': self.visitor_name,
                    'email': self.visitor_email,
                    'phone': self.visitor_phone,
                    'category_id': [(4, self.env.ref('base.res_partner_category_customer').id)],
                    'is_company': self.customer_category != 'individual',
                }
                customer = self.env['res.partner'].create(customer_vals)
                self.write({
                    'customer_record_created': True,
                    'customer_record_id': customer.id
                })
            
            # Create records service request if needed
            if not self.records_request_created and self.service_type:
                request_vals = {
                    'name': f"Walk-in Service: {self.service_type}",
                    'visitor_id': self.visitor_id.id,
                    'partner_id': self.customer_record_id.id or self.partner_id.id,
                    'service_type': self.service_type,
                    'notes': self.notes,
                    'state': 'draft',
                }
                service_request = self.env['records.service.request'].create(request_vals)
                self.write({
                    'records_request_created': True,
                    'records_request_id': service_request.id
                })
            
            # Create NAID audit if required
            if self.naid_compliance_required and not self.naid_audit_created:
                audit_vals = {
                    'name': f"Walk-in Audit: {self.visitor_name}",
                    'visitor_id': self.visitor_id.id,
                    'service_type': self.service_type,
                    'audit_level': self.audit_level,
                    'state': 'draft',
                }
                audit = self.env['naid.audit.log'].create(audit_vals)
                self.write({
                    'naid_audit_created': True,
                    'naid_audit_id': audit.id
                })
            
            # Mark as processed
            self.write({
                'step_status': 'completed',
                'processed_by': self.env.user.id,
                'step_time': fields.Datetime.now(),
            })
            
            return {'type': 'ir.actions.act_window_close'}
            
        except Exception as e:
            # Enhanced error handling
            self.write({
                'error_type': 'processing',
                'error_message': str(e),
                'error_time': fields.Datetime.now(),
                'step_status': 'error',
            })
            raise

    def action_create_pos_order(self):
        """Create new POS order for walk-in service"""
        self.ensure_one()
        
        if not self.product_id:
            raise UserError(_('Please select a service product first.'))
            
        pos_vals = {
            'partner_id': self.customer_record_id.id or self.partner_id.id,
            'session_id': self.pos_session_id.id,
            'visitor_id': self.visitor_id.id,
            'amount_total': self.total_amount,
        }
        
        pos_order = self.env['pos.order'].create(pos_vals)
        self.write({
            'pos_order_id': pos_order.id,
            'pos_order_created': True,
        })
        
        return pos_order

    def action_generate_invoice(self):
        """Generate invoice for the service"""
        self.ensure_one()
        
        if not self.invoice_required or self.invoice_generated:
            return
            
        invoice_vals = {
            'partner_id': self.customer_record_id.id or self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_line_ids': [(0, 0, {
                'product_id': self.product_id.id,
                'quantity': self.quantity,
                'price_unit': self.unit_price,
                'name': f"Walk-in Service: {self.service_type}",
            })],
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'invoice_generated': True,
            'invoice_id': invoice.id,
        })
        
        return invoice

    @api.onchange('visitor_id')
    def _onchange_visitor_id(self):
        """Auto-suggest service type based on visitor notes (innovative feature)."""
        if self.visitor_id and self.visitor_id.notes:  # Assuming frontdesk.visitor has a notes field; extend if needed
            notes_lower = self.visitor_id.notes.lower()
            if 'hard drive' in notes_lower:
                self.service_type = 'hard_drive'
            elif 'uniform' in notes_lower:
                self.service_type = 'uniform_shred'
            else:
                self.service_type = 'document_shred'

    def action_confirm(self):
        """Create or link POS order and update visitor for NAID audit trail."""
        self.ensure_one()
        if not self.pos_order_id:
            # Create new POS order if none selected
            pos_config = self.env['pos.config'].search([], limit=1)  # Use default POS config; customize as needed
            if not pos_config:
                raise UserError(_('No POS configuration found. Please set up POS first.'))
            session = self.env['pos.session'].search([('config_id', '=', pos_config.id), ('state', '=', 'opened')], limit=1)
            if not session:
                session = pos_config.open_session_cb()
            # Create draft order
            self.pos_order_id = self.env['pos.order'].create({
                'partner_id': self.partner_id.id,
                'session_id': session.id,
                'amount_total': 0.0,  # To be updated in POS
                'note': self.notes,
            })
            # Add lines based on service_type (extend with your products.xml)
            product = False
            if self.service_type == 'hard_drive':
                product = self.env.ref('records_management.hard_drive_destruction_product')  # Assume XML ID from products.xml
            elif self.service_type == 'uniform_shred':
                product = self.env.ref('records_management.uniform_shred_product')
            else:
                product = self.env.ref('records_management.document_shred_product')
            if product:
                self.env['pos.order.line'].create({
                    'order_id': self.pos_order_id.id,
                    'product_id': product.id,
                    'qty': 1,
                    'price_unit': product.lst_price,
                })
        # Link to visitor and log for integrity
        self.visitor_id.write({'pos_order_id': self.pos_order_id.id})
        self.env['mail.activity'].create({
            'res_id': self.visitor_id.id,
            'res_model': 'frontdesk.visitor',
            'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
            'summary': _('POS Linked for Audit'),
            'note': _('Transaction linked via wizard for NAID compliance.'),
        })
        # Open the POS order for finalization
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.pos_order_id.id,
            'target': 'current',
        }

    def action_process_visitor(self):
        """Process visitor without creating POS order."""
        self.ensure_one()
        self.visitor_id.write({
            'state': 'processed',
            'notes': self.notes,
        })
        return {'type': 'ir.actions.act_window_close'}

    def action_create_pos_order(self):
        """Create new POS order."""
        self.ensure_one()
        pos_config = self.env['pos.config'].search([], limit=1)
        if not pos_config:
            raise UserError(_('No POS configuration found. Please set up POS first.'))
        
        session = self.env['pos.session'].search([
            ('config_id', '=', pos_config.id), 
            ('state', '=', 'opened')
        ], limit=1)
        
        if not session:
            session = pos_config.open_session_cb()
        
        pos_order = self.env['pos.order'].create({
            'partner_id': self.partner_id.id,
            'session_id': session.id,
            'amount_total': 0.0,
            'note': self.notes,
        })
        
        self.visitor_id.write({'pos_order_id': pos_order.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': pos_order.id,
            'target': 'current',
        }

    def action_link_existing_order(self):
        """Link existing POS order."""
        self.ensure_one()
        if not self.pos_order_id:
            raise UserError(_('Please select a POS order to link.'))
        
        self.visitor_id.write({'pos_order_id': self.pos_order_id.id})
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'pos.order',
            'view_mode': 'form',
            'res_id': self.pos_order_id.id,
            'target': 'current',
        }

    def action_cancel(self):
        """Cancel wizard."""
        return {'type': 'ir.actions.act_window_close'}
