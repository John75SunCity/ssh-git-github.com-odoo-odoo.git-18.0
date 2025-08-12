# -*- coding: utf-8 -*-
"""
Container Retrieval Work Order Module

This module manages work orders for retrieving and delivering whole containers to customers.
It handles the complete lifecycle from pickup at storage facility to delivery at customer location,
including transportation coordination, customer notifications, and delivery confirmation.

Key Features:
- Container pickup and delivery coordination
- Transportation resource management
- Customer delivery scheduling and notifications
- Container condition tracking and documentation
- Integration with FSM and route optimization
- Delivery confirmation and customer signatures

Business Processes:
1. Work Order Creation: Generate from customer requests or scheduled retrievals
2. Resource Assignment: Assign vehicles, drivers, and delivery schedules
3. Container Preparation: Verify container condition and contents
4. Transportation: Coordinate pickup and delivery logistics
5. Customer Delivery: Handle delivery, customer interaction, and confirmation
6. Documentation: Generate delivery receipts and update container location

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3
"""

from datetime import datetime, timedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ContainerRetrievalWorkOrder(models.Model):
    _name = "container.retrieval.work.order"
    _description = "Container Retrieval Work Order"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "priority desc, scheduled_delivery_date asc, name"
    _rec_name = "display_name"

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Work Order Number",
        required=True,
        tracking=True,
        index=True,
        copy=False,
        default=lambda self: _("New"),
        help="Unique container retrieval work order number"
    )
    display_name = fields.Char(
        string="Display Name",
        compute="_compute_display_name",
        store=True,
        help="Formatted display name for the work order"
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
        string="Assigned User",
        default=lambda self: self.env.user,
        tracking=True,
        help="Primary user responsible for this work order"
    )
    active = fields.Boolean(string="Active", default=True, tracking=True)

    # ============================================================================
    # WORK ORDER STATE MANAGEMENT
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('scheduled', 'Scheduled'),
        ('in_transit', 'In Transit'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True,
       help="Current status of the container retrieval work order")

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True,
       help="Work order priority level for scheduling")

    # ============================================================================
    # CUSTOMER AND CONTAINER INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        required=True,
        tracking=True,
        domain="[('is_company', '=', True)]",
        help="Customer requesting container retrieval"
    )
    container_ids = fields.Many2many(
        "records.container",
        "container_retrieval_work_order_container_rel",
        "work_order_id",
        "container_id",
        string="Containers to Retrieve",
        required=True,
        help="Containers to be retrieved and delivered"
    )
    container_count = fields.Integer(
        string="Container Count",
        compute="_compute_container_metrics",
        store=True,
        help="Number of containers in this work order"
    )
    total_volume = fields.Float(
        string="Total Volume (CF)",
        compute="_compute_container_metrics",
        store=True,
        digits=(12, 3),
        help="Total cubic feet of all containers"
    )
    total_weight = fields.Float(
        string="Estimated Total Weight (lbs)",
        compute="_compute_container_metrics",
        store=True,
        digits="Stock Weight",
        help="Estimated total weight of all containers"
    )

    # ============================================================================
    # DELIVERY SCHEDULING AND LOGISTICS
    # ============================================================================
    scheduled_delivery_date = fields.Datetime(
        string="Scheduled Delivery Date",
        required=True,
        tracking=True,
        help="Planned date and time for container delivery"
    )
    delivery_window_start = fields.Datetime(
        string="Delivery Window Start",
        compute="_compute_delivery_window",
        store=True,
        help="Start of delivery time window"
    )
    delivery_window_end = fields.Datetime(
        string="Delivery Window End",
        compute="_compute_delivery_window",
        store=True,
        help="End of delivery time window"
    )
    actual_pickup_date = fields.Datetime(
        string="Actual Pickup Date",
        tracking=True,
        help="Actual date when containers were picked up from facility"
    )
    actual_delivery_date = fields.Datetime(
        string="Actual Delivery Date",
        tracking=True,
        help="Actual date when containers were delivered to customer"
    )

    # ============================================================================
    # DELIVERY LOCATION AND INSTRUCTIONS
    # ============================================================================
    delivery_address_id = fields.Many2one(
        "res.partner",
        string="Delivery Address",
        help="Specific delivery address (if different from customer address)"
    )
    delivery_instructions = fields.Text(
        string="Delivery Instructions",
        help="Special delivery instructions from customer"
    )
    access_requirements = fields.Text(
        string="Access Requirements",
        help="Special access requirements (keys, codes, security clearance)"
    )
    contact_person = fields.Char(
        string="On-site Contact Person",
        help="Person to contact at delivery location"
    )
    contact_phone = fields.Char(
        string="Contact Phone",
        help="Phone number for on-site contact"
    )

    # ============================================================================
    # TRANSPORTATION AND EQUIPMENT
    # ============================================================================
    vehicle_id = fields.Many2one(
        "records.vehicle",
        string="Assigned Vehicle",
        tracking=True,
        help="Vehicle assigned for container transportation"
    )
    driver_id = fields.Many2one(
        "hr.employee",
        string="Assigned Driver",
        tracking=True,
        help="Driver assigned for container delivery"
    )
    route_id = fields.Many2one(
        "pickup.route",
        string="Delivery Route",
        help="Optimized delivery route"
    )
    equipment_needed = fields.Text(
        string="Special Equipment Needed",
        help="Any special equipment required for delivery (crane, forklift, etc.)"
    )

    # ============================================================================
    # DOCUMENTATION AND CONFIRMATION
    # ============================================================================
    delivery_receipt_signed = fields.Boolean(
        string="Delivery Receipt Signed",
        tracking=True,
        help="Whether customer has signed delivery receipt"
    )
    customer_signature = fields.Binary(
        string="Customer Signature",
        help="Digital signature from customer confirming delivery"
    )
    delivery_photo = fields.Binary(
        string="Delivery Photo",
        help="Photo documentation of delivered containers"
    )
    delivery_notes = fields.Text(
        string="Delivery Notes",
        help="Notes from delivery personnel about the delivery"
    )
    customer_satisfaction_rating = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied'),
    ], string='Customer Satisfaction', help="Customer satisfaction rating")

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    duration_hours = fields.Float(
        string="Duration (Hours)",
        compute="_compute_duration",
        help="Total duration from pickup to delivery in hours"
    )
    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute="_compute_overdue_status",
        help="Whether delivery is overdue"
    )
    days_until_delivery = fields.Integer(
        string="Days Until Delivery",
        compute="_compute_days_until_delivery",
        help="Number of days until scheduled delivery"
    )

    # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
    # ============================================================================
    activity_ids = fields.One2many("mail.activity", "res_id", string="Activities")
    message_follower_ids = fields.One2many("mail.followers", "res_id", string="Followers")
    message_ids = fields.One2many("mail.message", "res_id", string="Messages")

    # ============================================================================
    # MODEL CREATE WITH SEQUENCE
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'container.retrieval.work.order') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id', 'container_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.container_count:
                record.display_name = _("%s - %s (%s containers)",
                    record.name, record.partner_id.name, record.container_count)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Container Retrieval")

    @api.depends('container_ids')
    def _compute_container_metrics(self):
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)
            record.total_volume = sum(containers.mapped('volume_cf')) if containers else 0.0
            record.total_weight = sum(containers.mapped('estimated_weight')) if containers else 0.0

    @api.depends('scheduled_delivery_date')
    def _compute_delivery_window(self):
        for record in self:
            if record.scheduled_delivery_date:
                # Default 2-hour delivery window
                record.delivery_window_start = record.scheduled_delivery_date - timedelta(hours=1)
                record.delivery_window_end = record.scheduled_delivery_date + timedelta(hours=1)
            else:
                record.delivery_window_start = False
                record.delivery_window_end = False

    @api.depends('actual_pickup_date', 'actual_delivery_date')
    def _compute_duration(self):
        for record in self:
            if record.actual_pickup_date and record.actual_delivery_date:
                delta = record.actual_delivery_date - record.actual_pickup_date
                record.duration_hours = delta.total_seconds() / 3600.0
            else:
                record.duration_hours = 0.0

    @api.depends('scheduled_delivery_date', 'state')
    def _compute_overdue_status(self):
        now = datetime.now()
        for record in self:
            record.is_overdue = (
                record.scheduled_delivery_date and 
                record.scheduled_delivery_date < now and 
                record.state not in ['delivered', 'completed', 'cancelled']
            )

    @api.depends('scheduled_delivery_date')
    def _compute_days_until_delivery(self):
        today = datetime.now().date()
        for record in self:
            if record.scheduled_delivery_date:
                delivery_date = record.scheduled_delivery_date.date()
                delta = delivery_date - today
                record.days_until_delivery = delta.days
            else:
                record.days_until_delivery = 0

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('scheduled_delivery_date')
    def _check_delivery_date(self):
        for record in self:
            if record.scheduled_delivery_date and record.scheduled_delivery_date <= datetime.now():
                raise ValidationError(_("Scheduled delivery date must be in the future"))

    @api.constrains('container_ids')
    def _check_containers(self):
        for record in self:
            if not record.container_ids:
                raise ValidationError(_("At least one container must be selected for retrieval"))

    @api.constrains('actual_pickup_date', 'actual_delivery_date')
    def _check_delivery_sequence(self):
        for record in self:
            if (record.actual_pickup_date and record.actual_delivery_date and
                record.actual_pickup_date > record.actual_delivery_date):
                raise ValidationError(_("Pickup date cannot be after delivery date"))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed"))
        
        # pylint: disable=no-member

        
        self.write({'state': 'confirmed'})
        self.message_post(
            body=_("Container retrieval work order confirmed for %s", self.partner_id.name),
            message_type='notification'
        )
        return True

    def action_schedule(self):
        """Schedule the work order"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can be scheduled"))
        
        if not self.vehicle_id or not self.driver_id:
            raise UserError(_("Vehicle and driver must be assigned before scheduling"))
        
        # pylint: disable=no-member

        
        self.write({'state': 'scheduled'})
        self.message_post(
            body=_("Work order scheduled for delivery on %s", self.scheduled_delivery_date),
            message_type='notification'
        )
        return True

    def action_start_transit(self):
        """Mark containers as in transit"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled work orders can be started"))
        
        # pylint: disable=no-member

        
        self.write({
            'state': 'in_transit',
            'actual_pickup_date': fields.Datetime.now()
        })
        
        # Update container locations to in-transit
        # pylint: disable=no-member

        self.container_ids.write({'location_status': 'in_transit'})
        
        self.message_post(
            body=_("Containers picked up and in transit to %s", self.partner_id.name),
            message_type='notification'
        )
        return True

    def action_confirm_delivery(self):
        """Confirm delivery completion"""
        self.ensure_one()
        if self.state != 'in_transit':
            raise UserError(_("Only work orders in transit can be marked as delivered"))
        
        # pylint: disable=no-member

        
        self.write({
            'state': 'delivered',
            'actual_delivery_date': fields.Datetime.now()
        })
        
        # Update container locations to customer location
        delivery_location = self.delivery_address_id or self.partner_id
        if delivery_location:
            # Find or create customer location record
            # pylint: disable=no-member

            customer_location = self.env['records.location'].search([
                ('partner_id', '=', delivery_location.id),
                ('location_type', '=', 'customer')
            ], limit=1)
            
            if not customer_location:
                # pylint: disable=no-member

                customer_location = self.env['records.location'].create({
                    'name': _("Customer Location - %s", delivery_location.name),
                    'partner_id': delivery_location.id,
                    'location_type': 'customer',
                    'address': delivery_location.contact_address,
                })
            
            # Update container locations
            # pylint: disable=no-member

            self.container_ids.write({
                'location_id': customer_location.id,
                'location_status': 'at_customer'
            })
        
        self.message_post(
            body=_("Containers successfully delivered to %s", self.partner_id.name),
            message_type='notification'
        )
        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed"))
        
        if not self.delivery_receipt_signed:
            raise UserError(_("Delivery receipt must be signed before completion"))
        
        # pylint: disable=no-member

        
        self.write({'state': 'completed'})
        self.message_post(
            body=_("Container retrieval work order completed successfully"),
            message_type='notification'
        )
        
        # Create activity for follow-up if needed
        if self.customer_satisfaction_rating and int(self.customer_satisfaction_rating) < 4:
            self.activity_schedule(
                'mail.mail_activity_data_call',
                summary=_("Follow up on delivery satisfaction"),
                note=_("Customer satisfaction rating was %s. Follow up required.", 
                       dict(self._fields['customer_satisfaction_rating'].selection)[self.customer_satisfaction_rating]),
                user_id=self.user_id.id
            )
        
        return True

    def action_cancel(self):
        """Cancel the work order"""
        self.ensure_one()
        if self.state in ['delivered', 'completed']:
            raise UserError(_("Delivered or completed work orders cannot be cancelled"))
        
        # pylint: disable=no-member

        
        self.write({'state': 'cancelled'})
        self.message_post(
            body=_("Container retrieval work order cancelled"),
            message_type='notification'
        )
        return True

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def send_delivery_notification(self):
        """Send delivery notification to customer"""
        self.ensure_one()
        template = self.env.ref('records_management.email_template_container_delivery_notification', False)
        if template:
            template.send_mail(self.id, force_send=True)

    def generate_delivery_report(self):
        """Generate delivery report for customer"""
        self.ensure_one()
        return {
            'type': 'ir.actions.report',
            'report_name': 'records_management.report_container_delivery',
            'report_type': 'qweb-pdf',
            'res_id': self.id,
            'target': 'new',
        }

    def action_reschedule_delivery(self):
        """Open wizard to reschedule delivery"""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Reschedule Delivery'),
            'res_model': 'container.delivery.reschedule.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'default_current_date': self.scheduled_delivery_date,
            }
        }
