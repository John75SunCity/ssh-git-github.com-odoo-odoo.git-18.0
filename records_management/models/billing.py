# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class Billing(models.Model):
    _name = "records.billing"
    _description = "General Billing Model"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "invoice_date desc"

    # Phase 1: Explicit Activity Field (1 field)
