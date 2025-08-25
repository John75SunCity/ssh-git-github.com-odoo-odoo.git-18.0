import base64
import hashlib
import re
from datetime import datetime, timedelta
import logging

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class NaidCertificate(models.Model):
    _name = 'naid.certificate'
    _description = 'NAID Destruction Certificate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'issue_date desc, certificate_number desc'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Reference', related='certificate_number', store=True)
    certificate_number = fields.Char(string='Certificate Number', required=True, copy=False, readonly=True, default=lambda self: _('New'))
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, readonly=True)
    partner_id = fields.Many2one('res.partner', string='Customer', required=True, readonly=True, states={'draft': [('readonly', False)]})

    # FSM & Operational Links
    fsm_task_id = fields.Many2one('project.task', string='FSM Work Order', readonly=True, states={'draft': [('readonly', False)]}, help="Link to the Field Service task for this destruction.")
    technician_user_id = fields.Many2one('res.users', string='Technician', related='fsm_task_id.user_id', store=True, readonly=True)

    # Link to the source of the destruction
    res_model = fields.Char(string='Related Document Model', readonly=True)
    res_id = fields.Integer(string='Related Document ID', readonly=True)

    destruction_date = fields.Datetime(string='Destruction Date', required=True, readonly=True, states={'draft': [('readonly', False)]})
    issue_date = fields.Datetime(string='Issue Date', readonly=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('issued', 'Issued'),
        ('sent', 'Sent'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    certificate_data = fields.Binary(string='Certificate PDF', readonly=True)
    certificate_filename = fields.Char(string='Certificate Filename', readonly=True)

    destruction_item_ids = fields.One2many('naid.certificate.item', 'certificate_id', string='Destroyed Items')
    container_ids = fields.Many2many('records.container', string='Destroyed Containers')
    box_ids = fields.Many2many('records.container', string='Destroyed Containers')
    total_weight = fields.Float(string='Total Weight (kg)', compute='_compute_totals', store=True)
    total_items = fields.Integer(string='Total Items', compute='_compute_totals', store=True)

    # Witness Information
    witness_name = fields.Char(string='Witness Name')
    witness_signature = fields.Binary(string='Witness Signature')

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_item_ids.weight', 'destruction_item_ids.quantity', 'container_ids', 'box_ids')
    def _compute_totals(self):
        for cert in self:
            cert.total_weight = sum(item.weight for item in cert.destruction_item_ids)
            cert.total_items = sum(item.quantity for item in cert.destruction_item_ids) + len(cert.container_ids) + len(cert.box_ids)

    @api.onchange('fsm_task_id')
    def _onchange_fsm_task_id(self):
        if self.fsm_task_id:
            self.partner_id = self.fsm_task_id.partner_id
            self.destruction_date = self.fsm_task_id.date_end or fields.Datetime.now()
            self.res_model = 'project.task'
            self.res_id = self.fsm_task_id.id

            # Automatically link related containers/boxes if they are on the task
            if hasattr(self.fsm_task_id, 'container_ids'):
                self.container_ids = [(6, 0, self.fsm_task_id.container_ids.ids)]
            if hasattr(self.fsm_task_id, 'box_ids'):
                self.box_ids = [(6, 0, self.fsm_task_id.box_ids.ids)]

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_issue_certificate(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft certificates can be issued."))
        if not self.destruction_item_ids and not self.container_ids and not self.box_ids:
            raise UserError(_("Cannot issue a certificate with no destroyed items, containers, or boxes listed."))

        # Placeholder for PDF generation logic
        # In a real scenario, this would call the report action
        pdf_content = self._generate_certificate_pdf()
        pdf_filename = f"CoD-{self.certificate_number}.pdf"

        self.write({
            'state': 'issued',
            'issue_date': fields.Datetime.now(),
            'certificate_data': pdf_content,
            'certificate_filename': pdf_filename,
        })
        self.message_post(body=_("Certificate issued and PDF generated."))

    def action_send_by_email(self):
        self.ensure_one()
        if self.state != 'issued':
            raise UserError(_("Only issued certificates can be sent."))

        template = self.env.ref('records_management.email_template_naid_certificate', raise_if_not_found=False)
        if not template:
            raise UserError(_("The email template for NAID Certificates could not be found."))

        template.send_mail(self.id, force_send=True)
        self.write({'state': 'sent'})
        self.message_post(body=_("Certificate sent to customer via email."))

    def action_cancel(self):
        self.ensure_one()
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Certificate has been cancelled."))

    def action_reset_to_draft(self):
        self.ensure_one()
        self.write({
            'state': 'draft',
            'issue_date': False,
            'certificate_data': False,
            'certificate_filename': False,
        })
        self.message_post(body=_("Certificate reset to draft."))

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    def _generate_certificate_pdf(self):
        """Generates the PDF for the certificate by calling the report action."""
        self.ensure_one()
        report = self.env.ref('records_management.action_report_naid_certificate')
        pdf_content, _file_type = report._render_qweb_pdf(self.ids)
        return base64.b64encode(pdf_content)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('certificate_number', _('New')) == _('New'):
                vals['certificate_number'] = self.env['ir.sequence'].next_by_code('naid.certificate') or _('New')
        return super().create(vals_list)
