from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    code = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    active = fields.Boolean()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    partner_id = fields.Many2one()
    building = fields.Char()
    floor = fields.Char()
    zone = fields.Char()
    aisle = fields.Char()
    rack = fields.Char()
    shelf = fields.Char()
    position = fields.Char()
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one()
    zip = fields.Char()
    country_id = fields.Many2one()
    full_address = fields.Text()
    location_type = fields.Selection()
    storage_capacity = fields.Integer()
    max_capacity = fields.Integer()
    current_utilization = fields.Integer()
    available_spaces = fields.Integer()
    available_space = fields.Integer()
    utilization_percentage = fields.Float()
    box_count = fields.Integer()
    max_weight_capacity = fields.Float()
    temperature_controlled = fields.Boolean()
    humidity_controlled = fields.Boolean()
    fire_suppression = fields.Boolean()
    security_level = fields.Selection()
    access_restrictions = fields.Text()
    authorized_user_ids = fields.Many2many()
    requires_escort = fields.Boolean()
    security_camera = fields.Boolean()
    access_card_required = fields.Boolean()
    operational_status = fields.Selection()
    availability_schedule = fields.Text()
    last_inspection_date = fields.Date()
    next_inspection_date = fields.Date()
    container_ids = fields.One2many()
    box_ids = fields.One2many()
    parent_location_id = fields.Many2one()
    child_location_ids = fields.One2many()
    state = fields.Selection()
    child_count = fields.Integer()
    is_available = fields.Boolean()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    climate_controlled = fields.Boolean(string='Climate Controlled')
    fire_protection_system = fields.Char(string='Fire Protection System')
    biometric_access = fields.Boolean(string='Biometric Access')
    surveillance_cameras = fields.Integer(string='Number of Cameras')
    last_security_audit = fields.Date(string='Last Security Audit')
    next_security_audit_due = fields.Date(string='Next Security Audit Due')
    access_instructions = fields.Text(string='Access Instructions')
    storage_start_date = fields.Date(string='Storage Start Date')
    action_location_report = fields.Char(string='Action Location Report')
    action_view_containers = fields.Char(string='Action View Containers')
    at_capacity = fields.Char(string='At Capacity')
    button_box = fields.Char(string='Button Box')
    card = fields.Char(string='Card')
    containers = fields.Char(string='Containers')
    context = fields.Char(string='Context')
    details = fields.Char(string='Details')
    group_by_parent = fields.Char(string='Group By Parent')
    group_by_type = fields.Selection(string='Group By Type')
    help = fields.Char(string='Help')
    inactive = fields.Boolean(string='Inactive')
    lots_of_space = fields.Char(string='Lots Of Space')
    near_capacity = fields.Char(string='Near Capacity')
    optimal_load = fields.Char(string='Optimal Load')
    res_model = fields.Char(string='Res Model')
    search_view_id = fields.Many2one('search.view')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_full_address(self):
            """Compute full formatted address"""
            for record in self:
                address_parts = []
                if record.street:
                    address_parts.append(record.street)
                if record.street2:
                    address_parts.append(record.street2)
                if record.city:
                    address_parts.append(record.city)
                if record.state_id:
                    address_parts.append(record.state_id.name)
                if record.zip:
                    address_parts.append(record.zip)
                if record.country_id:
                    address_parts.append(record.country_id.name)
                record.full_address = ", ".join(address_parts) if address_parts else "":

    def _compute_current_utilization(self):
            """Compute current utilization based on container count"""
            for record in self:
                record.current_utilization = len(record.container_ids)


    def _compute_box_count(self):
            """Compute the number of boxes at this location"""
            for record in self:
                record.box_count = len(record.box_ids)


    def _compute_available_space(self):
            """Compute available space based on maximum capacity and current box count"""
            for record in self:
                record.available_space = max(0, record.max_capacity - record.box_count)


    def _compute_available_spaces(self):
            """Compute available spaces based on storage capacity and utilization"""
            for record in self:
                if record.storage_capacity > 0:
                    record.available_spaces = max()
                        0, record.storage_capacity - record.current_utilization

                else:
                    record.available_spaces = 0


    def _compute_utilization_percentage(self):
            """Compute utilization percentage"""
            for record in self:
                if record.storage_capacity > 0:
                    record.utilization_percentage = ()
                        record.current_utilization / record.storage_capacity * 100.0

                else:
                    record.utilization_percentage = 0.0


    def _compute_child_count(self):
            """Compute count of child locations"""
            for record in self:
                record.child_count = len(record.child_location_ids)


    def _compute_is_available(self):
            """Compute if location is available for new storage""":
            for record in self:
                record.is_available = ()
                    record.operational_status == "active"
                    and record.current_utilization < record.storage_capacity


        # ============================================================================
            # CRUD METHODS
        # ============================================================================

    def create(self, vals_list):
            """Create locations with auto-generated codes if needed""":
            if not vals_list:
                return self.env[self._name]

            for vals in vals_list:
                if not vals.get("code"):
                    seq_code = self.env["ir.sequence"].next_by_code("records.location")
                    if seq_code:
                        vals["code"] = seq_code
                    else:
                        vals["code"] = "LOC/%s" % uuid.uuid4().hex[:8]

            return super().create(vals_list)

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_view_containers(self):
            """View containers at this location"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Records Containers"),
                "res_model": "records.container",
                "view_mode": "tree,form",
                "domain": [("location_id", "=", self.id)],
                "context": {"default_location_id": self.id},



    def action_location_report(self):
            """Generate location utilization and capacity report"""
            self.ensure_one()
            return {}
                "type": "ir.actions.report",
                "report_name": "records_management.location_utilization_report",
                "report_type": "qweb-pdf",
                "data": {"ids": [self.id]},
                "context": self.env.context,



    def action_maintenance_mode(self):
            """Set location to maintenance mode"""
            self.ensure_one()
            self.write({"operational_status": "maintenance"})
            self.message_post()
                body=_("Location %s set to maintenance mode", self.name),
                message_type="notification",


    def action_activate_location(self):
            """Activate location"""
            for record in self:
                record.write({)}
                    "state": "active",
                    "operational_status": "active"

                record.message_post(body=_("Location activated"))


    def action_deactivate_location(self):
            """Deactivate location"""
            for record in self:
                if record.current_utilization > 0:
                    raise UserError(_("Cannot deactivate location with stored containers"))

                record.write({)}
                    "state": "inactive",
                    "operational_status": "inactive"

                record.message_post(body=_("Location deactivated"))


    def action_reserve_space(self):
            """Open form to reserve space at this location"""
            self.ensure_one()
            if not self.is_available:
                raise UserError(_("Location is not available for reservations")):
            return {}
                "type": "ir.actions.act_window",
                "name": _("Reserve Space"),
                "res_model": "records.location.reservation",
                "view_mode": "form",
                "target": "new",
                "context": {"default_location_id": self.id},



    def action_schedule_inspection(self):
            """Schedule location inspection"""
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Schedule Inspection"),
                "res_model": "records.location.inspection",
                "view_mode": "form",
                "target": "new",
                "context": {"default_location_id": self.id},


        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_full_location_path(self):
            """Return full hierarchical path of location"""
            self.ensure_one()
            path = [self.name]
            current = self.parent_location_id
            while current:
                path.insert(0, current.name)
                current = current.parent_location_id
            return " > ".join(path)


    def get_available_capacity(self):
            """Return available storage capacity"""
            self.ensure_one()
            return max(0, self.storage_capacity - self.current_utilization)


    def get_location_coordinates(self):
            """Get detailed location coordinates"""
            self.ensure_one()
            coordinates = []

            if self.building:
                coordinates.append(_("Building: %s", self.building))
            if self.floor:
                coordinates.append(_("Floor: %s", self.floor))
            if self.zone:
                coordinates.append(_("Zone: %s", self.zone))
            if self.aisle:
                coordinates.append(_("Aisle: %s", self.aisle))
            if self.rack:
                coordinates.append(_("Rack: %s", self.rack))
            if self.shelf:
                coordinates.append(_("Shelf: %s", self.shelf))
            if self.position:
                coordinates.append(_("Position: %s", self.position))

            return ", ".join(coordinates)


    def get_security_info(self):
            """Get comprehensive security information"""
            self.ensure_one()
            security_features = []

            security_features.append(_("Security Level: %s", dict(self._fields['security_level'].selection)[self.security_level]))

            if self.security_camera:
                security_features.append(_("Security Camera: Yes"))
            if self.access_card_required:
                security_features.append(_("Access Card Required: Yes"))
            if self.requires_escort:
                security_features.append(_("Escort Required: Yes"))
            if self.fire_suppression:
                security_features.append(_("Fire Suppression: Yes"))
            if self.temperature_controlled:
                security_features.append(_("Temperature Controlled: Yes"))
            if self.humidity_controlled:
                security_features.append(_("Humidity Controlled: Yes"))

            return security_features


    def check_capacity_availability(self, required_spaces):
            """Check if location has sufficient capacity for required spaces""":
            self.ensure_one()
            available = self.get_available_capacity()
            return available >= required_spaces


    def find_available_locations(self, required_capacity=1, location_type=None, security_level=None):
            """Find locations with available capacity matching criteria"""
            domain = []
                ('is_available', '=', True),
                ('available_spaces', '>=', required_capacity),
                ('operational_status', '=', 'active')


            if location_type:
                domain.append(('location_type', '=', location_type))

            if security_level:
                domain.append(('security_level', '=', security_level))

            return self.search(domain, order='utilization_percentage asc')

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_storage_capacity(self):
            """Validate storage capacity constraints"""
            for record in self:
                if record.storage_capacity < 0:
                    raise ValidationError(_("Storage capacity cannot be negative"))
                if record.max_capacity < 0:
                    raise ValidationError(_("Maximum capacity cannot be negative"))
                if record.storage_capacity > record.max_capacity:
                    raise ValidationError(_("Storage capacity cannot exceed maximum capacity"))


    def _check_parent_location(self):
            """Validate parent location hierarchy"""
            for record in self:
                if record.parent_location_id:
                    if record.parent_location_id == record:
                        raise ValidationError(_("A location cannot be its own parent"))

                    # Check for circular reference:
                    current = record.parent_location_id
                    visited = {record.id}
                    while current:
                        if current.id in visited:
                            raise ValidationError()
                                _("Circular reference detected in location hierarchy")

                        visited.add(current.id)
                        current = current.parent_location_id


    def _check_code_uniqueness(self):
            """Ensure location code uniqueness"""
            for record in self:
                if record.code:
                    existing = self.search([)]
                        ("code", "=", record.code),
                        ("id", "!=", record.id)

                    if existing:
                        raise ValidationError(_("Location code must be unique"))


    def _check_weight_capacity(self):
            """Validate weight capacity constraints"""
            for record in self:
                if record.max_weight_capacity and record.max_weight_capacity < 0:
                    raise ValidationError(_("Maximum weight capacity cannot be negative"))


    def _check_utilization_percentage(self):
            """Validate utilization percentage is within bounds"""
            for record in self:
                if record.utilization_percentage < 0 or record.utilization_percentage > 100:
                    raise ValidationError(_("Utilization percentage must be between 0 and 100"))

        # ============================================================================
            # BUSINESS LOGIC METHODS
        # ============================================================================

    def update_operational_status(self):
            """Update operational status based on utilization"""
            for record in self:
                if record.utilization_percentage >= 100:
                    record.operational_status = 'full'
                elif record.utilization_percentage >= 95:
                    # Near capacity warning
                    record.message_post()
                        body=_("Location %s is near capacity (%s%%)",
                                record.name, record.utilization_percentage
                        message_type="notification"



    def schedule_maintenance(self, maintenance_date, description=None):
            """Schedule maintenance for this location""":
            self.ensure_one()

            if self.current_utilization > 0:
                # Create notification for containers that need relocation:
                self.message_post()
                    body=_("Maintenance scheduled for %s. %s containers need relocation.",:)
                            maintenance_date, self.current_utilization
                    message_type="notification"


            self.write({)}
                'operational_status': 'maintenance',
                'next_inspection_date': maintenance_date


            if description:
                self.message_post(body=_("Maintenance scheduled: %s", description))


    def get_capacity_forecast(self, days_ahead=30):
            """Forecast capacity utilization for planning purposes""":
            self.ensure_one()

            # Simple capacity forecasting based on recent trends
            # This could be enhanced with more sophisticated algorithms
            current_utilization = self.current_utilization
            capacity = self.storage_capacity

            if capacity == 0:
                return {'error': _('No storage capacity defined')}

            # Calculate trend based on recent container additions
            recent_additions = self.env['records.container').search_count([]]
                ('location_id', '=', self.id),
                ('create_date', '>=', fields.Datetime.now() - )
                    fields.Datetime.timedelta(days=30)


            daily_growth_rate = recent_additions / 30 if recent_additions else 0:
            projected_utilization = current_utilization + (daily_growth_rate * days_ahead)
            projected_percentage = (projected_utilization / capacity) * 100

            return {}
                'current_utilization': current_utilization,
                'projected_utilization': min(projected_utilization, capacity),
                'projected_percentage': min(projected_percentage, 100),
                'days_to_capacity': (capacity - current_utilization) / daily_growth_rate if daily_growth_rate > 0 else None,:
                'recommendation': self._get_capacity_recommendation(projected_percentage)



    def _get_capacity_recommendation(self, projected_percentage):
            """Get recommendation based on projected capacity"""
            if projected_percentage >= 95:
                return _('URGENT: Location will reach capacity soon. Consider expansion or relocation.')
            elif projected_percentage >= 80:
                return _('WARNING: Location utilization will be high. Monitor closely.')
            elif projected_percentage >= 60:
                return _('NORMAL: Utilization is within acceptable range.')
            else:
                return _('GOOD: Location has ample available capacity.')

    def _compute_utilization(self):
            """Calculate current utilization percentage"""
            for record in self:
                if record.max_capacity and record.max_capacity > 0:
                    record.current_utilization = (record.box_count / record.max_capacity) * 100
                else:
                    record.current_utilization = 0.0

