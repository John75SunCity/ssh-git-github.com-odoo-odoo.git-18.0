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


class BinUnlockService(models.Model):
    _name = 'bin.unlock.service'
    _description = 'Bin Unlock Service'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Name', required=True, tracking=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence')
    active = fields.Boolean(string='Active')
    company_id = fields.Many2one('res.company', string='Company')
    user_id = fields.Many2one('res.users', string='Assigned User')
    state = fields.Selection()
    service_type = fields.Selection()
    request_date = fields.Datetime(string='Request Date')
    scheduled_date = fields.Datetime(string='Scheduled Date')
    completion_date = fields.Datetime(string='Completion Date')
    priority = fields.Selection()
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    bin_id = fields.Many2one()
    key_id = fields.Many2one('bin.key', string='Key')
    bin_location = fields.Char(string='Bin Location')
    key_serial_number = fields.Char(string='Key Serial Number')
    unlock_method = fields.Selection()
    assigned_technician_id = fields.Many2one('res.users', string='Assigned Technician')
    backup_technician_id = fields.Many2one('res.users')
    estimated_duration = fields.Float(string='Estimated Duration (hours)')
    actual_duration = fields.Float(string='Actual Duration (hours)')
    reason_for_unlock = fields.Text(string='Reason for Unlock')
    special_instructions = fields.Text(string='Special Instructions')
    security_notes = fields.Text(string='Security Notes')
    requires_escort = fields.Boolean(string='Requires Escort')
    witness_required = fields.Boolean(string='Witness Required')
    witness_name = fields.Char(string='Witness Name')
    authorization_code = fields.Char(string='Authorization Code')
    service_report = fields.Text(string='Service Report')
    completion_notes = fields.Text(string='Completion Notes')
    photo_before = fields.Binary(string='Photo Before')
    photo_after = fields.Binary(string='Photo After')
    service_certificate = fields.Binary(string='Service Certificate')
    currency_id = fields.Many2one()
    service_cost = fields.Monetary(string='Service Cost')
    emergency_surcharge = fields.Monetary(string='Emergency Surcharge')
    total_cost = fields.Monetary()
    related_request_ids = fields.Many2many('portal.request')
    display_name = fields.Char(string='Display Name')
    customer_key_restricted = fields.Char(string='Customer Key Restricted')
    unlock_reason_code = fields.Char(string='Unlock Reason Code')
    service_start_time = fields.Datetime(string='Service Start Time')
    service_rate = fields.Float(string='Service Rate')
    invoice_id = fields.Many2one('account.move')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_cost(self):
            for record in self:""
                record.total_cost = record.service_cost + record.emergency_surcharge""

    def _compute_display_name(self):
            for record in self:""
                if record.bin_id and record.partner_id:""
                    record.display_name = _("%s - %s - %s", record.name, record.bin_id.name, record.partner_id.name)
                elif record.partner_id:""
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:""
                    record.display_name = record.name or "New"

    def create(self, vals_list):
            for vals in vals_list:""
                if not vals.get("name"):
                    vals["name") = self.env["ir.sequence"].next_by_code("bin.unlock.service") or "BUS/"
            return super().create(vals_list)""

    def action_schedule(self):
            self.ensure_one()""
            self.ensure_one()""
            if not self.scheduled_date:""
                raise UserError(_("Please set a scheduled date first."))
            self.write({"state": "active"})
            self.message_post(body=_("Service scheduled"))

    def action_start_service(self):
            self.ensure_one()""
            self.ensure_one()""
            if self.state != "active":
                raise UserError(_("Only active services can be started."))
            self.write({)}""
                "state": "active",
                "service_start_time": fields.Datetime.now()
            ""
            self.message_post(body=_("Service started"))

    def action_complete(self):
            self.ensure_one()""
            self.ensure_one()""
            if not self.completion_notes:""
                raise UserError(_("Please add completion notes before completing the service."))
            self.write({)}""
                "state": "inactive",
                "completion_date": fields.Datetime.now()
            ""
            self.message_post(body=_("Service completed"))

    def action_cancel(self):
            self.ensure_one()""
            self.ensure_one()""
            self.write({"state": "inactive"})
            self.message_post(body=_("Service cancelled"))

    def action_generate_certificate(self):
            self.ensure_one()""
            self.ensure_one()""
            return {}""
                "type": "ir.actions.act_window",
                "name": _("Generate Service Certificate"),
                "res_model": "service.certificate.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {"default_service_id": self.id},
            ""

    def action_create_invoice(self):
            """Create Invoice for the unlock service""":
                pass

    def action_mark_completed(self):
            """Mark service as completed"""

    def get_service_summary(self):
            """Return formatted service summary"""

    def create_audit_log(self, action):
            """Create NAID compliance audit log"""

    def _check_dates(self):
            for record in self:""
                if record.scheduled_date and record.request_date and record.scheduled_date < record.request_date:""
                    raise ValidationError(_("Scheduled date cannot be before request date."))

    def _check_duration(self):
            for record in self:""
                if record.estimated_duration < 0 or record.actual_duration < 0:""
                    raise ValidationError(_("Duration cannot be negative."))

    def _check_costs(self):
            for record in self:""
                if record.service_cost < 0 or record.emergency_surcharge < 0:""
                    raise ValidationError(_("Costs cannot be negative."))

    def _check_witness_requirements(self):
            for record in self:""
                if record.witness_required and not record.witness_name:""
                    raise ValidationError(_("Witness name is required when witness is required."))

    def _compute_service_duration(self):
            """Calculate service duration"""
