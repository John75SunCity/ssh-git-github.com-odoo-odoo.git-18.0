from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ShreddingCertificate(models.Model):
    _name = 'shredding.certificate'
    _description = 'Shredding Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name desc'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Certificate #", required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string='Issued By', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(default=True)
    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('delivered', 'Delivered'),
        ('archived', 'Archived'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # DATES & DESTRUCTION DETAILS
    # ============================================================================
    certificate_date = fields.Date(string="Certificate Date", default=fields.Date.context_today, required=True, tracking=True)
    destruction_date = fields.Date(string="Destruction Date", required=True, tracking=True)
    destruction_method = fields.Selection([
        ('on_site_shredding', 'On-Site Shredding'),
        ('off_site_shredding', 'Off-Site Shredding'),
        ('incineration', 'Incineration'),
    ], string="Destruction Method", default='on_site_shredding', required=True)
    destruction_equipment = fields.Char(string="Destruction Equipment")
    equipment_serial_number = fields.Char(string="Equipment Serial Number")
    operator_name = fields.Char(string="Operator Name")

    # ============================================================================
    # CUSTOMER & WITNESS INFORMATION
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    customer_contact_id = fields.Many2one('res.partner', string="Customer Contact")
    service_location = fields.Char(string="Service Location")
    witness_required = fields.Boolean(string="Witness Required")
    witness_name = fields.Char(string="Witness Name")
    witness_title = fields.Char(string="Witness Title")

    # ============================================================================
    # MATERIALS & TOTALS
    # ============================================================================
    shredding_service_ids = fields.Many2many('fsm.order', string="Shredding Services")
    total_weight = fields.Float(string="Total Weight (kg)", compute='_compute_totals', store=True)
    total_containers = fields.Integer(string="Total Containers", compute='_compute_totals', store=True)
    service_count = fields.Integer(string="Service Count", compute='_compute_service_count', store=True)

    # ============================================================================
    # COMPLIANCE & DELIVERY
    # ============================================================================
    naid_level = fields.Selection([('aaa', 'NAID AAA'), ('aa', 'NAID AA')], string="NAID Level", default='aaa')
    certification_statement = fields.Text(string="Certification Statement", default=lambda self: self._default_certification_statement())
    chain_of_custody_number = fields.Char(string="Chain of Custody #")
    delivery_method = fields.Selection([('portal', 'Portal'), ('email', 'Email')], string="Delivery Method", default='portal')
    delivered_date = fields.Date(string="Delivered Date", readonly=True)
    notes = fields.Text(string='Internal Notes')

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shredding.certificate') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('shredding_service_ids')
    def _compute_service_count(self):
        for record in self:
            record.service_count = len(record.shredding_service_ids)

    @api.depends('shredding_service_ids.container_count', 'shredding_service_ids.total_weight')
    def _compute_totals(self):
        for record in self:
            record.total_weight = sum(record.shredding_service_ids.mapped('total_weight'))
            record.total_containers = sum(record.shredding_service_ids.mapped('container_count'))

    # ============================================================================
    # ONCHANGE & DEFAULTS
    # ============================================================================
    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        if self.partner_id:
            self.customer_contact_id = self.partner_id.child_ids[:1] if self.partner_id.child_ids else self.partner_id

    def _default_certification_statement(self):
        return _("This certifies that the materials listed have been collected and destroyed in a secure manner, rendering them completely unreadable and unusable, in compliance with NAID standards.")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_issue_certificate(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft certificates can be issued."))
        if not self.shredding_service_ids:
            raise UserError(_("You must link at least one shredding service before issuing a certificate."))
        self.write({'state': 'issued'})
        self.message_post(body=_("Certificate has been issued."))

    def action_deliver_certificate(self):
        self.ensure_one()
        if self.state != 'issued':
            raise UserError(_("Only issued certificates can be delivered."))
        
        if self.delivery_method == 'email':
            self._send_certificate_email()
        
        self.write({'state': 'delivered', 'delivered_date': fields.Date.context_today(self)})
        self.message_post(body=_("Certificate marked as delivered via %s.", self.delivery_method))

    def action_archive_certificate(self):
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Certificate has been archived."))

    def action_reset_to_draft(self):
        self.write({'state': 'draft', 'active': True})
        self.message_post(body=_("Certificate has been reset to draft."))

    def action_print_certificate(self):
        self.ensure_one()
        return self.env.ref('records_management.action_report_shredding_certificate').report_action(self)

    # ============================================================================
    # HELPER & PRIVATE METHODS
    # ============================================================================
    def _send_certificate_email(self):
        self.ensure_one()
        if not self.partner_id.email:
            raise UserError(_("Customer email address is required for email delivery."))
        
        template = self.env.ref('records_management.email_template_shredding_certificate', raise_if_not_found=False)
        if template:
            template.send_mail(self.id, force_send=True)
            self.message_post(body=_("Certificate sent to %s", self.partner_id.email))
        else:
            raise UserError(_("Email template for shredding certificate not found."))
