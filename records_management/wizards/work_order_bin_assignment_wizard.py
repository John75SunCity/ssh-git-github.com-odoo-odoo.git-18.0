# -*- coding: utf-8 -*-
"""
Work Order Bin Assignment Wizard

This wizard manages the assignment of bins to work orders for efficient document
processing and NAID compliance tracking. Supports bulk operations and audit trails.

Key Features:
- Bulk bin assignment to work orders
- NAID compliance validation
- Capacity and availability checking
- Audit trail creation
- Integration with FSM workflows
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderBinAssignmentWizard(models.TransientModel):
    _name = 'work.order.bin.assignment.wizard'
    _description = 'Work Order Bin Assignment Wizard'
    _inherit = ['mail.thread']

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Assignment Name',
        required=True,
        default=lambda self: _('Bin Assignment - %s') % fields.Date.today(),
        tracking=True,
        help='Name for this bin assignment operation'
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='Assigned User',
        default=lambda self: self.env.user,
        required=True,
        tracking=True
    )

    # ============================================================================
    # WORK ORDER AND BIN FIELDS
    # ============================================================================
    work_order_ids = fields.Many2many(
        'file.retrieval.work.order',
        string='Work Orders',
        required=True,
        help='Work orders to assign bins to'
    )

    available_bin_ids = fields.Many2many(
        'records.container',
        'wizard_available_bin_rel',
        'wizard_id', 'bin_id',
        string='Available Bins',
        compute='_compute_available_bins',
        help='Bins available for assignment'
    )

    selected_bin_ids = fields.Many2many(
        'records.container',
        'wizard_selected_bin_rel',
        'wizard_id', 'bin_id',
        string='Selected Bins',
        help='Bins selected for assignment'
    )

    # ============================================================================
    # ASSIGNMENT CONFIGURATION
    # ============================================================================
    assignment_type = fields.Selection([
        ('manual', 'Manual Selection'),
        ('auto_optimal', 'Auto - Optimal Capacity'),
        ('auto_location', 'Auto - By Location'),
        ('auto_priority', 'Auto - By Priority')
    ], string='Assignment Type', default='manual', required=True)

    max_bins_per_order = fields.Integer(
        string='Max Bins per Order',
        default=5,
        help='Maximum number of bins to assign per work order'
    )

    prioritize_empty_bins = fields.Boolean(
        string='Prioritize Empty Bins',
        default=True,
        help='Prioritize empty bins for new assignments'
    )

    # ============================================================================
    # STATUS AND VALIDATION FIELDS
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('validated', 'Validated'),
        ('assigned', 'Assigned')
    ], string='State', default='draft', tracking=True)

    validation_message = fields.Text(
        string='Validation Message',
        readonly=True
    )

    total_capacity_needed = fields.Float(
        string='Total Capacity Needed (CF)',
        compute='_compute_capacity_metrics',
        help='Total cubic feet capacity needed'
    )

    available_capacity = fields.Float(
        string='Available Capacity (CF)',
        compute='_compute_capacity_metrics',
        help='Total available capacity in selected bins'
    )

    # ============================================================================
    # NOTES AND COMMENTS
    # ============================================================================
    notes = fields.Text(
        string='Assignment Notes',
        help='Additional notes for this bin assignment'
    )

    assignment_reason = fields.Selection([
        ('new_pickup', 'New Pickup Service'),
        ('reorganization', 'Storage Reorganization'),
        ('capacity_optimization', 'Capacity Optimization'),
        ('location_change', 'Location Change'),
        ('emergency', 'Emergency Assignment')
    ], string='Assignment Reason', default='new_pickup')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('work_order_ids', 'assignment_type')
    def _compute_available_bins(self):
        """Compute available bins based on assignment type and work orders"""
        for wizard in self:
            domain = [
                ('state', '=', 'available'),
                ('company_id', '=', wizard.company_id.id)
            ]

            if wizard.prioritize_empty_bins:
                domain.append(('capacity_used_percentage', '<', 50))

            if wizard.assignment_type == 'auto_location' and wizard.work_order_ids:
                # Filter by location proximity
                locations = wizard.work_order_ids.mapped('pickup_location_id')
                if locations:
                    domain.append(('location_id', 'in', locations.ids))

            wizard.available_bin_ids = self.env['records.container'].search(domain)

    @api.depends('work_order_ids', 'selected_bin_ids')
    def _compute_capacity_metrics(self):
        """Compute capacity metrics for validation"""
        for wizard in self:
            # Calculate total capacity needed from work orders
            total_needed = sum(wizard.work_order_ids.mapped('estimated_volume_cf'))
            wizard.total_capacity_needed = total_needed

            # Calculate available capacity from selected bins
            total_available = sum(wizard.selected_bin_ids.mapped('available_capacity_cf'))
            wizard.available_capacity = total_available

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('selected_bin_ids', 'work_order_ids')
    def _validate_assignment_capacity(self):
        """Validate that selected bins have sufficient capacity"""
        for wizard in self:
            if wizard.selected_bin_ids and wizard.work_order_ids:
                if wizard.available_capacity < wizard.total_capacity_needed:
                    raise UserError(_('Insufficient bin capacity. Available: %.2f CF, Needed: %.2f CF') % (
                        wizard.available_capacity,
                        wizard.total_capacity_needed
                    ))

    def _validate_assignment_rules(self):
        """Validate assignment rules and business constraints"""
        self.ensure_one()

        if not self.work_order_ids:
            raise UserError(_('Please select at least one work order'))

        if not self.selected_bin_ids and self.assignment_type == 'manual':
            raise UserError(_('Please select at least one bin for manual assignment'))

        # Check for conflicting assignments
        existing_assignments = self.env['file.retrieval.work.order'].search([
            ('assigned_bin_ids', 'in', self.selected_bin_ids.ids),
            ('state', 'in', ['confirmed', 'in_progress']),
            ('id', 'not in', self.work_order_ids.ids)
        ])

        if existing_assignments:
            raise UserError(_('Some selected bins are already assigned to other active work orders: %s') % (
                ', '.join(existing_assignments.mapped('name'))
            ))

        return True

    # ============================================================================
    # AUTO ASSIGNMENT METHODS
    # ============================================================================
    def _auto_assign_optimal_capacity(self):
        """Automatically assign bins based on optimal capacity utilization"""
        self.ensure_one()

        assigned_bins = self.env['records.container']
        remaining_capacity = self.total_capacity_needed

        # Sort bins by efficiency (capacity vs location proximity)
        available_bins = self.available_bin_ids.sorted(
            key=lambda b: (b.available_capacity_cf, -b.location_priority),
            reverse=True
        )

        for bin_record in available_bins:
            if remaining_capacity <= 0:
                break

            if len(assigned_bins) >= self.max_bins_per_order:
                break

            assigned_bins |= bin_record
            remaining_capacity -= bin_record.available_capacity_cf

        return assigned_bins

    def _auto_assign_by_location(self):
        """Automatically assign bins based on location proximity"""
        self.ensure_one()

        assigned_bins = self.env['records.container']
        work_order_locations = self.work_order_ids.mapped('pickup_location_id')

        for location in work_order_locations:
            location_bins = self.available_bin_ids.filtered(
                lambda b, _loc_id=location.id: b.location_id.id == _loc_id
            )[:self.max_bins_per_order]

            assigned_bins |= location_bins

        return assigned_bins[:self.max_bins_per_order]

    def _auto_assign_by_priority(self):
        """Automatically assign bins based on work order priority"""
        self.ensure_one()

        # Sort work orders by priority
        sorted_orders = self.work_order_ids.sorted('priority', reverse=True)
        assigned_bins = self.env['records.container']

        for order in sorted_orders:
            if len(assigned_bins) >= self.max_bins_per_order:
                break

            # Find best bin for this order
            suitable_bins = self.available_bin_ids.filtered(
                lambda b, _needed_cf=order.estimated_volume_cf: b.available_capacity_cf >= _needed_cf
            )

            if suitable_bins:
                assigned_bins |= suitable_bins[0]

        return assigned_bins

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_validate_assignment(self):
        """Validate the assignment configuration"""
        self.ensure_one()

        try:
            self._validate_assignment_rules()

            # Perform auto-assignment if needed
            if self.assignment_type != 'manual':
                if self.assignment_type == 'auto_optimal':
                    self.selected_bin_ids = self._auto_assign_optimal_capacity()
                elif self.assignment_type == 'auto_location':
                    self.selected_bin_ids = self._auto_assign_by_location()
                elif self.assignment_type == 'auto_priority':
                    self.selected_bin_ids = self._auto_assign_by_priority()

            # Final validation
            self._validate_assignment_capacity()

            self.write({
                'state': 'validated',
                'validation_message': _('Assignment validated successfully. Ready to execute.')
            })

        except UserError as e:
            self.write({
                'state': 'draft',
                'validation_message': str(e)
            })
            raise

        return self._return_wizard_form()

    def action_execute(self):
        """Execute the bin assignment operation"""
        self.ensure_one()

        if self.state != 'validated':
            self.action_validate_assignment()

        # Perform the actual assignment
        assignment_count = 0
        for work_order in self.work_order_ids:
            # Assign bins to work order
            bins_for_order = self.selected_bin_ids[:self.max_bins_per_order]
            work_order.write({
                'assigned_bin_ids': [(6, 0, bins_for_order.ids)]
            })

            # Update bin states
            bins_for_order.write({
                'state': 'assigned',
                'assigned_work_order_id': work_order.id
            })

            assignment_count += len(bins_for_order)

            # Create NAID audit log
            self._create_naid_audit_log(work_order, bins_for_order)

        self.write({'state': 'assigned'})

        # Show success message
        return self._show_success_message(assignment_count)

    def action_cancel(self):
        """Cancel the wizard operation"""
        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _create_naid_audit_log(self, work_order, assigned_bins):
        """Create NAID compliance audit log for bin assignment"""
        self.env['naid.audit.log'].create({
            'name': _('Bin Assignment: %s') % work_order.name,
            'activity_type': 'bin_assignment',
            'work_order_id': work_order.id,
            'container_ids': [(6, 0, assigned_bins.ids)],
            'performed_by': self.env.user.id,
            'activity_date': fields.Datetime.now(),
            'description': _('Assigned %d bins to work order %s via wizard') % (
                           len(assigned_bins), work_order.name),
            'compliance_level': 'standard'
        })

    def _return_wizard_form(self):
        """Return to wizard form view"""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': self.env.context
        }

    def _show_success_message(self, assignment_count):
        """Show success message after assignment"""
        message = _('Successfully assigned %d bins to %d work orders') % (
            assignment_count, len(self.work_order_ids))

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Assignment Complete'),
                'message': message,
                'type': 'success',
                'sticky': False,
            }
        }

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('assignment_type')
    def _onchange_assignment_type(self):
        """Clear selected bins when assignment type changes"""
        if self.assignment_type != 'manual':
            self.selected_bin_ids = [(5, 0, 0)]

    @api.onchange('work_order_ids')
    def _onchange_work_order_ids(self):
        """Update available bins when work orders change"""
        self._compute_available_bins()
