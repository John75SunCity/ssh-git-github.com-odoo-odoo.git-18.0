from odoo import models, fields, api, _

class RecordsContainerLog(models.Model):
    _name = 'records.container.log'
    _description = 'Records Container Log'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'
    _rec_name = 'display_name'

    name = fields.Char(string='Log Reference', required=True, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    container_id = fields.Many2one('records.container', string='Container', required=True)
    event_type = fields.Selection([
        ('move', 'Move'),
        ('audit', 'Audit'),
        ('access', 'Access'),
        ('maintenance', 'Maintenance'),
        ('other', 'Other'),
    ], string='Event Type', required=True)
    date = fields.Datetime(string='Event Date', default=fields.Datetime.now, required=True)
    user_id = fields.Many2one('res.users', string='User', default=lambda self: self.env.user)
    notes = fields.Text(string='Notes')

    @api.depends('name', 'event_type')
    def _compute_display_name(self):
        for rec in self:
            rec.display_name = f"{rec.name or ''} - {rec.event_type or ''}"
