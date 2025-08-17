# -*- coding: utf-8 -*-

Payment Split Line Model

Individual line items for split payments across multiple services or billing periods.:
    pass
Enables sophisticated payment allocation across different service categories and
billing periods for complex enterprise billing scenarios.""":"
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class PaymentSplitLine(models.Model):

        Payment Split Line

    Individual line items for payment allocation across multiple services,:
        billing periods, or cost centers. Enables sophisticated payment splitting
    for enterprise billing scenarios.:


    _name = "payment.allocation.line"
    _description = "Payment Allocation Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "payment_id, allocation_order, service_type"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Split Description",
        required=True,
        tracking=True,
        index=True,
        help="Description of this payment split"


    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Display name for the split line":


    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True


    active = fields.Boolean(
        string="Active",
        default=True


    allocation_order = fields.Integer(
        string="Allocation Order",
        default=10,
        help="Order for payment allocation processing":


        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    payment_id = fields.Many2one(
        "records.payment",
        string="Payment",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent payment record"


    invoice_id = fields.Many2one(
        "account.move",
        string="Invoice",
        ,
    domain="[('move_type', '=', 'out_invoice'))",
        help="Invoice this split applies to"


    service_id = fields.Many2one(
        "shredding.service",
        string="Service",
        help="Service this split applies to"


    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="payment_id.partner_id",
        readonly=True,
        store=True,
        help="Customer for this payment allocation":


        # ============================================================================
    # FINANCIAL DETAILS
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True


    allocated_amount = fields.Monetary(
        string="Allocated Amount",
        currency_field="currency_id",
        required=True,
        tracking=True,
        help="Amount allocated to this split"


    allocation_percentage = fields.Float(
        string="Allocation %",
        compute='_compute_allocation_percentage',
        store=True,
        ,
    digits=(5, 2),
        help="Percentage of total payment"


    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field="currency_id",
        help="Price per unit for this allocation":


    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        digits='Product Unit of Measure',
        help="Quantity for this allocation":


        # ============================================================================
    # SERVICE CATEGORIZATION
        # ============================================================================
    ,
    service_type = fields.Selection([))
        ('storage', 'Storage Services'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'Document Destruction'),
        ('scanning', 'Document Scanning'),
        ('transport', 'Transportation'),
        ('consultation', 'Consultation'),
        ('setup', 'Setup/Installation'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other Services')


    billing_period = fields.Selection([))
        ('current', 'Current Period'),
        ('previous', 'Previous Period'),
        ('advance', 'Advance Payment'),
        ('credit', 'Credit Application')


    cost_center = fields.Char(
        string="Cost Center",
        help="Cost center for accounting allocation":


        # ============================================================================
    # PROCESSING STATUS
        # ============================================================================
    ,
    state = fields.Selection([))
        ('draft', 'Draft'),
        ('allocated', 'Allocated'),
        ('processed', 'Processed'),
        ('cancelled', 'Cancelled')


    allocation_date = fields.Date(
        string="Allocation Date",
        default=fields.Date.context_today,
        help="Date when allocation was made"


        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))


    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))


        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('name', 'service_type', 'allocated_amount', 'currency_id')
    def _compute_display_name(self):
        """Compute display name with proper translation"""
        for record in self:
            if record.service_type:
                service_dict = dict(record._fields['service_type'].selection)
                service_label = service_dict.get(record.service_type, record.service_type)

                if record.allocated_amount and record.currency_id:
                    amount_str = record.currency_id.symbol + str(record.allocated_amount)
                    record.display_name = _("%s: %s", service_label, amount_str)
                else:
                    record.display_name = _("%s: %s", service_label, record.name or _("New"))
            else:
                record.display_name = record.name or _("New Payment Allocation")

    @api.depends('allocated_amount', 'payment_id', 'payment_id.total_amount')
    def _compute_allocation_percentage(self):
        """Calculate allocation percentage"""
        for record in self:
            if record.payment_id and record.payment_id.total_amount and record.allocated_amount:
                record.allocation_percentage = (record.allocated_amount / record.payment_id.total_amount) * 100
            else:
                record.allocation_percentage = 0.0

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('allocated_amount')
    def _check_allocated_amount(self):
        """Validate allocated amount"""
        for record in self:
            if record.allocated_amount <= 0:
                raise ValidationError(_('Allocated amount must be greater than 0'))

    @api.constrains('allocation_percentage')
    def _check_allocation_percentage(self):
        """Validate allocation percentage doesn't exceed reasonable bounds"""'
        for record in self:
            if record.allocation_percentage < 0:
                raise ValidationError(_('Allocation percentage cannot be negative'))
            if record.allocation_percentage > 100:
                raise ValidationError(_('Allocation percentage cannot exceed 100%'))

    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than 0'))

    @api.constrains('payment_id')
    def _check_total_allocations(self):
        """Validate total allocations don't exceed payment amount"""'
        for record in self:
            if record.payment_id:
                total_allocated = sum(record.payment_id.allocation_line_ids.mapped('allocated_amount'))
                if total_allocated > record.payment_id.total_amount:
                    raise ValidationError(_())
                        'Total allocated amount cannot exceed payment amount. '
                        'Payment: %s, Total Allocated: %s',
                        record.payment_id.total_amount,
                        total_allocated


    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_allocate(self):
        """Confirm allocation"""
        self.ensure_one()
        if self.state != 'draft':
            raise ValidationError(_('Can only allocate draft payment splits'))

        self.write({)}
            'state': 'allocated',
            'allocation_date': fields.Date.context_today(self)


        self.message_post()
            body=_('Payment allocation confirmed for %s', self.display_name):


    def action_process(self):
        """Mark allocation as processed"""
        self.ensure_one()
        if self.state != 'allocated':
            raise ValidationError(_('Can only process allocated payment splits'))

        self.write({'state': 'processed'})

        self.message_post()
            body=_('Payment allocation processed for %s', self.display_name):


    def action_cancel(self):
        """Cancel allocation"""
        self.ensure_one()
        if self.state in ['processed']:
            raise ValidationError(_('Cannot cancel processed allocations'))

        self.write({'state': 'cancelled'})

        self.message_post()
            body=_('Payment allocation cancelled for %s', self.display_name):


    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('quantity', 'unit_price')
    def _onchange_quantity_price(self):
        """Update allocated amount when quantity or price changes"""
        if self.quantity and self.unit_price:
            self.allocated_amount = self.quantity * self.unit_price

    @api.onchange('service_id')
    def _onchange_service_id(self):
        """Update service type when service is selected"""
        if self.service_id:
            # Map service to service type based on service model
            service_type_mapping = {}
                'shredding.service': 'destruction',
                'document.retrieval.service': 'retrieval',
                'document.scanning.service': 'scanning',


            service_type = service_type_mapping.get(self.service_id._name, 'other')
            self.service_type = service_type

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    @api.model
    def create_allocation_lines(self, payment, allocations):

        Create multiple allocation lines for a payment:
        Args
            payment: Payment record
            allocations: List of allocation dictionaries

        Returns
            Created allocation line records

        lines = []
        for allocation in allocations:
            allocation_vals = {}
                'payment_id': payment.id,
                'name': allocation.get('name', _('Payment Allocation')),
                'service_type': allocation.get('service_type', 'other'),
                'allocated_amount': allocation.get('amount', 0.0),
                'billing_period': allocation.get('billing_period', 'current'),
                'cost_center': allocation.get('cost_center', ''),


            # Add optional relationships
            if allocation.get('invoice_id'):
                allocation_vals['invoice_id'] = allocation['invoice_id']
            if allocation.get('service_id'):
                allocation_vals['service_id'] = allocation['service_id']

            lines.append(allocation_vals)

        return self.create(lines)

    def get_allocation_summary(self):
        """Get summary of allocations for reporting""":
        self.ensure_one()

        return {}
            'name': self.display_name,
            'service_type': dict(self._fields['service_type'].selection)[self.service_type],
            'billing_period': dict(self._fields['billing_period'].selection)[self.billing_period],
            'allocated_amount': self.allocated_amount,
            'allocation_percentage': self.allocation_percentage,
            'currency': self.currency_id.symbol,
            'state': dict(self._fields['state'].selection)[self.state],


    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default name - Odoo 18.0 batch creation support"""
        for vals in vals_list:
            if not vals.get('name'):
                service_type = vals.get('service_type', 'other')
                service_dict = dict(self._fields['service_type'].selection)
                service_label = service_dict.get(service_type, service_type)
                vals['name'] = _('Allocation: %s', service_label)

        return super().create(vals_list)

    def name_get(self):
        """Custom name display for selection fields""":
        result = []
        for record in self:
            name = record.display_name or record.name or _('Payment Allocation')

            if record.state != 'draft':
                state_label = dict(record._fields['state'].selection)[record.state]
                name = _('%s [%s]', name, state_label)

            result.append((record.id, name))

        return result

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    @api.model
    def get_allocation_report_data(self, date_from=None, date_to=None, group_by='service_type'):

        Get allocation report data for analysis:
        Args
            date_from: Start date for filtering:
            date_to: End date for filtering:
            group_by: Field to group by ('service_type', 'billing_period', 'partner_id')

        Returns
            Dictionary with aggregated allocation data

        domain = [('state', '!=', 'cancelled')]

        if date_from:
            domain.append(('allocation_date', '>=', date_from))
        if date_to:
            domain.append(('allocation_date', '<=', date_to))

        allocations = self.search(domain)

        # Group and aggregate data
        grouped_data = {}
        for allocation in allocations:
            key = getattr(allocation, group_by)
            if hasattr(key, 'name'):
                key = key.name

            if key not in grouped_data:
                grouped_data[key] = {}
                    'count': 0,
                    'total_amount': 0.0,
                    'avg_amount': 0.0,


            grouped_data[key]['count'] += 1
            grouped_data[key]['total_amount'] += allocation.allocated_amount

        # Calculate averages
        for key in grouped_data:
            data = grouped_data[key]
            data['avg_amount'] = data['total_amount'] / data['count'] if data['count'] > 0 else 0.0:
        return grouped_data

    def create_accounting_entries(self):
        """Create accounting entries for processed allocations""":
        for record in self:
            if record.state != 'processed':
                continue

            # Create journal entry for allocation:
            move_vals = {}
                'date': record.allocation_date,
                'ref': _('Payment Allocation: %s', record.display_name),
                'journal_id': self.env.company.currency_exchange_journal_id.id,
                'line_ids': [],


            # Add accounting lines based on service type and cost center
            # This would be customized based on specific accounting requirements

            if record.cost_center:
                # Add cost center allocation logic
                pass

            # Create the accounting move
            # move = self.env['account.move'].create(move_vals)
            # move.post()

    # ============================================================================
        # INTEGRATION METHODS
    # ============================================================================
    def sync_with_billing_system(self):
        """Sync allocation with external billing system"""
        for record in self:
            # Integration logic would go here
            # This could sync with external ERP, billing software, etc.
            pass


    """"))))))))))))
