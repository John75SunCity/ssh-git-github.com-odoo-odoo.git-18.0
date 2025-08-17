# -*- coding: utf-8 -*-
# Records Promotional Discount Model

from odoo import api, fields, models




class RecordsPromotionalDiscount(models.Model):

        Represents promotional discounts applied to billing configurations.
    This model tracks discount campaigns, including their type (percentage or fixed), 
        value, validity period, usage limits, and associated billing configuration.
    Used to manage and apply promotional offers to customer invoices, ensuring
        accurate discount calculations and compliance with business rules.


    _name = "records.promotional.discount"
    _description = "Records Promotional Discount"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "config_id, start_date desc"

    config_id = fields.Many2one(
        "records.billing.config",
        string="Billing Config",
        required=True,
        ondelete="cascade",
    
    name = fields.Char(string="Promotion Name", required=True),
    promotion_code = fields.Char(string="Promotion Code"),
    discount_type = fields.Selection(
        [("percentage", "Percentage"), ("fixed", "Fixed Amount")], string="Discount Type",
        required=True,
    
    discount_value = fields.Float(
        string="Discount Value", digits=(10, 2), required=True
    
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
    
    start_date = fields.Date(string="Start Date", required=True),
    end_date = fields.Date(string="End Date", required=True),
    minimum_order = fields.Monetary(
        string="Minimum Order", currency_field="currency_id"
    
    maximum_discount = fields.Monetary(
        string="Maximum Discount", currency_field="currency_id"
    
    usage_limit = fields.Integer(string="Usage Limit"),
    times_used = fields.Integer(string="Times Used", default=0),
    active = fields.Boolean(string="Active", default=True)

        # Workflow state management
    state = fields.Selection([)]
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    
        help='Current status of the record'

