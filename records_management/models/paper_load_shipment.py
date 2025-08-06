# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PaperLoadShipment(models.Model):
    _name = "paper.load.shipment"
    _description = "Paper Load Shipment"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name desc"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Name", required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", string="Company", default=lambda self: self.env.company)
    user_id = fields.Many2one("res.users", string="Assigned User", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("active", "Active"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("completed", "Completed"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", tracking=True)
    
    status = fields.Selection([
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('loaded', 'Loaded'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered')
    ], string="Shipment Status", default='pending')
    
    processing_status = fields.Selection([
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('processed', 'Processed'),
        ('error', 'Error')
    ], string="Processing Status", default='queued')

    # ============================================================================
    # SHIPMENT DETAILS
    # ============================================================================
    shipment_number = fields.Char(string="Shipment Number", required=True)
    reference_number = fields.Char(string="Reference Number")
    
    # Weight and Volume
    total_weight = fields.Float(string="Total Weight", digits=(10, 2))
    estimated_volume = fields.Float(string="Estimated Volume", digits=(10, 2))
    actual_weight = fields.Float(string="Actual Weight", digits=(10, 2))
    
    # Paper specifications
    paper_grade = fields.Selection([
        ('high', 'High Grade'),
        ('medium', 'Medium Grade'),
        ('low', 'Low Grade'),
        ('mixed', 'Mixed Grade')
    ], string="Paper Grade")
    
    contamination_level = fields.Selection([
        ('none', 'No Contamination'),
        ('low', 'Low Contamination'),
        ('medium', 'Medium Contamination'),
        ('high', 'High Contamination')
    ], string="Contamination Level", default='none')

    # ============================================================================
    # LOCATIONS AND LOGISTICS
    # ============================================================================
    pickup_location_id = fields.Many2one("records.location", string="Pickup Location")
    delivery_location_id = fields.Many2one("records.location", string="Delivery Location")
    current_location_id = fields.Many2one("records.location", string="Current Location")
    
    transportation_mode = fields.Selection([
        ('truck', 'Truck'),
        ('rail', 'Rail'),
        ('ship', 'Ship'),
        ('air', 'Air')
    ], string="Transportation Mode", default='truck')
    
    # ============================================================================
    # DATES AND SCHEDULING
    # ============================================================================
    date_created = fields.Datetime(string="Created Date", default=fields.Datetime.now)
    date_modified = fields.Datetime(string="Modified Date")
    scheduled_pickup_date = fields.Datetime(string="Scheduled Pickup")
    actual_pickup_date = fields.Datetime(string="Actual Pickup")
    scheduled_delivery_date = fields.Datetime(string="Scheduled Delivery")
    actual_delivery_date = fields.Datetime(string="Actual Delivery")

    # ============================================================================
    # BUSINESS RELATIONSHIPS
    # ============================================================================
    customer_id = fields.Many2one("res.partner", string="Customer", domain="[('is_company', '=', True)]")
    vendor_id = fields.Many2one("res.partner", string="Vendor/Recycler")
    driver_id = fields.Many2one("res.partner", string="Driver")
    carrier_id = fields.Many2one("res.partner", string="Carrier")
    
    # Bales relationship
    bale_ids = fields.One2many("paper.bale", "load_shipment_id", string="Paper Bales")
    bale_count = fields.Integer(string="Bale Count", compute="_compute_bale_count")

    # ============================================================================
    # DELIVERY AND CONFIRMATION
    # ============================================================================
    delivery_confirmation_method = fields.Selection([
        ('signature', 'Signature'),
        ('email', 'Email Confirmation'),
        ('phone', 'Phone Confirmation'),
        ('portal', 'Portal Confirmation')
    ], string="Confirmation Method", default='signature')
    
    delivery_priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string="Delivery Priority", default='normal')
    
    environmental_conditions = fields.Selection([
        ('normal', 'Normal'),
        ('controlled', 'Controlled Environment'),
        ('hazmat', 'Hazardous Materials'),
        ('refrigerated', 'Refrigerated')
    ], string="Environmental Conditions", default='normal')

    # ============================================================================
    # QUALITY AND SATISFACTION
    # ============================================================================
    customer_satisfaction_rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string="Customer Rating")
    
    quality_check_passed = fields.Boolean(string="Quality Check Passed", default=False)
    inspection_notes = fields.Text(string="Inspection Notes")

    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    estimated_cost = fields.Monetary(string="Estimated Cost", currency_field='currency_id')
    actual_cost = fields.Monetary(string="Actual Cost", currency_field='currency_id')
    revenue = fields.Monetary(string="Revenue", currency_field='currency_id')
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('bale_ids')
    def _compute_bale_count(self):
        """Count associated bales"""
        for record in self:
            record.bale_count = len(record.bale_ids)

    # ============================================================================
    # DESCRIPTIVE FIELDS
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")
    special_instructions = fields.Text(string="Special Instructions")
    delivery_instructions = fields.Text(string="Delivery Instructions")

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the shipment"""
        self.ensure_one()
        if not self.bale_ids:
            raise UserError("Cannot confirm shipment without bales")
        self.state = 'active'
        self.status = 'confirmed'
        self.message_post(body="Shipment confirmed")

    def action_start_transit(self):
        """Start transit"""
        self.ensure_one()
        self.state = 'in_transit'
        self.status = 'shipped'
        self.actual_pickup_date = fields.Datetime.now()
        self.message_post(body="Shipment in transit")

    def action_deliver(self):
        """Mark as delivered"""
        self.ensure_one()
        self.state = 'delivered'
        self.status = 'delivered'
        self.actual_delivery_date = fields.Datetime.now()
        self.message_post(body="Shipment delivered")

    def action_complete(self):
        """Complete the shipment"""
        self.ensure_one()
        if not self.actual_delivery_date:
            raise UserError("Cannot complete shipment without delivery confirmation")
        self.state = 'completed'
        self.message_post(body="Shipment completed")

    def action_cancel(self):
        """Cancel the shipment"""
        self.ensure_one()
        if self.state in ['delivered', 'completed']:
            raise UserError("Cannot cancel delivered or completed shipment")
        self.state = 'cancelled'
        self.message_post(body="Shipment cancelled")

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('total_weight', 'actual_weight')
    def _check_weights(self):
        """Validate weights are positive"""
        for record in self:
            if record.total_weight and record.total_weight < 0:
                raise ValidationError("Total weight must be positive")
            if record.actual_weight and record.actual_weight < 0:
                raise ValidationError("Actual weight must be positive")

    @api.constrains('scheduled_pickup_date', 'scheduled_delivery_date')
    def _check_scheduled_dates(self):
        """Validate scheduled date sequence"""
        for record in self:
            if record.scheduled_pickup_date and record.scheduled_delivery_date:
                if record.scheduled_pickup_date > record.scheduled_delivery_date:
                    raise ValidationError("Pickup date cannot be after delivery date")

    @api.constrains('shipment_number')
    def _check_unique_shipment_number(self):
        """Ensure shipment number is unique"""
        for record in self:
            if record.shipment_number:
                existing = self.search([
                    ('shipment_number', '=', record.shipment_number),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(f"Shipment number {record.shipment_number} already exists")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals):
        """Override create to set shipment number"""
        if 'shipment_number' not in vals or not vals['shipment_number']:
            vals['shipment_number'] = self.env['ir.sequence'].next_by_code('paper.load.shipment') or '/'
        if 'date_modified' not in vals:
            vals['date_modified'] = fields.Datetime.now()
        return super().create(vals)

    def write(self, vals):
        """Override write for modification tracking"""
        vals['date_modified'] = fields.Datetime.now()
        result = super().write(vals)
        for record in self:
            if 'state' in vals:
                record.message_post(body=f"State changed to {record.state}")
        return result

    def unlink(self):
        """Override unlink with validation"""
        for record in self:
            if record.state in ['in_transit', 'delivered', 'completed']:
                raise UserError(f"Cannot delete shipment {record.name} in state {record.state}")
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
                name += f" ({record.shipment_number})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search by name, shipment number, or reference"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|',
                     ('name', operator, name),
                     ('shipment_number', operator, name),
                     ('reference_number', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")
\n    # ============================================================================\n    # AUTO-GENERATED FIELDS (Batch 1)\n    # ============================================================================\n    manifest_generated = fields.Monetary(string='Manifest Generated', currency_field='currency_id', tracking=True)\n    mobile_manifest = fields.Char(string='Mobile Manifest', tracking=True)\n    pickup_date = fields.Date(string='Pickup Date', tracking=True)\n\n    # ============================================================================\n    # AUTO-GENERATED ACTION METHODS (Batch 1)\n    # ============================================================================\n    def action_add_bales_to_load(self):
        """Add Bales To Load - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Add Bales To Load"),
            "res_model": "paper.load.shipment",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }\n    def action_create_invoice(self):
        """Create Invoice - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Create Invoice"),
            "res_model": "paper.load.shipment",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }\n    def action_generate_manifest(self):
        """Generate Manifest - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_generate_manifest_template",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }\n    def action_mark_delivered(self):
        """Mark Delivered - Update field"""
        self.ensure_one()
        self.write({"delivered": True})
        self.message_post(body=_("Mark Delivered"))
        return True\n    def action_mark_in_transit(self):
        """Mark In Transit - Update field"""
        self.ensure_one()
        self.write({"in_transit": True})
        self.message_post(body=_("Mark In Transit"))
        return True\n    def action_mark_paid(self):
        """Mark Paid - Update field"""
        self.ensure_one()
        self.write({"paid": True})
        self.message_post(body=_("Mark Paid"))
        return True\n    def action_ready_for_pickup(self):
        """Ready For Pickup - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Ready For Pickup"),
            "res_model": "paper.load.shipment",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }\n    def action_schedule_pickup(self):
        """Schedule Pickup - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Schedule Pickup"),
            "res_model": "paper.load.shipment",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }\n    def action_view_manifest(self):
        """View Manifest - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Manifest"),
            "res_model": "paper.load.shipment",
            "view_mode": "tree,form",
            "domain": [("shipment_id", "=", self.id)],
            "context": {"default_shipment_id": self.id},
        }\n    def action_view_weight_breakdown(self):
        """View Weight Breakdown - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Weight Breakdown"),
            "res_model": "paper.load.shipment",
            "view_mode": "tree,form",
            "domain": [("shipment_id", "=", self.id)],
            "context": {"default_shipment_id": self.id},
        }