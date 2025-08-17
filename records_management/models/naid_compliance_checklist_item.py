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
from odoo.exceptions import ValidationError


class NaidComplianceChecklistItem(models.Model):
    _name = 'naid.compliance.checklist.item'
    _description = 'NAID Compliance Checklist Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    sequence = fields.Integer(string='Sequence')
    description = fields.Text(string='Item Description')
    active = fields.Boolean(string='Active')
    checklist_id = fields.Many2one()
    category = fields.Selection()
    is_compliant = fields.Boolean()
    compliance_date = fields.Date(string='Compliance Date')
    verified_by_id = fields.Many2one('res.users')
    evidence_attachment = fields.Binary(string='Evidence')
    evidence_filename = fields.Char(string='Evidence Filename')
    notes = fields.Text(string='Notes')
    is_mandatory = fields.Boolean(string='Mandatory')
    risk_level = fields.Selection()
    deadline = fields.Date(string='Deadline')
    is_overdue = fields.Boolean()
    days_until_deadline = fields.Integer()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_is_overdue(self):
            """Check if item is overdue""":

    def _compute_days_until_deadline(self):
            """Calculate days until deadline"""

    def action_mark_non_compliant(self):
            """Mark item as non-compliant"""

    def _check_deadline(self):
            """Validate deadline is not in the past for new items""":
