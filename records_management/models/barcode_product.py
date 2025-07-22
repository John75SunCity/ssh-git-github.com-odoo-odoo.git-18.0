from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class BarcodeProduct(models.Model):
    _name = 'barcode.product'
    _description = 'Barcode Product'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    name = fields.Char('Product Name', required=True, tracking=True)
    barcode = fields.Char('Barcode', required=True, index=True, tracking=True)
    product_id = fields.Many2one('product.product', 'Related Product', tracking=True)
    active = fields.Boolean('Active', default=True, tracking=True)
    
    # Product details
    description = fields.Text('Description')
    category = fields.Selection([
        ('storage', 'Storage Service'),
        ('destruction', 'Destruction Service'),
        ('retrieval', 'Retrieval Service'),
        ('scanning', 'Scanning Service'),
        ('other', 'Other Service'),
    ], string='Category', default='storage', tracking=True)
    
    # Pricing
    unit_price = fields.Float('Unit Price', tracking=True)
    currency_id = fields.Many2one('res.currency', 'Currency', 
                                 default=lambda self: self.env.company.currency_id)
    
    # Usage statistics
    usage_count = fields.Integer('Usage Count', default=0)
    last_used = fields.Datetime('Last Used')
    
    @api.constrains('barcode')
    def _check_barcode_unique(self):
        """Ensure barcode is unique"""
        for record in self:
            if record.barcode:
                existing = self.search([
                    ('barcode', '=', record.barcode),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(
                        _('Barcode "%s" already exists for product "%s"') % 
                        (record.barcode, existing[0].name)
                    )

    def action_activate(self):
        """Activate this barcode product"""
        self.write({'active': True})
        self.message_post(body=_('Product activated by %s') % self.env.user.name)

    def action_deactivate(self):
        """Deactivate this barcode product"""
        self.write({'active': False})
        self.message_post(body=_('Product deactivated by %s') % self.env.user.name)

    def action_update_pricing(self):
        """Update pricing for this product"""
        self.ensure_one()
        return {
            'name': _('Update Pricing: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'barcode.product',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {'form_view_initial_mode': 'edit'},
        }

    def action_generate_product_barcodes(self):
        """Generate barcodes for all variants of this product"""
        self.ensure_one()
        variants_without_barcode = self.product_variant_ids.filtered(lambda v: not v.barcode)
        for variant in variants_without_barcode:
            variant.barcode = self.env['ir.sequence'].next_by_code('product.barcode') or f'PROD-{variant.id}'
        return {
            'name': _('Generated Barcodes'),
            'type': 'ir.actions.act_window',
            'res_model': 'product.product',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', variants_without_barcode.ids)],
        }

    def action_view_storage_boxes(self):
        """View storage boxes using this barcode"""
        self.ensure_one()
        return {
            'name': _('Storage Boxes: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box',
            'view_mode': 'tree,form',
            'domain': [('barcode_product_id', '=', self.id)],
            'context': {'default_barcode_product_id': self.id},
        }

    def action_view_shred_bins(self):
        """View shred bins using this barcode"""
        self.ensure_one()
        return {
            'name': _('Shred Bins: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.service',
            'view_mode': 'tree,form',
            'domain': [('barcode_product_id', '=', self.id)],
            'context': {'default_barcode_product_id': self.id},
        }

    def action_view_revenue(self):
        """View revenue report for this product"""
        self.ensure_one()
        return {
            'name': _('Revenue Report: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'account.move.line',
            'view_mode': 'tree,graph,pivot',
            'domain': [('product_id', '=', self.product_id.id)],
            'context': {'group_by': ['date']},
        }

    def increment_usage(self):
        """Increment usage count and update last used"""
        self.write({
            'usage_count': self.usage_count + 1,
            'last_used': fields.Datetime.now()
        })
