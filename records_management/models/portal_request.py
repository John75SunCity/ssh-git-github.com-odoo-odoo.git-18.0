# Updated file: Added @api.model_create_multi decorator to override create in batch mode (fixes deprecation warning in log for non-batch create). This accomplishes efficient multi-record creation (e.g., batch requests from portal submissions), aligning with Odoo 18.0 performance best practices. Clean/simple: Minimal change, preserves existing logic. User-friendly: No UI impact, but faster for large ops. Innovative idea: Extend with AI request prioritization (use torch to score urgency from description sentiment); standards: NAID AAA verifiable workflows (batch signing ensures compliant bulk destruction requests).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.sign.models.sign_request import SignRequest  # Explicit import for integration

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Removed 'sign.mixin' - invalid/non-existent
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', default='New', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")  # Added for granular requests
    request_type = fields.Selection([
        ('destruction', 'Destruction Request'),
        ('service', 'Service Request'),
        ('inventory_checkout', 'Inventory Checkout'),
        ('billing_update', 'Billing Update'),
        ('quote_generate', 'Quote Generation'),
    ], string='Request Type', required=True)
    description = fields.Html(string='Description')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='draft', tracking=True)
    sign_request_id = fields.Many2one('sign.request', string='Signature Request')  # For admin/requestor signatures
    requestor_signature_date = fields.Datetime(string='Requestor Signature Date')
    admin_signature_date = fields.Datetime(string='Admin Signature Date')
    audit_log = fields.Html(string='Audit Trail', readonly=True)  # Auto-populated log
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')  # Link to FSM for field actions
    invoice_id = fields.Many2one('account.move', string='Related Invoice')  # For billing updates
    temp_inventory_ids = fields.Many2many('temp.inventory', string='Temporary Inventory Items')  # For new inventory additions

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            rec.name = self.env['ir.sequence'].next_by_code('portal.request')
            rec._generate_signature_request()
            rec._append_audit_log(_('Request created by %s.', rec.partner_id.name))
        return records

    def action_submit(self):
        self.write({'state': 'submitted'})
        if not self.sign_request_id.is_signed:
            raise ValidationError(_("Signatures required before submission."))
        if self.request_type == 'destruction' and not (self.requestor_signature_date and self.admin_signature_date):
            raise ValidationError(_("Dual signatures required for destruction requests per NAID AAA."))
        if self._is_field_request():
            self._create_fsm_task()
        self._send_notification()
        self._append_audit_log(_('Submitted on %s.', fields.Datetime.now()))

    def action_approve(self):
        self.ensure_one()
        if self.request_type == 'billing_update' and self._is_sensitive_change():
            # Approval for rates/quantity - update internal records
            self.invoice_id.write({'ref': self.description})  # Example PO update
        self.state = 'approved'
        self._append_audit_log(_('Approved by admin on %s.', fields.Datetime.now()))

    def action_reject(self):
        self.state = 'rejected'
        self._append_audit_log(_('Rejected by admin on %s.', fields.Datetime.now()))

    def _generate_signature_request(self):
        template = self.env.ref('records_management.sign_template_portal_request')  # Assume template with 2 roles: requestor/admin
        if not template:
            raise ValidationError(_("Signature template missing. Configure in Sign app."))
        sign_request = self.env['sign.request'].create({
            'template_id': template.id,
            'reference': self.name,
            'request_item_ids': [(0, 0, {
                'role_id': self.env.ref('sign.sign_item_role_requestor').id,  # Use standard roles or custom
                'partner_id': self.partner_id.id,
            }), (0, 0, {
                'role_id': self.env.ref('sign.sign_item_role_admin').id,
                'partner_id': self.env.company.partner_id.id,  # Admin as company
            })],
        })
        sign_request.action_draft()  # Prepare for signing
        self.sign_request_id = sign_request

    @api.depends('sign_request_id.state')
    def _check_signatures(self):
        for rec in self:
            if rec.sign_request_id:
                items = rec.sign_request_id.request_item_ids
                requestor_item = items.filtered(lambda i: i.role_id.name == 'Requestor')
                admin_item = items.filtered(lambda i: i.role_id.name == 'Admin')
                rec.requestor_signature_date = requestor_item.signing_date if requestor_item.is_signed else False
                rec.admin_signature_date = admin_item.signing_date if admin_item.is_signed else False

    def _create_fsm_task(self):
        task = self.env['project.task'].create({
            'name': f'FSM for {self.name}',
            'partner_id': self.partner_id.id,
            'description': self.description,
            'project_id': self.env.ref('industry_fsm.fsm_project').id,  # Assume FSM project
        })
        self.fsm_task_id = task
        return task

    def _send_notification(self):
        # Email
        template = self.env.ref('records_management.portal_request_submitted_email')
        template.send_mail(self.id, force_send=True)
        # SMS if phone
        if self.partner_id.mobile:
            self.env['sms.sms'].create({
                'number': self.partner_id.mobile,
                'body': _('New portal request submitted: %s.', self.name),
            }).send()

    def _append_audit_log(self, message):
        self.audit_log += f'<p>{fields.Datetime.now()}: {message}</p>'

    def _is_sensitive_change(self):
        # Logic to detect rate/quantity changes in description
        return 'rate' in self.description.lower() or 'quantity' in self.description.lower()

    def _is_field_request(self):
        return self.request_type in ('destruction', 'service', 'inventory_checkout')
