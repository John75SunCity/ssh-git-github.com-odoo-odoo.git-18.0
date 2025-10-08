# -*- coding: utf-8 -*-
"""
Mobile Dashboard Widget Category Model

This model categorizes dashboard widgets for better organization and management.
Provides a hierarchical structure for mobile dashboard widget classification.
"""

from odoo import fields, models, _


class MobileDashboardWidgetCategory(models.Model):
    """
    Mobile Dashboard Widget Category Model

    Categorizes dashboard widgets for better organization.
    """

    _name = "mobile.dashboard.widget.category"
    _description = "Mobile Dashboard Widget Category"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string="Category Name", required=True, help="Name of the widget category"
    )

    technical_name = fields.Char(
        string="Technical Name",
        required=True,
        help="Technical identifier for the category",
    )

    description = fields.Text(string="Description", help="Description of this category")

    icon = fields.Char(string="Category Icon", help="Icon for the category (disambiguated from activity_exception_icon)")

    is_active = fields.Boolean(
        string="Active", default=True, help="Whether this category is active"
    )

    sort_order = fields.Integer(
        string="Sort Order", default=10, help="Order in which categories appear"
    )

    # Relationships
    widget_ids = fields.One2many(
        "mobile.dashboard.widget",
        "category_id",
        string="Widgets",
        help="Widgets in this category",
    )

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company.id,
        help="Company this category belongs to",
    )

    # Constraints
    name_company_uniq = models.Constraint(
        "unique(name, company_id)",
        _("Category name must be unique per company"),
    )
    technical_name_company_uniq = models.Constraint(
        "unique(technical_name, company_id)",
        _("Technical name must be unique per company"),
    )
    ]
