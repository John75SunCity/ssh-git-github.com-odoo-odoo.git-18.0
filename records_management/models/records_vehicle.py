from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsVehicle(models.Model):
    _name = 'records.vehicle'
    _description = 'Records Vehicle Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Vehicle Name/Identifier", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    vin = fields.Char(string="VIN", tracking=True)
    license_plate = fields.Char(string="License Plate", required=True, tracking=True)

    # ============================================================================
    # STATUS & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('archived', 'Archived'),
    ], string="Lifecycle Status", default='active', required=True, tracking=True)

    status = fields.Selection([
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
    ], string="Operational Status", default='available', required=True, tracking=True)

    # ============================================================================
    # SPECIFICATIONS & CAPACITY
    # ============================================================================
    vehicle_type = fields.Selection([
        ('truck', 'Truck'),
        ('van', 'Van'),
        ('car', 'Car'),
        ('other', 'Other'),
    ], string="Vehicle Type", default='truck', tracking=True)

    fuel_type = fields.Selection([
        ('gasoline', 'Gasoline'),
        ('diesel', 'Diesel'),
        ('electric', 'Electric'),
        ('hybrid', 'Hybrid'),
    ], string="Fuel Type", tracking=True)

    vehicle_capacity_volume = fields.Float(string="Capacity (Volume)", help="Total volume capacity in cubic meters.", tracking=True)
    vehicle_capacity_weight = fields.Float(string="Capacity (Weight)", help="Total weight capacity in kilograms.", tracking=True)
    max_boxes = fields.Integer(string="Max Container Capacity", help="Maximum number of standard containers the vehicle can hold.", tracking=True)

    # ============================================================================
    # MAINTENANCE & RESPONSIBILITY
    # ============================================================================
    driver_id = fields.Many2one('res.users', string="Assigned Driver", tracking=True)
    last_service_date = fields.Date(string="Last Service Date", tracking=True)
    next_service_date = fields.Date(string="Next Service Date", tracking=True)
    service_notes = fields.Text(string="Maintenance Notes")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    pickup_route_ids = fields.One2many('fsm.route', 'vehicle_id', string="Pickup Routes")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('license_plate', 'company_id')
    def _check_license_plate_unique(self):
        for record in self:
            if record.license_plate:
                domain = [
                    ('license_plate', '=', record.license_plate),
                    ('company_id', '=', record.company_id.id),
                    ('id', '!=', record.id),
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("A vehicle with this license plate already exists in this company."))

    @api.constrains('last_service_date', 'next_service_date')
    def _check_service_dates(self):
        for record in self:
            if record.last_service_date and record.next_service_date and record.next_service_date < record.last_service_date:
                raise ValidationError(_("The next service date cannot be before the last service date."))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'license_plate')
    def _compute_display_name(self):
        for record in self:
            if record.name and record.license_plate:
                record.display_name = f"{record.name} [{record.license_plate}]"
            else:
                record.display_name = record.name or _("New Vehicle")

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.vehicle') or _('New Vehicle')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_set_available(self):
        self.ensure_one()
        self.write({'status': 'available'})
        self.message_post(body=_("Vehicle status set to Available."))

    def action_set_in_use(self):
        self.ensure_one()
        self.write({'status': 'in_use'})
        self.message_post(body=_("Vehicle status set to In Use."))

    def action_set_maintenance(self):
        self.ensure_one()
        self.write({'status': 'maintenance'})
        self.message_post(body=_("Vehicle status set to Under Maintenance."))

    def action_view_routes(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Vehicle Routes"),
            "res_model": "fsm.route",
            "view_mode": "tree,form,kanban",
            "domain": [("vehicle_id", "=", self.id)],
            "context": {'default_vehicle_id': self.id}
        }

    # ============================================================================
    # AUTOMATED ACTIONS (CRON)
    # ============================================================================
    @api.model
    def _cron_schedule_maintenance_due_activities(self):
        """Cron job to check for vehicles due for maintenance and schedule activities."""
        due_vehicles = self.search([
            ('next_service_date', '<=', fields.Date.today()),
            ('status', '!=', 'maintenance'),
            ('state', '=', 'active'),
        ])
        for vehicle in due_vehicles:
            vehicle.activity_schedule(
                'mail.mail_activity_data_todo',
                summary=_("Maintenance Due: %s") % vehicle.display_name,
                note=_("Vehicle maintenance is due. Please schedule service."),
                user_id=vehicle.driver_id.id or self.env.user.id,
                date_deadline=fields.Date.today(),
            )
