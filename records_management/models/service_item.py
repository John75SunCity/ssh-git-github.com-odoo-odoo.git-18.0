from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ServiceItem(models.Model):
    _name = 'service.item'
    _description = 'Service Item Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, category, service_type'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    description = fields.Text()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    show_maintenance_tracking = fields.Boolean()
    show_financial_tracking = fields.Boolean()
    show_performance_metrics = fields.Boolean()
    state = fields.Selection()
    service_type = fields.Selection()
    category = fields.Selection()
    model_number = fields.Char()
    serial_number = fields.Char()
    manufacturer = fields.Char()
    purchase_date = fields.Date()
    warranty_expiry = fields.Date()
    currency_id = fields.Many2one()
    purchase_cost = fields.Monetary()
    current_value = fields.Monetary()
    maintenance_cost = fields.Monetary()
    depreciation_rate = fields.Float()
    location_id = fields.Many2one()
    assigned_user_id = fields.Many2one()
    department_id = fields.Many2one()
    last_maintenance = fields.Date()
    next_maintenance = fields.Date()
    maintenance_interval = fields.Integer()
    maintenance_due = fields.Boolean()
    capacity = fields.Float()
    capacity_unit = fields.Selection()
    utilization_rate = fields.Float()
    efficiency_rating = fields.Selection()
    warranty_status = fields.Selection()
    age_months = fields.Integer()
    service_request_ids = fields.One2many()
    maintenance_request_ids = fields.One2many()
    specifications = fields.Text()
    operating_instructions = fields.Text()
    safety_notes = fields.Text()
    notes = fields.Text(string='Internal Notes')
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    action_activate = fields.Char(string='Action Activate')
    action_deactivate = fields.Char(string='Action Deactivate')
    action_duplicate_service = fields.Char(string='Action Duplicate Service')
    action_view_pricing_history = fields.Char(string='Action View Pricing History')
    action_view_related_requests = fields.Char(string='Action View Related Requests')
    activities = fields.Char(string='Activities')
    activity_state = fields.Selection(string='Activity State')
    adjustment_type = fields.Selection(string='Adjustment Type')
    analytics = fields.Char(string='Analytics')
    approval_level = fields.Char(string='Approval Level')
    audit_trail_required = fields.Boolean(string='Audit Trail Required')
    auto_create_task = fields.Char(string='Auto Create Task')
    average_completion_time = fields.Float(string='Average Completion Time')
    base_price = fields.Float(string='Base Price')
    button_box = fields.Char(string='Button Box')
    certificate_required = fields.Boolean(string='Certificate Required')
    certification_required = fields.Boolean(string='Certification Required')
    completed_count = fields.Integer(string='Completed Count')
    compliance = fields.Char(string='Compliance')
    condition_field = fields.Char(string='Condition Field')
    condition_operator = fields.Char(string='Condition Operator')
    condition_value = fields.Char(string='Condition Value')
    context = fields.Char(string='Context')
    cost_price = fields.Float(string='Cost Price')
    customer_can_request = fields.Char(string='Customer Can Request')
    customer_satisfaction = fields.Char(string='Customer Satisfaction')
    domain = fields.Char(string='Domain')
    email_confirmation_required = fields.Boolean(string='Email Confirmation Required')
    equipment_ids = fields.One2many('equipment')
    estimated_duration = fields.Char(string='Estimated Duration')
    group_active = fields.Boolean(string='Group Active')
    group_approval = fields.Char(string='Group Approval')
    group_category = fields.Char(string='Group Category')
    group_company = fields.Char(string='Group Company')
    group_create_date = fields.Date(string='Group Create Date')
    group_naid = fields.Char(string='Group Naid')
    group_type = fields.Selection(string='Group Type')
    help = fields.Char(string='Help')
    high_demand = fields.Char(string='High Demand')
    inactive = fields.Boolean(string='Inactive')
    internal_notes = fields.Char(string='Internal Notes')
    iso_compliant = fields.Char(string='Iso Compliant')
    last_revenue_date = fields.Date(string='Last Revenue Date')
    low_revenue = fields.Char(string='Low Revenue')
    margin_percent = fields.Float(string='Margin Percent')
    max_technicians = fields.Char(string='Max Technicians')
    min_technicians = fields.Char(string='Min Technicians')
    monthly_revenue = fields.Char(string='Monthly Revenue')
    my_services = fields.Char(string='My Services')
    naid_compliant = fields.Char(string='Naid Compliant')
    notification_template_id = fields.Many2one('notification.template')
    operational_settings = fields.Char(string='Operational Settings')
    portal_category = fields.Char(string='Portal Category')
    portal_description = fields.Char(string='Portal Description')
    portal_settings = fields.Char(string='Portal Settings')
    portal_visible = fields.Char(string='Portal Visible')
    price_adjustment = fields.Char(string='Price Adjustment')
    pricing = fields.Char(string='Pricing')
    pricing_rule_ids = fields.One2many('pricing.rule')
    pricing_rules = fields.Char(string='Pricing Rules')
    quality_check_required = fields.Boolean(string='Quality Check Required')
    request_count = fields.Integer(string='Request Count')
    require_customer_approval = fields.Char(string='Require Customer Approval')
    requires_approval = fields.Char(string='Requires Approval')
    requires_equipment = fields.Char(string='Requires Equipment')
    requires_witness = fields.Char(string='Requires Witness')
    res_model = fields.Char(string='Res Model')
    resources = fields.Char(string='Resources')
    revenue_trend = fields.Char(string='Revenue Trend')
    service_category = fields.Char(string='Service Category')
    service_code = fields.Char(string='Service Code')
    service_details = fields.Char(string='Service Details')
    skill_level_required = fields.Boolean(string='Skill Level Required')
    special_tools_required = fields.Boolean(string='Special Tools Required')
    total_revenue = fields.Char(string='Total Revenue')
    type = fields.Selection(string='Type')
    unit_of_measure = fields.Char(string='Unit Of Measure')
    vehicle_type_required = fields.Boolean(string='Vehicle Type Required')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    today = fields.Date()
    today = fields.Date()
    today = fields.Date()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _is_service_item_feature_enabled(self, feature_key):
            """Check if service item feature is enabled in RM Module Configurator""":
            configurator = self.env["rm.module.configurator").search(]
                []
                    ("category", "=", "service_management"),
                    ("config_key", "=", feature_key),
                    ("company_id", "in", [self.env.company.id, False]),

                limit=1,

            return configurator.boolean_value if configurator else True:
        # Configurator visibility controls

    def _compute_configurator_settings(self):
            """Compute configurator settings for UI visibility""":
            for record in self:
                record.show_maintenance_tracking = ()
                    record._is_service_item_feature_enabled()
                        "enable_maintenance_tracking"


                record.show_financial_tracking = ()
                    record._is_service_item_feature_enabled()
                        "enable_financial_tracking"


                record.show_performance_metrics = ()
                    record._is_service_item_feature_enabled()
                        "enable_performance_metrics"



        # ============================================================================
            # STATE MANAGEMENT
        # ============================================================================

    def _compute_completed_count(self):
            for record in self:
                record.completed_count = len(record.completed_ids)


    def _compute_request_count(self):
            for record in self:
                record.request_count = len(record.request_ids)


    def _compute_total_revenue(self):
            for record in self:
                record.total_revenue = sum(record.line_ids.mapped('amount'))


            # ============================================================================
        # COMPUTE METHODS
            # ============================================================================

    def _compute_warranty_status(self):
            """Compute warranty status based on expiry date"""

    def _compute_next_maintenance(self):
            """Calculate next maintenance date"""
            for item in self:
                if item.last_maintenance and item.maintenance_interval:
                    item.next_maintenance = item.last_maintenance + timedelta()
                        days=item.maintenance_interval

                else:
                    item.next_maintenance = False


    def _compute_maintenance_due(self):
            """Check if maintenance is due""":

    def _compute_age(self):
            """Calculate age in months"""

    def name_get(self):
            """Custom name display with category and model"""
            result = []
            for record in self:
                name = record.name
                if record.category:
                    category_name = dict(self._fields["category").selection).get(]
                        record.category

                    name = _("%s (%s)", name, category_name)
                if record.model_number:
                    name = _("%s - %s", name, record.model_number)
                result.append((record.id, name))
            return result

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_mark_available(self):
            """Mark service item as available"""
            self.ensure_one()
            if self.state not in ["draft", "maintenance"]:
                raise UserError()
                    _("Cannot mark item as available from current state")

            self.write({"state": "available"})
            self.message_post(body=_("Service item marked as available"))


    def action_mark_in_use(self):
            """Mark service item as in use"""
            self.ensure_one()
            if self.state != "available":
                raise UserError(_("Only available items can be marked as in use"))
            self.write({"state": "in_use"})
            self.message_post(body=_("Service item marked as in use"))


    def action_send_to_maintenance(self):
            """Send service item to maintenance"""
            self.ensure_one()
            self.write({"state": "maintenance"})
            # Create maintenance request if maintenance module is available:
            if "maintenance.request" in self.env:
                maintenance_request = self.env["maintenance.request").create(]
                    {}
                        "name": _("Maintenance - %s", self.name),
                        "equipment_id": self.id,
                        "request_type": ()
                            "corrective" if self.maintenance_due else "preventive":

                        "description": _("Maintenance required for %s", self.name),:


                self.message_post()
                    body=_()
                        "Service item sent to maintenance. Request created: %s",
                        maintenance_request.name,


                return {}
                    "type": "ir.actions.act_window",
                    "name": _("Maintenance Request"),
                    "res_model": "maintenance.request",
                    "res_id": maintenance_request.id,
                    "view_mode": "form",
                    "target": "current",

            else:
                self.message_post(body=_("Service item sent to maintenance"))


    def action_schedule_maintenance(self):
            """Schedule preventive maintenance"""
            self.ensure_one()
            if "maintenance.request" in self.env:
                return {}
                    "type": "ir.actions.act_window",
                    "name": _("Schedule Maintenance - %s", self.name),
                    "res_model": "maintenance.request",
                    "view_mode": "form",
                    "target": "new",
                    "context": {}
                        "default_name": _("Scheduled Maintenance - %s", self.name),
                        "default_equipment_id": self.id,
                        "default_request_type": "preventive",
                        "default_description": _("Scheduled maintenance for %s", self.name),:


            else:
                raise UserError(_("Maintenance module not available"))


    def action_retire_item(self):
            """Retire service item"""
            self.ensure_one()
            if self.state == "in_use":
                raise UserError(_("Cannot retire item that is currently in use"))
            self.write({"state": "retired", "active": False})
            self.message_post(body=_("Service item retired"))


    def action_view_service_requests(self):
            """View service requests for this item""":
            self.ensure_one()
            return {}
                "type": "ir.actions.act_window",
                "name": _("Service Requests - %s", self.name),
                "res_model": "portal.request",
                "view_mode": "tree,form",
                "domain": [("service_item_id", "=", self.id)],
                "context": {"default_service_item_id": self.id},



    def action_view_maintenance_history(self):
            """View maintenance history"""
            self.ensure_one()
            if "maintenance.request" in self.env:
                return {}
                    "type": "ir.actions.act_window",
                    "name": _("Maintenance History - %s", self.name),
                    "res_model": "maintenance.request",
                    "view_mode": "tree,form",
                    "domain": [("equipment_id", "=", self.id)],
                    "context": {"default_equipment_id": self.id},

            else:
                raise UserError(_("Maintenance module not available"))

        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_maintenance_interval(self):
            """Validate maintenance interval is reasonable"""
            for record in self:
                if record.maintenance_interval < 1 or record.maintenance_interval > 3650:
                    raise ValidationError()
                        _("Maintenance interval must be between 1 and 3650 days")



    def _check_utilization_rate(self):
            """Validate utilization rate is within valid range"""
            for record in self:
                if record.utilization_rate < 0 or record.utilization_rate > 100:
                    raise ValidationError(_("Utilization rate must be between 0% and 100%"))


    def _check_capacity(self):
            """Validate capacity is positive"""
            for record in self:
                if record.capacity < 0:
                    raise ValidationError(_("Capacity cannot be negative"))


    def _check_financial_values(self):
            """Validate financial values are not negative"""
            for record in self:
                if any(:)
                    val < 0
                    for val in [:]
                        record.purchase_cost or 0,
                        record.current_value or 0,
                        record.maintenance_cost or 0,


                    raise ValidationError(_("Financial values cannot be negative"))

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def get_utilization_summary(self):
            """Get utilization summary for reporting""":
            self.ensure_one()
            return {}
                "item_name": self.name,
                "category": self.category,
                "service_type": self.service_type,
                "utilization_rate": self.utilization_rate,
                "efficiency_rating": self.efficiency_rating,
                "state": self.state,
                "maintenance_due": self.maintenance_due,
                "age_months": self.age_months,



    def calculate_depreciated_value(self):
            """Calculate current depreciated value"""
            self.ensure_one()
            if not self.purchase_cost or not self.purchase_date:
                return 0.0
            age_years = self.age_months / 12.0
            depreciation_amount = ()
                self.purchase_cost * (self.depreciation_rate / 100.0) * age_years

            depreciated_value = max(0.0, self.purchase_cost - depreciation_amount)
            return depreciated_value


    def get_maintenance_due_items(self):
            """Get all items with maintenance due"""
            return self.search([("maintenance_due", "=", True), ("state", "!=", "retired")])


    def _check_maintenance_schedules(self):
            """Cron job to check maintenance schedules and create activities"""
            overdue_items = self.search()
                []
                    ("maintenance_due", "=", True),
                    ("state", "not in", ["maintenance", "retired"]),


            for item in overdue_items:
                # Determine assigned user
                assigned_user_id = item.user_id.id or item.assigned_user_id.id
                if not assigned_user_id:
                    # Skip items without assigned users or log warning
                    continue
                # Create maintenance activity
                try:
                    item.activity_schedule()
                        "mail.mail_activity_data_todo",
                        summary=_("Maintenance Due: %s", item.name),
                        note=_()
                            "Service item maintenance is due based on the scheduled interval."

                        user_id=assigned_user_id,
                        date_deadline=fields.Date.today(),

                except Exception
                    # Continue processing other items if activity creation fails:
                    continue
