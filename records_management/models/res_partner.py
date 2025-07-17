from typing import List
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Reference', required=True, default='New', tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    department_id = fields.Many2one('records.department', string='Department', tracking=True, domain="[('partner_id', '=', partner_id)]")
    request_type = fields.Selection([
        ('destruction', 'Destruction Request'),
        ('service', 'Service Request'),
        ('inventory_checkout', 'Inventory Checkout'),
        ('billing_update', 'Billing Update'),
        ('quote_generate', 'Quote Generation'),
    ], string='Request Type', required=True, tracking=True)
    description = fields.Html(string='Description', tracking=True)
    state = fields.Selection([
        ('draft', 'Draft'), ('submitted', 'Submitted'),
        ('approved', 'Approved'), ('rejected', 'Rejected')
    ], default='draft', tracking=True)
    sign_request_id = fields.Many2one('sign.request', string='Signature Request')
    requestor_signature_date = fields.Datetime(string='Requestor Signature Date', readonly=True)
    admin_signature_date = fields.Datetime(string='Admin Signature Date', readonly=True)
    audit_log = fields.Html(string='Audit Trail', readonly=True)
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')
    invoice_id = fields.Many2one('account.move', string='Related Invoice')
    quote_id = fields.Many2one('sale.order', string='Related Quote')
    suggested_date = fields.Date(compute='_compute_suggested_date', store=True, help='Based on retention policy.')

    @api.depends('department_id.retention_policy_id', 'request_type')
    def _compute_suggested_date(self):
        for rec in self:
            if rec.request_type in ('destruction', 'service') and rec.department_id.retention_policy_id:
                rec.suggested_date = fields.Date.today() + fields.Date.timedelta(days=rec.department_id.retention_policy_id.duration_days or 0)
            else:
                rec.suggested_date = False

    @api.model_create_multi
    def create(self, vals_list: List[dict]):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('portal.request') or 'New'
            rec._generate_signature_request()
            rec._append_audit_log(_('Created by %s.', rec.partner_id.name))
        return records

    def action_submit(self):
        self.ensure_one()
        if self.sign_request_id and not all(self.sign_request_id.request_item_ids.mapped('is_signed')):
            raise ValidationError(_("All signatures required (NAID AAA dual for destruction)."))
        self.state = 'submitted'
        if self._is_field_request():
            self._create_fsm_task()
        if self.request_type == 'quote_generate':
            self._generate_quote()
        self._send_notification()
        self._append_audit_log(_('Submitted on %s.', fields.Datetime.now()))

    def action_approve(self):
        self.ensure_one()
        self.state = 'approved'
        if self.request_type == 'billing_update' and self._is_sensitive_change():
            self.invoice_id.write({'ref': self.description})  # e.g., PO update
        self._append_audit_log(_('Approved on %s.', fields.Datetime.now()))

    def action_reject(self):
        self.state = 'rejected'
        self._append_audit_log(_('Rejected on %s.', fields.Datetime.now()))

    def _generate_signature_request(self):
        template = self.env.ref('records_management.sign_template_portal_request', raise_if_not_found=False)
        if template:
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': self.name,
                'request_item_ids': [(0, 0, {
                    'role_id': self.env.ref('sign.sign_item_role_employee').id,  # Requestor
                    'partner_id': self.partner_id.id,
                }), (0, 0, {
                    'role_id': self.env.ref('sign.sign_item_role_manager').id,  # Admin
                    'partner_id': self.env.user.partner_id.id,
                })],
            })
            self.sign_request_id = sign_request

    def _create_fsm_task(self):
        task = self.env['project.task'].create({
            'name': f'FSM: {self.name}',
            'partner_id': self.partner_id.id,
            'description': self.description,
            'project_id': self.env.ref('industry_fsm.fsm_project').id,
        })
        self.fsm_task_id = task

    def _generate_quote(self):
        quote = self.env['sale.order'].create({
            'partner_id': self.partner_id.id,
            'order_line': [(0, 0, {
                'product_id': self.env.ref('records_management.product_shredding_service').id,
                'product_uom_qty': 1,
            })],
        })
        self.quote_id = quote

    def _send_notification(self):
        self.env.ref('records_management.portal_request_submitted_email').send_mail(self.id, force_send=True)
        if self.partner_id.mobile:
            self.env['sms.sms'].create({'number': self.partner_id.mobile, 'body': _(f'Request {self.name} submitted.')}).send()

    def _append_audit_log(self, message):
        self.audit_log = (self.audit_log or '') + f'<p>{fields.Datetime.now()}: {message}</p>'

    def _is_sensitive_change(self):
        return any(word in self.description.lower() for word in ['rate', 'quantity', 'po'])

    def _is_field_request(self):
        return self.request_type in ('destruction', 'service', 'inventory_checkout')