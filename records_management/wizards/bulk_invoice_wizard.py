# -*- coding: utf-8 -*-
"""
Bulk Invoice Generation Wizard

Wizard for generating invoices from multiple completed work orders,
storage fees, and other billable records management services.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class BulkInvoiceWizard(models.TransientModel):
    """
    Wizard for bulk invoice generation from Records Management services.
    
    Allows users to:
    - Select multiple completed work orders
    - Include monthly storage fees
    - Generate consolidated or individual invoices
    - Preview billing before generation
    """
    _name = 'bulk.invoice.wizard'
    _description = 'Bulk Invoice Generation Wizard'

    # ============================================================================
    # CONFIGURATION
    # ============================================================================
    invoice_mode = fields.Selection([
        ('individual', 'One Invoice per Work Order'),
        ('consolidated', 'Consolidated by Customer'),
    ], string='Invoice Mode', default='consolidated', required=True,
       help="Individual: Creates separate invoice for each work order\n"
            "Consolidated: Groups all services by customer into single invoice")
    
    include_storage_fees = fields.Boolean(
        string='Include Storage Fees',
        default=True,
        help='Include monthly storage fees in the invoice'
    )
    
    billing_period_id = fields.Many2one(
        comodel_name='billing.period',
        string='Billing Period',
        help='Billing period for storage fees (if included)'
    )
    
    invoice_date = fields.Date(
        string='Invoice Date',
        default=fields.Date.today,
        required=True
    )
    
    # ============================================================================
    # WORK ORDER SELECTIONS
    # ============================================================================
    retrieval_order_ids = fields.Many2many(
        comodel_name='work.order.retrieval',
        relation='bulk_invoice_wizard_retrieval_rel',
        column1='wizard_id',
        column2='order_id',
        string='Retrieval Work Orders',
        domain=[('state', '=', 'completed'), ('billable', '=', True), ('invoice_id', '=', False)]
    )
    
    shredding_order_ids = fields.Many2many(
        comodel_name='work.order.shredding',
        relation='bulk_invoice_wizard_shredding_rel',
        column1='wizard_id',
        column2='order_id',
        string='Shredding Work Orders',
        domain=[('state', 'in', ['completed', 'verified']), ('invoice_id', '=', False)]
    )
    
    # ============================================================================
    # CUSTOMER FILTER
    # ============================================================================
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        relation='bulk_invoice_wizard_partner_rel',
        column1='wizard_id',
        column2='partner_id',
        string='Filter by Customers',
        help='Leave empty to include all customers'
    )
    
    # ============================================================================
    # PREVIEW / SUMMARY
    # ============================================================================
    preview_html = fields.Html(
        string='Billing Preview',
        compute='_compute_preview',
        readonly=True
    )
    
    total_work_orders = fields.Integer(
        string='Total Work Orders',
        compute='_compute_totals'
    )
    
    total_amount = fields.Float(
        string='Total Amount',
        compute='_compute_totals'
    )
    
    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('retrieval_order_ids', 'shredding_order_ids', 'include_storage_fees')
    def _compute_totals(self):
        """Compute summary totals"""
        for wizard in self:
            wizard.total_work_orders = len(wizard.retrieval_order_ids) + len(wizard.shredding_order_ids)
            
            total = 0.0
            for order in wizard.retrieval_order_ids:
                total += order.subtotal or order.actual_cost or order.estimated_cost or 0.0
            for order in wizard.shredding_order_ids:
                total += order.total_billable_amount if hasattr(order, 'total_billable_amount') else 0.0
            
            wizard.total_amount = total
    
    @api.depends('retrieval_order_ids', 'shredding_order_ids', 'include_storage_fees', 'invoice_mode')
    def _compute_preview(self):
        """Generate HTML preview of billing"""
        for wizard in self:
            html = '<div class="table-responsive">'
            html += '<table class="table table-sm table-bordered">'
            html += '<thead class="table-light"><tr>'
            html += '<th>Customer</th><th>Type</th><th>Reference</th><th>Amount</th>'
            html += '</tr></thead><tbody>'
            
            # Group by customer if consolidated
            customer_totals = {}
            
            for order in wizard.retrieval_order_ids:
                partner = order.partner_id.name
                amount = order.subtotal or order.actual_cost or order.estimated_cost or 0.0
                if partner not in customer_totals:
                    customer_totals[partner] = {'retrieval': 0, 'shredding': 0, 'storage': 0}
                customer_totals[partner]['retrieval'] += amount
                
                if wizard.invoice_mode == 'individual':
                    html += f'<tr><td>{partner}</td><td>Retrieval</td><td>{order.name}</td><td>${amount:,.2f}</td></tr>'
            
            for order in wizard.shredding_order_ids:
                partner = order.partner_id.name
                amount = order.total_billable_amount if hasattr(order, 'total_billable_amount') else 0.0
                if partner not in customer_totals:
                    customer_totals[partner] = {'retrieval': 0, 'shredding': 0, 'storage': 0}
                customer_totals[partner]['shredding'] += amount
                
                if wizard.invoice_mode == 'individual':
                    html += f'<tr><td>{partner}</td><td>Shredding</td><td>{order.name}</td><td>${amount:,.2f}</td></tr>'
            
            if wizard.invoice_mode == 'consolidated':
                for partner, totals in customer_totals.items():
                    total = sum(totals.values())
                    html += f'<tr><td><strong>{partner}</strong></td><td>All Services</td>'
                    html += f'<td>Consolidated</td><td><strong>${total:,.2f}</strong></td></tr>'
            
            html += '</tbody></table></div>'
            
            # Summary
            html += f'<div class="alert alert-info mt-3">'
            html += f'<strong>Summary:</strong> {wizard.total_work_orders} work orders, '
            html += f'Total: ${wizard.total_amount:,.2f}'
            html += '</div>'
            
            wizard.preview_html = html
    
    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_load_billable_orders(self):
        """Load all billable orders that haven't been invoiced"""
        self.ensure_one()
        
        # Build domain
        domain_retrieval = [
            ('state', '=', 'completed'),
            ('billable', '=', True),
            ('invoice_id', '=', False)
        ]
        domain_shredding = [
            ('state', 'in', ['completed', 'verified']),
            ('invoice_id', '=', False)
        ]
        
        if self.partner_ids:
            domain_retrieval.append(('partner_id', 'in', self.partner_ids.ids))
            domain_shredding.append(('partner_id', 'in', self.partner_ids.ids))
        
        retrieval_orders = self.env['work.order.retrieval'].search(domain_retrieval)
        shredding_orders = self.env['work.order.shredding'].search(domain_shredding)
        
        self.write({
            'retrieval_order_ids': [(6, 0, retrieval_orders.ids)],
            'shredding_order_ids': [(6, 0, shredding_orders.ids)],
        })
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_generate_invoices(self):
        """Generate invoices based on wizard configuration"""
        self.ensure_one()
        
        if not self.retrieval_order_ids and not self.shredding_order_ids:
            raise UserError(_("No work orders selected for invoicing."))
        
        invoices = self.env['account.move']
        
        if self.invoice_mode == 'individual':
            invoices = self._generate_individual_invoices()
        else:
            invoices = self._generate_consolidated_invoices()
        
        # Show results
        if len(invoices) == 1:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Generated Invoice'),
                'res_model': 'account.move',
                'res_id': invoices.id,
                'view_mode': 'form',
                'target': 'current',
            }
        else:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Generated Invoices'),
                'res_model': 'account.move',
                'view_mode': 'tree,form',
                'domain': [('id', 'in', invoices.ids)],
                'target': 'current',
            }
    
    def _generate_individual_invoices(self):
        """Generate one invoice per work order"""
        invoices = self.env['account.move']
        
        for order in self.retrieval_order_ids:
            try:
                order.action_create_invoice()
                if order.invoice_id:
                    invoices |= order.invoice_id
            except Exception as e:
                order.message_post(body=_('Invoice generation failed: %s') % str(e))
        
        for order in self.shredding_order_ids:
            try:
                order.action_create_invoice()
                if order.invoice_id:
                    invoices |= order.invoice_id
            except Exception as e:
                order.message_post(body=_('Invoice generation failed: %s') % str(e))
        
        return invoices
    
    def _generate_consolidated_invoices(self):
        """Generate one invoice per customer with all their services"""
        invoices = self.env['account.move']
        
        # Group orders by customer
        orders_by_partner = {}
        
        for order in self.retrieval_order_ids:
            partner_id = order.partner_id.id
            if partner_id not in orders_by_partner:
                orders_by_partner[partner_id] = {'retrieval': [], 'shredding': [], 'partner': order.partner_id}
            orders_by_partner[partner_id]['retrieval'].append(order)
        
        for order in self.shredding_order_ids:
            partner_id = order.partner_id.id
            if partner_id not in orders_by_partner:
                orders_by_partner[partner_id] = {'retrieval': [], 'shredding': [], 'partner': order.partner_id}
            orders_by_partner[partner_id]['shredding'].append(order)
        
        # Create one invoice per customer
        for partner_id, data in orders_by_partner.items():
            partner = data['partner']
            
            # Create invoice header
            invoice_vals = {
                'move_type': 'out_invoice',
                'partner_id': partner_id,
                'invoice_date': self.invoice_date,
                'invoice_origin': ', '.join(
                    [o.name for o in data['retrieval']] + 
                    [o.name for o in data['shredding']]
                )[:200],  # Truncate if too long
                'narration': _('Consolidated invoice for Records Management services'),
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            
            # Add retrieval lines
            for order in data['retrieval']:
                self._create_invoice_line_from_retrieval(invoice, order)
                order.invoice_id = invoice.id
                order.state = 'invoiced' if hasattr(order, 'state') else order.state
            
            # Add shredding lines  
            for order in data['shredding']:
                self._create_invoice_lines_from_shredding(invoice, order)
                order.invoice_id = invoice.id
                order.state = 'invoiced'
            
            invoices |= invoice
        
        return invoices
    
    def _create_invoice_line_from_retrieval(self, invoice, order):
        """Create invoice line from retrieval work order"""
        # Get or create service product
        product = order.service_product_id or self._get_retrieval_product()
        
        price = order.unit_price or order.actual_cost or order.estimated_cost or product.lst_price
        qty = order.quantity or order.total_boxes or 1
        
        line_vals = {
            'move_id': invoice.id,
            'product_id': product.id if product else False,
            'name': _('Retrieval Service - %s\nBoxes: %d') % (order.name, order.total_boxes or 0),
            'quantity': qty,
            'price_unit': price / qty if qty else price,
            # Records Management tracking
            'records_related': True,
            'records_service_type': 'retrieval',
            'work_order_reference': order.name,
        }
        
        if order.retrieval_item_ids:
            container_ids = order.retrieval_item_ids.mapped('box_id').ids
            if container_ids:
                line_vals['container_ids'] = [(6, 0, container_ids)]
                line_vals['container_count'] = len(container_ids)
        
        self.env['account.move.line'].create(line_vals)
    
    def _create_invoice_lines_from_shredding(self, invoice, order):
        """Create invoice lines from shredding work order"""
        # Get or create service product
        product = self._get_shredding_product()
        
        # If order has service events, create line per event
        if hasattr(order, 'service_event_ids') and order.service_event_ids:
            for event in order.service_event_ids.filtered(lambda e: e.is_billable):
                line_vals = {
                    'move_id': invoice.id,
                    'product_id': product.id if product else False,
                    'name': _('Shredding - %s - Bin %s') % (
                        order.name,
                        event.bin_id.barcode if event.bin_id else 'N/A'
                    ),
                    'quantity': 1,
                    'price_unit': event.billable_amount,
                    # Records Management tracking
                    'records_related': True,
                    'records_service_type': 'destruction',
                    'work_order_reference': order.name,
                }
                self.env['account.move.line'].create(line_vals)
        else:
            # Single line for the order
            price = order.total_billable_amount if hasattr(order, 'total_billable_amount') else 0.0
            line_vals = {
                'move_id': invoice.id,
                'product_id': product.id if product else False,
                'name': _('Shredding Service - %s') % order.name,
                'quantity': 1,
                'price_unit': price,
                'records_related': True,
                'records_service_type': 'destruction',
                'work_order_reference': order.name,
            }
            self.env['account.move.line'].create(line_vals)
    
    def _get_retrieval_product(self):
        """Get or create retrieval service product"""
        product = self.env['product.product'].search([
            ('name', '=', 'Records Retrieval Service'),
            ('type', '=', 'service')
        ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Records Retrieval Service',
                'type': 'service',
                'list_price': 25.0,
                'invoice_policy': 'order',
            })
        
        return product
    
    def _get_shredding_product(self):
        """Get or create shredding service product"""
        product = self.env.ref('records_management.product_shredding_service', raise_if_not_found=False)
        
        if not product:
            product = self.env['product.product'].search([
                ('name', 'ilike', 'shredding'),
                ('type', '=', 'service')
            ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Shredding Service',
                'type': 'service',
                'list_price': 0.0,
                'invoice_policy': 'order',
            })
        
        return product
