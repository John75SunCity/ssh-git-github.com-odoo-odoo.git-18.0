# -*- coding: utf-8 -*-

Paper Load Shipment Model

Manages paper bale shipments for recycling operations with complete tracking,:
    pass
logistics coordination, and NAID compliance for document destruction certificates.""":"
Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperLoadShipment(models.Model):

        Paper Load Shipment Management
    
    Tracks paper bale shipments from pickup to delivery with complete
        chain of custody for NAID compliance and environmental responsibility.:


    _name = "paper.load.shipment"
    _description = "Paper Load Shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Name",
        required=True,
        tracking=True,
        index=True,
        help="Shipment identification name"
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="User responsible for this shipment":
    

    active = fields.Boolean(
        string="Active",
        default=True
    

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for processing":
    

        # ============================================================================
    # SHIPMENT IDENTIFICATION
        # ============================================================================
    shipment_number = fields.Char(
        string="Shipment Number",
        required=True,
        index=True,
        copy=False,
        help="Unique shipment identifier"
    

    reference_number = fields.Char(
        string="Reference Number",
        help="External reference number"
    

        # ============================================================================
    # STATE MANAGEMENT
        # ============================================================================
    ,
    state = fields.Selection([))
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("loaded", "Loaded"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    

        # ============================================================================
    # WEIGHT AND VOLUME TRACKING
        # ============================================================================
    total_weight = fields.Float(
        ,
    string="Total Weight (lbs)",
        digits=(12, 2),
        help="Total weight of all bales in pounds"
    

    estimated_volume = fields.Float(
        ,
    string="Estimated Volume (CF)",
        digits=(12, 3),
        help="Estimated volume in cubic feet"
    

    actual_weight = fields.Float(
        ,
    string="Actual Weight (lbs)",
        digits=(12, 2),
        help="Actual weight at destination"
    

        # ============================================================================
    # PAPER SPECIFICATIONS
        # ============================================================================
    paper_grade = fields.Selection([))
        ('high', 'High Grade'),
        ('medium', 'Medium Grade'),
        ('low', 'Low Grade'),
        ('mixed', 'Mixed Grade')
    

    contamination_level = fields.Selection([))
        ('none', 'No Contamination'),
        ('low', 'Low Contamination'),
        ('medium', 'Medium Contamination'),
        ('high', 'High Contamination')
    

        # ============================================================================
    # LOCATIONS AND LOGISTICS
        # ============================================================================
    pickup_location_id = fields.Many2one(
        "records.location",
        string="Pickup Location",
        help="Location where bales are collected"
    

    delivery_location_id = fields.Many2one(
        "records.location",
        string="Delivery Location",
        help="Final destination for recycling":
    

    current_location_id = fields.Many2one(
        "records.location",
        string="Current Location",
        help="Current shipment location"
    

    ,
    transportation_mode = fields.Selection([))
        ('truck', 'Truck'),
        ('rail', 'Rail'),
        ('ship', 'Ship'),
        ('air', 'Air')
    

        # ============================================================================
    # DATES AND SCHEDULING
        # ============================================================================
    date_created = fields.Datetime(
        string="Created Date",
        default=fields.Datetime.now,
        readonly=True
    

    date_modified = fields.Datetime(
        string="Modified Date",
        readonly=True
    

    scheduled_pickup_date = fields.Datetime(
        string="Scheduled Pickup",
        tracking=True
    

    actual_pickup_date = fields.Datetime(
        string="Actual Pickup",
        tracking=True
    

    scheduled_delivery_date = fields.Datetime(
        string="Scheduled Delivery",
        tracking=True
    

    actual_delivery_date = fields.Datetime(
        string="Actual Delivery",
        tracking=True
    

        # ============================================================================
    # BUSINESS RELATIONSHIPS
        # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        ,
    domain="[('is_company', '=', True))",
        help="Customer whose materials are being shipped"
    

    vendor_id = fields.Many2one(
        "res.partner",
        string="Vendor/Recycler",
        help="Recycling facility receiving the materials"
    

    driver_id = fields.Many2one(
        "res.partner",
        string="Driver",
        ,
    domain="[('is_company', '=', False))",
        help="Driver responsible for transport":
    

    carrier_id = fields.Many2one(
        "res.partner",
        string="Carrier",
        help="Transportation company"
    

        # ============================================================================
    # PAPER BALES RELATIONSHIP
        # ============================================================================
    bale_ids = fields.One2many(
        "paper.bale",
        "load_shipment_id",
        string="Paper Bales",
        help="Bales included in this shipment"
    

    bale_count = fields.Integer(
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
    

    environmental_conditions = fields.Selection([))
        ('normal', 'Normal'),
        ('controlled', 'Controlled Environment'),
        ('hazmat', 'Hazardous Materials'),
        ('refrigerated', 'Refrigerated')
    

        # ============================================================================
    # QUALITY AND SATISFACTION
        # ============================================================================
    customer_satisfaction_rating = fields.Selection([))
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    

    quality_check_passed = fields.Boolean(
        string="Quality Check Passed",
        default=False,
        tracking=True
    

    inspection_notes = fields.Text(
        string="Inspection Notes",
        help="Quality inspection details"
    

        # ============================================================================
    # FINANCIAL INFORMATION
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    

    estimated_cost = fields.Monetary(
        string="Estimated Cost",
        currency_field='currency_id',
        help="Estimated transportation cost"
    

    actual_cost = fields.Monetary(
        string="Actual Cost",
        currency_field='currency_id',
        help="Final transportation cost"
    

    revenue = fields.Monetary(
        string="Revenue",
        currency_field='currency_id',
        help="Revenue from recycled materials"
    

        # ============================================================================
    # DESCRIPTIVE FIELDS
        # ============================================================================
    description = fields.Text(
        string="Description",
        help="General shipment description"
    

    notes = fields.Text(
        string="Internal Notes",
        help="Internal processing notes"
    

    special_instructions = fields.Text(
        string="Special Instructions",
        help="Special handling requirements"
    

    delivery_instructions = fields.Text(
        string="Delivery Instructions",
        help="Specific delivery requirements"
    

        # ============================================================================
    # MANIFEST AND MOBILE TRACKING
        # ============================================================================
    manifest_generated = fields.Boolean(
        string='Manifest Generated',
        default=False,
        tracking=True,
        help="Indicates if shipping manifest has been generated":
    

    mobile_manifest = fields.Char(
        string='Mobile Manifest ID',
        tracking=True,
        help="Mobile tracking identifier"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    action_add_bales_to_load = fields.Char(string='Action Add Bales To Load'),
    action_create_invoice = fields.Char(string='Action Create Invoice'),
    action_generate_manifest = fields.Char(string='Action Generate Manifest'),
    action_mark_delivered = fields.Char(string='Action Mark Delivered'),
    action_mark_in_transit = fields.Char(string='Action Mark In Transit'),
    action_mark_paid = fields.Char(string='Action Mark Paid'),
    action_ready_for_pickup = fields.Char(string='Action Ready For Pickup'),
    action_schedule_pickup = fields.Char(string='Action Schedule Pickup'),
    action_view_manifest = fields.Char(string='Action View Manifest'),
    action_view_weight_breakdown = fields.Char(string='Action View Weight Breakdown'),
    bale_number = fields.Char(string='Bale Number'),
    bales = fields.Char(string='Bales'),
    button_box = fields.Char(string='Button Box'),
    card = fields.Char(string='Card'),
    cardboard_count = fields.Integer(string='Cardboard Count', compute='_compute_cardboard_count',,
    store=True),
    cardboard_weight = fields.Float(string='Cardboard Weight',,
    digits=(12, 2))
    company_signature_date = fields.Date(string='Company Signature Date'),
    delivered = fields.Char(string='Delivered'),
    delivery_notes = fields.Char(string='Delivery Notes'),
    destination_address = fields.Char(string='Destination Address'),
    display_name = fields.Char(string='Display Name'),
    draft = fields.Char(string='Draft'),
    driver_license = fields.Char(string='Driver License'),
    driver_name = fields.Char(string='Driver Name'),
    driver_phone = fields.Char(string='Driver Phone'),
    driver_signature_date = fields.Date(string='Driver Signature Date'),
    gps_delivery_location = fields.Char(string='Gps Delivery Location'),
    gps_pickup_location = fields.Char(string='Gps Pickup Location'),
    grade_breakdown = fields.Char(string='Grade Breakdown'),
    group_customer = fields.Char(string='Group Customer'),
    group_driver = fields.Char(string='Group Driver'),
    group_pickup_date = fields.Date(string='Group Pickup Date'),
    group_status = fields.Selection([), string='Group Status')  # TODO: Define selection options
    help = fields.Char(string='Help'),
    in_transit = fields.Char(string='In Transit'),
    invoice_amount = fields.Float(string='Invoice Amount',,
    digits=(12, 2))
    invoice_date = fields.Date(string='Invoice Date'),
    invoiced = fields.Char(string='Invoiced'),
    load_number = fields.Char(string='Load Number'),
    load_summary = fields.Char(string='Load Summary'),
    manifest_date = fields.Date(string='Manifest Date'),
    manifest_number = fields.Char(string='Manifest Number'),
    mixed_paper_count = fields.Integer(string='Mixed Paper Count', compute='_compute_mixed_paper_count',,
    store=True),
    mixed_paper_weight = fields.Float(string='Mixed Paper Weight',,
    digits=(12, 2))
    mobile_entry = fields.Char(string='Mobile Entry'),
    mobile_integration = fields.Char(string='Mobile Integration'),
    paid = fields.Char(string='Paid'),
    payment_amount = fields.Float(string='Payment Amount',,
    digits=(12, 2))
    payment_due_date = fields.Date(string='Payment Due Date'),
    payment_notes = fields.Char(string='Payment Notes'),
    payment_received_date = fields.Date(string='Payment Received Date'),
    payment_tracking = fields.Char(string='Payment Tracking'),
    pickup_date = fields.Date(string='Pickup Date'),
    pickup_info = fields.Char(string='Pickup Info'),
    pickup_time = fields.Float(string='Pickup Time',,
    digits=(12, 2))
    production_date = fields.Date(string='Production Date'),
    ready_pickup = fields.Char(string='Ready Pickup'),
    res_model = fields.Char(string='Res Model'),
    scheduled = fields.Char(string='Scheduled'),
    search_view_id = fields.Many2one('search.view',,
    string='Search View Id'),
    signatures = fields.Char(string='Signatures'),
    signed_by = fields.Char(string='Signed By'),
    status = fields.Selection([('new', 'New'), ('in_progress', 'In Progress')), ('completed', 'Completed')], string='Status', default='new')
    system_info = fields.Char(string='System Info'),
    this_month = fields.Char(string='This Month'),
    this_week = fields.Char(string='This Week'),
    today = fields.Char(string='Today'),
    total_weight_kg = fields.Char(string='Total Weight Kg'),
    total_weight_lbs = fields.Char(string='Total Weight Lbs'),
    transportation = fields.Char(string='Transportation'),
    transportation_company = fields.Char(string='Transportation Company'),
    truck_info = fields.Char(string='Truck Info'),
    truck_visualization = fields.Char(string='Truck Visualization'),
    view_mode = fields.Char(string='View Mode'),
    weighed_by = fields.Char(string='Weighed By'),
    weight_lbs = fields.Char(string='Weight Lbs'),
    white_paper_count = fields.Integer(string='White Paper Count', compute='_compute_white_paper_count',,
    store=True),
    white_paper_weight = fields.Float(string='White Paper Weight',,
    digits=(12, 2))

    @api.depends('cardboard_ids')
    def _compute_cardboard_count(self):
        for record in self:
            record.cardboard_count = len(record.cardboard_ids)

    @api.depends('mixed_paper_ids')
    def _compute_mixed_paper_count(self):
        for record in self:
            record.mixed_paper_count = len(record.mixed_paper_ids)

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_weight_kg(self):
        for record in self:
            record.total_weight_kg = sum(record.line_ids.mapped('amount'))

    @api.depends('line_ids', 'line_ids.amount')  # TODO: Adjust field dependencies
    def _compute_total_weight_lbs(self):
        for record in self:
            record.total_weight_lbs = sum(record.line_ids.mapped('amount'))

    @api.depends('white_paper_ids')
    def _compute_white_paper_count(self):
        for record in self:
            record.white_paper_count = len(record.white_paper_ids)
    

        # ============================================================================
    # COMPUTED FIELDS
        # ============================================================================
    @api.depends('bale_ids', 'bale_ids.weight')
    def _compute_bale_metrics(self):
        """Compute bale count and total weight"""
        for record in self:
            bales = record.bale_ids
            record.bale_count = len(bales)
            record.total_weight = sum(bales.mapped('weight'))

    # ============================================================================
        # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the shipment"""
        self.ensure_one()
        if not self.bale_ids:
            raise UserError(_("Cannot confirm shipment without bales"))

        self.write({'state': 'confirmed'})
        self.message_post(body=_("Shipment confirmed"))

    def action_load_bales(self):
        """Mark bales as loaded"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Can only load confirmed shipments"))

        self.write({'state': 'loaded'})
        self.message_post(body=_("Bales loaded for shipment")):
    def action_start_transit(self):
        """Start transit"""
        self.ensure_one()
        if self.state != 'loaded':
            raise UserError(_("Can only start transit for loaded shipments")):
        self.write({)}
            'state': 'in_transit',
            'actual_pickup_date': fields.Datetime.now()
        
        self.message_post(body=_("Shipment in transit"))

    def action_deliver(self):
        """Mark as delivered"""
        self.ensure_one()
        if self.state != 'in_transit':
            raise UserError(_("Can only deliver shipments in transit"))

        self.write({)}
            'state': 'delivered',
            'actual_delivery_date': fields.Datetime.now()
        
        self.message_post(body=_("Shipment delivered"))

    def action_complete(self):
        """Complete the shipment"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Can only complete delivered shipments"))

        if not self.actual_delivery_date:
            raise UserError(_("Cannot complete shipment without delivery confirmation"))

        self.write({'state': 'completed'})
        self.message_post(body=_("Shipment completed"))

    def action_cancel(self):
        """Cancel the shipment"""
        self.ensure_one()
        if self.state in ['delivered', 'completed'):
            raise UserError(_("Cannot cancel delivered or completed shipment"))

        self.write({'state': 'cancelled'})
        self.message_post(body=_("Shipment cancelled"))

    # ============================================================================
        # MANIFEST AND DOCUMENT GENERATION
    # ============================================================================
    def action_generate_manifest(self):
        """Generate shipping manifest"""
        self.ensure_one()
        if not self.bale_ids:
            raise UserError(_("Cannot generate manifest without bales"))

        self.write({'manifest_generated': True})
        self.message_post(body=_("Shipping manifest generated"))

        return {}
            "type": "ir.actions.report",
            "report_name": "records_management.paper_shipment_manifest_template",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        

    def action_view_bales(self):
        """View associated bales"""
        self.ensure_one()
        return {}
            "type": "ir.actions.act_window",
            "name": _("Paper Bales"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("load_shipment_id", "=", self.id)],
            "context": {"default_load_shipment_id": self.id},
        

    def action_create_invoice(self):
        """Create invoice for shipment""":
        self.ensure_one()
        if not self.partner_id:
            raise UserError(_("Cannot create invoice without customer"))

        # Create invoice logic would go here
        self.message_post(body=_("Invoice creation requested"))

        return {}
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "account.move",
            "view_mode": "form",
            "target": "current",
            "context": {}
                "default_partner_id": self.partner_id.id,
                "default_move_type": "out_invoice",
            
        

    def action_schedule_pickup(self):
        """Schedule pickup appointment"""
        self.ensure_one()
        return {}
            "type": "ir.actions.act_window",
            "name": _("Schedule Pickup"),
            "res_model": "pickup.request",
            "view_mode": "form",
            "target": "new",
            "context": {}
                "default_partner_id": self.partner_id.id,
                "default_shipment_id": self.id,
            
        

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('total_weight', 'actual_weight')
    def _check_weights(self):
        """Validate weights are positive"""
        for record in self:
            if record.total_weight and record.total_weight < 0:
                raise ValidationError(_("Total weight must be positive"))
            if record.actual_weight and record.actual_weight < 0:
                raise ValidationError(_("Actual weight must be positive"))

    @api.constrains('scheduled_pickup_date', 'scheduled_delivery_date')
    def _check_scheduled_dates(self):
        """Validate scheduled date sequence"""
        for record in self:
            if record.scheduled_pickup_date and record.scheduled_delivery_date:
                if record.scheduled_pickup_date > record.scheduled_delivery_date:
                    raise ValidationError(_())
                        "Pickup date cannot be after delivery date"
                    

    @api.constrains('shipment_number')
    def _check_unique_shipment_number(self):
        """Ensure shipment number is unique"""
        for record in self:
            if record.shipment_number:
                existing = self.search([)]
                    ('shipment_number', '=', record.shipment_number),
                    ('id', '!=', record.id)
                
                if existing:
                    raise ValidationError(_())
                        "Shipment number %s already exists",
                        record.shipment_number
                    

    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set shipment number and tracking"""
        for vals in vals_list:
            if not vals.get('shipment_number'):
                vals['shipment_number'] = self.env['ir.sequence').next_by_code(]
                    'paper.load.shipment'
                
            
            if not vals.get('date_modified'):
    vals['date_modified'] = fields.Datetime.now()

        return super().create(vals_list)

    def write(self, vals):
        """Override write for modification tracking""":
    vals['date_modified'] = fields.Datetime.now()
        result = super().write(vals)
        
        for record in self:
            if 'state' in vals:
                record.message_post(body=_())
                    "State changed to %s",
                    dict(record._fields['state'].selection)[record.state]
                
        
        return result

    def unlink(self):
        """Override unlink with validation"""
        for record in self:
            if record.state in ['in_transit', 'delivered', 'completed']:
                raise UserError(_())
                    "Cannot delete shipment %s in state %s",
                    record.name,
                    record.state
                
        return super().unlink()

    # ============================================================================
        # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.name
            if record.shipment_number:
                name = _("%s (%s)", name, record.shipment_number)
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search by name, shipment number, or reference"""
        args = args or []
        domain = []
        if name:
            domain = []
                '|', '|',
                ('name', operator, name),
                ('shipment_number', operator, name),
                ('reference_number', operator, name)
            
        return self._search()
            domain + args,
            limit=limit,
            access_rights_uid=name_get_uid
        

    # ============================================================================
        # REPORTING METHODS
    # ============================================================================
    def get_weight_breakdown(self):
        """Get weight breakdown by paper grade"""
        self.ensure_one()
        breakdown = {}
        
        for bale in self.bale_ids:
            grade = bale.paper_grade or 'unspecified'
            if grade not in breakdown:
                breakdown[grade] = {'count': 0, 'weight': 0.0}
            
            breakdown[grade]['count'] += 1
            breakdown[grade]['weight'] += bale.weight or 0.0
        
        return breakdown

    def get_delivery_status(self):
        """Get comprehensive delivery status"""
        self.ensure_one()
        
        status_info = {}
            'shipment_number': self.shipment_number,
            'state': self.state,
            'progress_percentage': self._calculate_progress_percentage(),
            'estimated_delivery': self.scheduled_delivery_date,
            'current_location': self.current_location_id.name if self.current_location_id else None,:
        
        
        return status_info

    def _calculate_progress_percentage(self):
        """Calculate shipment progress percentage"""
        state_progress = {}
            'draft': 0,
            'confirmed': 20,
            'loaded': 40,
            'in_transit': 70,
            'delivered': 90,
            'completed': 100,
            'cancelled': 0,
        
        return state_progress.get(self.state, 0)

    # ============================================================================
        # INTEGRATION METHODS
    # ============================================================================
    def sync_with_carrier_api(self):
        """Sync shipment status with carrier API"""
        for record in self:
            if record.carrier_id and record.shipment_number:
                # Integration logic would go here
                # This could sync with FedEx, UPS, etc.
                pass

    def create_naid_audit_trail(self):
        """Create NAID compliance audit trail"""
        self.ensure_one()
        if self.state == 'completed':
            audit_vals = {}
                'name': _('Paper Shipment Completed: %s', self.shipment_number),
                'model_name': self._name,
                'record_id': self.id,
                'action': 'shipment_completed',
                'user_id': self.env.user.id,
                'timestamp': fields.Datetime.now(),
                'details': _('Shipment %s completed with %d bales', 
                            self.shipment_number, self.bale_count
            
            
            self.env['naid.audit.log'].create(audit_vals)


    """")))))))))))))))))))))))))