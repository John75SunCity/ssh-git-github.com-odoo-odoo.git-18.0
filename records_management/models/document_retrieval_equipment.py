from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields


class DocumentRetrievalEquipment(models.Model):
    _name = 'document.retrieval.equipment'
    _description = 'Document Retrieval Equipment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    equipment_type = fields.Selection()
    status = fields.Selection()
    location_id = fields.Many2one('records.location')
    assigned_to_id = fields.Many2one('hr.employee')
    model = fields.Char(string='Model')
    serial_number = fields.Char(string='Serial Number')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_expiry = fields.Date(string='Warranty Expiry')
    last_maintenance = fields.Date(string='Last Maintenance')
    next_maintenance = fields.Date(string='Next Maintenance')
    maintenance_notes = fields.Text(string='Maintenance Notes')
    usage_hours = fields.Float(string='Total Usage Hours')
    current_work_order_id = fields.Many2one()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    state = fields.Selection()
