# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class LegalCitation(models.Model):
    """
    Legal Citation - Laws, regulations, codes that justify retention policies
    
    "Cites or describes the laws, regulations, code, or rules that justify 
    the retention policy. The retention information for a record series may 
    reference one or more legal citations."
    
    Examples:
    - CAC 001: Personnel & Health Records, Title 22, California Administrative Code, 70723(c), California
    - 29 CFR 1910.1020: OSHA Access to Employee Exposure and Medical Records
    - IRS Revenue Procedure 98-25: Records retention for tax purposes
    - HIPAA 164.530(j): Medical records retention requirements
    - SOX Section 802: Document retention for public companies
    """
    _name = 'legal.citation'
    _description = 'Legal Citation'
    _order = 'code, title'

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================
    code = fields.Char(
        string='Citation Code',
        required=True,
        help='Citation code or reference number (e.g., "CAC 001", "29 CFR 1910.1020", "SOX-802")'
    )
    title = fields.Char(
        string='Title',
        required=True,
        help='Descriptive title for this legal citation'
    )

    # ============================================================================
    # LEGAL DETAILS
    # ============================================================================
    law_act_code = fields.Char(
        string='Law/Act Code',
        help='The law or act code that applies (e.g., "Title 22", "29 CFR", "HIPAA")'
    )
    law_act_code_title = fields.Char(
        string='Law/Act Code Title',
        help='Full title of the law or act code'
    )
    section = fields.Char(
        string='Section',
        help='Applicable section of the law or act code (e.g., "70723(c)", "1910.1020", "164.530(j)")'
    )
    jurisdiction = fields.Char(
        string='Jurisdiction',
        help='Jurisdiction for this legal citation (e.g., "California", "Federal", "New York")'
    )

    # ============================================================================
    # CATEGORIZATION
    # ============================================================================
    legal_citation_type_id = fields.Many2one(
        comodel_name='legal.citation.type',
        string='Citation Type',
        required=True,
        help='Type of legal citation (Federal, State, County, City, etc.)'
    )

    # ============================================================================
    # RETENTION REQUIREMENTS
    # ============================================================================
    retention_value = fields.Integer(
        string='Retention Period',
        help='Numerical value for retention requirement (e.g., 7 for 7 years)'
    )
    retention_unit = fields.Selection(
        selection=[
            ('day', 'Day(s)'),
            ('week', 'Week(s)'),
            ('month', 'Month(s)'),
            ('year', 'Year(s)'),
            ('permanent', 'Permanent')
        ],
        string='Retention Unit',
        default='year',
        help='Unit of time for retention period'
    )

    # ============================================================================
    # DESCRIPTION & NOTES
    # ============================================================================
    description = fields.Text(
        string='Description',
        help='Detailed description of this legal citation and why it matters'
    )

    # ============================================================================
    # SYSTEM FIELDS
    # ============================================================================
    active = fields.Boolean(
        default=True,
        help='Inactive citations are hidden but retain historical data'
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('code', 'title')
    def _compute_display_name(self):
        for citation in self:
            if citation.code and citation.title:
                citation.display_name = "%s - %s" % (citation.code, citation.title)
            elif citation.code:
                citation.display_name = citation.code
            else:
                citation.display_name = citation.title or _('New Citation')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('code_unique', 'unique(code)', 'Citation code must be unique!'),
    ]

    @api.constrains('retention_value', 'retention_unit')
    def _check_retention_value(self):
        for citation in self:
            if citation.retention_unit != 'permanent' and citation.retention_value:
                if citation.retention_value < 0:
                    raise ValidationError(_('Retention value must be positive!'))
