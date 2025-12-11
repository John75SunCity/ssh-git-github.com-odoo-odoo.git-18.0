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

    # Simplified workflow: Scheduled → In Progress → Completed → Invoiced
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('pending_billing', 'Pending Billing'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='scheduled', required=True, tracking=True)

    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, tracking=True)
    department_id = fields.Many2one(
        comodel_name='records.department',
        string="Department",
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
        help="Optional department for service address and billing purposes"
    )
    portal_request_id = fields.Many2one(comodel_name='portal.request', string="Portal Request", ondelete='set null')

    # ============================================================================
    # PICKUP/SERVICE LOCATION (Customer Address Selection)
    # ============================================================================
    customer_staging_location_id = fields.Many2one(
        comodel_name='customer.staging.location',
        string="Staging Location",
        domain="[('partner_id', '=', partner_id), '|', ('department_id', '=', department_id), ('department_id', '=', False)]",
        tracking=True,
        help="Customer's staging location from portal. Helps technicians find containers on-site."
    )
    use_service_location = fields.Boolean(
        string="Use Service Location",
        default=False,
        help="Check to select a specific pickup/service address for this work order. "
             "The address will print on work orders and invoices. "
             "If unchecked, the customer's default address is used."
    )
    service_location_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Location",
        domain="[('parent_id', '=', partner_id), ('is_service_location', '=', True)]",
        help="Select a saved service location, or create a new one. "
             "New locations are saved for future use."
    )
    # Effective address used for invoices/reports - computed based on checkbox
    effective_service_address = fields.Text(
        string="Service Address",
        compute='_compute_effective_service_address',
        store=True,
        help="The address where service will be performed. "
             "Uses service location if selected, otherwise customer's default address."
    )
    effective_service_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Address Contact",
        compute='_compute_effective_service_address',
        store=True,
        help="The contact record for the service address (for invoice printing)"
    )

    @api.depends('use_service_location', 'service_location_id', 'partner_id')
    def _compute_effective_service_address(self):
        """Compute the effective service address based on checkbox selection.
        
        - If use_service_location is True and service_location_id is set:
          Use the service location's address
        - Otherwise: Use the customer's (partner_id) default address
        """
        for order in self:
            if order.use_service_location and order.service_location_id:
                # Use service location address
                order.effective_service_partner_id = order.service_location_id
                order.effective_service_address = order.service_location_id.contact_address or ''
            elif order.partner_id:
                # Use customer's default address
                order.effective_service_partner_id = order.partner_id
                order.effective_service_address = order.partner_id.contact_address or ''
            else:
                order.effective_service_partner_id = False
                order.effective_service_address = ''

    @api.onchange('use_service_location')
    def _onchange_use_service_location(self):
        """Clear service location when checkbox is unchecked."""
        if not self.use_service_location:
            self.service_location_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id_service_location(self):
        """Clear service location when customer changes."""
        self.service_location_id = False

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
        ('bin_onetime', 'One-Time Purge'),
        ('bin_recurring', 'Recurring Bin Service'),
        ('bin_mobile', 'Mobile Bin Service'),
    ], string="Service Type", default='onsite', tracking=True)

    material_type = fields.Selection([
        ('paper', 'Paper Documents'),
        ('hard_drive', 'Hard Drives'),
        ('mixed_media', 'Mixed Media (Tapes, CDs, etc.)'),
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

    # ============================================================================
    # SIGNATURE FIELDS
    # ============================================================================
    technician_signature = fields.Binary(
        string="Technician Signature",
        help="Digital signature of the technician who performed the service"
    )
    technician_signature_date = fields.Datetime(
        string="Technician Signed Date",
        readonly=True,
        help="Date and time when technician signed"
    )
    technician_printed_name = fields.Char(
        string="Technician Printed Name",
        help="Printed name of the technician"
    )
    customer_signature = fields.Binary(
        string="Customer Signature",
        help="Digital signature of the customer representative"
    )
    customer_signature_date = fields.Datetime(
        string="Customer Signed Date",
        readonly=True,
        help="Date and time when customer signed"
    )
    customer_printed_name = fields.Char(
        string="Customer Printed Name",
        help="Printed name of the customer representative"
    )

    # ============================================================================
    # WITNESS FIELDS (for NAID compliance)
    # ============================================================================
    witness_required = fields.Boolean(
        string="Witness Required",
        default=False,
        tracking=True,
        help="Check if a witness is required for this destruction service"
    )
    witness_name = fields.Char(
        string="Witness Name",
        tracking=True,
        help="Name of the witness present during destruction"
    )
    witness_signature = fields.Binary(
        string="Witness Signature",
        help="Digital signature of the witness"
    )
    witness_signature_date = fields.Datetime(
        string="Witness Signed Date",
        readonly=True,
        help="Date and time when witness signed"
    )

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
        
        records = super().create(vals_list)
        
        # Approve portal requests when linked during creation
        for record in records:
            if record.portal_request_id and record.portal_request_id.state in ['draft', 'submitted', 'pending']:
                record.portal_request_id.write({
                    'state': 'approved',
                    'work_order_id': record.id,
                })
                record.portal_request_id.message_post(
                    body=_("Request approved and linked to Shredding Work Order: %s") % record.name
                )
        
        return records

    def write(self, vals):
        # Track if portal_request_id is being set
        portal_request_to_approve = False
        if 'portal_request_id' in vals and vals['portal_request_id']:
            portal_request_to_approve = self.env['portal.request'].browse(vals['portal_request_id'])
        
        if 'state' in vals and vals['state'] == 'in_progress':
            vals.setdefault('start_date', fields.Datetime.now())
        if 'state' in vals and vals['state'] == 'completed':
            vals.setdefault('completion_date', fields.Datetime.now())
        
        result = super().write(vals)
        
        # Approve portal request when linked to work order
        if portal_request_to_approve and portal_request_to_approve.state in ['draft', 'submitted', 'pending']:
            portal_request_to_approve.write({
                'state': 'approved',
                'work_order_id': self.id if len(self) == 1 else False,
            })
            portal_request_to_approve.message_post(
                body=_("Request approved and linked to Shredding Work Order: %s") % self.name
            )
        
        return result

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_work_from_scheduled(self):
        """Start work directly from scheduled state."""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled work orders can be started."))
        # Create FSM task if not already linked
        if not self.fsm_task_id:
            self._create_fsm_task()
        self.write({'state': 'in_progress', 'start_date': fields.Datetime.now()})
        self.message_post(body=_("Work order started."))

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

    def action_complete_work(self):
        """Complete the work order and handle billing based on customer preference."""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress work orders can be completed."))
        self.write({'state': 'completed', 'completion_date': fields.Datetime.now()})
        if self.certificate_required and not self.certificate_id:
            self._generate_destruction_certificate()
        self.message_post(body=_("Work order completed."))

        # Handle billing preference
        if self.partner_id.consolidated_billing:
            self.state = 'pending_billing'
            self.message_post(body=_("Marked as pending monthly billing."))
        else:
            self.action_create_invoice()
            self.state = 'invoiced'
            self.message_post(body=_("Immediate invoice created."))

    def action_cancel(self):
        """Cancel the work order."""
        self.ensure_one()
        if self.state in ['completed', 'invoiced', 'cancelled']:
            raise UserError(_("Cannot cancel a work order that is already completed, invoiced, or cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order cancelled."))

    def action_reset_to_scheduled(self):
        """Reset work order back to scheduled state."""
        self.ensure_one()
        self.write({'state': 'scheduled'})
        self.message_post(body=_("Work order reset to scheduled."))

    def action_invoice(self):
        """Mark work order as invoiced."""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Only completed work orders can be invoiced."))
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
        
        if self.state not in ['scheduled', 'in_progress']:
            return {
                'success': False,
                'message': _('Work order must be scheduled or in progress to scan barcodes')
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
        if self.state not in ['scheduled', 'in_progress']:
            raise UserError(_("Can only scan barcodes for scheduled or in-progress work orders."))
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
    # BIN SERVICE SCANNING ACTIONS (TIP/SWAP WORKFLOW)
    # ============================================================================
    def action_open_bin_service_scanner(self):
        """
        Open the bin service scanner wizard for TIP/SWAP operations.
        
        This is the main entry point for technicians servicing bins.
        They can choose TIP or SWAP mode, then scan bins to record service.
        
        Returns:
            dict: Action to open bin service wizard
        """
        self.ensure_one()
        if self.state not in ['scheduled', 'in_progress']:
            raise UserError(_("Work order must be scheduled or in progress to scan bins."))
        
        return {
            'name': _('Bin Service Scanner'),
            'type': 'ir.actions.act_window',
            'res_model': 'work.order.bin.service.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            }
        }

    def action_tip_bin(self, bin_barcode):
        """
        Record a TIP service for a bin.
        
        TIP = Empty the bin's contents into the shredding truck and return 
        the same bin to the customer. Creates 1 billable service event.
        
        Args:
            bin_barcode (str): Barcode of the bin being tipped
            
        Returns:
            dict: Result with success status, message, and event details
        """
        self.ensure_one()
        
        if self.state not in ['scheduled', 'in_progress']:
            return {
                'success': False,
                'message': _('Work order must be scheduled or in progress to record bin service')
            }
        
        # Auto-start work if scheduled
        if self.state == 'scheduled':
            self.write({'state': 'in_progress', 'start_date': fields.Datetime.now()})
        
        # Find bin by barcode
        ShredBin = self.env['shredding.service.bin']
        bin_record = ShredBin.search([('barcode', '=', bin_barcode)], limit=1)
        
        if not bin_record:
            return {
                'success': False,
                'message': _('No bin found with barcode: %s') % bin_barcode
            }
        
        # Create TIP service event (billable)
        event = self.env['shredding.service.event'].create_tip_event(
            bin_id=bin_record.id,
            customer_id=self.partner_id.id,
            shredding_work_order_id=self.id,
            notes=_("Tipped during work order %s") % self.name
        )
        
        # Update scan time
        self.write({'last_scan_time': fields.Datetime.now()})
        
        # Log in chatter
        self.message_post(
            body=_('TIP: Bin %s (Size: %s) - Billable: %s') % (
                bin_record.barcode, 
                bin_record.bin_size_id.name if bin_record.bin_size_id else 'N/A',
                event.billable_amount
            ),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'success': True,
            'message': _('TIP recorded: %s') % bin_record.barcode,
            'event_id': event.id,
            'bin_name': bin_record.name,
            'bin_barcode': bin_record.barcode,
            'billable_amount': event.billable_amount,
            'service_type': 'tip',
            'total_billable': self.total_billable_amount,
        }

    def action_swap_bin(self, old_bin_barcode, new_bin_barcode):
        """
        Record a SWAP service for bins.
        
        SWAP = Take away a full bin (swap_out) and leave an empty bin (swap_in).
        Only the swap_out is billable - the swap_in is just inventory tracking.
        Creates 2 service events but only 1 is billable.
        
        Args:
            old_bin_barcode (str): Barcode of the full bin being picked up (BILLABLE)
            new_bin_barcode (str): Barcode of the empty bin being left (NOT billable)
            
        Returns:
            dict: Result with success status and swap details
        """
        self.ensure_one()
        
        if self.state not in ['scheduled', 'in_progress']:
            return {
                'success': False,
                'message': _('Work order must be scheduled or in progress to record bin service')
            }
        
        # Auto-start work if scheduled
        if self.state == 'scheduled':
            self.write({'state': 'in_progress', 'start_date': fields.Datetime.now()})
        
        # Find both bins
        ShredBin = self.env['shredding.service.bin']
        old_bin = ShredBin.search([('barcode', '=', old_bin_barcode)], limit=1)
        new_bin = ShredBin.search([('barcode', '=', new_bin_barcode)], limit=1)
        
        if not old_bin:
            return {
                'success': False,
                'message': _('Old bin not found with barcode: %s') % old_bin_barcode
            }
        
        if not new_bin:
            return {
                'success': False,
                'message': _('New bin not found with barcode: %s') % new_bin_barcode
            }
        
        if old_bin_barcode == new_bin_barcode:
            return {
                'success': False,
                'message': _('Swap requires two different bins. Use TIP for same bin.')
            }
        
        # Create SWAP service events (only swap_out is billable)
        events = self.env['shredding.service.event'].create_swap_events(
            old_bin_id=old_bin.id,
            new_bin_id=new_bin.id,
            customer_id=self.partner_id.id,
            shredding_work_order_id=self.id,
            notes=_("Swapped during work order %s") % self.name
        )
        
        # Get the billable event (swap_out)
        billable_event = events.filtered(lambda e: e.is_billable)[:1]
        
        # Update scan time
        self.write({'last_scan_time': fields.Datetime.now()})
        
        # Log in chatter
        self.message_post(
            body=_('SWAP: Picked up %s (Size: %s), Left %s - Billable: %s') % (
                old_bin.barcode,
                old_bin.bin_size_id.name if old_bin.bin_size_id else 'N/A',
                new_bin.barcode,
                billable_event.billable_amount if billable_event else 0
            ),
            subtype_xmlid='mail.mt_note'
        )
        
        return {
            'success': True,
            'message': _('SWAP recorded: %s → %s') % (old_bin.barcode, new_bin.barcode),
            'event_ids': events.ids,
            'old_bin_barcode': old_bin.barcode,
            'new_bin_barcode': new_bin.barcode,
            'billable_amount': billable_event.billable_amount if billable_event else 0,
            'service_type': 'swap',
            'total_billable': self.total_billable_amount,
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('scheduled_date')
    def _check_scheduled_date(self):
        for order in self:
            if order.state == 'scheduled' and order.scheduled_date and order.scheduled_date < fields.Datetime.now():
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

    @api.model
    def _monthly_bill_pending(self):
        """Cron method to batch invoice pending_billing work orders at month end."""
        pending_orders = self.search([('state', '=', 'pending_billing')])
        
        # Group by customer
        orders_by_partner = {}
        for order in pending_orders:
            if order.partner_id.id not in orders_by_partner:
                orders_by_partner[order.partner_id.id] = []
            orders_by_partner[order.partner_id.id].append(order)
        
        for partner_id, orders in orders_by_partner.items():
            partner = self.env['res.partner'].browse(partner_id)
            invoice_vals = {
                'partner_id': partner_id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
                'ref': _("Monthly Shredding Services"),
                'invoice_line_ids': [],
            }
            
            for order in orders:
                line_vals = order._prepare_invoice_line_values()
                line_vals['name'] = _("Shredding Work Order %s") % order.name
                invoice_vals['invoice_line_ids'].append((0, 0, line_vals))
            
            invoice = self.env['account.move'].create(invoice_vals)
            invoice.action_post()
            
            # Update orders
            for order in orders:
                order.write({
                    'invoice_id': invoice.id,
                    'state': 'invoiced'
                })
                order.message_post(body=_("Invoiced in monthly batch: %s") % invoice.name)
