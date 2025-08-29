# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NAIDTrainingRequirement(models.Model):
    _name = 'naid.training.requirement'
    _description = 'NAID Training Requirement'
    _order = 'training_type, duration_hours'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Training Name',
        required=True,
        help='Name of the training requirement'
    )
    training_type = fields.Selection([
        ('basic', 'Basic NAID Training'),
        ('advanced', 'Advanced NAID Training'),
        ('supervisor', 'Supervisor Training'),
        ('equipment', 'Equipment Operation'),
        ('security', 'Security Procedures'),
        ('compliance', 'Compliance Training')
    ], string='Training Type', required=True, default='basic')

    # Training Details
    required_for_roles = fields.Text(
        string='Required for Roles',
        help='Description of which roles or positions require this training'
    )
    duration_hours = fields.Float(
        string='Duration (Hours)',
        required=True,
        default=4.0,
        help='Duration of the training in hours'
    )
    renewal_frequency_months = fields.Integer(
        string='Renewal Frequency (Months)',
        required=True,
        default=24,
        help='How often this training must be renewed in months'
    )
    topics = fields.Text(
        string='Training Topics',
        help='List of topics covered in this training'
    )

    # Active status
    active = fields.Boolean(string='Active', default=True)

    @api.depends('name', 'training_type')
    def _compute_display_name(self):
        for record in self:
            if record.training_type and record.name:
                training_type_display = dict(record._fields['training_type'].selection).get(record.training_type, record.training_type)
                record.display_name = f"{record.name} ({training_type_display})"
            else:
                record.display_name = record.name or 'New Training Requirement'
