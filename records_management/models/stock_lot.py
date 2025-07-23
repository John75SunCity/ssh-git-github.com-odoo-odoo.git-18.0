# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, _


class StockLot(models.Model):
    _inherit = 'stock.lot'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    # Customer tracking for records management
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer associated with this lot/serial number'
    )
    
    # Extensions for shredding integration (e.g., link to shredding service)
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service'
    )

    def action_view_customer_lots(self):
        """View all lots for this customer"""
        self.ensure_one()
        return {
            'name': _('Customer Lots'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'view_mode': 'tree,form',
            'domain': [('customer_id', '=', self.customer_id.id)],
            'context': {'default_customer_id': self.customer_id.id},
        }

    def action_schedule_shredding(self):
        """Schedule shredding for this lot"""
        self.ensure_one()
        return {
            'name': _('Schedule Shredding'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.schedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_lot_id': self.id},
        }

    def action_view_shredding_service(self):
        """View associated shredding service"""
        self.ensure_one()
        if self.shredding_service_id:
            return {
                'name': _('Shredding Service'),
                'type': 'ir.actions.act_window',
                'res_model': 'shredding.service',
                'res_id': self.shredding_service_id.id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    def action_update_customer(self):
        """Update customer for this lot"""
        self.ensure_one()
        return {
            'name': _('Update Customer'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.lot',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_print_label(self):
        """Print lot label"""
        self.ensure_one()
        return {
            'name': _('Print Lot Label'),
            'type': 'ir.actions.report',
            'report_name': 'records_management.lot_label_report',
            'report_type': 'qweb-pdf',
            'report_file': 'records_management.lot_label_report',
            'context': {'active_ids': [self.id]},
        }
