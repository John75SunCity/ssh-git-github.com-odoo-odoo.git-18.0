from odoo import _, fields, models


class NaidComplianceChecklist(models.Model):
    _name = 'naid.compliance.checklist'
    _description = 'NAID Compliance Checklist'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'

    name = fields.Char(string='Checklist Name', required=True, tracking=True)
    active = fields.Boolean(default=True)
    description = fields.Text(string='Description')
    # Inverse side expected by checklist item model (assumes item has checklist_id Many2one)
    item_ids = fields.One2many(
        comodel_name='naid.compliance.checklist.item',
        inverse_name='checklist_id',
        string='Items'
    )
