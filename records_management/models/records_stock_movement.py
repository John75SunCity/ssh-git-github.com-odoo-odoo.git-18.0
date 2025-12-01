# -*- coding: utf-8 -*-
"""
Records Stock Movement Tracking

This module provides comprehensive stock movement tracking for records containers,
integrating with Odoo's native stock system while maintaining customer-specific
audit trails and real-time location synchronization.

Key Features:
- Real-time movement tracking with timestamps
- Integration with stock.move and stock.quant
- Customer portal visibility with filtering
- Automated notifications and alerts
- NAID compliance audit trails
"""

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime
import logging

_logger = logging.getLogger(__name__)


class RecordsStockMovement(models.Model):
    """
    Stock Movement Tracking for Records Containers
    
    Tracks all movements of records containers through the warehouse system,
    providing complete audit trail and real-time location synchronization.
    """
    _name = 'records.stock.movement'
    _description = 'Records Container Stock Movement'
    _order = 'movement_date desc, id desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    
    display_name = fields.Char(
        string='Movement',
        compute='_compute_display_name',
        store=True,
        help='Human-readable movement description'
    )
    
    active = fields.Boolean(default=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    
    # ============================================================================
    # MOVEMENT DETAILS
    # ============================================================================
    
    container_id = fields.Many2one(
        'records.container',
        string='Container',
        required=True,
        ondelete='cascade',
        index=True,
        help='Container being moved'
    )
    
    movement_date = fields.Datetime(
        string='Movement Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='When the movement occurred'
    )
    
    movement_type = fields.Selection([
        ('location_change', 'Location Change'),
        ('pickup', 'Pickup'),
        ('delivery', 'Delivery'),
        ('transfer', 'Internal Transfer'),
        ('receipt', 'Receipt'),
        ('destruction', 'Destruction'),
        ('retrieval', 'Retrieval'),
        ('adjustment', 'Inventory Adjustment'),
    ], string='Movement Type', required=True, help='Type of movement')
    
    # ============================================================================
    # LOCATION TRACKING
    # ============================================================================
    
    from_location_id = fields.Many2one(
        'stock.location',
        string='From Location',
        help='Previous location (empty for initial receipt)'
    )
    
    to_location_id = fields.Many2one(
        'stock.location',
        string='To Location',
        required=True,
        help='New location after movement'
    )
    
    # ============================================================================
    # INTEGRATION WITH STOCK SYSTEM
    # ============================================================================
    
    stock_move_id = fields.Many2one(
        'stock.move',
        string='Stock Move',
        help='Related Odoo stock move (if applicable)'
    )
    
    quant_id = fields.Many2one(
        'stock.quant',
        string='Stock Quant',
        help='Related stock quant record'
    )
    
    # ============================================================================
    # AUDIT & RESPONSIBILITY
    # ============================================================================
    
    user_id = fields.Many2one(
        'res.users',
        string='Moved By',
        required=True,
        default=lambda self: self.env.user,
        help='User who performed the movement'
    )
    
    partner_id = fields.Many2one(
        'res.partner',
        related='container_id.partner_id',
        string='Customer',
        store=True,
        index=True,
        help='Container owner for filtering'
    )
    
    reason = fields.Text(
        string='Reason/Notes',
        help='Reason for movement or additional notes'
    )
    
    # ============================================================================
    # STATUS & METADATA
    # ============================================================================
    
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True)
    
    is_portal_visible = fields.Boolean(
        string='Portal Visible',
        default=True,
        help='Whether this movement is visible to customer in portal'
    )
    
    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    
    @api.depends('container_id', 'movement_type', 'to_location_id', 'movement_date')
    def _compute_display_name(self):
        for record in self:
            if record.container_id and record.movement_type:
                date_str = record.movement_date.strftime('%Y-%m-%d %H:%M') if record.movement_date else 'Unknown'
                location_str = record.to_location_id.complete_name if record.to_location_id else 'Unknown Location'
                record.display_name = f"{record.container_id.name} - {record._get_movement_type_display()} to {location_str} ({date_str})"
            else:
                record.display_name = 'Movement Record'
    
    def _get_movement_type_display(self):
        """Get human-readable movement type"""
        type_mapping = {
            'location_change': 'Moved',
            'pickup': 'Picked Up',
            'delivery': 'Delivered',
            'transfer': 'Transferred',
            'receipt': 'Received',
            'destruction': 'Destroyed',
            'retrieval': 'Retrieved',
            'adjustment': 'Adjusted',
        }
        return type_mapping.get(self.movement_type, self.movement_type.title())
    
    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    
    @api.model
    def create_movement(self, container, to_location, movement_type='location_change', reason=None, user=None):
        """
        Create a new movement record with all required tracking information.
        
        Args:
            container: records.container record
            to_location: stock.location record (destination)
            movement_type: type of movement (see selection field)
            reason: optional reason/notes
            user: user performing the movement (defaults to current user)
        
        Returns:
            records.stock.movement record
        """
        if not user:
            user = self.env.user
            
        # Get current location from container's quant
        from_location = container.current_location_id if container.current_location_id else False
        
        movement_vals = {
            'container_id': container.id,
            'movement_type': movement_type,
            'from_location_id': from_location.id if from_location else False,
            'to_location_id': to_location.id,
            'user_id': user.id,
            'reason': reason or '',
            'state': 'confirmed',
            'quant_id': container.quant_id.id if container.quant_id else False,
        }
        
        movement = self.create(movement_vals)
        
        # Log the movement
        _logger.info(f"Stock movement created: {movement.display_name}")
        
        # Post message to container
        container.message_post(
            body=_("Container moved to %s by %s") % (to_location.complete_name, user.name),
            message_type='notification'
        )
        
        return movement
    
    def action_confirm(self):
        """Confirm the movement and update stock quant if needed"""
        for record in self:
            if record.state != 'draft':
                continue
                
            # Update the container's stock quant location
            if record.quant_id and record.to_location_id:
                record.quant_id.sudo().write({
                    'location_id': record.to_location_id.id
                })
                
            # Update container location
            record.container_id.write({
                'location_id': record.to_location_id.id
            })
            
            record.write({'state': 'confirmed'})
    
    def action_complete(self):
        """Mark movement as completed"""
        self.write({'state': 'done'})
    
    def action_cancel(self):
        """Cancel the movement"""
        self.write({'state': 'cancelled'})
    
    # ============================================================================
    # PORTAL METHODS
    # ============================================================================
    
    def get_portal_movements(self, partner, limit=50, offset=0, filters=None):
        """
        Get movement history for portal display with proper security filtering.
        
        Args:
            partner: res.partner record (customer)
            limit: number of records to return
            offset: pagination offset
            filters: dict of additional filters
        
        Returns:
            dict with movements data and pagination info
        """
        domain = [
            ('partner_id', '=', partner.commercial_partner_id.id),
            ('is_portal_visible', '=', True),
            ('state', 'in', ['confirmed', 'done'])
        ]
        
        # Apply additional filters
        if filters:
            if filters.get('movement_type'):
                domain.append(('movement_type', '=', filters['movement_type']))
            if filters.get('date_from'):
                domain.append(('movement_date', '>=', filters['date_from']))
            if filters.get('date_to'):
                domain.append(('movement_date', '<=', filters['date_to']))
            if filters.get('container_id'):
                domain.append(('container_id', '=', filters['container_id']))
        
        # Get movements with pagination
        movements = self.search(domain, limit=limit, offset=offset, order='movement_date desc')
        total_count = self.search_count(domain)
        
        # Format for portal display
        movements_data = []
        for movement in movements:
            movements_data.append({
                'id': movement.id,
                'container_name': movement.container_id.name,
                'movement_type': movement._get_movement_type_display(),
                'from_location': movement.from_location_id.complete_name if movement.from_location_id else 'Initial Location',
                'to_location': movement.to_location_id.complete_name,
                'movement_date': movement.movement_date.strftime('%Y-%m-%d %H:%M'),
                'user_name': movement.user_id.name,
                'reason': movement.reason or '',
                'state': movement.state,
            })
        
        return {
            'movements': movements_data,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count,
        }
    
    # ============================================================================
    # CONSTRAINTS & VALIDATIONS
    # ============================================================================
    
    @api.constrains('from_location_id', 'to_location_id')
    def _check_locations(self):
        for record in self:
            if record.from_location_id and record.to_location_id:
                if record.from_location_id.id == record.to_location_id.id:
                    raise ValidationError(_("From and To locations cannot be the same."))
    
    @api.constrains('movement_date')
    def _check_movement_date(self):
        for record in self:
            if record.movement_date and record.movement_date > fields.Datetime.now():
                raise ValidationError(_("Movement date cannot be in the future."))


