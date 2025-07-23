# Updated file: Added missing fields and fixed dependencies
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class PortalRequest(models.Model):
    _name = 'portal.request'
    _description = 'Customer Portal Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', default='New', readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True)
    department_id = fields.Many2one('records.department', string='Department', domain="[('partner_id', '=', partner_id)]")
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
    ], default='draft')
    
    # Missing fields that caused the view error
    is_walk_in = fields.Boolean(string='Walk-in Request', default=False, help='Indicates if this is a walk-in request')
    linked_visitor_id = fields.Many2one('res.partner', string='Linked Visitor', help='Partner record for walk-in visitors')
    
    # Existing fields
    sign_request_id = fields.Many2one('sign.request', string='Signature Request')
    requestor_signature_date = fields.Datetime(string='Requestor Signature Date')
    admin_signature_date = fields.Datetime(string='Admin Signature Date')
    audit_log = fields.Html(string='Audit Trail', readonly=True)
    fsm_task_id = fields.Many2one('project.task', string='FSM Task')
    invoice_id = fields.Many2one('account.move', string='Related Invoice')
    temp_inventory_ids = fields.Many2many('temp.inventory', string='Temporary Inventory Items')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for rec in records:
            if rec.name == 'New':
                rec.name = self.env['ir.sequence'].next_by_code('portal.request') or 'PR-' + str(rec.id)
            # Only generate signature request if sign module is available
            if 'sign' in self.env.registry._init_modules:
                rec._generate_signature_request()
            rec._append_audit_log(_('Request created by %s.', rec.partner_id.name))
        return records

    def action_submit(self):
        self.write({'state': 'submitted'})
        # Check signatures only if sign module is available
        if 'sign' in self.env.registry._init_modules and self.sign_request_id:
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
            if self.invoice_id:
                self.invoice_id.write({'ref': self.description})
        self.state = 'approved'
        self._append_audit_log(_('Approved by admin on %s.', fields.Datetime.now()))

    def action_reject(self):
        self.state = 'rejected'
        self._append_audit_log(_('Rejected by admin on %s.', fields.Datetime.now()))

    def _generate_signature_request(self):
        try:
            template = self.env.ref('records_management.sign_template_portal_request', raise_if_not_found=False)
            if not template:
                return  # Skip if template doesn't exist
            
            sign_request = self.env['sign.request'].create({
                'template_id': template.id,
                'reference': self.name,
                'request_item_ids': [(0, 0, {
                    'role_id': self.env.ref('sign.sign_item_role_requestor', raise_if_not_found=False).id,
                    'partner_id': self.partner_id.id,
                }), (0, 0, {
                    'role_id': self.env.ref('sign.sign_item_role_admin', raise_if_not_found=False).id,
                    'partner_id': self.env.company.partner_id.id,
                })],
            })
            sign_request.action_draft()
            self.sign_request_id = sign_request
        except Exception:
            # Gracefully handle if sign module is not available
            pass

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
        try:
            # Check if FSM module is available
            project_ref = self.env.ref('industry_fsm.fsm_project', raise_if_not_found=False)
            project_id = project_ref.id if project_ref else False
            
            task = self.env['project.task'].create({
                'name': f'FSM for {self.name}',
                'partner_id': self.partner_id.id,
                'description': self.description,
                'project_id': project_id,
            })
            self.fsm_task_id = task
            return task
        except Exception:
            # Gracefully handle if FSM module is not available
            pass

    def _send_notification(self):
        try:
            # Email
            template = self.env.ref('records_management.portal_request_submitted_email', raise_if_not_found=False)
            if template:
                template.send_mail(self.id, force_send=True)
            
            # SMS if phone and SMS module available
            if self.partner_id.mobile and 'sms' in self.env.registry._init_modules:
                self.env['sms.sms'].create({
                    'number': self.partner_id.mobile,
                    'body': _('New portal request submitted: %s.', self.name),
                }).send()
        except Exception:
            # Gracefully handle if modules are not available
            pass

    def _append_audit_log(self, message):
        if not self.audit_log:
            self.audit_log = ''
        self.audit_log += f'<p>{fields.Datetime.now()}: {message}</p>'

    def _is_sensitive_change(self):
        if not self.description:
            return False
        return 'rate' in self.description.lower() or 'quantity' in self.description.lower()

    def _is_field_request(self):
        return self.request_type in ('destruction', 'service', 'inventory_checkout')

    @api.onchange('is_walk_in')
    def _onchange_is_walk_in(self):
        """Clear linked visitor when not a walk-in request"""
        if not self.is_walk_in:
            self.linked_visitor_id = False