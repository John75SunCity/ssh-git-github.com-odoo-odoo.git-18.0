# -*- coding: utf-8 -*-
from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError

class PaperBale(models.Model):
    _name = "paper.bale"
    _description = "Paper Bale"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Bale Number", required=True, tracking=True, index=True)
    company_id = fields.Many2one("res.company", default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one("res.users", default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string="Active", default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    reference_number = fields.Char(string="Reference Number")
    external_reference = fields.Char(string="External Reference")

    # ============================================================================
    # STATE AND STATUS MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('created', 'Created'),
        ('quality_checked', 'Quality Checked'),
        ('loaded', 'Loaded on Trailer'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('recycled', 'Recycled'),
        ('rejected', 'Rejected/Sent to Trash')
    ], default='created', tracking=True)
    
    # ============================================================================
    # PAPER AND BALE SPECIFICATIONS
    # ============================================================================
    weight = fields.Float(string="Weight", digits=(10, 2), tracking=True)
    weight_unit = fields.Selection([
        ('lb', 'Pounds'),
        ('kg', 'Kilograms'),
        ('ton', 'Tons')
    ], default='lb', string="Weight Unit")
    
    paper_type = fields.Selection([
        ('mixed', 'Mixed Paper'),
        ('office', 'Office Paper'),
        ('cardboard', 'Cardboard'),
        ('newspaper', 'Newspaper'),
        ('magazine', 'Magazine'),
        ('shredded', 'Shredded Paper')
    ], string="Paper Type", tracking=True)
    
    bale_type = fields.Selection([
        ('standard', 'Standard'),
        ('compacted', 'Compacted'),
        ('loose', 'Loose')
    ], string="Bale Type", default='standard')
    
    paper_grade = fields.Selection([
        ('high', 'High Grade'),
        ('medium', 'Medium Grade'),
        ('low', 'Low Grade')
    ], string="Paper Grade")
    
    contamination_level = fields.Selection([
        ('none', 'No Contamination'),
        ('low', 'Low Contamination'),
        ('medium', 'Medium Contamination'),
        ('high', 'High Contamination')
    ], string="Contamination Level", default='none')

    # ============================================================================
    # LOCATION AND LOGISTICS
    # ============================================================================
    pickup_location_id = fields.Many2one("records.location", string="Pickup Location")
    delivery_location_id = fields.Many2one("records.location", string="Delivery Location")
    current_location_id = fields.Many2one("records.location", string="Current Location")
    
    transportation_method = fields.Selection([
        ('truck', 'Truck'),
        ('rail', 'Rail'),
        ('ship', 'Ship')
    ], string="Transportation Method", default='truck')
    
    # ============================================================================
    # DATES AND SCHEDULING
    # ============================================================================
    bale_date = fields.Date(string="Bale Date", default=fields.Date.today, tracking=True)
    pickup_date = fields.Date(string="Pickup Date")
    delivery_date = fields.Date(string="Delivery Date")
    shipped_date = fields.Date(string="Shipped Date")
    
    # ============================================================================
    # BUSINESS RELATIONSHIPS
    # ============================================================================
    customer_id = fields.Many2one("res.partner", string="Customer", domain="[('is_company', '=', True)]")
    vendor_id = fields.Many2one("res.partner", string="Recycling Vendor")
    driver_id = fields.Many2one("res.partner", string="Driver")
    load_shipment_id = fields.Many2one("paper.load.shipment", string="Load Shipment")
    
    # ============================================================================
    # COMPLIANCE AND SECURITY
    # ============================================================================
    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string="Confidentiality Level", default='internal')
    
    certificate_of_destruction = fields.Boolean(string="Certificate of Destruction", default=False)
    chain_of_custody_verified = fields.Boolean(string="Chain of Custody Verified", default=False)
    
    # ============================================================================
    # FINANCIAL INFORMATION
    # ============================================================================
    sale_price = fields.Monetary(string="Sale Price", currency_field='currency_id')
    cost = fields.Monetary(string="Cost", currency_field='currency_id')
    currency_id = fields.Many2one("res.currency", related="company_id.currency_id")
    load_id = fields.Many2one("load", string="Load")
    
    # ============================================================================
    # ENVIRONMENTAL AND METRICS
    # ============================================================================
    recycling_category = fields.Selection([
        ('post_consumer', 'Post Consumer'),
        ('post_industrial', 'Post Industrial'),
        ('mixed', 'Mixed')
    ], string="Recycling Category")
    
    # Computed fields
    density = fields.Float(string="Density", compute="_compute_density", store=True)
    document_count = fields.Integer(string="Document Count", compute="_compute_document_count")
    environmental_impact = fields.Float(string="Environmental Impact Score", compute="_compute_environmental_impact")
    
    # ============================================================================
    # DESCRIPTIVE FIELDS
    # ============================================================================
    description = fields.Text(string="Description")
    notes = fields.Text(string="Internal Notes")
    special_instructions = fields.Text(string="Special Instructions")

    # ============================================================================
    # COMPUTED METHODS (Consolidated)
    # ============================================================================
    @api.depends('weight')
    def _compute_density(self):
        """Calculate bale density"""
        for record in self:
            # Simplified density calculation
            record.density = record.weight / 100.0 if record.weight else 0.0

    def _compute_document_count(self):
        """Count related documents"""
        for record in self:
            record.document_count = len(record.source_document_ids)

    @api.depends('weight', 'paper_type')
    def _compute_environmental_impact(self):
        """Calculate environmental impact score"""
        for record in self:
            base_score = record.weight * 0.1 if record.weight else 0.0
            if record.paper_type == 'office':
                base_score *= 1.2
            elif record.paper_type == 'mixed':
                base_score *= 0.8
            record.environmental_impact = base_score

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    source_document_ids = fields.One2many("paper.bale.source.document", "bale_id", string="Source Documents")
    
    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    def action_quality_check(self):
        """Mark bale as quality checked"""
        self.ensure_one()
        self.state = 'quality_checked'
        self.message_post(body="Bale quality checked")

    def action_load_trailer(self):
        """Mark bale as loaded on trailer"""
        self.ensure_one()
        self.state = 'loaded'
        self.message_post(body="Bale loaded on trailer")

    def action_ship(self):
        """Mark bale as shipped"""
        self.ensure_one()
        self.state = 'shipped'
        self.shipped_date = fields.Date.today()
        self.message_post(body="Bale shipped")

    def action_deliver(self):
        """Mark bale as delivered"""
        self.ensure_one()
        self.state = 'delivered'
        self.delivery_date = fields.Date.today()
        self.message_post(body="Bale delivered")

    def action_recycle(self):
        """Mark bale as recycled"""
        self.ensure_one()
        if not self.certificate_of_destruction:
            raise UserError("Certificate of destruction required before recycling")
        self.state = 'recycled'
        self.message_post(body="Bale recycled - process complete")

    def action_reject(self):
        """Reject bale and send to trash"""
        self.ensure_one()
        self.state = 'rejected'
        self.message_post(body="Bale rejected and sent to trash")

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('weight')
    def _check_weight(self):
        """Validate weight is positive"""
        for record in self:
            if record.weight and record.weight <= 0:
                raise ValidationError("Weight must be positive")

    @api.constrains('pickup_date', 'delivery_date')
    def _check_dates(self):
        """Validate date sequence"""
        for record in self:
            if record.pickup_date and record.delivery_date:
                if record.pickup_date > record.delivery_date:
                    raise ValidationError("Pickup date cannot be after delivery date")

    # ============================================================================
    # ODOO FRAMEWORK INTEGRATION
    # ============================================================================
    @api.model_create_multi
    def create(self, vals):
        """Override create to set sequence and initial state"""
        if 'name' not in vals or vals['name'] == '/':
            vals['name'] = self.env['ir.sequence'].next_by_code('paper.bale') or '/'
        return super().create(vals)

    def write(self, vals):
        """Override write for state change tracking"""
        if 'state' in vals:
            for record in self:
                old_state = record.state
                new_state = vals['state']
                if old_state != new_state:
                    record.message_post(
                        body=f"State changed from {old_state} to {new_state}"
                    )
        return super().write(vals)

    def unlink(self):
        """Override unlink to prevent deletion of shipped bales"""
        for record in self:
            if record.state in ['shipped', 'delivered', 'recycled']:
                raise UserError(f"Cannot delete bale {record.name} in state {record.state}")
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = f"{record.name}"
            if record.paper_type:
                name += f" ({record.paper_type})"
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name, args=None, operator='ilike', limit=100, name_get_uid=None):
        """Enhanced search by name, reference, or paper type"""
        args = args or []
        domain = []
        if name:
            domain = ['|', '|', '|',
                     ('name', operator, name),
                     ('reference_number', operator, name),
                     ('external_reference', operator, name),
                     ('paper_type', operator, name)]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================    bale_status = fields.Selection([('draft', 'Draft')], string='Bale Status', default='draft', tracking=True)
    creation_date = fields.Date(string='Creation Date', tracking=True)
    loaded_on_trailer = fields.Char(string='Loaded On Trailer', tracking=True)
    quality_grade = fields.Char(string='Quality Grade', tracking=True)
    sustainable_source = fields.Char(string='Sustainable Source', tracking=True)

    # ============================================================================
    # AUTO-GENERATED ACTION METHODS (Batch 1)
    # ============================================================================
    def action_date(self):
        """Date - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Date"),
            "res_model": "paper.bale",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_move_to_storage(self):
        """Move To Storage - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Move To Storage"),
            "res_model": "paper.bale",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_print_label(self):
        """Print Label - Generate report"""
        self.ensure_one()
        return {
            "type": "ir.actions.report",
            "report_name": "records_management.action_print_label_template",
            "report_type": "qweb-pdf",
            "data": {"ids": [self.id]},
            "context": self.env.context,
        }
    def action_quality_inspection(self):
        """Quality Inspection - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Inspection"),
            "res_model": "paper.bale",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_type(self):
        """Type - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Type"),
            "res_model": "paper.bale",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }
    def action_view_inspection_details(self):
        """View Inspection Details - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Inspection Details"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }
    def action_view_source_documents(self):
        """View Source Documents - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Source Documents"),
            "res_model": "records.document",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }
    def action_view_trailer_info(self):
        """View Trailer Info - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Trailer Info"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }
    def action_view_weight_history(self):
        """View Weight History - View related records"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("View Weight History"),
            "res_model": "paper.bale",
            "view_mode": "tree,form",
            "domain": [("bale_id", "=", self.id)],
            "context": {"default_bale_id": self.id},
        }
    def action_weigh_bale(self):
        """Weigh Bale - Action method"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Weigh Bale"),
            "res_model": "paper.bale",
            "view_mode": "form",
            "target": "new",
            "context": self.env.context,
        }