# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class RecordSeries(models.Model):
    """
    Record Series - Groups of identical or related records
    
    "Group of identical or related records that are normally used and filed as a unit. 
    Record Series may break down and be categorized along such lines as legal, payroll, 
    personnel, and contract depending on the organization. A record series can be assigned 
    to any item (container, filefolder, or tape) in the database.
    
    A Record Series Code is typically used as a control number/value for a specific 
    Record Series. For example: GS3011-156 – Audit Reports"
    
    Examples:
    - HR-PERS: Personnel Files
    - FIN-AUDT: Audit Reports
    - LEG-CNTR: Legal Contracts
    - MED-PTNT: Patient Medical Records
    - TAX-PYRL: Payroll Tax Records
    """
    _name = 'record.series'
    _description = 'Record Series'
    _order = 'code, name'

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================
    code = fields.Char(
        string='Series Code',
        required=True,
        help='Control number/code for this record series (e.g., "GS3011-156", "HR-PERS", "FIN-AUDT")'
    )
    name = fields.Char(
        string='Series Name',
        required=True,
        help='Descriptive name for this record series (e.g., "Audit Reports", "Personnel Files")'
    )
    description = fields.Text(
        string='Description',
        help='Detailed description of what records belong to this series'
    )

    # ============================================================================
    # RETENTION & LEGAL CITATIONS
    # ============================================================================
    legal_citation_ids = fields.Many2many(
        comodel_name='legal.citation',
        relation='record_series_legal_citation_rel',
        column1='series_id',
        column2='citation_id',
        string='Legal Citations',
        help='Legal citations that justify the retention policy for this record series. '
             'A record series may reference one or more legal citations.'
    )

    # ============================================================================
    # DISPOSITION
    # ============================================================================
    disposition_id = fields.Many2one(
        comodel_name='record.disposition',
        string='Disposition Method',
        help='How records in this series should be handled at end of retention period'
    )

    # ============================================================================
    # DEFAULT RETENTION (can be overridden by legal citations)
    # ============================================================================
    default_retention_value = fields.Integer(
        string='Default Retention Period',
        help='Default retention period for this series (can be overridden by legal citations)'
    )
    default_retention_unit = fields.Selection(
        selection=[
            ('day', 'Day(s)'),
            ('week', 'Week(s)'),
            ('month', 'Month(s)'),
            ('year', 'Year(s)'),
            ('permanent', 'Permanent')
        ],
        string='Retention Unit',
        default='year',
        help='Unit of time for default retention period'
    )

    # ============================================================================
    # CATEGORIZATION
    # ============================================================================
    category = fields.Selection(
        selection=[
            ('legal', 'Legal'),
            ('financial', 'Financial'),
            ('hr_personnel', 'HR/Personnel'),
            ('medical', 'Medical'),
            ('contracts', 'Contracts'),
            ('tax', 'Tax'),
            ('audit', 'Audit'),
            ('correspondence', 'Correspondence'),
            ('administrative', 'Administrative'),
            ('other', 'Other')
        ],
        string='Category',
        help='General category for this record series'
    )

    # ============================================================================
    # CUSTOMER RELATIONSHIP
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        help='Leave blank for company-wide series, or assign to specific customer for custom series'
    )
    department_id = fields.Many2one(
        comodel_name='records.department',
        string='Department',
        help='Department this record series belongs to (optional)'
    )

    # ============================================================================
    # SYSTEM FIELDS
    # ============================================================================
    active = fields.Boolean(
        default=True,
        help='Inactive series are hidden but retain historical data'
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True
    )

    @api.depends('code', 'name')
    def _compute_display_name(self):
        for series in self:
            if series.code and series.name:
                series.display_name = "%s - %s" % (series.code, series.name)
            elif series.code:
                series.display_name = series.code
            else:
                series.display_name = series.name or _('New Series')

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    _sql_constraints = [
        ('code_partner_unique', 'unique(code, partner_id)',
         'Record series code must be unique per customer!'),
    ]
