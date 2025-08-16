# -*- coding: utf-8 -*-

Service Item Management Module

This module provides comprehensive service item management functionality for the Records:
    pass
Management System. It handles equipment, vehicles, tools, and personnel resources used
in records management operations with complete lifecycle tracking, maintenance scheduling,
and performance monitoring.

Key Features
- Multi-category service item management (equipment, vehicles, tools, personnel)
- Complete lifecycle tracking from purchase to retirement
- Maintenance scheduling with interval-based alerts
- Capacity and performance monitoring with utilization tracking
- Financial tracking with purchase cost and depreciation
- Integration with service requests and operational workflows

Business Processes
1. Item Registration: Register new service items with specifications and financial data
2. Assignment Management: Assign items to users, departments, and locations
3. Maintenance Scheduling: Automated maintenance alerts and service tracking
4. Performance Monitoring: Track utilization rates and efficiency ratings
5. Lifecycle Management: Manage item states from draft to retirement
6. Service Integration: Link items to service requests and operational tasks

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from datetime import timedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ServiceItem(models.Model):
    _name = "service.item"
    _description = "Service Item Management"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, category, service_type"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Service Item Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for this service item",:
    
    description = fields.Text(
        string="Description", help="Detailed description of the service item"
    
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True,
    
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this service item",:
    
    active = fields.Boolean(string="Active", default=True,,
    tracking=True)

        # ============================================================================
    # RM MODULE CONFIGURATOR INTEGRATION
        # ============================================================================
    def _is_service_item_feature_enabled(self, feature_key):
        """Check if service item feature is enabled in RM Module Configurator""":
        configurator = self.env["rm.module.configurator").search()
            []
                ("category", "=", "service_management"),
                ("config_key", "=", feature_key),
                ("company_id", "in", [self.env.company.id, False]),
            
            limit=1,
        
        return configurator.boolean_value if configurator else True:
    # Configurator visibility controls
    show_maintenance_tracking = fields.Boolean(
        string="Show Maintenance Tracking",
        compute="_compute_configurator_settings",
        help="Show maintenance tracking fields based on configuration",
    
    show_financial_tracking = fields.Boolean(
        string="Show Financial Tracking",
        compute="_compute_configurator_settings",
        help="Show financial tracking fields based on configuration",
    
    show_performance_metrics = fields.Boolean(
        string="Show Performance Metrics",
        compute="_compute_configurator_settings",
        ,
    help="Show performance metrics based on configuration",
    

    @api.depends("company_id")
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
    state = fields.Selection(
        [)
            ("draft", "Draft"),
            ("available", "Available"),
            ("in_use", "In Use"),
            ("maintenance", "Under Maintenance"),
            ("retired", "Retired"),
        
        string="Status",
        default="draft",
        tracking=True,
        help="Current status of the service item",
    

        # ============================================================================
    # SERVICE CONFIGURATION
        # ============================================================================
    service_type = fields.Selection(
        [)
            ("pickup", "Pickup Service"),
            ("shredding", "Shredding Service"),
            ("destruction", "Destruction Service"),
            ("storage", "Storage Service"),
            ("retrieval", "Document Retrieval"),
            ("transport", "Transport Service"),
            ("scanning", "Scanning Service"),
            ("consultation", "Consultation Service"),
        
        string="Service Type",
        required=True,
        tracking=True,
        help="Type of service this item supports",
    
    category = fields.Selection(
        [)
            ("equipment", "Equipment"),
            ("vehicle", "Vehicle"),
            ("container", "Container"),
            ("tool", "Tool"),
            ("software", "Software"),
            ("personnel", "Personnel"),
        
        string="Category",
        required=True,
        tracking=True,
        help="Category classification of the service item",
    

        # ============================================================================
    # ITEM SPECIFICATIONS
        # ============================================================================
    model_number = fields.Char(
        string="Model Number", help="Manufacturer model number"
    
    serial_number = fields.Char(
        string="Serial Number",
        index=True,
        help="Unique serial number for identification",:
    
    manufacturer = fields.Char(
        string="Manufacturer", help="Equipment or item manufacturer"
    
    purchase_date = fields.Date(
        string="Purchase Date",
        tracking=True,
        help="Date of purchase or acquisition",
    
    warranty_expiry = fields.Date(
        string="Warranty Expiry", tracking=True, help="Warranty expiration date"
    

        # ============================================================================
    # FINANCIAL INFORMATION
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True,
    
    purchase_cost = fields.Monetary(
        string="Purchase Cost",
        currency_field="currency_id",
        help="Original purchase cost",
    
    current_value = fields.Monetary(
        string="Current Value",
        currency_field="currency_id",
        help="Current estimated value",
    
    maintenance_cost = fields.Monetary(
        string="Total Maintenance Cost",
        currency_field="currency_id",
        help="Cumulative maintenance costs",
    
    depreciation_rate = fields.Float(
        string="Annual Depreciation Rate %",
        default=10.0,
        help="Annual depreciation percentage",
    
        # ============================================================================
    # OPERATIONAL STATUS
        # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        tracking=True,
        help="Current physical location",
    
    assigned_user_id = fields.Many2one(
        "res.users",
        string="Assigned To",
        tracking=True,
        help="User currently assigned to this item",
    
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        tracking=True,
        help="Department responsible for this item",:
    

        # ============================================================================
    # MAINTENANCE TRACKING
        # ============================================================================
    last_maintenance = fields.Date(
        string="Last Maintenance",
        tracking=True,
        help="Date of last maintenance service",
    
    next_maintenance = fields.Date(
        string="Next Maintenance",
        compute="_compute_next_maintenance",
        store=True,
        help="Calculated next maintenance date",
    
    maintenance_interval = fields.Integer(
        ,
    string="Maintenance Interval (days)",
        default=90,
        help="Number of days between maintenance services",
    
    maintenance_due = fields.Boolean(
        string="Maintenance Due",
        compute="_compute_maintenance_due",
        store=True,
        help="Whether maintenance is currently due",
    

        # ============================================================================
    # CAPACITY & PERFORMANCE
        # ============================================================================
    capacity = fields.Float(
        string="Capacity", help="Maximum capacity of the service item"
    
    ,
    capacity_unit = fields.Selection(
        [)
            ("kg", "Kilograms"),
            ("pieces", "Pieces"),
            ("hours", "Hours"),
            ("boxes", "Boxes"),
            ("pages", "Pages"),
            ("liters", "Liters"),
            ("cubic_meters", "Cubic Meters"),
        
        string="Capacity Unit",
        default="pieces",
        help="Unit of measurement for capacity",:
    
    utilization_rate = fields.Float(
        string="Utilization Rate %",
        default=0.0,
        ,
    digits=(5, 2),
        help="Current utilization percentage",
    
    efficiency_rating = fields.Selection(
        [)
            ("poor", "Poor"),
            ("fair", "Fair"),
            ("good", "Good"),
            ("excellent", "Excellent"),
        
        string="Efficiency Rating",
        default="good",
        help="Performance efficiency rating",
    

        # ============================================================================
    # COMPUTED STATUS FIELDS
        # ============================================================================
    warranty_status = fields.Selection(
        [)
            ("active", "Active"),
            ("expired", "Expired"),
            ("unknown", "Unknown"),
        
        string="Warranty Status",
        compute="_compute_warranty_status",
        store=True,
        help="Current warranty status",
    
    age_months = fields.Integer(
        ,
    string="Age (Months)",
        compute="_compute_age",
        store=True,
        help="Age of the item in months",
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    service_request_ids = fields.One2many(
        "portal.request",
        "service_item_id",
        string="Service Requests",
        help="Service requests using this item",
    
    maintenance_request_ids = fields.One2many(
        "maintenance.request",
        "equipment_id",
        string="Maintenance Requests",
        help="Maintenance requests for this item",:
    

        # ============================================================================
    # DOCUMENTATION FIELDS
        # ============================================================================
    specifications = fields.Text(
        string="Technical Specifications",
        help="Detailed technical specifications",
    
    operating_instructions = fields.Text(
        string="Operating Instructions",
        help="Instructions for operating the item",:
    
    safety_notes = fields.Text(
        string="Safety Notes", help="Important safety considerations"
    
    notes = fields.Text(string="Internal Notes",,
    help="Internal notes and comments")

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name)),
    
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name)),
    
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    action_activate = fields.Char(string='Action Activate'),
    action_deactivate = fields.Char(string='Action Deactivate'),
    action_duplicate_service = fields.Char(string='Action Duplicate Service'),
    action_view_pricing_history = fields.Char(string='Action View Pricing History'),
    action_view_related_requests = fields.Char(string='Action View Related Requests'),
    activities = fields.Char(string='Activities'),
    activity_state = fields.Selection([), string='Activity State')  # TODO: Define selection options
    adjustment_type = fields.Selection([), string='Adjustment Type')  # TODO: Define selection options
    analytics = fields.Char(string='Analytics'),
    approval_level = fields.Char(string='Approval Level'),
    audit_trail_required = fields.Boolean(string='Audit Trail Required',,
    default=False),
    auto_create_task = fields.Char(string='Auto Create Task'),
    average_completion_time = fields.Float(string='Average Completion Time',,
    digits=(12, 2))
    base_price = fields.Float(string='Base Price',,
    digits=(12, 2))
    button_box = fields.Char(string='Button Box'),
    certificate_required = fields.Boolean(string='Certificate Required',,
    default=False),
    certification_required = fields.Boolean(string='Certification Required',,
    default=False),
    completed_count = fields.Integer(string='Completed Count', compute='_compute_completed_count',,
    store=True),
    compliance = fields.Char(string='Compliance'),
    condition_field = fields.Char(string='Condition Field'),
    condition_operator = fields.Char(string='Condition Operator'),
    condition_value = fields.Char(string='Condition Value'),
    context = fields.Char(string='Context'),
    cost_price = fields.Float(string='Cost Price',,
    digits=(12, 2))
    customer_can_request = fields.Char(string='Customer Can Request'),
    customer_satisfaction = fields.Char(string='Customer Satisfaction'),
    domain = fields.Char(string='Domain'),
    email_confirmation_required = fields.Boolean(string='Email Confirmation Required',,
    default=False),
    equipment_ids = fields.One2many('equipment', 'service_item_id',,
    string='Equipment Ids'),
    estimated_duration = fields.Char(string='Estimated Duration'),
    group_active = fields.Boolean(string='Group Active',,
    default=False),
    group_approval = fields.Char(string='Group Approval'),
    group_category = fields.Char(string='Group Category'),
    group_company = fields.Char(string='Group Company'),
    group_create_date = fields.Date(string='Group Create Date'),
    group_naid = fields.Char(string='Group Naid'),
    group_type = fields.Selection([), string='Group Type')  # TODO: Define selection options
    help = fields.Char(string='Help'),
    high_demand = fields.Char(string='High Demand'),
    inactive = fields.Boolean(string='Inactive',,
    default=False),
    internal_notes = fields.Char(string='Internal Notes'),
    iso_compliant = fields.Char(string='Iso Compliant'),
    last_revenue_date = fields.Date(string='Last Revenue Date'),
    low_revenue = fields.Char(string='Low Revenue'),
    margin_percent = fields.Float(string='Margin Percent',,
    digits=(12, 2))
    max_technicians = fields.Char(string='Max Technicians'),
    min_technicians = fields.Char(string='Min Technicians'),
    monthly_revenue = fields.Char(string='Monthly Revenue'),
    my_services = fields.Char(string='My Services'),
    naid_compliant = fields.Char(string='Naid Compliant'),
    notification_template_id = fields.Many2one('notification.template',,
    string='Notification Template Id'),
    operational_settings = fields.Char(string='Operational Settings'),
    portal_category = fields.Char(string='Portal Category'),
    portal_description = fields.Char(string='Portal Description'),
    portal_settings = fields.Char(string='Portal Settings'),
    portal_visible = fields.Char(string='Portal Visible'),
    price_adjustment = fields.Char(string='Price Adjustment'),
    pricing = fields.Char(string='Pricing'),
    pricing_rule_ids = fields.One2many('pricing.rule', 'service_item_id',,
    string='Pricing Rule Ids'),
    pricing_rules = fields.Char(string='Pricing Rules'),
    quality_check_required = fields.Boolean(string='Quality Check Required',,
    default=False),
    request_count = fields.Integer(string='Request Count', compute='_compute_request_count',,
    store=True),
    require_customer_approval = fields.Char(string='Require Customer Approval'),
    requires_approval = fields.Char(string='Requires Approval'),
    requires_equipment = fields.Char(string='Requires Equipment'),
    requires_witness = fields.Char(string='Requires Witness'),
    res_model = fields.Char(string='Res Model'),
    resources = fields.Char(string='Resources'),
    revenue_trend = fields.Char(string='Revenue Trend'),
    service_category = fields.Char(string='Service Category'),
    service_code = fields.Char(string='Service Code'),
    service_details = fields.Char(string='Service Details'),
    skill_level_required = fields.Boolean(string='Skill Level Required',,
    default=False),
    special_tools_required = fields.Boolean(string='Special Tools Required',,
    default=False),
    total_revenue = fields.Char(string='Total Revenue'),
    type = fields.Selection([), string='Type')  # TODO: Define selection options
    unit_of_measure = fields.Char(string='Unit Of Measure'),
    vehicle_type_required = fields.Boolean(string='Vehicle Type Required',,
    default=False),
    view_mode = fields.Char(string='View Mode'),
    web_ribbon = fields.Char(string='Web Ribbon')

    @api.depends('completed_ids')
    def _compute_completed_count(self):
        for record in self:
            record.completed_count = len(record.completed_ids)

    @api.depends('request_ids')
    def _compute_request_count(self):
        for record in self:
            record.request_count = len(record.request_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_revenue(self):
        for record in self:
            record.total_revenue = sum(record.line_ids.mapped('amount'))
    

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends("purchase_date", "warranty_expiry")
    def _compute_warranty_status(self):
        """Compute warranty status based on expiry date"""
    today = fields.Date.today()
        for item in self:
            if item.warranty_expiry:
                if item.warranty_expiry >= today:
                    item.warranty_status = "active"
                else:
                    item.warranty_status = "expired"
            else:
                item.warranty_status = "unknown"

    @api.depends("last_maintenance", "maintenance_interval")
    def _compute_next_maintenance(self):
        """Calculate next maintenance date"""
        for item in self:
            if item.last_maintenance and item.maintenance_interval:
                item.next_maintenance = item.last_maintenance + timedelta()
                    days=item.maintenance_interval
                
            else:
                item.next_maintenance = False

    @api.depends("next_maintenance")
    def _compute_maintenance_due(self):
        """Check if maintenance is due""":
    today = fields.Date.today()
        for item in self:
            if item.next_maintenance:
                item.maintenance_due = item.next_maintenance <= today
            else:
                item.maintenance_due = False

    @api.depends("purchase_date")
    def _compute_age(self):
        """Calculate age in months"""
    today = fields.Date.today()
        for item in self:
            if item.purchase_date:
                # Calculate difference in months
                months = (today.year - item.purchase_date.year) * 12 + ()
                    today.month - item.purchase_date.month
                
                item.age_months = max(0, months)  # Ensure non-negative
            else:
                item.age_months = 0

    # ============================================================================
        # ODOO FRAMEWORK METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display with category and model"""
        result = [)
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
    @api.constrains("maintenance_interval")
    def _check_maintenance_interval(self):
        """Validate maintenance interval is reasonable"""
        for record in self:
            if record.maintenance_interval < 1 or record.maintenance_interval > 3650:
                raise ValidationError()
                    _("Maintenance interval must be between 1 and 3650 days")
                

    @api.constrains("utilization_rate")
    def _check_utilization_rate(self):
        """Validate utilization rate is within valid range"""
        for record in self:
            if record.utilization_rate < 0 or record.utilization_rate > 100:
                raise ValidationError(_("Utilization rate must be between 0% and 100%"))

    @api.constrains("capacity")
    def _check_capacity(self):
        """Validate capacity is positive"""
        for record in self:
            if record.capacity < 0:
                raise ValidationError(_("Capacity cannot be negative"))

    @api.constrains("purchase_cost", "current_value", "maintenance_cost")
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

    @api.model
    def get_maintenance_due_items(self):
        """Get all items with maintenance due"""
        return self.search([("maintenance_due", "=", True), ("state", "!=", "retired")])

    @api.model
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
))))))))))))))))))))))))))