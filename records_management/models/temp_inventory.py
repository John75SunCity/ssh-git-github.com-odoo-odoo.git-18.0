# -*- coding: utf-8 -*-
"""
Transitory Items Management - Pre-Pickup Customer Inventory
Handles customer-declared inventory before physical pickup and barcoding
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class TransitoryItems(models.Model):
    """
    Transitory Items - Customer-declared inventory awaiting pickup
    
    Tracks managed records boxes, files, and items that customers add to their account
    before we physically pick them up and assign barcodes. These items should be 
    charged the same as regular inventory and count toward storage capacity planning.
    """

    _name = "transitory.items"
    _description = "Transitory Items - Pre-Pickup Customer Inventory"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "creation_date desc, name"
    _rec_name = "name"

    # ==========================================
    # CORE IDENTIFICATION FIELDS
    # ==========================================
    name = fields.Char(string="Item Description", required=True, tracking=True,
                      help="Customer description of the item/box/file")
    reference = fields.Char(string="Customer Reference", tracking=True,
                           help="Customer's internal reference number")
    company_id = fields.Many2one('res.company', default=lambda self: self.env.company, required=True)
    user_id = fields.Many2one('res.users', string='Created By',
                             default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True, tracking=True)

    # ==========================================
    # CUSTOMER INFORMATION
    # ==========================================
    customer_id = fields.Many2one('res.partner', string='Customer', required=True, tracking=True)
    customer_contact_id = fields.Many2one('res.partner', string='Customer Contact',
                                         domain="[('parent_id', '=', customer_id)]")
    department_id = fields.Many2one('records.department', string='Department', tracking=True)

    # ==========================================
    # ITEM DETAILS
    # ==========================================
    item_type = fields.Selection([
        ('records_box', 'Records Box'),
        ('file_folder', 'File/Folder'),
        ('document_set', 'Document Set'),
        ('media', 'Media (Tapes/Disks)'),
        ('equipment', 'Equipment/Hardware'),
        ('other', 'Other Item')
    ], string='Item Type', required=True, tracking=True, default='records_box')

    quantity = fields.Integer(string='Quantity', default=1, required=True, tracking=True,
                             help="Number of items (boxes, files, etc.)")
    estimated_weight = fields.Float(string='Estimated Weight (lbs)', tracking=True,
                                   help="Customer's estimate - will be verified at pickup")
    content_description = fields.Text(string='Content Description', tracking=True,
                                     help="Description of what's inside the item")
    
    # Size estimates for storage planning
    estimated_cubic_feet = fields.Float(string='Estimated Size (cubic feet)', tracking=True,
                                       help="For storage capacity planning")
    
    # ==========================================
    # STATUS AND WORKFLOW
    # ==========================================
    state = fields.Selection([
        ('declared', 'Customer Declared'),
        ('scheduled', 'Pickup Scheduled'),
        ('collected', 'Collected/Converted'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='declared', tracking=True, required=True)

    # ==========================================
    # PICKUP AND CONVERSION TRACKING
    # ==========================================
    creation_date = fields.Datetime(string='Declaration Date',
                                   default=fields.Datetime.now, required=True, tracking=True)
    scheduled_pickup_date = fields.Date(string='Scheduled Pickup Date', tracking=True)
    actual_pickup_date = fields.Date(string='Actual Pickup Date', tracking=True)
    
    pickup_request_id = fields.Many2one('pickup.request', string='Related Pickup Request',
                                       tracking=True)
    
    # Conversion to real inventory
    converted_to_box_id = fields.Many2one('records.box', string='Converted to Records Box',
                                         tracking=True, readonly=True)
    converted_date = fields.Datetime(string='Conversion Date', tracking=True, readonly=True)
    converted_by_id = fields.Many2one('res.users', string='Converted By', tracking=True, readonly=True)

    # ==========================================
    # BILLING FIELDS
    # ==========================================
    billable = fields.Boolean(string='Billable', default=True, tracking=True,
                              help="Should be charged same as regular inventory")
    monthly_storage_rate = fields.Float(string='Monthly Storage Rate', tracking=True,
                                       help="Monthly storage charge per item")
    total_storage_value = fields.Float(string='Total Storage Value',
                                      compute='_compute_storage_values', store=True,
                                      help="Total value for capacity planning")
    
    # Billing relationship
    billing_account_id = fields.Many2one('advanced.billing', string='Billing Account',
                                        related='customer_id.billing_account_id', store=True)

    # ==========================================
    # COMPUTED FIELDS
    # ==========================================
    days_in_system = fields.Integer(string='Days in System',
                                    compute='_compute_days_in_system',
                                    help="Days since customer declared this item")
    is_overdue_pickup = fields.Boolean(string='Pickup Overdue',
                                      compute='_compute_pickup_status',
                                      help="Scheduled pickup date has passed")
    storage_impact = fields.Float(string='Storage Impact',
                                 compute='_compute_storage_values', store=True,
                                 help="Storage space impact for capacity planning")
    retrieval_item_ids = fields.Char(string="Retrieval Item Ids", help="Items for retrieval")
    rate_id = fields.Many2one("res.partner", string="Rate Id", help="Applicable rate")

    @api.depends('creation_date')
    def _compute_days_in_system(self):
        """Calculate days since item was declared"""
        today = fields.Date.today()
        for record in self:
            if record.creation_date:
                creation_date = record.creation_date.date()
                record.days_in_system = (today - creation_date).days
            else:
                record.days_in_system = 0

    @api.depends('scheduled_pickup_date', 'state')
    def _compute_pickup_status(self):
        """Check if pickup is overdue"""
        today = fields.Date.today()
        for record in self:
            record.is_overdue_pickup = (
                record.state in ('declared', 'scheduled') and
                record.scheduled_pickup_date and
                record.scheduled_pickup_date < today
            )

    @api.depends('quantity', 'estimated_cubic_feet', 'monthly_storage_rate')
    def _compute_storage_values(self):
        """Calculate storage impact and billing values"""
        for record in self:
            # Storage impact for capacity planning
            record.storage_impact = record.quantity * (record.estimated_cubic_feet or 1.0)
            
            # Total storage value for billing
            record.total_storage_value = record.quantity * record.monthly_storage_rate

    # ==========================================
    # WORKFLOW ACTION METHODS
    # ==========================================
    def action_schedule_pickup(self):
        """Schedule pickup for transitory items"""
        for record in self:
            if record.state != 'declared':
                raise UserError(_('Only declared items can be scheduled for pickup'))
            
            if not record.scheduled_pickup_date:
                raise UserError(_('Please set a pickup date before scheduling'))
            
            record.write({'state': 'scheduled'})
            record.message_post(
                body=_('Pickup scheduled for %s') % record.scheduled_pickup_date,
                message_type='notification'
            )

    def action_convert_to_records_box(self):
        """Convert transitory item to actual records box after pickup"""
        self.ensure_one()
        
        if self.state != 'scheduled':
            raise UserError(_('Only scheduled items can be converted'))
        
        if self.converted_to_box_id:
            raise UserError(_('This item has already been converted'))
        
        # Create actual records box
        box_vals = {
            'name': f"Box from {self.name}",
            'customer_id': self.customer_id.id,
            'department_id': self.department_id.id,
            'description': self.content_description,
            'estimated_weight': self.estimated_weight,
            'state': 'active',
            'source_transitory_id': self.id,
        }
        
        # Add location if we have a default intake location
        default_location = self.env['records.location'].search([
            ('location_type', '=', 'intake')
        ], limit=1)
        if default_location:
            box_vals['location_id'] = default_location.id
        
        new_box = self.env['records.box'].create(box_vals)
        
        self.write({
            'state': 'collected',
            'converted_to_box_id': new_box.id,
            'converted_date': fields.Datetime.now(),
            'converted_by_id': self.env.user.id,
            'actual_pickup_date': fields.Date.today()
        })
        
        self.message_post(
            body=_('Converted to Records Box: %s') % new_box.name,
            message_type='notification'
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Created Records Box',
            'view_mode': 'form',
            'res_model': 'records.box',
            'res_id': new_box.id,
            'target': 'current',
        }

    def action_cancel_item(self):
        """Cancel transitory item"""
        for record in self:
            if record.state == 'collected':
                raise UserError(_('Cannot cancel items that have already been collected'))
            
            record.write({'state': 'cancelled'})
            record.message_post(
                body=_('Item cancelled by %s') % self.env.user.name,
                message_type='notification'
            )

    def action_create_pickup_request(self):
        """Create pickup request for these items"""
        self.ensure_one()
        
        pickup_vals = {
            'customer_id': self.customer_id.id,
            'requested_date': self.scheduled_pickup_date or fields.Date.today(),
            'description': f"Pickup for transitory items: {self.name}",
            'special_instructions': f"Collect item: {self.content_description}",
            'state': 'draft'
        }
        
        pickup_request = self.env['pickup.request'].create(pickup_vals)
        
        # Link this item to the pickup request
        self.write({'pickup_request_id': pickup_request.id})
        
        return {
            'type': 'ir.actions.act_window',
            'name': 'Pickup Request',
            'view_mode': 'form',
            'res_model': 'pickup.request',
            'res_id': pickup_request.id,
            'target': 'current',
        }

    # ==========================================
    # BILLING INTEGRATION METHODS
    # ==========================================
    def create_monthly_storage_charges(self):
        """Create monthly storage charges for transitory items
        Called by scheduled action to bill for storage space reservation"""
        
        items_to_bill = self.search([
            ('state', 'in', ('declared', 'scheduled')),
            ('billable', '=', True),
            ('monthly_storage_rate', '>', 0)
        ])
        
        for item in items_to_bill:
            if item.billing_account_id:
                # Create billing line for storage
                billing_line_vals = {
                    'billing_id': item.billing_account_id.id,
                    'product_id': self.env.ref('records_management.product_storage_transitory').id,
                    'quantity': item.quantity,
                    'unit_price': item.monthly_storage_rate,
                    'description': f"Transitory storage for {item.name}",
                    'date': fields.Date.today(),
                    'source_model': 'transitory.items',
                    'source_id': item.id,
                }
                
                self.env['advanced.billing.line'].create(billing_line_vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set default storage rates"""
        for vals in vals_list:
            # Set default storage rate based on item type
            if not vals.get('monthly_storage_rate') and vals.get('item_type'):
                item_type = vals['item_type']
                if item_type == 'records_box':
                    vals['monthly_storage_rate'] = 1.50  # Same as regular box storage
                elif item_type in ('file_folder', 'document_set'):
                    vals['monthly_storage_rate'] = 0.75
                elif item_type == 'media':
                    vals['monthly_storage_rate'] = 2.00
                else:
                    vals['monthly_storage_rate'] = 1.00
        
        return super().create(vals_list)

    # ==========================================
    # VALIDATION METHODS
    # ==========================================
    @api.constrains('quantity')
    def _check_quantity(self):
        """Validate quantity is positive"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_('Quantity must be greater than zero'))

    @api.constrains('scheduled_pickup_date')
    def _check_pickup_date(self):
        """Validate pickup date is not in the past"""
        for record in self:
            if record.scheduled_pickup_date and record.scheduled_pickup_date < fields.Date.today():
                if record.state == 'declared':  # Only check for new items
                    raise ValidationError(_('Pickup date cannot be in the past'))

    @api.constrains('estimated_weight', 'estimated_cubic_feet')
    def _check_estimates(self):
        """Validate estimates are reasonable"""
        for record in self:
            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_('Estimated weight cannot be negative'))
            if record.estimated_cubic_feet and record.estimated_cubic_feet < 0:
                raise ValidationError(_('Estimated size cannot be negative'))
    def action_done(self):
        """Mark as done"""
        self.write({'state': 'done'})
