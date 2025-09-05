# -*- coding: utf-8 -*-

from odoo import api, fields, models


class NAIDEquipmentStandard(models.Model):
    _name = 'naid.equipment.standard'
    _description = 'NAID Equipment Standard'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'equipment_type, name'
    _rec_name = 'name'

    # Basic Information
    name = fields.Char(
        string='Standard Name',
        required=True,
        help='Name of the equipment standard'
    )
    equipment_type = fields.Selection([
        ('shredder', 'Document Shredder'),
        ('baler', 'Paper Baler'),
        ('scanner', 'Document Scanner'),
        ('scale', 'Weighing Scale'),
        ('crusher', 'Hard Drive Crusher'),
        ('other', 'Other Equipment')
    ], string='Equipment Type', required=True, default='shredder')

    minimum_security_level = fields.Char(
        string='Minimum Security Level',
        help='Minimum NAID security level required (e.g., NAID-1, NAID-2)'
    )

    # Maintenance and Calibration
    calibration_frequency_days = fields.Integer(
        string='Calibration Frequency (Days)',
        default=30,
        help='How often equipment must be calibrated in days'
    )
    maintenance_requirements = fields.Text(
        string='Maintenance Requirements',
        help='Description of required maintenance activities'
    )
    performance_specifications = fields.Text(
        string='Performance Specifications',
        help='Technical specifications and performance requirements'
    )

    # Active status
    active = fields.Boolean(string='Active', default=True)

    @api.depends('name', 'equipment_type')
    def _compute_display_name(self):
        for record in self:
            if record.equipment_type and record.name:
                equipment_type_display = dict(record._fields['equipment_type'].selection).get(record.equipment_type, record.equipment_type)
                record.display_name = f"{record.name} ({equipment_type_display})"
            else:
                record.display_name = record.name or 'New Equipment Standard'
