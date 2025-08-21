from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
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
    responsible_person_id = fields.Many2one('res.user', string='Responsible')
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
    temp_inventory_id = fields.Many2one('temp.inventory', string="Temporary Inventory")
    retention_policy_id = fields.Many2one('records.retention.policy', string="Retention Policy", tracking=True)
    series_id = fields.Many2one('records.series', string='Series', tracking=True)
    storage_box_id = fields.Many2one('records.storage.box', string='Storage Box', tracking=True)
    request_id = fields.Many2one('records.request', string='Request', tracking=True)

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
    storage_date = fields.Date(string="Storage Date", tracking=True)
    last_access_date = fields.Date(string="Last Access Date", tracking=True)
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
    document_category = fields.Char("Document Category", tracking=True)
    media_type = fields.Char("Media Type", tracking=True)
    original_format = fields.Char("Original Format", tracking=True)
    digitized = fields.Boolean("Digitized", tracking=True)
    digital_scan_ids = fields.One2many('records.digital.scan', 'document_id', string="Digital Scans")
    scan_count = fields.Integer(string="Scan Count", compute='_compute_scan_count', store=True)
    audit_log_ids = fields.One2many('naid.audit.log', 'document_id', string="Audit Logs")
    audit_log_count = fields.Integer(string="Audit Log Count", compute='_compute_audit_log_count', store=True)
    chain_of_custody_ids = fields.One2many('naid.custody', 'document_id', string="Chain of Custody")
    chain_of_custody_count = fields.Integer(string="Chain of Custody Events", compute='_compute_chain_of_custody_count', store=True)

    # ============================================================================
    # DESTRUCTION INFO
    # ============================================================================
    destruction_method = fields.Char("Destruction Method", tracking=True)
    destruction_certificate_id = fields.Many2one('naid.certificate', string="Destruction Certificate", tracking=True)
    naid_destruction_verified = fields.Boolean("NAID Destruction Verified", tracking=True)
    destruction_authorized_by_id = fields.Many2one('res.users', string="Destruction Authorized By", tracking=True)
    destruction_witness_id = fields.Many2one('res.partner', string="Destruction Witness", tracking=True)
    destruction_facility = fields.Char("Destruction Facility", tracking=True)
    destruction_notes = fields.Text("Destruction Notes", tracking=True)

    # ============================================================================
    # AUDIT & CHAIN OF CUSTODY
    # ============================================================================
    event_date = fields.Date(string="Event Date", help="Date of the last significant event (e.g., access, move, audit).")
    compliance_verified = fields.Boolean(string="Compliance Verified", help="Indicates if the document's handling meets compliance standards.")
    scan_date = fields.Datetime(string="Last Scan Date", help="Timestamp of the last barcode scan.")
    last_verified_by_id = fields.Many2one('res.users', string="Last Verified By", help="User who last verified the document's status or location.")
    last_verified_date = fields.Datetime(string="Last Verified Date", help="Timestamp of the last verification.")
    is_missing = fields.Boolean(string="Is Missing", help="Flagged if the document cannot be located during an audit.")
    missing_since_date = fields.Date(string="Missing Since", help="Date the document was first reported as missing.")
    found_date = fields.Date(string="Date Found", help="Date the document was located after being missing.")

    # ============================================================================
    # FILTERS & GROUPING FIELDS (for advanced search and reporting)
    # ============================================================================
    pending_destruction = fields.Boolean(string="Pending Destruction", compute='_compute_pending_destruction', store=True, search='_search_pending_destruction', help="True if the document is eligible for destruction but not yet destroyed.")
    recently_accessed = fields.Boolean(string="Recently Accessed", compute='_compute_recent_access', search='_search_recent_access', help="True if the document was accessed in the last 30 days.")
    group_by_customer_id = fields.Many2one(related='partner_id', string="Group by Customer", store=False, readonly=True) # For grouping in views
    group_by_department_id = fields.Many2one(related='department_id', string="Group by Department", store=False, readonly=True) # For grouping in views
    group_by_location_id = fields.Many2one(related='location_id', string="Group by Location", store=False, readonly=True) # For grouping in views
    group_by_doc_type_id = fields.Many2one(related='document_type_id', string="Group by Document Type", store=False, readonly=True) # For grouping in views
    destroyed = fields.Boolean(string="Is Destroyed", compute='_compute_destroyed', store=True, help="True if the document's state is 'destroyed'.")

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to set sequence and log creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.document') or _('New')
        docs = super().create(vals_list)
        for doc in docs:
            doc.message_post(body=_('Document "%s" created') % doc.name)
        return docs

    def write(self, vals):
        if 'is_permanent' in vals and vals['is_permanent']:
            vals.update({
                'permanent_user_id': self.env.user.id,
                'permanent_date': fields.Datetime.now(),
            })
        if 'state' in vals:
            for record in self:
                record.message_post_with_view(
                    'mail.message_origin_link',
                    values={'self': record, 'origin': record.state, 'edit': True},
                    subtype_id=self.env.ref('mail.mt_note').id)
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

    @api.depends('chain_of_custody_ids')
    def _compute_chain_of_custody_count(self):
        for record in self:
            record.chain_of_custody_count = len(record.chain_of_custody_ids)

    @api.depends('last_review_date', 'vital_record_review_period')
    def _compute_next_review_date(self):
        for record in self:
            if record.last_review_date and record.vital_record_review_period > 0:
                record.next_review_date = record.last_review_date + relativedelta(years=record.vital_record_review_period)
            else:
                record.next_review_date = False

    def _compute_document_qr_code(self):
        # This would generate a QR code, likely using an external library
        for record in self:
            record.document_qr_code = False

    @api.depends('checked_out_date', 'expected_return_date')
    def _compute_is_overdue(self):
        for record in self:
            record.is_overdue = record.checked_out_date and record.expected_return_date and record.expected_return_date < fields.Date.today()

    @api.depends('attachment_ids')
    def _compute_has_attachments(self):
        for record in self:
            record.has_attachments = bool(record.attachment_ids)

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = len(record.attachment_ids)

    def _compute_public_url(self):
        for record in self:
            record.public_url = ''

    def _compute_is_favorite(self):
        for record in self:
            record.is_favorite = False

    def _inverse_is_favorite(self):
        pass

    def _compute_related_records_count(self):
        for record in self:
            record.related_records_count = 0

    @api.depends('destruction_eligible_date', 'is_permanent')
    def _compute_destruction_eligible(self):
        for record in self:
            record.destruction_eligible = not record.is_permanent and record.destruction_eligible_date and record.destruction_eligible_date <= fields.Date.today()

    def _compute_destruction_profit(self):
        for record in self:
            record.destruction_profit = record.destruction_revenue - record.destruction_cost

    @api.depends('destruction_eligible_date', 'state')
    def _compute_pending_destruction(self):
        for record in self:
            record.pending_destruction = record.destruction_eligible_date and record.state == 'awaiting_destruction'

    def _search_pending_destruction(self, operator, value):
        if operator == '=' and value:
            return [('destruction_eligible_date', '!=', False), ('state', '=', 'awaiting_destruction')]
        return [('state', '!=', 'awaiting_destruction')]

    @api.depends('last_access_date')
    def _compute_recent_access(self):
        thirty_days_ago = fields.Date.today() - relativedelta(days=30)
        for record in self:
            record.recently_accessed = record.last_access_date and record.last_access_date >= thirty_days_ago

    def _search_recent_access(self, operator, value):
        if operator == '=' and value:
            return [('last_access_date', '>=', fields.Date.today() - relativedelta(days=30))]
        return [('last_access_date', '<', fields.Date.today() - relativedelta(days=30))]

    @api.depends('state')
    def _compute_destroyed(self):
        for record in self:
            record.destroyed = record.state == 'destroyed'

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
        """Reset the document state back to 'Draft'."""
        self.ensure_one()
        if self.state not in ['in_storage', 'archived']:
            raise UserError(
                _("Cannot reset document to draft from its current state: %s. Only documents that are in storage or archived can be reset.", self.state)
            )
        self.write({'state': 'draft'})
        self.message_post(
            body=_("Document state reset to Draft by %s", self.env.user.name),
            subject=_("Document Reset to Draft")
        )
        # Return a client action to notify the user
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Success"),
                'message': _("Document %s has been reset to Draft", self.display_name),
                'sticky': False,
            }
        }