class RecordsContainerMovementMixin(models.AbstractModel):
    """
    Mixin to add movement tracking capabilities to containers
    """
    _name = 'records.container.movement.mixin'
    _description = 'Container Movement Tracking Mixin'
    
    movement_ids = fields.One2many(
        'records.stock.movement',
        'container_id',
        string='Movement History',
        help='Complete movement history for this container'
    )
    
    movement_count = fields.Integer(
        string='Total Movements',
        compute='_compute_movement_count',
        help='Number of recorded movements'
    )
    
    last_movement_date = fields.Datetime(
        string='Last Moved',
        compute='_compute_last_movement',
        store=True,
        help='When this container was last moved'
    )
    
    last_movement_location = fields.Char(
        string='Last Movement Location',
        compute='_compute_last_movement',
        store=True,
        help='Location from last movement'
    )
    
    @api.depends('movement_ids')
    def _compute_movement_count(self):
        for record in self:
            record.movement_count = len(record.movement_ids)
    
    @api.depends('movement_ids.movement_date', 'movement_ids.to_location_id')
    def _compute_last_movement(self):
        for record in self:
            last_movement = record.movement_ids.sorted('movement_date', reverse=True)[:1]
            if last_movement:
                record.last_movement_date = last_movement.movement_date
                record.last_movement_location = last_movement.to_location_id.complete_name
            else:
                record.last_movement_date = False
                record.last_movement_location = ''
    
    def action_view_movements(self):
        """Open movement history view"""
        self.ensure_one()
        return {
            'name': _('Movement History'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.stock.movement',
            'view_mode': 'list,form',
            'domain': [('container_id', '=', self.id)],
            'context': {'default_container_id': self.id},
        }
    
    def create_movement(self, to_location, movement_type='location_change', reason=None):
        """Shortcut method to create movement for this container"""
        return self.env['records.stock.movement'].create_movement(
            container=self,
            to_location=to_location,
            movement_type=movement_type,
            reason=reason
        )
