# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from dateutil.relativedelta import relativedelta
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CustomerInventoryReport(models.Model):
    """Model for customer inventory reports."""
    _name = 'customer.inventory.report'
    _description = 'Customer Inventory Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'report_date desc, customer_id'

    # Phase 1: Explicit Activity Field (1 field)