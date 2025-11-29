# -*- coding: utf-8 -*-
"""
Monthly Storage Billing Wizard

Generates monthly storage invoices for customers based on:
1. Initial setup fees for NEW containers (only charged once per container)
2. Monthly storage fees by container type
3. Minimum monthly charge applied when storage fees are below threshold

Business Rules:
- Setup fee charged only ONCE per container (tracked by database ID)
- No proration - full month charged regardless of add date within period
- Minimum charge replaces storage fees until fees exceed minimum
- Invoices generated per customer with itemized breakdown

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from collections import defaultdict
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class MonthlyStorageBillingWizard(models.TransientModel):
    """
    Wizard for generating monthly storage invoices.
    
    Workflow:
    1. Select billing period
    2. Preview billing summary
    3. Generate invoices per customer
    """
    _name = 'monthly.storage.billing.wizard'
    _description = 'Monthly Storage Billing Wizard'

    # ============================================================================
    # BILLING PERIOD
    # ============================================================================
    billing_period_id = fields.Many2one(
        comodel_name='billing.period',
        string='Billing Period',
        required=True,
        help='The billing period for which to generate invoices'
    )
    start_date = fields.Date(
        string='Period Start',
        related='billing_period_id.start_date',
        readonly=True
    )
    end_date = fields.Date(
        string='Period End',
        related='billing_period_id.end_date',
        readonly=True
    )

    # ============================================================================
    # RATE CONFIGURATION
    # ============================================================================
    use_base_rates = fields.Boolean(
        string='Use Base Rates',
        default=True,
        help='Use base rate configuration for customers without negotiated rates'
    )
    base_rate_id = fields.Many2one(
        comodel_name='base.rate',
        string='Base Rate Card',
        domain=[('state', '=', 'active')],
        help='Base rate card to use for default pricing'
    )

    # Rate overrides (default from base_rate or container_type)
    setup_fee = fields.Monetary(
        string='Setup Fee (per container)',
        currency_field='currency_id',
        default=3.50,
        help='One-time fee for each NEW container added'
    )
    minimum_monthly_charge = fields.Monetary(
        string='Minimum Monthly Charge',
        currency_field='currency_id',
        default=45.00,
        help='Minimum charge applied when storage fees are below this amount'
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        default=lambda self: self.env.company.currency_id
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        default=lambda self: self.env.company
    )

    # ============================================================================
    # CUSTOMER FILTERING
    # ============================================================================
    partner_ids = fields.Many2many(
        comodel_name='res.partner',
        string='Customers',
        domain=[('is_company', '=', True)],
        help='Leave empty to bill all customers with active containers'
    )

    include_pending_work_orders = fields.Boolean(
        string='Include Pending Work Orders',
        default=True,
        help='Include completed work orders that are pending consolidated billing'
    )

    # ============================================================================
    # BILLING PREVIEW
    # ============================================================================
    preview_line_ids = fields.One2many(
        comodel_name='monthly.storage.billing.preview',
        inverse_name='wizard_id',
        string='Billing Preview'
    )

    total_setup_fees = fields.Monetary(
        string='Total Setup Fees',
        currency_field='currency_id',
        compute='_compute_totals'
    )
    total_storage_fees = fields.Monetary(
        string='Total Storage Fees',
        currency_field='currency_id',
        compute='_compute_totals'
    )
    total_minimum_adjustments = fields.Monetary(
        string='Total Minimum Adjustments',
        currency_field='currency_id',
        compute='_compute_totals'
    )
    grand_total = fields.Monetary(
        string='Grand Total',
        currency_field='currency_id',
        compute='_compute_totals'
    )
    customer_count = fields.Integer(
        string='Customers to Bill',
        compute='_compute_totals'
    )
    container_count = fields.Integer(
        string='Containers to Bill',
        compute='_compute_totals'
    )

    # ============================================================================
    # STATE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Configure'),
        ('preview', 'Preview'),
        ('done', 'Completed'),
    ], string='Status', default='draft')

    invoices_created = fields.Integer(string='Invoices Created', readonly=True)
    invoice_ids = fields.Many2many(
        comodel_name='account.move',
        string='Created Invoices',
        readonly=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('preview_line_ids', 'preview_line_ids.total_amount')
    def _compute_totals(self):
        for wizard in self:
            wizard.total_setup_fees = sum(wizard.preview_line_ids.mapped('setup_fees_total'))
            wizard.total_storage_fees = sum(wizard.preview_line_ids.mapped('storage_fees_total'))
            wizard.total_minimum_adjustments = sum(wizard.preview_line_ids.mapped('minimum_adjustment'))
            wizard.grand_total = sum(wizard.preview_line_ids.mapped('total_amount'))
            wizard.customer_count = len(wizard.preview_line_ids)
            wizard.container_count = sum(wizard.preview_line_ids.mapped('total_containers'))

    @api.onchange('base_rate_id')
    def _onchange_base_rate(self):
        """Load rates from selected base rate card"""
        if self.base_rate_id:
            self.setup_fee = self.base_rate_id.container_setup_fee or 3.50
            self.minimum_monthly_charge = self.base_rate_id.minimum_monthly_charge or 45.00

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_generate_preview(self):
        """Generate billing preview for all eligible customers"""
        self.ensure_one()

        if not self.billing_period_id:
            raise UserError(_('Please select a billing period.'))

        # Clear existing preview
        self.preview_line_ids.unlink()

        # Get customers to bill
        domain = [('active', '=', True)]
        if self.partner_ids:
            customers = self.partner_ids
        else:
            # Find all customers with active containers
            container_partners = self.env['records.container'].search([
                ('active', '=', True),
                ('state', 'not in', ['destroyed', 'perm_out']),
            ]).mapped('partner_id')
            customers = container_partners

        # Generate preview for each customer
        preview_vals = []
        for partner in customers:
            preview_data = self._compute_customer_billing(partner)
            if preview_data['total_containers'] > 0:
                preview_vals.append({
                    'wizard_id': self.id,
                    'partner_id': partner.id,
                    **preview_data
                })

        if preview_vals:
            self.env['monthly.storage.billing.preview'].create(preview_vals)

        self.state = 'preview'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.storage.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _compute_customer_billing(self, partner):
        """Compute billing amounts for a single customer"""
        Container = self.env['records.container']

        # Get active containers for this customer (not destroyed/perm_out)
        containers = Container.search([
            ('partner_id', '=', partner.id),
            ('active', '=', True),
            ('state', 'not in', ['destroyed', 'perm_out']),
        ])

        # NEW containers: created during this billing period and setup fee not yet charged
        new_containers = containers.filtered(
            lambda c: c.create_date.date() >= self.start_date
            and c.create_date.date() <= self.end_date
            and not c.setup_fee_charged
        )

        # Count containers by type for storage fees
        type_counts = defaultdict(int)
        type_rates = {}
        for container in containers:
            ctype = container.container_type_id
            type_counts[ctype.id] += 1
            if ctype.id not in type_rates:
                # Get rate: negotiated rate > container type rate
                rate = container.monthly_rate_effective or ctype.standard_rate or 0.0
                type_rates[ctype.id] = {
                    'name': ctype.name,
                    'rate': rate,
                }

        # Calculate fees
        setup_fees_total = len(new_containers) * self.setup_fee

        storage_fees_total = 0.0
        storage_breakdown = []
        for ctype_id, count in type_counts.items():
            rate_info = type_rates.get(ctype_id, {'name': 'Unknown', 'rate': 0})
            subtotal = count * rate_info['rate']
            storage_fees_total += subtotal
            storage_breakdown.append({
                'type_name': rate_info['name'],
                'count': count,
                'rate': rate_info['rate'],
                'subtotal': subtotal,
            })

        # Apply minimum charge
        minimum_adjustment = 0.0
        if storage_fees_total < self.minimum_monthly_charge:
            minimum_adjustment = self.minimum_monthly_charge - storage_fees_total

        # Calculate pending work order charges (for consolidated billing)
        pending_work_orders = 0
        work_order_total = 0.0

        if self.include_pending_work_orders and partner.consolidated_billing:
            # Find pending shredding work orders
            shredding_orders = self.env['work.order.shredding'].search([
                ('partner_id', '=', partner.id),
                ('pending_consolidated_billing', '=', True),
                ('invoice_id', '=', False),
            ])
            for wo in shredding_orders:
                pending_work_orders += 1
                work_order_total += wo.subtotal or 0.0

            # Find pending retrieval work orders
            retrieval_orders = self.env['work.order.retrieval'].search([
                ('partner_id', '=', partner.id),
                ('pending_consolidated_billing', '=', True),
                ('invoice_id', '=', False),
            ])
            for wo in retrieval_orders:
                pending_work_orders += 1
                work_order_total += wo.subtotal or 0.0

        total_amount = setup_fees_total + storage_fees_total + minimum_adjustment + work_order_total

        return {
            'new_containers': len(new_containers),
            'total_containers': len(containers),
            'setup_fees_total': setup_fees_total,
            'storage_fees_total': storage_fees_total,
            'minimum_adjustment': minimum_adjustment,
            'pending_work_orders': pending_work_orders,
            'work_order_total': work_order_total,
            'total_amount': total_amount,
            'storage_breakdown': str(storage_breakdown),
        }

    def action_generate_invoices(self):
        """Generate actual invoices for all preview lines"""
        self.ensure_one()

        if self.state != 'preview':
            raise UserError(_('Please generate preview first.'))

        if not self.preview_line_ids:
            raise UserError(_('No customers to bill.'))

        invoices = self.env['account.move']

        for preview in self.preview_line_ids:
            if preview.total_amount <= 0:
                continue

            invoice = self._create_customer_invoice(preview)
            invoices |= invoice

        # Update billing period
        self.billing_period_id.state = 'invoiced'

        self.invoices_created = len(invoices)
        self.invoice_ids = [(6, 0, invoices.ids)]
        self.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.storage.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def _create_customer_invoice(self, preview):
        """Create invoice for a single customer based on preview"""
        Container = self.env['records.container']

        # Prepare invoice
        invoice_vals = {
            'move_type': 'out_invoice',
            'partner_id': preview.partner_id.id,
            'invoice_date': self.billing_period_id.invoice_date or fields.Date.today(),
            'billing_period_id': self.billing_period_id.id,
            'is_storage_invoice': True,
            'narration': _('Monthly Storage Invoice for %s') % self.billing_period_id.name,
            'invoice_line_ids': [],
        }

        # Get containers for this customer
        containers = Container.search([
            ('partner_id', '=', preview.partner_id.id),
            ('active', '=', True),
            ('state', 'not in', ['destroyed', 'perm_out']),
        ])

        # NEW containers needing setup fee
        new_containers = containers.filtered(
            lambda c: c.create_date.date() >= self.start_date
            and c.create_date.date() <= self.end_date
            and not c.setup_fee_charged
        )

        # Get or create products
        setup_product = self._get_setup_fee_product()
        storage_product = self._get_storage_fee_product()
        minimum_product = self._get_minimum_charge_product()

        line_vals = []

        # 1. Setup Fees for new containers
        if new_containers:
            line_vals.append((0, 0, {
                'product_id': setup_product.id,
                'name': _('Initial Container Setup Fee - %d new containers') % len(new_containers),
                'quantity': len(new_containers),
                'price_unit': self.setup_fee,
            }))

        # 2. Monthly Storage Fees by container type
        type_counts = defaultdict(list)
        for container in containers:
            type_counts[container.container_type_id].append(container)

        storage_total = 0.0
        for ctype, ctype_containers in type_counts.items():
            count = len(ctype_containers)
            # Use effective rate from first container (assumes same rate per type)
            rate = ctype_containers[0].monthly_rate_effective or ctype.standard_rate or 0.0
            subtotal = count * rate
            storage_total += subtotal

            line_vals.append((0, 0, {
                'product_id': storage_product.id,
                'name': _('%s - %d containers @ $%.2f/month') % (ctype.name, count, rate),
                'quantity': count,
                'price_unit': rate,
            }))

        # 3. Minimum charge adjustment if applicable
        if storage_total < self.minimum_monthly_charge:
            adjustment = self.minimum_monthly_charge - storage_total
            line_vals.append((0, 0, {
                'product_id': minimum_product.id,
                'name': _('Minimum Monthly Charge Adjustment'),
                'quantity': 1,
                'price_unit': adjustment,
            }))

        # 4. Pending Work Orders (for consolidated billing customers)
        pending_work_orders = []
        if self.include_pending_work_orders and preview.partner_id.consolidated_billing:
            # Shredding work orders
            shredding_orders = self.env['work.order.shredding'].search([
                ('partner_id', '=', preview.partner_id.id),
                ('pending_consolidated_billing', '=', True),
                ('invoice_id', '=', False),
            ])
            pending_work_orders.extend(shredding_orders)

            for wo in shredding_orders:
                wo_product = wo.service_product_id or self._get_work_order_product('shredding')
                line_vals.append((0, 0, {
                    'product_id': wo_product.id,
                    'name': _('Shredding Service - %s') % wo.name,
                    'quantity': wo.quantity or 1,
                    'price_unit': wo.unit_price or wo_product.list_price,
                }))

            # Retrieval work orders
            retrieval_orders = self.env['work.order.retrieval'].search([
                ('partner_id', '=', preview.partner_id.id),
                ('pending_consolidated_billing', '=', True),
                ('invoice_id', '=', False),
            ])
            pending_work_orders.extend(retrieval_orders)

            for wo in retrieval_orders:
                wo_product = wo.service_product_id or self._get_work_order_product('retrieval')
                line_vals.append((0, 0, {
                    'product_id': wo_product.id,
                    'name': _('Retrieval Service - %s') % wo.name,
                    'quantity': wo.quantity or 1,
                    'price_unit': wo.unit_price or wo_product.list_price,
                }))

        invoice_vals['invoice_line_ids'] = line_vals

        # Create invoice
        invoice = self.env['account.move'].create(invoice_vals)

        # Link work orders to this invoice and clear pending flag
        for wo in pending_work_orders:
            wo.write({
                'invoice_id': invoice.id,
                'pending_consolidated_billing': False,
                'billing_period_id': self.billing_period_id.id,
            })

        # Mark setup fees as charged on new containers
        today = fields.Date.today()
        for container in new_containers:
            container.write({
                'setup_fee_charged': True,
                'setup_fee_invoice_id': invoice.id,
                'setup_fee_date': today,
            })

        # Update last billing period on all containers
        containers.write({
            'last_storage_billing_date': today,
            'last_storage_billing_period_id': self.billing_period_id.id,
        })

        return invoice

    def _get_setup_fee_product(self):
        """Get or create product for container setup fees"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-SETUP-FEE'),
        ], limit=1)

        if not product:
            product = self.env['product.product'].create({
                'name': 'Container Setup Fee',
                'default_code': 'RM-SETUP-FEE',
                'type': 'service',
                'list_price': self.setup_fee,
                'invoice_policy': 'order',
                'description': 'One-time initial setup fee for new containers',
            })

        return product

    def _get_storage_fee_product(self):
        """Get or create product for monthly storage fees"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-STORAGE-FEE'),
        ], limit=1)

        if not product:
            product = self.env['product.product'].create({
                'name': 'Monthly Storage Fee',
                'default_code': 'RM-STORAGE-FEE',
                'type': 'service',
                'list_price': 0.32,
                'invoice_policy': 'order',
                'description': 'Monthly storage fee per container',
            })

        return product

    def _get_minimum_charge_product(self):
        """Get or create product for minimum charge adjustment"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-MINIMUM-ADJ'),
        ], limit=1)

        if not product:
            product = self.env['product.product'].create({
                'name': 'Minimum Monthly Charge Adjustment',
                'default_code': 'RM-MINIMUM-ADJ',
                'type': 'service',
                'list_price': 0.00,
                'invoice_policy': 'order',
                'description': 'Adjustment to meet minimum monthly storage charge',
            })

        return product

    def _get_work_order_product(self, wo_type):
        """Get or create product for work order services"""
        if wo_type == 'shredding':
            code = 'RM-SHREDDING-SVC'
            name = 'Shredding Service'
            price = 25.00
        elif wo_type == 'retrieval':
            code = 'RM-RETRIEVAL-SVC'
            name = 'Retrieval Service'
            price = 15.00
        else:
            code = 'RM-SERVICE'
            name = 'Records Management Service'
            price = 0.00

        product = self.env['product.product'].search([
            ('default_code', '=', code),
        ], limit=1)

        if not product:
            product = self.env['product.product'].create({
                'name': name,
                'default_code': code,
                'type': 'service',
                'list_price': price,
                'invoice_policy': 'order',
            })

        return product

    def action_view_invoices(self):
        """View created invoices"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Storage Invoices'),
            'res_model': 'account.move',
            'view_mode': 'list,form',
            'domain': [('id', 'in', self.invoice_ids.ids)],
        }

    def action_back_to_config(self):
        """Go back to configuration step"""
        self.state = 'draft'
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'monthly.storage.billing.wizard',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }


class MonthlyStorageBillingPreview(models.TransientModel):
    """Preview line for monthly storage billing"""
    _name = 'monthly.storage.billing.preview'
    _description = 'Monthly Storage Billing Preview Line'

    wizard_id = fields.Many2one(
        comodel_name='monthly.storage.billing.wizard',
        string='Wizard',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        required=True
    )
    currency_id = fields.Many2one(
        related='wizard_id.currency_id'
    )

    # Container counts
    new_containers = fields.Integer(string='New Containers')
    total_containers = fields.Integer(string='Total Containers')

    # Fee breakdown
    setup_fees_total = fields.Monetary(
        string='Setup Fees',
        currency_field='currency_id'
    )
    storage_fees_total = fields.Monetary(
        string='Storage Fees',
        currency_field='currency_id'
    )
    minimum_adjustment = fields.Monetary(
        string='Min. Adjustment',
        currency_field='currency_id'
    )

    # Work order charges (for consolidated billing customers)
    pending_work_orders = fields.Integer(string='Pending Work Orders')
    work_order_total = fields.Monetary(
        string='Work Order Charges',
        currency_field='currency_id'
    )

    total_amount = fields.Monetary(
        string='Total',
        currency_field='currency_id'
    )

    # Detailed breakdown (JSON string for display)
    storage_breakdown = fields.Text(string='Storage Breakdown')
