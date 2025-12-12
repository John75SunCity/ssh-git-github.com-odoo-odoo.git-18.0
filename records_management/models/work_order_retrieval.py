from pytz import UTC  # third-party before Odoo imports
from odoo import _, api, fields, models  # ordered per guideline
from odoo.exceptions import ValidationError, UserError


class WorkOrderRetrieval(models.Model):
    _name = 'work.order.retrieval'
    _description = 'Work Order Retrieval'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'work.order.invoice.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Work Order', required=True, readonly=True, default=lambda self: "New")
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(default=10)

    # Partner and Customer Information
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    customer_id = fields.Many2one(comodel_name='res.partner', string='Related Customer', related='partner_id', store=True)
    department_id = fields.Many2one(
        comodel_name='records.department',
        string="Department",
        domain="[('partner_id', '=', partner_id)]",
        tracking=True,
        help="Optional department for service address and billing purposes"
    )
    customer_staging_location_id = fields.Many2one(
        comodel_name='customer.staging.location',
        string="Staging Location",
        domain="[('partner_id', '=', partner_id), '|', ('department_id', '=', department_id), ('department_id', '=', False)]",
        tracking=True,
        help="Customer's staging location from portal. Helps technicians find containers on-site."
    )
    portal_request_id = fields.Many2one(comodel_name='portal.request', string='Portal Request', ondelete='set null')

    # Assignment and Team
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    assigned_team_id = fields.Many2one(comodel_name='hr.department', string='Assigned Team')
    team_leader_id = fields.Many2one(comodel_name='res.users', string='Team Leader')
    technician_ids = fields.Many2many('res.users', 'work_order_retrieval_res_users_rel', 'work_order_id', 'user_id', string='Technicians')

    # Scheduling and Dates
    scheduled_date = fields.Datetime(string='Scheduled Start Date', tracking=True)
    start_date = fields.Datetime(string='Start Date')
    completion_date = fields.Datetime(string='Completion Date')
    estimated_duration = fields.Float(string='Estimated Duration (Hours)', help='Estimated time in hours')
    actual_duration = fields.Float(string='Actual Duration (Hours)', help='Actual time spent in hours')

    # Status and Priority
    # Simplified workflow: Scheduled → In Progress → Completed
    state = fields.Selection([
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='scheduled', tracking=True)

    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent'),
        ('3', 'Critical')
    ], string='Priority', default='0', tracking=True)

    urgency_reason = fields.Text(string='Urgency Reason')

    # Sale Order Integration (for native Odoo invoicing)
    sale_order_id = fields.Many2one(
        comodel_name='sale.order',
        string="Sales Order",
        help="Linked sales order for native Odoo invoicing",
        tracking=True,
        copy=False
    )

    # Work Order Details
    work_order_type = fields.Selection([
        ('document_retrieval', 'Document Retrieval'),
        ('box_retrieval', 'Box Retrieval'),
        ('bulk_retrieval', 'Bulk Retrieval')
    ], string='Retrieval Type', default='document_retrieval')

    # Location and Access
    service_location_id = fields.Many2one(comodel_name='stock.location', string='Service Location')
    customer_address = fields.Text(string='Customer Address')
    access_instructions = fields.Text(string='Access Instructions')
    access_restrictions = fields.Text(string='Access Restrictions')
    contact_person = fields.Char(string='Contact Person')
    contact_phone = fields.Char(string='Contact Phone')

    # Equipment and Vehicle
    equipment_ids = fields.Many2many('maintenance.equipment', 'work_order_retrieval_equipment_rel', 'work_order_id', 'equipment_id', string='Equipment Required')
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string='Vehicle')

    # Items to Retrieve
    item_count = fields.Integer(string='Number of Items', default=1)
    item_descriptions = fields.Text(string='Item Descriptions')
    special_instructions = fields.Text(string='Special Instructions')

    # Completion and Quality
    completion_notes = fields.Text(string='Completion Notes')
    customer_signature = fields.Binary(string='Customer Signature')
    customer_satisfaction = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied')
    ], string='Customer Satisfaction')

    quality_check_passed = fields.Boolean(string='Quality Check Passed', default=True)
    supervisor_approval = fields.Boolean(string='Supervisor Approval')

    # Financial
    estimated_cost = fields.Monetary(string="Estimated Cost", currency_field="currency_id")
    actual_cost = fields.Monetary(string="Actual Cost", currency_field="currency_id")
    # currency_id provided by work.order.invoice.mixin
    # billable provided by work.order.invoice.mixin

    # Retrieval-specific fields
    retrieval_date = fields.Date(string='Retrieval Date', tracking=True)
    assigned_technician_id = fields.Many2one(comodel_name='res.users', string='Assigned Technician')
    location_id = fields.Many2one(comodel_name='stock.location', string='Storage Location')
    pickup_address = fields.Text(string='Pickup Address')
    total_boxes = fields.Integer(string='Total Boxes', default=0)
    completed_boxes = fields.Integer(string='Completed Boxes', default=0)
    progress_percentage = fields.Float(string='Progress (%)', compute='_compute_progress', store=True)
    start_time = fields.Datetime(string='Start Time')
    completion_time = fields.Datetime(string='Completion Time')
    equipment_needed = fields.Text(string='Equipment Needed')
    access_requirements = fields.Text(string='Access Requirements')
    safety_notes = fields.Text(string='Safety Notes')
    retrieval_item_ids = fields.One2many(comodel_name='retrieval.item.line', inverse_name='work_order_id', string='Items to Retrieve')
    attachment_ids = fields.Many2many(comodel_name='ir.attachment', string='Attachments')
    technician_signature = fields.Binary(string='Technician Signature')

    # Portal visibility
    portal_visible = fields.Boolean(
        string='Visible in Portal',
        default=True,
        help='If checked, this work order will be visible to the customer in their portal'
    )

    # ============================================================================
    # FSM INTEGRATION - All services scheduled via FSM tasks
    # ============================================================================
    fsm_task_id = fields.Many2one(
        comodel_name='project.task',
        string="FSM Task",
        domain="[('is_fsm', '=', True)]",
        tracking=True,
        help="Field Service task for scheduling this retrieval work order."
    )
    fsm_task_state = fields.Char(
        related='fsm_task_id.stage_id.name',
        string="FSM Task Status",
        store=False,
        readonly=True
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('name', 'partner_id', 'work_order_type')
    def _compute_display_name(self):
        """Compute the display name for the work order based on its name, partner, and type."""
        for record in self:
            parts = [record.name or 'New']
            if record.partner_id:
                parts.append(f"({record.partner_id.name})")
            if record.work_order_type:
                type_label = dict(record._fields['work_order_type'].selection).get(record.work_order_type, '')
                parts.append(f"- {type_label}")
            record.display_name = ' '.join(parts)

    @api.depends('completed_boxes', 'total_boxes')
    def _compute_progress(self):
        """Compute progress percentage based on completed vs total boxes."""
        for record in self:
            if record.total_boxes > 0:
                record.progress_percentage = (record.completed_boxes / record.total_boxes) * 100
            else:
                record.progress_percentage = 0.0

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('start_date', 'completion_date')
    def _check_date_sequence(self):
        for record in self:
            if record.start_date and record.completion_date:
                if record.start_date > record.completion_date:
                    raise ValidationError(_("Start date cannot be after completion date."))

    @api.constrains('estimated_duration', 'actual_duration')
    def _check_duration_positive(self):
        for record in self:
            if record.estimated_duration is not None and record.estimated_duration < 0:
                raise ValidationError(_("Estimated duration cannot be negative."))
            if record.actual_duration is not None and record.actual_duration < 0:
                raise ValidationError(_("Actual duration cannot be negative."))

    @api.constrains('item_count')
    def _check_item_count_positive(self):
        for record in self:
            if record.item_count < 0:
                raise ValidationError(_("Item count cannot be negative."))

    # ============================================================================
    # CRUD METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.retrieval') or _('New')
        return super().create(vals_list)

    # ===================== CRUD / DISPLAY HELPERS =====================
    # Deprecated name_get in Odoo 19; rely on computed display_name

    # Replaces former _name_search (removed to follow _search_<field> convention)
    def _search_display_name(self, operator, value):
        """Domain generator for display_name searches (name / partner / portal / contact)."""
        if not value:
            return []
        return [
            '|', '|', '|',
            ('name', operator, value),
            ('partner_id.name', operator, value),
            ('portal_request_id.name', operator, value),
            ('contact_person', operator, value),
        ]

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_confirm(self):
        """Confirm the work order"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        self.state = 'confirmed'
        self.message_post(body=_("Work order confirmed."))

    def action_assign(self):
        """Assign the work order to a team"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can be assigned."))
        self.state = 'assigned'
        self.message_post(body=_("Work order assigned."))

    def action_start(self):
        """Start the work order"""
        self.ensure_one()
        if self.state != 'assigned':
            raise UserError(_("Only assigned work orders can be started."))
        self.state = 'in_progress'
        self.start_date = fields.Datetime.now()
        self.start_time = fields.Datetime.now()
        self.message_post(body=_("Work order started."))

    def action_start_retrieval(self):
        """Start retrieval - simplified workflow for technicians.
        
        Automatically moves through confirm/assign states if needed,
        so technicians can start directly from any pre-started state.
        """
        self.ensure_one()
        
        # Auto-progress through states if not already in_progress
        if self.state == 'draft':
            self.state = 'confirmed'
        if self.state == 'confirmed':
            # Auto-assign to current user if not assigned
            if not self.user_id:
                self.user_id = self.env.user
            self.state = 'assigned'
        if self.state == 'assigned':
            self.state = 'in_progress'
            self.start_date = fields.Datetime.now()
            self.start_time = fields.Datetime.now()
            self.message_post(body=_('Retrieval started by %s') % self.env.user.name)
        
        return True

    def action_complete(self):
        """Complete the work order"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_("Only in-progress work orders can be completed."))
        self.state = 'completed'
        self.completion_date = fields.Datetime.now()
        self.completion_time = fields.Datetime.now()
        if self.start_date:
            start_dt = fields.Datetime.from_string(self.start_date)
            completion_dt = fields.Datetime.from_string(self.completion_date)
            if start_dt.tzinfo is None:
                start_dt = UTC.localize(start_dt)
            else:
                start_dt = start_dt.astimezone(UTC)
            if completion_dt.tzinfo is None:
                completion_dt = UTC.localize(completion_dt)
            else:
                completion_dt = completion_dt.astimezone(UTC)
            self.actual_duration = (completion_dt - start_dt).total_seconds() / 3600.0
        self.message_post(body=_("Work order completed."))

    def action_complete_retrieval(self):
        """Complete retrieval - alias for action_complete"""
        return self.action_complete()

    def action_cancel(self):
        """Cancel the work order"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_("Completed work orders cannot be cancelled."))
        self.state = 'cancelled'
        self.message_post(body=_("Work order cancelled."))

    def action_cancel_retrieval(self):
        """Cancel retrieval - alias for action_cancel"""
        return self.action_cancel()

    def action_view_audit_logs(self):
        """View audit logs for this retrieval"""
        self.ensure_one()
        return {
            'name': _('Audit Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'naid.audit.log',
            'view_mode': 'list,form',
            'domain': [('work_order_retrieval_id', '=', self.id)],
            'context': {'default_work_order_retrieval_id': self.id},
        }

    def action_reset_to_draft(self):
        """Reset to draft state"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_("Completed work orders cannot be reset to draft."))
        self.state = 'draft'
        self.start_date = False
        self.completion_date = False
        self.actual_duration = 0.0
        self.message_post(body=_("Work order reset to draft."))

    # ============================================================================
    # FSM TASK INTEGRATION
    # ============================================================================
    def action_create_fsm_task(self):
        """Create FSM task for retrieval work order."""
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
                'name': _('Field Service - Retrieval'),
                'is_fsm': True,
                'company_id': self.env.company.id,
            })

        # Create FSM task
        task_vals = {
            'name': _('Retrieval: %s') % self.name,
            'project_id': fsm_project.id,
            'partner_id': self.partner_id.id,
            'is_fsm': True,
            'planned_date_begin': self.scheduled_date or fields.Datetime.now(),
            'user_ids': [(6, 0, [self.assigned_technician_id.id])] if self.assigned_technician_id else (
                [(6, 0, [self.user_id.id])] if self.user_id else []
            ),
            'description': _(
                '<p><strong>Retrieval Work Order</strong></p>'
                '<ul>'
                '<li>Work Order: %s</li>'
                '<li>Customer: %s</li>'
                '<li>Type: %s</li>'
                '<li>Total Boxes: %d</li>'
                '</ul>'
            ) % (
                self.name,
                self.partner_id.name,
                dict(self._fields['work_order_type'].selection).get(self.work_order_type, ''),
                self.total_boxes or 0
            ),
        }

        # Add retrieval work order back-link if field exists
        if 'retrieval_work_order_wo_id' in self.env['project.task']._fields:
            task_vals['retrieval_work_order_wo_id'] = self.id

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

    def action_open_picklist_scanner(self):
        """Open the barcode scanning interface for this work order's pick list (wizard popup)."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Scan Containers - %s') % self.name,
            'res_model': 'retrieval.scan.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_work_order_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
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

    def action_scan_barcode(self, barcode):
        """
        Alias for action_scan_container - required by the camera scanner.
        The camera scanner calls action_scan_barcode on the work order model.
        """
        return self.action_scan_container(barcode)

    def action_scan_container(self, barcode):
        """
        Process a scanned barcode during retrieval.
        Marks the corresponding item as retrieved if found in the pick list.
        """
        self.ensure_one()
        
        if self.state not in ('in_progress', 'assigned'):
            raise UserError(_("Work order must be in progress to scan containers."))
        
        # Find the container by barcode
        container = self.env['records.container'].search([
            '|',
            ('barcode', '=', barcode),
            ('temp_barcode', '=', barcode)
        ], limit=1)
        
        if not container:
            return {
                'success': False,
                'message': _('Container not found: %s') % barcode
            }
        
        # Check if container is in the pick list
        item_line = self.retrieval_item_ids.filtered(lambda l: l.box_id.id == container.id)
        
        if not item_line:
            return {
                'success': False,
                'message': _('Container %s is not on this pick list') % container.name
            }
        
        if item_line.retrieved:
            return {
                'success': False,
                'message': _('Container %s already scanned') % container.name
            }
        
        # Mark as retrieved
        item_line.write({
            'retrieved': True,
            'retrieval_time': fields.Datetime.now(),
        })
        
        # Update progress
        self.completed_boxes = len(self.retrieval_item_ids.filtered('retrieved'))
        
        # Log the scan
        self.message_post(body=_('Scanned container: %s at location %s') % (
            container.name,
            container.location_id.name if container.location_id else 'Unknown'
        ))
        
        return {
            'success': True,
            'message': _('✓ Container %s verified') % container.name,
            'container_name': container.name,
            'location': container.location_id.name if container.location_id else 'Unknown',
            'remaining': len(self.retrieval_item_ids.filtered(lambda l: not l.retrieved))
        }

    @api.model
    def get_priority_work_orders(self, limit=100):
        """Get high priority work orders requiring attention (limited for performance)"""
        return self.search([
            ('priority', 'in', ['2', '3']),
            ('state', 'in', ['confirmed', 'assigned', 'in_progress']),
        ], order='priority desc, scheduled_date asc', limit=limit)

    def bulk_confirm(self):  # multi-record helper (not an 'action_' single-record)
        """Bulk confirm selected work orders (utility method, not single-record action)."""
        for record in self:
            if record.state == 'draft':
                record.action_confirm()

    def bulk_start(self):  # multi-record helper (not an 'action_' single-record)
        """Bulk start selected work orders (utility method, not single-record action)."""
        for record in self:
            if record.state == 'assigned':
                record.action_start()

    # ============================================================================
    # INVOICE MIXIN OVERRIDES
    # ============================================================================
    def _get_default_product_name(self):
        """Return default product name for retrieval services"""
        return _('Records Retrieval Service')

    def _get_default_price(self):
        """Return default price for retrieval - based on boxes"""
        return 25.0  # Default $25 per retrieval

    def _get_service_type(self):
        """Return service type for invoice line tracking"""
        return 'retrieval'

    def _get_invoice_line_description(self):
        """Custom invoice line description for retrieval"""
        parts = [_('Records Retrieval Service')]
        parts.append(_('Work Order: %s') % self.name)
        if self.partner_id:
            parts.append(_('Customer: %s') % self.partner_id.name)
        if self.total_boxes:
            parts.append(_('Boxes Retrieved: %d') % self.total_boxes)
        if self.scheduled_date:
            parts.append(_('Date: %s') % self.scheduled_date.strftime('%Y-%m-%d'))
        return '\n'.join(parts)

    def _prepare_invoice_line_values(self, invoice):
        """Override to add retrieval-specific data"""
        values = super()._prepare_invoice_line_values(invoice)
        
        # Use total_boxes as quantity if set
        if self.total_boxes:
            values['quantity'] = self.total_boxes
        
        # Add container tracking
        if self.retrieval_item_ids:
            container_ids = self.retrieval_item_ids.mapped('box_id').ids
            if container_ids:
                values['container_ids'] = [(6, 0, container_ids)]
                values['container_count'] = len(container_ids)
        
        return values
