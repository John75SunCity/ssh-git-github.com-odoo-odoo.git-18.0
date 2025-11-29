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
        """Create invoice for this work order"""
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
