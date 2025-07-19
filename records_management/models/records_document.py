from odoo import models, fields, api, _


class RecordsDocument(models.Model):
    _name = 'records.document'
    _description = 'Document Record'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, name'

    # Core fields
    name = fields.Char('Document Reference', required=True, tracking=True)
    box_id = fields.Many2one(
        'records.box', string='Box', required=True, tracking=True,
        index=True, domain="[('state', '=', 'active')]"
    )
    location_id = fields.Many2one(
        related='box_id.location_id', string='Storage Location', store=True
    )

    # Document metadata
    document_type_id = fields.Many2one(
        'records.document.type', string='Document Type'
    )
    date = fields.Date('Document Date', default=fields.Date.context_today)
    description = fields.Html('Description')
    tags = fields.Many2many('records.tag', string='Tags')

    # Retention details
    retention_policy_id = fields.Many2one(
        'records.retention.policy', string='Retention Policy'
    )
    retention_date = fields.Date(
        'Retention Date', tracking=True,
        compute='_compute_retention_date', store=True
    )
    days_to_retention = fields.Integer(
        'Days until destruction', compute='_compute_days_to_retention'
    )

    # Relations
    partner_id = fields.Many2one('res.partner', string='Related Partner')
    customer_id = fields.Many2one(
        'res.partner',
        string='Customer',
        domain="[('is_company', '=', True)]",
        tracking=True,
        index=True
    )
    department_id = fields.Many2one(
        'records.department', string='Department',
        tracking=True, index=True
    )
    user_id = fields.Many2one(
        'res.users', string='Responsible',
        tracking=True
    )
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company
    )

    # File management
    attachment_ids = fields.Many2many(
        'ir.attachment', string='Attachments'
    )
    attachment_count = fields.Integer(
        'Document Attachments Count', compute='_compute_attachment_count'
    )

    # Status fields
    state = fields.Selection([
        ('draft', 'Draft'),
        ('stored', 'Stored'),
        ('retrieved', 'Retrieved'),
        ('returned', 'Returned'),
        ('archived', 'Archived'),
        ('destroyed', 'Destroyed')
    ], string='Status', default='draft', tracking=True)
    active = fields.Boolean(default=True)

    # Compute methods
    @api.depends('date', 'retention_policy_id',
                 'retention_policy_id.retention_years')
    def _compute_retention_date(self):
        for doc in self:
            if (doc.date and doc.retention_policy_id and
                    doc.retention_policy_id.retention_years):
                years = doc.retention_policy_id.retention_years
                doc.retention_date = fields.Date.add(doc.date, years=years)
            else:
                doc.retention_date = False

    @api.depends('retention_date')
    def _compute_days_to_retention(self):
        today = fields.Date.today()
        for doc in self:
            if doc.retention_date:
                delta = (doc.retention_date - today).days
                doc.days_to_retention = max(0, delta)
            else:
                doc.days_to_retention = 0

    def _compute_attachment_count(self):
        for rec in self:
            rec.attachment_count = len(rec.attachment_ids)

    # Onchange methods
    @api.onchange('box_id')
    def _onchange_box_id(self):
        """Ensure customer_id and department_id are always consistent with the selected box."""
        if self.box_id:
            self.customer_id = self.box_id.customer_id
            self.department_id = self.box_id.department_id
        else:
            self.customer_id = False
            self.department_id = False

    # Action methods for workflow buttons
    def action_store(self):
        """Store the document in the designated location."""
        for record in self:
            if record.state == 'draft':
                record.state = 'stored'
        return True

    def action_retrieve(self):
        """Retrieve the document from storage."""
        for record in self:
            if record.state in ('stored', 'returned'):
                record.state = 'retrieved'
        return True

    def action_return(self):
        """Return the document to storage."""
        for record in self:
            if record.state == 'retrieved':
                record.state = 'returned'
        return True

    def action_destroy(self):
        """Mark the document as destroyed (NAID compliance)."""
        for record in self:
            if record.state in ('stored', 'returned'):
                record.state = 'destroyed'
        return True

    def action_preview(self):
        """Preview the document attachment if available."""
        self.ensure_one()
        if self.attachment_ids:
            return {
                'type': 'ir.actions.act_url',
                'url': f'/web/content/{self.attachment_ids[0].id}?download=false',
                'target': 'new',
            }
        return False

    def action_schedule_destruction(self):
        """Schedule the document for destruction."""
        for record in self:
            if record.state == 'archived':
                # Set retention date for destruction scheduling
                if not record.retention_date:
                    record.retention_date = fields.Date.today()
        return True

    def action_view_attachments(self):
        """View all attachments for this document."""
        self.ensure_one()
        return {
            'name': _('Attachments'),
            'type': 'ir.actions.act_window',
            'res_model': 'ir.attachment',
            'view_mode': 'tree,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {
                'default_res_model': self._name,
                'default_res_id': self.id,
            },
        }