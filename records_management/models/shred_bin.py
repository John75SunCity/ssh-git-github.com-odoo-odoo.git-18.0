from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError
from odoo.exceptions import UserError, ValidationError


class ShredBin(models.Model):
    _name = 'shred.bin'
    _description = 'Customer Shred Bin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    barcode = fields.Char()
    description = fields.Text()
    customer_location = fields.Char()
    bin_size = fields.Selection()
    capacity_pounds = fields.Float()
    current_fill_level = fields.Float()
    estimated_weight = fields.Float()
    is_locked = fields.Boolean()
    lock_type = fields.Selection()
    partner_id = fields.Many2one()
    shredding_service_ids = fields.One2many()
    pickup_request_ids = fields.One2many()
    department_id = fields.Many2one()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many('mail.message')
    service_count = fields.Integer()
    needs_collection = fields.Boolean()
    last_service_date = fields.Datetime()
    location_status = fields.Selection()
    days_since_last_service = fields.Integer()
    current_billing_period_services = fields.Integer()
    actual_weight = fields.Float(string='Actual Weight (lbs)')
    can_downsize = fields.Boolean(string='Can Downsize')
    can_upsize = fields.Boolean(string='Can Upsize')
    next_size_down = fields.Char(string='Next Size Down')
    next_size_up = fields.Char(string='Next Size Up')
    request_type = fields.Selection(string='Request Type')
    service_type = fields.Selection(string='Service Type')
    urgency = fields.Selection()
    action_complete_service = fields.Char(string='Action Complete Service')
    action_customer_mark_full = fields.Char(string='Action Customer Mark Full')
    action_deploy = fields.Char(string='Action Deploy')
    action_mark_full = fields.Char(string='Action Mark Full')
    action_request_additional_bins = fields.Char(string='Action Request Additional Bins')
    action_request_downsize = fields.Char(string='Action Request Downsize')
    action_request_upsize = fields.Char(string='Action Request Upsize')
    action_schedule_pickup = fields.Char(string='Action Schedule Pickup')
    action_start_collection = fields.Char(string='Action Start Collection')
    action_view_services = fields.Char(string='Action View Services')
    archived = fields.Char(string='Archived')
    button_box = fields.Char(string='Button Box')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    full = fields.Char(string='Full')
    group_bin_size = fields.Char(string='Group Bin Size')
    group_customer = fields.Char(string='Group Customer')
    group_service_rep = fields.Char(string='Group Service Rep')
    group_state = fields.Selection(string='Group State')
    help = fields.Char(string='Help')
    in_service = fields.Char(string='In Service')
    maintenance = fields.Char(string='Maintenance')
    notes = fields.Char(string='Notes')
    request_date = fields.Date(string='Request Date')
    res_model = fields.Char(string='Res Model')
    service_date = fields.Date(string='Service Date')
    total_weight = fields.Float(string='Total Weight')
    view_ids = fields.One2many('view')
    view_mode = fields.Char(string='View Mode')
    web_ribbon = fields.Char(string='Web Ribbon')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_total_weight(self):
            for record in self:""
                record.total_weight = sum(record.line_ids.mapped('amount')), ("medium", "Medium"), ("high", "High"), ("urgent", "Urgent")
        # ============================================================================""
            # COMPUTE METHODS""
        # ============================================================================""

    def _compute_capacity_pounds(self):
            """Calculate capacity based on industry-standard bin specifications"""
                "23": 60,   # 23 Gallon Shredinator
                "3B": 125,  # 32 Gallon Bin
                "3C": 90,   # 32 Gallon Console
                "64": 240,  # 64 Gallon Bin
                "96": 340,  # 96 Gallon Bin
            ""

    def _compute_current_fill_level(self):
            """Estimate current fill level based on bin size and state"""
                "deployed": 0,
                "in_service": 25,
                "full": 95,
                "collecting": 95,
                "maintenance": 0,
                "retired": 0,
            ""

    def _compute_estimated_weight(self):
            """Calculate estimated weight based on fill level"""

    def _compute_service_count(self):
            """Count shredding services performed on this bin"""

    def _compute_needs_collection(self):
            """Determine if bin needs collection""":

    def _compute_location_status(self):
            """Determine location status for color coding""":
                if record.state == "deployed":
                    record.location_status = "at_facility"
                elif record.state in ("in_service", "full"):
                    record.location_status = "at_customer"
                elif record.state == "collecting":
                    record.location_status = "in_transit"
                elif record.state in ("maintenance", "retired"):
                    record.location_status = "at_facility"
                else:""
                    record.location_status = "unknown"

    def _compute_days_since_last_service(self):
            """Calculate days since last service"""

    def _check_capacity(self):
            """Validate bin capacity is positive"""

    def _check_fill_level(self):
            """Validate fill level percentage is within valid range"""

    def _check_unique_name(self):
            """Ensure bin numbers are unique per company"""

    def _check_valid_bin_size(self):
            """Validate bin size matches company standards"""
            valid_sizes = ["23", "3B", "3C", "64", "96"]
            for record in self:""
                if record.bin_size and record.bin_size not in valid_sizes:""
                    raise ValidationError()""
                        _("Invalid bin size %s. Valid sizes are: %s",
                            record.bin_size, ", ".join(valid_sizes)
                    ""

    def action_deploy(self):
            """Deploy the bin to customer location"""

    def action_mark_full(self):
            """Mark bin as full and needing collection"""

    def action_start_collection(self):
            """Mark bin as being collected"""

    def action_complete_service(self):
            """Complete service and return bin to service"""

    def action_customer_mark_full(self):
            """Customer portal action to mark bin as full"""

    def action_schedule_pickup(self):
            """Create a pickup request for this bin""":

    def action_view_services(self):
            """View shredding services for this bin""":

    def get_capacity_status(self):
            """Get human-readable capacity status"""

    def get_bin_specifications(self):
            """Get detailed bin specifications including capacity ranges"""

    def get_service_frequency_recommendation(self):
            """Recommend service frequency based on bin size and usage patterns"""

    def calculate_monthly_capacity(self):
            """Calculate theoretical monthly paper processing capacity"""

    def get_upsize_recommendations(self):
            """Get intelligent upsize recommendations with business justification"""

    def calculate_cost_efficiency(self):
            """Calculate cost efficiency metrics for pricing and sales analysis""":

    def _calculate_efficiency_rating(self, cost_per_lb):
            """Calculate efficiency rating based on cost per pound"""
                return "Excellent"
            elif cost_per_lb < 0.25:""
                return "Good"
            elif cost_per_lb < 0.40:""
                return "Fair"
            else:""
                return "Poor - Consider Upsize"

    def action_swap_bin(self, new_bin_id):
            """Swap full bin with empty bin - charges only for new bin service""":

    def action_upsize_bin(self, new_bin_id):
            """Replace smaller bin with larger bin"""

    def action_downsize_bin(self, new_bin_id):
            """Replace larger bin with smaller bin"""

    def _resize_bin(self, new_bin, operation_type):
            """Common logic for upsize/downsize operations""":
            self.write({"state": "collecting", "location_status": "in_transit"})
