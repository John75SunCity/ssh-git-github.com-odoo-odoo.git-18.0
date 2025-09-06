from odoo import api, fields, models, _


class ChainOfCustodyEvent(models.Model):
    """Individual custody event linked to a chain.of.custody record.

    Minimal implementation to satisfy view references and relational integrity.
    Extendable for future audit enhancements (GPS, signatures, etc.).
    """

    _name = 'chain.of.custody.event'
    _description = 'Chain of Custody Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    custody_id = fields.Many2one(
        comodel_name='chain.of.custody',
        string='Chain of Custody',
        required=True,
        ondelete='cascade',
        index=True,
    )
    event_date = fields.Datetime(string='Event Date', default=fields.Datetime.now, required=True)
    event_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('handoff', 'Handoff'),
        ('inspection', 'Inspection'),
        ('transport', 'Transport'),
        ('arrival', 'Arrival'),
        ('storage', 'Storage'),
        ('exception', 'Exception'),
    ], string='Event Type', default='pickup', required=True, tracking=True)
    responsible_person = fields.Char(string='Responsible Person')
    location = fields.Char(string='Location')
    signature_verified = fields.Boolean(string='Signature Verified')
    temperature = fields.Float(string='Temperature (°C)')
    humidity = fields.Float(string='Humidity (%)')
    notes = fields.Text(string='Notes')

    # Basic name_get for readability in many2one dropdowns
    def name_get(self):
        result = []
        for rec in self:
            label = "%s - %s" % (rec.event_date and rec.event_date.strftime('%Y-%m-%d %H:%M') or '', rec.event_type or '')
            result.append((rec.id, label))
        return result
