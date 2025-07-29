# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class CustomerRateProfile(models.Model):
    _name = "customer.rate.profile"
    _description = "Customer Rate Profile"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name"
    _rec_name = "name"

    name = fields.Char(
        string="Profile Name", compute="_compute_name", store=True, readonly=False
    )
    partner_id = fields.Many2one(
        "res.partner", string="Customer", required=True, ondelete="cascade"
    )
    active = fields.Boolean(default=True)

    profile_type = fields.Selection(
        [
            ("general", "General"),
            ("service_specific", "Service Specific"),
            ("promotional", "Promotional"),
        ],
        string="Profile Type",
        default="general",
        required=True,
        tracking=True,
        help="Defines the scope of the rate profile. General applies broadly, Service Specific to certain tasks, and Promotional for temporary rates.",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        required=True,
        default=lambda self: self.env.company,
    )
    user_id = fields.Many2one(
        "res.users", string="Responsible User", default=lambda self: self.env.user
    )
    state = fields.Selection(
        [("draft", "Draft"), ("active", "Active"), ("archived", "Archived")],
        string="Status",
        default="draft",
        tracking=True,
    )

    @api.depends("partner_id", "profile_type")
    def _compute_name(self):
        for record in self:
            if record.partner_id:
                name_parts = [record.partner_id.name]
                if record.profile_type:
                    name_parts.append(record.profile_type.title())
                record.name = " - ".join(name_parts)
            else:
                record.name = "New Rate Profile"
