from odoo import _, api, fields, models  # Ensure imports are correct
from odoo.exceptions import UserError, ValidationError


class DocumentSearchAttempt(models.Model):
    _name = 'document.search.attempt'
    _description = 'Document Search Attempt'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'search_date desc, id desc'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Search Reference", required=True, index=True, copy=False, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    active = fields.Boolean(string='Active', default=True)

    # Unified linkage (supersedes all legacy file_retrieval/retrieval_item variants)
    retrieval_line_id = fields.Many2one(
        'records.retrieval.order.line',
        string='Retrieval Line',
        help='Unified retrieval order line replacing legacy file/item links'
    )

    # DEPRECATED LEGACY LINK (required only so deprecated document.retrieval.item One2many inverse still resolves)
    # This field was previously removed during legacy purge. It is reintroduced strictly to avoid
    # registry KeyError on inverse_name 'retrieval_item_id' from the deprecated model's
    # search_attempt_ids One2many. New logic MUST use retrieval_line_id instead.
    retrieval_item_id = fields.Many2one(
        'document.retrieval.item',
        string='(Deprecated) Retrieval Item',
        help='Legacy linkage kept only for backward compatibility. Use retrieval_line_id going forward.',
        index=True
    )

    # Specialized retrieval item links
    container_retrieval_id = fields.Many2one(
        "container.retrieval", string="Container Retrieval", help="Link to container retrieval request"
    )
    scan_retrieval_id = fields.Many2one(
        "scan.retrieval", string="Scan Retrieval", help="Link to scan retrieval request"
    )
    container_retrieval_item_id = fields.Many2one(
        "container.retrieval.item", string="Container Retrieval Item", help="Link to specific container retrieval item"
    )

    # Related workflow tracking
    work_order_id = fields.Many2one(
        "records.retrieval.order", string="Retrieval Order", help="Associated unified retrieval order for this search"
    )

    # Core Search Details
    container_id = fields.Many2one('records.container', string='Container Searched', required=True, tracking=True)
    partner_id = fields.Many2one('res.partner', string='Customer', related='container_id.partner_id', store=True)
    location_id = fields.Many2one('records.location', string='Location', related='container_id.location_id', store=True)
    searched_by_id = fields.Many2one('res.users', string='Searched By', required=True, default=lambda self: self.env.user)
    search_date = fields.Datetime(string='Search Date', required=True, default=fields.Datetime.now)
    search_duration = fields.Float(string='Search Duration (minutes)')

    found = fields.Boolean(string='Found', default=False)
    found_date = fields.Datetime(string='Found Date')

    requested_file_name = fields.Char(string="Requested File Name")
    search_notes = fields.Text(string="Search Notes / Findings")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('verified', 'Verified'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True)

    # ============================================================================
    # CONSTRAINS
    # ============================================================================
    @api.constrains('search_duration')
    def _check_duration_non_negative(self):
        for attempt in self:
            if attempt.search_duration and attempt.search_duration < 0:
                raise ValidationError(_("Search duration cannot be negative."))

    @api.constrains('search_date', 'found_date')
    def _check_date_sequence(self):
        for attempt in self:
            if attempt.search_date and attempt.found_date and attempt.search_date > attempt.found_date:
                raise ValidationError(_("Search date cannot be after the found date."))

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('name', 'requested_file_name', 'container_id.name', 'found')
    def _compute_display_name(self):
        for attempt in self:
            parts = []
            if attempt.requested_file_name:
                parts.append(attempt.requested_file_name)
            elif attempt.name:
                parts.append(attempt.name)

            if attempt.container_id:
                parts.append(_('in') + ' ' + attempt.container_id.name)

            status = _("Found") if attempt.found else _("Not Found")
            parts.append("[%s]" % status)
            attempt.display_name = " - ".join(parts)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('found')
    def _onchange_found(self):
        if self.found and not self.found_date:
            self.found_date = fields.Datetime.now()
        elif not self.found:
            self.found_date = False

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_finish(self):
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete searches that are in progress.'))
        if not self.search_notes:
            raise UserError(_('Please provide search notes before completing.'))
        status_msg = _('found') if self.found else _('not found')
        self.write({'state': 'completed'})
        self.message_post(body=_('Search completed. Document was') + ' ' + status_msg)
        return True

    def action_create_retrieval_request(self):
        """Create a new retrieval request based on this search attempt"""
        self.ensure_one()
        if not self.found:
            raise UserError(_("Cannot create retrieval request for unfound documents."))

        # Create container retrieval if none exists
        if not self.container_retrieval_id:
            retrieval = self.env["container.retrieval"].create(
                {
                    "partner_id": self.partner_id.id,
                    "container_id": self.container_id.id,
                    "requested_by_id": self.env.user.id,
                    "request_date": fields.Datetime.now(),
                    "notes": _('Based on search attempt:') + ' ' + self.name + '\n' + _('File:') + ' ' + (self.requested_file_name or 'N/A'),
                }
            )
            self.container_retrieval_id = retrieval.id

        return {
            "type": "ir.actions.act_window",
            "name": _("Container Retrieval"),
            "res_model": "container.retrieval",
            "res_id": self.container_retrieval_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_create_work_order(self):
        """Create a work order for this search if none exists"""
        self.ensure_one()
        if not self.work_order_id:
            work_order = self.env["records.retrieval.order"].create({
                "partner_id": self.partner_id.id,
                "location_id": self.location_id.id,
                "assigned_to_id": self.searched_by_id.id,
                "state": "assigned",
                "notes": _('Work order for search attempt:') + ' ' + self.name,
            })
            self.work_order_id = work_order.id

        return {
            "type": "ir.actions.act_window",
            "name": _("Work Order"),
            "res_model": "records.retrieval.order",
            "res_id": self.work_order_id.id,
            "view_mode": "form",
            "target": "current",
        }

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('document.search.attempt') or _('New')
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if 'state' in vals:
            for attempt in self:
                state_label = dict(attempt._fields['state'].selection).get(attempt.state)
                if state_label:
                    attempt.message_post(body=_('Status changed to') + ' ' + state_label)
        return res
