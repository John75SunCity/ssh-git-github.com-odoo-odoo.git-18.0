from dateutil.relativedelta import relativedelta
from odoo import models,     @a    def create(self, vals_list):
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_('Document "%s" created', doc.name))
        return docsdel_create_multi
    def create(self, vals_list):
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_("Document '%s' created") % (doc.name,))
        return docs, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsDocument(models.Model):
    _name = 'records.document'
    _description = 'Records Document'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name, create_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Document Name", required=True, tracking=True)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    user_id = fields.Many2one('res.users', string="Responsible", default=lambda self: self.env.user, tracking=True)
    reference = fields.Char(string="Reference / Barcode", copy=False, tracking=True)
    description = fields.Text(string="Description")

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, tracking=True)
    department_id = fields.Many2one('records.department', string="Department", domain="[('partner_id', '=', partner_id)]", tracking=True)
    container_id = fields.Many2one('records.container', string="Container", tracking=True)
    location_id = fields.Many2one(related='container_id.location_id', string="Location", store=True, readonly=True)
    document_type_id = fields.Many2one('records.document.type', string="Document Type", tracking=True)
    lot_id = fields.Many2one('stock.lot', string="Stock Lot", tracking=True, help="Lot/Serial number associated with this document.")

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_storage', 'In Storage'),
        ('in_transit', 'In Transit'),
        ('checked_out', 'Checked Out'),
        ('archived', 'Archived'),
        ('awaiting_destruction', 'Awaiting Destruction'),
        ('destroyed', 'Destroyed'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # DATES & RETENTION
    # ============================================================================
    create_date = fields.Datetime(string="Creation Date", readonly=True)
    received_date = fields.Date(string="Received Date", default=fields.Date.context_today, tracking=True)
    destruction_eligible_date = fields.Date(string="Destruction Eligible Date", compute='_compute_destruction_eligible_date', store=True, tracking=True)
    actual_destruction_date = fields.Date(string="Actual Destruction Date", readonly=True, tracking=True)
    days_until_destruction = fields.Integer(string="Days Until Destruction", compute='_compute_days_until_destruction')

    # ============================================================================
    # LEGAL HOLD / PERMANENT FLAG
    # ============================================================================
    is_permanent = fields.Boolean(string="Is Permanent", tracking=True, help="Mark this document to be exempt from destruction policies.")
    permanent_reason = fields.Text(string="Reason for Permanence", tracking=True)
    permanent_user_id = fields.Many2one('res.users', string="Flagged Permanent By", readonly=True, tracking=True)
    permanent_date = fields.Datetime(string="Flagged Permanent On", readonly=True, tracking=True)

    # ============================================================================
    # DIGITAL & COMPLIANCE
    # ============================================================================
    digital_scan_ids = fields.One2many('records.digital.scan', 'document_id', string="Digital Scans")
    scan_count = fields.Integer(string="Scan Count", compute='_compute_scan_count', store=True)
    audit_log_ids = fields.One2many('naid.audit.log', 'document_id', string="Audit Logs")
    audit_log_count = fields.Integer(string="Audit Log Count", compute='_compute_audit_log_count', store=True)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_("Document '%s' created") % doc.name)
        return docs

    def write(self, vals):
        if 'is_permanent' in vals and vals['is_permanent']:
            vals.update({
                'permanent_user_id': self.env.user.id,
                'permanent_date': fields.Datetime.now(),
            })
        return super().write(vals)

    def unlink(self):
        for doc in self:
            if doc.state not in ('draft', 'archived'):
                raise UserError(_("Cannot delete a document that is not in draft or archived state. Please archive it first."))
        return super().unlink()

    # ============================================================================
    # COMPUTE & ONCHANGE METHODS
    # ============================================================================
    @api.depends('name', 'reference')
    def _compute_display_name(self):
        for record in self:
            if record.reference:
                record.display_name = f"[{record.reference}] {record.name}"
            else:
                record.display_name = record.name

    @api.depends('received_date', 'document_type_id.effective_retention_years', 'is_permanent')
    def _compute_destruction_eligible_date(self):
        for record in self:
            if record.is_permanent or not record.received_date or not record.document_type_id or record.document_type_id.effective_retention_years <= 0:
                record.destruction_eligible_date = False
            else:
                years = record.document_type_id.effective_retention_years
                record.destruction_eligible_date = record.received_date + relativedelta(years=years)

    @api.depends('destruction_eligible_date')
    def _compute_days_until_destruction(self):
        today = fields.Date.context_today(self)
        for record in self:
            if record.destruction_eligible_date and not record.is_permanent:
                delta = record.destruction_eligible_date - today
                record.days_until_destruction = delta.days
            else:
                record.days_until_destruction = False

    @api.depends('digital_scan_ids')
    def _compute_scan_count(self):
        for record in self:
            record.scan_count = len(record.digital_scan_ids)

    @api.depends('audit_log_ids')
    def _compute_audit_log_count(self):
        for record in self:
            record.audit_log_count = len(record.audit_log_ids)

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('is_permanent', 'permanent_reason')
    def _check_permanent_reason(self):
        for record in self:
            if record.is_permanent and not record.permanent_reason:
                raise ValidationError(_("A reason is required when flagging a document as permanent."))

    @api.constrains('state', 'is_permanent')
    def _check_destruction_of_permanent(self):
        for record in self:
            if record.is_permanent and record.state in ('awaiting_destruction', 'destroyed'):
                raise ValidationError(_("A document flagged as permanent cannot be destroyed."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_view_scans(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Digital Scans'),
            'res_model': 'records.digital.scan',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }

    def action_view_audit_logs(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Logs'),
            'res_model': 'naid.audit.log',
            'view_mode': 'tree,form',
            'domain': [('document_id', '=', self.id)],
            'context': {'default_document_id': self.id}
        }

    def action_flag_permanent(self):
        # This action is intended to open a wizard for setting the reason.
        # For now, we can use a simplified direct write for demonstration.
        # A wizard would be better for UX.
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Flag as Permanent'),
            'res_model': 'records.document.flag.permanent.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_document_id': self.id}
        }

    def action_reset_to_draft(self):
        """
        Reset document state to draft, with enhanced validation and auditing.
        Only documents in 'in_storage' or 'archived' states can be reset.
        This action is logged for compliance purposes.
        """
        self.ensure_one()
        if self.state in ('destroyed', 'in_transit', 'checked_out'):
            raise UserError(_(
                "Cannot reset document to draft from its current state: %s. "
                "Only documents that are in storage or archived can be reset.", self.state
            ))

        self.write({'state': 'draft'})

        # Create a NAID audit log for this action
        self.env['naid.audit.log'].create({
            'document_id': self.id,
            'event_type': 'state_change',
            'description': _("Document state reset to Draft by %s.", self.env.user.name),
            'user_id': self.env.user.id,
        })

        self.message_post(body=_("Document reset to draft state."))

        return {
            'effect': {
                'fadeout': 'slow',
                'message': _("Document %s has been reset to Draft.", self.display_name),
                'type': 'rainbow_man',
            }
        }