# -*- coding: utf-8 -*-
"""
Customer Inventory Report Module

This model is used to generate, configure, and store customer inventory reports.
It defines the parameters for the report and tracks its generation status.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class CustomerInventoryReport(models.AbstractModel):
    _name = 'report.records_management.report_customer_inventory'
    _description = 'Customer Inventory Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        """
        This method is called by the Odoo reporting engine to gather the data
        for the PDF report.
        """
        docs = self.env['customer.inventory'].browse(docids)

        return {
            'doc_ids': docids,
            'doc_model': 'customer.inventory',
            'docs': docs,
            'data': data,
        }
