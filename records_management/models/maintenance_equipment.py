import logging

from dateutil.relativedelta import relativedelta  # type: ignore

from odoo import _, api, fields, models

# Removed deprecated import of dp; use digits='Product Price' directly in fields

_logger = logging.getLogger(__name__)


class MaintenanceEquipment(models.Model):
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
    parts_cost = fields.Float(string="Parts Cost", digits="Product Price")
    labor_cost = fields.Float(string="Labor Cost", digits="Product Price")
    external_cost = fields.Float(string="External Service Cost", digits="Product Price")
    total_maintenance_cost = fields.Float(
        string="Total Maintenance Cost",
        compute="_compute_total_cost",
        store=True,
        digits="Product Price",
    )

    compliance_notes = fields.Text(string='Compliance Notes')

    warranty_expiry_date = fields.Date(string="Warranty Expiry Date")
    is_under_warranty = fields.Boolean(string="Under Warranty", compute="_compute_is_under_warranty", store=True)

    # Additional fields needed for destruction certificate templates
    particle_size = fields.Float(
        string='Particle Size (mm)',
        help="Particle size output in millimeters for destruction compliance"
    )

    # Relationship with shredding services
    shredding_service_ids = fields.One2many(
        'shredding.service',
        'equipment_id',
        string='Shredding Services',
        help="Services using this equipment"
    )

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
        for equipment in self:
            if equipment.last_calibration_date and equipment.maintenance_frequency:
                # Updated to use relativedelta for proper date calculations
                frequency_map = {
                    "daily": relativedelta(days=1),
                    "weekly": relativedelta(weeks=1),
                    "monthly": relativedelta(months=1),
                    "quarterly": relativedelta(months=3),
                    "yearly": relativedelta(years=1),
                }
                equipment.next_calibration_date = equipment.last_calibration_date + frequency_map.get(
                    equipment.maintenance_frequency, relativedelta()
                )
            else:
                equipment.next_calibration_date = False

    @api.depends("warranty_expiry_date")
    def _compute_is_under_warranty(self):
        for equipment in self:
            equipment.is_under_warranty = bool(
                equipment.warranty_expiry_date and equipment.warranty_expiry_date >= fields.Date.today()
            )

    # ============================================================================
    # CRON METHODS
    # ============================================================================
    def _check_calibration_due(self):  # Renamed to follow Odoo naming conventions
        """Cron method to check for equipment that needs calibration"""
        today = fields.Date.today()
        overdue_equipment = self.search([
            ('calibration_required', '=', True),
            ('next_calibration_date', '<=', today)
        ])
        _logger.info(_('Found %s equipment items requiring calibration') % len(overdue_equipment))

        for equipment in overdue_equipment:
            maintenance_request = self.env["maintenance.request"].create(
                {
                    "name": _("Calibration Required: %s", equipment.name),
                    "equipment_id": equipment.id,
                    "request_date": fields.Date.today(),
                    "maintenance_type": "preventive",
                    "priority": "1",
                    "description": _(
                        "Equipment %s requires calibration. Last calibration: %s",
                        equipment.name,
                        equipment.last_calibration_date or _("Never"),
                    ),
                }
            )

            activity_type = self.env.ref("mail.mail_activity_data_todo", raise_if_not_found=False)
            if activity_type:
                self.env["mail.activity"].create(
                    {
                        "res_model": "maintenance.request",
                        "res_id": maintenance_request.id,
                        "note": _("Equipment %s calibration is overdue. Please schedule calibration.", equipment.name),
                        "summary": _("Equipment Calibration Overdue"),
                        "user_id": (
                            equipment.technician_user_id.id if equipment.technician_user_id else self.env.user.id
                        ),
                        "date_deadline": fields.Date.today(),
                    }
                )

            if equipment.maintenance_team_id.partner_id.email:
                equipment.message_post(
                    body=_("Equipment %s requires immediate calibration. Maintenance request created.", equipment.name),
                    subject=_("Calibration Overdue: %s", equipment.name),
                    message_type="email",
                )

            _logger.info(
                _(
                    "Created maintenance request ID %s (%s) for overdue equipment %s",
                    maintenance_request.id,
                    maintenance_request.name,
                    equipment.name,
                )
            )
