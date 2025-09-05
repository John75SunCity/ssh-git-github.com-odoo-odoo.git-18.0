# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NAIDCertificationLevel(models.Model):
    _name = 'naid.certification.level'
    _description = 'NAID Certification Level'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'level_code'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Level Name',
        required=True,
        help='Name of the NAID certification level'
    )
    level_code = fields.Char(
        string='Level Code',
        required=True,
        help='Code identifier for the certification level (e.g., NAID-1, NAID-2)'
    )
    security_level = fields.Selection([
        ('basic', 'Basic'),
        ('intermediate', 'Intermediate'),
        ('high', 'High Security'),
        ('top_secret', 'Top Secret')
    ], string='Security Level', required=True, default='basic')

    description = fields.Text(
        string='Description',
        help='Detailed description of the certification level requirements'
    )

    # Requirements
    particle_size_requirement = fields.Char(
        string='Particle Size Requirement',
        help='Required particle size for destruction (e.g., "10mm strips", "2mm cross-cut")'
    )
    witness_requirement = fields.Char(
        string='Witness Requirement',
        help='Number and type of witnesses required for destruction'
    )
    documentation_required = fields.Text(
        string='Documentation Required',
        help='Documentation requirements for this certification level'
    )

    # Active status
    active = fields.Boolean(string='Active', default=True)

    # Constraints
    _sql_constraints = [
        ('level_code_unique', 'unique(level_code)', 'Level code must be unique!'),
    ]

    @api.depends('name', 'level_code')
    def _compute_display_name(self):
        for record in self:
            if record.level_code and record.name:
                record.display_name = f"[{record.level_code}] {record.name}"
            else:
                record.display_name = record.name or record.level_code or 'New Certification Level'
