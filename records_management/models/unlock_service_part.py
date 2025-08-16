# -*- coding: utf-8 -*-
"""
Unlock Service Parts Management Module

This module manages parts and materials used in unlock services within the Records
Management System. It provides comprehensive tracking of inventory usage, cost
calculations, and integration with billing and inventory systems.

Key Features:
- Parts inventory tracking and management
- Cost calculation with markup and pricing
- Stock level monitoring and alerts
- Vendor management and procurement tracking
- Warranty and maintenance tracking
- Usage analytics and reporting

Business Process:
1. Part Selection: Choose parts for service requirements
2. Inventory Check: Validate availability and reserve stock
3. Cost Calculation: Calculate service costs with markup
4. Usage Tracking: Document actual parts used in service
5. Billing Integration: Include parts costs in service billing
6. Inventory Update: Update stock levels after service completion

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class UnlockServicePart(models.Model):
    _name = "unlock.service.part"
    _description = "Unlock Service Part Management"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "service_history_id, sequence, product_id"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Computed display name for the service part"
    )

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence order for parts list"
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    user_id = fields.Many2one(
        "res.users",
        string="Created By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who added this part to the service"
    )

    active = fields.Boolean(
        string="Active",
        default=True,
        tracking=True,
        help="Set to False to archive this part record"
    )

    # ============================================================================
    # SERVICE RELATIONSHIP FIELDS
    # ============================================================================

    service_history_id = fields.Many2one(
        "unlock.service.history",
        string="Service History",
        required=True,
        ondelete="cascade",
        tracking=True,
        index=True,
        help="Related unlock service history record"
    )

    partner_id = fields.Many2one(
        "res.partner",
        related="service_history_id.partner_id",
        string="Customer",
        store=True,
        readonly=True,
        help="Customer for this service"
    )

    technician_id = fields.Many2one(
        "hr.employee",
        related="service_history_id.technician_id",
        string="Technician",
        store=True,
        readonly=True,
        help="Technician performing the service"
    )

    # ============================================================================
    # PRODUCT AND INVENTORY FIELDS
    # ============================================================================

    product_id = fields.Many2one(
        "product.product",
        string="Product/Part",
        required=True,
        tracking=True,
        domain=[('type', 'in', ['product', 'consu'])],
        help="Product or part used in the service"
    )

    name = fields.Char(
        related="product_id.name",
        string="Product Name",
        readonly=True,
        store=True
    )

    product_code = fields.Char(
        related="product_id.default_code",
        string="Product Code",
        readonly=True,
        store=True
    )

    product_category_id = fields.Many2one(
        related="product_id.categ_id",
        string="Product Category",
        readonly=True,
        store=True
    )

    uom_id = fields.Many2one(
        related="product_id.uom_id",
        string="Unit of Measure",
        readonly=True,
        store=True
    )

    # ============================================================================
    # QUANTITY AND USAGE FIELDS
    # ============================================================================

    quantity_planned = fields.Float(
        string="Planned Quantity",
        default=1.0,
        digits="Product Unit of Measure",
        tracking=True,
        help="Planned quantity to be used"
    )

    quantity_used = fields.Float(
        string="Actual Quantity Used",
        digits="Product Unit of Measure",
        tracking=True,
        help="Actual quantity used in the service"
    )

    quantity = fields.Float(
        string="Quantity",
        compute="_compute_quantity",
        store=True,
        digits="Product Unit of Measure",
        help="Final quantity (uses actual if set, otherwise planned)"
    )

    quantity_available = fields.Float(
        related="product_id.qty_available",
        string="Available Stock",
        readonly=True,
        help="Current available stock for this product"
    )

    quantity_reserved = fields.Float(
        string="Reserved Quantity",
        digits="Product Unit of Measure",
        help="Quantity reserved for this service"
    )

    # ============================================================================
    # PRICING AND COST FIELDS
    # ============================================================================

    unit_cost = fields.Float(
        string="Unit Cost",
        related="product_id.standard_price",
        readonly=True,
        help="Standard cost per unit from product",
    )

    unit_price = fields.Float(
        string="Unit Sale Price",
        related="product_id.list_price",
        readonly=True,
        help="Standard sale price per unit",
    )

    markup_percentage = fields.Float(
        string="Markup %",
        default=20.0,
        tracking=True,
        help="Markup percentage for service pricing"
    )

    service_price = fields.Monetary(
        string="Service Price",
        compute="_compute_service_price",
        store=True,
        currency_field="currency_id",
        help="Final service price including markup"
    )

    total_cost = fields.Monetary(
        string="Total Cost",
        compute="_compute_total_amounts",
        store=True,
        currency_field="currency_id",
        help="Total cost (quantity × unit cost)"
    )

    total_price = fields.Monetary(
        string="Total Price",
        compute="_compute_total_amounts",
        store=True,
        currency_field="currency_id",
        help="Total service price (quantity × service price)"
    )

    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        string="Currency",
        readonly=True
    )

    # ============================================================================
    # STATUS AND WORKFLOW FIELDS
    # ============================================================================

    state = fields.Selection([
        ('planned', 'Planned'),
        ('reserved', 'Reserved'),
        ('used', 'Used'),
        ('returned', 'Returned'),
        ('cancelled', 'Cancelled')
    ], string="Status", default='planned', tracking=True, required=True,
       help="Current status of this part in the service")

    is_critical = fields.Boolean(
        string="Critical Part",
        help="Mark as critical if this part is essential for service completion"
    )

    is_warranty_covered = fields.Boolean(
        string="Warranty Covered",
        help="Indicates if this part is covered under warranty"
    )

    warranty_date = fields.Date(
        string="Warranty Expiry",
        help="Date when warranty coverage expires"
    )

    # ============================================================================
    # VENDOR AND PROCUREMENT FIELDS
    # ============================================================================

    vendor_id = fields.Many2one(
        "res.partner",
        string="Preferred Vendor",
        domain=[('is_company', '=', True), ('supplier_rank', '>', 0)],
        help="Preferred vendor for this part"
    )

    procurement_date = fields.Date(
        string="Procurement Date",
        help="Date when part was procured"
    )

    batch_number = fields.Char(
        string="Batch/Serial Number",
        help="Batch or serial number for traceability"
    )

    expiry_date = fields.Date(
        string="Expiry Date",
        help="Expiry date for time-sensitive parts"
    )

    # ============================================================================
    # NOTES AND DOCUMENTATION FIELDS
    # ============================================================================

    usage_notes = fields.Text(
        string="Usage Notes",
        help="Notes about part usage or installation"
    )

    replacement_reason = fields.Text(
        string="Replacement Reason",
        help="Reason why this part needed replacement"
    )

    quality_notes = fields.Text(
        string="Quality Notes",
        help="Quality inspection notes"
    )

    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes for technicians"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================

    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=[('res_model', '=', 'unlock.service.part')]
    )

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=[('res_model', '=', 'unlock.service.part')]
    )

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=[('res_model', '=', 'unlock.service.part')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection([], string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')]
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================

    @api.depends('product_id', 'quantity', 'service_history_id')
    def _compute_display_name(self):
        """Compute display name for the part record"""
        for record in self:
            if record.product_id and record.service_history_id:
                record.display_name = _("%s - %s (Qty: %s)", 
                                      record.service_history_id.name,
                                      record.product_id.name,
                                      record.quantity or record.quantity_planned)
            elif record.product_id:
                record.display_name = record.product_id.name
            else:
                record.display_name = _("New Service Part")

    @api.depends('quantity_used', 'quantity_planned')
    def _compute_quantity(self):
        """Compute final quantity based on actual or planned"""
        for record in self:
            record.quantity = record.quantity_used or record.quantity_planned

    @api.depends('unit_price', 'markup_percentage')
    def _compute_service_price(self):
        """Compute service price with markup"""
        for record in self:
            if record.unit_price and record.markup_percentage:
                record.service_price = record.unit_price * (1 + record.markup_percentage / 100)
            else:
                record.service_price = record.unit_price

    @api.depends('quantity', 'unit_cost', 'service_price')
    def _compute_total_amounts(self):
        """Compute total cost and price amounts"""
        for record in self:
            record.total_cost = record.quantity * record.unit_cost
            record.total_price = record.quantity * record.service_price

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================

    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update related fields when product changes"""
        if self.product_id:
            # Check stock availability
            if self.product_id.qty_available <= 0:
                return {
                    'warning': {
                        'title': _('Stock Warning'),
                        'message': _('Product %s is out of stock. Available: %s') % (
                            self.product_id.name, self.product_id.qty_available
                        )
                    }
                }

    @api.onchange('quantity_planned')
    def _onchange_quantity_planned(self):
        """Validate planned quantity against stock"""
        if self.quantity_planned and self.product_id:
            if self.quantity_planned > self.product_id.qty_available:
                return {
                    'warning': {
                        'title': _('Insufficient Stock'),
                        'message': _('Planned quantity %s exceeds available stock %s for %s') % (
                            self.quantity_planned, self.product_id.qty_available, self.product_id.name
                        )
                    }
                }

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================

    @api.constrains('quantity_planned', 'quantity_used')
    def _check_quantities(self):
        """Validate quantity values"""
        for record in self:
            if record.quantity_planned < 0:
                raise ValidationError(_("Planned quantity cannot be negative"))

            if record.quantity_used < 0:
                raise ValidationError(_("Used quantity cannot be negative"))

            if record.quantity_used and record.quantity_used > record.quantity_planned:
                raise ValidationError(_(
                    "Used quantity (%s) cannot exceed planned quantity (%s) for %s"
                ) % (record.quantity_used, record.quantity_planned, record.product_id.name))

    @api.constrains('markup_percentage')
    def _check_markup_percentage(self):
        """Validate markup percentage"""
        for record in self:
            if record.markup_percentage < 0:
                raise ValidationError(_("Markup percentage cannot be negative"))

            if record.markup_percentage > 1000:
                raise ValidationError(_("Markup percentage cannot exceed 1000%"))

    @api.constrains('expiry_date', 'warranty_date')
    def _check_dates(self):
        """Validate date fields"""
        for record in self:
            if record.expiry_date and record.expiry_date < fields.Date.today():
                raise ValidationError(_("Expiry date cannot be in the past"))

            if record.warranty_date and record.warranty_date < fields.Date.today():
                # Warning only, don't prevent saving
                record.message_post(
                    body=_("Warning: Warranty date is in the past for %s") % record.product_id.name,
                    message_type='comment'
                )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================

    def action_reserve_stock(self):
        """Reserve stock for this service part"""
        self.ensure_one()

        if self.state != 'planned':
            raise UserError(_("Can only reserve stock for planned parts"))

        if self.quantity_planned > self.product_id.qty_available:
            raise UserError(_(
                "Cannot reserve %s units of %s. Only %s available."
            ) % (self.quantity_planned, self.product_id.name, self.product_id.qty_available))

        self.write({
            'state': 'reserved',
            'quantity_reserved': self.quantity_planned
        })

        self._create_audit_log('stock_reserved')

        return True

    def action_mark_used(self):
        """Mark part as used in service"""
        self.ensure_one()

        if self.state not in ['planned', 'reserved']:
            raise UserError(_("Part must be planned or reserved to mark as used"))

        # Open wizard to enter actual quantity used
        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark Part as Used'),
            'res_model': 'unlock.service.part.usage.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_part_id': self.id,
                'default_quantity_used': self.quantity_planned
            }
        }

    def action_return_unused(self):
        """Return unused parts to stock"""
        self.ensure_one()

        if self.state != 'reserved':
            raise UserError(_("Can only return reserved parts"))

        unused_quantity = self.quantity_reserved - (self.quantity_used or 0)

        if unused_quantity > 0:
            self.write({
                'state': 'returned',
                'quantity_reserved': self.quantity_used or 0
            })

            self._create_audit_log('stock_returned', {
                'returned_quantity': unused_quantity
            })

            self.message_post(
                body=_("Returned %s units of %s to stock") % (
                    unused_quantity, self.product_id.name
                )
            )

        return True

    def action_cancel_part(self):
        """Cancel this service part"""
        self.ensure_one()

        if self.state == 'used':
            raise UserError(_("Cannot cancel parts that have been used"))

        self.write({'state': 'cancelled'})
        self._create_audit_log('part_cancelled')

        return True

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================

    def _create_audit_log(self, event_type, additional_data=None):
        """Create audit log entry"""
        audit_data = {
            'event_type': event_type,
            'model_name': self._name,
            'record_id': self.id,
            'user_id': self.env.user.id,
            'company_id': self.company_id.id,
            'description': _('Service part %s: %s') % (self.product_id.name, event_type),
            'additional_data': additional_data or {}
        }

        # Add to related service history audit
        if self.service_history_id:
            audit_data['related_service_id'] = self.service_history_id.id

        return self.env['unlock.service.audit'].create(audit_data)

    def _calculate_total_service_cost(self):
        """Calculate total cost for billing integration"""
        return self.total_price

    def _check_warranty_status(self):
        """Check if part is still under warranty"""
        if self.warranty_date:
            return self.warranty_date >= fields.Date.today()
        return False

    def _get_replacement_recommendations(self):
        """Get recommended replacement parts"""
        # Business logic to suggest alternative parts
        domain = [
            ('categ_id', '=', self.product_category_id.id),
            ('id', '!=', self.product_id.id),
            ('active', '=', True)
        ]
        return self.env['product.product'].search(domain, limit=5)

    # ============================================================================
    # INTEGRATION METHODS
    # ============================================================================

    @api.model
    def create_from_service_template(self, service_history_id, template_parts):
        """Create parts from service template"""
        parts = []
        for template_part in template_parts:
            part_vals = {
                'service_history_id': service_history_id,
                'product_id': template_part['product_id'],
                'quantity_planned': template_part.get('quantity', 1.0),
                'markup_percentage': template_part.get('markup', 20.0),
                'is_critical': template_part.get('is_critical', False)
            }
            parts.append(self.create(part_vals))
        return parts

    def export_to_billing(self):
        """Export part costs to billing system"""
        billing_data = {
            'service_id': self.service_history_id.id,
            'product_id': self.product_id.id,
            'quantity': self.quantity,
            'unit_price': self.service_price,
            'total_amount': self.total_price,
            'description': _('Service part: %s') % self.product_id.name
        }
        return billing_data

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================

    @api.model
    def get_usage_analytics(self, date_from=None, date_to=None):
        """Get parts usage analytics"""
        domain = [('state', '=', 'used')]

        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        used_parts = self.search(domain)

        analytics = {
            'total_parts_used': len(used_parts),
            'total_cost': sum(used_parts.mapped('total_cost')),
            'total_revenue': sum(used_parts.mapped('total_price')),
            'most_used_products': self._get_most_used_products(used_parts),
            'cost_by_category': self._get_cost_by_category(used_parts)
        }

        return analytics

    def _get_most_used_products(self, parts):
        """Get most frequently used products"""
        product_usage = {}
        for part in parts:
            if part.product_id.id in product_usage:
                product_usage[part.product_id.id]['quantity'] += part.quantity
                product_usage[part.product_id.id]['count'] += 1
            else:
                product_usage[part.product_id.id] = {
                    'product': part.product_id.name,
                    'quantity': part.quantity,
                    'count': 1
                }

        return sorted(product_usage.values(), key=lambda x: x['quantity'], reverse=True)[:10]

    def _get_cost_by_category(self, parts):
        """Get cost breakdown by product category"""
        category_costs = {}
        for part in parts:
            category = part.product_category_id.name or 'Uncategorized'
            if category in category_costs:
                category_costs[category] += part.total_cost
            else:
                category_costs[category] = part.total_cost

        return category_costs
