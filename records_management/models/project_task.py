from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ProjectTask(models.Model):
    _inherit = 'project.task'

    # ============================================================================
    # RECORDS MANAGEMENT FIELDS
    # ============================================================================
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

    # --- Scheduling ---
    scheduled_start_time = fields.Datetime(string="Scheduled Start")
    scheduled_end_time = fields.Datetime(string="Scheduled End")
    actual_start_time = fields.Datetime(string="Actual Start", readonly=True)
    actual_end_time = fields.Datetime(string="Actual End", readonly=True)

    # --- Route & Vehicle ---
    route_id = fields.Many2one('fsm.route', string="Route")
    vehicle_id = fields.Many2one('fleet.vehicle', string="Vehicle")

    # --- Compliance & Audit ---
    naid_compliant = fields.Boolean(string="NAID Compliant", related='route_id.is_naid_compliant', store=True)
    audit_trail_ids = fields.One2many('naid.audit.log', 'task_id', string="Audit Trail")
    certificate_required = fields.Boolean(string="Certificate Required", compute='_compute_certificate_required', store=True)
    certificate_of_destruction_id = fields.Many2one('ir.attachment', string="Certificate of Destruction", readonly=True)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('work_order_type')
    def _compute_certificate_required(self):
        """Determine if a completion certificate is required based on the task type."""
        for task in self:
            task.certificate_required = task.work_order_type in ['destruction']

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
        self.message_post(body=_("Task started by %s.", self.env.user.name))

    def action_complete_task(self):
        """Complete the task, log the event, and generate certificates if needed."""
        self.ensure_one()
        self.write({
            'actual_end_time': fields.Datetime.now(),
        })
        self._create_audit_log('task_completed', _("Task execution completed."))
        self.message_post(body=_("Task completed by %s.", self.env.user.name))

        if self.certificate_required:
            self._generate_completion_certificate()

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

        self.env['naid.audit.log'].create({
            'event_type': event_type,
            'description': description,
            'user_id': self.env.user.id,
            'task_id': self.id,
            'res_model': self._name,
            'res_id': self.id,
        })

    def _generate_completion_certificate(self):
        """Generate and attach a Certificate of Destruction."""
        self.ensure_one()
        # This would call a report action to generate the PDF
        # For simplicity, we'll create a log message and a placeholder attachment.
        report_action = self.env.ref('records_management.action_report_certificate_of_destruction')
        pdf_content, _file_type = report_action._render_qweb_pdf(self.ids)

        attachment = self.env['ir.attachment'].create({
            'name': _("Certificate-of-Destruction-%s.pdf", self.name),
            'type': 'binary',
            'datas': base64.b64encode(pdf_content),
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
        tasks = super(ProjectTask, self).create(vals_list)
        for task in tasks:
            if task.naid_compliant:
                task._create_audit_log('task_created', _("Task created: %s", task.name))
        return tasks

    def write(self, vals):
        """Override write to track important changes like stage or user assignment."""
        if 'stage_id' in vals:
            stage = self.env['project.task.type'].browse(vals['stage_id'])
            for task in self:
                if task.naid_compliant:
                    task._create_audit_log('stage_change', _("Stage changed to: %s", stage.name))

        if 'user_ids' in vals:
            for task in self:
                if task.naid_compliant:
                    task._create_audit_log('assignment_change', _("User assignment updated."))

        return super(ProjectTask, self).write(vals)

    def unlink(self):
        """Prevent deletion of tasks with audit trails."""
        for task in self:
            if task.audit_trail_ids:
                raise UserError(_("Cannot delete a task with NAID audit trail entries. Please archive it instead."))



