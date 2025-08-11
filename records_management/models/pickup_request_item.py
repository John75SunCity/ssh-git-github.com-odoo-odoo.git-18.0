# -*- coding: utf-8 -*-
"""
Pickup Request Item Management Module

This module provides detailed line-item management for pickup requests within the Records
Management System. It enables granular tracking of individual items, containers, and documents
included in pickup operations with comprehensive audit trails and status management.

Key Features:
- Detailed line-item tracking for pickup requests with barcode integration
- Individual item status management through the pickup lifecycle
- Weight and dimension tracking for accurate logistics planning
- Special handling requirements and instructions for sensitive items
- Integration with inventory management and container tracking systems
- Real-time status updates and delivery confirmation workflows
- Cost tracking and billing integration for individual items

Business Processes:
1. Item Addition: Adding specific items to pickup requests with detailed specifications
2. Status Tracking: Individual item status management through pickup and delivery
3. Inventory Updates: Real-time inventory adjustments during pickup operations
4. Special Handling: Management of items requiring special security or handling procedures
5. Delivery Confirmation: Item-level delivery verification and customer confirmation
6. Billing Integration: Individual item cost calculation and billing allocation
7. Exception Handling: Management of damaged, missing, or incomplete items

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PickupRequestItem(models.Model):
    """
    Pickup Request Item - Individual items within pickup requests
    """

    _name = "pickup.request.item"
    _description = "Pickup Request Item"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "pickup_request_id, sequence, name"
    _rec_name = "name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Name",
        required=True,
        tracking=True,
        index=True,
        help="Name or identifier for the pickup item"
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True,
        index=True
    )
    user_id = fields.Many2one(
        "res.users",
        string="Responsible User",
        default=lambda self: self.env.user,
        tracking=True,
        index=True,
        help="User responsible for this item"
    )
    active = fields.Boolean(
        string="Active",
        default=True,
        help="Whether this item is active"
    )

    # ============================================================================
    # PICKUP REQUEST RELATIONSHIP
    # ============================================================================
    pickup_request_id = fields.Many2one(
        "pickup.request",
        string="Pickup Request",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent pickup request"
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order of items in the pickup request"
    )

    # ============================================================================
    # ITEM CLASSIFICATION
    # ============================================================================
    item_type = fields.Selection([
        ("container", "Document Container"),
        ("box", "File Box"),
        ("folder", "File Folder"),
        ("equipment", "Equipment"),
        ("media", "Storage Media"),
        ("bulk", "Bulk Materials"),
        ("special", "Special Handling Item"),
        ("other", "Other Item"),
    ], string="Item Type", required=True, tracking=True,
       help="Type of item being picked up")

    item_category = fields.Selection([
        ("document", "Document/Paper"),
        ("electronic", "Electronic Media"),
        ("hardware", "Computer Hardware"),
        ("confidential", "Confidential Material"),
        ("hazardous", "Hazardous Material"),
        ("general", "General Items"),
    ], string="Category", default="document",
       help="General category of the item")

    # ============================================================================
    # STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ("draft", "Draft"),
        ("confirmed", "Confirmed"),
        ("picked", "Picked Up"),
        ("in_transit", "In Transit"),
        ("delivered", "Delivered"),
        ("exception", "Exception"),
        ("cancelled", "Cancelled"),
    ], string="Status", default="draft", required=True, tracking=True,
       help="Current status of the pickup item")

    # ============================================================================
    # ITEM SPECIFICATIONS
    # ============================================================================
    description = fields.Text(
        string="Description",
        help="Detailed description of the item"
    )
    barcode = fields.Char(
        string="Barcode/QR Code",
        help="Barcode or QR code for item identification"
    )
    estimated_quantity = fields.Integer(
        string="Estimated Quantity",
        default=1,
        help="Estimated number of items"
    )
    actual_quantity = fields.Integer(
        string="Actual Quantity",
        help="Actual number of items picked up"
    )
    estimated_weight = fields.Float(
        string="Estimated Weight (lbs)",
        digits=(8, 2),
        help="Estimated weight in pounds"
    )
    actual_weight = fields.Float(
        string="Actual Weight (lbs)",
        digits=(8, 2),
        help="Actual weight measured during pickup"
    )
    dimensions = fields.Char(
        string="Dimensions (L×W×H)",
        help="Physical dimensions of the item"
    )

    # ============================================================================
    # SPECIAL HANDLING
    # ============================================================================
    special_handling = fields.Boolean(
        string="Special Handling Required",
        default=False,
        help="Whether item requires special handling"
    )
    handling_instructions = fields.Text(
        string="Handling Instructions",
        help="Special handling instructions for pickup team"
    )
    confidential = fields.Boolean(
        string="Confidential",
        default=False,
        help="Whether item contains confidential information"
    )
    chain_of_custody_required = fields.Boolean(
        string="Chain of Custody Required",
        default=False,
        help="Whether item requires chain of custody documentation"
    )
    witness_required = fields.Boolean(
        string="Customer Witness Required",
        default=False,
        help="Whether customer witness is required for pickup"
    )

    # ============================================================================
    # LOCATION AND TRACKING
    # ============================================================================
    pickup_location = fields.Char(
        string="Pickup Location",
        help="Specific location within customer site"
    )
    current_location = fields.Char(
        string="Current Location",
        help="Current location of the item"
    )
    destination_location = fields.Char(
        string="Destination Location",
        help="Final destination for the item"
    )

    # ============================================================================
    # CONTAINER RELATIONSHIPS
    # ============================================================================
    container_id = fields.Many2one(
        "records.container",
        string="Related Container",
        help="Associated container if applicable"
    )

    # ============================================================================
    # TIMING FIELDS
    # ============================================================================
    date_created = fields.Datetime(
        string="Date Created",
        default=fields.Datetime.now,
        required=True,
        help="When this item was added to the request"
    )
    date_confirmed = fields.Datetime(
        string="Date Confirmed",
        help="When this item was confirmed for pickup"
    )
    date_picked = fields.Datetime(
        string="Date Picked Up",
        help="When this item was actually picked up"
    )
    date_delivered = fields.Datetime(
        string="Date Delivered",
        help="When this item was delivered to destination"
    )

    # ============================================================================
    # BILLING AND COST TRACKING
    # ============================================================================
    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this item is billable to customer"
    )
    unit_cost = fields.Monetary(
        string="Unit Cost",
        currency_field="currency_id",
        help="Cost per unit for this item type"
    )
    total_cost = fields.Monetary(
        string="Total Cost",
        currency_field="currency_id",
        compute="_compute_total_cost",
        store=True,
        help="Total cost for this item"
    )
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        store=True
    )

    # ============================================================================
    # DOCUMENTATION AND NOTES
    # ============================================================================
    notes = fields.Text(
        string="Internal Notes",
        help="Internal notes about this item"
    )
    customer_notes = fields.Text(
        string="Customer Notes",
        help="Notes from customer about this item"
    )
    pickup_notes = fields.Text(
        string="Pickup Notes",
        help="Notes from pickup team about this item"
    )
    exception_notes = fields.Text(
        string="Exception Notes",
        help="Notes about any exceptions or issues"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        domain=lambda self: [("res_model", "=", self._name)],
    )
    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        domain=lambda self: [("model", "=", self._name)],
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Display name for the item"
    )

    @api.depends("name", "item_type", "pickup_request_id")
    def _compute_display_name(self):
        """Compute display name for the item"""
        for record in self:
            if record.pickup_request_id:
                record.display_name = _("[%s] %s - %s", 
                    record.pickup_request_id.name, 
                    record.name, 
                    dict(record._fields['item_type'].selection)[record.item_type] if record.item_type else ''
                )
            else:
                record.display_name = record.name

    @api.depends("actual_quantity", "unit_cost")
    def _compute_total_cost(self):
        """Compute total cost based on quantity and unit cost"""
        for record in self:
            if record.actual_quantity and record.unit_cost:
                record.total_cost = record.actual_quantity * record.unit_cost
            elif record.estimated_quantity and record.unit_cost:
                record.total_cost = record.estimated_quantity * record.unit_cost
            else:
                record.total_cost = 0.0

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the pickup item"""
        self.ensure_one()
        if self.state != "draft":
            raise UserError(_("Only draft items can be confirmed"))

        self.write({
            "state": "confirmed",
            "date_confirmed": fields.Datetime.now(),
        })
        self.message_post(body=_("Pickup item confirmed"))

    def action_pick_up(self):
        """Mark item as picked up"""
        self.ensure_one()
        if self.state not in ["confirmed"]:
            raise UserError(_("Only confirmed items can be picked up"))

        self.write({
            "state": "picked",
            "date_picked": fields.Datetime.now(),
        })
        self.message_post(body=_("Item picked up"))

    def action_mark_in_transit(self):
        """Mark item as in transit"""
        self.ensure_one()
        if self.state != "picked":
            raise UserError(_("Only picked up items can be marked in transit"))

        self.write({"state": "in_transit"})
        self.message_post(body=_("Item in transit"))

    def action_deliver(self):
        """Mark item as delivered"""
        self.ensure_one()
        if self.state != "in_transit":
            raise UserError(_("Only items in transit can be delivered"))

        self.write({
            "state": "delivered",
            "date_delivered": fields.Datetime.now(),
        })
        self.message_post(body=_("Item delivered successfully"))

    def action_mark_exception(self):
        """Mark item as having an exception"""
        self.ensure_one()
        self.write({"state": "exception"})
        self.message_post(body=_("Item marked as exception - requires attention"))

    def action_cancel(self):
        """Cancel the pickup item"""
        self.ensure_one()
        if self.state in ["delivered"]:
            raise UserError(_("Delivered items cannot be cancelled"))

        self.write({"state": "cancelled"})
        self.message_post(body=_("Pickup item cancelled"))

    def action_reset_to_draft(self):
        """Reset item to draft state"""
        self.ensure_one()
        if self.state in ["delivered"]:
            raise UserError(_("Delivered items cannot be reset to draft"))

        self.write({"state": "draft"})
        self.message_post(body=_("Pickup item reset to draft"))

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def create_naid_audit_log(self, event_type, description):
        """Create NAID compliance audit log entry"""
        self.ensure_one()
        if self.env.get('naid.audit.log'):
            self.env['naid.audit.log'].create({
                'event_type': event_type,
                'model_name': self._name,
                'record_id': self.id,
                'description': description,
                'pickup_request_id': self.pickup_request_id.id,
                'timestamp': fields.Datetime.now(),
                'user_id': self.env.user.id,
            })

    def get_item_summary(self):
        """Get item summary for reporting"""
        self.ensure_one()
        return {
            'name': self.name,
            'type': self.item_type,
            'category': self.item_category,
            'status': self.state,
            'quantity': self.actual_quantity or self.estimated_quantity,
            'weight': self.actual_weight or self.estimated_weight,
            'special_handling': self.special_handling,
            'confidential': self.confidential,
            'total_cost': self.total_cost,
        }

    def update_inventory(self):
        """Update inventory when item is picked up"""
        self.ensure_one()
        if self.container_id and self.state == 'picked':
            # Update container location and status
            self.container_id.write({
                'location_id': False,  # Remove from current location
                'state': 'in_transit',
            })

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('estimated_quantity', 'actual_quantity')
    def _check_quantities(self):
        """Validate quantities are positive"""
        for record in self:
            if record.estimated_quantity and record.estimated_quantity <= 0:
                raise ValidationError(_("Estimated quantity must be positive"))
            
            if record.actual_quantity and record.actual_quantity <= 0:
                raise ValidationError(_("Actual quantity must be positive"))

    @api.constrains('estimated_weight', 'actual_weight')
    def _check_weights(self):
        """Validate weights are positive"""
        for record in self:
            if record.estimated_weight and record.estimated_weight < 0:
                raise ValidationError(_("Estimated weight cannot be negative"))
            
            if record.actual_weight and record.actual_weight < 0:
                raise ValidationError(_("Actual weight cannot be negative"))

    @api.constrains('unit_cost')
    def _check_unit_cost(self):
        """Validate unit cost is not negative"""
        for record in self:
            if record.unit_cost and record.unit_cost < 0:
                raise ValidationError(_("Unit cost cannot be negative"))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults and create audit trails"""
        for vals in vals_list:
            if not vals.get('name'):
                sequence = self.env['ir.sequence'].next_by_code('pickup.request.item')
                vals['name'] = sequence or _('New Item')
        
        items = super().create(vals_list)
        
        for item in items:
            item.create_naid_audit_log('item_created', _('Pickup item created: %s', item.name))
        
        return items

    def write(self, vals):
        """Override write to create audit trails for important changes"""
        result = super().write(vals)
        
        if 'state' in vals:
            for record in self:
                record.create_naid_audit_log(
                    'state_changed',
                    _('Item state changed to %s', record.state)
                )
        
        if any(field in vals for field in ['actual_quantity', 'actual_weight']):
            for record in self:
                record.update_inventory()
        
        return result

    def unlink(self):
        """Override unlink to prevent deletion in certain states"""
        for record in self:
            if record.state in ['picked', 'in_transit', 'delivered']:
                raise UserError(_(
                    'Cannot delete pickup item %s in %s state',
                    record.name, record.state
                ))
        
        return super().unlink()

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def name_get(self):
        """Custom name_get to show more context"""
        result = []
        for record in self:
            name = record.name
            if record.pickup_request_id:
                name = _("[%s] %s", record.pickup_request_id.name, record.name)
            if record.item_type:
                type_label = dict(record._fields['item_type'].selection)[record.item_type]
                name = _("%s (%s)", name, type_label)
            result.append((record.id, name))
        return result

    @api.model
    def get_items_by_status(self, status_list=None):
        """Get items filtered by status"""
        domain = []
        if status_list:
            domain.append(('state', 'in', status_list))
        
        return self.search(domain)

    def get_weight_summary(self):
        """Get weight summary for pickup planning"""
        self.ensure_one()
        return {
            'estimated_weight': self.estimated_weight or 0.0,
            'actual_weight': self.actual_weight or 0.0,
            'weight_variance': (self.actual_weight or 0.0) - (self.estimated_weight or 0.0),
        }
