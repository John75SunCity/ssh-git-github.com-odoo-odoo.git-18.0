# -*- coding: utf-8 -*-
"""
Portal Spreadsheet Template Column Model

Defines columns for spreadsheet templates used in portal import/export.
Each column specifies header text, field mapping, data type, and validation.

This model must be loaded BEFORE portal.spreadsheet.template (parent).
"""

from odoo import _, api, fields, models


class PortalSpreadsheetTemplateColumn(models.Model):
    _name = 'portal.spreadsheet.template.column'
    _description = 'Portal Spreadsheet Template Column'
    _order = 'sequence, id'

    template_id = fields.Many2one(
        comodel_name='portal.spreadsheet.template',
        string='Template',
        required=True,
        ondelete='cascade'
    )

    name = fields.Char(
        string='Column Header',
        required=True,
        help='The column header text that appears in the spreadsheet'
    )

    sequence = fields.Integer(default=10)

    field_name = fields.Char(
        string='Field Name',
        required=True,
        help='The technical field name for mapping during import'
    )

    required = fields.Boolean(
        string='Required',
        default=False,
        help='Mark this column as required (adds * to header)'
    )

    instruction = fields.Text(
        string='Instruction',
        help='Help text shown in the second row of the template'
    )

    sample_value = fields.Char(
        string='Sample Value',
        help='Example value shown in the third row of the template'
    )

    width = fields.Integer(
        string='Column Width',
        default=20,
        help='Column width in Excel (characters)'
    )

    data_type = fields.Selection([
        ('text', 'Text'),
        ('number', 'Number'),
        ('date', 'Date'),
        ('boolean', 'Yes/No'),
        ('selection', 'Selection'),
        ('relation', 'Related Record'),
    ], string='Data Type', default='text')

    selection_values = fields.Text(
        string='Selection Values',
        help='Comma-separated list of valid values for selection type'
    )

    relation_model = fields.Char(
        string='Related Model',
        help='Model name for relation type (e.g., res.partner)'
    )

    relation_field = fields.Char(
        string='Match Field',
        default='name',
        help='Field to match when looking up related records'
    )
