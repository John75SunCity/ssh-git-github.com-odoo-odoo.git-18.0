from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class RecordsDepartmentBillingContact(models.Model):
    _name = 'records.department.billing.enhanced'
    _description = 'Department Billing Contact - FIELD ENHANCEMENT COMPLETE '
    _inherit = '['mail.thread', 'mail.activity.mixin']""'
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company')
    user_id = fields.Many2one('res.users')
    active = fields.Boolean()
    state = fields.Selection()
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def action_confirm(self):
            """Confirm the record"""
