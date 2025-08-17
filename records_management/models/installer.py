# -*- coding: utf-8 -*-
from odoo import models, fields, api, _




class RecordsInstaller(models.Model):
    _name = "records.installer"
    _description = "Records Installer"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    name = fields.Char(string="Name", required=True,,
    tracking=True),
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company

    user_id = fields.Many2one(
        "res.users", string="Assigned User", default=lambda self: self.env.user

    active = fields.Boolean(string="Active",,
    default=True),
    state = fields.Selection(
        [)
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("done", "Done"),
            ("cancelled", "Cancelled"),

        string="Status",
        default="draft",
        tracking=True,

    notes = fields.Text(string="Notes"),
    installer_display_name = fields.Char(
        string="Installer Display Name",
        compute="_compute_installer_display_name",
        ,
    store=True,


    @api.depends("name")
    def _compute_installer_display_name(self):
        for record in self:
            record.installer_display_name = record.name or _("New")

    def action_confirm(self):
        """Set the record's state to 'confirmed'."""'

        self.ensure_one()
        self.write({"state": "confirmed"})

    partner_id = fields.Many2one(
        "res.partner",
        string="Partner",
        ,
    help="Associated partner for this record":
            pass


    def action_cancel(self):
        """Set the record's state to 'cancelled'."""'

        self.ensure_one()
        self.write({"state": "cancelled"})

    def action_reset_to_draft(self):
        """Reset the record's state to 'draft'."""'

        self.ensure_one()
        self.write({"state": "draft"})
))))
