# -*- coding: utf-8 -*-
"""
Mobile Dashboard Widget Category Model

This model categorizes dashboard widgets for better organization and management.
Provides a hierarchical structure for mobile dashboard widget classification.
"""

from odoo import models, fields


class MobileDashboardWidgetCategory(models.Model):
    """
    Mobile Dashboard Widget Category Model

    Categorizes dashboard widgets for better organization.
    """

    _name = 'mobile.dashboard.widget.category'
    _description = 'Mobile Dashboard Widget Category'

    name = fields.Char(
        string='Category Name',
        required=True,
        help='Name of the widget category'
    )

    technical_name = fields.Char(
        string='Technical Name',
        required=True,
        help='Technical identifier for the category'
    )

    description = fields.Text(
        string='Description',
        help='Description of this category'
    )

    icon = fields.Char(
        string='Icon',
        help='Icon for the category'
    )

    is_active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this category is active'
    )

    sort_order = fields.Integer(
        string='Sort Order',
        default=10,
        help='Order in which categories appear'
    )

    # Relationships
    widget_ids = fields.One2many(
        'mobile.dashboard.widget',
        'category_id',
        string='Widgets',
        help='Widgets in this category'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        help='Company this category belongs to'
    )

    # Constraints
    _sql_constraints = [
        ('unique_name_company', 'unique(name, company_id)',
         'Category name must be unique per company'),
        ('unique_technical_name', 'unique(technical_name, company_id)',
         'Technical name must be unique per company'),
    ]
