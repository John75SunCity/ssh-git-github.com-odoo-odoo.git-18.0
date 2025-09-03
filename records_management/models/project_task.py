import base64
import logging

from odoo import api, fields, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

class ProjectTask(models.Model):
    """
    Extends the `project.task` model to integrate Records Management functionality.

    This model adds fields and methods to support features such as:
    - FSM partner integration
    - Shredding services and compliance tracking
    - Scheduling, routing, and vehicle assignment
    - NAID AAA compliance with audit logging
    - Certificate of Destruction generation
    """

    _inherit = 'project.task'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
    # FSM Partner Integration
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', tracking=True, index=True)

    # Service Item Reference
    service_item_id = fields.Many2one(comodel_name='service.item', string='Service Item', index=True)

    # Shred Bin Reference
    shred_bin_id = fields.Many2one(comodel_name='shred.bin', string='Shred Bin', index=True)

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

    # --- Team Assignment ---
    shredding_team_id = fields.Many2one(
        comodel_name='shredding.team',
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
    route_id = fields.Many2one(comodel_name='pickup.route', string="Pickup Route")
    vehicle_id = fields.Many2one(comodel_name='fleet.vehicle', string="Vehicle")

    # Container relationship - Many2many field
    container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='project_task_records_container_rel',
        column1='task_id',
        column2='container_id',
        string="Related Containers",
        help="Containers associated with this task"
    )

    # --- Compliance & Audit ---
    naid_audit_log_ids = fields.One2many(comodel_name='naid.audit.log', inverse_name='task_id', string='Audit Logs')
    retention_policy_id = fields.Many2one(comodel_name='records.retention.policy', string='Retention Policy', index=True)
    naid_compliant = fields.Boolean(string="NAID Compliant", default=False, help="Enable NAID AAA compliance tracking for this task")
    certificate_required = fields.Boolean(string="Certificate Required", compute='_compute_certificate_required', store=True)
    certificate_of_destruction_id = fields.Many2one(comodel_name='ir.attachment', string="Certificate of Destruction", readonly=True)

    # Optimized computed fields
    total_weight = fields.Float(string='Total Weight', compute='_compute_total_weight', store=True)
    container_count = fields.Integer(string='Container Count', compute='_compute_container_count', store=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_ids', 'container_ids.container_type_id', 'container_ids.container_type_id.average_weight_lbs')
    def _compute_total_weight(self):
        """
        Compute the total estimated weight of containers associated with the task.

        The weight is calculated based on the average weight of each container type.
        Ensures safe dependency handling for container type definitions.
        """
        for task in self:
            # Safe computation of estimated weight using container type definitions
            estimated_weight = 0.0
            for container in task.container_ids:
                if (hasattr(container, 'container_type_id') and
                    container.container_type_id and
                    hasattr(container.container_type_id, 'average_weight_lbs') and
                    container.container_type_id.average_weight_lbs):
                    estimated_weight += container.container_type_id.average_weight_lbs
            task.total_weight = estimated_weight

    @api.depends('container_ids')
    def _compute_container_count(self):
        """
        Compute the total number of containers associated with the task.
        """
        for task in self:
            task.container_count = len(task.container_ids)

    @api.depends('work_order_type')
    def _compute_certificate_required(self):
        """
        Determine if a Certificate of Destruction is required for the task.

        The certificate is required only for tasks of type 'destruction'.
        """
        for task in self:
            task.certificate_required = task.work_order_type == 'destruction'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_start_task(self):
        """
        Start the task execution.

        Logs the event, updates the actual start time, and posts a message.
        Raises:
            UserError: If the task is already in a closed stage.
        """
        self.ensure_one()
        if self.stage_id.is_closed:
            raise UserError(_("Cannot start a task that is already in a closed stage."))
        self.write({
            'actual_start_time': fields.Datetime.now(),
        })
        self._create_audit_log('task_started', _("Task execution started."))
        self.message_post(body=_("Task started."))

    def action_complete_task(self):
        """
        Complete the task execution.

        Logs the event, updates the actual end time, and generates a Certificate
        of Destruction if required. Posts a completion message.
        """
        self.ensure_one()
        self.write({
            'actual_end_time': fields.Datetime.now(),
        })
        self._create_audit_log('task_completed', _("Task execution completed."))
        self.message_post(body=_("Task completed."))

        if self.certificate_required:
            self._generate_completion_certificate()

    def action_complete_destruction(self):
        """
        Mark the destruction task as completed with NAID compliance logging.

        Creates an audit log entry for the destruction completion.
        """
        self.ensure_one()
        if hasattr(self, 'state'):
            self.write({'state': 'done'})
        self.env['naid.audit.log'].create({'task_id': self.id, 'action': 'destruction_completed'})

    def action_view_related_containers(self):
        """
        Open the tree view of containers related to the task.

        Raises:
            UserError: If no containers are associated with the task.
        Returns:
            dict: An action to open the related containers' tree view.
        """
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
        """
        Create a NAID audit log entry for the task.

        Logs events such as task creation, stage changes, and user assignments.
        Skips logging if the task is not NAID compliant.

        Args:
            event_type (str): The type of event being logged.
            description (str): A description of the event.
        """
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
        """
        Generate and attach a Certificate of Destruction to the task.

        The certificate is generated as a PDF and attached to the task record.
        Posts a message with the certificate attachment.
        """
        self.ensure_one()
        try:
            report_action = self.env.ref('records_management.action_report_certificate_of_destruction')
            pdf_content, _ = report_action._render_qweb_pdf(res_ids=self.ids)

            certificate_name = _("Certificate-of-Destruction-%s.pdf", self.name)
            attachment = self.env['ir.attachment'].create({
                'name': certificate_name,
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
        except Exception as e:
            _logger.error("Failed to generate certificate for task %s: %s", self.name, e)
            raise UserError(_("Failed to generate Certificate of Destruction: %s", str(e)))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """
        Override the create method to add an initial audit log for NAID-compliant tasks.

        Args:
            vals_list (list): A list of dictionaries containing the values for the new records.

        Returns:
            recordset: The created task records.
        """
        tasks = super().create(vals_list)
        for task in tasks:
            if task.naid_compliant:
                description = _('Task created: %s', task.name)
                task._create_audit_log('task_created', description)
        return tasks

    def write(self, vals):
        """
        Override the write method to track changes to important fields.

        Logs events such as stage changes and user assignments for NAID-compliant tasks.

        Args:
            vals (dict): A dictionary of field values to update.

        Returns:
            bool: True if the write operation is successful.
        """
        if 'stage_id' in vals:
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if task.naid_compliant:
                    description = _('Stage changed to: %s', stage.name)
                    task._create_audit_log('stage_change', description)

        if 'user_ids' in vals:
            for task in self:
                if task.naid_compliant:
                    task._create_audit_log('assignment_change', _("User assignment updated."))

        return super().write(vals)

    def unlink(self):
        """
        Override the unlink method to prevent deletion of tasks with audit trails.

        Raises:
            UserError: If the task has associated NAID audit trail entries.
        Returns:
            bool: True if the unlink operation is successful.
        """
        for task in self:
            if task.naid_audit_log_ids:
                raise UserError(_("Cannot delete a task with NAID audit trail entries. Please archive it instead."))
        return super().unlink()


