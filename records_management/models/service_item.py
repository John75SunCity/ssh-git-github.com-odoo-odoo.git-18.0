from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import date, timedelta


class ServiceItem(models.Model):
    _name = 'service.item'
    _description = 'Service Item Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, category, service_type'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Service/Item Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    service_code = fields.Char(string="Service Code", copy=False)

    # ============================================================================
    # CATEGORIZATION & TYPE
    # ============================================================================
    category = fields.Selection([
        ('equipment', 'Equipment'),
        ('service', 'Service'),
        ('consumable', 'Consumable'),
    ], string="Category", default='service', required=True, tracking=True)

    service_type = fields.Selection([
        ('shredding', 'Shredding'),
        ('storage', 'Storage'),
        ('scanning', 'Scanning'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ], string="Service Type", tracking=True)

    # ============================================================================
    # STATUS & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('available', 'Available'),
        ('in_use', 'In Use'),
        ('maintenance', 'Under Maintenance'),
        ('retired', 'Retired'),
    ], string="Status", default='available', required=True, tracking=True, help="Lifecycle status of the service item.")

    # ============================================================================
    # SPECIFICATIONS (for Equipment)
    # ============================================================================
    model_number = fields.Char(string="Model Number", tracking=True)
    serial_number = fields.Char(string="Serial Number", tracking=True)
    manufacturer = fields.Char(string="Manufacturer", tracking=True)
    capacity = fields.Float(string="Capacity", help="Capacity of the item, e.g., pages per minute for a scanner.")
    capacity_unit = fields.Selection([
        ('pages_per_minute', 'Pages/Minute'),
        ('kg_per_hour', 'kg/Hour'),
        ('items', 'Items'),
    ], string="Capacity Unit")
    specifications = fields.Text(string="Technical Specifications")
    operating_instructions = fields.Text(string="Operating Instructions")
    safety_notes = fields.Text(string="Safety Notes")

    # ============================================================================
    # FINANCIALS
    # ============================================================================
    currency_id = fields.Many2one(related='company_id.currency_id')
    purchase_cost = fields.Monetary(string="Purchase Cost", tracking=True)
    current_value = fields.Monetary(string="Current Value", compute='_compute_current_value', store=True)
    maintenance_cost = fields.Monetary(string="Total Maintenance Cost", compute='_compute_maintenance_cost', store=True)
    purchase_date = fields.Date(string="Purchase Date", tracking=True)
    warranty_expiry = fields.Date(string="Warranty Expiry", tracking=True)
    depreciation_rate = fields.Float(string="Annual Depreciation Rate (%)", default=10.0)

    # ============================================================================
    # MAINTENANCE (for Equipment)
    # ============================================================================
    location_id = fields.Many2one('stock.location', string="Location", domain="[('usage', '=', 'internal')]")
    assigned_user_id = fields.Many2one('res.users', string="Assigned User", tracking=True)
    department_id = fields.Many2one('hr.department', string="Department")
    last_maintenance_date = fields.Date(string="Last Maintenance Date", tracking=True)
    next_maintenance_date = fields.Date(string="Next Maintenance Date", compute='_compute_next_maintenance_date', store=True)
    maintenance_interval_days = fields.Integer(string="Maintenance Interval (Days)", default=180)
    is_maintenance_due = fields.Boolean(string="Maintenance Due", compute='_compute_is_maintenance_due', store=True)
    maintenance_request_ids = fields.One2many('maintenance.request', 'equipment_id', string="Maintenance Requests")
    maintenance_request_count = fields.Integer(compute='_compute_maintenance_request_count', string="Maintenance Count")

    # ============================================================================
    # RELATIONSHIPS & ANALYTICS
    # ============================================================================
    service_request_ids = fields.One2many('project.task', 'service_item_id', string="Service Requests")
    service_request_count = fields.Integer(compute='_compute_service_request_count', string="Service Request Count")
    utilization_rate = fields.Float(string="Utilization Rate (%)", help="Calculated based on usage vs. availability.")
    efficiency_rating = fields.Selection([('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], string="Efficiency Rating")

    # ============================================================================
    # CONFIGURATOR VISIBILITY
    # ============================================================================
    show_maintenance_tracking = fields.Boolean(compute='_compute_configurator_settings')
    show_financial_tracking = fields.Boolean(compute='_compute_configurator_settings')
    show_performance_metrics = fields.Boolean(compute='_compute_configurator_settings')

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('name', 'service_code')
    def _compute_display_name(self):
        for record in self:
            if record.service_code:
                record.display_name = f"[{record.service_code}] {record.name}"
            else:
                record.display_name = record.name

    def _is_feature_enabled(self, feature_key):
        self.ensure_one()
        return self.env['rm.module.configurator'].is_feature_enabled('service_management', feature_key, self.company_id.id)

    def _compute_configurator_settings(self):
        for record in self:
            record.show_maintenance_tracking = record._is_feature_enabled("enable_maintenance_tracking")
            record.show_financial_tracking = record._is_feature_enabled("enable_financial_tracking")
            record.show_performance_metrics = record._is_feature_enabled("enable_performance_metrics")

    @api.depends('purchase_date', 'purchase_cost', 'depreciation_rate')
    def _compute_current_value(self):
        for record in self:
            if record.purchase_cost and record.purchase_date:
                age_days = (date.today() - record.purchase_date).days
                age_years = age_days / 365.25
                depreciation_amount = record.purchase_cost * (record.depreciation_rate / 100.0) * age_years
                record.current_value = max(0.0, record.purchase_cost - depreciation_amount)
            else:
                record.current_value = record.purchase_cost or 0.0

    @api.depends('maintenance_request_ids.cost')
    def _compute_maintenance_cost(self):
        for record in self:
            record.maintenance_cost = sum(record.maintenance_request_ids.mapped('cost'))

    @api.depends('last_maintenance_date', 'maintenance_interval_days')
    def _compute_next_maintenance_date(self):
        for record in self:
            if record.last_maintenance_date and record.maintenance_interval_days > 0:
                record.next_maintenance_date = record.last_maintenance_date + timedelta(days=record.maintenance_interval_days)
            else:
                record.next_maintenance_date = False

    @api.depends('next_maintenance_date')
    def _compute_is_maintenance_due(self):
        for record in self:
            record.is_maintenance_due = record.next_maintenance_date and record.next_maintenance_date <= date.today()

    @api.depends('maintenance_request_ids')
    def _compute_maintenance_request_count(self):
        for record in self:
            record.maintenance_request_count = len(record.maintenance_request_ids)

    @api.depends('service_request_ids')
    def _compute_service_request_count(self):
        for record in self:
            record.service_request_count = len(record.service_request_ids)

    @api.constrains('maintenance_interval_days')
    def _check_maintenance_interval(self):
        for record in self:
            if record.maintenance_interval_days < 0:
                raise ValidationError(_("Maintenance interval must be a positive number."))

    @api.constrains('purchase_cost', 'current_value')
    def _check_financial_values(self):
        for record in self:
            if record.purchase_cost < 0 or record.current_value < 0:
                raise ValidationError(_("Financial values cannot be negative."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_set_available(self):
        self.write({'state': 'available'})
        self.message_post(body=_("Status set to Available."))

    def action_set_in_use(self):
        self.write({'state': 'in_use'})
        self.message_post(body=_("Status set to In Use."))

    def action_send_for_maintenance(self):
        self.ensure_one()
        self.write({'state': 'maintenance'})
        self.message_post(body=_("Status set to Under Maintenance."))
        if 'maintenance.request' in self.env:
            return {
                'type': 'ir.actions.act_window',
                'name': _('New Maintenance Request'),
                'res_model': 'maintenance.request',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_name': _('Maintenance for %s', self.name),
                    'default_equipment_id': self.id,
                    'default_maintenance_type': 'corrective' if self.is_maintenance_due else 'preventive',
                }
            }

    def action_retire(self):
        self.write({'state': 'retired', 'active': False})
        self.message_post(body=_("Item has been retired."))

    def action_view_maintenance_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Maintenance Requests"),
            "res_model": "maintenance.request",
            "view_mode": "tree,form,kanban",
            "domain": [("equipment_id", "=", self.id)],
            "context": {'default_equipment_id': self.id}
        }

    def action_view_service_requests(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Service Requests"),
            "res_model": "project.task",
            "view_mode": "tree,form,kanban",
            "domain": [("service_item_id", "=", self.id)],
            "context": {'default_service_item_id': self.id}
        }

    # ============================================================================
    # CRON JOB
    # ============================================================================
    @api.model
    def _cron_check_maintenance_due(self):
        """Cron job to create activities for items due for maintenance."""
        due_items = self.search([
            ('is_maintenance_due', '=', True),
            ('state', 'in', ['available', 'in_use'])
        ])
        for item in due_items:
            activity_type = self.env.ref('mail.mail_activity_data_todo')
            user = item.assigned_user_id or item.user_id
            if user:
                item.activity_schedule(
                    activity_type_id=activity_type.id,
                    summary=_("Maintenance Due: %s", item.display_name),
                    note=_("Preventive maintenance is due for this item."),
                    user_id=user.id,
                    date_deadline=fields.Date.today(),
                )
