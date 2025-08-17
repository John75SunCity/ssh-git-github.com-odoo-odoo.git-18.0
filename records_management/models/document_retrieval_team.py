from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo import models, fields, api


class DocumentRetrievalTeam(models.Model):
    _name = 'document.retrieval.team'
    _description = 'Document Retrieval Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
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
    retrieval_metrics_ids = fields.One2many()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    state = fields.Selection()
    action_activate_team = fields.Char(string='Action Activate Team')
    action_deactivate_team = fields.Char(string='Action Deactivate Team')
    action_mark_available = fields.Char(string='Action Mark Available')
    action_mark_busy = fields.Char(string='Action Mark Busy')
    action_view_performance_metrics = fields.Char(string='Action View Performance Metrics')
    action_view_team_members = fields.Char(string='Action View Team Members')
    action_view_work_order = fields.Char(string='Action View Work Order')
    action_view_work_orders = fields.Char(string='Action View Work Orders')
    active_workorders = fields.Char(string='Active Workorders')
    after_hours_available = fields.Char(string='After Hours Available')
    availability = fields.Char(string='Availability')
    available = fields.Char(string='Available')
    avg_completion_time_days = fields.Char(string='Avg Completion Time Days')
    avg_items_per_day = fields.Char(string='Avg Items Per Day')
    avg_retrieval_time_hours = fields.Char(string='Avg Retrieval Time Hours')
    busy = fields.Char(string='Busy')
    button_box = fields.Char(string='Button Box')
    can_access_offsite_locations = fields.Char(string='Can Access Offsite Locations')
    can_work_after_hours = fields.Char(string='Can Work After Hours')
    can_work_weekends = fields.Char(string='Can Work Weekends')
    capacity_info = fields.Char(string='Capacity Info')
    context = fields.Char(string='Context')
    current_location_id = fields.Many2one('current.location')
    current_orders = fields.Char(string='Current Orders')
    current_workorder_ids = fields.One2many('current.workorder')
    customer_satisfaction_score = fields.Char(string='Customer Satisfaction Score')
    date_joined = fields.Char(string='Date Joined')
    description = fields.Char(string='Description')
    domain = fields.Char(string='Domain')
    efficiency_metrics = fields.Char(string='Efficiency Metrics')
    emergency_teams = fields.Char(string='Emergency Teams')
    equipment = fields.Char(string='Equipment')
    has_heavy_lifting_tools = fields.Char(string='Has Heavy Lifting Tools')
    has_ladder_equipment = fields.Char(string='Has Ladder Equipment')
    has_mobile_scanner = fields.Char(string='Has Mobile Scanner')
    has_safety_equipment = fields.Char(string='Has Safety Equipment')
    has_tablet_device = fields.Char(string='Has Tablet Device')
    help = fields.Char(string='Help')
    id = fields.Char(string='Id')
    inactive = fields.Boolean(string='Inactive')
    internal_notes = fields.Char(string='Internal Notes')
    is_emergency_team = fields.Char(string='Is Emergency Team')
    item_count = fields.Integer(string='Item Count')
    max_container_access_height = fields.Char(string='Max Container Access Height')
    member_count = fields.Integer(string='Member Count')
    next_available_date = fields.Date(string='Next Available Date')
    notes = fields.Char(string='Notes')
    partner_id = fields.Many2one('res.partner')
    performance = fields.Char(string='Performance')
    priority_level = fields.Char(string='Priority Level')
    productivity_metrics = fields.Char(string='Productivity Metrics')
    res_model = fields.Char(string='Res Model')
    role = fields.Char(string='Role')
    schedule = fields.Char(string='Schedule')
    scheduled_date = fields.Date(string='Scheduled Date')
    shift_end_time = fields.Float(string='Shift End Time')
    shift_start_time = fields.Float(string='Shift Start Time')
    specialized_tools = fields.Char(string='Specialized Tools')
    standard_equipment = fields.Char(string='Standard Equipment')
    success_rate_percentage = fields.Char(string='Success Rate Percentage')
    team_code = fields.Char(string='Team Code')
    team_info = fields.Char(string='Team Info')
    team_leader_id = fields.Many2one('team.leader')
    team_members = fields.Char(string='Team Members')
    total_containers_accessed = fields.Char(string='Total Containers Accessed')
    total_items_retrieved = fields.Char(string='Total Items Retrieved')
    type = fields.Selection(string='Type')
    unavailable = fields.Char(string='Unavailable')
    vehicle_id = fields.Many2one('vehicle')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')
    weekend_available = fields.Char(string='Weekend Available')
    working_hours = fields.Char(string='Working Hours')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_item_count(self):
            for record in self:
                record.item_count = len(record.item_ids)


    def _compute_member_count(self):
            for record in self:
                record.member_count = len(record.member_ids)


    def _compute_total_containers_accessed(self):
            for record in self:
                record.total_containers_accessed = sum(record.line_ids.mapped('amount'))


    def _compute_total_items_retrieved(self):
            for record in self:
                record.total_items_retrieved = sum(record.line_ids.mapped('amount')),
            ('active', 'Active'),
            ('inactive', 'Inactive'),
            ('archived', 'Archived'),

            help='Current status of the record'

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_order_counts(self):
            """Compute order counts for the team""":
            for team in self:
                team_member_ids = team.member_ids.mapped("user_id.id")
                # Count active work orders
                active_count = self.env["file.retrieval.work.order").search_count(]
                    []
                        ("state", "in", ["draft", "in_progress"]),
                        ("team_id", "=", team.id),


                completed_count = self.env[]
                    "file.retrieval.work.order"
                ).search_count(
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
                    ).search(
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
