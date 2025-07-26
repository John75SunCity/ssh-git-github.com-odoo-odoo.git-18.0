# -*- coding: utf-8 -*-
"""
Enhanced work order management for shredding services with bin assignment
and customer preference integration.
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class WorkOrderShredding(models.Model):
    """Enhanced work order for shredding services with bin management"""
    _name = 'work.order.shredding'
    _description = 'Shredding Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'scheduled_date desc, name'
    _rec_name = 'name'

    # Core identification
    name = fields.Char(
        string='Work Order #',
        required=True,
        copy=False,
        readonly=True,
        index=True,
        default=lambda self: _('New'),
        tracking=True
    
    # Customer and service information
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        domain=[('is_company', '=', True)]
    
    customer_department_id = fields.Many2one(
        'records.department',
        string='Department',
        tracking=True,
        domain="[('partner_id', '=', customer_id)]"
    
    # Service configuration
    service_type = fields.Selection([
        ('standard', 'Standard (Off-Site)'),
        ('mobile', 'Mobile (On-Site)')
    
    # Shredding workflow type
    shredding_workflow = fields.Selection([
        ('external', 'External/On-Site Shredding'),
        ('managed_inventory', 'Managed Inventory Destruction')
       help="External: Shred customer's boxes at their location. Managed: Destroy boxes from our warehouse.")
    
    # Payment and billing
    billing_method = fields.Selection([
        ('immediate', 'Immediate Payment'),
        ('monthly', 'Monthly Billing')
    
    preferred_service_type = fields.Selection(
        related='customer_id.preferred_shredding_service',
        string='Customer Preferred Service',
        readonly=True
    
    # Bin assignment
    bin_ids = fields.One2many(
        'shredding.bin',
        'work_order_id',
        string='Assigned Bins'
    
    # Managed inventory destruction
    inventory_item_ids = fields.One2many(
        'shredding.inventory.item',
        'work_order_id',
        string='Inventory Items for Destruction',
        help="Items from managed warehouse inventory selected for destruction"
    
    # Combined item count
    bin_count = fields.Integer(
        string='Number of Bins',
        compute='_compute_item_counts',
        store=True
    
    inventory_item_count = fields.Integer(
        string='Number of Inventory Items',
        compute='_compute_item_counts',
        store=True
    
    total_item_count = fields.Integer(
        string='Total Items',
        compute='_compute_item_counts',
        store=True,
        help="Total bins + inventory items for destruction"
    
    # Scheduling
    scheduled_date = fields.Date(
        string='Scheduled Date',
        required=True,
        default=fields.Date.today,
        tracking=True
    
    scheduled_time = fields.Datetime(
        string='Scheduled Time',
        tracking=True
    
    # Personnel assignment
    technician_id = fields.Many2one(
        'res.users',
        string='Assigned Technician',
        tracking=True,
        domain=[('groups_id', 'in', [
            'records_management.group_shredding_technician'
        ])]
    
    supervisor_id = fields.Many2one(
        'res.users',
        string='Supervisor',
        tracking=True,
        domain=[('groups_id', 'in', [
            'records_management.group_records_manager'
        ])]
    
    # Status and workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('pending_approval', 'Pending Approval'),
        ('approved', 'Approved'),
        ('confirmed', 'Confirmed'),
        ('picklist_generated', 'Picklist Generated'),
        ('items_retrieved', 'Items Retrieved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    
    # Approval workflow (for managed inventory destruction)
    requires_approval = fields.Boolean(
        string='Requires Approval',
        compute='_compute_requires_approval',
        store=True,
        help="Managed inventory destruction requires customer approval"
    
    customer_approved = fields.Boolean(
        string='Customer Approved',
        tracking=True
    
    customer_approval_date = fields.Datetime(
        string='Customer Approval Date',
        tracking=True
    
    supervisor_approved = fields.Boolean(
        string='Supervisor Approved',
        tracking=True
    
    supervisor_approval_date = fields.Datetime(
        string='Supervisor Approval Date',
        tracking=True
    
    # Execution tracking
    actual_start_time = fields.Datetime(
        string='Actual Start Time',
        tracking=True
    
    actual_completion_time = fields.Datetime(
        string='Actual Completion Time',
        tracking=True
    
    # Customer confirmation
    customer_signature = fields.Binary(
        string='Customer Signature'
    
    customer_signature_date = fields.Datetime(
        string='Signature Date'
    
    customer_representative = fields.Char(
        string='Customer Representative'
    
    # Documentation
    notes = fields.Text(
        string='Work Order Notes'
    
    internal_notes = fields.Text(
        string='Internal Notes'
    
    # Pricing breakdown
    retrieval_cost = fields.Float(
        string='Retrieval Cost',
        compute='_compute_pricing_breakdown',
        store=True,
        help="Cost to retrieve items from warehouse shelves"
    
    permanent_removal_cost = fields.Float(
        string='Permanent Removal Cost',
        compute='_compute_pricing_breakdown',
        store=True,
        help="Cost for permanently removing items from inventory"
    
    shredding_cost = fields.Float(
        string='Shredding Cost',
        compute='_compute_pricing_breakdown',
        store=True,
        help="Cost for shredding/destruction service"
    
    service_call_cost = fields.Float(
        string='Service Call Cost',
        compute='_compute_pricing_breakdown',
        store=True,
        help="Cost for on-site service call (external shredding)"
    
    total_cost = fields.Float(
        string='Total Cost',
        compute='_compute_pricing_breakdown',
        store=True,
        tracking=True
    
    # Certificate and documentation
    certificate_issued = fields.Boolean(
        string='Certificate Issued',
        tracking=True
    
    certificate_number = fields.Char(
        string='Certificate Number',
        help="Destruction certificate reference number"
    
    certificate_date = fields.Date(
        string='Certificate Date'
    
    # Company and audit
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company
    
    create_uid = fields.Many2one(
        'res.users',
        string='Created by',
        readonly=True
    
    create_date = fields.Datetime(
        string='Created on',
        readonly=True

    @api.model
    def create(self, vals):
        """Generate sequence number on creation"""
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code(
                'work.order.shredding'
            ) or _('New')
        return super().create(vals)

    @api.depends('bin_ids', 'inventory_item_ids')
    def _compute_item_counts(self):
        """Compute counts for bins and inventory items"""
        for order in self:
            order.bin_count = len(order.bin_ids)
            order.inventory_item_count = len(order.inventory_item_ids)
            order.total_item_count = order.bin_count + order.inventory_item_count
    
    @api.depends('shredding_workflow')
    def _compute_billing_method(self):
        """Determine billing method based on workflow type"""
        for order in self:
            if order.shredding_workflow == 'managed_inventory':
                order.billing_method = 'monthly'
            else:
                order.billing_method = 'immediate'
    
    @api.depends('shredding_workflow')
    def _compute_requires_approval(self):
        """Managed inventory destruction requires approval"""
        for order in self:
            order.requires_approval = (order.shredding_workflow == 'managed_inventory')

    @api.depends('bin_ids', 'inventory_item_ids', 'shredding_workflow', 'service_type')
    def _compute_pricing_breakdown(self):
        """Compute detailed pricing breakdown for different scenarios"""
        for order in self:
            # Initialize costs
            retrieval_cost = 0.0
            permanent_removal_cost = 0.0
            shredding_cost = 0.0
            service_call_cost = 0.0
            
            # Get base rates (you'll need to implement shredding rates similar to retrieval rates)
            base_rates = self.env['shredding.base.rates'].search([
                ('active', '=', True)
            ], limit=1, order='effective_date desc')
            
            if not base_rates:
                # Create default rates if none exist
                base_rates = self.env['shredding.base.rates'].create({
                    'name': 'Default Shredding Rates',
                    'shredding_rate_per_box': 8.50,  # Example rate
                    'retrieval_rate_per_item': 3.50,  # Same as document retrieval
                    'permanent_removal_rate': 2.00,   # Additional fee for removal from inventory
                    'service_call_base_rate': 75.00,  # On-site service call
                })
            
            if order.shredding_workflow == 'managed_inventory':
                # Managed inventory destruction pricing
                total_items = order.inventory_item_count
                if total_items > 0:
                    # Retrieval cost (same as document retrieval)
                    retrieval_cost = base_rates.retrieval_rate_per_item * total_items
                    
                    # Permanent removal cost
                    permanent_removal_cost = base_rates.permanent_removal_rate * total_items
                    
                    # Shredding cost
                    shredding_cost = base_rates.shredding_rate_per_box * total_items
                
            else:
                # External/on-site shredding pricing
                total_bins = order.bin_count
                if total_bins > 0:
                    # Service call cost
                    service_call_cost = base_rates.service_call_base_rate
                    
                    # Shredding cost per bin
                    shredding_cost = base_rates.shredding_rate_per_box * total_bins
            
            # Apply customer-specific rates if available
            customer_rates = self.env['shredding.customer.rates'].search([
                ('customer_id', '=', order.customer_id.id),
                ('active', '=', True),
                ('effective_date', '<=', fields.Date.today()),
                '|',
                ('expiry_date', '=', False),
                ('expiry_date', '>=', fields.Date.today())
            ], limit=1, order='effective_date desc')
            
            if customer_rates:
                # Apply customer-specific multipliers or fixed rates
                if customer_rates.custom_shredding_rate > 0:
                    shredding_cost = customer_rates.custom_shredding_rate * order.total_item_count
                
                if customer_rates.custom_service_call_rate > 0:
                    service_call_cost = customer_rates.custom_service_call_rate
            
            # Set computed values
            order.retrieval_cost = retrieval_cost
            order.permanent_removal_cost = permanent_removal_cost
            order.shredding_cost = shredding_cost
            order.service_call_cost = service_call_cost
            order.total_cost = retrieval_cost + permanent_removal_cost + shredding_cost + service_call_cost

    @api.onchange('customer_id')
    def _onchange_customer_id(self):
        """Set default service type from customer preferences"""
        if self.customer_id and self.customer_id.preferred_shredding_service:
            self.service_type = self.customer_id.preferred_shredding_service

    def action_submit_for_approval(self):
        """Submit managed inventory destruction for approval"""
        self.ensure_one()
        if self.shredding_workflow != 'managed_inventory':
            raise UserError(_('Only managed inventory destruction requires approval.'))
        
        if not self.inventory_item_ids:
            raise UserError(_('Cannot submit without inventory items selected for destruction.'))
        
        self.write({'state': 'pending_approval'})
        
        # Send notification to customer for approval
        self.message_post(
            body=_('Destruction request submitted for approval. Total cost: $%.2f') % self.total_cost
        return True
    
    def action_customer_approve(self):
        """Customer approves the destruction"""
        self.ensure_one()
        if self.state != 'pending_approval':
            raise UserError(_('Work order must be pending approval.'))
        
        self.write({
            'customer_approved': True,
            'customer_approval_date': fields.Datetime.now()
        })
        
        # Check if supervisor approval is also required
        if self.customer_approved and self.supervisor_approved:
            self.write({'state': 'approved'})
        
        return True
    
    def action_supervisor_approve(self):
        """Supervisor approves the destruction"""
        self.ensure_one()
        if self.state != 'pending_approval':
            raise UserError(_('Work order must be pending approval.'))
        
        self.write({
            'supervisor_approved': True,
            'supervisor_approval_date': fields.Datetime.now(),
            'supervisor_id': self.env.user.id
        })
        
        # Check if both approvals are complete
        if self.customer_approved and self.supervisor_approved:
            self.write({'state': 'approved'})
        
        return True

    def action_confirm(self):
        """Confirm the work order"""
        self.ensure_one()
        
        # Check requirements based on workflow type
        if self.shredding_workflow == 'external':
            if not self.bin_ids:
                raise UserError(_('Cannot confirm external shredding without assigned bins.'))
            required_state = 'draft'
        else:  # managed_inventory
            if not self.inventory_item_ids:
                raise UserError(_('Cannot confirm managed inventory destruction without selected items.'))
            required_state = 'approved' if self.requires_approval else 'draft'
        
        if self.state != required_state:
            if required_state == 'approved':
                raise UserError(_('Managed inventory destruction must be approved before confirmation.'))
            else:
                raise UserError(_('Work order must be in draft state for confirmation.'))
        
        self.write({'state': 'confirmed'})
        return True
    
    def action_generate_picklist(self):
        """Generate picklist for managed inventory destruction"""
        self.ensure_one()
        if self.shredding_workflow != 'managed_inventory':
            raise UserError(_('Picklist only applies to managed inventory destruction.'))
        
        if self.state != 'confirmed':
            raise UserError(_('Work order must be confirmed to generate picklist.'))
        
        # Create picklist entries
        picklist_items = []
        for item in self.inventory_item_ids:
            picklist_items.append({
                'work_order_id': self.id,
                'box_id': item.box_id.id if item.box_id else False,
                'document_id': item.document_id.id if item.document_id else False,
                'location_id': item.current_location_id.id if item.current_location_id else False,
                'status': 'pending_pickup',
            })
        
        # Create picklist records
        for item_data in picklist_items:
            self.env['shredding.picklist.item'].create(item_data)
        
        self.write({'state': 'picklist_generated'})
        
        self.message_post(
            body=_('Picklist generated with %d items for warehouse retrieval.') % len(picklist_items)
        
        return {
            'name': _('Picklist Generated'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.picklist.item',
            'view_mode': 'tree,form',
            'domain': [('work_order_id', '=', self.id)],
            'context': {'default_work_order_id': self.id},
        }
    
    def action_items_retrieved(self):
        """Mark items as retrieved from warehouse"""
        self.ensure_one()
        if self.state != 'picklist_generated':
            raise UserError(_('Picklist must be generated first.'))
        
        self.write({'state': 'items_retrieved'})
        return True

    def action_start_work(self):
        """Start work execution"""
        self.ensure_one()
        
        required_states = ['confirmed']
        if self.shredding_workflow == 'managed_inventory':
            required_states = ['items_retrieved']
        
        if self.state not in required_states:
            if self.shredding_workflow == 'managed_inventory':
                raise UserError(_('Items must be retrieved from warehouse before starting shredding.'))
            else:
                raise UserError(_('Can only start confirmed work orders.'))
        
        self.write({
            'state': 'in_progress',
            'actual_start_time': fields.Datetime.now()
        })
        return True

    def action_complete_work(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete work orders that are in progress.'))
        
        # Mark all bins as completed
        self.bin_ids.write({'status': 'completed'})
        
        # Generate certificate number
        if not self.certificate_number:
            self.certificate_number = self.env['ir.sequence'].next_by_code('shredding.certificate') or 'CERT-' + str(self.id)
        
        self.write({
            'state': 'completed',
            'actual_completion_time': fields.Datetime.now(),
            'certificate_issued': True,
            'certificate_date': fields.Date.today()
        })
        
        # If managed inventory, update inventory status
        if self.shredding_workflow == 'managed_inventory':
            for item in self.inventory_item_ids:
                if item.box_id:
                    item.box_id.write({'state': 'destroyed', 'destruction_date': fields.Date.today()})
                if item.document_id:
                    item.document_id.write({'state': 'destroyed', 'destruction_date': fields.Date.today()})
        
        return True

    def action_cancel(self):
        """Cancel the work order"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_(
                'Cannot cancel completed work orders.'
            ))
        
        # Reset bin status
        self.bin_ids.write({'status': 'draft'})
        
        self.write({'state': 'cancelled'})
        return True

    def action_assign_bins(self):
        """Open wizard to assign bins to this work order"""
        self.ensure_one()
        return {
            'name': _('Assign Bins'),
            'type': 'ir.actions.act_window',
            'res_model': 'work.order.bin.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'default_customer_id': self.customer_id.id,
                'default_service_type': self.service_type,
            }
        }

    def action_view_bins(self):
        """View bins assigned to this work order"""
        self.ensure_one()
        return {
            'name': _('Work Order Bins'),
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.bin',
            'view_mode': 'tree,form',
            'domain': [('work_order_id', '=', self.id)],
            'context': {'default_work_order_id': self.id},
        }

    def action_generate_barcodes(self):
        """Generate barcodes for all bins in this work order"""
        self.ensure_one()
        generated_count = 0
        
        for bin_rec in self.bin_ids:
            if not bin_rec.barcode:
                # Generate 10-digit barcode with bin size and service type encoding
                bin_rec.generate_barcode()
                generated_count += 1
        
        if generated_count > 0:
            self.message_post(
                body=_('Generated barcodes for %d bins.') % generated_count
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Barcodes Generated'),
                'message': _('Generated %d barcodes successfully.') % generated_count,
                'type': 'success',
            }
        }

    def action_print_work_order(self):
        """Print work order with bin details"""
        self.ensure_one()
        return self.env.ref(
            'records_management.action_report_work_order_shredding'
        ).report_action(self)

