# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Billing(models.Model):
    _name = 'records.billing'
    _description = 'General Billing Model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'invoice_date desc'

    name = fields.Char('Reference', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', 'Customer', required=True, tracking=True)
    department_id = fields.Many2one('records.department', 'Department', tracking=True)
    invoice_date = fields.Date('Invoice Date', default=fields.Date.today, tracking=True)
    amount_total = fields.Float('Total Amount', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('invoiced', 'Invoiced'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Invoice integration
    invoice_id = fields.Many2one('account.move', 'Invoice', readonly=True)
    
    def action_generate_invoice(self):
        """Generate invoice for this billing"""
        self.ensure_one()
        if self.invoice_id:
            return self._show_existing_invoice()
        
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': self.invoice_date,
            'ref': self.name,
            'invoice_line_ids': [(0, 0, {
                'name': f'Records Management Services - {self.name}',
                'quantity': 1,
                'price_unit': self.amount_total,
            })]
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced'
        })
        
        self.message_post(body=_('Invoice generated: %s') % invoice.name)
        return self._show_existing_invoice()

    def action_view_analytics(self):
        """View analytics for billing"""
        self.ensure_one()
        return {
            'name': _('Billing Analytics'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.analytics.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_view_billing_history(self):
        """View billing history for customer"""
        self.ensure_one()
        return {
            'name': _('Billing History: %s') % self.partner_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'default_partner_id': self.partner_id.id},
        }

    def action_configure_rates(self):
        """Configure billing rates"""
        self.ensure_one()
        return {
            'name': _('Configure Billing Rates'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing.config',
            'view_mode': 'tree,form',
            'target': 'current',
        }

    def action_test_billing(self):
        """Test billing calculation"""
        self.ensure_one()
        return {
            'name': _('Test Billing Calculation'),
            'type': 'ir.actions.act_window',
            'res_model': 'billing.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_billing_id': self.id},
        }

    def action_duplicate(self):
        """Duplicate this billing record"""
        self.ensure_one()
        copy = self.copy({'name': f'{self.name} (Copy)', 'state': 'draft', 'invoice_id': False})
        return {
            'name': _('Billing Copy'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.billing',
            'res_id': copy.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_invoices(self):
        """View invoices for this billing"""
        self.ensure_one()
        if not self.invoice_id:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'message': 'No invoice generated yet.',
                    'type': 'warning',
                }
            }
        
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_revenue(self):
        """View revenue analytics"""
        self.ensure_one()
        return {
            'name': _('Revenue Analytics'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.analytic.line',
            'view_mode': 'graph,pivot,tree',
            'domain': [('partner_id', '=', self.partner_id.id)],
            'context': {'group_by': ['date']},
        }

    def action_view_invoice(self):
        """View invoice (context action)"""
        invoice_id = self.env.context.get('invoice_id')
        if invoice_id:
            return {
                'name': _('Invoice'),
                'type': 'ir.actions.act_window',
                'res_model': 'account.move',
                'res_id': invoice_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def _show_existing_invoice(self):
        """Show the existing invoice"""
        return {
            'name': _('Invoice'),
            'type': 'ir.actions.act_window',
            'res_model': 'account.move',
            'res_id': self.invoice_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.billing') or _('New')
        return super().create(vals_list)
