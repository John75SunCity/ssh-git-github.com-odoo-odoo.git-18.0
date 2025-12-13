# -*- coding: utf-8 -*-
"""
Records Management Sale Order Extension

This module extends Odoo's native sale.order to integrate with the existing
Records Management work order models. Instead of replacing the existing work
order models, this provides:

1. A flag to identify RM-related sales orders
2. Links back to existing work order models (shredding, retrieval, etc.)
3. Helper methods for creating sale orders from work orders

The existing work order models (work.order.shredding, work.order.retrieval, etc.)
remain the source of truth for operational data. This extension allows those
models to leverage native Odoo invoicing when desired.

Integration Pattern:
- work.order.shredding → sale_order_id → sale.order
- work.order.retrieval → sale_order_id → sale.order  
- etc.
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RMSaleOrder(models.Model):
    """
    Extends sale.order for Records Management integration.
    
    This is a LIGHTWEIGHT extension that links native sale.order to
    existing RM work order models. The existing work order models
    retain all business logic - this just enables native invoicing.
    """
    _inherit = 'sale.order'

    # ============================================================================
    # RM IDENTIFICATION
    # ============================================================================
    is_rm_work_order = fields.Boolean(
        string="Is RM Work Order",
        default=False,
        tracking=True,
        help="Indicates this sales order is linked to Records Management work orders"
    )
    
    work_order_type = fields.Selection([
        ('pickup', 'Pickup Service'),
        ('delivery', 'Delivery Service'),
        ('retrieval', 'Container Retrieval'),
        ('destruction', 'Destruction Service'),
        ('shredding', 'Shredding Bin Service'),
        ('scanning', 'Document Scanning'),
        ('access', 'On-Site File Access'),
        ('audit', 'Compliance Audit'),
        ('other', 'Other Service'),
    ], string="Work Order Type",
       tracking=True,
       help="Type of records management service (for reference only)"
    )

    # ============================================================================
    # LINKS TO EXISTING WORK ORDER MODELS
    # These are One2many because one sale order may cover multiple work orders
    # ============================================================================
    shredding_work_order_ids = fields.One2many(
        comodel_name='work.order.shredding',
        inverse_name='sale_order_id',
        string="Shredding Work Orders",
        help="Linked shredding work orders"
    )
    
    retrieval_work_order_ids = fields.One2many(
        comodel_name='work.order.retrieval',
        inverse_name='sale_order_id',
        string="Retrieval Work Orders",
        help="Linked retrieval work orders"
    )
    
    # REMOVED: Duplicate of shredding_work_order_ids - use that field instead
    # destruction_work_order_ids was causing "same label" warning
    
    access_work_order_ids = fields.One2many(
        comodel_name='container.access.work.order',
        inverse_name='sale_order_id',
        string="Access Work Orders",
        help="Linked on-site access work orders"
    )

    # ============================================================================
    # COMPUTED COUNTS
    # ============================================================================
    shredding_wo_count = fields.Integer(
        compute='_compute_work_order_counts',
        string="Shredding WOs"
    )
    retrieval_wo_count = fields.Integer(
        compute='_compute_work_order_counts',
        string="Retrieval WOs"
    )
    # REMOVED: destruction_wo_count - redundant with shredding_wo_count
    access_wo_count = fields.Integer(
        compute='_compute_work_order_counts',
        string="Access WOs"
    )
    total_work_order_count = fields.Integer(
        compute='_compute_work_order_counts',
        string="Total Work Orders"
    )

    @api.depends('shredding_work_order_ids', 'retrieval_work_order_ids', 'access_work_order_ids')
    def _compute_work_order_counts(self):
        for order in self:
            order.shredding_wo_count = len(order.shredding_work_order_ids)
            order.retrieval_wo_count = len(order.retrieval_work_order_ids)
            order.access_wo_count = len(order.access_work_order_ids)
            order.total_work_order_count = (
                order.shredding_wo_count + 
                order.retrieval_wo_count + 
                order.access_wo_count
            )

    # ============================================================================
    # SMART BUTTONS
    # ============================================================================
    def action_view_shredding_work_orders(self):
        """View linked shredding work orders"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Shredding Work Orders'),
            'res_model': 'work.order.shredding',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.shredding_work_order_ids.ids)],
            'context': {'default_sale_order_id': self.id},
        }

    def action_view_retrieval_work_orders(self):
        """View linked retrieval work orders"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Retrieval Work Orders'),
            'res_model': 'work.order.retrieval',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.retrieval_work_order_ids.ids)],
            'context': {'default_sale_order_id': self.id},
        }

    # REMOVED: action_view_destruction_work_orders - redundant with action_view_shredding_work_orders

    def action_view_access_work_orders(self):
        """View linked access work orders"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Access Work Orders'),
            'res_model': 'container.access.work.order',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.access_work_order_ids.ids)],
            'context': {'default_sale_order_id': self.id},
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    @api.model
    def create_from_work_order(self, work_order, products=None):
        """
        Create a sale order from an existing work order.
        
        This method allows existing work order models to generate
        a native Odoo sale order for invoicing purposes.
        
        Args:
            work_order: The source work order record
            products: Optional list of (product_id, qty, price) tuples
            
        Returns:
            The created sale.order record
        """
        if not work_order.partner_id:
            raise UserError(_("Work order must have a customer before creating a sale order."))
        
        # Determine work order type from model name
        model_to_type = {
            'work.order.shredding': 'shredding',
            'work.order.retrieval': 'retrieval',
            'container.access.work.order': 'access',
        }
        wo_type = model_to_type.get(work_order._name, 'other')
        
        # Create the sale order
        sale_order = self.create({
            'partner_id': work_order.partner_id.id,
            'is_rm_work_order': True,
            'work_order_type': wo_type,
            'origin': work_order.name if hasattr(work_order, 'name') else '',
        })
        
        # Link the work order back to sale order
        work_order.write({'sale_order_id': sale_order.id})
        
        # Add product lines if provided
        if products:
            for product_id, qty, price in products:
                self.env['sale.order.line'].create({
                    'order_id': sale_order.id,
                    'product_id': product_id,
                    'product_uom_qty': qty,
                    'price_unit': price,
                })
        
        return sale_order

    def action_sync_from_work_orders(self):
        """
        Sync sale order lines from linked work orders.
        
        This reads the service details from linked work orders and
        creates/updates sale order lines accordingly.
        """
        self.ensure_one()
        # This can be extended to pull billing data from linked work orders
        # For now, it's a placeholder for future enhancement
        return True
