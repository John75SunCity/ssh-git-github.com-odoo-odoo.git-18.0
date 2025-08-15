# -*- coding: utf-8 -*-
"""
Customer Inventory Report Line Model

Individual line items for customer inventory reports.
"""

from odoo import models, fields, api, _


class CustomerInventoryReportLine(models.Model):
    """Customer Inventory Report Line"""

    _name = "customer.inventory.report.line"
    _description = "Customer Inventory Report Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "report_id, container_id, document_type"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Line Description", 
        required=True,
        tracking=True
    )

    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        required=True
    )

    active = fields.Boolean(default=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    report_id = fields.Many2one(
        "customer.inventory.report",
        string="Inventory Report",
        required=True,
        ondelete="cascade",
        index=True
    )

    container_id = fields.Many2one(
        "records.container",
        string="Container",
        required=True
    )

    # ============================================================================
    # INVENTORY DETAILS
    # ============================================================================
    document_type = fields.Char(
        string="Document Type",
        help="Type of documents in container"
    )

    document_count = fields.Integer(
        string="Document Count",
        default=0,
        help="Number of documents"
    )

    storage_date = fields.Date(
        string="Storage Date",
        help="Date documents were stored"
    )

    location_code = fields.Char(
        string="Location Code",
        help="Storage location code"
    )

    # ============================================================================
    # FINANCIAL
    # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        related="company_id.currency_id",
        readonly=True
    )

    monthly_cost = fields.Monetary(
        string="Monthly Storage Cost",
        currency_field="currency_id",
        help="Monthly storage cost"
    )

    # Mail Thread Framework Fields
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
