# -*- coding: utf-8 -*-
"""
Recurring Work Order Schedule

Manages recurring work order schedules that automatically generate
work orders based on defined intervals (daily, weekly, monthly, etc.)

Author: Records Management System
Version: 18.0.1.0.0
License: LGPL-3
"""

from datetime import timedelta
from dateutil.relativedelta import relativedelta

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecurringWorkOrderSchedule(models.Model):
    """
    Defines a recurring schedule that automatically creates work orders
    at specified intervals.
    """
    _name = 'recurring.work.order.schedule'
    _description = 'Recurring Work Order Schedule'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'next_occurrence_date asc, name'

    # ============================================================================
    # IDENTIFICATION
    # ============================================================================
    name = fields.Char(
        string="Schedule Name",
        required=True,
        tracking=True,
        help="Descriptive name for this recurring schedule, e.g., 'Weekly Bin Service - ABC Corp'"
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)
    company_id = fields.Many2one(
        comodel_name='res.company',
        string="Company",
        required=True,
        default=lambda self: self.env.company
    )

    # ============================================================================
    # CUSTOMER & SERVICE TYPE
    # ============================================================================
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer",
        required=True,
        tracking=True,
        domain="[('customer_rank', '>', 0)]"
    )
    department_id = fields.Many2one(
        comodel_name='records.department',
        string="Department",
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
        help="Optional department for service address and billing purposes"
    )
    
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('destruction', 'Destruction Services'),
    ], string="Service Category", required=True, default='destruction', tracking=True)
    
    work_order_type = fields.Selection([
        # Storage Services
        ('retrieval', 'Retrieval'),
        ('delivery', 'Delivery'),
        ('pickup', 'Pickup'),
        ('container_access', 'Container Access'),
        # Destruction Services
        ('container_destruction', 'Container Destruction'),
        ('shredding', 'Shredding Service'),
    ], string="Work Order Type", required=True, tracking=True)
    
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
    ], string="Priority", default='0')

    # ============================================================================
    # SCHEDULE CONFIGURATION
    # ============================================================================
    interval_type = fields.Selection([
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly (Every 2 Weeks)'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ], string="Frequency", required=True, default='weekly', tracking=True)
    
    interval_number = fields.Integer(
        string="Every",
        default=1,
        help="Run every X intervals (e.g., every 2 weeks)"
    )
    
    # Specific day settings
    day_of_week = fields.Selection([
        ('0', 'Monday'),
        ('1', 'Tuesday'),
        ('2', 'Wednesday'),
        ('3', 'Thursday'),
        ('4', 'Friday'),
        ('5', 'Saturday'),
        ('6', 'Sunday'),
    ], string="Day of Week", help="For weekly schedules, which day to create the work order")
    
    day_of_month = fields.Integer(
        string="Day of Month",
        default=1,
        help="For monthly schedules, which day of the month (1-28 recommended)"
    )
    
    preferred_time = fields.Float(
        string="Preferred Time",
        default=9.0,
        help="Preferred time of day for the scheduled service (24h format, e.g., 9.0 = 9:00 AM)"
    )
    
    # Schedule dates
    start_date = fields.Date(
        string="Start Date",
        required=True,
        default=fields.Date.context_today,
        tracking=True
    )
    end_date = fields.Date(
        string="End Date",
        help="Leave empty for indefinite schedule"
    )
    next_occurrence_date = fields.Date(
        string="Next Occurrence",
        compute='_compute_next_occurrence',
        store=True,
        tracking=True
    )
    
    # Advance creation
    advance_days = fields.Integer(
        string="Create In Advance (Days)",
        default=7,
        help="How many days before the scheduled date to create the work order"
    )

    # ============================================================================
    # SERVICE-SPECIFIC CONFIGURATION
    # ============================================================================
    # Bin service configuration
    bin_count = fields.Integer(
        string="Number of Bins",
        default=1,
        help="Number of bins to service"
    )
    bin_ids = fields.Many2many(
        comodel_name='shredding.service.bin',
        relation='recurring_schedule_bin_rel',
        column1='schedule_id',
        column2='bin_id',
        string="Specific Bins",
        domain="[('current_customer_id', '=', partner_id)]",
        help="Specific bins to service. Leave empty to service all customer bins."
    )
    
    # Shredding configuration
    shredding_service_type = fields.Selection([
        ('onsite', 'On-Site Shredding'),
        ('offsite', 'Off-Site Shredding'),
        ('mobile', 'Mobile Shredding Truck'),
    ], string="Shredding Type", default='onsite')
    
    material_type = fields.Selection([
        ('paper', 'Paper Documents'),
        ('hard_drives', 'Hard Drives'),
        ('media', 'Media (Tapes, CDs, etc.)'),
        ('mixed', 'Mixed Materials'),
    ], string="Material Type", default='paper')
    
    # Notes/instructions
    notes = fields.Text(
        string="Standing Instructions",
        help="Instructions that will be copied to each generated work order"
    )

    # ============================================================================
    # TRACKING & HISTORY
    # ============================================================================
    last_generated_date = fields.Date(
        string="Last Generated",
        readonly=True
    )
    generated_order_count = fields.Integer(
        string="Orders Generated",
        compute='_compute_generated_order_count'
    )
    generated_order_ids = fields.One2many(
        comodel_name='recurring.work.order.history',
        inverse_name='schedule_id',
        string="Generated Orders"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('start_date', 'interval_type', 'interval_number', 'last_generated_date', 'day_of_week', 'day_of_month')
    def _compute_next_occurrence(self):
        """Calculate the next occurrence date based on schedule settings."""
        for schedule in self:
            if not schedule.start_date:
                schedule.next_occurrence_date = False
                continue
            
            base_date = schedule.last_generated_date or schedule.start_date
            today = fields.Date.context_today(self)
            
            # Calculate next occurrence
            next_date = schedule._get_next_occurrence_from_date(base_date)
            
            # Make sure it's in the future
            while next_date and next_date <= today:
                next_date = schedule._get_next_occurrence_from_date(next_date)
            
            # Check if past end date
            if schedule.end_date and next_date and next_date > schedule.end_date:
                next_date = False
            
            schedule.next_occurrence_date = next_date

    def _get_next_occurrence_from_date(self, from_date):
        """Calculate the next occurrence after a given date."""
        self.ensure_one()
        if not from_date:
            return False
        
        interval = self.interval_number or 1
        
        if self.interval_type == 'daily':
            return from_date + timedelta(days=interval)
        
        elif self.interval_type == 'weekly':
            next_date = from_date + timedelta(weeks=interval)
            # Adjust to specific day of week if set
            if self.day_of_week:
                target_weekday = int(self.day_of_week)
                days_ahead = target_weekday - next_date.weekday()
                if days_ahead <= 0:
                    days_ahead += 7
                next_date = next_date + timedelta(days=days_ahead)
            return next_date
        
        elif self.interval_type == 'biweekly':
            return from_date + timedelta(weeks=2 * interval)
        
        elif self.interval_type == 'monthly':
            next_date = from_date + relativedelta(months=interval)
            # Adjust to specific day of month if set
            if self.day_of_month:
                try:
                    next_date = next_date.replace(day=min(self.day_of_month, 28))
                except ValueError:
                    pass  # Keep calculated date if day is invalid
            return next_date
        
        elif self.interval_type == 'quarterly':
            return from_date + relativedelta(months=3 * interval)
        
        elif self.interval_type == 'yearly':
            return from_date + relativedelta(years=interval)
        
        return from_date + timedelta(days=1)

    def _compute_generated_order_count(self):
        """Count generated work orders."""
        for schedule in self:
            schedule.generated_order_count = len(schedule.generated_order_ids)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Clear department when customer changes."""
        if self.partner_id:
            self.department_id = False
            # Reset bins when customer changes
            self.bin_ids = False
    
    @api.onchange('service_category')
    def _onchange_service_category(self):
        """Clear work order type when category changes to ensure valid selection."""
        storage_types = ['retrieval', 'delivery', 'pickup', 'container_access']
        destruction_types = ['container_destruction', 'shredding']
        
        if self.service_category == 'storage' and self.work_order_type in destruction_types:
            self.work_order_type = False
        elif self.service_category == 'destruction' and self.work_order_type in storage_types:
            self.work_order_type = False

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('interval_number')
    def _check_interval_number(self):
        for schedule in self:
            if schedule.interval_number < 1:
                raise ValidationError(_("Interval number must be at least 1."))

    @api.constrains('day_of_month')
    def _check_day_of_month(self):
        for schedule in self:
            if schedule.day_of_month and (schedule.day_of_month < 1 or schedule.day_of_month > 28):
                raise ValidationError(_("Day of month should be between 1 and 28 to avoid month-end issues."))

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for schedule in self:
            if schedule.end_date and schedule.start_date > schedule.end_date:
                raise ValidationError(_("End date must be after start date."))

    # ============================================================================
    # WORK ORDER GENERATION
    # ============================================================================
    def action_generate_next_order(self):
        """Manually generate the next work order."""
        self.ensure_one()
        return self._generate_work_order()

    def _generate_work_order(self):
        """Generate a work order based on this schedule."""
        self.ensure_one()
        
        if not self.active:
            raise UserError(_("Cannot generate work order for inactive schedule."))
        
        if not self.next_occurrence_date:
            raise UserError(_("No next occurrence date calculated."))
        
        # Create the work order based on type
        work_order = self._create_work_order_by_type()
        
        # Record in history
        self.env['recurring.work.order.history'].create({
            'schedule_id': self.id,
            'work_order_model': work_order._name,
            'work_order_id': work_order.id,
            'scheduled_date': self.next_occurrence_date,
            'generated_date': fields.Date.context_today(self),
        })
        
        # Update last generated date
        self.last_generated_date = fields.Date.context_today(self)
        
        # Post message
        self.message_post(
            body=_("Generated work order: %s for %s") % (work_order.name, self.next_occurrence_date),
            message_type='notification'
        )
        
        return work_order

    def _create_work_order_by_type(self):
        """Create the appropriate work order based on type."""
        self.ensure_one()
        
        # Convert preferred time to datetime
        scheduled_datetime = fields.Datetime.to_datetime(self.next_occurrence_date)
        hours = int(self.preferred_time)
        minutes = int((self.preferred_time - hours) * 60)
        scheduled_datetime = scheduled_datetime.replace(hour=hours, minute=minutes)
        
        # Base values common to all types (only partner_id and priority)
        # NOTE: Different work order types use different field names for notes:
        # - work.order.shredding uses 'special_instructions'
        # - container.destruction.work.order uses 'destruction_reason'
        # - work.order.retrieval and container.access.work.order don't have notes field
        base_vals = {
            'partner_id': self.partner_id.id,
            'priority': self.priority,
        }
        
        if self.work_order_type == 'shredding':
            vals = {
                **base_vals,
                'scheduled_date': scheduled_datetime,
                'special_instructions': self.notes or '',
            }
            return self.env['work.order.shredding'].create(vals)
        
        elif self.work_order_type == 'container_destruction':
            vals = {
                **base_vals,
                'scheduled_destruction_date': scheduled_datetime,
                'destruction_reason': self.notes or '',
            }
            return self.env['container.destruction.work.order'].create(vals)
        
        elif self.work_order_type == 'retrieval':
            vals = {
                **base_vals,
                'scheduled_date': scheduled_datetime,
            }
            return self.env['work.order.retrieval'].create(vals)
        
        elif self.work_order_type == 'container_access':
            vals = {
                **base_vals,
                'scheduled_date': scheduled_datetime,
            }
            return self.env['container.access.work.order'].create(vals)
        
        else:
            raise UserError(_("Work order type '%s' is not yet supported for recurring schedules.") % self.work_order_type)

    # ============================================================================
    # CRON JOB
    # ============================================================================
    @api.model
    def _cron_generate_upcoming_orders(self):
        """
        Cron job to automatically generate work orders for upcoming scheduled dates.
        Runs daily and creates orders that are within the 'advance_days' window.
        """
        today = fields.Date.context_today(self)
        
        # Find all active schedules
        schedules = self.search([
            ('active', '=', True),
            ('next_occurrence_date', '!=', False),
        ])
        
        generated_count = 0
        for schedule in schedules:
            # Check if we should generate (within advance window)
            if not schedule.next_occurrence_date:
                continue
            
            days_until = (schedule.next_occurrence_date - today).days
            
            if days_until <= schedule.advance_days:
                # Check if already generated for this occurrence
                existing = self.env['recurring.work.order.history'].search([
                    ('schedule_id', '=', schedule.id),
                    ('scheduled_date', '=', schedule.next_occurrence_date),
                ], limit=1)
                
                if not existing:
                    try:
                        schedule._generate_work_order()
                        generated_count += 1
                    except Exception as e:
                        # Log error but continue with other schedules
                        schedule.message_post(
                            body=_("Failed to generate work order: %s") % str(e),
                            message_type='notification'
                        )
        
        return generated_count

    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_view_generated_orders(self):
        """View all work orders generated from this schedule."""
        self.ensure_one()
        return {
            'name': _('Generated Work Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'recurring.work.order.history',
            'view_mode': 'list,form',
            'domain': [('schedule_id', '=', self.id)],
            'context': {'default_schedule_id': self.id},
        }

    def action_pause_schedule(self):
        """Pause the recurring schedule."""
        self.write({'active': False})

    def action_resume_schedule(self):
        """Resume the recurring schedule."""
        self.write({'active': True})


class RecurringWorkOrderHistory(models.Model):
    """
    Tracks work orders generated from recurring schedules.
    """
    _name = 'recurring.work.order.history'
    _description = 'Recurring Work Order History'
    _order = 'generated_date desc, id desc'

    schedule_id = fields.Many2one(
        comodel_name='recurring.work.order.schedule',
        string="Schedule",
        required=True,
        ondelete='cascade'
    )
    work_order_model = fields.Char(string="Work Order Model", required=True)
    work_order_id = fields.Integer(string="Work Order ID", required=True)
    work_order_reference = fields.Char(
        string="Work Order",
        compute='_compute_work_order_reference'
    )
    scheduled_date = fields.Date(string="Scheduled Date", required=True)
    generated_date = fields.Date(string="Generated Date", required=True)

    def _compute_work_order_reference(self):
        """Get the work order name/reference."""
        for record in self:
            try:
                wo = self.env[record.work_order_model].browse(record.work_order_id)
                record.work_order_reference = wo.name if wo.exists() else _("(Deleted)")
            except Exception:
                record.work_order_reference = _("(Unknown)")

    def action_open_work_order(self):
        """Open the linked work order."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.work_order_model,
            'res_id': self.work_order_id,
            'view_mode': 'form',
            'target': 'current',
        }
