# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    Partner Bin Key Management - Simple Key Tracking
    import logging
    from odoo import models, fields, api, _
    from odoo.exceptions import UserError, ValidationError
    _logger = logging.getLogger(__name__)
    class PartnerBinKey(models.Model):

        Partner Bin Key Management
    Simple tracking of who has which generic physical keys


    _name = "partner.bin.key"

"
    _description = "partner.bin.key"

"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "partner.bin.key"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Partner Bin Key Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"
""
        # ============================================================================""
    # CORE IDENTIFICATION FIELDS""
        # ============================================================================""
    name = fields.Char(string="Key ID", required=True, tracking=True,,
    index=True),""
    description = fields.Text(string="Description"),
    active = fields.Boolean(string="Active", default=True,,
    tracking=True),""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True,""
    ""
    user_id = fields.Many2one(""
        "res.users",
        string="Key Manager",
        default=lambda self: self.env.user,""
        tracking=True,""
    ""
""
        # ============================================================================""
    # KEY ASSIGNMENT FIELDS""
        # ============================================================================""
    partner_id = fields.Many2one(""
        "res.partner",
        string="Assigned Customer",
        required=True,""
        tracking=True,""
        ,""
    domain=[("is_company", "= """"
        """"res.partner","
        string="Assigned To",
        ,""
    domain=[("is_company", "= """"
"""            (""""available", "Available"),"
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
            ("assigned", "Assigned"),
            ("lost", "Lost"),
            ("returned", "Returned"),
        ""
        string="Key Status",
        default="available",
        tracking=True,""
        required=True,""
    ""
""
    status = fields.Selection(""
        [("new", "New"), ("in_progress", "In Progress"), ("completed", "Completed")), string="Service Status",
        default="new",
    ""
""
        # ============================================================================ """"
    # DATE FIELDS""""""
        # ============================================================================ """"
    assignment_date = fields.Date(string=""""Assignment Date",,"
    tracking=True),""
    return_date = fields.Date(string="Return Date",,
    tracking=True),""
    issue_date = fields.Date(string="Issue Date"),
    key_issue_date = fields.Date(string="Key Issue Date"),
    service_date = fields.Date(string="Service Date")
""
        # ============================================================================ """"
    # BUSINESS FIELDS""""""
        # ============================================================================ """"
    billable = fields.Boolean(string=""""Billable",,"
    default=False),""
    charge_amount = fields.Float(string="Charge Amount",,
    digits=(12, 2))""
    key_number = fields.Char(string="Key Number"),
    bin_location = fields.Char(string="Bin Location"),
    issue_location = fields.Char(string="Issue Location"),
    service_number = fields.Char(string="Service Number"),
    unlock_reason = fields.Char(string="Unlock Reason")
""
        # ============================================================================""
    # RELATIONSHIP FIELDS""
        # ============================================================================""
    active_bin_key_ids = fields.One2many(""
        "bin.key.management",
        "partner_bin_key_id",
        string="Active Bin Keys",
        ,""
    domain=[("active", "= """""
        """"bin.key.history", "partner_bin_key_id", string="Bin Key History""
    ""
    unlock_service_history_ids = fields.One2many(""
        "unlock.service.history", "partner_bin_key_id", string="Unlock Service History"
    ""
""
        # ============================================================================""
    # COMPUTED FIELDS""
        # ============================================================================""
    active_bin_key_count = fields.Integer(""
        string="Active Bin Key Count",
        compute="_compute_active_bin_key_count",
        store=True,""
    ""
    unlock_service_count = fields.Integer(""
        string="Unlock Service Count",
        compute="_compute_unlock_service_count",
        store=True,""
    ""
    density = fields.Float(string="Density",,
    compute="_compute_density"),
    total_items = fields.Integer(""
        string="Total Items", compute="_compute_total_items", store=True
    ""
""
        # ============================================================================ """"
    # REFERENCE FIELDS""""""
        # ============================================================================ """"
    category_id = fields.Many2one(""""res.partner.category",,"
    string="Category"),
    country_id = fields.Many2one("res.country",,
    string="Country"),
    binding_model_id = fields.Many2one("ir.model",,
    string="Binding Model")
""
        # ============================================================================ """"
    # TEXT AND NOTE FIELDS""""""
        # ============================================================================ """"
    notes = fields.Text(string=""""Notes",,"
    tracking=True),""
    emergency_contact = fields.Char(string="Emergency Contact"),
    emergency_contacts = fields.Char(string="Emergency Contacts")
""
        # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance):""
            pass""
    activity_ids = fields.One2many("mail.activity", "res_id",,
    string="Activities"),
    message_follower_ids = fields.One2many(""
        "mail.followers", "res_id", string="Followers"
    ""
    message_ids = fields.One2many("mail.message", "res_id",,
    string="Messages")
""
        # ============================================================================""
    # SEQUENCE FIELDS""
        # ============================================================================""
    sequence = fields.Integer(""
        string="Sequence", 
        default=10,""
        help="Order sequence for sorting":
    
    ,
    action_issue_new_key = fields.Char(string='Action Issue New Key'),
    action_report_lost_key = fields.Char(string='Action Report Lost Key'),
    action_return_key = fields.Char(string='Action Return Key'),
    action_view_active_key = fields.Char(string='Action View Active Key'),
    action_view_bin_keys = fields.Char(string='Action View Bin Keys'),
    action_view_unlock_services = fields.Char(string='Action View Unlock Services'),
    binding_view_types = fields.Char(string='Binding View Types'),
    button_box = fields.Char(string='Button Box'),
    context = fields.Char(string='Context'),
    customer = fields.Char(string='Customer'),
    has_bin_key = fields.Char(string='Has Bin Key'),
    invoice_created = fields.Char(string='Invoice Created'),
    is_emergency_key_contact = fields.Char(string='Is Emergency Key Contact'),
    no_bin_key = fields.Char(string='No Bin Key'),"
    res_model = fields.Char(string='Res Model'),"
    target = fields.Char(string='Target'),""
    total_bin_keys_issued = fields.Char(string='Total Bin Keys Issued'),""
    total_unlock_charges = fields.Char(string='Total Unlock Charges'),""
    view_mode = fields.Char(string='View Mode')""
""
    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies""
    def _compute_total_bin_keys_issued(self):""
        for record in self:""
            record.total_bin_keys_issued = sum(record.line_ids.mapped('amount'))""
""
    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies""
    def _compute_total_unlock_charges(self):""
        for record in self:""
            record.total_unlock_charges = sum(record.line_ids.mapped('amount'))""
""
    # ============================================================================ """"
        # COMPUTE METHODS""""""
    # ============================================================================ """"
    @api.depends(""""active_bin_key_ids")"
    def _compute_active_bin_key_count(self):""
        """Compute count of active bin keys"""
    """    @api.depends("unlock_service_history_ids")"
    def _compute_unlock_service_count(self):""
        """Compute count of unlock services"""
    """    @api.depends("weight", "weight_unit", "total_volume")"
    def _compute_density(self):""
        """Compute density of the bale"""
""""
""""
"""                if record.weight_unit == "lb":"
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
""""
""""
""""
                    weight_kg = record.weight * 0.453592""
                elif record.weight_unit == "ton":
                    weight_kg = record.weight * 1000""
""
                record.density = weight_kg / record.total_volume""
            else:""
                record.density = 0.0""
""
    @api.depends("inventory_item_ids")
    def _compute_total_items(self):""
        """Compute total number of items in inventory"""
""""
""""
"""    def action_assign_key(self):"
"""
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
        """Assign key to contact"""
"""        if self.state != "available":"
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
""""
""""
""""
""""
            raise UserError(_("Only available keys can be assigned"))
        if not self.assigned_to_contact:""
            raise UserError(_("Contact must be specified for assignment")):
        self.write({"state": "assigned", "assignment_date": fields.Date.today()})
        self.message_post(body=_("Key assigned to %s", self.assigned_to_contact.name))
""
    def action_return_key(self):""
        """Return key"""
"""        if self.state != "assigned":"
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
            raise UserError(_("Only assigned keys can be returned"))
""
        self.write({"state": "returned", "return_date": fields.Date.today()})
        self.message_post(body=_("Key returned by %s", self.assigned_to_contact.name))
""
    def action_report_lost(self):""
        """Report key as lost"""
"""        self.write({"state": "lost"})"
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
""""
""""
""""
""""
        self.message_post(body=_("Key reported as lost"))
""
    def action_make_available(self):""
        """Make key available again"""
""""
""""
"""                "state": "available","
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
                "assigned_to_contact": False,
                "assignment_date": False,
                "return_date": False,
            ""
        ""
        self.message_post(body=_("Key made available"))
""
    def action_issue_new_key(self):""
        """Issue new key to customer"""
""""
""""
"""            "type": "ir.actions.act_window","
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
""""
""""
            "name": _("Issue New Key"),
            "res_model": "bin.key.issue.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_partner_id": self.partner_id.id},
        ""
""
    def action_view_active_keys(self):""
        """View active bin keys"""
""""
""""
"""            "type": "ir.actions.act_window","
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
            "name": _("Active Bin Keys"),
            "res_model": "bin.key.management",
            "view_mode": "tree,form",
            "domain": [("partner_bin_key_id", "=", self.id), ("active", "= """""
    """"
        """"""View unlock service history""""
""""
""""
"""            "type": "ir.actions.act_window","
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
""""
""""
""""
            "name": _("Unlock Services"),
            "res_model": "unlock.service.history",
            "view_mode": "tree,form",
            "domain": [("partner_bin_key_id", "= """", self.id),"
        ""
""
    def action_view_key_history(self):""
        """"""View bin key history""""
""""
""""
"""            "type": "ir.actions.act_window","
"""
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
            "name": _("Key History"),
            "res_model": "bin.key.history",
            "view_mode": "tree,form",
            "domain": [("partner_bin_key_id", "= """""
""""
        """"""Override create to set sequence number if needed""":"
        for vals in vals_list:""
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code()
                    "partner.bin.key"
                ) or _("New Key"
        return super().create(vals_list)""
""
    def name_get(self):""
        """Custom name display"""
"""            name = record.name or _("New Key")"
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
""""
""""
""""
                name += _(" - %s", record.partner_id.name)
            if record.state:""
                state_dict = dict(record._fields["state"].selection)
                name += _(" (%s)", state_dict.get(record.state, ""))
            result.append((record.id, name))""
        return result""
""
    # ============================================================================""
        # VALIDATION METHODS""
    # ============================================================================""
    @api.constrains("assignment_date", "return_date")
    def _check_dates(self):""
        """Validate date consistency"""
""""
""""
"""                        "Assignment date cannot be after return date for record %s (ID: %s)""
"""
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
                    ) % (record.name or "Unknown", record.id
                    _logger.error(msg)""
                    raise ValidationError(msg)""
""
    @api.constrains("state", "assigned_to_contact")
    def _check_assignment(self):""
        """Validate assignment requirements"""
            if record.state == "assigned" and not record.assigned_to_contact:
                raise ValidationError()""
                    _("Assigned keys must have a contact specified (Key: %s, ID: %s)", (record.name), record.id)
                ""
""
    @api.constrains("charge_amount")
    def _check_charge_amount(self):""
        """Validate charge amount"""
""""
""""
"""                    "Charge amount cannot be negative for record %s (ID: %s)","
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
""""
""""
""""
                    record.name or "Unknown",
                    record.id,""
                ""
                _logger.error(msg)""
                raise ValidationError(msg)""
""
    @api.constrains("key_number")
    def _check_key_number(self):""
        """Validate unique key number per partner"""
""""
""""
"""                        ("key_number", "= """"
                        (""""partner_id", "= """"
                        (""""id", "!= """"
"""                        _(""""Key number %s already exists for customer %s", (record.key_number), record.partner_id.name):""
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
))))))))""
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
"""
"""