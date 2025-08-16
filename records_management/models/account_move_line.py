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

    # NOTE: This Many2one field is needed for the One2many relationship from work_order_coordinator
    # The Reference field above handles the polymorphic relationships to different work order types
    work_order_coordinator_id = fields.Many2one(
        "work.order.coordinator",
        string="Work Order Coordinator",
        help="Coordinator for consolidated billing"
    )

    # ============================================================================
    # RECORDS MANAGEMENT INTEGRATION FIELDS
    # ============================================================================
    records_related = fields.Boolean(
        string="Records Related",
        default=False,
        help="Indicates if this invoice line is related to records management services"
    )

    records_service_type = fields.Selection([
        ("storage", "Storage"),
        ("retrieval", "Retrieval"),
        ("destruction", "Destruction")
    ], string="Records Service Type", help="Type of records management service")

    container_count = fields.Integer(
        string="Container Count",
        help="Number of containers involved in this service"
    )

    shredding_weight = fields.Float(
        string="Shredding Weight (lbs)",
        digits=(8,2),
        help="Weight of materials shredded"
    )

    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        help="Related pickup request"
    )

    destruction_service_id = fields.Many2one(
        "shredding.service",
        string="Destruction Service",
        help="Related destruction service"
    )

    storage_location_id = fields.Many2one(
        "records.location",
        string="Storage Location",
        help="Storage location for records"
    )

    naid_audit_required = fields.Boolean(
        string="NAID Audit Required",
        default=False,
        help="Indicates if NAID audit trail is required"
    )
