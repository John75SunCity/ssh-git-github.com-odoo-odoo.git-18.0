# -*- coding: utf-8 -*-
"""
Account Move Line Extensions for Work Order Billing Integration

Extends account.move.line model to link invoice lines to work orders.
"""

from odoo import models, fields


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    work_order_id = fields.Reference(
        selection=[
            ('container.retrieval.work.order', 'Container Retrieval'),
            ('file.retrieval.work.order', 'File Retrieval'),
            ('scan.retrieval.work.order', 'Scan Retrieval'),
            ('container.destruction.work.order', 'Container Destruction'),
            ('container.access.work.order', 'Container Access'),
        ],
        string='Related Work Order',
        help="Work order that generated this invoice line"
    )

    work_order_coordinator_id = fields.Many2one(
        "work.order.coordinator",
        string="Work Order Coordinator",
        help="Coordinator for consolidated billing"
    )
