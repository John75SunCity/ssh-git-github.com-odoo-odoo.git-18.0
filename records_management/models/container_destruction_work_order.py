# -*- coding: utf-8 -*-
"""
Container Destruction Work Order Module

Manages the entire lifecycle of destroying records containers, from initial
request and authorization to final certification, ensuring a compliant
and auditable process.

Author: Records Management System
Version: 18.0.0.2.29
License: LGPL-3
"""

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ContainerDestructionWorkOrder(models.Model):
    _name = 'container.destruction.work.order'
    _description = 'Container Destruction Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.invoice.mixin']
    _order = 'priority desc, scheduled_destruction_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION & WORKFLOW
    # ============================================================================
    name = fields.Char(
        string='Work Order Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: "New"
    )
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', required=True, default=lambda self: self.env.company)
    user_id = fields.Many2one(comodel_name='res.users', string='Responsible', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)
    # Simplified workflow: Scheduled → In Progress → Completed → Invoiced
    # Certificate of destruction is generated automatically with invoice
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', required=True, tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string='Priority', default='0')

    # ------------------------------------------------------------------
    # PORTAL VISIBILITY
    # ------------------------------------------------------------------
    portal_visible = fields.Boolean(
        string='Portal Visible',
        default=True,
        help='Controls whether this destruction work order is visible in the customer portal.\n'
             'Used by unified work order portal controller domain filtering. Disable to hide sensitive or internal-only orders.'
    )

    # ============================================================================
    # CUSTOMER & AUTHORIZATION
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    department_id = fields.Many2one(
        comodel_name='records.department',
        string="Department",
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
        help="Optional department for service address and billing purposes"
    )
    portal_request_id = fields.Many2one(comodel_name='portal.request', string='Portal Request', ondelete='set null')

    # Pickup/Service Location
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
             "If unchecked, the customer's default address is used."
    )
    service_location_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Location",
        domain="[('parent_id', '=', partner_id), ('is_service_location', '=', True)]",
        help="Select a saved service location for pickup. New locations are saved for future use."
    )
    effective_service_address = fields.Text(
        string="Service Address",
        compute='_compute_effective_service_address',
        store=True,
        help="The address where pickup will occur."
    )
    effective_service_partner_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Address Contact",
        compute='_compute_effective_service_address',
        store=True
    )

    @api.depends('use_service_location', 'service_location_id', 'partner_id')
    def _compute_effective_service_address(self):
        """Compute effective address: service location if selected, else customer default."""
        for order in self:
            if order.use_service_location and order.service_location_id:
                order.effective_service_partner_id = order.service_location_id
                order.effective_service_address = order.service_location_id.contact_address or ''
            elif order.partner_id:
                order.effective_service_partner_id = order.partner_id
                order.effective_service_address = order.partner_id.contact_address or ''
            else:
                order.effective_service_partner_id = False
                order.effective_service_address = ''

    @api.onchange('use_service_location')
    def _onchange_use_service_location(self):
        if not self.use_service_location:
            self.service_location_id = False

    @api.onchange('partner_id')
    def _onchange_partner_id_service_location(self):
        self.service_location_id = False

    destruction_reason = fields.Text(string='Reason for Destruction')
    customer_authorized = fields.Boolean(string='Customer Authorized', readonly=True)
    customer_authorization_date = fields.Datetime(string='Authorization Date', readonly=True)
    authorized_by = fields.Char(string='Authorized By', tracking=True)
    authorization_document = fields.Binary(string='Authorization Document', attachment=True)

    # ============================================================================
    # CONTAINER & INVENTORY DETAILS
    # ============================================================================
    container_ids = fields.Many2many(
        'records.container',
        relation='container_destruction_work_order_container_rel',
        column1='work_order_id',
        column2='container_id',
        string='Containers for Destruction',
        required=True
    )
    container_count = fields.Integer(string='Container Count', compute='_compute_container_metrics', store=True)
    total_cubic_feet = fields.Float(string='Total Cubic Feet', compute='_compute_container_metrics', store=True)
    estimated_weight_lbs = fields.Float(string='Estimated Weight (lbs)', compute='_compute_container_metrics', store=True)
    inventory_completed = fields.Boolean(string='Inventory Completed', readonly=True)
    inventory_date = fields.Datetime(string='Inventory Date', readonly=True)
    inventory_user_id = fields.Many2one(comodel_name='res.users', string='Inventoried By', readonly=True)

    # ============================================================================
    # SCHEDULING & EXECUTION
    # ============================================================================
    scheduled_destruction_date = fields.Datetime(string='Scheduled Destruction Date', tracking=True)
    pickup_date = fields.Datetime(string='Pickup Date', readonly=True)
    actual_destruction_date = fields.Datetime(string='Actual Destruction Date', readonly=True)
    estimated_duration_hours = fields.Float(string='Estimated Duration (Hours)', compute='_compute_estimated_duration')
    destruction_facility_id = fields.Many2one(comodel_name='stock.location', string='Destruction Facility', domain="[('is_destruction_facility', '=', True)]")
    shredding_equipment_id = fields.Many2one(comodel_name='maintenance.equipment', string='Shredding Equipment')
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('pulping', 'Pulping'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration')
    ], string='Destruction Method', default='shredding', required=True)
    naid_compliant = fields.Boolean(string='NAID Compliant', default=True)

    # ============================================================================
    # WITNESS & VERIFICATION
    # ============================================================================
    witness_required = fields.Boolean(
        string='Witness Required',
        help="Check if a witness is required for this destruction"
    )
    witness_name = fields.Char(
        string='Witness Name',
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
    destruction_verified = fields.Boolean(string='Destruction Verified', readonly=True)
    verification_date = fields.Datetime(string='Verification Date', readonly=True)
    verification_notes = fields.Text(string='Verification Notes')

    # ============================================================================
    # SIGNATURE FIELDS
    # ============================================================================
    technician_signature = fields.Binary(
        string="Technician Signature",
        help="Digital signature of the technician who performed the destruction"
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
    # CHAIN OF CUSTODY
    # ============================================================================
    custody_transfer_ids = fields.One2many('custody.transfer.event', 'destruction_work_order_id', string='Chain of Custody')
    custody_complete = fields.Boolean(string='Custody Complete', compute='_compute_custody_complete')
    transport_vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Transport Vehicle')
    driver_id = fields.Many2one(comodel_name='hr.employee', string='Driver')

    # ============================================================================
    # POST-DESTRUCTION & CERTIFICATION
    # ============================================================================
    actual_weight_destroyed_lbs = fields.Float(string='Actual Weight Destroyed (lbs)')
    destruction_start_time = fields.Datetime(string='Destruction Start Time', readonly=True)
    destruction_end_time = fields.Datetime(string='Destruction End Time', readonly=True)
    destruction_duration_minutes = fields.Integer(string='Destruction Duration (Minutes)', compute='_compute_destruction_duration')
    certificate_id = fields.Many2one(comodel_name='shredding.certificate', string='Certificate of Destruction', readonly=True)

    # ============================================================================
    # ============================================================================
    # BARCODE SCANNING FIELDS
    # ============================================================================
    scanned_barcode_ids = fields.Many2many(
        comodel_name='records.container',
        relation='destruction_work_order_scanned_container_rel',
        column1='work_order_id',
        column2='container_id',
        string='Scanned Containers',
        help="Containers verified via barcode scanning"
    )
    scanned_count = fields.Integer(
        string='Scanned Count',
        compute='_compute_scanned_count',
        store=True
    )
    last_scan_time = fields.Datetime(
        string='Last Scan Time',
        readonly=True
    )

    # FSM INTEGRATION - All services scheduled via FSM tasks
    # ============================================================================
    fsm_task_id = fields.Many2one(
        comodel_name='project.task',
        string="FSM Task",
        domain="[('is_fsm', '=', True)]",
        help="Linked Field Service task for scheduling and technician assignment",
        tracking=True,
        copy=False
    )
    fsm_task_state = fields.Char(
        related='fsm_task_id.stage_id.name',
        string="FSM Status",
        readonly=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'container_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.container_count:
                record.display_name = _("%s - %s (%s containers)", record.name, record.partner_id.name, record.container_count)
            elif record.partner_id:
                record.display_name = _("%s - %s", record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New Container Destruction")

    @api.depends('container_ids', 'container_ids.container_type_id')
    def _compute_container_metrics(self):
        """Compute container metrics with safe dependency pattern"""
        for record in self:
            containers = record.container_ids
            record.container_count = len(containers)

            # Safe computation of cubic feet
            total_cubic_feet = 0.0
            for container in containers:
                if hasattr(container, 'cubic_feet') and container.cubic_feet:
                    total_cubic_feet += container.cubic_feet
            record.total_cubic_feet = total_cubic_feet

            # Safe computation of estimated weight using container type definitions
            estimated_weight = 0.0
            for container in containers:
                if (hasattr(container, 'container_type_id') and
                    container.container_type_id and
                    hasattr(container.container_type_id, 'average_weight_lbs') and
                    container.container_type_id.average_weight_lbs):
                    estimated_weight += container.container_type_id.average_weight_lbs
            record.estimated_weight_lbs = estimated_weight

    @api.depends('container_count', 'destruction_method')
    def _compute_estimated_duration(self):
        for record in self:
            if record.container_count:
                base_minutes = {'shredding': 15, 'pulping': 20, 'incineration': 30, 'disintegration': 25}
                method_time = base_minutes.get(record.destruction_method, 15)
                total_minutes = (record.container_count * method_time) + 60  # Add 1hr for setup
                record.estimated_duration_hours = total_minutes / 60.0
            else:
                record.estimated_duration_hours = 0.0

    @api.depends('custody_transfer_ids.transfer_type')
    def _compute_custody_complete(self):
        for record in self:
            required_events = ['pickup', 'destruction']
            documented_events = record.custody_transfer_ids.mapped('transfer_type')
            record.custody_complete = all(event in documented_events for event in required_events)

    @api.depends('destruction_start_time', 'destruction_end_time')
    def _compute_destruction_duration(self):
        for record in self:
            if record.destruction_start_time and record.destruction_end_time:
                duration = record.destruction_end_time - record.destruction_start_time
                record.destruction_duration_minutes = int(duration.total_seconds() / 60)
            else:
                record.destruction_duration_minutes = 0

    @api.depends('scanned_barcode_ids')
    def _compute_scanned_count(self):
        for record in self:
            record.scanned_count = len(record.scanned_barcode_ids)

    # ============================================================================
    # ACTION METHODS (Simplified Workflow)
    # ============================================================================
    def action_start_destruction(self):
        """Start destruction from scheduled state."""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_("Only scheduled work orders can be started."))
        self.write({
            'state': 'in_progress',
            'destruction_start_time': fields.Datetime.now()
        })
        self.message_post(body=_("Destruction process started."))

    def action_open_scanner(self):
        """Open barcode scanner wizard for scanning containers, bins, and files."""
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

    def action_complete_destruction(self):
        """Complete destruction and generate certificate."""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress work orders can be completed."))
        self.write({
            'state': 'completed',
            'destruction_end_time': fields.Datetime.now(),
            'actual_destruction_date': fields.Datetime.now().date()
        })
        self.container_ids.write({'state': 'destroyed'})
        self.message_post(body=_("Destruction completed."))

    def action_mark_all_destroyed(self):
        """
        Mark all containers as destroyed.
        
        This action:
        1. Changes container state to 'destroyed'
        2. Updates destruction date
        3. Creates audit trail entries
        
        Returns:
            bool: True on success
        """
        self.ensure_one()
        
        if self.state not in ['in_progress', 'scheduled']:
            raise UserError(_("Work order must be scheduled or in progress."))
        
        if not self.container_ids:
            raise UserError(_("No containers selected for destruction."))
        
        destruction_date = fields.Datetime.now()
        destroyed_count = 0
        
        for container in self.container_ids:
            # Skip already destroyed containers
            if container.state == 'destroyed':
                continue
            
            # Update container state and destruction metadata
            container.sudo().write({
                'state': 'destroyed',
                'destruction_date': destruction_date.date(),
            })
            
            # Create audit log entry
            self.env['naid.audit.log'].sudo().create({
                'action_type': 'destruction',
                'container_id': container.id,
                'user_id': self.env.user.id,
                'description': _('Container %s destroyed via work order %s') % (container.name, self.name),
                'timestamp': destruction_date,
            })
            
            destroyed_count += 1
        
        if destroyed_count > 0:
            self.write({
                'state': 'completed',
                'actual_destruction_date': destruction_date.date(),
                'destruction_end_time': destruction_date,
            })
            
            self.message_post(body=_("✅ Marked %d container(s) as destroyed.") % destroyed_count)
        else:
            raise UserError(_("All containers are already destroyed."))
        
        return True

    def action_verify_and_destroy(self):
        """Verify and destroy all containers in the work order."""
        self.ensure_one()
        
        if self.state not in ['in_progress', 'scheduled']:
            raise UserError(_("Work order must be scheduled or in progress."))
        
        if not self.container_ids:
            raise UserError(_("No containers selected for destruction."))
        
        destroyed_count = 0
        failed_containers = []
        
        for container in self.container_ids:
            if container.state == 'destroyed':
                continue
            
            try:
                container.action_barcode_destroy()
                destroyed_count += 1
            except UserError as e:
                failed_containers.append((container.name, str(e)))
        
        if destroyed_count > 0:
            all_destroyed = all(c.state == 'destroyed' for c in self.container_ids)
            
            if all_destroyed:
                self.write({
                    'state': 'completed',
                    'actual_destruction_date': fields.Date.today(),
                    'destruction_end_time': fields.Datetime.now(),
                })
                message = _("✅ All %d container(s) destroyed.") % destroyed_count
            else:
                remaining = len(self.container_ids.filtered(lambda c: c.state != 'destroyed'))
                message = _("✅ %d destroyed, %d remaining") % (destroyed_count, remaining)
            
            if failed_containers:
                message += "<br/><br/>⚠️ Failed:"
                for name, error in failed_containers:
                    message += "<br/>• %s: %s" % (name, error)
            
            self.message_post(body=message)
        else:
            raise UserError(_("All containers already destroyed or failed."))
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Destruction Complete'),
                'message': _('%d container(s) destroyed') % destroyed_count,
                'type': 'success',
                'sticky': False,
            }
        }

    def action_generate_certificate(self):
        """Generate certificate of destruction."""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_("Complete the work order first."))
        if self.certificate_id:
            raise UserError(_("Certificate already exists."))

        certificate = self.env['shredding.certificate'].create({
            'destruction_work_order_id': self.id,
            'partner_id': self.partner_id.id,
            'destruction_date': self.actual_destruction_date,
            'destruction_method': self.destruction_method,
            'technician_signature': self.technician_signature,
            'technician_signature_date': self.technician_signature_date,
            'technician_printed_name': self.technician_printed_name,
            'customer_signature': self.customer_signature,
            'customer_signature_date': self.customer_signature_date,
            'customer_printed_name': self.customer_printed_name,
            # Add witness information
            'witness_name': self.witness_name if self.witness_required else False,
            'witness_signature': self.witness_signature if self.witness_required else False,
            'witness_signature_date': self.witness_signature_date if self.witness_required else False,
        })
        self.write({'certificate_id': certificate.id})
        self.message_post(body=_("Certificate of Destruction %s generated.") % certificate.name)
        return {
            'type': 'ir.actions.act_window',
            'name': _('Certificate of Destruction'),
            'res_model': 'shredding.certificate',
            'res_id': certificate.id,
            'view_mode': 'form',
        }

    def action_cancel(self):
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Work order cancelled."))

    # ============================================================================
    # FSM TASK INTEGRATION
    # ============================================================================
    def action_create_fsm_task(self):
        """Create FSM task for container destruction work order."""
        self.ensure_one()
        if self.fsm_task_id:
            raise UserError(_("An FSM task already exists for this work order."))

        # Find or create FSM project
        fsm_project = self.env['project.project'].search([
            ('is_fsm', '=', True),
            ('company_id', '=', self.env.company.id)
        ], limit=1)

        if not fsm_project:
            fsm_project = self.env['project.project'].create({
                'name': _('Field Service - Container Destruction'),
                'is_fsm': True,
                'company_id': self.env.company.id,
            })

        # Create FSM task
        task_vals = {
            'name': _('Container Destruction: %s') % self.name,
            'project_id': fsm_project.id,
            'partner_id': self.partner_id.id,
            'is_fsm': True,
            'planned_date_begin': self.scheduled_destruction_date or fields.Datetime.now(),
            'user_ids': [(6, 0, [self.assigned_technician_id.id])] if self.assigned_technician_id else [],
            'description': _(
                '<p><strong>Container Destruction Work Order</strong></p>'
                '<ul>'
                '<li>Work Order: %s</li>'
                '<li>Customer: %s</li>'
                '<li>Containers: %d</li>'
                '<li>Method: %s</li>'
                '</ul>'
            ) % (
                self.name,
                self.partner_id.name,
                len(self.container_ids),
                dict(self._fields['destruction_method'].selection).get(self.destruction_method, '')
            ),
        }

        # Add destruction work order back-link if field exists
        if 'destruction_work_order_id' in self.env['project.task']._fields:
            task_vals['destruction_work_order_id'] = self.id

        fsm_task = self.env['project.task'].create(task_vals)
        self.fsm_task_id = fsm_task.id
        self.message_post(body=_("FSM Task %s created for field service scheduling.") % fsm_task.name)

        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task'),
            'res_model': 'project.task',
            'res_id': fsm_task.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_open_fsm_task(self):
        """Open the linked FSM task."""
        self.ensure_one()
        if not self.fsm_task_id:
            raise UserError(_("No FSM task linked to this work order."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('FSM Task'),
            'res_model': 'project.task',
            'res_id': self.fsm_task_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('container.destruction.work.order') or _('New')
        
        records = super().create(vals_list)
        
        # Approve portal requests when linked during creation
        for record in records:
            if record.portal_request_id and record.portal_request_id.state in ['draft', 'submitted', 'pending']:
                record.portal_request_id.write({
                    'state': 'approved',
                    'work_order_id': record.id,
                })
                record.portal_request_id.message_post(
                    body=_("Request approved and linked to Destruction Work Order: %s") % record.name
                )
        
        return records

    def write(self, vals):
        # Track if portal_request_id is being set
        portal_request_to_approve = False
        if 'portal_request_id' in vals and vals['portal_request_id']:
            portal_request_to_approve = self.env['portal.request'].browse(vals['portal_request_id'])
        
        result = super().write(vals)
        
        # Approve portal request when linked to work order
        if portal_request_to_approve and portal_request_to_approve.state in ['draft', 'submitted', 'pending']:
            portal_request_to_approve.write({
                'state': 'approved',
                'work_order_id': self.id if len(self) == 1 else False,
            })
            portal_request_to_approve.message_post(
                body=_("Request approved and linked to Destruction Work Order: %s") % self.name
            )
        
        return result
