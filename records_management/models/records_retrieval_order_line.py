from odoo import api, fields, models, _


class RecordsRetrievalOrderLine(models.Model):
    _name = 'records.retrieval.order.line'
    _description = 'Retrieval Order Line'
    _inherit = ['mail.thread']
    _order = 'priority desc, order_id, name'

    order_id = fields.Many2one(comodel_name='records.retrieval.order', string='Retrieval Order', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Line Reference', required=True, copy=False, default=lambda self: "New")
    file_name = fields.Char(string='File Name', required=True, tracking=True)
    requested_file_name = fields.Char(string='Requested File Name', help='Alias for API parity with legacy model', compute='_compute_requested_file_name', store=True)
    file_description = fields.Char(string='Description')
    file_reference = fields.Char(string='File Reference')
    file_type = fields.Selection([
        ('document', 'Document'),
        ('contract', 'Contract'),
        ('invoice', 'Invoice'),
        ('report', 'Report'),
        ('legal', 'Legal Document'),
        ('medical', 'Medical Record'),
        ('financial', 'Financial Record'),
        ('hr', 'HR Document'),
        ('other', 'Other')
    ], string='File Type', default='document')
    item_type = fields.Selection([
        ('file', 'File'),
        ('folder', 'Folder'),
        ('container', 'Container'),
        ('scan', 'Scan Target'),
        ('other', 'Other')
    ], string='Item Type', default='file')
    container_id = fields.Many2one(comodel_name='records.container', string='Container')
    location_id = fields.Many2one(comodel_name='records.location', string='Location', related='container_id.location_id', store=True)
    position_note = fields.Char(string='Position / Slot')
    barcode = fields.Char(string='Barcode')
    estimated_pages = fields.Integer(string='Est. Pages', default=0)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('locating', 'Locating'),
        ('located', 'Located'),
        ('retrieving', 'Retrieving'),
        ('retrieved', 'Retrieved'),
        ('not_found', 'Not Found'),
        ('partial', 'Partial'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed')
    ], string='Status', default='pending', tracking=True, help="Processing status of this specific line item")
    
    # Alias for compatibility with views that expect 'state' field
    state = fields.Selection(related='status', string='State', store=False, 
                           help="Alias for status field to maintain view compatibility")
    
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    assigned_user_id = fields.Many2one(comodel_name='res.users', string='Assigned To')
    retrieved_by_id = fields.Many2one(comodel_name='res.users', string='Retrieved By')
    date_retrieved = fields.Datetime(string='Date Retrieved')
    date_delivered = fields.Datetime(string='Date Delivered')
    notes = fields.Text(string='Notes')
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', tracking=True)

    # ------------------------------------------------------------------
    # Unified retrieval line fields
    # ------------------------------------------------------------------
    discovery_container_id = fields.Many2one(comodel_name='records.container', string='Discovery Container')
    searched_container_ids = fields.Many2many(
        'records.container',
        'retrieval_line_searched_container_rel',
        'line_id', 'container_id',
        string='Searched Containers'
    )
    # Link search attempts directly to unified line (replaces file_retrieval_id / retrieval_item_id)
    search_attempt_ids = fields.One2many('document.search.attempt', 'retrieval_line_id', string='Search Attempts')
    # Use distinct label to avoid duplicate with search_attempt_ids
    search_attempt_count = fields.Integer(string='Search Attempt Count', compute='_compute_attempt_count')
    condition_before = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition Before')
    condition_after = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition After')
    not_found_reason = fields.Selection([
        ('not_in_container', 'Not in Expected Container'),
        ('container_missing', 'Container Missing'),
        ('destroyed', 'File Destroyed'),
        ('misfiled', 'Misfiled'),
        ('access_denied', 'Access Denied'),
        ('other', 'Other Reason')
    ], string='Not Found Reason')
    not_found_notes = fields.Text(string='Not Found Notes')
    due_date = fields.Datetime(string='Due Date')
    # ------------------------------------------------------------------
    # Additional legacy item parity fields
    # ------------------------------------------------------------------
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal', tracking=True)
    access_authorized = fields.Boolean(string='Access Authorized', default=True)
    authorization_notes = fields.Text(string='Authorization Notes')
    current_location = fields.Char(string='Current Location')
    # request/scheduling (related to order for consistency; kept for api parity)
    request_date = fields.Datetime(string='Request Date', related='order_id.request_date', store=True)
    scheduled_date_line = fields.Datetime(string='Scheduled Date (Line Override)')
    effective_scheduled_date = fields.Datetime(string='Effective Scheduled Date', compute='_compute_effective_scheduled_date', store=True)
    search_start_date = fields.Datetime(string='Search Start Date')
    retrieval_date = fields.Datetime(string='Retrieval Date', related='date_retrieved', store=True)
    completion_date = fields.Datetime(string='Completion Date')
    estimated_time = fields.Float(string='Estimated Time (Hours)', default=0.0)
    actual_time = fields.Float(string='Actual Time (Hours)', default=0.0)
    condition_notes = fields.Text(string='Condition Notes')
    quality_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
        ('review', 'Under Review')
    ], string='Quality Status', default='pending', tracking=True)
    delivery_method = fields.Selection([
        ('scan', 'Digital Scan'),
        ('copy', 'Physical Copy'),
        ('original', 'Original Document'),
        ('pickup', 'Customer Pickup'),
        ('mail', 'Mail Delivery'),
        ('email', 'Email Delivery')
    ], string='Delivery Method', default='scan')
    delivery_address = fields.Text(string='Delivery Address')
    delivery_instructions = fields.Text(string='Delivery Instructions')
    customer_notes = fields.Text(string='Customer Notes')
    search_notes = fields.Text(string='Search Notes')
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_overdue_status', store=True)
    days_since_request = fields.Integer(string='Days Since Request', compute='_compute_days_since_request', store=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    def action_mark_located(self):
        self.ensure_one()
        if self.status == 'pending':
            self.status = 'located'

    def action_mark_retrieved(self):
        self.ensure_one()
        if self.status in ['pending', 'located']:
            self.write({'status': 'retrieved', 'date_retrieved': fields.Datetime.now(), 'retrieved_by_id': self.env.user.id})

    def action_mark_delivered(self):
        self.ensure_one()
        if self.status == 'retrieved':
            self.write({'status': 'delivered', 'date_delivered': fields.Datetime.now()})

    def action_complete(self):
        self.ensure_one()
        if self.status == 'delivered':
            self.status = 'completed'

    # ------------------------------------------------------------------
    # Extended legacy-style actions
    # ------------------------------------------------------------------
    def action_start_lookup(self):
        self.ensure_one()
        self.ensure_one()
        if self.status != 'pending':
            return False
        self.write({'status': 'searching', 'search_start_date': fields.Datetime.now(), 'assigned_user_id': self.env.user.id})
        self.message_post(body=_('Search started for retrieval line'))
        return True

    def action_mark_not_found(self, reason='not_in_container', notes=None):
        self.ensure_one()
        if self.status not in ['searching', 'pending']:
            return False
        if not notes:
            # Keep dynamic timestamp outside translated segment to satisfy lint.
            notes = _("File not found after search at") + ' ' + fields.Datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        self.write({
            'status': 'not_found',
            'not_found_reason': reason,
            'not_found_notes': notes,
        })
        self.message_post(body=_('Marked not found') + ': ' + notes)
        return True

    def action_cancel(self):
        self.ensure_one()
        if self.status in ['completed', 'cancelled']:
            return False
        self.write({'status': 'cancelled'})
        self.message_post(body=_('Retrieval line cancelled'))
        return True

    def action_log_container_lookup(self, container, found=False, notes=""):
        self.ensure_one()
        if self.status != 'searching':
            return False
        # create search attempt
        self.env['document.search.attempt'].create({
            'retrieval_line_id': self.id,
            'container_id': container.id,
            'searched_by_id': self.env.user.id,
            'search_date': fields.Datetime.now(),
            'found': found,
            'search_notes': notes,
            'requested_file_name': self.file_name,
        })
        # add container to searched set
        self.write({'searched_container_ids': [(4, container.id)]})
        if found:
            self.write({
                'status': 'located',
                'discovery_container_id': container.id,
                'container_id': container.id,
            })
            self.message_post(body=_('File located in container') + ' ' + container.name)
        else:
            self.message_post(body=_('Container searched. File not found') + ': ' + container.name)
        return True

    # ------------------------------------------------------------------
    # Computes (display name, overdue, days since request, effective schedule)
    # ------------------------------------------------------------------
    @api.depends('file_name', 'barcode', 'status')
    def _compute_display_name(self):  # noqa: D401
        for rec in self:
            parts = [rec.file_name or rec.name or _('Retrieval Line')]
            if rec.barcode:
                parts.append('[%s]' % rec.barcode)
            if rec.status:
                parts.append('(%s)' % dict(rec._fields['status'].selection).get(rec.status, rec.status))
            rec.display_name = ' '.join(parts)

    @api.depends('due_date', 'status')
    def _compute_overdue_status(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.due_date and rec.status not in ['completed', 'cancelled']:
                rec.is_overdue = rec.due_date < now
            else:
                rec.is_overdue = False

    @api.depends('request_date')
    def _compute_days_since_request(self):
        now = fields.Datetime.now()
        for rec in self:
            if rec.request_date:
                rec.days_since_request = (now - rec.request_date).days
            else:
                rec.days_since_request = 0

    @api.depends('scheduled_date_line', 'order_id.scheduled_date')
    def _compute_effective_scheduled_date(self):
        for rec in self:
            rec.effective_scheduled_date = rec.scheduled_date_line or rec.order_id.scheduled_date

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    @api.depends('search_attempt_ids')
    def _compute_attempt_count(self):  # renamed to avoid linter misclassification
        """Compute number of search attempts for unified line."""
        for rec in self:
            rec.search_attempt_count = len(rec.search_attempt_ids)
    _compute_search_attempt_count = _compute_attempt_count  # backward compatibility alias

    @api.depends('file_name')
    def _compute_requested_file_name(self):
        for rec in self:
            rec.requested_file_name = rec.file_name

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.retrieval.order.line') or _('New')
        return super().create(vals_list)

    # ------------------------------------------------------------------
    # Onchange methods
    # ------------------------------------------------------------------
    @api.onchange('container_id')
    def _onchange_container_id(self):
        if self.container_id and hasattr(self.container_id, 'current_location'):
            self.current_location = self.container_id.current_location

    @api.onchange('status')
    def _onchange_status(self):
        if self.status == 'retrieved' and not self.date_retrieved:
            self.date_retrieved = fields.Datetime.now()
            self.retrieved_by_id = self.env.user

    # ------------------------------------------------------------------
    # Constraints
    # ------------------------------------------------------------------
    @api.constrains('partner_id', 'status')
    def _check_partner_required(self):
        for rec in self:
            if rec.status != 'cancelled' and not rec.partner_id:
                raise ValueError(_('Customer is required for retrieval lines unless cancelled.'))

    @api.constrains('estimated_time', 'actual_time')
    def _check_time_non_negative(self):
        for rec in self:
            if rec.estimated_time < 0:
                raise ValueError(_('Estimated time cannot be negative.'))
            if rec.actual_time < 0:
                raise ValueError(_('Actual time cannot be negative.'))

    @api.constrains('due_date', 'request_date')
    def _check_date_sequence(self):
        for rec in self:
            if rec.due_date and rec.request_date and rec.due_date < rec.request_date:
                raise ValueError(_('Due date cannot be before request date.'))

    # ------------------------------------------------------------------
    # Utility helpers (parity with legacy)
    # ------------------------------------------------------------------
    @api.model
    def find_by_status(self, status_list):
        return self.search([('status', 'in', status_list)])

    @api.model
    def find_by_partner(self, partner_id):
        return self.search([('partner_id', '=', partner_id)])

    @api.model
    def get_high_priority_items(self):
        return self.search([('priority', 'in', ['2', '3']), ('status', 'not in', ['completed', 'cancelled'])])

    def get_status_color(self):
        color_map = {
            'pending': 'secondary',
            'searching': 'info',
            'located': 'warning',
            'retrieved': 'primary',
            'packaged': 'info',
            'delivered': 'success',
            'returned': 'warning',
            'completed': 'success',
            'not_found': 'danger',
            'cancelled': 'dark'
        }
        return color_map.get(self.status, 'secondary')

    def get_priority_color(self):
        color_map = {'0': 'secondary', '1': 'info', '2': 'warning', '3': 'danger'}
        return color_map.get(self.priority, 'info')

    def log_activity(self, activity_type, message):  # activity_type reserved for future categorization
        self.ensure_one()
        self.message_post(body=message, message_type='notification')
        return True
