# Updated file: Added @api.model_create_multi decorator to override create in batch mode (fixes deprecation warning in log for non-batch create). This accomplishes efficient multi-record creation
# Added missing fields: is_walk_in and linked_visitor_id to fix view validation errors

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.sign.models.sign_request import SignRequest  # Explicit import for integration

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Removed 'sign.mixin' - invalid/non-existent
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', default='New', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")  # Added for granular requests
    request_type = fields.Selection([
        ('destruction', 'Destruction Request'),
        ('service', 'Service Request'),
        ('inventory_checkout', 'Inventory Checkout'),
        ('billing_update', 'Billing Update'),
        ('quote_generate', 'Quote Generation'),
    ], string='Request Type', required=True)
    description = fields.Html(string='Description')
    suggested_date = fields.Date(string='Suggested Date', help='Customer suggested date for service/request')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft')
    
    # Phase 1: Explicit Activity & Messaging Fields (3 fields)