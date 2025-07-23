# -*- coding: utf-8 -*-
from odoo import fields, models, api, _

class ProductTemplate(models.Model):
    _inherit = 'product.template'

    # Phase 1: Explicit Activity Field (1 field)
    activity_ids = fields.One2many('mail.activity', 'res_id', string='Activities')

    shred_type = fields.Selection([
        ('document', 'Document Shredding'),
        ('hard_drive', 'Hard Drive Destruction'),
        ('uniform', 'Uniform Shredding'),
    ], string='Shred Type', help='Type of shredding service for NAID-compliant categorization.')
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True, help='Flag if this product meets NAID AAA standards.')
    retention_note = fields.Text(string='Retention Note', compute='_compute_retention_note', store=True, 
                                 help='Computed note for ISO data integrity (e.g., retention policies).')

    @api.depends('type')
    def _compute_retention_note(self):
        for rec in self:
            if rec.type == 'service' and rec.shred_type:
                rec.retention_note = f"Service: {rec.shred_type}. Retain logs for 7 years per NAID standards."
            else:
                rec.retention_note = ""

    def action_view_sales(self):
        """View sales history for this product"""
        self.ensure_one()
        return {
            'name': _('Sales History: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'sale.order.line',
            'view_mode': 'tree,form',
            'domain': [('product_id.product_tmpl_id', '=', self.id)],
            'context': {'default_product_id': self.product_variant_ids[0].id if self.product_variant_ids else False},
        }

    def action_configure_pricing(self):
        """Configure pricing for this product"""
        self.ensure_one()
        return {
            'name': _('Configure Pricing: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_configure_variants(self):
        """Configure product variants"""
        self.ensure_one()
        return {
            'name': _('Product Variants: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_pricing_rules(self):
        """View pricing rules for this product"""
        self.ensure_one()
        return {
            'name': _('Pricing Rules: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_duplicate(self):
        """Duplicate this product"""
        self.ensure_one()
        new_product = self.copy({'name': _('%s (Copy)') % self.name})
        return {
            'name': _('Duplicated Product'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': new_product.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_update_costs(self):
        """Update product costs"""
        self.ensure_one()
        return {
            'name': _('Update Costs: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.template',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_view_variants(self):
        """View product variants"""
        self.ensure_one()
        return {
            'name': _('Product Variants: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }

    def action_view_pricing_history(self):
        """View pricing history"""
        self.ensure_one()
        return {
            'name': _('Pricing History: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'product.pricelist.item',
            'view_mode': 'tree,form',
            'domain': [('product_tmpl_id', '=', self.id)],
            'context': {'default_product_tmpl_id': self.id},
        }
