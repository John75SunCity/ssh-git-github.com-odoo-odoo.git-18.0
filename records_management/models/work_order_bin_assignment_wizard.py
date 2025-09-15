# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import logging

_logger = logging.getLogger(__name__)


class WorkOrderBinAssignmentWizard(models.TransientModel):
    """
    Work Order Bin Assignment Wizard - Manages the assignment of bins to work orders
    with intelligent matching based on location, capacity, and customer requirements.
    Integrates with real bin inventory and work order data.
    """
    _name = 'work.order.bin.assignment.wizard'
    _description = 'Work Order Bin Assignment Wizard'

    # Basic Information
    name = fields.Char(
        string='Bin Assignment',
        default='Work Order Bin Assignment',
        readonly=True
    )

    # Work Order Information
    work_order_id = fields.Many2one(
        'project.task',
        string='Work Order',
        required=True,
        domain=[('project_id.is_fsm', '=', True)],
        help='FSM work order requiring bin assignment'
    )

    work_order_name = fields.Char(
        string='Work Order Name',
        related='work_order_id.name',
        readonly=True
    )

    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        related='work_order_id.partner_id',
        readonly=True
    )

    work_order_stage = fields.Char(
        string='Stage',
        related='work_order_id.stage_id.name',
        readonly=True
    )

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        related='work_order_id.planned_date_begin',
        readonly=True
    )

    # Assignment Configuration
    assignment_type = fields.Selection([
        ('single', 'Assign Single Bin'),
        ('multiple', 'Assign Multiple Bins'),
        ('auto_match', 'Auto-Match Available Bins'),
        ('replace', 'Replace Existing Bin'),
        ('transfer', 'Transfer Between Work Orders')
    ], string='Assignment Type', required=True, default='single')

    # Bin Selection
    selected_bin_id = fields.Many2one(
        'shredding.service.bin',
        string='Selected Bin',
        help='Specific bin to assign'
    )

    bin_count = fields.Integer(
        string='Number of Bins',
        default=1,
        help='Number of bins to assign for multiple assignment'
    )

    # Auto-matching Criteria
    bin_size_preference = fields.Selection([
        ('small', 'Small Bins'),
        ('medium', 'Medium Bins'),
        ('large', 'Large Bins'),
        ('any', 'Any Size')
    ], string='Size Preference', default='any')

    location_proximity = fields.Boolean(
        string='Prioritize Location Proximity',
        default=True,
        help='Prefer bins closer to work order location'
    )

    customer_specific = fields.Boolean(
        string='Customer-Specific Bins Only',
        default=False,
        help='Only assign bins currently at this customer'
    )

    # Bin Status Filters
    include_available = fields.Boolean(
        string='Include Available Bins',
        default=True,
        help='Include bins that are available for assignment'
    )

    include_in_use = fields.Boolean(
        string='Include Bins In Use',
        default=False,
        help='Include bins currently assigned to other work orders'
    )

    # Current Assignments
    current_bins = fields.One2many(
        'shredding.service.bin',
        'shredding_service_id',
        related='work_order_id.bin_ids',
        string='Currently Assigned Bins',
        readonly=True
    )

    current_bin_count = fields.Integer(
        string='Currently Assigned',
        compute='_compute_current_assignments',
        help='Number of bins currently assigned'
    )

    # Available Bins
    available_bin_ids = fields.Many2many(
        'shredding.service.bin',
        string='Available Bins',
        compute='_compute_available_bins',
        help='Bins available for assignment based on criteria'
    )

    recommended_bins = fields.Many2many(
        'shredding.service.bin',
        'recommended_bin_rel',
        string='Recommended Bins',
        compute='_compute_recommended_bins',
        help='AI-recommended bins based on criteria and history'
    )

    # Assignment Results
    assignment_summary = fields.Text(
        string='Assignment Summary',
        readonly=True,
        help='Summary of assignment operations performed'
    )

    # Transfer Configuration (for transfer type)
    source_work_order_id = fields.Many2one(
        'project.task',
        string='Source Work Order',
        help='Work order to transfer bins from'
    )

    transfer_reason = fields.Selection([
        ('priority_change', 'Priority Change'),
        ('resource_reallocation', 'Resource Reallocation'),
        ('customer_request', 'Customer Request'),
        ('route_optimization', 'Route Optimization'),
        ('emergency', 'Emergency Reassignment')
    ], string='Transfer Reason', help='Reason for bin transfer')

    @api.depends('work_order_id')
    def _compute_current_assignments(self):
        """Compute current bin assignments"""
        for wizard in self:
            if wizard.work_order_id:
                # Count bins assigned to this work order
                bins = self.env['shredding.service.bin'].search([
                    ('shredding_service_id', '=', wizard.work_order_id.id)
                ])
                wizard.current_bin_count = len(bins)
            else:
                wizard.current_bin_count = 0

    @api.depends('assignment_type', 'bin_size_preference', 'customer_specific', 
                 'include_available', 'include_in_use', 'work_order_id')
    def _compute_available_bins(self):
        """Compute available bins based on criteria"""
        for wizard in self:
            domain = []
            
            # Status filter
            if wizard.include_available and not wizard.include_in_use:
                domain.append(('status', '=', 'active'))
                domain.append(('shredding_service_id', '=', False))
            elif wizard.include_in_use and not wizard.include_available:
                domain.append(('shredding_service_id', '!=', False))
            elif wizard.include_available and wizard.include_in_use:
                domain.append(('status', '=', 'active'))
            else:
                # Neither selected - no bins available
                wizard.available_bin_ids = [(6, 0, [])]
                continue
            
            # Size preference
            if wizard.bin_size_preference != 'any':
                size_mapping = {
                    'small': ['small', '32_gallon'],
                    'medium': ['medium', '64_gallon'],
                    'large': ['large', '96_gallon', 'extra_large']
                }
                sizes = size_mapping.get(wizard.bin_size_preference, [])
                if sizes:
                    domain.append(('bin_size', 'in', sizes))
            
            # Customer-specific filter
            if wizard.customer_specific and wizard.customer_id:
                domain.append(('current_customer_id', '=', wizard.customer_id.id))
            
            # Exclude bins already assigned to this work order
            if wizard.work_order_id:
                domain.append(('shredding_service_id', '!=', wizard.work_order_id.id))
            
            available_bins = self.env['shredding.service.bin'].search(domain)
            wizard.available_bin_ids = [(6, 0, available_bins.ids)]

    @api.depends('available_bin_ids', 'work_order_id', 'location_proximity')
    def _compute_recommended_bins(self):
        """Compute AI-recommended bins based on intelligent matching"""
        for wizard in self:
            if not wizard.available_bin_ids or not wizard.work_order_id:
                wizard.recommended_bins = [(6, 0, [])]
                continue
            
            # Score each available bin
            bin_scores = []
            work_order = wizard.work_order_id
            
            for bin_obj in wizard.available_bin_ids:
                score = 0
                
                # Location proximity scoring
                if wizard.location_proximity and work_order.partner_id:
                    if bin_obj.current_customer_id == work_order.partner_id:
                        score += 50  # Same customer
                    elif bin_obj.last_scan_customer_id == work_order.partner_id:
                        score += 30  # Previously at this customer
                    elif not bin_obj.current_customer_id:
                        score += 20  # Available for deployment
                
                # Size optimization scoring
                if hasattr(work_order, 'estimated_bin_requirement'):
                    required_size = work_order.estimated_bin_requirement
                    if bin_obj.bin_size == required_size:
                        score += 40
                    elif bin_obj.bin_size in ['medium', '64_gallon']:
                        score += 25  # Medium is generally versatile
                
                # Service history scoring
                if hasattr(bin_obj, 'service_success_rate'):
                    if bin_obj.service_success_rate > 0.9:
                        score += 20
                    elif bin_obj.service_success_rate > 0.7:
                        score += 10
                
                # Fill level optimization
                if hasattr(bin_obj, 'current_fill_level'):
                    if bin_obj.current_fill_level in ['empty', 'quarter']:
                        score += 15  # Ready for service
                    elif bin_obj.current_fill_level == 'half':
                        score += 10
                
                # Maintenance status
                if bin_obj.status == 'active':
                    score += 25
                elif bin_obj.status == 'maintenance':
                    score -= 50
                
                # Recent service history
                if hasattr(bin_obj, 'last_service_date') and bin_obj.last_service_date:
                    days_since_service = (fields.Date.today() - bin_obj.last_service_date.date()).days
                    if days_since_service > 30:
                        score += 15  # Needs service
                    elif days_since_service < 7:
                        score -= 10  # Recently serviced
                
                bin_scores.append((bin_obj.id, score))
            
            # Sort by score and take top recommendations
            bin_scores.sort(key=lambda x: x[1], reverse=True)
            recommended_ids = [bin_id for bin_id, score in bin_scores[:min(5, len(bin_scores))]]
            
            wizard.recommended_bins = [(6, 0, recommended_ids)]

    @api.onchange('assignment_type')
    def _onchange_assignment_type(self):
        """Reset fields when assignment type changes"""
        if self.assignment_type == 'multiple':
            self.bin_count = 3
        elif self.assignment_type == 'single':
            self.bin_count = 1

    @api.onchange('selected_bin_id')
    def _onchange_selected_bin(self):
        """Validate selected bin availability"""
        if self.selected_bin_id:
            if self.selected_bin_id.shredding_service_id and self.selected_bin_id.shredding_service_id != self.work_order_id:
                return {
                    'warning': {
                        'title': _('Bin Already Assigned'),
                        'message': _('This bin is already assigned to work order: %s') % self.selected_bin_id.shredding_service_id.name
                    }
                }

    def action_assign_bins(self):
        """Execute bin assignment based on configuration"""
        self.ensure_one()
        
        if not self.work_order_id:
            raise ValidationError(_("Please select a work order"))
        
        if self.assignment_type == 'single':
            return self._assign_single_bin()
        elif self.assignment_type == 'multiple':
            return self._assign_multiple_bins()
        elif self.assignment_type == 'auto_match':
            return self._auto_assign_bins()
        elif self.assignment_type == 'replace':
            return self._replace_bins()
        elif self.assignment_type == 'transfer':
            return self._transfer_bins()
        
        return {'type': 'ir.actions.act_window_close'}

    def _assign_single_bin(self):
        """Assign a single bin to the work order"""
        if not self.selected_bin_id:
            # Use first recommended bin if none selected
            if self.recommended_bins:
                self.selected_bin_id = self.recommended_bins[0]
            else:
                raise ValidationError(_("Please select a bin to assign"))
        
        # Check if bin is available
        if self.selected_bin_id.shredding_service_id and self.selected_bin_id.shredding_service_id != self.work_order_id:
            if not self.include_in_use:
                raise ValidationError(_("Selected bin is already assigned to another work order"))
        
        # Assign bin to work order
        self.selected_bin_id.write({
            'shredding_service_id': self.work_order_id.id,
            'status': 'active'
        })
        
        # Create assignment history
        self._create_assignment_history(self.selected_bin_id, 'assigned')
        
        self.assignment_summary = f"Successfully assigned bin {self.selected_bin_id.barcode} to work order {self.work_order_id.name}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bin Assigned'),
                'message': _('Bin %s assigned to work order %s') % (self.selected_bin_id.barcode, self.work_order_id.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _assign_multiple_bins(self):
        """Assign multiple bins to the work order"""
        if self.bin_count <= 0:
            raise ValidationError(_("Please specify number of bins to assign"))
        
        if self.bin_count > len(self.available_bin_ids):
            raise ValidationError(_("Not enough available bins. Available: %d, Requested: %d") % 
                                (len(self.available_bin_ids), self.bin_count))
        
        # Use recommended bins first, then available bins
        bins_to_assign = []
        
        # Take from recommended bins first
        for bin_obj in self.recommended_bins[:self.bin_count]:
            bins_to_assign.append(bin_obj)
        
        # Fill remaining from available bins
        remaining_needed = self.bin_count - len(bins_to_assign)
        if remaining_needed > 0:
            for bin_obj in self.available_bin_ids:
                if bin_obj not in bins_to_assign and len(bins_to_assign) < self.bin_count:
                    bins_to_assign.append(bin_obj)
        
        # Assign bins
        assigned_barcodes = []
        for bin_obj in bins_to_assign:
            bin_obj.write({
                'shredding_service_id': self.work_order_id.id,
                'status': 'active'
            })
            self._create_assignment_history(bin_obj, 'assigned')
            assigned_barcodes.append(bin_obj.barcode)
        
        self.assignment_summary = f"Successfully assigned {len(bins_to_assign)} bins to work order {self.work_order_id.name}:\n" + \
                                 "\n".join(f"• {barcode}" for barcode in assigned_barcodes)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bins Assigned'),
                'message': _('%d bins assigned to work order %s') % (len(bins_to_assign), self.work_order_id.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _auto_assign_bins(self):
        """Automatically assign best-matching bins"""
        if not self.recommended_bins:
            raise ValidationError(_("No recommended bins available for auto-assignment"))
        
        # Assign top 3 recommended bins (or less if not available)
        bins_to_assign = self.recommended_bins[:min(3, len(self.recommended_bins))]
        
        assigned_barcodes = []
        for bin_obj in bins_to_assign:
            bin_obj.write({
                'shredding_service_id': self.work_order_id.id,
                'status': 'active'
            })
            self._create_assignment_history(bin_obj, 'auto_assigned')
            assigned_barcodes.append(bin_obj.barcode)
        
        self.assignment_summary = f"Auto-assigned {len(bins_to_assign)} bins to work order {self.work_order_id.name}:\n" + \
                                 "\n".join(f"• {barcode}" for barcode in assigned_barcodes)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Auto-Assignment Complete'),
                'message': _('%d bins auto-assigned to work order %s') % (len(bins_to_assign), self.work_order_id.name),
                'type': 'success',
                'sticky': False,
            }
        }

    def _replace_bins(self):
        """Replace existing bin assignments"""
        if not self.current_bins:
            raise ValidationError(_("No bins currently assigned to replace"))
        
        if not self.selected_bin_id:
            raise ValidationError(_("Please select a replacement bin"))
        
        # Remove current assignments
        old_barcodes = []
        for bin_obj in self.current_bins:
            old_barcodes.append(bin_obj.barcode)
            bin_obj.write({'shredding_service_id': False})
            self._create_assignment_history(bin_obj, 'unassigned')
        
        # Assign new bin
        self.selected_bin_id.write({
            'shredding_service_id': self.work_order_id.id,
            'status': 'active'
        })
        self._create_assignment_history(self.selected_bin_id, 'replacement_assigned')
        
        self.assignment_summary = f"Replaced {len(old_barcodes)} bins with bin {self.selected_bin_id.barcode}\n" + \
                                 f"Removed: {', '.join(old_barcodes)}"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bins Replaced'),
                'message': _('Replaced %d bins with bin %s') % (len(old_barcodes), self.selected_bin_id.barcode),
                'type': 'success',
                'sticky': False,
            }
        }

    def _transfer_bins(self):
        """Transfer bins between work orders"""
        if not self.source_work_order_id:
            raise ValidationError(_("Please select source work order"))
        
        if not self.transfer_reason:
            raise ValidationError(_("Please specify transfer reason"))
        
        # Get bins from source work order
        source_bins = self.env['shredding.service.bin'].search([
            ('shredding_service_id', '=', self.source_work_order_id.id)
        ])
        
        if not source_bins:
            raise ValidationError(_("Source work order has no bins to transfer"))
        
        # Transfer bins
        transferred_barcodes = []
        for bin_obj in source_bins:
            # Create history for source
            self._create_assignment_history(bin_obj, 'transferred_out', 
                                          f"To: {self.work_order_id.name}, Reason: {self.transfer_reason}")
            
            # Transfer to target
            bin_obj.write({'shredding_service_id': self.work_order_id.id})
            
            # Create history for target
            self._create_assignment_history(bin_obj, 'transferred_in',
                                          f"From: {self.source_work_order_id.name}, Reason: {self.transfer_reason}")
            
            transferred_barcodes.append(bin_obj.barcode)
        
        self.assignment_summary = f"Transferred {len(source_bins)} bins from {self.source_work_order_id.name} to {self.work_order_id.name}\n" + \
                                 f"Reason: {self.transfer_reason}\n" + \
                                 "Bins: " + ", ".join(transferred_barcodes)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bins Transferred'),
                'message': _('Transferred %d bins between work orders') % len(source_bins),
                'type': 'success',
                'sticky': False,
            }
        }

    def _create_assignment_history(self, bin_obj, action, notes=None):
        """Create assignment history record"""
        try:
            history_vals = {
                'bin_id': bin_obj.id,
                'work_order_id': self.work_order_id.id,
                'action': action,
                'user_id': self.env.user.id,
                'date': fields.Datetime.now(),
                'notes': notes or f"Assignment via wizard: {action}"
            }
            
            # Try to create history record if model exists
            if hasattr(self.env, 'bin.assignment.history'):
                self.env['bin.assignment.history'].create(history_vals)
            else:
                # Fallback: create activity or log message
                bin_obj.message_post(
                    body=f"Bin assignment {action} for work order {self.work_order_id.name}",
                    subject="Bin Assignment"
                )
        except Exception as e:
            _logger.warning(f"Could not create assignment history: {e}")

    def action_preview_assignment(self):
        """Preview assignment without executing"""
        self.ensure_one()
        
        preview_data = {
            'work_order': self.work_order_id.name,
            'assignment_type': self.assignment_type,
            'recommended_count': len(self.recommended_bins),
            'available_count': len(self.available_bin_ids),
            'current_count': self.current_bin_count
        }
        
        if self.recommended_bins:
            recommended_barcodes = [bin_obj.barcode for bin_obj in self.recommended_bins[:5]]
            preview_message = f"Work Order: {self.work_order_id.name}\n" + \
                            f"Assignment Type: {self.assignment_type}\n" + \
                            f"Recommended Bins: {', '.join(recommended_barcodes)}\n" + \
                            f"Available: {len(self.available_bin_ids)} bins\n" + \
                            f"Currently Assigned: {self.current_bin_count} bins"
        else:
            preview_message = f"No bins available for assignment with current criteria"
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Assignment Preview'),
                'message': preview_message,
                'type': 'info',
                'sticky': True,
            }
        }
