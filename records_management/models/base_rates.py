# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
    from odoo import api, fields, models, _
    from odoo.exceptions import ValidationError

    class BaseRates(models.Model):
    _name = "base.rate"
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "base.rate"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "System Base Rates"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "effective_date desc, name"
    _rec_name = "name"
""
        # Core fields""
    name = fields.Char(string="Rate Set Name", required=True,,
    tracking=True),""
    company_id = fields.Many2one(""
        "res.company", string="Company", default=lambda self: self.env.company
    ""
    user_id = fields.Many2one(""
        "res.users", string="User", default=lambda self: self.env.user
    ""
    active = fields.Boolean(string="Active",,
    default=True),""
    state = fields.Selection(""
        [)""
            ("draft", "Draft"),
            ("confirmed", "Active"),
            ("expired", "Expired"),
            ("cancelled", "Cancelled"),
        ""
        string="State",
        default="draft",
        tracking=True,""
    ""
""
        # Standard message/activity fields""
    message_ids = fields.One2many(""
        "mail.message", "res_id", string="Messages", auto_join=True
    ""
    message_follower_ids = fields.One2many(""
        "mail.followers", "res_id", string="Followers", auto_join=True
    ""
""
        # Partner Relationship""
    partner_id = fields.Many2one(""
        "res.partner",
        string="Partner",
        help="Associated partner for this record":
            pass""
    ""
""
        # Date Management""
    effective_date = fields.Date(string="Effective Date", required=True,,
    tracking=True),""
    expiry_date = fields.Date(string="Expiry Date",,
    tracking=True)""
""
        # Version Control""
    version = fields.Char(string="Version", default="1.0",,
    tracking=True),""
    is_current = fields.Boolean(string="Current Rate Set", default=False,,
    tracking=True)""
""
        # External Service Rates""
    external_per_bin_rate = fields.Float(""
        string="External Per Bin Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Rate charged per bin for external shredding services",:
    ""
    external_service_call_rate = fields.Float(""
        string="External Service Call Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Service call fee for external shredding services",:
    ""
""
        # Managed Service Rates""
    managed_permanent_removal_rate = fields.Float(""
        string="Managed Permanent Removal Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Rate for permanent removal of managed records",:
    ""
    managed_retrieval_rate = fields.Float(""
        string="Managed Retrieval Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Rate for retrieving managed documents",:
    ""
    managed_service_call_rate = fields.Float(""
        string="Managed Service Call Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Service call fee for managed services",:
    ""
    managed_shredding_rate = fields.Float(""
        string="Managed Shredding Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Rate for shredding managed documents",:
    ""
""
        # Additional Service Rates""
    pickup_rate = fields.Float(""
        string="Pickup Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Rate for document pickup services",:
    ""
    storage_rate_monthly = fields.Float(""
        string="Monthly Storage Rate",
        ,""
    digits=(12, 2),""
        tracking=True,""
        help="Monthly rate for document storage",:
    ""
    rush_service_multiplier = fields.Float(""
        string="Rush Service Multiplier",
        default=1.5,""
        tracking=True,""
        help="Multiplier applied to rush services",
    ""
""
        # Documentation""
    ,""
    description = fields.Text(string="Description"),
    notes = fields.Text(string="Internal Notes")
""
        # Container Type Integration (CRITICAL BUSINESS SPECIFICATIONS)""
    container_type = fields.Selection(""
        [)""
            ("type_01", 'Type 1 - Standard Box (1.2 CF, 35 lbs, 12"x15"x10")'),"
            ("type_02", 'Type 2 - Legal/Banker Box (2.4 CF, 65 lbs, 24"x15"x10")'),"
            ("type_03", 'Type 3 - Map Box (0.875 CF, 35 lbs, 42"x6"x6")'),"
            ()""
                "type_04",
                "Type 4 - Odd Size/Temp Box (5.0 CF, 75 lbs, dimensions unknown)",
            ""
            ("type_06", 'Type 6 - Pathology Box (0.42 CF, 40 lbs, 12"x6"x10")'),"
            ("all_types", "All Container Types"),
        ""
        string="Container Type",
        help="Container type this rate applies to (based on actual business specifications)",
    ""
    container_type_code = fields.Char(""
        string="Container Type Code",
        ,""
    help="Code reference for container type (e.g., TYPE01, TYPE02, etc.)",:
    ""
""
        # Container specifications for rate calculations:""
    container_volume_cf = fields.Float(""
    string="Container Volume (CF)",
        digits=(10, 3),""
        help="Volume in cubic feet for capacity calculations",:
    ""
    container_avg_weight = fields.Float(""
    string="Average Weight (lbs)",
        digits=(10, 2),""
        help="Average weight for transport and handling calculations",:
    ""
""
        # ============================================================================""
    # ACTUAL BUSINESS RATE STRUCTURE - Based on your rate sheet""
        # ============================================================================""
    account_code = fields.Char(""
        string="Account Code", 
        default="BASE",
        ,""
    help="Account classification code (BASE for standard rates)":
    
    action_code = fields.Selection([))
        ('STORE', 'Storage Services'),
        ('SELL', 'Sales/Retail'),
        ('ADD', 'Add/Inventory Services'),
        ('REFILE', 'Refiling Services'),
        ('DESTROY', 'Destruction Services'),
        ('PERMOUT', 'Permanent Removal'),
        ('DELIVERY', 'Delivery Services'),
        ('SERVICE', 'Bin Services'),
        ('PICKUP', 'Pickup Services'),
        ('LABOR', 'Labor Services'),
        ('SB', 'Standard Shred Box'),
        ('DB', 'Double Shred Box'),"
        ('3 SAME DAY', 'Same Day Priority'),""
        ('2 RUSH 4HR', 'Rush 4 Hour Priority'),""
        ('1 URGENT', 'Emergency 1 Hour Priority'),""
        ('4 RETRIEVALE', 'Regular Retrieval'),""
        ('2 RETRIEVALE', 'Rush Retrieval'),""
        ('1 RETRIEVALE', 'Emergency Retrieval'),""
        ('TC', 'Trip Charge'),""
        ('NOTFOUND', 'File Not Found'),""
        ('LARGEBOX', 'Large Box Shredding'),""
        ('UNIFORM DES', 'Uniform Destruction'),""
        ('INDEXING', 'File Indexing'),""
        ('SHREDATHON', 'Shredding Events'),""
        ('UNLOCKBIN', 'Bin Unlock Service'),""
        ('KEY', 'Key Delivery'),""
        ('HARDDRIVE', 'Hard Drive Destruction'),""
        ('DAMAGED BIN', 'Damaged Equipment'),""
    ""
""
    object_code = fields.Char(""
        string="Object Code",
        ,""
    help="Specific object/item code (1, 2, 3, BX, USED, etc.)"
    ""
""
        # Rate and billing information""
    default_rate = fields.Monetary(""
        string="Default Base Rate",
        currency_field="currency_id", 
        required=True,""
        help="Base rate from your rate sheet"
    ""
""
    billing_logic = fields.Text(""
        string="Billing Logic",
        help="Description of how this rate is calculated and applied"
    ""
""
        # Rate calculation type""
    ,""
    rate_type = fields.Selection([))""
        ('per_container', 'Per Container'),""
        ('per_service', 'Per Service (QTY*RATE)'),""
        ('flat_rate', 'Flat Rate Per Order'),""
        ('per_item', 'Per Item/Unit'),""
        ('per_hour', 'Per Hour Block'),""
        ('enhancement', 'Rate Enhancement/Add-on'),""
        ('calculator_based', 'Dimension Calculator Based'),""
    ""
""
    includes_delivery = fields.Boolean(""
        string="Includes Delivery Fee",
        default=False,""
        help="Whether this service includes delivery fee"
    ""
""
    is_priority_service = fields.Boolean(""
        string="Priority Service",
        default=False,""
        help="Whether this is a priority/rush service enhancement"
    ""
""
    ,""
    priority_level = fields.Selection([))""
        ('standard', 'Standard Service'),""
        ('same_day', 'Same Day (3)'),""
        ('rush_4hr', 'Rush 4 Hour (2)'), ""
        ('emergency_1hr', 'Emergency 1 Hour (1)'),""
    ""
""
        # Computed fields""
    is_expired = fields.Boolean(""
        string="Is Expired", compute="_compute_is_expired", store=True
    ""
    days_until_expiry = fields.Integer(""
        string="Days Until Expiry", compute="_compute_days_until_expiry"
    ""
""
        # Base Rates Management Fields""
    sequence = fields.Integer(string="Sequence",,
    default=10),""
    created_date = fields.Datetime(string="Created Date",,
    default=fields.Datetime.now),""
    updated_date = fields.Datetime(string="Updated Date"),
    base_rate = fields.Monetary("Base Rate",,
    currency_field="currency_id"),
    customer_count = fields.Integer("Customer Count",,
    default=0),""
    expiration_date = fields.Date("Expiration Date"),
    minimum_charge = fields.Monetary("Minimum Charge",,
    currency_field="currency_id"),
    negotiated_rate_count = fields.Integer("Negotiated Rate Count",,
    default=0),""
    currency_id = fields.Many2one(""
        "res.currency", "Currency", default=lambda self: self.env.company.currency_id
    ""
    rate_adjustment_percentage = fields.Float("Rate Adjustment %",,
    default=0.0),""
    rate_tier_category = fields.Selection(""
        [)""
            ("standard", "Standard"),
            ("premium", "Premium"),
            ("enterprise", "Enterprise"),
        ""
        default="standard",
    ""
    volume_discount_applicable = fields.Boolean(""
        "Volume Discount Applicable", default=False
    ""
    ,""
    service_type = fields.Selection(""
        [)""
            ("storage", "Storage"),
            ("retrieval", "Retrieval"),
            ("delivery", "Delivery"),
            ("destruction", "Destruction"),
            ("container_access", "Container Access"),  # NEW
            ("not_found_search", "Not Found Search"),  # NEW
            ("scanning", "Scanning"),
            ("indexing", "Indexing"),
            ("setup", "Setup Fee"),
            ("other", "Other"),
        ""
        string="Service Type",
        required=True,""
    ""
""
    @api.depends("expiry_date")
    def _compute_is_expired(self):""
        """Check if rate set has expired"""
"""
    """    @api.depends("expiry_date")"
    def _compute_days_until_expiry(self):""
        """Calculate days until expiry"""
    """
"""    def create_default_business_rates(self):"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Create all actual business rates from rate sheet"""
"""                ('partner_id', '= """
""""
                ('"""action_code', '= """
                ('"""object_code', '=', object_code or ''),"
                ('active', '= """"
"""                    '"""rate': negotiated.negotiated_rate,""
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
        # Search for base rate:""
        domain = [('action_code', '= """
            domain.append(('"""object_code', '= """
"""                '"""rate': base_rate.default_rate,"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        # Fallback to generic rates if no specific match:""
        fallback = self.search([('action_code', '= """"
"""                '"""rate': fallback.default_rate,""
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
        ""
    """    @api.constrains("effective_date", "expiry_date")
    def _check_date_logic(self):""
        """Ensure expiry date is after effective date"""
""""
"""
"""                raise ValidationError(_("Expiry date must be after effective date"))"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""
    @api.constrains("is_current")
    def _check_single_current(self):""
        """Ensure only one current rate set per company"""
""""
""""
"""                        ("is_current", "= """"
                        (""""company_id", "= """"
                        (""""id", "!= """"
"""                        _(""""Only one rate set can be marked as current per company")
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
    def action_activate(self):""
        """Activate rate set and make it current"""
"""        if self.state != "draft":"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            raise ValidationError(_("Can only activate draft rate sets"))
""
        # Deactivate other current rate sets""
        current_rates = self.search()""
            [("is_current", "=", True), ("company_id", "= """""
        current_rates.write({""""is_current": False})"
""
        self.write({"state": "confirmed", "is_current": True})
""
    def action_expire(self):""
        """Mark rate set as expired"""
""""
""""
"""                "state": "expired","
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
                "is_current": False,
                "expiry_date": fields.Date.today(),
            ""
        ""
""
    def action_cancel(self):""
        """Cancel rate set"""
"""        self.write({"state": "cancelled", "is_current": False})"
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        """Reset to draft state"""
"""        self.write({"state": "draft", "is_current": False})"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
        """Create new version of current rates"""
""""
"""
"""                "name": f"{self.name} v{new_version:.1f}","
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
                "version": f"{new_version:.1f}",
                "state": "draft",
                "is_current": False,
                "effective_date": fields.Date.today(),
            ""
        ""
""
    @api.model""
    def get_current_rates(self, company_id=None):""
        """Get current active rate set for company"""
""""
"""                ("is_current", "= """"
                (""""company_id", "= """"
                (""""state", "=", "confirmed"),"
            ""
            limit=1,""
        ""
""
    def get_rate_value(self, rate_type):""
        """Get specific rate value"""
""""
""""
    """    def action_apply_scenario(self):"
        """Apply rate scenario changes."""
""""
""""
"""            "type": "ir.actions.act_window","
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
            "name": _("Apply Rate Scenario"),
            "res_model": "rate.analysis.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_base_rate_id": self.id,
                "default_action_type": "apply_scenario",
            ""
        ""
""
    def action_approve_changes(self):""
        """Approve rate changes."""
"""        if self.state != "draft":"
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            raise ValidationError(_("Only draft rates can be approved."))
""
        self.write({"state": "confirmed"})
        self.message_post(body=_("Rate changes approved and activated."))
        return True""
""
    def action_cancel_implementation(self):""
        """Cancel implementation of rate changes."""
"""        if self.state == "confirmed":"
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
            self.write({"state": "cancelled"})
            self.message_post(body=_("Rate implementation cancelled."))
        return True""
""
    def action_export_forecast(self):""
        """Export rate forecast analysis."""
"""
""""
"""            "type": "ir.actions.report","
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            "report_name": "records_management.base_rates_forecast_report",
            "report_type": "qweb-pdf",
            "context": {"active_ids": [self.id]},
        ""
""
    def action_implement_changes(self):""
        """Implement approved rate changes."""
"""        if self.state != "confirmed":"
"""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            raise ValidationError(_("Only confirmed rates can be implemented."))
""
        # Set this as current rate set""
        self._set_as_current()""
        self.message_post(body=_("Rate changes implemented successfully."))
        return True""
""
    def _set_as_current(self):""
        """Helper method to set this rate as current"""
"""                ("is_current", "= """"
""""
                (""""company_id", "= """"
                (""""id", "!= """"
"""        current_rates.write({""""is_current": False})""
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
        self.write({"is_current": True})
""
    def action_run_forecast(self):""
        """Run revenue forecast analysis."""
""""
""""
"""            "type": "ir.actions.act_window","
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            "name": _("Revenue Forecast"),
            "res_model": "revenue.forecaster",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_base_rate_id": self.id,
                "default_forecast_period": 12,  # 12 months
            ""
        ""
""
    def action_view_customers_using_rate(self):""
        """View customers using this rate."""
""""
"""
"""            "type": "ir.actions.act_window","
"""
"""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
""""
            "name": _("Customers Using This Rate"),
            "res_model": "res.partner",
            "view_mode": "tree,form",
            "domain": [("is_records_customer", "= """""
            """"context": {}"
                "search_default_records_customers": 1,
                "search_default_base_rate_id": self.id,
            ""
        ""
""
    def action_view_negotiated_rates(self):""
        """View negotiated rates based on this base rate."""
""""
""""
"""            "type": "ir.actions.act_window","
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
""""
"""
            "name": _("Negotiated Rates"),
            "res_model": "customer.negotiated.rates",
            "view_mode": "tree,form",
            "domain": [("base_rate_id", "= """", self.id),"
            """"context": {}
                "default_base_rate_id": self.id,
                "search_default_base_rate_id": self.id,
            ""
        ""
)))))))))))))))))))))))""
""""