from odoo import models, fields

class RecordsContainerLine(models.Model):
    _name = 'records.container.line'
    _description = 'Records Container Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'

    container_id = fields.Many2one(comodel_name='records.container', string='Container', required=True, ondelete='cascade')
    sequence = fields.Integer(string='Sequence', default=10)
    name = fields.Char(string='Description', required=True)
    document_type_id = fields.Many2one(comodel_name='records.document.type', string='Document Type')
    quantity = fields.Float(string='Quantity', default=1.0)
    unit_id = fields.Many2one(comodel_name='uom.uom', string='Unit of Measure')
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)

    # Dates and tracking
    date_added = fields.Datetime(string='Date Added', default=fields.Datetime.now)
    date_removed = fields.Datetime(string='Date Removed')

    # Status tracking
    state = fields.Selection([
        ('active', 'Active'),
        ('removed', 'Removed'),
        ('archived', 'Archived')
    ], string='Status', default='active')

    # Reference fields
    reference = fields.Char(string='Reference')
    barcode = fields.Char(string='Barcode')
