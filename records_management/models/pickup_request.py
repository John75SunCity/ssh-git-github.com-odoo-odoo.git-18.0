# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api


class PickupRequest(models.Model):
    """Model for pickup requests with workflow enhancements."""
    _name = 'pickup.request'
    _description = 'Pickup Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Name',
        required=True,
        default='New',
        tracking=True
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    request_date = fields.Date(
        string='Request Date',
        default=fields.Date.context_today,
        required=True,
        tracking=True
    )
    request_item_ids = fields.One2many(
        'pickup.request.item',
        'pickup_id',
        string='Request Items'
    )
    notes = fields.Text(string='Notes')
    
    # Phase 2: Audit & Compliance Fields (12 fields)
    audit_required = fields.Boolean(
        string='Audit Required',
        default=False,
        tracking=True
    )
    compliance_status = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('under_review', 'Under Review')
    ], string='Compliance Status', default='pending', tracking=True)
    risk_level = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string='Risk Level', default='low')
    regulatory_requirement = fields.Text(string='Regulatory Requirement')
    approval_required = fields.Boolean(
        string='Approval Required',
        default=False,
        tracking=True
    )
    approved_by = fields.Many2one('res.users', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal')
    chain_of_custody = fields.Text(string='Chain of Custody')
    pickup_authorization = fields.Char(string='Pickup Authorization')
    transport_requirements = fields.Text(string='Transport Requirements')
    compliance_notes = fields.Text(string='Compliance Notes')
    
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        required=True,
        tracking=True
    )
    quantity = fields.Float(
        string='Quantity',
        required=True,
        tracking=True,
        digits=(16, 2)
    )
    lot_id = fields.Many2one(
        'stock.lot',
        string='Lot',
        domain="[('product_id', '=', product_id)]"
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], default='draft', string='Status', tracking=True)
    scheduled_date = fields.Date(string='Scheduled Date', tracking=True)
    warehouse_id = fields.Many2one(
        'stock.warehouse',
        string='Warehouse',
        tracking=True
    )
    driver_id = fields.Many2one(
        'res.partner',
        string='Driver',
        domain="[('is_company', '=', False)]",
        tracking=True
    )
    vehicle_id = fields.Many2one(
        'fleet.vehicle',
        string='Vehicle',
        tracking=True
    )
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High')
    ], default='0', string='Priority', tracking=True)
    signature = fields.Binary(string='Signature')
    signed_by = fields.Many2one('res.users', string='Signed By')
    signature_date = fields.Datetime(string='Signature Date')
    completion_date = fields.Date(string='Completion Date', tracking=True)

    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'PickupRequest':
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                sequence = self.env['ir.sequence'].next_by_code(
                    'pickup.request'
                )
                vals['name'] = sequence or 'New'
        return super().create(vals_list)

    def action_confirm(self) -> bool:
        return self.write({'state': 'confirmed'})

    def action_schedule(self) -> bool:
        if not self.scheduled_date:
            self.scheduled_date = fields.Date.context_today(self)
        return self.write({'state': 'scheduled'})

    def action_complete(self) -> bool:
        self.completion_date = fields.Date.context_today(self)
        return self.write({'state': 'completed'})

    def action_cancel(self) -> bool:
        return self.write({'state': 'cancelled'})

    def action_view_items(self):
        """View pickup request items"""
        self.ensure_one()
        return {
            'name': _('Pickup Items'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.request.item',
            'view_mode': 'tree,form',
            'domain': [('pickup_request_id', '=', self.id)],
            'context': {'default_pickup_request_id': self.id},
        }

    def action_reschedule(self):
        """Reschedule pickup request"""
        self.ensure_one()
        return {
            'name': _('Reschedule Pickup'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    def action_assign_driver(self):
        """Assign driver to pickup request"""
        self.ensure_one()
        return {
            'name': _('Assign Driver'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.driver.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    def action_print_route(self):
        """Print pickup route"""
        self.ensure_one()
        return {
            'name': _('Print Route'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.pickup_route_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.pickup_route_report',
            'context': {'active_ids': [self.id]},
        }

    def action_send_notification(self):
        """Send pickup notification"""
        self.ensure_one()
        return {
            'name': _('Send Notification'),
            'type': 'ir.actions.act_window',
            'res_model': 'pickup.notification.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_pickup_id': self.id},
        }

    @api.onchange('customer_id')
    def _onchange_customer_id(self) -> None:
        """
        Update domain for driver and vehicle based on customer
        for better UI.
        """
        return {
            'domain': {
                'driver_id': [('parent_id', '=', self.customer_id.id)]
            }
        }
