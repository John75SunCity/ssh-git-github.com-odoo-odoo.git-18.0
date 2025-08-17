from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class AdvancedBilling(models.Model):
    _name = 'advanced.billing'
    _description = 'Advanced Billing'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True, tracking=True, index=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    
    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    billing_period_id = fields.Many2one('billing.period', string='Billing Period')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id)
    invoice_id = fields.Many2one('account.move', string='Generated Invoice', readonly=True)
    
    payment_terms = fields.Selection([
        ('immediate', 'Immediate'),
        ('15_days', '15 Days'),
        ('30_days', '30 Days'),
        ('45_days', '45 Days'),
        ('60_days', '60 Days'),
    ], string='Payment Terms', default='30_days')
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True)
    
    # Line relationships
    line_ids = fields.One2many('advanced.billing.line', 'billing_id', string='Billing Lines')
    service_line_ids = fields.One2many('advanced.billing.service.line', 'billing_id', string='Service Lines')
    storage_line_ids = fields.One2many('advanced.billing.storage.line', 'billing_id', string='Storage Lines')
    
    # Financial fields
    total_amount = fields.Monetary(string='Total Amount', currency_field='currency_id', compute='_compute_total_amount', store=True)
    service_amount = fields.Float(string='Service Amount')
    storage_amount = fields.Float(string='Storage Amount')
    
    # ============================================================================
    # BILLING CONFIGURATION FIELDS
    # ============================================================================
    billing_type = fields.Selection([
        ('service', 'Service Billing'),
        ('storage', 'Storage Billing'),
        ('combined', 'Combined Billing'),
    ], string='Billing Type', default='combined')
    
    billing_day = fields.Integer(string='Billing Day', default=1, help='Day of month for billing')
    
    # Dates
    invoice_date = fields.Date(string='Invoice Date')
    period_start_date = fields.Date(string='Period Start Date')
    period_end_date = fields.Date(string='Period End Date')
    
    # Contact information
    email = fields.Char(string='Email')
    phone = fields.Char(string='Phone')
    primary_contact = fields.Char(string='Primary Contact')
    
    # Prepaid configuration
    prepaid_enabled = fields.Boolean(string='Prepaid Enabled')
    prepaid_balance = fields.Monetary(string='Prepaid Balance', currency_field='currency_id')
    prepaid_discount_percent = fields.Float(string='Prepaid Discount %')
    prepaid_months = fields.Integer(string='Prepaid Months')
    
    # Automation settings
    auto_generate_service_invoices = fields.Boolean(string='Auto Generate Service Invoices')
    auto_generate_storage_invoices = fields.Boolean(string='Auto Generate Storage Invoices')
    auto_send_invoices = fields.Boolean(string='Auto Send Invoices')
    
    # Billing preferences
    receive_service_invoices = fields.Boolean(string='Receive Service Invoices', default=True)
    receive_statements = fields.Boolean(string='Receive Statements', default=True)
    receive_storage_invoices = fields.Boolean(string='Receive Storage Invoices', default=True)
    
    # Work order relationships
    retrieval_work_order_id = fields.Many2one('document.retrieval.work.order', string='Retrieval Work Order')
    shredding_work_order_id = fields.Many2one('shredding.service', string='Shredding Work Order')
    
    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', 'res_id', string='Followers')
    message_ids = fields.One2many('mail.message', 'res_id', string='Messages')
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('line_ids', 'line_ids.price_total', 'service_line_ids', 'service_line_ids.subtotal', 'storage_line_ids', 'storage_line_ids.subtotal')
    def _compute_total_amount(self):
        """Calculate total amount from all billing lines"""
        for record in self:
            line_total = sum(record.line_ids.mapped('price_total'))
            service_total = sum(record.service_line_ids.mapped('subtotal'))
            storage_total = sum(record.storage_line_ids.mapped('subtotal'))
            record.total_amount = line_total + service_total + storage_total

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm billing"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_("Only draft billing can be confirmed"))
        
        if not self.line_ids and not self.service_line_ids and not self.storage_line_ids:
            raise ValidationError(_("Cannot confirm billing without any lines"))
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Advanced billing confirmed"))

    def action_generate_invoice(self):
        """Generate invoice from billing lines"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise ValidationError(_("Only confirmed billing can be invoiced"))
        
        if not self.partner_id:
            raise ValidationError(_("Customer is required to generate invoice"))
        
        # Prepare invoice lines
        invoice_lines = []
        for line in self.line_ids:
            invoice_lines.append((0, 0, {
                'product_id': line.product_id.id if line.product_id else False,
                'name': line.name or line.description,
                'quantity': line.quantity,
                'price_unit': line.price_unit,
                'tax_ids': [(6, 0, line.tax_ids.ids)] if line.tax_ids else False,
            }))
        
        # Add service lines
        for line in self.service_line_ids:
            invoice_lines.append((0, 0, {
                'name': _("Service: %s", line.name),
                'quantity': 1,
                'price_unit': line.subtotal,
            }))
        
        # Add storage lines
        for line in self.storage_line_ids:
            invoice_lines.append((0, 0, {
                'name': _("Storage: %s", line.name),
                'quantity': 1,
                'price_unit': line.subtotal,
            }))
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'currency_id': self.currency_id.id,
            'invoice_date': self.invoice_date or fields.Date.today(),
            'invoice_line_ids': invoice_lines,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'state': 'invoiced',
            'invoice_id': invoice.id,
        })
        
        self.message_post(body=_("Invoice generated: %s", invoice.name))
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Generated Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_done(self):
        """Mark billing as done"""
        self.ensure_one()
        if self.state != 'invoiced':
            raise ValidationError(_("Only invoiced billing can be marked as done"))
        
        self.write({'state': 'done'})
        self.message_post(body=_("Advanced billing completed"))

    def action_cancel(self):
        """Cancel billing"""
        self.ensure_one()
        if self.state in ['invoiced', 'done']:
            raise ValidationError(_("Cannot cancel invoiced or completed billing"))
        
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Advanced billing cancelled"))

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('total_amount')
    def _check_total_amount(self):
        """Validate total amount is not negative"""
        for record in self:
            if record.total_amount < 0:
                raise ValidationError(_("Total amount cannot be negative"))

    @api.constrains('period_start_date', 'period_end_date')
    def _check_period_dates(self):
        """Validate period dates are logical"""
        for record in self:
            if record.period_start_date and record.period_end_date:
                if record.period_end_date < record.period_start_date:
                    raise ValidationError(_("Period end date cannot be before start date"))

    @api.constrains('billing_day')
    def _check_billing_day(self):
        """Validate billing day is within valid range"""
        for record in self:
            if record.billing_day and (record.billing_day < 1 or record.billing_day > 31):
                raise ValidationError(_("Billing day must be between 1 and 31"))

    @api.constrains('prepaid_discount_percent')
    def _check_prepaid_discount(self):
        """Validate prepaid discount percentage"""
        for record in self:
            if record.prepaid_discount_percent and (record.prepaid_discount_percent < 0 or record.prepaid_discount_percent > 100):
                raise ValidationError(_("Prepaid discount percentage must be between 0 and 100"))

