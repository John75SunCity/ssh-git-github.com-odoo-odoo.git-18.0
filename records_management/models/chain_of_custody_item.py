from odoo import api, fields, models, _


class ChainOfCustodyItem(models.Model):
    """Item line belonging to a chain.of.custody transfer.

    Captures documents/containers with quantity & valuation for insurance.
    """

    _name = 'chain.of.custody.item'
    _description = 'Chain of Custody Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    custody_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Chain of Custody',
        required=True,
        ondelete='cascade',
        index=True,
    )
    document_id = fields.Many2one(comodel_name='records.document', string='Document')
    container_id = fields.Many2one(comodel_name='records.container', string='Container')
    item_type = fields.Selection([
        ('document', 'Document'),
        ('container', 'Container'),
        ('asset', 'Asset'),
        ('other', 'Other'),
    ], string='Item Type', default='document', required=True)
    quantity = fields.Integer(string='Quantity', default=1)
    condition = fields.Selection([
        ('good', 'Good'),
        ('damaged', 'Damaged'),
        ('sealed', 'Sealed'),
        ('opened', 'Opened'),
    ], string='Condition', default='good')
    serial_number = fields.Char(string='Serial Number')
    value = fields.Monetary(string='Value')
    currency_id = fields.Many2one('res.currency', string='Currency', default=lambda self: self.env.company.currency_id.id)
    notes = fields.Text(string='Notes')

    def name_get(self):
        result = []
        for rec in self:
            base = rec.document_id.display_name or rec.container_id.display_name or _('Item')
            label = "%s (%s)" % (base, rec.item_type)
            result.append((rec.id, label))
        return result
