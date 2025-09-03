from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class FileRetrievalItem(models.Model):
    _name = 'file.retrieval.item'
    _description = 'File Retrieval Item Management'
    _inherit = ['retrieval.item.base', 'mail.thread', 'mail.activity.mixin']
    _rec_name = 'display_name'
    _order = 'priority desc, create_date desc'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================

    name = fields.Char(
        string='Item Reference',
        required=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
        help="Unique identifier for this file retrieval item"
    )

    barcode = fields.Char(
        string='Barcode',
        copy=False,
        tracking=True,
        help="Barcode identifier for tracking"
    )

    # ============================================================================
    # FILE-SPECIFIC FIELDS
    # ============================================================================

    requested_file_name = fields.Char(
        string='Requested File Name',
        required=True,
        tracking=True,
        help="Name of the file being requested for retrieval"
    )

    file_description = fields.Text(
        string='File Description',
        help="Additional description or details about the requested file"
    )

    file_reference = fields.Char(
        string='File Reference',
        help="Internal reference number or code for the file"
    )

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
    ], string='File Type', default='document', tracking=True)

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        help="Customer requesting the file retrieval"
    )

    work_order_id = fields.Many2one(
        'file.retrieval.work.order',
        string='Work Order',
        ondelete='cascade',
        tracking=True,
        help="Associated work order for this retrieval item"
    )

    container_id = fields.Many2one(
        'records.container',
        string='Target Container',
        tracking=True,
        help="Primary container where file is expected to be located"
    )

    discovery_container_id = fields.Many2one(
        'records.container',
        string='Discovery Container',
        tracking=True,
        help="Container where file was actually found (may differ from target)"
    )

    searched_container_ids = fields.Many2many(
        'records.container',
        'file_retrieval_item_searched_container_rel',
        'item_id', 'container_id',
        string='Searched Containers',
        help="Containers that have been searched for this file"
    )

    search_attempt_ids = fields.One2many(
        'document.search.attempt',
        'retrieval_item_id',
        string='Search Attempts',
        help="Detailed log of search attempts"
    )

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
        help="User assigned to handle this retrieval item"
    )

    retrieved_by_id = fields.Many2one(
        'res.users',
        string='Retrieved By',
        tracking=True,
        help="User who successfully retrieved the file"
    )

    # ============================================================================
    # STATUS AND WORKFLOW FIELDS
    # ============================================================================

    status = fields.Selection(
        selection_add=[
            ('packaged', 'Packaged'),
            ('delivered', 'Delivered'),
            ('returned', 'Returned')
        ],
        string='Status',
        ondelete={
            'packaged': 'set default',
            'delivered': 'set default',
            'returned': 'set default'
        }
    )

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1', required=True, tracking=True)

    # ============================================================================
    # SECURITY AND ACCESS FIELDS
    # ============================================================================

    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal', tracking=True)

    access_authorized = fields.Boolean(
        string='Access Authorized',
        default=True,
        help="Whether access to this file has been authorized"
    )

    authorization_notes = fields.Text(
        string='Authorization Notes',
        help="Notes regarding file access authorization"
    )

    # ============================================================================
    # LOCATION AND TRACKING FIELDS
    # ============================================================================

    current_location = fields.Char(
        string='Current Location',
        help="Current physical location of the file"
    )

    location_id = fields.Many2one(
        'records.location',
        string='Storage Location',
        help="Storage location where file should be located"
    )

    # ============================================================================
    # TIMING FIELDS
    # ============================================================================

    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True
    )

    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True,
        help="When this retrieval is scheduled to be completed"
    )

    search_start_date = fields.Datetime(
        string='Search Start Date',
        tracking=True
    )

    retrieval_date = fields.Datetime(
        string='Retrieval Date',
        tracking=True
    )

    completion_date = fields.Datetime(
        string='Completion Date',
        tracking=True
    )

    due_date = fields.Datetime(
        string='Due Date',
        tracking=True,
        help="When this retrieval must be completed"
    )

    # ============================================================================
    # MEASUREMENT AND ESTIMATION FIELDS
    # ============================================================================

    estimated_time = fields.Float(
        string='Estimated Time (Hours)',
        default=0.0,
        help="Estimated time to complete retrieval in hours"
    )

    actual_time = fields.Float(
        string='Actual Time (Hours)',
        default=0.0,
        help="Actual time spent on retrieval in hours"
    )

    # ============================================================================
    # CONDITION AND QUALITY FIELDS
    # ============================================================================

    condition_before = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition Before', tracking=True)

    condition_after = fields.Selection([
        ('excellent', 'Excellent'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('poor', 'Poor'),
        ('damaged', 'Damaged')
    ], string='Condition After', tracking=True)

    condition_notes = fields.Text(
        string='Condition Notes',
        help="Notes about file condition before and after retrieval"
    )

    quality_status = fields.Selection([
        ('pending', 'Pending'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('rejected', 'Rejected'),
        ('review', 'Under Review')
    ], string='Quality Status', default='pending', tracking=True,
       help="Quality assessment status for this retrieval item")

    # ============================================================================
    # NOT FOUND HANDLING FIELDS
    # ============================================================================

    not_found_reason = fields.Selection([
        ('not_in_container', 'Not in Expected Container'),
        ('container_missing', 'Container Missing'),
        ('destroyed', 'File Destroyed'),
        ('misfiled', 'Misfiled'),
        ('access_denied', 'Access Denied'),
        ('other', 'Other Reason')
    ], string='Not Found Reason', tracking=True)

    not_found_notes = fields.Text(
        string='Not Found Notes',
        help="Detailed explanation of why file was not found"
    )

    # ============================================================================
    # DELIVERY AND OUTPUT FIELDS
    # ============================================================================

    delivery_method = fields.Selection([
        ('scan', 'Digital Scan'),
        ('copy', 'Physical Copy'),
        ('original', 'Original Document'),
        ('pickup', 'Customer Pickup'),
        ('mail', 'Mail Delivery'),
        ('email', 'Email Delivery')
    ], string='Delivery Method', default='scan', tracking=True)

    delivery_address = fields.Text(
        string='Delivery Address',
        help="Specific delivery address if different from customer address"
    )

    delivery_instructions = fields.Text(
        string='Delivery Instructions',
        help="Special instructions for delivery"
    )

    # ============================================================================
    # NOTES AND COMMUNICATION FIELDS
    # ============================================================================

    notes = fields.Text(
        string='Internal Notes',
        help="Internal notes and comments"
    )

    customer_notes = fields.Text(
        string='Customer Notes',
        help="Notes provided by the customer"
    )

    search_notes = fields.Text(
        string='Search Notes',
        help="Notes from the search process"
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_overdue_status'
    )

    days_since_request = fields.Integer(
        string='Days Since Request',
        compute='_compute_days_since_request'
    )

    search_attempt_count = fields.Integer(
        string='Search Attempt Count',
        compute='_compute_search_attempt_count'
    )

    # ============================================================================
    # COMPUTED FIELD METHODS
    # ============================================================================

    @api.depends('name', 'barcode', 'status')
    def _compute_display_name(self):
        """Compute display name for the record"""
        for record in self:
            name_parts = [record.name or 'File Retrieval Item']
            if record.barcode:
                name_parts.append(f'[{record.barcode}]')
            if record.status:
                status_dict = dict(record._fields['status'].selection)
                name_parts.append(f'({status_dict.get(record.status, record.status)})')
            record.display_name = ' '.join(name_parts)

    @api.depends('due_date')
    def _compute_overdue_status(self):
        """Compute if the item is overdue"""
        now = fields.Datetime.now()
        for record in self:
            record.is_overdue = record.due_date and record.due_date < now and record.status not in ['completed', 'cancelled']

    @api.depends('request_date')
    def _compute_days_since_request(self):
        """Compute days since request was made"""
        now = fields.Datetime.now()
        for record in self:
            if record.request_date:
                delta = now - record.request_date
                record.days_since_request = delta.days
            else:
                record.days_since_request = 0

    @api.depends('search_attempt_ids')
    def _compute_search_attempt_count(self):
        """Compute number of search attempts"""
        for record in self:
            record.search_attempt_count = len(record.search_attempt_ids)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================

    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update location when container changes"""
        if self.container_id:
            if hasattr(self.container_id, 'current_location'):
                self.current_location = self.container_id.current_location
            if hasattr(self.container_id, 'location_id'):
                self.location_id = self.container_id.location_id

    @api.onchange('status')
    def _onchange_status(self):
        """Update fields when status changes"""
        if self.status == 'retrieved':
            self.retrieval_date = fields.Datetime.now()
            self.retrieved_by_id = self.env.user

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================

    @api.constrains('partner_id', 'status')
    def _check_partner_required(self):
        """Ensure partner is set for non-cancelled items"""
        for record in self:
            if record.status != 'cancelled' and not record.partner_id:
                raise ValidationError(_("Customer is required for all retrieval items except cancelled ones."))

    @api.constrains('estimated_time', 'actual_time')
    def _check_time_values(self):
        """Ensure time values are not negative"""
        for record in self:
            if record.estimated_time < 0:
                raise ValidationError(_("Estimated time cannot be negative."))
            if record.actual_time < 0:
                raise ValidationError(_("Actual time cannot be negative."))

    @api.constrains('due_date', 'request_date')
    def _check_date_logic(self):
        """Ensure due date is after request date"""
        for record in self:
            if record.due_date and record.request_date and record.due_date < record.request_date:
                raise ValidationError(_("Due date cannot be before request date."))

    # ============================================================================
    # CRUD METHODS
    # ============================================================================

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('file.retrieval.item') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # STATUS UPDATE METHODS
    # ============================================================================

    def action_start_search(self):
        """Start search process for the file"""
        self.ensure_one()
        if self.status not in ['pending']:
            raise UserError(_("You can only start search for items in 'Pending' status."))

        self.write({
            'status': 'searching',
            'search_start_date': fields.Datetime.now(),
            'user_id': self.env.user.id
        })
        self.message_post(body=_("File search has been initiated."))
        return True

    def action_mark_located(self):
        """Mark file as located"""
        self.ensure_one()
        if self.status not in ['pending', 'searching']:
            raise UserError(_("You can only mark items as located from 'Pending' or 'Searching' status."))

        self.write({
            'status': 'located',
            'retrieval_date': fields.Datetime.now()
        })
        self.message_post(body=_("File has been located."))
        return True

    def action_mark_retrieved(self):
        """Mark file as retrieved"""
        self.ensure_one()
        if self.status not in ['located']:
            raise UserError(_("You can only mark items as retrieved from 'Located' status."))

        self.write({
            'status': 'retrieved',
            'retrieval_date': fields.Datetime.now(),
            'retrieved_by_id': self.env.user.id
        })
        self.message_post(body=_("File has been retrieved."))
        return True

    def action_mark_completed(self):
        """Mark retrieval as completed"""
        self.ensure_one()
        if self.status not in ['retrieved', 'packaged', 'delivered']:
            raise UserError(_("You can only mark items as completed from 'Retrieved', 'Packaged', or 'Delivered' status."))

        self.write({
            'status': 'completed',
            'completion_date': fields.Datetime.now()
        })
        self.message_post(body=_("File retrieval has been completed."))
        return True

    def action_mark_not_found(self, reason='not_in_container', notes=None):
        """Mark file as not found"""
        self.ensure_one()
        if not notes:
            notes = _("File not found after search on %s") % fields.Datetime.now().strftime('%Y-%m-%d %H:%M')

        self.write({
            'status': 'not_found',
            'not_found_reason': reason,
            'not_found_notes': notes
        })
        self.message_post(body=_("File marked as not found: %s") % notes)
        return True

    def action_cancel(self):
        """Cancel the retrieval request"""
        self.ensure_one()
        if self.status in ['completed', 'delivered']:
            raise UserError(_("Cannot cancel completed or delivered items."))

        self.write({'status': 'cancelled'})
        self.message_post(body=_("File retrieval has been cancelled."))
        return True

    # ============================================================================
    # FILE SEARCH METHODS
    # ============================================================================

    def action_start_file_search(self):
        """Start the file search process"""
        self.ensure_one()
        if self.status not in ['pending']:
            raise UserError(_("You can only begin a search for items in the 'Pending' state."))

        return self.action_start_search()

    def action_log_container_search(self, container, found=False, notes=""):
        """Log a container search attempt"""
        self.ensure_one()
        if self.status != 'searching':
            raise UserError(_("You can only record search attempts for items in the 'Searching' state."))

        # Create search attempt record if model exists
        try:
            self.env['document.search.attempt'].create({
                'retrieval_item_id': self.id,
                'container_id': container.id,
                'found': found,
                'search_notes': notes,
                'requested_file_name': self.requested_file_name,
            })
        except Exception:
            # If search attempt model doesn't exist, just log to notes
            search_note = _("Searched container %s: %s. %s") % (
                container.name,
                _("Found") if found else _("Not found"),
                notes
            )
            current_notes = self.search_notes or ""
            self.search_notes = f"{current_notes}\n{search_note}".strip()

        # Add to searched containers
        self.write({'searched_container_ids': [(4, container.id)]})

        if found:
            self.write({
                'status': 'located',
                'discovery_container_id': container.id,
            })
            self.message_post(body=_("File located in container %s") % container.name)
        else:
            self.message_post(body=_("Container %s searched. File not found") % container.name)

        return True

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================

    @api.model
    def find_by_status(self, status_list):
        """Find items by status"""
        return self.search([('status', 'in', status_list)])

    @api.model
    def find_by_partner(self, partner_id):
        """Find items by partner"""
        return self.search([('partner_id', '=', partner_id)])

    @api.model
    def get_high_priority_items(self):
        """Get high priority items"""
        return self.search([
            ('priority', 'in', ['2', '3']),
            ('status', 'not in', ['completed', 'cancelled'])
        ])

    def get_status_color(self):
        """Get color for status display"""
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
        """Get color for priority display"""
        color_map = {
            '0': 'secondary',  # Low
            '1': 'info',       # Normal
            '2': 'warning',    # High
            '3': 'danger'      # Very High
        }
        return color_map.get(self.priority, 'info')

    def log_activity(self, activity_type, message):
        """Log an activity for tracking"""
        self.ensure_one()
        self.message_post(
            body=message,
            message_type='notification'
        )
        return True
