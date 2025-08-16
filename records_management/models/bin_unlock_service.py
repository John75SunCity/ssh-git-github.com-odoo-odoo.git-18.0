# -*- coding: utf-8 -*-
from odoo import models, fields, api, _

from odoo.exceptions import UserError, ValidationError




class BinUnlockService(models.Model):
    _name = "bin.unlock.service"
    _description = "Bin Unlock Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True,,
    index=True),
    description = fields.Text(string="Description"),
    sequence = fields.Integer(string="Sequence",,
    default=10),
    active = fields.Boolean(string="Active",,
    default=True),
    company_id = fields.Many2one("res.company", string="Company",,
    default=lambda self: self.env.company),
    user_id = fields.Many2one("res.users", string="Assigned User",,
    default=lambda self: self.env.user)

        # ============================================================================
    # STATE MANAGEMENT
        # ============================================================================
    state = fields.Selection([))
        ("draft", "Draft"), 
        ("active", "Active"),
        ("inactive", "Inactive"), 
        ("archived", "Archived")
    

        # ============================================================================
    # SERVICE REQUEST DETAILS
        # ============================================================================
    service_type = fields.Selection([))
        ("emergency", "Emergency Unlock"), 
        ("scheduled", "Scheduled Unlock"),
        ("bulk", "Bulk Unlock"), 
        ("maintenance", "Maintenance Unlock")
    

    request_date = fields.Datetime(string="Request Date", default=fields.Datetime.now,,
    tracking=True),
    scheduled_date = fields.Datetime(string="Scheduled Date",,
    tracking=True),
    completion_date = fields.Datetime(string="Completion Date",,
    tracking=True)

    priority = fields.Selection([))
        ("low", "Low"), 
        ("normal", "Normal"), 
        ("high", "High"), 
        ("urgent", "Urgent")
    

        # ============================================================================
    # BIN & KEY INFORMATION
        # ============================================================================
    partner_id = fields.Many2one("res.partner", string="Customer", required=True,,
    tracking=True),
    bin_id = fields.Many2one(
        "shred.bin", string="Shred Bin", required=True, tracking=True
    
    
    key_id = fields.Many2one("bin.key", string="Key",,
    tracking=True)

    bin_location = fields.Char(string="Bin Location"),
    key_serial_number = fields.Char(string="Key Serial Number"),
    unlock_method = fields.Selection([))
        ("physical_key", "Physical Key"), 
        ("electronic", "Electronic"),
        ("master_key", "Master Key"), 
        ("emergency_override", "Emergency Override")
    

        # ============================================================================
    # TECHNICIAN & SCHEDULING
        # ============================================================================
    assigned_technician_id = fields.Many2one("res.users", string="Assigned Technician",,
    tracking=True),
    backup_technician_id = fields.Many2one("res.users",,
    string="Backup Technician"),
    estimated_duration = fields.Float(string="Estimated Duration (hours)", default=0.5)
    actual_duration = fields.Float(string="Actual Duration (hours)")

        # ============================================================================
    # SERVICE DETAILS
        # ============================================================================
    reason_for_unlock = fields.Text(string="Reason for Unlock",,
    required=True):
        pass
    special_instructions = fields.Text(string="Special Instructions"),
    security_notes = fields.Text(string="Security Notes")

    requires_escort = fields.Boolean(string="Requires Escort",,
    default=False),
    witness_required = fields.Boolean(string="Witness Required",,
    default=False),
    witness_name = fields.Char(string="Witness Name")

        # ============================================================================
    # COMPLIANCE & DOCUMENTATION
        # ============================================================================
    authorization_code = fields.Char(string="Authorization Code"),
    service_report = fields.Text(string="Service Report"),
    completion_notes = fields.Text(string="Completion Notes")

    photo_before = fields.Binary(string="Photo Before"),
    photo_after = fields.Binary(string="Photo After"),
    service_certificate = fields.Binary(string="Service Certificate")

        # ============================================================================
    # FINANCIAL TRACKING
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency", 
        string="Currency", 
        default=lambda self: self.env.company.currency_id
    
    service_cost = fields.Monetary(string="Service Cost",,
    currency_field="currency_id"),
    emergency_surcharge = fields.Monetary(string="Emergency Surcharge",,
    currency_field="currency_id"),
    total_cost = fields.Monetary(
        string="Total Cost", 
        currency_field="currency_id", 
        compute="_compute_total_cost", 
        store=True
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    related_request_ids = fields.Many2many("portal.request",,
    string="Related Portal Requests")

        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    display_name = fields.Char(compute="_compute_display_name", string="Display Name",,
    store=True)

        # ============================================================================
    # AUTO-GENERATED FIELDS
        # ============================================================================
    customer_key_restricted = fields.Char(string='Customer Key Restricted',,
    tracking=True),
    unlock_reason_code = fields.Char(string='Unlock Reason Code',,
    tracking=True),
    service_start_time = fields.Datetime(string='Service Start Time'),
    service_rate = fields.Float(string='Service Rate',,
    default=25.0),
    invoice_id = fields.Many2one('account.move',,
    string='Invoice')

        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many("mail.followers", "res_id",,
    string="Followers"),
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages"),
    context = fields.Char(string='Context'),
    domain = fields.Char(string='Domain'),
    help = fields.Char(string='Help'),
    res_model = fields.Char(string='Res Model'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    view_mode = fields.Char(string='View Mode')

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends("service_cost", "emergency_surcharge")
    def _compute_total_cost(self):
        for record in self:
            record.total_cost = record.service_cost + record.emergency_surcharge

    @api.depends("name", "bin_id", "partner_id")
    def _compute_display_name(self):
        for record in self:
            if record.bin_id and record.partner_id:
                record.display_name = _("%s - %s - %s", record.name, record.bin_id.name, record.partner_id.name)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or "New"

    # ============================================================================
        # DEFAULT METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get("name"):
                vals["name") = self.env["ir.sequence"].next_by_code("bin.unlock.service") or "BUS/"
        return super().create(vals_list)

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_schedule(self):
        self.ensure_one()
        self.ensure_one()
        if not self.scheduled_date:
            raise UserError(_("Please set a scheduled date first."))
        self.write({"state": "active"})
        self.message_post(body=_("Service scheduled"))

    def action_start_service(self):
        self.ensure_one()
        self.ensure_one()
        if self.state != "active":
            raise UserError(_("Only active services can be started."))
        self.write({)}
            "state": "active",
            "service_start_time": fields.Datetime.now()
        
        self.message_post(body=_("Service started"))

    def action_complete(self):
        self.ensure_one()
        self.ensure_one()
        if not self.completion_notes:
            raise UserError(_("Please add completion notes before completing the service."))
        self.write({)}
            "state": "inactive",
            "completion_date": fields.Datetime.now()
        
        self.message_post(body=_("Service completed"))

    def action_cancel(self):
        self.ensure_one()
        self.ensure_one()
        self.write({"state": "inactive"})
        self.message_post(body=_("Service cancelled"))

    def action_generate_certificate(self):
        self.ensure_one()
        self.ensure_one()
        return {}
            "type": "ir.actions.act_window",
            "name": _("Generate Service Certificate"),
            "res_model": "service.certificate.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_service_id": self.id},
        

    def action_create_invoice(self):
        """Create Invoice for the unlock service""":
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError(_("Invoice already exists for this service")):
        invoice_vals = {}
            'move_type': 'out_invoice',
            'partner_id': self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'invoice_line_ids': [(0, 0, {)]}
                'name': _("Bin Unlock Service: %s", self.name),
                'quantity': 1,
                'price_unit': self.total_cost,
            
        
        
        invoice = self.env['account.move'].create(invoice_vals)
        self.invoice_id = invoice.id
        self.message_post(body=_("Invoice created: %s", invoice.name))
        
        return {}
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        

    def action_mark_completed(self):
        """Mark service as completed"""

        self.ensure_one()
        
        if self.state != "active":
            raise UserError(_("Only active services can be marked as completed"))
        
        self.write({)}
            "state": "inactive",
            "completion_date": fields.Datetime.now()
        
        self.message_post(body=_("Service marked as completed"))
        return True

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def get_service_summary(self):
        """Return formatted service summary"""
        self.ensure_one()
        return {}
            "service_name": self.name,
            "customer": self.partner_id.name,
            "bin": self.bin_id.name if self.bin_id else "N/A",:
            "status": self.state,
            "scheduled": self.scheduled_date.strftime("%Y-%m-%d %H:%M") if self.scheduled_date else "Not scheduled",:
            "cost": self.total_cost,
        

    def create_audit_log(self, action):
        """Create NAID compliance audit log"""
        self.ensure_one()
        self.env['naid.audit.log'].create({)}
            'name': _("Bin Unlock: %s", action),
            'model_name': self._name,
            'record_id': self.id,
            'action_type': action,
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'notes': _("Bin unlock service %s for bin %s", action, self.bin_id.name if self.bin_id else 'Unknown'),:
        

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains("scheduled_date", "request_date")
    def _check_dates(self):
        for record in self:
            if record.scheduled_date and record.request_date and record.scheduled_date < record.request_date:
                raise ValidationError(_("Scheduled date cannot be before request date."))

    @api.constrains("estimated_duration", "actual_duration")
    def _check_duration(self):
        for record in self:
            if record.estimated_duration < 0 or record.actual_duration < 0:
                raise ValidationError(_("Duration cannot be negative."))

    @api.constrains("service_cost", "emergency_surcharge")
    def _check_costs(self):
        for record in self:
            if record.service_cost < 0 or record.emergency_surcharge < 0:
                raise ValidationError(_("Costs cannot be negative."))

    @api.constrains("witness_required", "witness_name")
    def _check_witness_requirements(self):
        for record in self:
            if record.witness_required and not record.witness_name:
                raise ValidationError(_("Witness name is required when witness is required."))

    @api.depends('service_start_time', 'service_end_time')
    def _compute_service_duration(self):
        """Calculate service duration"""
        for record in self:
            if record.service_start_time and record.service_end_time:
                delta = record.service_end_time - record.service_start_time
                record.service_duration = delta.total_seconds() / 3600.0  # Hours
            else:
                record.service_duration = 0.0
