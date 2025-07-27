# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class ShreddingInventoryItem(models.Model):
    """Items selected for managed inventory destruction"""
    _name = 'shredding.inventory.item'
    _description = 'Shredding Inventory Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence, id'
    _rec_name = 'display_name'

    # Core fields
    display_name = fields.Char(compute='_compute_display_name', store=True)
    sequence = fields.Integer(string='Sequence', default=10)
    work_order_id = fields.Many2one('work.order.shredding', string='Work Order', required=True, ondelete='cascade')
    
    # Item references (one of these must be set
    box_id = fields.Many2one('records.box', string='Records Box', tracking=True)
    document_id = fields.Many2one('records.document', string='Document', tracking=True)
    
    # Location tracking
    current_location_id = fields.Many2one('records.location', string='Current Location', tracking=True)
    original_location_id = fields.Many2one('records.location', string='Original Location', tracking=True)
    
    # Retrieval details
    retrieval_cost = fields.Float(string='Retrieval Cost', digits=(16, 2, compute='_compute_costs', store=True)
    permanent_removal_cost = fields.Float(string='Permanent Removal Cost', digits=(16, 2), compute='_compute_costs', store=True)
    shredding_cost = fields.Float(string='Shredding Cost', digits=(16, 2), compute='_compute_costs', store=True)
    total_cost = fields.Float(string='Total Cost', digits=(16, 2), compute='_compute_costs', store=True)
    
    # Status tracking
    status = fields.Selection([
        ('draft', 'Draft',
        ('approved', 'Approved for Destruction'),
        ('pending_pickup', 'Pending Pickup'),
        ('retrieved', 'Retrieved from Warehouse'),
        ('destroyed', 'Destroyed'),
        ('cancelled', 'Cancelled')
    ], default='draft', tracking=True
    
    # Approval tracking
    customer_approved = fields.Boolean(string='Customer Approved', tracking=True)
    supervisor_approved = fields.Boolean(string='Supervisor Approved', tracking=True)
    approval_date = fields.Datetime(string='Approval Date', tracking=True)
    
    # Destruction tracking
    retrieved_date = fields.Datetime(string='Retrieved Date', tracking=True)
    destruction_date = fields.Datetime(string='Destruction Date', tracking=True)
    retrieved_by = fields.Many2one('res.users', string='Retrieved By', tracking=True)
    destroyed_by = fields.Many2one('res.users', string='Destroyed By', tracking=True)
    
    # Notes
    retrieval_notes = fields.Text(string='Retrieval Notes')
    destruction_notes = fields.Text(string='Destruction Notes')
    
    # Company
    company_id = fields.Many2one('res.company', string='Company', related='work_order_id.company_id', store=True)
    
    @api.depends('box_id.name', 'document_id.name', 'work_order_id.name')
    def _compute_display_name(self):
        for record in self:
            if record.box_id:
                record.display_name = f"Box: {record.box_id.name}"
            elif record.document_id:
                record.display_name = f"Document: {record.document_id.name}"
            else:
                record.display_name = f"Item #{record.id}"
    
    @api.depends('work_order_id.retrieval_cost', 'work_order_id.permanent_removal_cost', 
                 'work_order_id.shredding_cost', 'work_order_id.inventory_item_count'
    def _compute_costs(self):
        for record in self:
            # Calculate per-item costs based on work order totals
            work_order = record.work_order_id
            item_count = work_order.inventory_item_count or 1  # Avoid division by zero
            
            # Distribute work order costs across all inventory items
            if item_count > 0:
                record.retrieval_cost = (work_order.retrieval_cost or 0.0 / item_count
                record.permanent_removal_cost = (work_order.permanent_removal_cost or 0.0) / item_count
                record.shredding_cost = (work_order.shredding_cost or 0.0) / item_count
            else:
                record.retrieval_cost = 0.0
                record.permanent_removal_cost = 0.0
                record.shredding_cost = 0.0
            
            record.total_cost = record.retrieval_cost + record.permanent_removal_cost + record.shredding_cost
    
    @api.constrains('box_id', 'document_id')
    def _check_item_reference(self):
        for record in self:
            if not record.box_id and not record.document_id:
                raise ValidationError(_('Must specify either a Records Box or Document for destruction.'))
            if record.box_id and record.document_id:
                raise ValidationError(_('Cannot specify both Records Box and Document. Choose one.'))
    
    def action_approve_item(self):
        """Approve this item for destruction"""
        self.ensure_one()
        if self.status != 'draft':
            raise UserError(_('Can only approve draft items.'))
        
        self.write({
            'status': 'approved',
            'approval_date': fields.Datetime.now(),
            'customer_approved': True,
            'supervisor_approved': True  # Simplified for now
        }
        return True
    
    def action_mark_retrieved(self:
        """Mark item as retrieved from warehouse"""
        self.ensure_one()
        if self.status != 'pending_pickup':
            raise UserError(_('Item must be pending pickup to mark as retrieved.'))
        
        self.write({
            'status': 'retrieved',
            'retrieved_date': fields.Datetime.now(),
            'retrieved_by': self.env.user.id
        }
        
        # Update original item location to show it's been retrieved
        if self.box_id:
            self.box_id.write({'state': 'retrieved_for_destruction'}
        elif self.document_id:
            self.document_id.write({'state': 'retrieved_for_destruction'})
        
        return True
    
    def action_mark_destroyed(self):
        """Mark item as destroyed"""
        self.ensure_one()
        if self.status != 'retrieved':
            raise UserError(_('Item must be retrieved before it can be destroyed.'))
        
        self.write({
            'status': 'destroyed',
            'destruction_date': fields.Datetime.now(),
            'destroyed_by': self.env.user.id
        }
        
        # Update original item to destroyed state
        if self.box_id:
            self.box_id.write({
                'state': 'destroyed',
                'destruction_date': fields.Date.today(
            }
        elif self.document_id:
            self.document_id.write({
                'state': 'destroyed',
                'destruction_date': fields.Date.today()
            }
        
        return True

class ShreddingPicklistItem(models.Model):
    """Picklist items for warehouse retrieval"""
    _name = 'shredding.picklist.item'
    _description = 'Shredding Picklist Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, location_id, sequence, id'
    _rec_name = 'display_name'

    # Core fields
    
    # Item references
    location_id = fields.Many2one('records.location', string='Location', required=True)
    
    # Pickup tracking
        ('picked', 'Picked',
        ('not_found', 'Not Found'),
        ('damaged', 'Damaged'),
        ('cancelled', 'Cancelled')
    ], default='pending_pickup', tracking=True
    
    picked_date = fields.Datetime(string='Picked Date')
    picked_by = fields.Many2one('res.users', string='Picked By')
    notes = fields.Text(string='Notes')
    
    # Company
    
    @api.depends('box_id.name', 'document_id.name', 'location_id.name'
    def _compute_display_name(self):
        for record in self:
            item_name = record.box_id.name if record.box_id else record.document_id.name if record.document_id else 'Unknown'
            location_name = record.location_id.name if record.location_id else 'No Location'
            record.display_name = f"{item_name} @ {location_name}"
    
    def action_mark_picked(self):
        """Mark item as picked"""
        self.ensure_one()
        if self.status != 'pending_pickup':
            raise UserError(_('Can only pick items that are pending pickup.'))
        
        self.write({
            'status': 'picked',
            'picked_date': fields.Datetime.now(),
            'picked_by': self.env.user.id
        }
        return True
    
    def action_mark_not_found(self):
        """Mark item as not found"""
        self.ensure_one()
        self.write({'status': 'not_found'})
        return True
