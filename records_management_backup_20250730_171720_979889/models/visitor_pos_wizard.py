# -*- coding: utf-8 -*-
"""
Wizard to Link POS Transaction to Visitor
"""

from odoo import models, fields, api, _


class VisitorPosWizard(models.Model):
    """
    Wizard to Link POS Transaction to Visitor
    """

    _name = "visitor.pos.wizard"
    _description = "Wizard to Link POS Transaction to Visitor"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Visitor Information
    visitor_id = fields.Many2one('visitor', string='Visitor', required=True)
    visitor_name = fields.Char(string='Visitor Name', related='visitor_id.name', readonly=True)
    visitor_email = fields.Char(string='Email', related='visitor_id.email', readonly=True)
    visitor_phone = fields.Char(string='Phone', related='visitor_id.phone', readonly=True)
    check_in_time = fields.Datetime(string='Check-in Time')
    purpose_of_visit = fields.Char(string='Purpose of Visit')

    # POS Configuration
    pos_config_id = fields.Many2one('pos.config', string='POS Configuration')
    pos_session_id = fields.Many2one('pos.session', string='POS Session')
    cashier_id = fields.Many2one('res.users', string='Cashier')
    service_location = fields.Char(string='Service Location')
    processing_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal')

    # Customer Data Management
    existing_customer_id = fields.Many2one('res.partner', string='Existing Customer')
    create_new_customer = fields.Boolean(string='Create New Customer', default=False)
    customer_record_created = fields.Boolean(string='Customer Record Created', default=False)
    customer_record_id = fields.Many2one('res.partner', string='Customer Record')

    # Service Configuration
    service_type = fields.Selection([
        ('shredding', 'Document Shredding'),
        ('storage', 'Document Storage'),
        ('retrieval', 'Document Retrieval'),
        ('scanning', 'Document Scanning'),
        ('consultation', 'Consultation')
    ], string='Service Type')
    
    product_id = fields.Many2one('product.product', string='Service Product')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_price = fields.Float(string='Unit Price')
    discount_percent = fields.Float(string='Discount %')

    # Transaction Information
    pos_order_id = fields.Many2one('pos.order', string='POS Order')
    pos_order_created = fields.Boolean(string='POS Order Created', default=False)
    transaction_id = fields.Char(string='Transaction ID')
    payment_method_id = fields.Many2one('pos.payment.method', string='Payment Method')
    payment_reference = fields.Char(string='Payment Reference')

    # Financial Calculations
    base_amount = fields.Float(string='Base Amount', compute='_compute_amounts')
    discount_amount = fields.Float(string='Discount Amount', compute='_compute_amounts')
    subtotal = fields.Float(string='Subtotal', compute='_compute_amounts')
    tax_amount = fields.Float(string='Tax Amount', compute='_compute_amounts')
    total_amount = fields.Float(string='Total Amount', compute='_compute_amounts')

    # Service Requirements
    documentation_required = fields.Boolean(string='Documentation Required', default=False)
    certification_required = fields.Boolean(string='Certification Required', default=False)
    witness_required = fields.Boolean(string='Witness Required', default=False)
    chain_of_custody_required = fields.Boolean(string='Chain of Custody Required', default=False)

    # Processing Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('error', 'Error'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)

    processing_start_time = fields.Datetime(string='Processing Start Time')
    processing_end_time = fields.Datetime(string='Processing End Time')
    total_processing_time = fields.Float(string='Total Processing Time (minutes)', compute='_compute_processing_time')

    # Error Handling
    error_message = fields.Text(string='Error Message')
    error_details = fields.Text(string='Error Details')

    # Additional fields for comprehensive functionality
    estimated_service_time = fields.Float(string='Estimated Service Time (minutes)')
    special_requirements = fields.Text(string='Special Requirements')
    internal_notes = fields.Text(string='Internal Notes')
    
    @api.depends('quantity', 'unit_price', 'discount_percent')
    def _compute_amounts(self):
        for record in self:
            record.base_amount = record.quantity * record.unit_price
            record.discount_amount = record.base_amount * (record.discount_percent / 100.0)
            record.subtotal = record.base_amount - record.discount_amount
            # Simplified tax calculation - you may need to use proper tax computation
            record.tax_amount = record.subtotal * 0.1  # Assuming 10% tax
            record.total_amount = record.subtotal + record.tax_amount

    @api.depends('processing_start_time', 'processing_end_time')
    def _compute_processing_time(self):
        for record in self:
            if record.processing_start_time and record.processing_end_time:
                delta = record.processing_end_time - record.processing_start_time
                record.total_processing_time = delta.total_seconds() / 60.0
            else:
                record.total_processing_time = 0.0

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date(default=fields.Date.today)
    action_cancel = fields.Char(string='Action Cancel')
    action_create_pos_order = fields.Char(string='Action Create Pos Order')
    action_link_existing_order = fields.Char(string='Action Link Existing Order')
    action_process_visitor = fields.Char(string='Action Process Visitor')
activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities', auto_join=True)
    amount = fields.Char(string='Amount')
    audit_compliance = fields.Char(string='Audit Compliance')
    audit_level = fields.Char(string='Audit Level')
    audit_notes = fields.Char(string='Audit Notes')
    audit_required = fields.Boolean(string='Audit Required', default=False)
    authorization_code = fields.Char(string='Authorization Code')
    certificate_required = fields.Boolean(string='Certificate Required', default=False)
    chain_of_custody = fields.Char(string='Chain Of Custody')
    chain_of_custody_id = fields.Many2one('chain.of.custody', string='Chain Of Custody Id')
    collected = fields.Char(string='Collected')
    collection_date = fields.Date(string='Collection Date')
    compliance_documentation = fields.Char(string='Compliance Documentation')
    compliance_officer = fields.Char(string='Compliance Officer')
    confidentiality_level = fields.Char(string='Confidentiality Level')
    consultation = fields.Char(string='Consultation')
    context = fields.Char(string='Context')
    customer_category = fields.Char(string='Customer Category')
    customer_created = fields.Char(string='Customer Created')
    customer_credit_limit = fields.Char(string='Customer Credit Limit')
    customer_data = fields.Char(string='Customer Data')
    customer_payment_terms = fields.Char(string='Customer Payment Terms')
    customer_processing_time = fields.Float(string='Customer Processing Time', digits=(12, 2))
    destruction_method = fields.Char(string='Destruction Method')
    digitization_format = fields.Char(string='Digitization Format')
    document_count = fields.Integer(string='Document Count', compute='_compute_document_count', store=True)
    document_name = fields.Char(string='Document Name')
    document_processing = fields.Char(string='Document Processing')
    document_storage = fields.Char(string='Document Storage')
    document_type = fields.Selection([], string='Document Type')  # TODO: Define selection options
    duration_seconds = fields.Char(string='Duration Seconds')
    error_time = fields.Float(string='Error Time', digits=(12, 2))
    error_type = fields.Selection([], string='Error Type')  # TODO: Define selection options
    estimated_volume = fields.Char(string='Estimated Volume')
    express = fields.Char(string='Express')
    express_service = fields.Char(string='Express Service')
    express_surcharge = fields.Char(string='Express Surcharge')
    final_verification_by = fields.Char(string='Final Verification By')
    group_cashier = fields.Char(string='Group Cashier')
    group_date = fields.Date(string='Group Date')
    group_pos_config = fields.Char(string='Group Pos Config')
    group_priority = fields.Selection([], string='Group Priority')  # TODO: Define selection options
    group_service_type = fields.Selection([], string='Group Service Type')  # TODO: Define selection options
    help = fields.Char(string='Help')
    integration_error_ids = fields.One2many('integration.error', 'visitor_pos_wizard_id', string='Integration Error Ids')
    integration_status = fields.Selection([], string='Integration Status')  # TODO: Define selection options
    invoice_generated = fields.Char(string='Invoice Generated')
    invoice_id = fields.Many2one('invoice', string='Invoice Id')
    invoice_required = fields.Boolean(string='Invoice Required', default=False)
