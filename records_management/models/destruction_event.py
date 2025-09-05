from odoo import models, fields, api

class DestructionEvent(models.Model):
    _name = 'destruction.event'
    _description = 'Destruction Event Tracking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'

    name = fields.Char(string='Event Reference', required=True, default=lambda self: self.env['ir.sequence'].next_by_code('destruction.event'))
    date = fields.Date(string='Destruction Date', required=True, tracking=True)
    time = fields.Float(string='Destruction Time', tracking=True)  # In hours, e.g., 14.5 for 2:30 PM
    technician_id = fields.Many2one('res.users', string='Technician', required=True, tracking=True)
    requestor_id = fields.Many2one('res.users', string='Requestor', tracking=True)
    location_type = fields.Selection([
        ('onsite', 'On-Site'),
        ('offsite', 'Off-Site')
    ], string='Location Type', required=True, tracking=True)
    shredded_items = fields.Text(string='Items Shredded', required=True, tracking=True)  # Description of what was shredded
    quantity = fields.Float(string='Quantity Destroyed', required=True, tracking=True)  # e.g., weight or count
    unit_of_measure = fields.Selection([
        ('kg', 'Kilograms'),
        ('lbs', 'Pounds'),
        ('boxes', 'Boxes'),
        ('files', 'Files')
    ], string='Unit of Measure', required=True, tracking=True)
    notes = fields.Text(string='Notes')
    certificate_id = fields.Many2one('destruction.certificate', string='Related Certificate', tracking=True)
    audit_log_ids = fields.One2many('naid.audit.log', 'event_id', string='Audit Logs')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    @api.model
    def create(self, vals):
        # Auto-create audit log entry for compliance
        record = super().create(vals)
        self.env['naid.audit.log'].create({
            'event_id': record.id,
            'operation': 'destruction',
            'user_id': record.technician_id.id,
            'description': f'Destruction event: {record.shredded_items} - {record.quantity} {record.unit_of_measure}',
            'date': record.date,
        })
        return record
