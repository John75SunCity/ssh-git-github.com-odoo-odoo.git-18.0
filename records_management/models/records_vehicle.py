from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsVehicleInheritance(models.Model):
    """
    Records Management Vehicle Extensions

    Inherits from fleet.vehicle to leverage Odoo's built-in fleet management:
    - Standard vehicle data (license plate, VIN, driver, model, etc.)
    - Maintenance scheduling and tracking
    - Odometer readings and fuel logs
    - Insurance and contract management

    Adds only records-specific business logic:
    - Container capacity tracking
    - NAID compliance status
    - Specialized vehicle types for records business
    """
    _inherit = 'fleet.vehicle'
    _description = 'Records Management Vehicle Extensions'

    # ============================================================================
    # RECORDS-SPECIFIC EXTENSIONS (Only what fleet.vehicle doesn't provide)
    # ============================================================================

    # Container & Records Business Logic
    max_container_capacity = fields.Integer(
        string="Max Container Capacity",
        help="Maximum number of standard records containers the vehicle can hold.",
        tracking=True
    )

    # NAID Compliance & Certification
    naid_compliant = fields.Boolean(
        string="NAID Compliant Vehicle",
        default=False,
        help="Vehicle meets NAID AAA compliance standards for secure document transport.",
        tracking=True
    )

    # Specialized Vehicle Types for Records Business
    records_vehicle_type = fields.Selection([
        ('standard_pickup', 'Standard Pickup Vehicle'),
        ('secure_transport', 'Secure Document Transport'),
        ('shredding_truck', 'Mobile Shredding Truck'),
        ('container_delivery', 'Container Delivery Vehicle'),
    ], string="Records Vehicle Type", tracking=True)

    # Operational Status for Records Operations
    records_operational_status = fields.Selection([
        ('available', 'Available for Routes'),
        ('on_route', 'Currently on Route'),
        ('maintenance', 'Under Maintenance'),
        ('out_of_service', 'Out of Service'),
    ], string="Records Operational Status", default='available', tracking=True)

    # ============================================================================
    # RELATIONSHIPS (Updated to use fleet.vehicle as base)
    # ============================================================================
    pickup_route_ids = fields.One2many('pickup.route', 'vehicle_id', string="Pickup Routes")

    # Use fleet.vehicle's built-in driver_id instead of custom field
    # Use fleet.vehicle's built-in state management instead of custom state
    # Use fleet.vehicle's built-in company_id, license_plate, vin, etc.

    # ============================================================================
    # RECORDS-SPECIFIC BUSINESS METHODS
    # ============================================================================

    def action_set_records_available(self):
        """Set vehicle as available for records pickup routes."""
        self.ensure_one()
        self.write({'records_operational_status': 'available'})
        self.message_post(body=_("Vehicle set to Available for Records Routes."))

    def action_set_records_on_route(self):
        """Set vehicle as currently on a pickup route."""
        self.ensure_one()
        self.write({'records_operational_status': 'on_route'})
        self.message_post(body=_("Vehicle set to On Route."))

    def action_view_pickup_routes(self):
        """View pickup routes assigned to this vehicle."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicle Pickup Routes"),
            "res_model": "pickup.route",
            "view_mode": "tree,form,kanban",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {'default_vehicle_id': self.id}
        }

    @api.model
    def get_available_records_vehicles(self):
        """Get vehicles available for records pickup operations."""
        return self.search([
            ('records_operational_status', '=', 'available'),
            ('state_id.name', '!=', 'Archived'),  # Use fleet.vehicle's state
        ])

    def check_naid_compliance(self):
        """Validate NAID compliance requirements for secure transport."""
        self.ensure_one()
        if self.records_vehicle_type == 'secure_transport' and not self.naid_compliant:
            raise ValidationError(_("Secure transport vehicles must be NAID compliant."))
        return True
