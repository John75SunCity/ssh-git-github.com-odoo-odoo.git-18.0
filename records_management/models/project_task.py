import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    # FSM Partner Integration
    partner_id = fields.Many2one('res.partner', string='Customer', tracking=True, index=True)

    # Service Item Reference
    service_item_id = fields.Many2one('service.item', string='Service Item', index=True)

    # Shred Bin Reference
    shred_bin_id = fields.Many2one('shred.bin', string='Shred Bin', index=True)

    work_order_type = fields.Selection([
        ('pickup', 'Pickup'),
        ('retrieval', 'Retrieval'),
        ('destruction', 'Destruction'),
        ('internal', 'Internal Move'),
        ('other', 'Other'),
    ], string="Work Order Type", tracking=True)

    work_order_reference = fields.Reference(
        selection=[('portal.request', 'Portal Request')],
        string="Originating Request",
        readonly=True
    )

    container_ids = fields.Many2many('records.container', string="Related Containers")

    # --- Team Assignment ---
    shredding_team_id = fields.Many2one(
        'shredding.team',
        string="Shredding Team",
        help="The shredding team assigned to this task"
    )

    # Coordinator inverse for work.order.coordinator.fsm_task_ids
    coordinator_id = fields.Many2one(
        comodel_name='work.order.coordinator',
        string='Coordinator',
        index=True,
        help="Work Order Coordinator linked to this FSM task."
    )

    # --- Scheduling ---
    scheduled_start_time = fields.Datetime(string="Scheduled Start")
    scheduled_end_time = fields.Datetime(string="Scheduled End")
    actual_start_time = fields.Datetime(string="Actual Start", readonly=True)
    actual_end_time = fields.Datetime(string="Actual End", readonly=True)

    # --- Route & Vehicle ---
    route_id = fields.Many2one('fsm.route', string="Route")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    # --- Compliance & Audit ---
    naid_audit_log_ids = fields.One2many('naid.audit.log', 'task_id', string='Audit Logs')
    retention_policy_id = fields.Many2one('records.retention.policy', string='Retention Policy', index=True)  # Add index for search optimization
    certificate_required = fields.Boolean(string="Certificate Required", compute='_compute_certificate_required', store=True)
    certificate_of_destruction_id = fields.Many2one('ir.attachment', string="Certificate of Destruction", readonly=True)

    # Optimized computed field
    total_weight = fields.Float(string='Total Weight', compute='_compute_total_weight', store=True)  # Store for performance

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('timesheet_ids.hours_planned')  # Optimize dependencies
    def _compute_total_weight(self):
        for task in self:
            task.total_weight = sum(task.timesheet_ids.mapped('hours_planned'))  # Efficient sum

    @api.depends('work_order_type')
    def _compute_certificate_required(self):
        """Determine if a completion certificate is required based on the task type."""
        for task in self:
            task.certificate_required = task.work_order_type == 'destruction'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_task(self):
        """Start the task execution and log the event."""
        self.ensure_one()
        if self.stage_id.is_closed:
            raise UserError(_("Cannot start a task that is already in a closed stage."))
        self.write({
            'actual_start_time': fields.Datetime.now(),
        })
        self._create_audit_log('task_started', _("Task execution started."))
        self.message_post(body=_("Task started."))

    def action_complete_task(self):
        """Complete the task, log the event, and generate certificates if needed."""
        self.ensure_one()
        self.write({
            'actual_end_time': fields.Datetime.now(),
        })
        self._create_audit_log('task_completed', _("Task execution completed."))
        self.message_post(body=_("Task completed."))

        if self.certificate_required:
            self._generate_completion_certificate()

    def action_complete_destruction(self):
        """Complete destruction task with NAID compliance logging."""
        self.ensure_one()
        self.write({'state': 'done'})
        self.env['naid.audit.log'].create({'task_id': self.id, 'action': 'destruction_completed'})

    def action_view_related_containers(self):
        """Action to open the related containers' tree view."""
        self.ensure_one()
        if not self.container_ids:
            raise UserError(_("No containers are associated with this task."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Containers"),
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [('id', 'in', self.container_ids.ids)],
            "target": "current",
        }

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _create_audit_log(self, event_type, description):
        """Create a NAID audit log entry if the task is NAID compliant."""
        if not self.naid_compliant:
            return

        try:
            self.env['naid.audit.log'].create({
                'event_type': event_type,
                'description': description,
                'user_id': self.env.user.id,
                'task_id': self.id,
                'res_model': self._name,
                'res_id': self.id,
            })
        except Exception as e:
            _logger.error("Failed to create NAID audit log for task %s: %s", self.name, e)

    def _generate_completion_certificate(self):
        """Generate and attach a Certificate of Destruction."""
        self.ensure_one()
        report_action = self.env.ref('records_management.action_report_certificate_of_destruction')
        pdf_content, _ = report_action._render_qweb_pdf(res_ids=self.ids)
        attachment = self.env['ir.attachment'].create({
            'name': _("Certificate-of-Destruction-") + self.name + ".pdf",
            'type': 'binary',
            'datas': base64.encodebytes(pdf_content),
            'store_fname': fields.Datetime.now().strftime('certificate_%Y%m%d_%H%M%S.pdf'),
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf'
        })
        self.certificate_of_destruction_id = attachment.id
        self.message_post(
            body=_("Certificate of Destruction generated."),
            attachment_ids=[attachment.id]
        )

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to add initial audit log."""
        tasks = super().create(vals_list)
        for task in tasks:
            if task.naid_compliant:
                description = _('Task created: ') + task.name
                task._create_audit_log('task_created', description)
        return tasks

    def write(self, vals):
        """Override write to track important changes like stage or user assignment."""
        if 'stage_id' in vals:
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if task.naid_compliant:
                    description = _('Stage changed to: ') + stage.name
                    task._create_audit_log('stage_change', description)

        if 'user_ids' in vals:
            for task in self:
                if task.naid_compliant:
                    task._create_audit_log('assignment_change', _("User assignment updated."))

        return super().write(vals)

    def unlink(self):
        """Prevent deletion of tasks with audit trails."""
        for task in self:
            if task.audit_trail_ids:
                raise UserError(_("Cannot delete a task with NAID audit trail entries. Please archive it instead."))
        return super().unlink()


