# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResPartner(models.Model):
    _inherit = ["res.partner", "mail.thread", "mail.activity.mixin"]

    # Add new fields here, for example:
    # is_records_customer = fields.Boolean(string="Records Customer", default=False)
