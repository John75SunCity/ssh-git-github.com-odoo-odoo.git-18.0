from odoo import fields, models

class ShreddingService(models.Model):
    _name = 'shredding.service'
    _description = 'Shredding Service'

    name = fields.Char(string='Name', required=True)
