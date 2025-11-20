# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class LegalCitationType(models.Model):
    """
    Legal Citation Type - Categorizes legal citations
    
    Examples from O'Neil Stratus:
    - Federal (FED)
    - State (ST)
    - County (CO)
    - City (CI)
    
    Additional common types:
    - Industry Standard
    - Corporate Policy
    - Regulatory Body
    """
    _name = 'legal.citation.type'
    _description = 'Legal Citation Type'
    _order = 'sequence, name'
    
    name = fields.Char(
        string='Citation Type',
        required=True,
        help='Type of legal citation (Federal, State, County, City, etc.)'
    )
    code = fields.Char(
        string='Code',
        required=True,
        size=10,
        help='Short code for this citation type (e.g., FED, ST, CO, CI)'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of this citation type'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Display order in lists and forms'
    )
    active = fields.Boolean(
        default=True,
        help='Inactive types are hidden but retain historical data'
    )
    
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Citation type code must be unique!'),
    ]
