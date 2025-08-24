from odoo import models, fields

class NaidCertificateItem(models.Model):
    _name = 'naid.certificate.item'
    _description = 'NAID Destruction Certificate Item'

    certificate_id = fields.Many2one('naid.certificate', string='Certificate', required=True, ondelete='cascade')
    name = fields.Char(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0)
    uom_id = fields.Many2one('uom.uom', string='Unit of Measure', default=lambda self: self.env.ref('uom.product_uom_unit'))
    weight = fields.Float(string='Weight (kg)')
    material_type = fields.Char(string='Material Type', help="e.g., Paper, Hard Drives, Tapes")
