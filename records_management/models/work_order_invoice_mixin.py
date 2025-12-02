# -*- coding: utf-8 -*-
"""
Work Order Invoice Mixin

Provides common invoice generation functionality for all work order types.
This mixin can be inherited by any work order model to gain invoice capabilities.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class WorkOrderInvoiceMixin(models.AbstractModel):
    """
    Mixin for adding invoice generation capabilities to work orders.
    
    Inherit this mixin in any work order model to gain:
    - Invoice linking fields
    - action_create_invoice method
    - action_view_invoice method
    - Invoice status tracking
    """
    _name = 'work.order.invoice.mixin'
    _description = 'Work Order Invoice Mixin'

    # ============================================================================
    # CURRENCY (Required for Monetary fields)
    # ============================================================================
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )

    # ============================================================================
    # INVOICE FIELDS
    # ============================================================================
    invoice_id = fields.Many2one(
        comodel_name='account.move',
        string='Invoice',
        readonly=True,
        copy=False,
        help='Invoice generated for this work order'
    )

    invoice_status = fields.Selection([
        ('not_invoiced', 'Not Invoiced'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
    ], string='Invoice Status', compute='_compute_invoice_status', store=True)

    invoiced_amount = fields.Monetary(
        string='Invoiced Amount',
        compute='_compute_invoice_status',
        store=True,
        currency_field='currency_id'
    )

    # ============================================================================
    # BILLING CONFIGURATION
    # ============================================================================
    billable = fields.Boolean(string='Billable', default=True)
    
    pending_consolidated_billing = fields.Boolean(
        string='Pending Consolidated Billing',
        default=False,
        copy=False,
        help='Work order is completed and waiting for consolidated billing cycle'
    )
    
    billing_period_id = fields.Many2one(
        comodel_name='billing.period',
        string='Billing Period',
        readonly=True,
        copy=False,
        help='The billing period in which this work order was invoiced'
    )

    service_product_id = fields.Many2one(
        comodel_name='product.product',
        string='Service Product',
        domain=[('type', '=', 'service')],
        help='Product to use for invoicing this service'
    )

    unit_price = fields.Monetary(
        string='Unit Price',
        currency_field='currency_id',
        help='Price per unit for this service'
    )

    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        help='Quantity of service units'
    )

    subtotal = fields.Monetary(
        string='Subtotal',
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id'
    )

    # ============================================================================
    # CUSTOMER BALANCE FIELDS (For Technician Payment Collection)
    # ============================================================================
    customer_total_balance = fields.Monetary(
        string='Customer Total Balance',
        compute='_compute_customer_balances',
        currency_field='currency_id',
        help='Total outstanding balance for this customer across all invoices'
    )
    
    customer_past_due_balance = fields.Monetary(
        string='Past Due Balance',
        compute='_compute_customer_balances',
        currency_field='currency_id',
        help='Past due balance (invoices past their due date)'
    )
    
    customer_balance_status = fields.Selection([
        ('current', 'Current'),
        ('attention', 'Needs Attention'),
        ('overdue', 'Overdue'),
        ('critical', 'Critical - Collect Payment'),
    ], string='Balance Status', compute='_compute_customer_balances',
       help='Payment status indicator for technicians')
    
    department_total_balance = fields.Monetary(
        string='Department Balance',
        compute='_compute_department_balance',
        currency_field='currency_id',
        help='Outstanding balance for this department (if applicable)'
    )
    
    show_payment_alert = fields.Boolean(
        string='Show Payment Alert',
        compute='_compute_customer_balances',
        help='Flag to highlight customers needing payment collection'
    )

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('invoice_id', 'invoice_id.state', 'invoice_id.payment_state')
    def _compute_invoice_status(self):
        """Compute invoice status based on linked invoice"""
        for record in self:
            if not record.invoice_id:
                record.invoice_status = 'not_invoiced'
                record.invoiced_amount = 0.0
            elif record.invoice_id.payment_state == 'paid':
                record.invoice_status = 'paid'
                record.invoiced_amount = record.invoice_id.amount_total
            else:
                record.invoice_status = 'invoiced'
                record.invoiced_amount = record.invoice_id.amount_total

    @api.depends('unit_price', 'quantity')
    def _compute_subtotal(self):
        """Compute subtotal from price and quantity"""
        for record in self:
            record.subtotal = record.unit_price * record.quantity

    def _compute_customer_balances(self):
        """
        Compute customer balance information for technician payment collection.
        
        Shows total outstanding balance and past due amounts so technicians
        know when to discuss payment with customers during service calls.
        """
        today = fields.Date.today()
        
        for record in self:
            total_balance = 0.0
            past_due_balance = 0.0
            status = 'current'
            show_alert = False
            
            if hasattr(record, 'partner_id') and record.partner_id:
                partner = record.partner_id
                
                # Get all unpaid invoices for this customer
                unpaid_invoices = self.env['account.move'].sudo().search([
                    ('partner_id', '=', partner.id),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                ])
                
                for invoice in unpaid_invoices:
                    total_balance += invoice.amount_residual
                    
                    # Check if past due
                    if invoice.invoice_date_due and invoice.invoice_date_due < today:
                        past_due_balance += invoice.amount_residual
                
                # Determine status based on amounts
                if past_due_balance > 0:
                    days_oldest_due = 0
                    for invoice in unpaid_invoices:
                        if invoice.invoice_date_due and invoice.invoice_date_due < today:
                            days_past = (today - invoice.invoice_date_due).days
                            days_oldest_due = max(days_oldest_due, days_past)
                    
                    if days_oldest_due >= 90 or past_due_balance >= 1000:
                        status = 'critical'
                        show_alert = True
                    elif days_oldest_due >= 60 or past_due_balance >= 500:
                        status = 'overdue'
                        show_alert = True
                    elif days_oldest_due >= 30:
                        status = 'attention'
                        show_alert = True
                elif total_balance > 0:
                    status = 'current'
            
            record.customer_total_balance = total_balance
            record.customer_past_due_balance = past_due_balance
            record.customer_balance_status = status
            record.show_payment_alert = show_alert

    def _compute_department_balance(self):
        """
        Compute department-specific balance if work order has a department.
        
        Useful for organizations with departmental billing where each
        department has its own budget/payment responsibility.
        """
        today = fields.Date.today()
        
        for record in self:
            dept_balance = 0.0
            
            # Check if record has department_id field
            if hasattr(record, 'department_id') and record.department_id:
                department = record.department_id
                
                # Get unpaid invoices tagged to this department
                # This requires invoices to have department tracking
                unpaid_invoices = self.env['account.move'].sudo().search([
                    ('partner_id', '=', record.partner_id.id if hasattr(record, 'partner_id') and record.partner_id else False),
                    ('move_type', '=', 'out_invoice'),
                    ('state', '=', 'posted'),
                    ('payment_state', 'in', ['not_paid', 'partial']),
                ])
                
                # Filter by department if the invoice has department reference
                for invoice in unpaid_invoices:
                    # Check invoice lines for department reference
                    if hasattr(invoice, 'department_id') and invoice.department_id == department:
                        dept_balance += invoice.amount_residual
                    elif hasattr(invoice, 'invoice_origin') and invoice.invoice_origin:
                        # Try to match via work order origin
                        pass  # Could add logic to trace back to department
            
            record.department_total_balance = dept_balance

    # ============================================================================
    # PAYMENT COLLECTION ACTIONS (For Technicians)
    # ============================================================================
    def action_register_payment(self):
        """
        Open payment registration wizard for the customer's unpaid invoices.
        
        This allows technicians to process payments (credit card, check, cash)
        directly from the work order, updating the customer's balance immediately.
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        # Get all unpaid invoices for this customer
        unpaid_invoices = self.env['account.move'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ])
        
        if not unpaid_invoices:
            raise UserError(_("No unpaid invoices found for this customer."))
        
        # Open the payment wizard for all unpaid invoices
        return {
            'name': _('Register Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_ids': unpaid_invoices.ids,
                'default_partner_id': self.partner_id.id,
                # Pass work order info for field collection tracking
                'default_is_field_collection': True,
                'default_work_order_reference': self.name if hasattr(self, 'name') else '',
                'default_collected_by_id': self.env.user.id,
            },
        }

    def action_register_payment_with_proof(self):
        """
        Open payment wizard pre-configured for field collection with payment proof.
        
        This opens a wizard that allows the technician to:
        1. Select payment method (cash, check, credit card)
        2. Take a photo of check/cash as proof
        3. Enter check number if applicable
        4. Add collection notes
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        # Open the field payment wizard
        return {
            'name': _('Collect Payment with Proof'),
            'type': 'ir.actions.act_window',
            'res_model': 'work.order.field.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_amount': self.customer_total_balance,
                'default_work_order_reference': self.name if hasattr(self, 'name') else '',
                'default_work_order_model': self._name,
                'default_work_order_id': self.id,
            },
        }

    def action_view_unpaid_invoices(self):
        """
        Open list of unpaid invoices for this customer.
        
        Allows technicians to see invoice details, select specific
        invoices for payment, or view payment history.
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        # Get all unpaid invoices for this customer
        unpaid_invoices = self.env['account.move'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ])
        
        return {
            'name': _('Unpaid Invoices - %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', unpaid_invoices.ids)],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_move_type': 'out_invoice',
            },
        }

    def action_quick_payment(self):
        """
        Open a simplified payment form for quick field collection.
        
        Pre-populates with customer's total balance for convenience.
        Technician just needs to select payment method and confirm.
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        if self.customer_total_balance <= 0:
            raise UserError(_("No outstanding balance for this customer."))
        
        # Get unpaid invoices
        unpaid_invoices = self.env['account.move'].sudo().search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
        ])
        
        # Open payment wizard with amount pre-filled
        return {
            'name': _('Quick Payment - %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment.register',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'active_model': 'account.move',
                'active_ids': unpaid_invoices.ids,
                'default_partner_id': self.partner_id.id,
                'default_amount': self.customer_total_balance,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
            },
        }

    def action_view_payment_history(self):
        """
        View all payments received from this customer.
        
        Shows payment history for reference during customer conversations.
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        return {
            'name': _('Payment History - %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.payment',
            'view_mode': 'list,form',
            'domain': [
                ('partner_id', '=', self.partner_id.id),
                ('payment_type', '=', 'inbound'),
            ],
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_payment_type': 'inbound',
                'default_partner_type': 'customer',
            },
        }

    def action_field_payment(self):
        """
        Open the field payment wizard for technicians to collect payments.
        
        This wizard allows technicians to:
        - Select payment method (cash, check, credit card)
        - Take a photo of check/cash as proof
        - Enter check number if applicable
        - Add collection notes
        
        Returns the wizard action to open in a popup dialog.
        """
        self.ensure_one()
        
        if not hasattr(self, 'partner_id') or not self.partner_id:
            raise UserError(_("No customer set on this work order."))
        
        # Open the field payment wizard
        return {
            'name': _('Collect Payment'),
            'type': 'ir.actions.act_window',
            'res_model': 'work.order.field.payment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_partner_id': self.partner_id.id,
                'default_amount': self.customer_total_balance,
                'default_work_order_reference': self.name if hasattr(self, 'name') else '',
                'default_work_order_model': self._name,
                'default_work_order_id': self.id,
            },
        }

    # ============================================================================
    # INVOICE GENERATION
    # ============================================================================
    def _prepare_invoice_values(self):
        """
        Prepare values for creating an invoice.
        Override in specific work order models to customize.
        """
        self.ensure_one()

        if not self.partner_id:
            raise UserError(_("Cannot create invoice: No customer set on work order."))

        return {
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_origin': self.name,
            'narration': _('Invoice for %s') % self.name,
            'company_id': self.company_id.id if hasattr(self, 'company_id') and self.company_id else self.env.company.id,
        }

    def _prepare_invoice_line_values(self, invoice):
        """
        Prepare invoice line values.
        Override in specific work order models to customize.
        """
        self.ensure_one()

        # Get product - use service_product_id if set, otherwise find/create a default
        product = self.service_product_id
        if not product:
            product = self._get_default_service_product()

        # Get the description
        name = self._get_invoice_line_description()

        # Determine price - use unit_price if set, otherwise use product price
        price = self.unit_price or (product.lst_price if product else 0.0)

        # Get quantity
        qty = self.quantity or 1.0

        values = {
            'move_id': invoice.id,
            'product_id': product.id if product else False,
            'name': name,
            'quantity': qty,
            'price_unit': price,
            # Records Management tracking fields
            'records_related': True,
            'work_order_reference': self.name,
            'work_order_date': self.scheduled_date.date() if hasattr(self, 'scheduled_date') and self.scheduled_date else fields.Date.today(),
        }

        # Add service type based on model
        service_type = self._get_service_type()
        if service_type:
            values['records_service_type'] = service_type

        return values

    def _get_default_service_product(self):
        """Get or create default service product for this work order type"""
        # Try to find existing product
        product_name = self._get_default_product_name()
        product = self.env['product.product'].search([
            ('name', '=', product_name),
            ('type', '=', 'service')
        ], limit=1)

        if not product:
            # Create the product
            product = self.env['product.product'].create({
                'name': product_name,
                'type': 'service',
                'invoice_policy': 'order',
                'list_price': self._get_default_price(),
                'categ_id': self.env.ref('product.product_category_all').id,
            })

        return product

    def _get_default_product_name(self):
        """Override in subclass to set product name"""
        return _('Records Management Service')

    def _get_default_price(self):
        """Override in subclass to set default price"""
        return 0.0

    def _get_invoice_line_description(self):
        """Override in subclass to customize invoice line description"""
        parts = [self.name]
        if hasattr(self, 'partner_id') and self.partner_id:
            parts.append(_('Customer: %s') % self.partner_id.name)
        if hasattr(self, 'scheduled_date') and self.scheduled_date:
            parts.append(_('Date: %s') % self.scheduled_date.strftime('%Y-%m-%d'))
        return '\n'.join(parts)

    def _get_service_type(self):
        """Override in subclass to return service type for tracking"""
        return False

    def action_create_invoice(self):
        """
        Create invoice for this work order.
        
        Billing Mode Behavior:
        - Immediate Billing (consolidated_billing=False): Creates invoice immediately
        - Consolidated Billing (consolidated_billing=True): Marks as pending for billing period
        """
        self.ensure_one()

        # Validation
        if not self.billable:
            raise UserError(_("This work order is marked as non-billable."))

        if self.invoice_id:
            raise UserError(_("Invoice already exists for this work order: %s") % self.invoice_id.name)

        # Check state - only completed/verified work orders should be invoiced
        valid_states = ['completed', 'verified', 'certified']
        if hasattr(self, 'state') and self.state not in valid_states:
            raise UserError(_("Only completed or verified work orders can be invoiced. Current state: %s") % self.state)

        # Check customer's billing mode
        if hasattr(self, 'partner_id') and self.partner_id and self.partner_id.consolidated_billing:
            # Consolidated billing - mark as pending instead of creating invoice
            self.pending_consolidated_billing = True
            self.message_post(
                body=_('Work order marked for consolidated billing. '
                       'Invoice will be generated during the next billing period.')
            )
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Consolidated Billing'),
                    'message': _('This customer uses consolidated billing. Work order will be invoiced during the next billing period.'),
                    'type': 'info',
                    'sticky': False,
                }
            }

        # Immediate billing - create invoice now
        return self._create_invoice_immediate()
    
    def _create_invoice_immediate(self):
        """Create invoice immediately (used for immediate billing mode)"""
        self.ensure_one()

        # Create invoice
        invoice_vals = self._prepare_invoice_values()
        invoice = self.env['account.move'].create(invoice_vals)

        # Create invoice line
        line_vals = self._prepare_invoice_line_values(invoice)
        self.env['account.move.line'].create(line_vals)

        # Link invoice to work order
        self.invoice_id = invoice.id

        # Update state if model has 'invoiced' state option
        if hasattr(self, 'state') and 'invoiced' in dict(self._fields['state'].selection):
            self.write({'state': 'invoiced'})

        # Log message
        self.message_post(body=_('Invoice %s created') % invoice.name)

        # Return action to view invoice
        return self.action_view_invoice()
    
    def action_force_immediate_invoice(self):
        """
        Force immediate invoice creation even if customer has consolidated billing.
        Use for urgent billing situations.
        """
        self.ensure_one()
        
        if not self.billable:
            raise UserError(_("This work order is marked as non-billable."))
        
        if self.invoice_id:
            raise UserError(_("Invoice already exists for this work order: %s") % self.invoice_id.name)
        
        # Clear pending flag and create invoice immediately
        self.pending_consolidated_billing = False
        return self._create_invoice_immediate()

    def action_view_invoice(self):
        """View the linked invoice"""
        self.ensure_one()

        if not self.invoice_id:
            raise UserError(_("No invoice exists for this work order."))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # BATCH INVOICING
    # ============================================================================
    def action_create_invoices_batch(self):
        """Create invoices for multiple work orders (batch operation)"""
        invoices = self.env['account.move']
        errors = []

        for record in self:
            try:
                if record.billable and not record.invoice_id:
                    record.action_create_invoice()
                    invoices |= record.invoice_id
            except UserError as e:
                errors.append(_('%s: %s') % (record.name, str(e)))

        if errors:
            message = _('Invoices created: %s\n\nErrors:\n%s') % (len(invoices), '\n'.join(errors))
        else:
            message = _('Created %s invoice(s)') % len(invoices)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Invoice Generation'),
                'message': message,
                'type': 'success' if not errors else 'warning',
                'sticky': bool(errors),
            }
        }

    # ============================================================================
    # RESET BILLING
    # ============================================================================
    def action_reset_for_rebilling(self):
        """
        Reset billing status so work order can be billed again.
        
        Use this when:
        - An invoice was created by mistake
        - The invoice needs to be regenerated with different values
        - Testing billing functionality
        
        Note: This does NOT delete the linked invoice - only unlinks it.
        """
        self.ensure_one()
        
        if not self.invoice_id:
            raise UserError(_("This work order has not been invoiced yet."))
        
        invoice_name = self.invoice_id.name
        invoice_state = self.invoice_id.state
        
        # Clear billing fields
        self.write({
            'invoice_id': False,
            'billing_period_id': False,
            'pending_consolidated_billing': False,
        })
        
        # Log the reset in chatter
        self.message_post(
            body=_('Billing status reset for re-billing. '
                   'Previously linked invoice: %s (status: %s)') % (invoice_name, invoice_state)
        )
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Billing Reset'),
                'message': _('Work order %s has been reset and can now be billed again.') % self.name,
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_reset_for_rebilling_batch(self):
        """Reset billing status for multiple work orders"""
        reset_count = 0
        skipped = []
        
        for record in self:
            if record.invoice_id:
                invoice_name = record.invoice_id.name
                record.write({
                    'invoice_id': False,
                    'billing_period_id': False,
                    'pending_consolidated_billing': False,
                })
                record.message_post(
                    body=_('Billing status reset for re-billing (batch operation). '
                           'Previously linked invoice: %s') % invoice_name
                )
                reset_count += 1
            else:
                skipped.append(record.name)
        
        message = _('Reset %d work order(s) for re-billing.') % reset_count
        if skipped:
            message += _(' Skipped %d (not billed): %s') % (len(skipped), ', '.join(skipped[:5]))
            if len(skipped) > 5:
                message += '...'
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Batch Billing Reset'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }
