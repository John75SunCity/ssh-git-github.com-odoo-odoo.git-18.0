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


class RecordsBillingService(models.Model):
    _name = 'records.billing.service'
    _description = 'Billing Generation Service'
    _inherit = '['mail.thread', 'mail.activity.mixin']""'
    _order = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True)
    company_id = fields.Many2one('res.company')
    user_id = fields.Many2one('res.users')
    active = fields.Boolean()
    billing_id = fields.Many2one('records.billing', string='Related Billing')
    state = fields.Selection()
    description = fields.Text()
    notes = fields.Text()
    date = fields.Date()
    action_activate_service = fields.Char(string='Action Activate Service')
    action_archive_service = fields.Char(string='Action Archive Service')
    action_deactivate_service = fields.Char(string='Action Deactivate Service')
    action_view_billing_history = fields.Char(string='Action View Billing History')
    action_view_service_requests = fields.Char(string='Action View Service Requests')
    active_services = fields.Char(string='Active Services')
    activity_ids = fields.One2many('mail.activity', string='Activities')
    applicable_container_types = fields.Char(string='Applicable Container Types')
    archived = fields.Char(string='Archived')
    audit = fields.Char(string='Audit')
    auto_billing = fields.Char(string='Auto Billing')
    auto_billing_enabled = fields.Char(string='Auto Billing Enabled')
    base_rate = fields.Float(string='Base Rate')
    billing_count = fields.Integer(string='Billing Count')
    billing_frequency = fields.Char(string='Billing Frequency')
    billing_information = fields.Char(string='Billing Information')
    button_box = fields.Char(string='Button Box')
    cancellation_policy = fields.Char(string='Cancellation Policy')
    color = fields.Char(string='Color')
    configuration = fields.Char(string='Configuration')
    context = fields.Char(string='Context')
    create_date = fields.Date(string='Create Date')
    create_uid = fields.Char(string='Create Uid')
    currency_id = fields.Many2one('currency')
    domain = fields.Char(string='Domain')
    draft_services = fields.Char(string='Draft Services')
    effective_date = fields.Date(string='Effective Date')
    expiry_date = fields.Date(string='Expiry Date')
    group_billing_frequency = fields.Char(string='Group Billing Frequency')
    group_partner = fields.Char(string='Group Partner')
    group_service_category = fields.Char(string='Group Service Category')
    group_service_type = fields.Selection(string='Group Service Type')
    group_state = fields.Selection(string='Group State')
    help = fields.Char(string='Help')
    inactive_services = fields.Char(string='Inactive Services')
    last_billing_date = fields.Date(string='Last Billing Date')
    maximum_quantity = fields.Char(string='Maximum Quantity')
    message_follower_ids = fields.One2many('mail.followers', string='Followers')
    message_ids = fields.One2many('mail.message', string='Messages')
    minimum_charge = fields.Char(string='Minimum Charge')
    minimum_quantity = fields.Char(string='Minimum Quantity')
    next_billing_date = fields.Date(string='Next Billing Date')
    partner_id = fields.Many2one('res.partner')
    penalty_rate = fields.Float(string='Penalty Rate')
    prorate_billing = fields.Char(string='Prorate Billing')
    rate_tier_ids = fields.One2many('rate.tier')
    rates = fields.Char(string='Rates')
    requires_approval = fields.Char(string='Requires Approval')
    res_model = fields.Char(string='Res Model')
    service_category = fields.Char(string='Service Category')
    service_code = fields.Char(string='Service Code')
    service_details = fields.Char(string='Service Details')
    service_level = fields.Char(string='Service Level')
    service_request_count = fields.Integer(string='Service Request Count')
    service_terms = fields.Char(string='Service Terms')
    service_type = fields.Selection(string='Service Type')
    taxable = fields.Char(string='Taxable')
    terms = fields.Char(string='Terms')
    tier_name = fields.Char(string='Tier Name')
    tier_rate = fields.Float(string='Tier Rate')
    total_billed_amount = fields.Float(string='Total Billed Amount')
    type = fields.Selection(string='Type')
    unit_of_measure = fields.Char(string='Unit Of Measure')
    view_mode = fields.Char(string='View Mode')
    volume_based_pricing = fields.Char(string='Volume Based Pricing')
    web_ribbon = fields.Char(string='Web Ribbon')
    weight_based_pricing = fields.Char(string='Weight Based Pricing')
    write_date = fields.Date(string='Write Date')
    write_uid = fields.Char(string='Write Uid')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_billing_count(self):
            for record in self:""
                record.billing_count = len(record.billing_ids)""

    def _compute_service_request_count(self):
            for record in self:""
                record.service_request_count = len(record.service_request_ids)""

    def _compute_total_billed_amount(self):
            for record in self:""
                record.total_billed_amount = sum(record.line_ids.mapped('amount'))""

    def action_confirm(self):
            """Confirm the record"""
