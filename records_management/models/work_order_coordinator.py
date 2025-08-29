
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderCoordinator(models.Model):
    _name = 'work.order.coordinator'
    _description = 'Work Order Coordinator'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Coordination Reference", required=True, copy=False, readonly=True,
                        default=lambda self: _('New'))
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    portal_request_id = fields.Many2one('portal.request', string="Portal Request", ondelete='set null')

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('billed', 'Billed'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='draft', tracking=True)

    scheduled_date = fields.Datetime(string="Scheduled Start Date", tracking=True)
    priority = fields.Selection([
        ('0', 'Normal'),
        ('1', 'High'),
        ('2', 'Urgent')
    ], string="Priority", default='0')

    # Linked Work Orders
    container_retrieval_ids = fields.One2many('container.retrieval.work.order', 'coordinator_id', string="Container Retrievals")
    file_retrieval_ids = fields.One2many('file.retrieval.work.order', 'coordinator_id', string="File Retrievals")
    scan_retrieval_ids = fields.One2many('scan.retrieval.work.order', 'coordinator_id', string="Scan Retrievals")
    destruction_ids = fields.One2many('records.destruction', 'coordinator_id', string="Destruction Orders")

    # Coordination Metrics
    total_work_orders = fields.Integer(string="Total Work Orders", compute='_compute_coordination_metrics', store=True)
    completed_work_orders = fields.Integer(string="Completed Work Orders", compute='_compute_coordination_metrics', store=True)
    coordination_progress = fields.Float(string="Progress (%)", compute='_compute_coordination_metrics', store=True, aggregator="avg")

    # Resource Allocation
    employee_ids = fields.Many2many(
        'hr.employee',
        relation='work_order_coordinator_employee_rel',
        column1='coordinator_id',
        column2='employee_id',
        string="Assigned Employees"
    )
    vehicle_ids = fields.Many2many(
        'fleet.vehicle',
        relation='work_order_coordinator_vehicle_rel',
        column1='coordinator_id',
        column2='vehicle_id',
        string="Assigned Vehicles"
    )
    assigned_equipment_ids = fields.Many2many(
        'maintenance.equipment',
        relation='work_order_coordinator_equipment_rel',
        column1='coordinator_id',
        column2='equipment_id',
        string="Assigned Equipment"
    )

    # FSM Integration
    fsm_project_id = fields.Many2one('project.project', string="FSM Project", help="Project for managing Field Service tasks related to this coordination.")
    fsm_task_ids = fields.One2many('project.task', 'coordinator_id', string="FSM Tasks")

    # Billing
    consolidated_billing = fields.Boolean(string="Consolidated Billing", default=True)
    invoice_id = fields.Many2one('account.move', string="Consolidated Invoice", readonly=True, copy=False)

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_retrieval_ids.state', 'file_retrieval_ids.state', 'scan_retrieval_ids.state', 'destruction_ids.state')
    def _compute_coordination_metrics(self):
        for record in self:
            all_orders = record._get_all_work_orders()
            record.total_work_orders = len(all_orders)

            completed = all_orders.filtered(lambda wo: wo.state in ['completed', 'closed', 'done'])
            record.completed_work_orders = len(completed)

            if record.total_work_orders > 0:
                record.coordination_progress = (record.completed_work_orders / record.total_work_orders) * 100.0
            else:
                record.coordination_progress = 0.0

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('work.order.coordinator') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_coordinate_all(self):
        """Assigns shared resources to all linked work orders."""
        self.ensure_one()
        all_orders = self._get_all_work_orders()
        if not all_orders:
            raise UserError(_("There are no work orders to coordinate."))

        for order in all_orders:
            order_vals = {}
            if hasattr(order, 'coordinator_id'):
                order_vals['coordinator_id'] = self.id
            if hasattr(order, 'vehicle_ids') and self.vehicle_ids:
                order_vals['vehicle_ids'] = [(6, 0, self.vehicle_ids.ids)]
            if hasattr(order, 'employee_ids') and self.employee_ids:
                order_vals['employee_ids'] = [(6, 0, self.employee_ids.ids)]
            if order_vals:
                order.write(order_vals)

        self.write({'state': 'in_progress'})
        self.message_post(body=_("Coordination started for %s work orders.") % len(all_orders))

    def action_create_fsm_tasks(self):
        """Creates FSM tasks for all linked work orders."""
        self.ensure_one()
        if not self.fsm_project_id:
            project_vals = {
                'name': _("Records Management - %s") % self.partner_id.name,
                'is_fsm': True,
                'partner_id': self.partner_id.id,
                'allow_timesheets': True,
            }
            self.fsm_project_id = self.env['project.project'].create(project_vals)

        task_count = 0
        for order in self._get_all_work_orders():
            if hasattr(order, 'create_fsm_task'):
                order.create_fsm_task(self.fsm_project_id.id)
                task_count += 1

        self.message_post(body=_("Created %s FSM tasks for coordinated work orders.") % task_count)

    def action_consolidate_billing(self):
        """Creates a single consolidated invoice for all billable work orders."""
        self.ensure_one()
        if not self.consolidated_billing:
            raise UserError(_("Consolidated billing is not enabled for this coordination."))
        if self.invoice_id:
            raise UserError(_("A consolidated invoice already exists: %s") % self.invoice_id.name)

        invoice_lines = []
        for order in self._get_all_work_orders():
            if hasattr(order, '_prepare_invoice_line_vals'):
                invoice_lines.extend(order._prepare_invoice_line_vals())

        if not invoice_lines:
            raise UserError(_("There are no billable items to invoice."))

        invoice_vals = {
            'partner_id': self.partner_id.id,
            'move_type': 'out_invoice',
            'invoice_date': fields.Date.today(),
            'ref': self.name,
            'invoice_line_ids': invoice_lines,
        }
        invoice = self.env['account.move'].create(invoice_vals)
        self.write({'invoice_id': invoice.id, 'state': 'billed'})
        self.message_post(body=_("Consolidated invoice %s created with %s lines.") % (invoice.name, len(invoice_lines)))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Consolidated Invoice'),
            'res_model': 'account.move',
            'res_id': invoice.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def _get_all_work_orders(self):
        """Utility method to get a single recordset of all linked work orders."""
        self.ensure_one()
        # This approach correctly combines different models into a list of records
        # Note: The resulting list contains browse records of different models.
        all_orders = []
        all_orders.extend(self.container_retrieval_ids)
        all_orders.extend(self.file_retrieval_ids)
        all_orders.extend(self.scan_retrieval_ids)
        all_orders.extend(self.destruction_ids)
        return self.env[next(iter(all_orders), self.env['mail.thread'])].union(*all_orders) if all_orders else self.env['mail.thread']

