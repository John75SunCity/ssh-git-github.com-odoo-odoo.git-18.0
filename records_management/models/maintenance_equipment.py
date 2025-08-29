import logging
from odoo import models, fields, api, _

class MaintenanceEquipment(models.Model):
    _name = 'maintenance.equipment'
    _inherit = 'maintenance.equipment'
    _description = 'Maintenance Equipment Management'

    # ============================================================================
    # FIELDS
    # ============================================================================
    shredding_capacity_per_hour = fields.Float(string='Shredding Capacity (lbs/hour)')
    security_level = fields.Selection([
        ('p1', 'P-1'), ('p2', 'P-2'), ('p3', 'P-3'),
        ('p4', 'P-4'), ('p5', 'P-5'), ('p6', 'P-6'), ('p7', 'P-7')
    ], string='Security Level (DIN 66399)')

    location_id = fields.Many2one('records.location', string='Physical Location')

    # NAID Compliance
    naid_certification_date = fields.Date(string='NAID Certification Date')
    naid_certification_expiry = fields.Date(string='NAID Certification Expiry')

    # Calibration
    calibration_required = fields.Boolean(string='Requires Calibration', default=False)
    last_calibration_date = fields.Date(string='Last Calibration Date')
    next_calibration_date = fields.Date(string='Next Calibration Date', compute='_compute_next_calibration_date', store=True)
    maintenance_frequency = fields.Selection([
        ('daily', 'Daily'), ('weekly', 'Weekly'), ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'), ('yearly', 'Yearly')
    ], string='Maintenance Frequency')

    # Costing
    parts_cost = fields.Float(string='Parts Cost', digits='Product Price')
    labor_cost = fields.Float(string='Labor Cost', digits='Product Price')
    external_cost = fields.Float(string='External Service Cost', digits='Product Price')
    total_maintenance_cost = fields.Float(string='Total Maintenance Cost', compute='_compute_total_cost', store=True, digits='Product Price')

    compliance_notes = fields.Text(string='Compliance Notes')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('parts_cost', 'labor_cost', 'external_cost')
    def _compute_total_cost(self):
        for equipment in self:
            equipment.total_maintenance_cost = (
                (equipment.parts_cost or 0.0) +
                (equipment.labor_cost or 0.0) +
                (equipment.external_cost or 0.0)
            )

    @api.depends('last_calibration_date', 'maintenance_frequency')
    def _compute_next_calibration_date(self):
        # This is a placeholder for more complex date logic
        for equipment in self:
            if equipment.last_calibration_date and equipment.maintenance_frequency:
                # Simple example: add 30 days for monthly
                # A real implementation would use dateutil.relativedelta
                equipment.next_calibration_date = equipment.last_calibration_date + fields.date_utils.relativedelta(days=30)
            else:
                equipment.next_calibration_date = False

    # ============================================================================
    # CRON METHODS
    # ============================================================================
    def check_calibration_due(self):
        """Cron method to check for equipment that needs calibration"""
        today = fields.Date.today()
        overdue_equipment = self.search([
            ('calibration_required', '=', True),
            ('next_calibration_date', '<=', today)
        ])

        if overdue_equipment:
            # Log or send notifications for overdue calibrations
            _logger = logging.getLogger(__name__)
            _logger.info("Found %s equipment items requiring calibration", len(overdue_equipment))

            # TODO: Add notification logic here
            # For example, create maintenance requests or send emails

        return True

