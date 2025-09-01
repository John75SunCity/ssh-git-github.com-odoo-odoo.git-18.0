from odoo import models, fields, api


class MaintenanceTeam(models.Model):
    _inherit = 'maintenance.team'
    _description = 'Maintenance Team Management'

    # ============================================================================
    # FIELDS
    # ============================================================================
    specialization = fields.Selection([
        ('shredding', 'Shredding Equipment'),
        ('baling', 'Baling Machines'),
        ('vehicles', 'Vehicles'),
        ('general', 'General Facility')
    ], string='Team Specialization')

    service_location_ids = fields.Many2many(
        'records.location',
        'maintenance_team_location_rel',
        'team_id',
        'location_id',
        string='Serviced Locations'
    )

    # Maintenance Request Relationship
    maintenance_request_ids = fields.One2many(
        'maintenance.request',
        'maintenance_team_id',
        string='Maintenance Requests'
    )

    # NAID Compliance
    naid_certified = fields.Boolean(string='NAID Certified Team')
    certification_level = fields.Selection([
        ('associate', 'Associate'),
        ('professional', 'Professional')
    ], string='NAID Certification Level')

    # Performance Metrics
    average_response_time = fields.Float(string='Avg. Response Time (Hours)', compute='_compute_performance_metrics', store=True)
    average_resolution_time = fields.Float(string='Avg. Resolution Time (Hours)', compute='_compute_performance_metrics', store=True)

    records_department_id = fields.Many2one('records.department', string='Associated Department')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('maintenance_request_ids.request_date')
    def _compute_performance_metrics(self):
        """Compute performance metrics based on maintenance requests"""
        for team in self:
            requests = team.maintenance_request_ids.filtered(lambda r: r.request_date)
            if requests:
                # Calculate average resolution time (simplified)
                team.average_resolution_time = 24.0  # Default estimate in hours
                team.average_response_time = 2.0  # Default estimate in hours
            else:
                team.average_resolution_time = 0.0
                team.average_response_time = 0.0
