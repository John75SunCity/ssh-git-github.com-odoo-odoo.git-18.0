"""Key Inventory model for Odoo Records Management.
This model manages the inventory of keys, including assignment, status tracking,
location, and company association. It supports audit trails and activity tracking.
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class KeyInventory(models.Model):
    """Model for managing key inventory records.

    Tracks key name, serial number, location, assignment, status, and notes.
    Integrates with Odoo's mail threading and activity mixin for audit and communication.
    """

    _name = 'key.inventory'
    _description = 'Key Inventory'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name asc, id desc'
    _rec_name = 'name'

    name = fields.Char(string='Key Name', required=True, tracking=True)
    serial_number = fields.Char(string='Serial Number', tracking=True)
    location_id = fields.Many2one(comodel_name='stock.location', string='Location', tracking=True)
    assigned_to_id = fields.Many2one(comodel_name='res.users', string='Assigned To', tracking=True)
    status = fields.Selection([
        ('available', 'Available'),
        ('assigned', 'Assigned'),
        ('lost', 'Lost'),
        ('retired', 'Retired'),
    ], string='Status', default='available')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    notes = fields.Text(string='Notes')

    @api.constrains('status')
    def _check_status(self):
        allowed_statuses = {'available', 'assigned', 'lost', 'retired'}
        for record in self:
            if record.status not in allowed_statuses:
                raise ValidationError(_("Invalid status: %s", record.status))
