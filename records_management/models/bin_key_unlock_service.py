from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
    class BinKeyUnlockService(models.Model):
    _name = "bin.key.unlock.service"
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "bin.key.unlock.service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Bin Key Unlock Service"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "service_date desc, name"
    _rec_name = "name"
""
        # Core identification fields""
    name = fields.Char(""
        string="Service Reference", required=True, tracking=True, index=True
    ""
    company_id = fields.Many2one(""
        "res.company", default=lambda self: self.env.company, required=True
    ""
    active = fields.Boolean(string="Active",,
    default=True)""
""
        # Service details""
    partner_id = fields.Many2one(""
        "res.partner", string="Contact", required=True, tracking=True
    ""
    customer_company_id = fields.Many2one(""
        "res.partner",
        string="Customer Company",
        related="partner_id.parent_id",
        store=True,""
    ""
""
        # Service information""
    service_date = fields.Datetime(""
        string="Service Date", default=fields.Datetime.now, required=True
    ""
    technician_id = fields.Many2one(""
        "res.users",
        string="Technician",
        default=lambda self: self.env.user,""
        required=True,""
    ""
""
        # Unlock details""
    ,""
    unlock_reason = fields.Selection(""
        [)""
            ("lost_key", "Lost Key"),
            ("locked_out", "Locked Out"),
            ("emergency_access", "Emergency Access"),
            ("maintenance", "Maintenance Required"),
            ("other", "Other Reason"),
        ""
        string="Unlock Reason",
        required=True,""
        tracking=True,""
    ""
""
    unlock_reason_description = fields.Text(string="Reason Description"),
    unlock_bin_location = fields.Char(string="Bin Location",,
    required=True),""
    items_retrieved = fields.Text(string="Items Retrieved")
""
        # Financial fields""
    unlock_charge = fields.Monetary(""
        string="Unlock Charge", currency_field="currency_id"
    ""
    billable = fields.Boolean(string="Billable Service",,
    default=True),""
    currency_id = fields.Many2one(""
        "res.currency", default=lambda self: self.env.company.currency_id
    ""
""
        # Documentation""
    photo_ids = fields.Many2many(""
        "ir.attachment",
        "unlock_service_photo_rel",
        "service_id",
        "attachment_id",
        string="Service Photos",
        help="Photos documenting the unlock service",
    ""
    ,""
    service_notes = fields.Text(string="Service Notes")
""
        # State management""
    state = fields.Selection(""
        [)""
            ("draft", "Draft"),
            ("completed", "Completed"),
            ("invoiced", "Invoiced"),
            ("cancelled", "Cancelled"),
        ""
        string="Status",
        default="draft",
        tracking=True,""
    ""
""
        # Related bin key""
    bin_key_id = fields.Many2one(""
        "bin.key",
        string="Related Bin Key",
        compute="_compute_bin_key_id",
        store=True,""
    ""
""
        # Mail thread framework fields""
    activity_ids = fields.One2many(""
        "mail.activity", "res_id", string="Activities"
    ""
    message_follower_ids = fields.One2many(""
        "mail.followers", "res_id", string="Followers"
    ""
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages"),
    access_code_changed = fields.Char(string='Access Code Changed'),
    access_history_count = fields.Integer(string='Access History Count', compute='_compute_access_history_count',,
    store=True),
    access_level_required = fields.Boolean(string='Access Level Required',,
    default=False),
    action_cancel = fields.Char(string='Action Cancel'),
    action_complete_service = fields.Char(string='Action Complete Service'),
    action_confirm = fields.Char(string='Action Confirm'),
    action_reset_to_draft = fields.Char(string='Action Reset To Draft'),
    action_start_service = fields.Char(string='Action Start Service'),
    action_view_access_history = fields.Char(string='Action View Access History'),
    action_view_audit_logs = fields.Char(string='Action View Audit Logs'),
    active_services = fields.Char(string='Active Services'),
    actual_duration = fields.Char(string='Actual Duration'),
    additional_fees = fields.Char(string='Additional Fees'),
    assignment_info = fields.Char(string='Assignment Info'),
    audit_log_count = fields.Integer(string='Audit Log Count', compute='_compute_audit_log_count',,
    store=True),
    audit_trail_generated = fields.Char(string='Audit Trail Generated'),
    authorization_reference = fields.Char(string='Authorization Reference'),
    authorized_by = fields.Char(string='Authorized By'),
    billing = fields.Char(string='Billing'),
    billing_method = fields.Char(string='Billing Method'),
    billing_notes = fields.Char(string='Billing Notes'),
    biometric_update = fields.Char(string='Biometric Update'),
    button_box = fields.Char(string='Button Box'),
    chain_of_custody_maintained = fields.Char(string='Chain Of Custody Maintained'),
    color = fields.Char(string='Color'),
    completed_services = fields.Char(string='Completed Services'),
    completion_date = fields.Date(string='Completion Date'),
    compliance = fields.Char(string='Compliance'),
    compliance_notes = fields.Char(string='Compliance Notes'),
    compliance_officer_id = fields.Many2one('compliance.officer',,
    string='Compliance Officer Id'),
    context = fields.Char(string='Context'),
    department_id = fields.Many2one('department',,
    string='Department Id'),
    description = fields.Char(string='Description'),
    domain = fields.Char(string='Domain'),
    emergency = fields.Char(string='Emergency'),
    emergency_access = fields.Char(string='Emergency Access'),
    emergency_surcharge = fields.Char(string='Emergency Surcharge'),
    estimated_duration = fields.Char(string='Estimated Duration'),
    financial = fields.Char(string='Financial'),
    group_department = fields.Char(string='Group Department'),
    group_partner = fields.Char(string='Group Partner'),
    group_service_date = fields.Date(string='Group Service Date'),
    group_state = fields.Selection([), string='Group State')  # TODO: Define selection options
    group_technician = fields.Char(string='Group Technician'),
    help = fields.Char(string='Help'),
    identity_verified = fields.Boolean(string='Identity Verified',,
    default=False),
    invoice_id = fields.Many2one('invoice',,
    string='Invoice Id'),
    invoiced = fields.Char(string='Invoiced'),
    location_id = fields.Many2one('location',,
    string='Location Id'),
    my_services = fields.Char(string='My Services'),
    naid_compliant = fields.Char(string='Naid Compliant'),
    new_access_code = fields.Char(string='New Access Code'),
    payment_terms = fields.Char(string='Payment Terms'),
    pricing = fields.Char(string='Pricing'),
    requested_date = fields.Date(string='Requested Date'),
    res_model = fields.Char(string='Res Model'),
    security = fields.Char(string='Security'),
    security_info = fields.Char(string='Security Info'),
    security_level = fields.Char(string='Security Level'),
    service_details = fields.Char(string='Service Details'),
    service_info = fields.Char(string='Service Info'),
    service_rate = fields.Float(string='Service Rate',,
    digits=(12, 2))
    service_type = fields.Selection([), string='Service Type')  # TODO: Define selection options
    this_week = fields.Char(string='This Week'),
    today = fields.Char(string='Today'),
    total_cost = fields.Char(string='Total Cost'),
    travel_cost = fields.Char(string='Travel Cost'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    unlock_details = fields.Char(string='Unlock Details'),
    verification = fields.Char(string='Verification'),
    verification_method = fields.Char(string='Verification Method'),
    verification_reference = fields.Char(string='Verification Reference'),
    view_mode = fields.Char(string='View Mode'),
    witness_id = fields.Many2one('witness',,"
    string='Witness Id'),""
    witness_required = fields.Boolean(string='Witness Required',,""
    default=False)""
""
    @api.depends('access_history_ids')""
    def _compute_access_history_count(self):""
        for record in self:""
            record.access_history_count = len(record.access_history_ids)""
""
    @api.depends('audit_log_ids')""
    def _compute_audit_log_count(self):""
        for record in self:""
            record.audit_log_count = len(record.audit_log_ids)""
""
    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies""
    def _compute_total_cost(self):""
        for record in self:""
            record.total_cost = sum(record.line_ids.mapped('amount'))""
""
    @api.depends("partner_id")
    def _compute_bin_key_id(self):""
        """Find the active bin key for the contact"""
"""
"""                bin_key = self.env["bin.key").search()"
                    []""
                        ("partner_id", "= """", record.partner_id.id),"
                        (""""active", "= """"
                        (""""state", "in", ("issued", "active"),"
                    ""
                    limit=1,""
                ""
                record.bin_key_id = bin_key.id if bin_key else False:""
            else:""
                record.bin_key_id = False""
""
    @api.model_create_multi""
    def create(self, vals_list):""
        """Generate sequence number for new services"""
            if vals.get("name", "New") == "New":
                vals["name"] = ()
                    self.env["ir.sequence"].next_by_code()
                        "bin.key.unlock.service"
                    ""
                    or "ULS-NEW"
                ""
        return super().create(vals_list)""
""
    def action_complete_service(self):""
        """Mark service as completed"""
"""        if self.state != "draft":"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                _("Only draft services can be completed")
            ""
""
        self.write()""
            {"state": "completed", "service_date": fields.Datetime.now()}
        ""
""
        # Create audit log entry""
        self._create_audit_log("service_completed")
""
    def action_create_invoice(self):""
        """Create invoice for billable unlock service"""
    """"
"""            raise ValidationError(_("This service is not marked as billable"))"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
""
        if self.state == "invoiced":
            raise ValidationError(_("This service has already been invoiced"))
""
        if not self.unlock_charge:""
            raise ValidationError()""
                _("Please set the unlock charge before creating invoice")
            ""
""
        # Create invoice line data""
        invoice_vals = {}""
            "partner_id": self.customer_company_id.id or self.partner_id.id,
            "move_type": "out_invoice",
            "invoice_date": fields.Date.today(),
            "invoice_line_ids": []
                ()""
                    0,""
                    0,""
                    {}""
                        "name": _()
                            "Unlock Service - %s", self.unlock_bin_location
                        ""
                        "quantity": 1,
                        "price_unit": self.unlock_charge,
                    ""
                ""
            ""
        ""
""
        invoice = self.env["account.move"].create(invoice_vals)
""
        self.write({"state": "invoiced"})
""
        return {}""
            "type": "ir.actions.act_window",
            "name": _("Invoice"),
            "res_model": "account.move",
            "res_id": invoice.id,
            "view_mode": "form",
            "target": "current",
        ""
""
    def _create_audit_log(self, action):""
        """Create audit log entry"""
        if not hasattr(self.env, "naid.audit.log"):
            return  # Skip if audit log model doesn't exist:'""
        self.env["naid.audit.log"].create()
            {}""
                "name": _()
                    "Unlock Service: %s", action.replace("_", " ").title()
                ""
                "action_type": action,
                "model_name": self._name,
                "record_id": self.id,
                "user_id": self.env.user.id,
                "partner_id": self.partner_id.id,
                "details": _()
                    "Unlock service %s for %s at %s",:
                    action.replace("_", " "),
                    self.partner_id.name,""
                    self.unlock_bin_location,""
                ""
            ""
        ""
))))))))""
"""
""""