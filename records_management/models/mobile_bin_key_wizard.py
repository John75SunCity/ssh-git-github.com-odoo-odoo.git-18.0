# -*- coding: utf-8 -*-
"""
Mobile Bin Key Management Wizard
"""

from odoo import models, fields, _


class MobileBinKeyWizard(models.Model):
    """
    Mobile Bin Key Management Wizard
    """

    _name = "mobile.bin.key.wizard"
    _description = "Mobile Bin Key Management Wizard"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"

    # Core fields
    name = fields.Char(string="Name", required=True, tracking=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user)
    active = fields.Boolean(default=True)

    # Basic state management
    state = fields.Selection(
        [("draft", "Draft"), ("confirmed", "Confirmed"), ("done", "Done")],
        string="State",
        default="draft",
        tracking=True,
    )

    # Common fields
    description = fields.Text()
    notes = fields.Text()
    date = fields.Datetime(string="Date", default=fields.Datetime.now)
    action_execute = fields.Char(string="Action Execute")
    action_type = fields.Selection(
        [
            ("unlock", "Unlock Bin"),
            ("lock", "Lock Bin"),
            ("inspect", "Inspect Contents"),
            ("relocate", "Relocate Bin"),
            ("service", "Service Request"),
            ("quick_lookup", "Quick Lookup"),
        ],
        string="Action Type",
        default="unlock",
    )
    billable = fields.Boolean(string="Billable", default=False)
    bin_locations = fields.Char(string="Bin Locations")
    code = fields.Char(string="Code")
    contact_email = fields.Char(string="Contact Email")
    partner_id = fields.Many2one("res.partner", string="Partner")
    contact_mobile = fields.Char(string="Contact Mobile")
    contact_name = fields.Char(string="Contact Name")
    contact_phone = fields.Char(string="Contact Phone")
    contact_title = fields.Char(string="Contact Title")
    context = fields.Char(string="Context")
    create_new_contact = fields.Boolean(string="Create New Contact", default=False)
    customer_company_id = fields.Many2one(
        "res.partner", string="Customer Company", domain=[("is_company", "=", True)]
    )
    emergency_contact = fields.Char(string="Emergency Contact")
    issue_location = fields.Char(string="Issue Location")
    items_retrieved = fields.Char(string="Items Retrieved")
    key_lookup_results = fields.Char(string="Key Lookup Results")
    key_notes = fields.Char(string="Key Notes")
    model_id = fields.Many2one("ir.model", string="Model Id")
    photo_ids = fields.One2many(
        "mobile.photo", "mobile_bin_key_wizard_id", string="Photo Ids"
    )
    res_model = fields.Char(string="Res Model")
    service_notes = fields.Char(string="Service Notes")
    show_contact_creation = fields.Char(string="Show Contact Creation")
    show_key_assignment = fields.Char(string="Show Key Assignment")
    show_lookup_results = fields.Char(string="Show Lookup Results")
    show_unlock_service = fields.Char(string="Show Unlock Service")
    target = fields.Char(string="Target")
    unlock_bin_location = fields.Char(string="Unlock Bin Location")
    unlock_charge = fields.Char(string="Unlock Charge")
    unlock_reason = fields.Char(string="Unlock Reason")
    unlock_reason_description = fields.Char(string="Unlock Reason Description")
    view_mode = fields.Char(string="View Mode")
    created_date = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    sequence = fields.Integer(string="Sequence", default=10)
    updated_date = fields.Datetime(string="Updated Date", default=fields.Datetime.now)

    # Mail Thread Framework Fields
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the record by updating its workflow state to 'confirmed'."""
        self.write({"state": "confirmed"})

    def action_done(self):
        """Mark the record as done."""
        self.write({"state": "done"})

    def action_execute_wizard(self):
        """
        Execute the mobile bin key action.

        For 'quick_lookup', posts a message and refreshes the form view.
        For other action types, marks the record as done, posts a message, and closes the window.
        """
        self.ensure_one()
        action_type = self.action_type or "quick_lookup"
        if action_type == "quick_lookup":
            self.message_post(body=_("Lookup data refreshed"))
            return {
                "type": "ir.actions.act_window",
                "res_model": "mobile.bin.key.wizard",
                "res_id": self.id,
                "view_mode": "form",
                "target": "new",
            }
        else:
            self.write({"state": "done"})
            self.message_post(body=_("Mobile bin key action executed"))
            return {"type": "ir.actions.act_window_close"}

    def action_type_window(self):
        """
        Open a window to select or view the action type for the mobile bin key wizard.
        """
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Type"),
            "res_model": "mobile.bin.key.wizard",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
