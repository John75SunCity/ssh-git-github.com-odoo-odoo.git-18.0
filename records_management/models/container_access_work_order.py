from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class ContainerAccessWorkOrder(models.Model):
    _name = 'container.access.work.order'
    _description = 'Container Access Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_access_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    state = fields.Selection()
    priority = fields.Selection()
    partner_id = fields.Many2one()
    portal_request_id = fields.Many2one()
    requestor_name = fields.Char()
    requestor_title = fields.Char()
    access_purpose = fields.Text()
    access_type = fields.Selection()
    access_scope = fields.Selection()
    container_ids = fields.Many2many()
    container_count = fields.Integer()
    access_location_id = fields.Many2one()
    scheduled_access_date = fields.Datetime()
    scheduled_duration_hours = fields.Float()
    scheduled_end_time = fields.Datetime()
    actual_start_time = fields.Datetime()
    actual_end_time = fields.Datetime()
    actual_duration_hours = fields.Float()
    requires_escort = fields.Boolean()
    escort_employee_id = fields.Many2one()
    requires_key_access = fields.Boolean()
    bin_key_ids = fields.Many2many()
    visitor_ids = fields.One2many()
    max_visitors = fields.Integer()
    access_activity_ids = fields.One2many()
    items_accessed_count = fields.Integer()
    items_modified_count = fields.Integer()
    photo_documentation = fields.Boolean()
    video_monitoring = fields.Boolean()
    witness_required = fields.Boolean()
    witness_name = fields.Char()
    chain_of_custody_maintained = fields.Boolean()
    audit_trail_complete = fields.Boolean()
    compliance_notes = fields.Text()
    session_summary = fields.Text()
    findings = fields.Text()
    follow_up_required = fields.Boolean()
    follow_up_notes = fields.Text()
    activity_ids = fields.One2many('mail.activity')
    message_follower_ids = fields.One2many('mail.followers')
    message_ids = fields.One2many('mail.message')
    coordinator_id = fields.Many2one('work.order.coordinator')
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def create(self, vals_list):
            for vals in vals_list:
                if vals.get('name', _('New')) == _('New'):
                    vals['name') = self.env['ir.sequence'].next_by_code()
                        'container.access.work.order') or _('New'
            return super().create(vals_list)

        # ============================================================================
            # COMPUTE METHODS
        # ============================================================================

    def _compute_display_name(self):
            for record in self:
                if record.partner_id and record.container_count:
                    access_type_display = dict(record._fields['access_type'].selection).get(record.access_type, record.access_type)
                    record.display_name = _("%s - %s (%s containers - %s)",
                        record.name, record.partner_id.name, record.container_count, access_type_display
                elif record.partner_id:
                    record.display_name = _("%s - %s", record.name, record.partner_id.name)
                else:
                    record.display_name = record.name or _("New Container Access")


    def _compute_container_metrics(self):
            for record in self:
                record.container_count = len(record.container_ids)


    def _compute_scheduled_end_time(self):
            for record in self:
                if record.scheduled_access_date and record.scheduled_duration_hours:
                    record.scheduled_end_time = record.scheduled_access_date + timedelta(hours=record.scheduled_duration_hours)
                else:
                    record.scheduled_end_time = False


    def _compute_actual_duration(self):
            for record in self:
                if record.actual_start_time and record.actual_end_time:
                    duration = record.actual_end_time - record.actual_start_time
                    record.actual_duration_hours = duration.total_seconds() / 3600
                else:
                    record.actual_duration_hours = 0.0


    def _compute_access_metrics(self):
            for record in self:
                activities = record.access_activity_ids
                record.items_accessed_count = len(activities)
                record.items_modified_count = len(activities.filtered('item_modified'))


    def _compute_audit_trail_complete(self):
            for record in self:
                # Check if all required documentation is complete:
                has_activities = len(record.access_activity_ids) > 0
                has_visitors = len(record.visitor_ids) > 0
                custody_maintained = record.chain_of_custody_maintained
                record.audit_trail_complete = has_activities and has_visitors and custody_maintained

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_submit(self):
            """Submit access request for approval""":
            self.ensure_one()
            if self.state != 'draft':
                raise UserError(_("Only draft requests can be submitted"))

            self.write({'state': 'submitted'})
            self.message_post()
                body=_("Container access request submitted for approval"),:
                message_type='notification'

            return True


    def action_approve(self):
            """Approve access request"""
            self.ensure_one()
            if self.state != 'submitted':
                raise UserError(_("Only submitted requests can be approved"))

            self.write({'state': 'approved'})
            self.message_post()
                body=_("Container access request approved"),
                message_type='notification'

            return True


    def action_schedule(self):
            """Schedule the access session"""
            self.ensure_one()
            if self.state != 'approved':
                raise UserError(_("Only approved requests can be scheduled"))

            self.write({'state': 'scheduled'})
            self.message_post()
                body=_("Access session scheduled for %s", self.scheduled_access_date.strftime('%Y-%m-%d %H:%M')),
                message_type='notification'

            return True


    def action_start_access(self):
            """Start the access session"""
            self.ensure_one()
            if self.state != 'scheduled':
                raise UserError(_("Only scheduled sessions can be started"))

            # Verify security requirements
            if self.requires_escort and not self.escort_employee_id:
                raise UserError(_("Security escort is required but not assigned"))

            if self.requires_key_access and not self.bin_key_ids:
                raise UserError(_("Key access is required but no keys are assigned"))

            self.write({)}
                'state': 'in_progress',
                'actual_start_time': fields.Datetime.now()

            self.message_post()
                body=_("Container access session started"),
                message_type='notification'

            return True


    def action_suspend_access(self):
            """Temporarily suspend access session"""
            self.ensure_one()
            if self.state != 'in_progress':
                raise UserError(_("Only active sessions can be suspended"))

            self.write({'state': 'suspended'})
            self.message_post()
                body=_("Access session suspended"),
                message_type='notification'

            return True


    def action_resume_access(self):
            """Resume suspended access session"""
            self.ensure_one()
            if self.state != 'suspended':
                raise UserError(_("Only suspended sessions can be resumed"))

            self.write({'state': 'in_progress'})
            self.message_post()
                body=_("Access session resumed"),
                message_type='notification'

            return True


    def action_complete_access(self):
            """Complete the access session"""
            self.ensure_one()
            if self.state not in ['in_progress', 'suspended']:
                raise UserError(_("Only active or suspended sessions can be completed"))

            self.write({)}
                'state': 'completed',
                'actual_end_time': fields.Datetime.now()

            self.message_post()
                body=_("Container access session completed"),
                message_type='notification'

            return True


    def action_document_session(self):
            """Mark session as fully documented"""
            self.ensure_one()
            if self.state != 'completed':
                raise UserError(_("Only completed sessions can be documented"))

            if not self.session_summary:
                raise UserError(_("Session summary is required before documentation"))

            self.write({'state': 'documented'})
            self.message_post()
                body=_("Access session documentation completed"),
                message_type='notification'

            return True


    def action_close(self):
            """Close the work order"""
            self.ensure_one()
            if self.state != 'documented':
                raise UserError(_("Only documented sessions can be closed"))

            self.write({'state': 'closed'})
            self.message_post()
                body=_("Container access work order closed successfully"),
                message_type='notification'

            return True

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def add_access_activity(self, container_id, activity_type, description, item_modified=False):
            """Add an access activity record"""
            self.ensure_one()
            return self.env['container.access.activity'].create({)}
                'work_order_id': self.id,
                'container_id': container_id,
                'activity_type': activity_type,
                'description': description,
                'item_modified': item_modified,
                'activity_time': fields.Datetime.now(),
                'user_id': self.env.user.id,



    def generate_access_report(self):
            """Generate container access report"""
            self.ensure_one()
            return {}
                'type': 'ir.actions.report',
                'report_name': 'records_management.report_container_access',
                'report_type': 'qweb-pdf',
                'res_id': self.id,
                'target': 'new',



    def _check_scheduling(self):
            for record in self:
                if record.scheduled_access_date and record.scheduled_duration_hours:
                    if record.scheduled_duration_hours <= 0:
                        raise ValidationError(_("Scheduled duration must be positive"))

                    if record.scheduled_duration_hours > 24:
                        raise ValidationError(_("Access sessions cannot exceed 24 hours"))
