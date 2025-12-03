# -*- coding: utf-8 -*-
"""
Work Order Creation Wizard

A unified wizard that allows staff to create any type of work order
from a single interface. Guides the user through type selection and
then creates the appropriate work order record.

NOTE: For retrieval work orders, we use the `records.retrieval.work.order` model
(sequence prefix RRWO) which is the preferred/active retrieval model.
The `work.order.retrieval` model (WO prefix) is deprecated and should not be used.

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class WorkOrderCreationWizard(models.TransientModel):
    """
    Wizard to create any type of work order from a unified interface.
    Step 1: Select customer and work order type
    Step 2: Fill in type-specific details
    Step 3: Create the work order
    """
    _name = 'work.order.creation.wizard'
    _description = 'Work Order Creation Wizard'

    # ============================================================================
    # WIZARD STATE
    # ============================================================================
    state = fields.Selection([
        ('type_selection', 'Select Type'),
        ('details', 'Enter Details'),
    ], string="Step", default='type_selection')

    # ============================================================================
    # COMMON FIELDS (Step 1)
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True,
        domain="[('customer_rank', '>', 0)]"
    )
    
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('destruction', 'Destruction Services'),
    ], string="Service Category", required=True, default='storage')
    
    work_order_type = fields.Selection([
        # Storage Services - Container Operations
        ('retrieval', 'Container Retrieval - Pull containers from storage'),
        ('delivery', 'Container Delivery - Return containers to customer'),
        ('pickup', 'Container Pickup - Collect containers from customer'),
        ('container_access', 'Container Access - On-site file access'),
        # Storage Services - File Operations
        ('file_retrieval', 'File Retrieval - Pull individual files from containers'),
        ('file_refiling', 'File Re-filing - Return files to their original containers'),
        # Destruction Services  
        ('container_destruction', 'Container Destruction - Destroy stored containers'),
        ('shredding', 'Shredding Service - On-site/mobile shredding'),
    ], string="Work Order Type", required=True)
    
    @api.onchange('service_category')
    def _onchange_service_category(self):
        """Reset work order type when category changes."""
        # Set a default type based on category
        if self.service_category == 'storage':
            self.work_order_type = 'retrieval'
        elif self.service_category == 'destruction':
            self.work_order_type = 'container_destruction'

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
    ], string="Priority", default='0', required=True)
    
    scheduled_date = fields.Datetime(
        string="Scheduled Date/Time",
        required=True,
        default=fields.Datetime.now
    )
    
    notes = fields.Text(string="Notes / Instructions")

    # ============================================================================
    # RECURRING SCHEDULE FIELDS
    # ============================================================================
    make_recurring = fields.Boolean(
        string="Make Recurring",
        default=False,
        help="Create a recurring schedule for this type of work order"
    )
    
    interval_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly (Every 2 Weeks)'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
    ], string="Frequency", default='weekly')
    
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
    ], string="Day of Week", default='0')
    
    recurring_end_date = fields.Date(
        string="End Date",
        help="Leave empty for indefinite schedule"
    )

    # ============================================================================
    # RETRIEVAL-SPECIFIC FIELDS
    # ============================================================================
    retrieval_container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='wizard_retrieval_container_rel',
        column1='wizard_id',
        column2='container_id',
        string="Containers to Retrieve",
        domain="[('partner_id', '=', partner_id), ('state', '=', 'in')]"
    )
    retrieval_reason = fields.Selection([
        ('customer_request', 'Customer Request'),
        ('audit', 'Audit'),
        ('legal', 'Legal/Litigation'),
        ('other', 'Other'),
    ], string="Retrieval Reason", default='customer_request')
    
    # ============================================================================
    # PICKUP-SPECIFIC FIELDS
    # ============================================================================
    pickup_location = fields.Char(string="Pickup Location")
    estimated_container_count = fields.Integer(string="Estimated # of Containers", default=1)
    
    # ============================================================================
    # CONTAINER DESTRUCTION-SPECIFIC FIELDS
    # ============================================================================
    destruction_container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='wizard_destruction_container_rel',
        column1='wizard_id',
        column2='container_id',
        string="Containers for Destruction",
        domain="[('partner_id', '=', partner_id)]"
    )
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
    ], string="Destruction Method", default='shredding')
    witness_required = fields.Boolean(string="Witness Required", default=False)
    
    # ============================================================================
    # SHREDDING SERVICE-SPECIFIC FIELDS
    # ============================================================================
    shredding_service_type = fields.Selection([
        ('onsite', 'On-Site Shredding'),
        ('offsite', 'Off-Site Shredding'),
        ('mobile', 'Mobile Shredding Truck'),
        ('bin_onetime', 'One-Time Bin Service'),
        ('bin_recurring', 'Recurring Bin Service'),
        ('bin_mobile', 'Mobile Bin Service'),
    ], string="Shredding Service Type", default='onsite')
    material_type = fields.Selection([
        ('paper', 'Paper Documents'),
        ('hard_drives', 'Hard Drives'),
        ('media', 'Media (Tapes, CDs, etc.)'),
        ('mixed', 'Mixed Materials'),
    ], string="Material Type", default='paper')
    bin_quantity = fields.Integer(string="Number of Bins", default=1, help="Quantity of bins for the service")

    # ============================================================================
    # WIZARD ACTIONS
    # ============================================================================
    def action_next(self):
        """Move to the details step."""
        self.ensure_one()
        self.state = 'details'
        return self._reopen_wizard()
    
    def action_back(self):
        """Go back to type selection."""
        self.ensure_one()
        self.state = 'type_selection'
        return self._reopen_wizard()
    
    def _reopen_wizard(self):
        """Reopen the wizard with current state."""
        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_create_work_order(self):
        """Create the appropriate work order based on type selection."""
        self.ensure_one()
        
        # Dispatch to the appropriate creation method
        method_name = f'_create_{self.work_order_type}_order'
        if hasattr(self, method_name):
            work_order = getattr(self, method_name)()
        else:
            raise UserError(_("Work order type '%s' is not yet implemented.") % self.work_order_type)
        
        # Create recurring schedule if requested
        if self.make_recurring:
            schedule = self._create_recurring_schedule(work_order)
            # Return action to view the schedule instead
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'recurring.work.order.schedule',
                'res_id': schedule.id,
                'view_mode': 'form',
                'target': 'current',
            }
        
        # Return action to view the created work order
        return {
            'type': 'ir.actions.act_window',
            'res_model': work_order._name,
            'res_id': work_order.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_recurring_schedule(self, first_work_order):
        """Create a recurring schedule based on wizard settings."""
        self.ensure_one()
        
        # Build schedule name
        type_labels = dict(self._fields['work_order_type'].selection)
        interval_labels = dict(self._fields['interval_type'].selection)
        schedule_name = "%s %s - %s" % (
            interval_labels.get(self.interval_type, ''),
            type_labels.get(self.work_order_type, ''),
            self.partner_id.name
        )
        
        vals = {
            'name': schedule_name,
            'partner_id': self.partner_id.id,
            'service_category': self.service_category,
            'work_order_type': self.work_order_type,
            'priority': self.priority,
            'interval_type': self.interval_type,
            'interval_number': 1,
            'day_of_week': self.day_of_week if self.interval_type in ('weekly', 'biweekly') else False,
            'preferred_time': self.scheduled_date.hour + (self.scheduled_date.minute / 60.0) if self.scheduled_date else 9.0,
            'start_date': self.scheduled_date.date() if self.scheduled_date else fields.Date.context_today(self),
            'end_date': self.recurring_end_date,
            'notes': self.notes,
            'advance_days': 7,
        }
        
        # Add shredding-specific fields
        if self.work_order_type == 'shredding':
            vals.update({
                'shredding_service_type': self.shredding_service_type,
                'material_type': self.material_type,
            })
        
        schedule = self.env['recurring.work.order.schedule'].create(vals)
        
        # Link the first work order to the schedule history
        self.env['recurring.work.order.history'].create({
            'schedule_id': schedule.id,
            'work_order_model': first_work_order._name,
            'work_order_id': first_work_order.id,
            'scheduled_date': self.scheduled_date.date() if self.scheduled_date else fields.Date.context_today(self),
            'generated_date': fields.Date.context_today(self),
        })
        
        # Update schedule's last generated date
        schedule.last_generated_date = fields.Date.context_today(self)
        
        return schedule

    # ============================================================================
    # WORK ORDER CREATION METHODS
    # ============================================================================
    def _create_retrieval_order(self):
        """Create a retrieval work order using records.retrieval.work.order model.
        
        NOTE: We use records.retrieval.work.order (RRWO sequence) as the preferred
        retrieval model. The work.order.retrieval model is deprecated.
        """
        if not self.retrieval_container_ids:
            raise ValidationError(_("Please select at least one container to retrieve."))
        
        # Use records.retrieval.work.order model (preferred)
        vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'scanned_barcode_ids': [(6, 0, self.retrieval_container_ids.ids)],
        }
        work_order = self.env['records.retrieval.work.order'].create(vals)
        # Post notes to chatter if provided
        if self.notes:
            work_order.message_post(body=self.notes)
        return work_order

    def _create_delivery_order(self):
        """Create a delivery work order (return containers to customer).
        
        Uses records.retrieval.work.order model.
        """
        vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'scanned_barcode_ids': [(6, 0, self.retrieval_container_ids.ids)] if self.retrieval_container_ids else [],
        }
        work_order = self.env['records.retrieval.work.order'].create(vals)
        work_order.message_post(body=self.notes or _("Delivery - Return containers to customer"))
        return work_order

    def _create_file_retrieval_order(self):
        """Create a file retrieval work order (pull individual files from containers).
        
        This changes file status from 'in' to 'out'.
        Uses records.retrieval.work.order model.
        """
        vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'scanned_barcode_ids': [(6, 0, self.retrieval_container_ids.ids)] if self.retrieval_container_ids else [],
        }
        work_order = self.env['records.retrieval.work.order'].create(vals)
        work_order.message_post(body=self.notes or _("File Retrieval - Pull individual files from containers"))
        return work_order

    def _create_file_refiling_order(self):
        """Create a file re-filing work order (return files to original containers).
        
        This changes file status from 'out' to 'in' and directs technicians
        to return the files to the containers from which they originated.
        Uses records.retrieval.work.order model.
        """
        vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
            'scanned_barcode_ids': [(6, 0, self.retrieval_container_ids.ids)] if self.retrieval_container_ids else [],
        }
        work_order = self.env['records.retrieval.work.order'].create(vals)
        work_order.message_post(body=self.notes or _("File Re-filing - Return files to their original containers"))
        return work_order

    def _create_pickup_order(self):
        """Create a pickup work order.
        
        Uses records.retrieval.work.order model (preferred).
        """
        vals = {
            'partner_id': self.partner_id.id,
            'user_id': self.env.user.id,
        }
        work_order = self.env['records.retrieval.work.order'].create(vals)
        pickup_note = self.notes or _("Pickup - Collect containers from customer location: %s") % (self.pickup_location or 'TBD')
        work_order.message_post(body=pickup_note)
        return work_order

    def _create_container_access_order(self):
        """Create a container access work order."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_access_date': self.scheduled_date,
            'priority': self.priority,
            'access_purpose': self.notes,
        }
        return self.env['container.access.work.order'].create(vals)

    def _create_container_destruction_order(self):
        """Create a container destruction work order."""
        if not self.destruction_container_ids:
            raise ValidationError(_("Please select at least one container for destruction."))
        
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_destruction_date': self.scheduled_date,
            'priority': self.priority,
            'destruction_reason': self.notes,
            'container_ids': [(6, 0, self.destruction_container_ids.ids)],
            'destruction_method': self.destruction_method,
            'witness_required': self.witness_required,
        }
        return self.env['container.destruction.work.order'].create(vals)

    def _create_shredding_order(self):
        """Create a shredding work order."""
        vals = {
            'partner_id': self.partner_id.id,
            'scheduled_date': self.scheduled_date,
            'priority': self.priority,
            'shredding_service_type': self.shredding_service_type,
            'material_type': self.material_type,
            'bin_quantity': self.bin_quantity,
            'special_instructions': self.notes,
        }
        return self.env['work.order.shredding'].create(vals)
