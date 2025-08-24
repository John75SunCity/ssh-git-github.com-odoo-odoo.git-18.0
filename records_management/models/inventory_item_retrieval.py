from odoo import models, fields, api, _

class InventoryItemRetrieval(models.Model):
    _name = 'inventory.item.retrieval'
    _description = 'Inventory Item Retrieval'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Retrieval Reference', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    retrieval_date = fields.Datetime(string='Retrieval Date', required=True, default=fields.Datetime.now)
    responsible_id = fields.Many2one('res.users', string='Responsible', required=True, tracking=True)
    item_ids = fields.One2many('inventory.item.retrieval.line', 'retrieval_id', string='Retrieval Lines')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('cancel', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    notes = fields.Text(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('inventory.item.retrieval') or _('New')
        return super().create(vals)
