# -*- coding: utf-8 -*-
"""
Partner Bin Key Management - Simple Key Tracking
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class PartnerBinKey(models.Model):
    """
    Partner Bin Key Management
    Simple tracking of who has which generic physical keys
    """

    _name = "partner.bin.key"
    _description = "Partner Bin Key Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Key ID", required=True, tracking=True)
    description = fields.Text(string="Description")
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
    )
    user_id = fields.Many2one(
        "res.users",
        string="Key Manager",
        default=lambda self: self.env.user,
        tracking=True,
    )

    # ==========================================
    # KEY ASSIGNMENT
    # ==========================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Assigned Customer",  # Changed to avoid conflict with customer field
        required=True,
        tracking=True,
        domain=[("is_company", "=", True)],
    )
    assigned_to_contact = fields.Many2one(
        "res.partner",
        string="Assigned To",
        domain=[("is_company", "=", False)],
        tracking=True,
    )

    # ==========================================
    # BASIC STATUS
    # ==========================================
    state = fields.Selection(
        [
            ("available", "Available"),
            ("assigned", "Assigned"),
            ("lost", "Lost"),
            ("returned", "Returned"),
        ],
        string="Key Status",  # Changed to avoid conflict with status field
        default="available",
        tracking=True,
        required=True,
    )

    # ==========================================
    # TRACKING DATES
    # ==========================================
    assignment_date = fields.Date(string="Assignment Date", tracking=True)
    return_date = fields.Date(string="Return Date", tracking=True)

    # ==========================================
    # NOTES
    # ==========================================
    notes = fields.Text(string="Notes", tracking=True)
    action_issue_new_key = fields.Char(string="Action Issue New Key")
    action_report_lost_key = fields.Char(string="Action Report Lost Key")
    action_return_key = fields.Char(string="Action Return Key")
    action_view_active_key = fields.Char(string="Action View Active Key")
    action_view_bin_keys = fields.Char(string="Action View Bin Keys")
    action_view_unlock_services = fields.Char(string="Action View Unlock Services")
    active_bin_key_ids = fields.One2many(
        "bin.key.management",
        "partner_bin_key_id",
        string="Active Bin Keys",
        domain=[("active", "=", True)],
    )
    active_bin_key_count = fields.Integer(
        string="Active Bin Key Count",
        compute="_compute_active_bin_key_count",
        store=True,
    )
    billable = fields.Boolean(string="Billable", default=False)
    bin_key_history_ids = fields.One2many(
        "bin.key.history", "partner_bin_key_id", string="Bin Key History Ids"
    )
    bin_location = fields.Char(string="Bin Location")
    binding_model_id = fields.Many2one("ir.model", string="Binding Model Id")
    binding_view_types = fields.Char(string="Binding View Types")
    button_box = fields.Char(string="Button Box")
    category_id = fields.Many2one("res.partner.category", string="Category Id")
    charge_amount = fields.Float(string="Charge Amount", digits=(12, 2))
    context = fields.Char(string="Context")
    country_id = fields.Many2one("res.country", string="Country Id")
    emergency_contact = fields.Char(string="Emergency Contact")
    emergency_contacts = fields.Char(string="Emergency Contacts")
    has_bin_key = fields.Char(string="Has Bin Key")
    invoice_created = fields.Char(string="Invoice Created")
    is_emergency_key_contact = fields.Char(string="Is Emergency Key Contact")
    issue_date = fields.Date(string="Issue Date")
    issue_location = fields.Char(string="Issue Location")
    key_issue_date = fields.Date(string="Key Issue Date")
    key_number = fields.Char(string="Key Number")
    no_bin_key = fields.Char(string="No Bin Key")
    res_model = fields.Char(string="Res Model")
    service_date = fields.Date(string="Service Date")
    service_number = fields.Char(string="Service Number")
    status = fields.Selection(
        [("new", "New"), ("in_progress", "In Progress"), ("completed", "Completed")],
        string="Service Status",  # Changed to avoid conflict with state field
        default="new",
    )
    target = fields.Char(string="Target")
    total_bin_keys_issued = fields.Char(string="Total Bin Keys Issued")
    total_unlock_charges = fields.Char(string="Total Unlock Charges")
    unlock_reason = fields.Char(string="Unlock Reason")
    unlock_service_count = fields.Integer(
        string="Unlock Service Count",
        compute="_compute_unlock_service_count",
        store=True,
    )
    unlock_service_history_ids = fields.One2many(
        "unlock.service.history",
        "partner_bin_key_id",
        string="Unlock Service History Ids",
    )
    view_mode = fields.Char(string="View Mode")

    @api.depends("active_bin_key_ids")
    def _compute_active_bin_key_count(self):
        for record in self:
            record.active_bin_key_count = len(record.active_bin_key_ids)

    @api.depends("unlock_service_history_ids")
    def _compute_unlock_service_count(self):
        for record in self:
            record.unlock_service_count = len(record.unlock_service_history_ids)

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_assign_key(self):
        """Assign key to contact"""
        self.ensure_one()
        if self.state != "available":
            raise UserError(_("Only available keys can be assigned"))

        if not self.assigned_to_contact:
            raise UserError(_("Contact must be specified for assignment"))

        self.write({"state": "assigned", "assignment_date": fields.Date.today()})

        self.message_post(body=_("Key assigned to %s") % self.assigned_to_contact.name)

    def action_return_key(self):
        """Return key"""
        self.ensure_one()
        if self.state != "assigned":
            raise UserError(_("Only assigned keys can be returned"))

        self.write({"state": "returned", "return_date": fields.Date.today()})

        self.message_post(body=_("Key returned by %s") % self.assigned_to_contact.name)

    def action_report_lost(self):
        """Report key as lost"""
        self.ensure_one()
        self.write({"state": "lost"})
        self.message_post(body=_("Key reported as lost"))

    def action_make_available(self):
        """Make key available again"""
        self.ensure_one()
        self.write(
            {
                "state": "available",
                "assigned_to_contact": False,
                "assignment_date": False,
                "return_date": False,
            }
        )
        self.message_post(body=_("Key made available"))

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence number if needed"""
        for vals in vals_list:
            if not vals.get("name"):
                vals["name"] = self.env["ir.sequence"].next_by_code(
                    "partner.bin.key"
                ) or _("New Key")
        return super().create(vals_list)