message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers', auto_join=True)
message_ids = fields.One2many('mail.message', 'res_id', string='Messages', auto_join=True)
    my_processing = fields.Char(string='My Processing')
    naid_audit_created = fields.Char(string='Naid Audit Created')
    naid_audit_id = fields.Many2one('naid.audit', string='Naid Audit Id')
    naid_certificate_required = fields.Boolean(string='Naid Certificate Required', default=False)
    naid_compliance = fields.Char(string='Naid Compliance')
    naid_compliance_required = fields.Boolean(string='Naid Compliance Required', default=False)
    payment_split_ids = fields.One2many('payment.split', 'visitor_pos_wizard_id', string='Payment Split Ids')
    payment_terms = fields.Char(string='Payment Terms')
    pickup_required = fields.Boolean(string='Pickup Required', default=False)
    pos_config = fields.Char(string='Pos Config')
    pos_created = fields.Char(string='Pos Created')
    pricing_payment = fields.Char(string='Pricing Payment')
    processed_by = fields.Char(string='Processed By')
    processing_history = fields.Char(string='Processing History')
    processing_log_ids = fields.One2many('processing.log', 'visitor_pos_wizard_id', string='Processing Log Ids')
    quality_check_by = fields.Char(string='Quality Check By')
    receipt_email = fields.Char(string='Receipt Email')
    records_request_created = fields.Char(string='Records Request Created')
    records_request_id = fields.Many2one('records.request', string='Records Request Id')
    required = fields.Boolean(string='Required', default=False)
    required_document_ids = fields.One2many('records.document', 'visitor_pos_wizard_id', string='Required Document Ids')
    res_model = fields.Char(string='Res Model')
    resolution_notes = fields.Char(string='Resolution Notes')
    resolved = fields.Char(string='Resolved')
    retention_period = fields.Char(string='Retention Period')
    scanning_required = fields.Boolean(string='Scanning Required', default=False)
    search_view_id = fields.Many2one('search.view', string='Search View Id')
    service_configuration_time = fields.Float(string='Service Configuration Time', digits=(12, 2))
    service_details = fields.Char(string='Service Details')
    service_item_ids = fields.One2many('service.item', 'visitor_pos_wizard_id', string='Service Item Ids')
    service_selection = fields.Char(string='Service Selection')
    shredding = fields.Char(string='Shredding')
    shredding_type = fields.Selection([], string='Shredding Type')  # TODO: Define selection options
    step_description = fields.Char(string='Step Description')
    step_name = fields.Char(string='Step Name')
    step_status = fields.Selection([], string='Step Status')  # TODO: Define selection options
    step_time = fields.Float(string='Step Time', digits=(12, 2))
    supervisor_approval = fields.Char(string='Supervisor Approval')
    target = fields.Char(string='Target')
    tax_id = fields.Many2one('tax', string='Tax Id')
    today = fields.Char(string='Today')
    total_discount = fields.Char(string='Total Discount')
    view_id = fields.Many2one('view', string='View Id')
    view_mode = fields.Char(string='View Mode')
    visitor_info = fields.Char(string='Visitor Info')
    week = fields.Char(string='Week')
    witness_verification = fields.Char(string='Witness Verification')
    wizard_start_time = fields.Float(string='Wizard Start Time', digits=(12, 2))

    @api.depends('document_ids')
    def _compute_document_count(self):
        for record in self:
            record.document_count = len(record.document_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_discount(self):
        for record in self:
            record.total_discount = sum(record.line_ids.mapped('amount'))

    def action_confirm(self):
        """Confirm the record"""
        self.write({'state': 'confirmed'})

    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
