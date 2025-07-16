# New file: Model for handling portal requests (e.g., destruction, service, billing updates). Ensures NAID AAA compliance with signatures, timestamps, audit trails. Generates FSM tasks for field services. Supports requests for rate/quantity changes (approval workflow).

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from odoo.addons.sign.models.sign_request import SignRequest

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'sign.mixin']  # Inherit sign for signatures
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', default='New', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
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
    
    @api.model
    def create(self, vals):
        res = super().create(vals)
        res.name = self.env['ir.sequence'].next_by_code('portal.request')
        res._generate_signature_request()
        res._append_audit_log(_('Request created by %s.', res.partner_id.name))
        return res

    def action_submit(self):
        self.write({'state': 'submitted'})
        if self._signatures_complete():
            if not self.sign_request_id.is_signed:
                raise ValidationError(_("Signatures required before submission."))
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
        template = self.env.ref('records_management.sign_template_portal_request')  # Assume template with 2 roles
        sign_request = self.env['sign.request'].create({
            'template_id': template.id,
            'reference': self.name,
            'request_item_ids': [(0, 0, {
                'role_id': self.env.ref('records_management.sign_role_requestor').id,
                'partner_id': self.env.user.partner_id.id,
            }), (0, 0, {
                'role_id': self.env.ref('records_management.sign_role_admin').id,
            })],
        })
        self.sign_request_id = sign_request

    def _signatures_complete(self):
        # Hook from sign.mixin to check if both signed
        if self.sign_request_id:
            # Check requestor signature
            for item in self.sign_request_id.request_item_ids:
                if item.role_id == self.env.ref('records_management.sign_role_requestor', raise_if_not_found=False):
                    if item.state == 'completed':
                        self.requestor_signature_date = fields.Datetime.now()
                # Check admin signature
                elif item.role_id == self.env.ref('records_management.sign_role_admin', raise_if_not_found=False):
                    if item.state == 'completed':
                        self.admin_signature_date = fields.Datetime.now()
            return self.sign_request_id.state == 'signed'
        return False

    def _create_fsm_task(self):
        task = self.env['project.task'].create({
            'name': f'FSM for {self.name}',
            'partner_id': self.partner_id.id,
            'description': self.description,
            'portal_request_id': self.id,
            'is_records_management': True,
        })
        self.fsm_task_id = task
        return task

    def _send_notification(self):
        # Email
        template = self.env.ref('records_management.portal_request_submitted_email', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
        # SMS if phone
        if self.partner_id.mobile:
            self.env['sms.sms'].create({
                'number': self.partner_id.mobile,
                'body': _('New portal request submitted: %s.', self.name),
            }).send()

    def _append_audit_log(self, message):
        current_log = self.audit_log or ''
        self.audit_log = current_log + f'<p>{fields.Datetime.now()}: {message}</p>'

    def _is_sensitive_change(self):
        # Logic to detect rate/quantity changes in description
        return 'rate' in self.description.lower() or 'quantity' in self.description.lower()

    def _is_field_request(self):
        return self.request_type in ('destruction', 'service', 'inventory_checkout')
