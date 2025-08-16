# -*- coding: utf-8 -*-

FSM Task Service Line Model

Service line items for FSM tasks with detailed service breakdowns.:
    pass
Manages individual service components within Field Service Management tasks
including timing, pricing, quality tracking, and technician assignment.

Author: Records Management System
Version: 18.0.6.0.0
License: LGPL-3


from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class FSMTaskServiceLine(models.Model):

        FSM Task Service Line Management
    
    Manages individual service line items within FSM tasks including
        service breakdown, technician assignment, timing tracking, and
    quality assurance for comprehensive field service operations.:


    _name = "fsm.task.service.line"
    _description = "FSM Task Service Line"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = "task_id, sequence, service_type"
    _rec_name = "display_name"

        # ============================================================================
    # CORE IDENTIFICATION FIELDS
        # ============================================================================
    name = fields.Char(
        string="Service Description",
        required=True,
        tracking=True,
        index=True,
        help="Description of the service performed"
    

    display_name = fields.Char(
        string="Display Name",
        compute='_compute_display_name',
        store=True,
        help="Display name for the service line":
    

    company_id = fields.Many2one(
        "res.company",
        string="Company",
        default=lambda self: self.env.company,
        required=True
    

    user_id = fields.Many2one(
        "res.users",
        string="Recorded By",
        default=lambda self: self.env.user,
        tracking=True,
        help="User who recorded this service line"
    

    active = fields.Boolean(
        string="Active",
        default=True,
        help="Set to false to archive this service line"
    

    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Sequence for line ordering":
    

        # ============================================================================
    # RELATIONSHIP FIELDS
        # ============================================================================
    task_id = fields.Many2one(
        "project.task",
        string="FSM Task",
        required=True,
        ondelete="cascade",
        index=True,
        help="Parent FSM task"
    

    product_id = fields.Many2one(
        "product.product",
        string="Service Product",
        ,
    domain="[('type', '=', 'service'))",
        help="Service product for this line":
    

    employee_id = fields.Many2one(
        "hr.employee",
        string="Technician",
        help="Employee who performed the service"
    

    partner_id = fields.Many2one(
        "res.partner",
        string="Customer",
        related="task_id.partner_id",
        readonly=True,
        store=True,
        help="Customer for this service":
    

    project_id = fields.Many2one(
        "project.project",
        string="Project",
        related="task_id.project_id",
        readonly=True,
        store=True,
        help="Related project"
    

        # ============================================================================
    # SERVICE DETAILS
        # ============================================================================
    ,
    service_type = fields.Selection([))
        ('pickup', 'Container Pickup'),
        ('delivery', 'Container Delivery'),
        ('retrieval', 'Document Retrieval'),
        ('destruction', 'On-site Destruction'),
        ('scanning', 'Document Scanning'),
        ('indexing', 'Document Indexing'),
        ('consultation', 'Consultation'),
        ('maintenance', 'Equipment Maintenance'),
        ('travel', 'Travel Time'),
        ('setup', 'Equipment Setup'),
        ('inspection', 'Quality Inspection'),
        ('training', 'Customer Training'),
        ('other', 'Other Service')
    

    service_date = fields.Datetime(
        string="Service Date",
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time service was performed"
    

    duration_hours = fields.Float(
        ,
    string="Duration (Hours)",
        default=1.0,
        digits=(8, 2),
        help="Time spent on this service"
    

    start_time = fields.Datetime(
        string="Start Time",
        help="When the service started"
    

    end_time = fields.Datetime(
        string="End Time",
        help="When the service ended"
    

        # ============================================================================
    # QUANTITY AND UNITS
        # ============================================================================
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True,
        digits='Product Unit of Measure',
        help="Quantity of service units"
    

    ,
    unit_of_measure = fields.Selection([))
        ('hour', 'Hours'),
        ('container', 'Containers'),
        ('document', 'Documents'),
        ('cubic_foot', 'Cubic Feet'),
        ('pickup', 'Pickups'),
        ('scan', 'Scans'),
        ('consultation', 'Consultations'),
        ('trip', 'Trips'),
        ('item', 'Items'),
        ('other', 'Other')
    

        # ============================================================================
    # PRICING
        # ============================================================================
    currency_id = fields.Many2one(
        "res.currency",
        string="Currency",
        related="company_id.currency_id",
        readonly=True
    

    unit_price = fields.Monetary(
        string="Unit Price",
        currency_field="currency_id",
        help="Price per unit"
    

    total_price = fields.Monetary(
        string="Total Price",
        currency_field="currency_id",
        compute='_compute_total_price',
        store=True,
        help="Total line price"
    

    discount_percentage = fields.Float(
        string="Discount %",
        ,
    digits=(5, 2),
        help="Discount percentage applied"
    

    discounted_price = fields.Monetary(
        string="Discounted Price",
        currency_field="currency_id",
        compute='_compute_discounted_price',
        store=True,
        help="Price after discount"
    

        # ============================================================================
    # LOCATION AND EQUIPMENT
        # ============================================================================
    location_id = fields.Many2one(
        "records.location",
        string="Service Location",
        help="Location where service was performed"
    

    equipment_used = fields.Text(
        string="Equipment Used",
        help="Equipment or tools used for the service":
    

    vehicle_id = fields.Many2one(
        "fleet.vehicle",
        string="Vehicle Used",
        help="Vehicle used for this service":
    

        # ============================================================================
    # QUALITY AND COMPLETION
        # ============================================================================
    ,
    status = fields.Selection([))
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('paused', 'Paused'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled')
    

    completion_percentage = fields.Float(
        string="Completion %",
        default=0.0,
        ,
    digits=(5, 1),
        help="Percentage of service completed"
    

    quality_rating = fields.Selection([))
        ('1', 'Poor'),
        ('2', 'Fair'),
        ('3', 'Good'),
        ('4', 'Very Good'),
        ('5', 'Excellent')
    

    customer_satisfaction = fields.Selection([))
        ('very_unsatisfied', 'Very Unsatisfied'),
        ('unsatisfied', 'Unsatisfied'),
        ('neutral', 'Neutral'),
        ('satisfied', 'Satisfied'),
        ('very_satisfied', 'Very Satisfied')
    

        # ============================================================================
    # BILLING AND INVOICING
        # ============================================================================
    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this service is billable to customer"
    

    invoice_line_id = fields.Many2one(
        "account.move.line",
        string="Invoice Line",
        readonly=True,
        help="Related invoice line if billed":
    

    billing_notes = fields.Text(
        string="Billing Notes",
        help="Special notes for billing":
    

        # ============================================================================
    # NOTES AND OBSERVATIONS
        # ============================================================================
    service_notes = fields.Text(
        string="Service Notes",
        help="Detailed notes about the service performed"
    

    customer_feedback = fields.Text(
        string="Customer Feedback",
        help="Customer feedback on the service"
    

    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes not visible to customer"
    

        # ============================================================================
    # MAIL THREAD FRAMEWORK FIELDS
        # ============================================================================
    activity_ids = fields.One2many(
        "mail.activity",
        "res_id",
        string="Activities",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_follower_ids = fields.One2many(
        "mail.followers",
        "res_id",
        string="Followers",
        ,
    domain=lambda self: [("res_model", "=", self._name))
    

    message_ids = fields.One2many(
        "mail.message",
        "res_id",
        string="Messages",
        ,
    domain=lambda self: [("model", "=", self._name))
    

        # ============================================================================
    # COMPUTE METHODS
        # ============================================================================
    @api.depends('name', 'service_type', 'quantity', 'unit_of_measure')
    def _compute_display_name(self):
        """Compute display name with proper translation"""
        for record in self:
            parts = [record.name or _("New Service")]
            if record.quantity and record.unit_of_measure:
                uom_dict = dict(record._fields['unit_of_measure'].selection)
                uom_label = uom_dict.get(record.unit_of_measure, record.unit_of_measure)
                parts.append(_("(%s %s)", record.quantity, uom_label))

            record.display_name = " ".join(parts)

    @api.depends('quantity', 'unit_price')
    def _compute_total_price(self):
        """Calculate total price"""
        for record in self:
            record.total_price = record.quantity * record.unit_price

    @api.depends('total_price', 'discount_percentage')
    def _compute_discounted_price(self):
        """Calculate price after discount"""
        for record in self:
            if record.discount_percentage:
                discount_amount = record.total_price * (record.discount_percentage / 100)
                record.discounted_price = record.total_price - discount_amount
            else:
                record.discounted_price = record.total_price

    @api.depends('start_time', 'end_time')
    def _compute_duration_from_times(self):
        """Calculate duration from start/end times"""
        for record in self:
            if record.start_time and record.end_time:
                delta = record.end_time - record.start_time
                record.duration_hours = delta.total_seconds() / 3600

    # ============================================================================
        # ACTION METHODS
    # ============================================================================
    def action_start_service(self):
        """Start the service"""
        self.ensure_one()
        if self.status not in ['planned', 'paused']:
            raise UserError(_("Can only start planned or paused services"))

        self.write({)}
            'status': 'in_progress',
            'start_time': fields.Datetime.now()
        
        self.message_post(body=_("Service started"))

    def action_pause_service(self):
        """Pause the service"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_("Can only pause services in progress"))

        self.write({'status': 'paused'})
        self.message_post(body=_("Service paused"))

    def action_complete_service(self):
        """Complete the service"""
        self.ensure_one()
        if self.status != 'in_progress':
            raise UserError(_("Can only complete services in progress"))

        self.write({)}
            'status': 'completed',
            'completion_percentage': 100.0,
            'end_time': fields.Datetime.now()
        
        
        # Calculate duration if not set:
        if not self.duration_hours and self.start_time:
            self._compute_duration_from_times()

        self.message_post(body=_("Service completed"))

    def action_verify_service(self):
        """Verify service completion"""
        self.ensure_one()
        if self.status != 'completed':
            raise UserError(_("Can only verify completed services"))

        self.write({'status': 'verified'})
        self.message_post(body=_("Service verified"))

    def action_cancel_service(self):
        """Cancel the service"""
        self.ensure_one()
        if self.status in ['billed']:
            raise UserError(_("Cannot cancel billed services"))

        self.write({'status': 'cancelled'})
        self.message_post(body=_("Service cancelled"))

    def action_create_invoice_line(self):
        """Create invoice line for this service""":
        self.ensure_one()
        if not self.billable:
            raise UserError(_("Cannot create invoice line for non-billable service")):
        if self.invoice_line_id:
            raise UserError(_("Invoice line already exists for this service")):
        # Create invoice line logic would go here
        self.message_post(body=_("Invoice line creation requested"))

    # ============================================================================
        # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Update fields when product changes"""
        if self.product_id:
            self.name = self.product_id.name
            self.unit_price = self.product_id.list_price
            
            # Set default service type based on product
            if 'pickup' in self.product_id.name.lower():
                self.service_type = 'pickup'
            elif 'delivery' in self.product_id.name.lower():
                self.service_type = 'delivery'
            elif 'destruction' in self.product_id.name.lower():
                self.service_type = 'destruction'

    @api.onchange('service_type')
    def _onchange_service_type(self):
        """Update fields when service type changes"""
        if self.service_type:
            # Set default UOM based on service type
            uom_mapping = {}
                'pickup': 'container',
                'delivery': 'container',
                'retrieval': 'document',
                'scanning': 'scan',
                'consultation': 'hour',
                'travel': 'hour',
            
            
            if self.service_type in uom_mapping:
                self.unit_of_measure = uom_mapping[self.service_type]

    @api.onchange('start_time', 'end_time')
    def _onchange_service_times(self):
        """Update duration when times change"""
        if self.start_time and self.end_time:
            if self.end_time < self.start_time:
                raise UserError(_("End time cannot be before start time"))
            
            delta = self.end_time - self.start_time
            self.duration_hours = delta.total_seconds() / 3600

    # ============================================================================
        # VALIDATION METHODS
    # ============================================================================
    @api.constrains('quantity', 'unit_price')
    def _check_positive_values(self):
        """Validate positive values"""
        for record in self:
            if record.quantity <= 0:
                raise ValidationError(_("Quantity must be greater than 0"))
            if record.unit_price < 0:
                raise ValidationError(_("Unit price cannot be negative"))

    @api.constrains('duration_hours')
    def _check_duration(self):
        """Validate duration"""
        for record in self:
            if record.duration_hours < 0:
                raise ValidationError(_("Duration cannot be negative"))
            if record.duration_hours > 24:
                raise ValidationError(_("Duration cannot exceed 24 hours per service"))

    @api.constrains('completion_percentage')
    def _check_completion_percentage(self):
        """Validate completion percentage"""
        for record in self:
            if not 0 <= record.completion_percentage <= 100:
                raise ValidationError(_("Completion percentage must be between 0 and 100"))

    @api.constrains('discount_percentage')
    def _check_discount_percentage(self):
        """Validate discount percentage"""
        for record in self:
            if record.discount_percentage and not 0 <= record.discount_percentage <= 100:
                raise ValidationError(_("Discount percentage must be between 0 and 100"))

    @api.constrains('start_time', 'end_time')
    def _check_time_sequence(self):
        """Validate time sequence"""
        for record in self:
            if record.start_time and record.end_time:
                if record.start_time > record.end_time:
                    raise ValidationError(_("Start time must be before end time"))

    # ============================================================================
        # BUSINESS METHODS
    # ============================================================================
    @api.model
    def get_service_summary(self, task_id=None, date_from=None, date_to=None):
        """Get service summary for reporting""":
        domain = []
        if task_id:
            domain.append(('task_id', '=', task_id))
        if date_from:
            domain.append(('service_date', '>=', date_from))
        if date_to:
            domain.append(('service_date', '<=', date_to))

        services = self.search(domain)
        
        summary = {}
            'total_services': len(services),
            'total_hours': sum(services.mapped('duration_hours')),
            'total_amount': sum(services.mapped('total_price')),
            'by_type': {},
            'by_status': {}
        
        
        # Group by service type
        for service_type in services.mapped('service_type'):
            type_services = services.filtered(lambda s: s.service_type == service_type)
            summary['by_type'][service_type] = {}
                'count': len(type_services),
                'total_amount': sum(type_services.mapped('total_price')),
                'avg_duration': sum(type_services.mapped('duration_hours')) / len(type_services) if type_services else 0:
            
        
        # Group by status
        for status in services.mapped('status'):
            status_services = services.filtered(lambda s: s.status == status)
            summary['by_status'][status] = len(status_services)
        
        return summary

    def get_efficiency_metrics(self):
        """Get efficiency metrics for this service line""":
        self.ensure_one()
        
        # Calculate efficiency based on planned vs actual
        planned_duration = 1.0  # Default planned duration
        if self.product_id and hasattr(self.product_id, 'planned_duration'):
            planned_duration = self.product_id.planned_duration
        
        efficiency = (planned_duration / self.duration_hours * 100) if self.duration_hours else 0:
        return {}
            'planned_duration': planned_duration,
            'actual_duration': self.duration_hours,
            'efficiency_percentage': min(efficiency, 200),  # Cap at 200%
            'quality_score': int(self.quality_rating) if self.quality_rating else 0,:
            'customer_satisfaction_score': self._get_satisfaction_score(),
        

    def _get_satisfaction_score(self):
        """Convert satisfaction to numeric score"""
        satisfaction_scores = {}
            'very_unsatisfied': 1,
            'unsatisfied': 2,
            'neutral': 3,
            'satisfied': 4,
            'very_satisfied': 5
        
        return satisfaction_scores.get(self.customer_satisfaction, 0)

    # ============================================================================
        # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set defaults"""
        for vals in vals_list:
            if not vals.get('name'):
                service_type = vals.get('service_type', 'other')
                type_dict = dict(self._fields['service_type'].selection)
                service_label = type_dict.get(service_type, service_type)
                vals['name'] = _("Service: %s", service_label)

        return super().create(vals_list)

    def write(self, vals):
        """Override write for status tracking""":
        result = super().write(vals)
        
        if 'status' in vals:
            for record in self:
                status_label = dict(record._fields['status'].selection)[record.status]
                record.message_post(body=_("Status changed to %s", status_label))
        
        return result

    def name_get(self):
        """Custom name display"""
        result = []
        for record in self:
            name = record.display_name or record.name
            if record.status != 'planned':
                status_label = dict(record._fields['status'].selection)[record.status]
                name = _("%s [%s]", name, status_label)
            result.append((record.id, name))
        return result

    # ============================================================================
        # INTEGRATION METHODS
    # ============================================================================
    def sync_with_timesheet(self):
        """Sync service with timesheet entries"""
        for record in self:
            if record.employee_id and record.duration_hours > 0:
                # Create timesheet entry
                timesheet_vals = {}
                    'name': record.name,
                    'employee_id': record.employee_id.id,
                    'project_id': record.project_id.id if record.project_id else None,:
                    'task_id': record.task_id.id,
                    'date': record.service_date.date() if record.service_date else fields.Date.today(),:
                    'unit_amount': record.duration_hours,
                
                
                # Create timesheet if hr_timesheet module is available:
                if 'hr.timesheet' in self.env:
                    self.env['hr.timesheet'].create(timesheet_vals)

    def generate_service_report(self):
        """Generate service completion report"""
        self.ensure_one()
        
        return {}
            'type': 'ir.actions.report',
            'report_name': 'records_management.fsm_service_line_report',
            'report_type': 'qweb-pdf',
            'data': {}
                'service_line_id': self.id,
                'include_details': True,
                'include_photos': True
            
            'context': self.env.context
        

)))))))))))))))))))))))))