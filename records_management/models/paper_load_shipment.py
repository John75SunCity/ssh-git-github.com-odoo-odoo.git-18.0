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
    Paper Load Shipment Model
    Manages paper bale shipments for recycling operations with complete tracking,:
    pass
logistics coordination, and NAID compliance for document destruction certificates.""":"
Author: Records Management System""
Version: 18.0.6.0.0""
License: LGPL-3""
    from odoo import models, fields, api, _""
from odoo.exceptions import UserError, ValidationError""
    class PaperLoadShipment(models.Model):""
""
        Paper Load Shipment Management""
    ""
    Tracks paper bale shipments from pickup to delivery with complete""
        chain of custody for NAID compliance and environmental responsibility.:""
    ""
    _name = "paper.load.shipment"
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
""
    _description = "paper.load.shipment"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "paper.load.shipment"
    ""
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "Paper Load Shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"
""
        # ============================================================================ """"
    # CORE IDENTIFICATION FIELDS"""""
        # ============================================================================ """"
    name = fields.Char("""""
        string="Name",
        required=True,""
        tracking=True,""
        index=True,""
        help="Shipment identification name"
    ""
""
    company_id = fields.Many2one(""
        "res.company",
        string="Company",
        default=lambda self: self.env.company,""
        required=True""
    ""
""
    user_id = fields.Many2one(""
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,""
        tracking=True,""
        help="User responsible for this shipment":
    ""
""
    active = fields.Boolean(""
        string="Active",
        default=True""
    ""
""
    sequence = fields.Integer(""
        string="Sequence",
        default=10,""
        help="Order sequence for processing":
    ""
""
        # ============================================================================ """"
    # SHIPMENT IDENTIFICATION"""""
        # ============================================================================ """"
    shipment_number = fields.Char("""""
        string="Shipment Number",
        required=True,""
        index=True,""
        copy=False,""
        help="Unique shipment identifier"
    ""
""
    reference_number = fields.Char(""
        string="Reference Number",
        help="External reference number"
    ""
""
        # ============================================================================ """"
    # STATE MANAGEMENT"""""
        # ============================================================================ """"
    ,"""""
    state = fields.Selection([))""
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("loaded", "Loaded"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ""
""
        # ============================================================================ """"
    # WEIGHT AND VOLUME TRACKING"""""
        # ============================================================================ """"
    total_weight = fields.Float("""""
    string="Total Weight (lbs)",
        digits=(12, 2),""
        help="Total weight of all bales in pounds"
    ""
""
    estimated_volume = fields.Float(""
    string="Estimated Volume (CF)",
        digits=(12, 3),""
        help="Estimated volume in cubic feet"
    ""
""
    actual_weight = fields.Float(""
    string="Actual Weight (lbs)",
        digits=(12, 2),""
        help="Actual weight at destination"
    

        # ============================================================================
    # PAPER SPECIFICATIONS"
        # ============================================================================ """"
    paper_grade = fields.Selection([))"""""
        ('high', 'High Grade'),"
        ('medium', 'Medium Grade'),"
        ('low', 'Low Grade'),"
        ('mixed', 'Mixed Grade')"
    ""
""
    contamination_level = fields.Selection([))""
        ('none', 'No Contamination'),"
        ('low', 'Low Contamination'),"
        ('medium', 'Medium Contamination'),"
        ('high', 'High Contamination')"
    ""
""
        # ============================================================================ """"
    # LOCATIONS AND LOGISTICS"""""
        # ============================================================================ """"
    pickup_location_id = fields.Many2one("""""
        "records.location",
        string="Pickup Location",
        help="Location where bales are collected"
    ""
""
    delivery_location_id = fields.Many2one(""
        "records.location",
        string="Delivery Location",
        help="Final destination for recycling":
    ""
""
    current_location_id = fields.Many2one(""
        "records.location",
        string="Current Location",
        help="Current shipment location"
    ""
""
    ,""
    transportation_mode = fields.Selection([))""
        ('truck', 'Truck'),"
        ('rail', 'Rail'),"
        ('ship', 'Ship'),"
        ('air', 'Air')"
    ""
""
        # ============================================================================ """"
    # DATES AND SCHEDULING"""""
        # ============================================================================ """"
    date_created = fields.Datetime("""""
        string="Created Date",
        default=fields.Datetime.now,""
        readonly=True""
    ""
""
    date_modified = fields.Datetime(""
        string="Modified Date",
        readonly=True""
    ""
""
    scheduled_pickup_date = fields.Datetime(""
        string="Scheduled Pickup",
        tracking=True""
    ""
""
    actual_pickup_date = fields.Datetime(""
        string="Actual Pickup",
        tracking=True""
    ""
""
    scheduled_delivery_date = fields.Datetime(""
        string="Scheduled Delivery",
        tracking=True""
    ""
""
    actual_delivery_date = fields.Datetime(""
        string="Actual Delivery",
        tracking=True""
    ""
""
        # ============================================================================ """"
    # BUSINESS RELATIONSHIPS"""""
        # ============================================================================ """"
    partner_id = fields.Many2one("""""
        "res.partner",
        string="Customer",
        ,""
    domain="[('is_company', '=', True))",
        help="Customer whose materials are being shipped"
    ""
""
    vendor_id = fields.Many2one(""
        "res.partner",
        string="Vendor/Recycler",
        help="Recycling facility receiving the materials"
    ""
""
    driver_id = fields.Many2one(""
        "res.partner",
        string="Driver",
        ,""
    domain="[('is_company', '=', False))",
        help="Driver responsible for transport":
    ""
""
    carrier_id = fields.Many2one(""
        "res.partner",
        string="Carrier",
        help="Transportation company"
    ""
""
        # ============================================================================ """"
    # PAPER BALES RELATIONSHIP"""""
        # ============================================================================ """"
    bale_ids = fields.One2many("""""
        "paper.bale",
        "load_shipment_id",
        string="Paper Bales",
        help="Bales included in this shipment"
    ""
""
    bale_count = fields.Integer(""
        string="Bale Count",
        compute="_compute_bale_metrics",
        store=True
    

        # ============================================================================
    # DELIVERY AND CONFIRMATION
        # ============================================================================
    ,
    delivery_confirmation_method = fields.Selection([))
        ('signature', 'Signature'),
        ('email', 'Email Confirmation'),
        ('phone', 'Phone Confirmation'),
        ('portal', 'Portal Confirmation')
    

    delivery_priority = fields.Selection([))
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    
"
    environmental_conditions = fields.Selection([))""
        ('normal', 'Normal'),"
        ('controlled', 'Controlled Environment'),"
        ('hazmat', 'Hazardous Materials'),"
        ('refrigerated', 'Refrigerated')"
    ""
""
        # ============================================================================ """"
    # QUALITY AND SATISFACTION"""""
        # ============================================================================ """"
    customer_satisfaction_rating = fields.Selection([))"""""
        ('1', 'Very Poor'),"
        ('2', 'Poor'),"
        ('3', 'Average'),"
        ('4', 'Good'),"
        ('5', 'Excellent')"
    ""
""
    quality_check_passed = fields.Boolean(""
        string="Quality Check Passed",
        default=False,""
        tracking=True""
    ""
""
    inspection_notes = fields.Text(""
        string="Inspection Notes",
        help="Quality inspection details"
    ""
""
        # ============================================================================ """"
    # FINANCIAL INFORMATION"""""
        # ============================================================================ """"
    currency_id = fields.Many2one("""""
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True""
    ""
""
    estimated_cost = fields.Monetary(""
        string="Estimated Cost",
        currency_field='currency_id',"
        help="Estimated transportation cost"
    ""
""
    actual_cost = fields.Monetary(""
        string="Actual Cost",
        currency_field='currency_id',"
        help="Final transportation cost"
    ""
""
    revenue = fields.Monetary(""
        string="Revenue",
        currency_field='currency_id',"
        help="Revenue from recycled materials"
    ""
""
        # ============================================================================ """"
    # DESCRIPTIVE FIELDS"""""
        # ============================================================================ """"
    description = fields.Text("""""
        string="Description",
        help="General shipment description"
    ""
""
    notes = fields.Text(""
        string="Internal Notes",
        help="Internal processing notes"
    ""
""
    special_instructions = fields.Text(""
        string="Special Instructions",
        help="Special handling requirements"
    ""
""
    delivery_instructions = fields.Text(""
        string="Delivery Instructions",
        help="Specific delivery requirements"
    ""
""
        # ============================================================================ """"
    # MANIFEST AND MOBILE TRACKING"""""
        # ============================================================================ """"
    manifest_generated = fields.Boolean("""""
        string='Manifest Generated',"
        default=False,""
        tracking=True,""
        help="Indicates if shipping manifest has been generated":
    ""
""
    mobile_manifest = fields.Char(""
        string='Mobile Manifest ID',"
        tracking=True,""
        help="Mobile tracking identifier"
    ""
""
        # ============================================================================ """"
    # MAIL THREAD FRAMEWORK FIELDS"""""
        # ============================================================================ """"
    activity_ids = fields.One2many("""""
        "mail.activity",
        "res_id",
        string="Activities",
        ,""
    domain=lambda self: [("res_model", "= """", self._name))"
    ""
""
    message_follower_ids = fields.One2many(""
        """"mail.followers",
        "res_id",
        string="Followers",
        ,""
    domain=lambda self: [("res_model", "= """", self._name))"
    ""
""
    message_ids = fields.One2many(""
        """"mail.message",
        "res_id",
        string="Messages",
        ,""
    domain=lambda self: [("model", "= """", self._name))"
    action_add_bales_to_load = fields.Char(string='"""
""""
        """Compute bale count and total weight"""
"""
""""
"""    def action_confirm(self):"
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
        """Confirm the shipment"""
"""            raise UserError(_("Cannot confirm shipment without bales"))"
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
        self.message_post(body=_("Shipment confirmed"))
""
    def action_load_bales(self):""
        """Mark bales as loaded"""
"""            raise UserError(_("Can only load confirmed shipments"))"
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
        self.message_post(body=_("Bales loaded for shipment")):
    def action_start_transit(self):""
        """Start transit"""
"""            raise UserError(_("Can only start transit for loaded shipments")):"
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
        self.message_post(body=_("Shipment in transit"))
""
    def action_deliver(self):""
        """Mark as delivered"""
"""            raise UserError(_("Can only deliver shipments in transit"))"
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
        self.message_post(body=_("Shipment delivered"))
""
    def action_complete(self):""
        """Complete the shipment"""
"""            raise UserError(_("Can only complete delivered shipments"))"
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
            raise UserError(_("Cannot complete shipment without delivery confirmation"))
""
        self.write({'state': 'completed'})"
        self.message_post(body=_("Shipment completed"))
""
    def action_cancel(self):""
        """Cancel the shipment"""
"""            raise UserError(_("Cannot cancel delivered or completed shipment"))"
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
        self.message_post(body=_("Shipment cancelled"))
""
    # ============================================================================""
        # MANIFEST AND DOCUMENT GENERATION""
    # ============================================================================""
    def action_generate_manifest(self):""
        """Generate shipping manifest"""
"""            raise UserError(_("Cannot generate manifest without bales"))"
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
        self.message_post(body=_("Shipping manifest generated"))
""
        return {}""
            "type": "ir.actions.report",
            "report_name": "records_management.paper_shipment_manifest_template",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        ""
""
    def action_view_bales(self):""
        """View associated bales"""
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
""""
            "name": _("Paper Bales"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_shipment_id", "= """""
            """"context": {"default_load_shipment_id": self.id},"
        ""
""
    def action_create_invoice(self):""
        """Create invoice for shipment"""
"""            raise UserError(_("Cannot create invoice without customer"))"
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
        # Create invoice logic would go here""
        self.message_post(body=_("Invoice creation requested"))
""
        return {}""
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "context": {}
                "default_partner_id": self.partner_id.id,
                "default_move_type": "out_invoice",
            ""
        ""
""
    def action_schedule_pickup(self):""
        """Schedule pickup appointment"""
"""            "type": "ir.actions.act_window","
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
            "name": _("Schedule Pickup"),
            "res_model": "pickup.request",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_partner_id": self.partner_id.id,
                "default_shipment_id": self.id,
            ""
        ""
""
    # ============================================================================""
        # VALIDATION METHODS""
    # ============================================================================""
    @api.constrains('total_weight', 'actual_weight')""
    def _check_weights(self):""
        """Validate weights are positive"""
"""                raise ValidationError(_("Total weight must be positive"))"
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
                raise ValidationError(_("Actual weight must be positive"))
""
    @api.constrains('scheduled_pickup_date', 'scheduled_delivery_date')""
    def _check_scheduled_dates(self):""
        """Validate scheduled date sequence"""
"""
""""
"""                        "Pickup date cannot be after delivery date""
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
    def _check_unique_shipment_number(self):""
        """Ensure shipment number is unique"""
"""                    ('shipment_number', '= """
""""
                    ('"""id', '!= """
""""
""""""                        "Shipment number %s already exists",
                        record.shipment_number""
                    ""
""
    # ============================================================================ """"
        # ORM METHODS""""""
    # ============================================================================ """"
    @api.model_create_multi""""""
    def create(self, vals_list):""
        """Override create to set shipment number and tracking"""
    """"
    """    def write(self, vals):"
        """Override write for modification tracking"""
""""
""""
"""                    "State changed to %s","
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
""""
""""
""""
""""
    def unlink(self):""
        """Override unlink with validation"""
""""
""""
"""                    "Cannot delete shipment %s in state %s","
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
    def name_get(self):""
        """Custom name display"""
""""
""""
"""                name = _("%s (%s)", name, record.shipment_number)"
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
""""
""""
""""
""""
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):""
        """Enhanced search by name, shipment number, or reference"""
""""
""""
"""    def get_weight_breakdown(self):"
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
        """Get weight breakdown by paper grade"""
""""
""""
    """"
        """Get comprehensive delivery status"""
""""
""""
    """    def _calculate_progress_percentage(self):"
        """Calculate shipment progress percentage"""
""""
""""
""""
        """Sync shipment status with carrier API"""
""""
""""
    """    def create_naid_audit_trail(self):"
        """Create NAID compliance audit trail"""
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
"""
"""