# Part of Odoo. See LICENSE file for full copyright and licensing details.

from typing import List
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class RecordsBox(models.Model):
    """Model for document storage boxes with enhanced fields."""
    _name = 'records.box'
    _description = 'Document Storage Box'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    name = fields.Char(
        string='Box Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New')
    )
    alternate_code = fields.Char(string='Alternate Code', copy=False)
    description = fields.Char(string='Description', required=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft')
    item_status = fields.Selection([
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('pending', 'Pending'),
        ('permanent_out', 'Permanent Out'),
        ('destroyed', 'Destroyed'),
        ('archived', 'Archived')
    ], string='Item Status', default='active')
    status_date = fields.Datetime(
        string='Status Date',
        default=fields.Datetime.now
    )
    add_date = fields.Datetime(
        string='Add Date',
        default=fields.Datetime.now,
        readonly=True
    )
    storage_date = fields.Date(
        string='Storage Date',
        help='Date when the box was placed in storage location'
    )
    destroy_date = fields.Date(string='Destroy Date')
    access_count = fields.Integer(string='Access Count', default=0)
    perm_flag = fields.Boolean(string='Permanent Flag', default=False)
    product_id = fields.Many2one('product.product', string='Box Product')
    location_id = fields.Many2one(
        'records.location',
        string='Storage Location',
        index=True
    )
    location_code = fields.Char(
        related='location_id.code',
        string='Location Code',
        readonly=True
    )
    customer_inventory_id = fields.Many2one(
        'customer.inventory.report',
        string='Customer Inventory Report',
        ondelete='cascade'
    )
    container_type = fields.Selection([
        ('standard', 'Standard Box'),
        ('map_box', 'Map Box'),
        ('specialty', 'Specialty Box'),
        ('pallet', 'Pallet'),
        ('other', 'Other')
    ], string='Container Type', default='standard')
    
    # Business-specific box type codes for pricing and location management
    box_type_code = fields.Selection([
        ('01', 'Type 01 - Standard File Box'),
        ('03', 'Type 03 - Map Box'),
        ('04', 'Type 04 - Oversize/Odd-shaped Box'),
        ('06', 'Type 06 - Specialty/Vault Box'),
    ], string='Box Type Code', default='01', required=True,
       help="Box type determines pricing, storage location, and handling requirements")
    
    # Computed field for customer-friendly display
    box_type_display = fields.Char(
        string='Box Type',
        compute='_compute_box_type_display',
        store=True,
        help="Customer-friendly display name for invoicing and reports"
    )
    
    # Pricing related to box type
    monthly_rate = fields.Float(
        string='Monthly Storage Rate',
        compute='_compute_monthly_rate',
        store=True,
        help="Monthly storage rate based on box type"
    )
    security_code = fields.Char(string='Security Code')
    category_code = fields.Char(string='Category Code')
    record_series = fields.Char(string='Record Series')
    object_code = fields.Char(string='Object Code')
    account_level1 = fields.Char(string='Account Level 1')
    account_level2 = fields.Char(string='Account Level 2')
    account_level3 = fields.Char(string='Account Level 3')
    sequence_from = fields.Integer(string='Sequence From')
    sequence_to = fields.Integer(string='Sequence To')
    date_from = fields.Date(string='Date From')
    date_to = fields.Date(string='Date To')
    custom_metadata_1 = fields.Char(string='Custom Metadata 1')
    custom_metadata_2 = fields.Char(string='Custom Metadata 2')
    custom_metadata_3 = fields.Char(string='Custom Metadata 3')
    custom_metadata_4 = fields.Char(string='Custom Metadata 4')
    custom_date = fields.Date(string='Custom Date')
    charge_for_storage = fields.Boolean(
        string='Charge for Storage',
        default=True
    )
    charge_for_add = fields.Boolean(string='Charge for Add', default=True)
    capacity = fields.Integer(string='Capacity (documents)', default=100)
    used_capacity = fields.Float(
        string='Used Capacity (%)',
        compute='_compute_used_capacity',
        store=False
    )
    barcode = fields.Char(string='Barcode', copy=False, index=True)
    barcode_length = fields.Integer(string='Barcode Length', default=12)
    barcode_type = fields.Selection([
        ('code128', 'Code 128'),
        ('code39', 'Code 39'),
        ('upc', 'UPC'),
        ('ean13', 'EAN-13'),
        ('qr', 'QR Code'),
        ('other', 'Other')
    ], string='Barcode Type', default='code128')
    document_ids = fields.One2many(
        'records.document',
        'box_id',
        string='Documents'
    )
    document_count = fields.Integer(
        compute='_compute_document_count',
        string='Document Count',
        store=True
    )
    notes = fields.Html(string='Notes')
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company
    )
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company', '=', True)]",
        index=True
    )
    department_id = fields.Many2one(
        'records.department',
        string='Department',
        index=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Responsible',
        default=lambda self: self.env.user
    )
    create_date = fields.Datetime(string='Created on', readonly=True)
    destruction_date = fields.Date(string='Destruction Date')
    color = fields.Integer(string='Color Index')
    tag_ids = fields.Many2many('records.tag', string='Tags')

    # One2many relations referenced in views
    movement_ids = fields.One2many(
        'records.box.movement', 'box_id',
        string='Movement History'
    )
    service_request_ids = fields.One2many(
        'pickup.request', 'box_id',
        string='Service Requests'
    )

    # Phase 1 Critical Fields - Added by automated script
    activity_ids = fields.One2many('mail.activity', compute='_compute_activity_ids', string='Activities')
    message_follower_ids = fields.One2many('mail.followers', compute='_compute_message_followers', string='Followers')
    message_ids = fields.One2many('mail.message', compute='_compute_message_ids', string='Messages')
    movement_count = fields.Integer('Movement Count', compute='_compute_movement_count')
    service_request_count = fields.Integer('Service Request Count', compute='_compute_service_request_count')
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy')
    size_category = fields.Selection([('small', 'Small'), ('medium', 'Medium'), ('large', 'Large')], string='Size Category')
    weight = fields.Float('Weight (lbs)')
    priority = fields.Selection([('low', 'Low'), ('normal', 'Normal'), ('high', 'High')], string='Priority', default='normal')

    # Phase 2 Audit & Compliance Fields - Added by automated script
    audit_log_ids = fields.One2many('records.audit.log', 'box_id', string='Audit Logs')
    last_audit_date = fields.Datetime('Last Audit Date', readonly=True)
    audit_required = fields.Boolean('Audit Required', default=True)
    physical_audit_required = fields.Boolean('Physical Audit Required', default=False)
    inventory_verified = fields.Boolean('Inventory Verified', default=False)
    inventory_verification_date = fields.Date('Inventory Verification Date')
    inventory_discrepancies = fields.Text('Inventory Discrepancies')
    compliance_status = fields.Selection([('compliant', 'Compliant'), ('non_compliant', 'Non-Compliant'), ('pending_review', 'Pending Review')], string='Compliance Status', default='pending_review')
    naid_certified = fields.Boolean('NAID Certified Storage', default=False)
    iso_certified = fields.Boolean('ISO Certified Storage', default=False)
    security_clearance_required = fields.Selection([('none', 'None'), ('basic', 'Basic'), ('secret', 'Secret'), ('top_secret', 'Top Secret')], string='Security Clearance Required', default='none')
    environmental_controls = fields.Boolean('Environmental Controls', default=False)
    fire_suppression = fields.Boolean('Fire Suppression System', default=False)
    custody_log_ids = fields.One2many('records.chain.custody', 'box_id', string='Chain of Custody')
    current_custodian_id = fields.Many2one('res.users', string='Current Custodian')
    transfer_log_ids = fields.One2many('records.box.transfer', 'box_id', string='Transfer Log')
    witness_required = fields.Boolean('Witness Required for Transfer', default=False)
    tamper_evident_seal = fields.Char('Tamper Evident Seal Number')
    seal_verified = fields.Boolean('Seal Verified', default=False)
    seal_verification_date = fields.Datetime('Seal Verification Date')

    # Phase 3: Analytics & Computed Fields (9 fields)
    utilization_rate = fields.Float(
        string='Utilization Rate (%)',
        compute='_compute_box_analytics',
        store=True,
        help='Percentage of box capacity currently utilized'
    )
    storage_duration = fields.Integer(
        string='Storage Duration (days)',
        compute='_compute_box_analytics',
        store=True,
        help='Number of days box has been in storage'
    )
    retrieval_frequency = fields.Float(
        string='Retrieval Frequency (per month)',
        compute='_compute_box_analytics',
        store=True,
        help='Average retrievals per month'
    )
    cost_per_document = fields.Float(
        string='Cost per Document',
        compute='_compute_box_analytics',
        store=True,
        help='Storage cost divided by document count'
    )
    space_efficiency = fields.Float(
        string='Space Efficiency Score',
        compute='_compute_box_analytics',
        store=True,
        help='Efficiency score based on space utilization'
    )
    destruction_eligibility = fields.Selection([
        ('not_eligible', 'Not Eligible'),
        ('review_required', 'Review Required'),
        ('eligible', 'Eligible'),
        ('overdue', 'Overdue')
    ], string='Destruction Eligibility', compute='_compute_box_analytics', store=True)
    security_score = fields.Float(
        string='Security Score',
        compute='_compute_box_analytics',
        store=True,
        help='Security assessment score (0-100)'
    )
    movement_pattern = fields.Selection([
        ('static', 'Static'),
        ('occasional', 'Occasional'),
        ('frequent', 'Frequent'),
        ('high_activity', 'High Activity')
    ], string='Movement Pattern', compute='_compute_box_analytics', store=True)
    box_insights = fields.Text(
        string='Box Analytics Insights',
        compute='_compute_box_analytics',
        store=True,
        help='AI-generated insights about box management'
    )
    
    # Missing technical view fields for XML processing and records management
    arch = fields.Text(string='View Architecture', help='XML view architecture definition')
    context = fields.Text(string='Context', help='View context information')
    created_date = fields.Date(string='Created Date', default=fields.Date.today)
    document_type_id = fields.Many2one('records.document.type', string='Document Type')
    from_location_id = fields.Many2one('records.location', string='From Location')
    help = fields.Text(string='Help', help='Help text for this record')
    model = fields.Char(string='Model', help='Model name for technical references')
    movement_date = fields.Date(string='Movement Date', default=fields.Date.today)
    movement_type = fields.Selection([
        ('in', 'Incoming'),
        ('out', 'Outgoing'),
        ('transfer', 'Transfer'),
        ('inventory', 'Inventory')
    ], string='Movement Type', default='in')
    request_date = fields.Date(string='Request Date', default=fields.Date.today)
    res_model = fields.Char(string='Resource Model', help='Resource model name')
    responsible_user_id = fields.Many2one('res.users', string='Responsible User')
    search_view_id = fields.Many2one('ir.ui.view', string='Search View', help='Search view reference')
    to_location_id = fields.Many2one('records.location', string='To Location')
    view_mode = fields.Char(string='View Mode', help='View mode configuration')


    @api.model_create_multi
    def create(self, vals_list: List[dict]) -> 'RecordsBox':
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('records.box')
                vals['name'] = sequence or _('New')
        return super().create(vals_list)

    @api.depends('document_ids')
    def _compute_document_count(self) -> None:
        for box in self:
            box.document_count = len(box.document_ids)

    @api.depends('document_count', 'capacity')
    def _compute_used_capacity(self) -> None:
        for box in self:
            if box.capacity:
                percentage = (box.document_count / box.capacity * 100)
                box.used_capacity = percentage
            else:
                box.used_capacity = 0

    @api.depends('movement_ids')
    def _compute_movement_count(self):
        """Compute count of movement records for this box"""
        for box in self:
            movement_count = 0
            if hasattr(box, 'movement_ids'):
                movement_count = len(box.movement_ids)
            else:
                # Count movements from movement model if relation exists
                try:
                    movement_count = self.env['records.box.movement'].search_count([
                        ('box_id', '=', box.id)
                    ])
                except Exception:
                    pass
            box.movement_count = movement_count

    @api.depends('service_request_ids')
    def _compute_service_request_count(self):
        """Compute count of service requests for this box"""
        for box in self:
            service_count = 0
            if hasattr(box, 'service_request_ids'):
                service_count = len(box.service_request_ids)
            else:
                # Count service requests if relation exists
                try:
                    service_count = self.env['pickup.request'].search_count([
                        ('box_id', '=', box.id)
                    ])
                except Exception:
                    pass
            box.service_request_count = service_count

    @api.depends('storage_date', 'access_count', 'state', 'document_ids', 'location_id')
    def _compute_box_analytics(self):
        """Compute analytics and business intelligence for storage boxes"""
        for box in self:
            # Storage duration calculation
            if box.storage_date:
                box.storage_duration = (fields.Date.today() - box.storage_date).days
            else:
                box.storage_duration = 0
            
            # Utilization rate (assume max 50 documents per box)
            max_capacity = 50
            doc_count = len(box.document_ids) if box.document_ids else 0
            box.utilization_rate = min(100, (doc_count / max_capacity) * 100) if max_capacity else 0
            
            # Retrieval frequency (based on access count)
            if box.storage_duration > 0:
                days_per_month = 30
                months_stored = max(1, box.storage_duration / days_per_month)
                box.retrieval_frequency = (box.access_count or 0) / months_stored
            else:
                box.retrieval_frequency = 0.0
            
            # Cost per document
            monthly_storage_cost = 5.0  # $5 per box per month
            if box.storage_duration > 0:
                total_cost = (box.storage_duration / 30) * monthly_storage_cost
                if doc_count > 0:
                    box.cost_per_document = total_cost / doc_count
                else:
                    box.cost_per_document = total_cost
            else:
                box.cost_per_document = 0.0
            
            # Space efficiency score
            efficiency = 0
            if box.utilization_rate > 90:
                efficiency = 100
            elif box.utilization_rate > 75:
                efficiency = 85
            elif box.utilization_rate > 50:
                efficiency = 70
            elif box.utilization_rate > 25:
                efficiency = 50
            else:
                efficiency = 25
            
            # Bonus for high retrieval frequency (shows it's useful)
            if box.retrieval_frequency > 1.0:
                efficiency += 10
            
            box.space_efficiency = min(100, efficiency)
            
            # Destruction eligibility assessment
            if box.storage_duration > 2555:  # 7+ years
                box.destruction_eligibility = 'overdue'
            elif box.storage_duration > 2190:  # 6+ years
                box.destruction_eligibility = 'eligible'
            elif box.storage_duration > 1825:  # 5+ years
                box.destruction_eligibility = 'review_required'
            else:
                box.destruction_eligibility = 'not_eligible'
            
            # Security score calculation
            security_score = 50  # Base score
            
            if box.location_id:
                security_score += 20  # Has assigned location
            
            if hasattr(box, 'security_clearance_required') and box.security_clearance_required != 'none':
                security_score += 15
            
            if hasattr(box, 'tamper_evident_seal') and box.tamper_evident_seal:
                security_score += 10
            
            if hasattr(box, 'environmental_controls') and box.environmental_controls:
                security_score += 5
            
            box.security_score = min(100, security_score)
            
            # Movement pattern analysis
            if box.retrieval_frequency > 2.0:
                box.movement_pattern = 'high_activity'
            elif box.retrieval_frequency > 1.0:
                box.movement_pattern = 'frequent'
            elif box.retrieval_frequency > 0.2:
                box.movement_pattern = 'occasional'
            else:
                box.movement_pattern = 'static'
            
            # Analytics insights
            insights = []
            
            if box.utilization_rate < 30:
                insights.append("📦 Low utilization - consider consolidation")
            
            if box.cost_per_document > 2.0:
                insights.append("💰 High cost per document - review efficiency")
            
            if box.destruction_eligibility == 'overdue':
                insights.append("🗑️ Overdue for destruction review")
            
            if box.retrieval_frequency > 2.0:
                insights.append("🔥 High activity - consider digitization")
            
            if box.security_score < 60:
                insights.append("🔒 Security enhancements recommended")
            
            if box.space_efficiency > 90:
                insights.append("⭐ Excellent space efficiency")
            
            if not insights:
                insights.append("✅ Box management optimized")
            
            box.box_insights = " | ".join(insights)

    @api.depends('box_type_code')
    def _compute_box_type_display(self) -> None:
        """Compute customer-friendly display name for box type."""
        for box in self:
            type_mapping = {
                '01': 'Standard File Box',
                '03': 'Map Box',
                '04': 'Oversize Box',
                '06': 'Specialty Box',
            }
            box.box_type_display = type_mapping.get(box.box_type_code, 'Unknown Type')

    @api.depends('box_type_code')
    def _compute_monthly_rate(self) -> None:
        """Compute monthly storage rate based on box type."""
        for box in self:
            # Standard pricing structure - can be made configurable later
            rate_mapping = {
                '01': 0.32,  # Standard file boxes
                '03': 0.45,  # Map boxes (larger)
                '04': 0.50,  # Oversize boxes (special handling)
                '06': 0.40,  # Specialty boxes (vault storage)
            }
            box.monthly_rate = rate_mapping.get(box.box_type_code, 0.32)

    @api.model
    def classify_barcode_type(self, barcode):
        """Classify object type based on barcode length according to business rules."""
        if not barcode:
            return None
            
        length = len(str(barcode))
        classification = {
            5: 'location',
            15: 'location',
            6: 'container',  # File boxes - default to type 01
            7: 'filefolder',
            10: 'shred_bin',
            14: 'temp_filefolder'  # Portal-created, needs reassignment
        }
        return classification.get(length)

    @api.model
    def create_from_barcode_scan(self, barcode, location_id=None):
        """Create box from barcode scan with intelligent type detection."""
        barcode_type = self.classify_barcode_type(barcode)
        
        if barcode_type != 'container':
            raise ValidationError(_(
                'Barcode %s (%d digits) is not a container barcode. '
                'Only 6-digit barcodes can create boxes.'
            ) % (barcode, len(str(barcode))))
        
        # Check if box already exists
        existing_box = self.search([('barcode', '=', barcode)])
        if existing_box:
            raise ValidationError(_(
                'Box with barcode %s already exists: %s'
            ) % (barcode, existing_box.name))
        
        # Auto-detect box type based on location if provided
        box_type_code = '01'  # Default to standard
        if location_id:
            location = self.env['records.location'].browse(location_id)
            if location.location_type == 'map':
                box_type_code = '03'
            elif location.location_type == 'vault':
                box_type_code = '06'
            elif location.location_type == 'oversize':
                box_type_code = '04'
        
        return self.create({
            'barcode': barcode,
            'box_type_code': box_type_code,
            'location_id': location_id,
            'description': f'Box scanned from barcode {barcode}',
            'state': 'active'
        })

    def action_bulk_convert_box_type(self):
        """Open wizard for bulk box type conversion."""
        return {
            'name': _('Bulk Convert Box Types'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.box.type.converter',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_box_ids': [(6, 0, self.ids)],
                'default_current_type': self[0].box_type_code if len(self) == 1 else False,
            }
        }

    @api.constrains('box_type_code', 'location_id')
    def _check_box_type_location_compatibility(self):
        """Validate that box types are placed in appropriate location types."""
        for box in self:
            if not box.location_id:
                continue
                
            location_type = box.location_id.location_type
            box_type = box.box_type_code
            
            # Define allowed combinations
            incompatible_combinations = [
                # Standard boxes (01) should not be in vault, map, or oversize areas
                ('01', 'vault'),
                ('01', 'map'), 
                ('01', 'oversize'),
                # Map boxes (03) should only be in map areas
                ('03', 'aisles'),
                ('03', 'pallets'),
                ('03', 'vault'),
                ('03', 'oversize'),
                ('03', 'refiles'),
                # Oversize boxes (04) should only be in oversize areas
                ('04', 'aisles'),
                ('04', 'pallets'),
                ('04', 'vault'),
                ('04', 'map'),
                ('04', 'refiles'),
                # Specialty boxes (06) should only be in vault
                ('06', 'aisles'),
                ('06', 'pallets'),
                ('06', 'map'),
                ('06', 'oversize'),
                ('06', 'refiles'),
            ]
            
            if (box_type, location_type) in incompatible_combinations:
                # Get field selections safely
                box_type_selection = dict(box._fields['box_type_code'].selection)
                location_type_selection = dict(box.location_id._fields['location_type'].selection)
                
                box_type_name = box_type_selection.get(box_type, box_type)
                location_type_name = location_type_selection.get(location_type, location_type)
                
                raise ValidationError(_(
                    'Box type mismatch: %s cannot be stored in %s location.\n'
                    'Please move this box to an appropriate location type.'
                ) % (box_type_name, location_type_name))

    def action_view_documents(self) -> dict:
        self.ensure_one()
        return {
            'name': _('Documents'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_set_active(self) -> bool:
        return self.write({'state': 'active'})

    def action_archive_box(self) -> bool:
        return self.write({'state': 'archived'})

    def action_destroy_box(self) -> bool:
        return self.write({
            'state': 'destroyed',
            'item_status': 'destroyed',
            'destroy_date': fields.Date.today(),
            'status_date': fields.Datetime.now()
        })

    def action_increment_access(self) -> bool:
        return self.write({'access_count': self.access_count + 1})

    def action_permanent_out(self) -> bool:
        return self.write({
            'item_status': 'permanent_out',
            'state': 'archived',
            'status_date': fields.Datetime.now()
        })

    def action_generate_box_barcode(self):
        """Generate barcode for this box"""
        self.ensure_one()
        if not self.barcode:
            self.barcode = self.env['ir.sequence'].next_by_code('records.box.barcode') or 'BOX-' + str(self.id)
        return True

    def action_generate_barcode(self):
        """Generate barcode for this box (alias for action_generate_box_barcode)"""
        return self.action_generate_box_barcode()

    def action_bulk_convert_box_type(self):
        """Bulk convert box types"""
        active_ids = self.env.context.get('active_ids', [])
        if not active_ids:
            active_ids = self.ids
        
        return {
            'name': _('Bulk Convert Box Types'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.box.type.converter',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_box_ids': [(6, 0, active_ids)]},
        }

    def action_move_box(self):
        """Move box to a different location."""
        self.ensure_one()
        return {
            'name': _('Move Box: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box.movement.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_box_id': self.id},
        }

    def action_schedule_destruction(self):
        """Schedule this box for destruction."""
        self.ensure_one()
        return {
            'name': _('Schedule Destruction: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.destruction.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_box_ids': [(6, 0, [self.id])]},
        }

    def action_store_box(self):
        """Store box in warehouse."""
        self.ensure_one()
        self.write({
            'state': 'stored',
            'storage_date': fields.Date.today(),
        })
        return True

    def action_view_movements(self):
        """View movement history for this box."""
        self.ensure_one()
        return {
            'name': _('Box Movements: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.box.movement',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_view_requests(self):
        """View service requests for this box."""
        self.ensure_one()
        return {
            'name': _('Service Requests: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.service.request',
            'view_mode': 'tree,form',
            'domain': [('box_id', '=', self.id)],
            'context': {'default_box_id': self.id},
        }

    def action_view_document(self):
        """View a specific document in this box."""
        # This would be called from a context with document_id
        document_id = self.env.context.get('document_id')
        if document_id:
            return {
                'name': _('Document Details'),
                'type': 'ir.actions.act_window',
                'res_model': 'records.document',
                'res_id': document_id,
                'view_mode': 'form',
                'target': 'current',
            }
        return False

    @api.constrains('barcode', 'barcode_length')
    def _check_barcode_length(self) -> None:
        for box in self:
            if (box.barcode and box.barcode_length and
                    len(box.barcode) != box.barcode_length):
                error_msg = _(
                    "Barcode length mismatch for box %s. "
                    "Expected %s digits, got %s."
                )
                raise ValidationError(
                    error_msg % (
                        box.name, box.barcode_length, len(box.barcode)
                    )
                )

    @api.constrains('sequence_from', 'sequence_to')
    def _check_sequence_range(self) -> None:
        for box in self:
            if (box.sequence_from and box.sequence_to and
                    box.sequence_from > box.sequence_to):
                error_msg = _(
                    "Invalid sequence range for box %s. "
                    "From (%s) cannot be greater than To (%s)."
                )
                raise ValidationError(
                    error_msg % (box.name, box.sequence_from, box.sequence_to)
                )

    @api.constrains('date_from', 'date_to')
    def _check_date_range(self) -> None:
        for box in self:
            if (box.date_from and box.date_to and
                    box.date_from > box.date_to):
                error_msg = _(
                    "Invalid date range for box %s. "
                    "From (%s) cannot be greater than To (%s)."
                )
                raise ValidationError(
                    error_msg % (box.name, box.date_from, box.date_to)
                )

    @api.constrains('document_count', 'capacity')
    def _check_capacity(self) -> None:
        for box in self:
            if box.document_count > box.capacity:
                error_msg = _(
                    "Box %s is over capacity! Maximum is %s documents."
                )
                raise ValidationError(error_msg % (box.name, box.capacity))

    def write(self, vals: dict) -> bool:
        res = super().write(vals)
        if 'customer_id' in vals or 'department_id' in vals:
            for box in self:
                customer_id = box.customer_id.id if box.customer_id else False
                department_id = (box.department_id.id if box.department_id
                                 else False)
                box.document_ids.write({
                    'customer_id': customer_id,
                    'department_id': department_id,
                })
        return res

    @api.onchange('container_type')
    def _onchange_container_type(self) -> None:
        """Update capacity based on container type for better UX."""
        if self.container_type == 'standard':
            self.capacity = 100
        elif self.container_type == 'map_box':
            self.capacity = 50
        elif self.container_type == 'pallet':
            self.capacity = 48
    
    # Compute method for activity_ids One2many field
    @api.depends()
    def _compute_activity_ids(self):
        """Compute activities for this record"""
        for record in self:
            record.activity_ids = self.env["mail.activity"].search([
                ("res_model", "=", "records.box"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_followers(self):
        """Compute message followers for this record"""
        for record in self:
            record.message_follower_ids = self.env["mail.followers"].search([
                ("res_model", "=", "records.box"),
                ("res_id", "=", record.id)
            ])

    @api.depends()
    def _compute_message_ids(self):
        """Compute messages for this record"""
        for record in self:
            record.message_ids = self.env["mail.message"].search([
                ("res_model", "=", "records.box"),
                ("res_id", "=", record.id)
            ])