class WorkOrderBinAssignmentWizard(models.TransientModel):
    """Wizard for assigning bins to work orders"""
    _name = 'work.order.bin.assignment.wizard'
    _description = 'Work Order Bin Assignment Wizard'

    work_order_id = fields.Many2one(
        'work.order.shredding',
        string='Work Order',
        required=True
    
    # Bin quantity selection
    bins_23_gallon = fields.Integer(
        string='23 Gallon Bins',
        default=0
    
    bins_32_gallon = fields.Integer(
        string='32 Gallon Bins',
        default=0
    
    bins_console = fields.Integer(
        string='Console Bins',
        default=0
    
    bins_64_gallon = fields.Integer(
        string='64 Gallon Bins',
        default=0
    
    bins_96_gallon = fields.Integer(
        string='96 Gallon Bins',
        default=0
    
    def action_assign_bins(self):
        """Create and assign bins to the work order"""
        self.ensure_one()
        
        bin_sizes = [
            ('23_gallon', self.bins_23_gallon),
            ('32_gallon', self.bins_32_gallon),
            ('console', self.bins_console),
            ('64_gallon', self.bins_64_gallon),
            ('96_gallon', self.bins_96_gallon),
        ]
        
        created_bins = 0
        
        for size, quantity in bin_sizes:
            for i in range(quantity):
                # Create bin
                bin_vals = {
                    'customer_id': self.customer_id.id,
                    'work_order_id': self.work_order_id.id,
                    'bin_size': size,
                    'service_type': self.service_type,
                    'status': 'assigned',
                }
                
                self.env['shredding.bin'].create(bin_vals)
                created_bins += 1
        
        if created_bins > 0:
            self.work_order_id.message_post(
                body=_('Assigned %d bins to work order.') % created_bins
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bins Assigned'),
                'message': _('Successfully assigned %d bins.') % created_bins,
                'type': 'success',
            }
        }
