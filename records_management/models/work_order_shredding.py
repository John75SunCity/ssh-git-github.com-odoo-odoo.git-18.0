from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class WorkOrderShredding(models.Model):
    _name = "work.order.shredding"
    _description = 'Shredding Work Order Management'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.invoice.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Work Order #", required=True, copy=False, readonly=True, default=lambda self: "New")
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', required=True, tracking=True)

    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, tracking=True)
    portal_request_id = fields.Many2one(comodel_name='portal.request', string="Portal Request", ondelete='set null')

    # ============================================================================
    # FSM INTEGRATION - All services are scheduled via FSM tasks
    # ============================================================================
    fsm_task_id = fields.Many2one(
        comodel_name='project.task',
        string="FSM Task",
        domain="[('is_fsm', '=', True)]",
        help="Linked Field Service task for scheduling, technician assignment, and mobile workflow",
        tracking=True,
        copy=False
    )
    fsm_task_state = fields.Char(
        related='fsm_task_id.stage_id.name',
        string="FSM Status",
        readonly=True
    )
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Sales Order",
        help="Linked sales order for invoicing",
        tracking=True,
        copy=False
    )

    scheduled_date = fields.Datetime(string="Scheduled Date", required=True, tracking=True)
    start_date = fields.Datetime(string='Start Time', readonly=True, copy=False)
    completion_date = fields.Datetime(string='Completion Time', readonly=True, copy=False)
    actual_duration = fields.Float(string="Duration (Hours)", compute='_compute_actual_duration', store=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string="Priority", default='0', tracking=True)

    assigned_team_id = fields.Many2one(comodel_name='maintenance.team', string="Assigned Team")
    technician_ids = fields.Many2many(
        'hr.employee',
        relation='work_order_shredding_technician_rel',
        column1='work_order_id',
        column2='employee_id',
        string="Assigned Technicians"
    )
    equipment_ids = fields.Many2many(
        'maintenance.equipment',
        relation='work_order_shredding_equipment_rel',
        column1='work_order_id',
        column2='equipment_id',
        string="Assigned Equipment"
    )
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string="Assigned Vehicle")

    # ============================================================================
    # SERVICE TYPE AND BILLING
    # ============================================================================
    shredding_service_type = fields.Selection([
        ('onsite', 'On-Site Shredding'),
        ('offsite', 'Off-Site Shredding'),
        ('mobile', 'Mobile Shredding Truck'),
        ('bin_onetime', 'One-Time Bin Service'),
        ('bin_recurring', 'Recurring Bin Service'),
        ('bin_mobile', 'Mobile Bin Service'),
    ], string="Service Type", default='onsite', tracking=True)

    material_type = fields.Selection([
        ('paper', 'Paper'),
        ('hard_drive', 'Hard Drives'),
        ('mixed_media', 'Mixed Media'),
    ], string="Material Type", default='paper')

    # Quantity-based billing (per unit, not weight)
    bin_quantity = fields.Integer(
        string="Number of Bins",
        default=1,
        tracking=True,
        help="Quantity of bins for the service (billed per unit)"
    )

    # Weight fields kept for reference/reporting only
    estimated_weight = fields.Float(string="Estimated Weight (kg)")
    actual_weight = fields.Float(string="Actual Weight (kg)", tracking=True)
    boxes_count = fields.Integer(string="Number of Boxes Picked Up", default=0, tracking=True)

    special_instructions = fields.Text(string="Special Instructions")
    completion_notes = fields.Text(string="Completion Notes")

    # Portal visibility
    portal_visible = fields.Boolean(
        string='Visible in Portal',
        default=True,
        help='If checked, this work order will be visible to the customer in their portal'
    )

    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    certificate_id = fields.Many2one(comodel_name='naid.certificate', string="Destruction Certificate", readonly=True, copy=False)

    # Invoice related fields
    invoice_id = fields.Many2one(comodel_name='account.move', string='Invoice', readonly=True, copy=False)
    invoiced = fields.Boolean(string="Invoiced", compute='_compute_invoiced', store=True)

    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    # currency_id provided by work.order.invoice.mixin
    active = fields.Boolean(default=True)

    # Computed count fields for stat buttons
    certificate_count = fields.Integer(string="Certificates Count", compute='_compute_certificate_count', store=False)
    completion_percentage = fields.Float(string="Completion %", compute='_compute_completion_percentage', store=False)

    # ============================================================================
    # BARCODE SCANNING FIELDS
    # ============================================================================
    scanned_barcode_ids = fields.Many2many(
        comodel_name='records.container',
        relation='work_order_shredding_scanned_barcodes',
        column1='work_order_id',
        column2='container_id',
        string='Scanned Containers',
        help="Containers that were scanned during this work order"
    )
    scanned_count = fields.Integer(
        string='Scanned Items',
        compute='_compute_scanned_count',
        store=True
    )
    last_scan_time = fields.Datetime(
        string='Last Scan',
        readonly=True,
        help="Timestamp of the most recent barcode scan"
    )

    # ============================================================================
    # SERVICE EVENT TRACKING
    # ============================================================================
    service_event_ids = fields.One2many(
        comodel_name='shredding.service.event',
        inverse_name='shredding_work_order_id',
        string="Service Events"
    )
    billable_event_count = fields.Integer(
        string="Billable Services",
        compute='_compute_service_event_stats',
        store=True,
        help="Number of billable service events (tips + swaps)"
    )
    total_billable_amount = fields.Monetary(
        string="Total Billable",
        compute='_compute_service_event_stats',
        store=True,
        currency_field='currency_id',
        help="Total amount to bill for all services"
    )
    total_scans = fields.Integer(
        string="Total Scans",
        compute='_compute_service_event_stats',
        store=True,
        help="Total barcode scans performed (including non-billable)"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'state')
    def _compute_display_name(self):
        for order in self:
            state_label = dict(order._fields['state'].selection).get(order.state, '')
            customer_name = order.partner_id.name or ''
            order.display_name = f"{order.name} - {customer_name} ({state_label})"

    @api.depends('start_date', 'completion_date')
    def _compute_actual_duration(self):
        for order in self:
            if order.start_date and order.completion_date:
                delta = order.completion_date - order.start_date
                order.actual_duration = delta.total_seconds() / 3600.0
            else:
                order.actual_duration = 0.0

    @api.depends('scanned_barcode_ids')
    def _compute_scanned_count(self):
        """Count of containers scanned during work order."""
        for order in self:
            order.scanned_count = len(order.scanned_barcode_ids)

    @api.depends('state', 'invoice_id')
    def _compute_invoiced(self):
        for order in self:
            order.invoiced = order.state == 'invoiced' or bool(order.invoice_id)

    @api.depends('certificate_id')
    def _compute_certificate_count(self):
        """Compute whether a destruction certificate exists"""
        for order in self:
            order.certificate_count = 1 if order.certificate_id else 0

    @api.depends('state')
    def _compute_completion_percentage(self):
        """Compute completion percentage based on state"""
        state_completion = {
            'draft': 0,
            'confirmed': 20,
            'assigned': 40,
            'in_progress': 70,
            'completed': 95,
            'verified': 100,
            'invoiced': 100,
            'cancelled': 0,
        }
        for order in self:
            order.completion_percentage = state_completion.get(order.state, 0)

    @api.depends('service_event_ids', 'service_event_ids.is_billable', 'service_event_ids.billable_amount')
    def _compute_service_event_stats(self):
        """
        Compute billing statistics from service events.
        
        Billing Logic:
        - TIP: 1 scan = 1 billable event
        - SWAP: 2 scans (swap_out + swap_in) = 1 billable event (only swap_out is billable)
        - Deliveries, pickups, maintenance are NOT billable (logistics/internal)
        """
        for order in self:
            all_events = order.service_event_ids
            billable_events = all_events.filtered(lambda e: e.is_billable)
            
            order.total_scans = len(all_events)
            order.billable_event_count = len(billable_events)
            order.total_billable_amount = sum(billable_events.mapped('billable_amount'))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.shredding') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        if 'state' in vals and vals['state'] == 'in_progress':
            vals.setdefault('start_date', fields.Datetime.now())
        if 'state' in vals and vals['state'] == 'completed':
            vals.setdefault('completion_date', fields.Datetime.now())
        return super().write(vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the work order and optionally create linked FSM task."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        
        # Create FSM task if not already linked
        if not self.fsm_task_id:
            self._create_fsm_task()
        
        self.write({'state': 'confirmed'})
        self.message_post(body=_("Work order confirmed."))

    def _create_fsm_task(self):
        """
        Create a linked FSM task for this shredding work order.
        Uses Odoo's Field Service infrastructure for scheduling.
        """
        self.ensure_one()
        
        # Get or create the FSM project for shredding services
        fsm_project = self.env['project.project'].search([
            ('is_fsm', '=', True),
            ('name', 'ilike', 'shredding')
        ], limit=1)
        
        if not fsm_project:
            # Use default FSM project
            fsm_project = self.env['project.project'].search([
                ('is_fsm', '=', True)
            ], limit=1)
        
        if not fsm_project:
            # FSM module not properly configured, skip FSM task creation
            return
        
        # Map material type to service type for FSM
        service_type_map = {
            'paper': 'on_site_shredding',
            'hard_drive': 'hard_drive_destruction',
            'mixed_media': 'off_site_shredding',
        }
        
        task_vals = {
            'name': _("Shredding Service: %s") % self.name,
            'project_id': fsm_project.id,
            'partner_id': self.partner_id.id,
            'is_fsm': True,
            'date_deadline': self.scheduled_date.date() if self.scheduled_date else False,
            'description': self.special_instructions or '',
            'shredding_work_order_id': self.id,  # Link back to this work order
        }
        
        # Add FSM-specific fields if they exist on project.task
        if 'service_type' in self.env['project.task']._fields:
            task_vals['service_type'] = service_type_map.get(self.material_type, 'on_site_shredding')
        if 'material_type' in self.env['project.task']._fields:
            task_vals['material_type'] = self.material_type
        
        fsm_task = self.env['project.task'].create(task_vals)
        self.fsm_task_id = fsm_task
        
        self.message_post(
            body=_("FSM Task %s created for scheduling and technician assignment.") % fsm_task.name
        )

    def action_open_fsm_task(self):
        """Open the linked FSM task for scheduling and management."""
        self.ensure_one()
        if not self.fsm_task_id:
            raise UserError(_("No FSM task linked. Confirm the work order first."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task'),
            'res_model': 'project.task',
            'res_id': self.fsm_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_start_work(self):
        self.ensure_one()
        if self.state not in ['confirmed', 'assigned']:
            raise UserError(_("Work order must be confirmed or assigned before starting."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Work order started."))

    def action_complete_work(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress work orders can be completed."))
        self.write({'state': 'completed'})
        if self.certificate_required and not self.certificate_id:
            self._generate_destruction_certificate()
        self.message_post(body=_("Work order completed."))

    def action_verify(self):
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed work orders can be verified."))
        self.write({'state': 'verified'})
        self.message_post(body=_("Work order verified by %s.", self.env.user.name))

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['completed', 'verified', 'invoiced', 'cancelled']:
            raise UserError(_("Cannot cancel a work order that is already completed, verified, invoiced, or cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({'state': 'draft'})
        self.message_post(body=_("Work order reset to draft."))

    def action_invoice(self):
        """Mark work order as invoiced"""
        self.ensure_one()
        if self.state not in ['completed', 'verified']:
            raise UserError(_("Only completed or verified work orders can be invoiced."))
        self.write({'state': 'invoiced'})
        self.message_post(body=_("Work order marked as invoiced."))

    def action_view_certificate(self):
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(_("No certificate associated with this work order."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificate"),
            "res_model": "naid.certificate",
            "res_id": self.certificate_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_view_certificates(self):
        """Open the associated destruction certificate"""
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(_("No certificate associated with this work order."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Destruction Certificate"),
            "res_model": "naid.certificate",
            "res_id": self.certificate_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _generate_destruction_certificate(self):
        """Generate destruction certificate with box count details"""
        self.ensure_one()
        if self.certificate_id:
            return self.certificate_id

        certificate_vals = {
            'name': _("Certificate for %s", self.name),
            'certificate_type': 'destruction',
            'partner_id': self.partner_id.id,
            'work_order_id': self.id,
            'destruction_date': self.completion_date or fields.Datetime.now(),
            'total_weight': self.actual_weight,
            'material_type': self.material_type,
        }
        certificate = self.env['naid.certificate'].create(certificate_vals)
        
        # Create destruction item line for the boxes count
        if self.boxes_count > 0:
            self.env['naid.certificate.destruction.item'].create({
                'certificate_id': certificate.id,
                'description': _("%d Boxes of %s", self.boxes_count, self.material_type or 'Mixed Media'),
                'quantity': self.boxes_count,
                'weight': self.actual_weight / self.boxes_count if self.boxes_count else 0,
            })
        
        self.certificate_id = certificate
        self.message_post(body=_("Destruction Certificate %s created for %d boxes.", certificate.name, self.boxes_count))
        return certificate

    def action_scan_barcode(self, barcode_value):
        """
        Scan a barcode during work order execution.
        Can be called from mobile app, USB scanner, or manual entry.
        
        Args:
            barcode_value (str): The barcode value to scan
            
        Returns:
            dict: Result with success status and message
        """
        self.ensure_one()
        
        if self.state not in ['confirmed', 'assigned', 'in_progress']:
            return {
                'success': False,
                'message': _('Work order must be confirmed/in progress to scan barcodes')
            }
        
        # Find container by barcode
        container = self.env['records.container'].search([
            '|',
            ('barcode', '=', barcode_value),
            ('temp_barcode', '=', barcode_value)
        ], limit=1)
        
        if not container:
            return {
                'success': False,
                'message': _('No container found with barcode: %s') % barcode_value
            }
        
        # Check if already scanned
        if container in self.scanned_barcode_ids:
            return {
                'success': False,
                'message': _('Container %s already scanned') % container.name,
                'warning': True
            }
        
        # Add to scanned list
        self.write({
            'scanned_barcode_ids': [(4, container.id)],
            'last_scan_time': fields.Datetime.now(),
        })
        
        # Log in chatter
        self.message_post(
            body=_('Container scanned: %s (Barcode: %s)') % (container.name, barcode_value),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'success': True,
            'message': _('Scanned: %s') % container.name,
            'container_id': container.id,
            'container_name': container.name,
            'total_scanned': len(self.scanned_barcode_ids)
        }

    def action_open_scanner(self):
        """Open barcode scanner wizard for continuous scanning."""
        self.ensure_one()
        return {
            'name': _('Scan Barcodes'),
            'type': 'ir.actions.act_window',
            'res_model': 'barcode.scan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_model': self._name,
                'default_work_order_id': self.id,
            }
        }

    def action_open_camera_scanner(self):
        """
        Directly open the camera barcode scanner (bypasses wizard popup).
        
        This launches the Scanbot SDK camera scanner as a client action.
        Scanned barcodes are automatically sent to action_scan_barcode().
        Perfect for mobile scanning workflows on work orders.
        
        Returns:
            dict: Client action to launch rm_camera_scanner
        """
        self.ensure_one()
        if self.state not in ['draft', 'confirmed', 'assigned', 'in_progress']:
            raise UserError(_("Can only scan barcodes for active work orders."))
        return {
            'type': 'ir.actions.client',
            'tag': 'rm_camera_scanner',
            'name': _('Camera Scanner - %s') % self.name,
            'context': {
                'operation_mode': 'work_order',
                'work_order_model': self._name,
                'work_order_id': self.id,
            },
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for order in self:
            if order.state == 'draft' and order.scheduled_date and order.scheduled_date < fields.Datetime.now():
                raise ValidationError(_("Scheduled date cannot be in the past."))

    @api.constrains('start_date', 'completion_date')
    def _check_date_sequence(self):
        for order in self:
            if order.start_date and order.completion_date and order.start_date > order.completion_date:
                raise ValidationError(_("Completion date must be after the start date."))

    @api.constrains('estimated_weight', 'actual_weight')
    def _check_weights(self):
        for order in self:
            if order.estimated_weight and order.estimated_weight < 0:
                raise ValidationError(_("Estimated weight cannot be negative."))
            if order.actual_weight and order.actual_weight < 0:
                raise ValidationError(_("Actual weight cannot be negative."))

    # ============================================================================
    # BILLING METHODS
    # ============================================================================
    def get_billable_summary(self):
        """
        Get a summary of billable events from this work order.
        
        Billing Logic:
        - TIP: 1 scan = 1 billable event = 1 charge
        - SWAP: 2 scans (swap_out + swap_in) = 1 billable event = 1 charge
        - Deliveries, pickups, maintenance are NOT billable
        
        Returns:
            dict with billing summary
        """
        self.ensure_one()
        
        billable_events = self.service_event_ids.filtered(lambda e: e.is_billable)
        
        # Group by service type
        tips = billable_events.filtered(lambda e: e.service_type == 'tip')
        swaps = billable_events.filtered(lambda e: e.service_type == 'swap_out')
        
        return {
            'total_scans': len(self.service_event_ids),
            'billable_events': len(billable_events),
            'tip_count': len(tips),
            'swap_count': len(swaps),
            'tip_total': sum(tips.mapped('billable_amount')),
            'swap_total': sum(swaps.mapped('billable_amount')),
            'grand_total': self.total_billable_amount,
        }
    
    def action_create_invoice(self):
        """Create an invoice for this work order based on billable events."""
        self.ensure_one()
        
        if self.invoice_id:
            raise UserError(_("An invoice already exists for this work order."))
        
        if not self.service_event_ids.filtered(lambda e: e.is_billable):
            raise UserError(_("No billable services on this work order."))
        
        # Get billing summary
        summary = self.get_billable_summary()
        
        # Create invoice
        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_origin': self.name,
            'invoice_date': fields.Date.today(),
            'ref': _("Shredding Services - %s") % self.name,
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Get the default shredding service product
        shredding_product = self.env.ref(
            'records_management.product_shredding_service', 
            raise_if_not_found=False
        )
        
        # Create invoice lines for each billable event
        for event in self.service_event_ids.filtered(lambda e: e.is_billable):
            line_vals = {
                'move_id': invoice.id,
                'name': _("%s - Bin %s") % (
                    dict(event._fields['service_type'].selection).get(event.service_type),
                    event.bin_id.barcode
                ),
                'quantity': 1,
                'price_unit': event.billable_amount,
            }
            if shredding_product:
                line_vals['product_id'] = shredding_product.id
            
            self.env['account.move.line'].create(line_vals)
        
        # Link invoice to work order
        self.write({
            'invoice_id': invoice.id,
            'state': 'invoiced',
        })
        
        self.message_post(
            body=_("Invoice %s created with %d billable services, total: %s") % (
                invoice.name or invoice.id,
                summary['billable_events'],
                summary['grand_total']
            ),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'type': 'ir.actions.act_window',
            'name': _('Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
        }
