import uuid
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsLocation(models.Model):
    _name = 'records.location'
    _description = 'Records Storage Location'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Location Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    code = fields.Char(string="Location Code", required=True, copy=False, readonly=True, default=lambda self: _('New'), tracking=True)
    active = fields.Boolean(string='Active', default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # HIERARCHY & RELATIONSHIPS
    # ============================================================================
    parent_location_id = fields.Many2one('records.location', string="Parent Location", ondelete='cascade', tracking=True)
    child_location_ids = fields.One2many('records.location', 'parent_location_id', string="Child Locations")
    child_count = fields.Integer(string="Child Location Count", compute='_compute_child_count')
    container_ids = fields.One2many('records.container', 'location_id', string="Containers")
    container_count = fields.Integer(string="Container Count", compute='_compute_container_count', store=True)

    # ============================================================================
    # ADDRESS & COORDINATES
    # ============================================================================
    street = fields.Char()
    street2 = fields.Char()
    city = fields.Char()
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', domain="[('country_id', '=?', country_id)]")
    zip = fields.Char(string='Zip', change_default=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict')
    full_address = fields.Text(string="Full Address", compute='_compute_full_address')
    
    building = fields.Char(string="Building")
    floor = fields.Char(string="Floor")
    zone = fields.Char(string="Zone")
    aisle = fields.Char(string="Aisle")
    rack = fields.Char(string="Rack")
    shelf = fields.Char(string="Shelf")
    position = fields.Char(string="Position")
    full_coordinates = fields.Char(string="Full Coordinates", compute='_compute_full_coordinates', store=True)

    # ============================================================================
    # CAPACITY & UTILIZATION
    # ============================================================================
    max_capacity = fields.Integer(string="Maximum Capacity (Containers)", tracking=True, help="The total number of containers this location can hold.")
    utilization_percentage = fields.Float(string="Utilization (%)", compute='_compute_utilization_percentage', store=True, group_operator="avg")
    available_spaces = fields.Integer(string="Available Spaces", compute='_compute_available_spaces', store=True)
    is_at_capacity = fields.Boolean(string="Is At Capacity", compute='_compute_is_at_capacity', store=True)

    # ============================================================================
    # STATUS & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('maintenance', 'Maintenance'),
        ('full', 'Full'),
        ('inactive', 'Inactive'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SECURITY & COMPLIANCE
    # ============================================================================
    security_level = fields.Selection([
        ('level_1', 'Level 1 (Low)'),
        ('level_2', 'Level 2 (Medium)'),
        ('level_3', 'Level 3 (High)'),
        ('level_4', 'Level 4 (Maximum)'),
    ], string="Security Level", default='level_2', tracking=True)
    temperature_controlled = fields.Boolean(string="Temperature Controlled", tracking=True)
    humidity_controlled = fields.Boolean(string="Humidity Controlled", tracking=True)
    fire_suppression_system = fields.Boolean(string="Fire Suppression System", tracking=True)
    last_inspection_date = fields.Date(string="Last Inspection Date", readonly=True)
    next_inspection_date = fields.Date(string="Next Inspection Date", tracking=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('code', _('New')) == _('New'):
                vals['code'] = self.env['ir.sequence'].next_by_code('records.location') or _('New')
        return super().create(vals_list)

    def unlink(self):
        for loc in self:
            if loc.container_ids:
                raise UserError(_("You cannot delete a location that contains containers. Please move them first."))
            if loc.child_location_ids:
                raise UserError(_("You cannot delete a location that has child locations. Please remove or re-parent them first."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'code')
    def _compute_display_name(self):
        for record in self:
            record.display_name = f"[{record.code}] {record.name}" if record.code else record.name

    @api.depends('street', 'street2', 'city', 'state_id', 'zip', 'country_id')
    def _compute_full_address(self):
        for record in self:
            address_parts = [record.street, record.street2, record.city, record.state_id.name, record.zip, record.country_id.name]
            record.full_address = ', '.join(filter(None, address_parts))

    @api.depends('building', 'floor', 'zone', 'aisle', 'rack', 'shelf', 'position')
    def _compute_full_coordinates(self):
        for record in self:
            parts = [record.building, record.floor, record.zone, record.aisle, record.rack, record.shelf, record.position]
            record.full_coordinates = ' > '.join(filter(None, parts))

    @api.depends('child_location_ids')
    def _compute_child_count(self):
        for record in self:
            record.child_count = len(record.child_location_ids)

    @api.depends('container_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.container_ids)

    @api.depends('container_count', 'max_capacity')
    def _compute_utilization_percentage(self):
        for record in self:
            if record.max_capacity > 0:
                record.utilization_percentage = (record.container_count / record.max_capacity) * 100.0
            else:
                record.utilization_percentage = 0.0

    @api.depends('container_count', 'max_capacity')
    def _compute_available_spaces(self):
        for record in self:
            record.available_spaces = max(0, record.max_capacity - record.container_count)

    @api.depends('available_spaces')
    def _compute_is_at_capacity(self):
        for record in self:
            record.is_at_capacity = record.available_spaces <= 0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('parent_location_id')
    def _check_location_hierarchy(self):
        if not self._check_recursion():
            raise ValidationError(_('You cannot create recursive locations.'))

    @api.constrains('max_capacity')
    def _check_max_capacity(self):
        for record in self:
            if record.max_capacity < 0:
                raise ValidationError(_("Maximum capacity cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_containers(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Containers'),
            'res_model': 'records.container',
            'view_mode': 'tree,form,kanban',
            'domain': [('location_id', '=', self.id)],
            'context': {'default_location_id': self.id}
        }

    def action_view_child_locations(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Child Locations'),
            'res_model': 'records.location',
            'view_mode': 'tree,form',
            'domain': [('parent_location_id', '=', self.id)],
            'context': {'default_parent_location_id': self.id}
        }

    def action_activate(self):
        self.write({'active': True, 'state': 'active'})
        self.message_post(body=_("Location activated."))

    def action_deactivate(self):
        self.write({'active': False, 'state': 'inactive'})
        self.message_post(body=_("Location deactivated."))

