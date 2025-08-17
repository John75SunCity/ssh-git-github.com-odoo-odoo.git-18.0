from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class BinKeyUnlockService(models.Model):
    _name = 'bin.key.unlock.service'
    _description = 'Bin Key Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    partner_id = fields.Many2one()
    customer_company_id = fields.Many2one()
    service_date = fields.Datetime()
    technician_id = fields.Many2one()
    unlock_reason = fields.Selection()
    unlock_reason_description = fields.Text(string='Reason Description')
    unlock_bin_location = fields.Char(string='Bin Location')
    items_retrieved = fields.Text(string='Items Retrieved')
    unlock_charge = fields.Monetary()
    billable = fields.Boolean(string='Billable Service')
    currency_id = fields.Many2one()
    photo_ids = fields.Many2many()
    service_notes = fields.Text(string='Service Notes')
    state = fields.Selection()
    bin_key_id = fields.Many2one()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    access_code_changed = fields.Char(string='Access Code Changed')
    access_history_count = fields.Integer(string='Access History Count')
    access_level_required = fields.Boolean(string='Access Level Required')
    action_cancel = fields.Char(string='Action Cancel')
    action_complete_service = fields.Char(string='Action Complete Service')
    action_confirm = fields.Char(string='Action Confirm')
    action_reset_to_draft = fields.Char(string='Action Reset To Draft')
    action_start_service = fields.Char(string='Action Start Service')
    action_view_access_history = fields.Char(string='Action View Access History')
    action_view_audit_logs = fields.Char(string='Action View Audit Logs')
    active_services = fields.Char(string='Active Services')
    actual_duration = fields.Char(string='Actual Duration')
    additional_fees = fields.Char(string='Additional Fees')
    assignment_info = fields.Char(string='Assignment Info')
    audit_log_count = fields.Integer(string='Audit Log Count')
    audit_trail_generated = fields.Char(string='Audit Trail Generated')
    authorization_reference = fields.Char(string='Authorization Reference')
    authorized_by = fields.Char(string='Authorized By')
    billing = fields.Char(string='Billing')
    billing_method = fields.Char(string='Billing Method')
    billing_notes = fields.Char(string='Billing Notes')
    biometric_update = fields.Char(string='Biometric Update')
    button_box = fields.Char(string='Button Box')
    chain_of_custody_maintained = fields.Char(string='Chain Of Custody Maintained')
    color = fields.Char(string='Color')
    completed_services = fields.Char(string='Completed Services')
    completion_date = fields.Date(string='Completion Date')
    compliance = fields.Char(string='Compliance')
    compliance_notes = fields.Char(string='Compliance Notes')
    compliance_officer_id = fields.Many2one('compliance.officer')
    context = fields.Char(string='Context')
    department_id = fields.Many2one('department')
    description = fields.Char(string='Description')
    domain = fields.Char(string='Domain')
    emergency = fields.Char(string='Emergency')
    emergency_access = fields.Char(string='Emergency Access')
    emergency_surcharge = fields.Char(string='Emergency Surcharge')
    estimated_duration = fields.Char(string='Estimated Duration')
    financial = fields.Char(string='Financial')
    group_department = fields.Char(string='Group Department')
    group_partner = fields.Char(string='Group Partner')
    group_service_date = fields.Date(string='Group Service Date')
    group_state = fields.Selection(string='Group State')
    group_technician = fields.Char(string='Group Technician')
    help = fields.Char(string='Help')
    identity_verified = fields.Boolean(string='Identity Verified')
    invoice_id = fields.Many2one('invoice')
    invoiced = fields.Char(string='Invoiced')
    location_id = fields.Many2one('location')
    my_services = fields.Char(string='My Services')
    naid_compliant = fields.Char(string='Naid Compliant')
    new_access_code = fields.Char(string='New Access Code')
    payment_terms = fields.Char(string='Payment Terms')
    pricing = fields.Char(string='Pricing')
    requested_date = fields.Date(string='Requested Date')
    res_model = fields.Char(string='Res Model')
    security = fields.Char(string='Security')
    security_info = fields.Char(string='Security Info')
    security_level = fields.Char(string='Security Level')
    service_details = fields.Char(string='Service Details')
    service_info = fields.Char(string='Service Info')
    service_rate = fields.Float(string='Service Rate')
    service_type = fields.Selection(string='Service Type')
    this_week = fields.Char(string='This Week')
    today = fields.Char(string='Today')
    total_cost = fields.Char(string='Total Cost')
    travel_cost = fields.Char(string='Travel Cost')
    type = fields.Selection(string='Type')
    unlock_details = fields.Char(string='Unlock Details')
    verification = fields.Char(string='Verification')
    verification_method = fields.Char(string='Verification Method')
    verification_reference = fields.Char(string='Verification Reference')
    view_mode = fields.Char(string='View Mode')
    witness_id = fields.Many2one('witness')
    witness_required = fields.Boolean(string='Witness Required')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_access_history_count(self):
                for record in self:""
                record.access_history_count = len(record.access_history_ids)""

    def _compute_audit_log_count(self):
                for record in self:""
                record.audit_log_count = len(record.audit_log_ids)""

    def _compute_total_cost(self):
                for record in self:""
                record.total_cost = sum(record.line_ids.mapped('amount'))""

    def _compute_bin_key_id(self):
                """Find the active bin key for the contact""":
                    pass

    def create(self, vals_list):
                """Generate sequence number for new services""":
                if vals.get("name", "New") == "New":
                    vals["name"] = ()
                        self.env["ir.sequence"].next_by_code()
                            "bin.key.unlock.service"
                        ""
                        or "ULS-NEW"
                    ""

    def action_complete_service(self):
                """Mark service as completed"""

    def action_create_invoice(self):
                """Create invoice for billable unlock service""":

    def _create_audit_log(self, action):
                """Create audit log entry"""
