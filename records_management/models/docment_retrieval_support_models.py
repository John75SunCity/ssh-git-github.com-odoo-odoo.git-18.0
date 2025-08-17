from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class DocumentRetrievalItem(models.Model):
    _name = 'file.retrieval.metrics.summary'
    _description = 'Document Retrieval Metrics'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    work_order_id = fields.Many2one()
    sequence = fields.Integer(string='Sequence')
    document_id = fields.Many2one('records.document')
    container_id = fields.Many2one('records.container')
    location_id = fields.Many2one('records.location')
    item_type = fields.Selection()
    description = fields.Text(string='Item Description')
    barcode = fields.Char(string='Barcode/ID')
    status = fields.Selection()
    estimated_time = fields.Float(string='Estimated Time (hours)')
    actual_time = fields.Float(string='Actual Time (hours)')
    difficulty_level = fields.Selection()
    retrieval_date = fields.Datetime(string='Retrieved Date')
    retrieved_by_id = fields.Many2one('hr.employee')
    condition_notes = fields.Text(string='Condition Notes')
    special_handling = fields.Boolean(string='Special Handling Required')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_issues = fields.Text(string='Quality Issues')
    completeness_verified = fields.Boolean()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    action_locate_item = fields.Char(string='Action Locate Item')
    action_package_item = fields.Char(string='Action Package Item')
    action_retrieve_item = fields.Char(string='Action Retrieve Item')
    active_items = fields.Char(string='Active Items')
    context = fields.Char(string='Context')
    group_partner = fields.Char(string='Group Partner')
    group_priority = fields.Selection(string='Group Priority')
    group_status = fields.Selection(string='Group Status')
    group_work_order = fields.Char(string='Group Work Order')
    help = fields.Char(string='Help')
    high_priority = fields.Selection(string='High Priority')
    pending_items = fields.Char(string='Pending Items')
    res_model = fields.Char(string='Res Model')
    very_high_priority = fields.Selection(string='Very High Priority')
    view_mode = fields.Char(string='View Mode')
    name = fields.Char(string='Team Name', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    team_lead_id = fields.Many2one('hr.employee')
    member_ids = fields.Many2many()
    specialization = fields.Selection()
    active_orders_count = fields.Integer()
    completed_orders_count = fields.Integer()
    average_completion_time = fields.Float()
    efficiency_rating = fields.Float()
    max_concurrent_orders = fields.Integer(string='Max Concurrent Orders')
    current_workload = fields.Float()
    available_from = fields.Float()
    available_to = fields.Float()
    working_days = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    service_type = fields.Selection()
    currency_id = fields.Many2one()
    base_fee = fields.Monetary(string='Base Fee')
    per_document_fee = fields.Monetary()
    per_hour_fee = fields.Monetary(string='Per Hour Fee')
    per_box_fee = fields.Monetary(string='Per Box Fee')
    volume_threshold = fields.Integer(string='Volume Threshold')
    volume_discount_percent = fields.Float(string='Volume Discount (%)')
    priority_level = fields.Selection()
    priority_multiplier = fields.Float()
    delivery_included = fields.Boolean(string='Delivery Included')
    delivery_fee = fields.Monetary(string='Delivery Fee')
    delivery_radius_km = fields.Float(string='Delivery Radius (km)')
    scanning_fee = fields.Monetary(string='Scanning Fee')
    ocr_fee = fields.Monetary(string='OCR Fee')
    digital_delivery_fee = fields.Monetary()
    same_day_multiplier = fields.Float()
    next_day_multiplier = fields.Float()
    valid_from = fields.Date(string='Valid From')
    valid_to = fields.Date(string='Valid To')
    partner_id = fields.Many2one('res.partner')
    customer_tier = fields.Selection()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    equipment_type = fields.Selection()
    status = fields.Selection()
    location_id = fields.Many2one('records.location')
    assigned_to_id = fields.Many2one('hr.employee')
    model = fields.Char(string='Model')
    serial_number = fields.Char(string='Serial Number')
    purchase_date = fields.Date(string='Purchase Date')
    warranty_expiry = fields.Date(string='Warranty Expiry')
    last_maintenance = fields.Date(string='Last Maintenance')
    next_maintenance = fields.Date(string='Next Maintenance')
    maintenance_notes = fields.Text(string='Maintenance Notes')
    usage_hours = fields.Float(string='Total Usage Hours')
    current_work_order_id = fields.Many2one()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    name = fields.Char(string='Metric Name', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    date = fields.Date()
    work_order_id = fields.Many2one()
    team_id = fields.Many2one('document.retrieval.team')
    employee_id = fields.Many2one('hr.employee')
    documents_retrieved = fields.Integer(string='Documents Retrieved')
    hours_worked = fields.Float(string='Hours Worked')
    accuracy_rate = fields.Float(string='Accuracy Rate (%)')
    customer_satisfaction = fields.Float()
    currency_id = fields.Many2one()
    documents_per_hour = fields.Float()
    cost_per_document = fields.Monetary()
    revenue_generated = fields.Monetary()
    profit_margin = fields.Float(string='Profit Margin (%)')
    errors_count = fields.Integer(string='Errors Count')
    rework_required = fields.Integer(string='Rework Required')
    on_time_delivery = fields.Boolean(string='On Time Delivery')
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    state = fields.Selection()

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_order_counts(self):
            """Compute order counts for the team""":
            for team in self:
                team_member_ids = team.member_ids.mapped("user_id.id")
                active_count = self.env["file.retrieval.work.order").search_count(]
                    [("user_id", "in", team_member_ids), ("state", "=", "active")]

                completed_count = self.env[]
                    "file.retrieval.work.order"

                    []
                        ("user_id", "in", team_member_ids),
                        ("state", "=", "inactive"),



                team.active_orders_count = active_count
                team.completed_orders_count = completed_count


    def _compute_performance(self):
            """Compute performance metrics"""
            for team in self:
                if team.member_ids:
                    team_member_ids = team.member_ids.mapped("user_id.id")
                    completed_orders = self.env[]
                        "file.retrieval.work.order"

                        []
                            ("user_id", "in", team_member_ids),
                            ("state", "=", "inactive"),
                            ("completion_date", "!=", False),



                    if completed_orders:
                        total_days = 0
                        efficiency_scores = []

                        for order in completed_orders:
                            if order.requested_date and order.completion_date:
                                completion_days = ()
                                    order.completion_date.date() - order.requested_date

                                total_days += completion_days

                            if order.estimated_hours and order.actual_hours:
                                efficiency = ()
                                    order.estimated_hours / order.actual_hours

                                efficiency_scores.append()
                                    min(efficiency, 200)


                        team.average_completion_time = total_days / len(completed_orders)
                        team.efficiency_rating = ()
                            sum(efficiency_scores) / len(efficiency_scores)
                            if efficiency_scores:
                            else 0

                    else:
                        team.average_completion_time = 0
                        team.efficiency_rating = 0
                else:
                    team.average_completion_time = 0
                    team.efficiency_rating = 0


    def _compute_workload(self):
            """Compute current workload percentage"""
            for team in self:
                if team.max_concurrent_orders > 0:
                    team.current_workload = ()
                        team.active_orders_count / team.max_concurrent_orders

                else:
                    team.current_workload = 0



    def _compute_efficiency(self):
            """Compute documents per hour efficiency"""
            for metric in self:
                if metric.hours_worked > 0:
                    metric.documents_per_hour = ()
                        metric.documents_retrieved / metric.hours_worked

                else:
                    metric.documents_per_hour = 0

