from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta


class FileRetrievalWorkOrder(models.Model):
    _name = 'file.retrieval.work.order'
    _description = 'File Retrieval Work Order'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, scheduled_date asc, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Work Order #", required=True, index=True, copy=False, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned To', default=lambda self: self.env.user, tracking=True)
    active = fields.Boolean(string='Active', default=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locating', 'Locating'),
        ('retrieving', 'Retrieving'),
        ('packaging', 'Packaging'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    priority = fields.Selection([('0', 'Low'), ('1', 'Normal'), ('2', 'High')], string='Priority', default='1')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    portal_request_id = fields.Many2one('portal.request', string='Portal Request')
    request_description = fields.Text(string='Request Description')

    retrieval_item_ids = fields.One2many('file.retrieval.item', 'work_order_id', string='Retrieval Items')
    item_count = fields.Integer(string="Item Count", compute='_compute_item_metrics', store=True)
    estimated_pages = fields.Integer(string="Estimated Pages", compute='_compute_item_metrics', store=True)

    container_ids = fields.Many2many('records.container', string='Related Containers', compute='_compute_related_containers', store=True)
    location_ids = fields.Many2many('records.location', string='Related Locations', compute='_compute_related_containers', store=True)

    access_coordination_needed = fields.Boolean(string='Access Coordination Needed')
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    estimated_completion_date = fields.Datetime(string='Est. Completion', compute='_compute_estimated_completion', store=True)
    actual_start_date = fields.Datetime(string='Actual Start Date')
    actual_completion_date = fields.Datetime(string='Actual Completion Date')

    delivery_method = fields.Selection([('scan', 'Scan & Email'), ('physical', 'Physical Delivery')], string='Delivery Method')
    packaging_type = fields.Selection([('box', 'Box'), ('envelope', 'Envelope')], string='Packaging Type')
    delivery_address_id = fields.Many2one('res.partner', string='Delivery Address')
    delivery_instructions = fields.Text(string='Delivery Instructions')

    progress_percentage = fields.Float(string='Progress', compute='_compute_progress', store=True)
    files_located_count = fields.Integer(string='Files Located', compute='_update_progress_metrics', store=True)
    files_retrieved_count = fields.Integer(string='Files Retrieved', compute='_update_progress_metrics', store=True)
    files_quality_approved_count = fields.Integer(string='Files Approved', compute='_update_progress_metrics', store=True)

    coordinator_id = fields.Many2one('res.users', string='Coordinator')
    rate_id = fields.Many2one('base.rate', string='Rate')
    invoice_id = fields.Many2one('account.move', string='Invoice', readonly=True)

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'item_count')
    def _compute_display_name(self):
        for record in self:
            if record.partner_id and record.item_count:
                record.display_name = _("%s - %s (%s files)") % (record.name, record.partner_id.name, record.item_count)
            elif record.partner_id:
                record.display_name = _("%s - %s") % (record.name, record.partner_id.name)
            else:
                record.display_name = record.name or _("New File Retrieval")

    @api.depends('retrieval_item_ids')
    def _compute_item_metrics(self):
        for record in self:
            items = record.retrieval_item_ids
            record.item_count = len(items)
            record.estimated_pages = sum(items.mapped('estimated_pages')) if items else 0

    @api.depends('retrieval_item_ids.container_id')
    def _compute_related_containers(self):
        for record in self:
            containers = record.retrieval_item_ids.mapped('container_id')
            record.container_ids = [(6, 0, containers.ids)]
            record.location_ids = [(6, 0, containers.mapped('storage_location_id').ids)]

    @api.depends('scheduled_date', 'item_count')
    def _compute_estimated_completion(self):
        for record in self:
            if record.scheduled_date and record.item_count:
                estimated_hours = 4 + (record.item_count * 2)
                record.estimated_completion_date = record.scheduled_date + timedelta(hours=estimated_hours)
            else:
                record.estimated_completion_date = False

    @api.depends('files_retrieved_count', 'item_count')
    def _compute_progress(self):
        for record in self:
            if record.item_count > 0:
                record.progress_percentage = (record.files_retrieved_count / record.item_count) * 100
            else:
                record.progress_percentage = 0.0

    @api.depends('retrieval_item_ids.status')
    def _update_progress_metrics(self):
        for record in self:
            items = record.retrieval_item_ids
            if items:
                record.files_located_count = len(items.filtered(lambda r: r.status in ['located', 'retrieved', 'packaged', 'delivered']))
                record.files_retrieved_count = len(items.filtered(lambda r: r.status in ['retrieved', 'packaged', 'delivered']))
                record.files_quality_approved_count = len(items.filtered(lambda r: r.status in ['packaged', 'delivered']))
            else:
                record.files_located_count = 0
                record.files_retrieved_count = 0
                record.files_quality_approved_count = 0

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('file.retrieval.work.order') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_confirm(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))
        self.write({'state': 'confirmed'})
        self.message_post(body=_("File retrieval work order confirmed for %s") % self.partner_id.name, message_type='notification')
        return True

    def action_start_locating(self):
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can start file location."))
        self.write({'state': 'locating', 'actual_start_date': fields.Datetime.now()})
        self.message_post(body=_("Started file location process."), message_type='notification')
        return True

    def action_complete(self):
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed."))
        self.write({'state': 'completed', 'actual_completion_date': fields.Datetime.now()})
        self.message_post(body=_("File retrieval work order completed successfully."), message_type='notification')
        return True

    def action_view_retrieval_items(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Retrieval Items"),
            "res_model": "file.retrieval.item",
            "view_mode": "tree,form",
            "domain": [("work_order_id", "=", self.id)],
            "context": {"default_work_order_id": self.id},
            "target": "current",
        }

    # ============================================================================
    # BUSINESS WORKFLOW METHODS
    # ============================================================================

    def _create_naid_audit_log(self, event_type):
        """Create NAID audit log for work order events"""
        if self.env["ir.module.module"].search([
            ("name", "=", "records_management"),
            ("state", "=", "installed")
        ]):
            self.env["naid.audit.log"].create({
                "event_type": event_type,
                "model_name": self._name,
                "record_id": self.id,
                "partner_id": self.partner_id.id,
                "description": _("Work order: %s") % self.name,
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now()
            })

