from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
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

    # Additional computed fields for enhanced workflow management
    urgency_score = fields.Integer(string='Urgency Score', compute='_compute_urgency_score', store=True,
                                  help="Calculated urgency score for prioritizing work orders")
    days_until_scheduled = fields.Integer(string='Days Until Scheduled', compute='_compute_days_until_scheduled', store=True)
    actual_duration_hours = fields.Float(string='Actual Duration (Hours)', compute='_compute_actual_duration_hours', store=True)

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'item_count')
    def _compute_display_name(self):
        """Compute display name with null safety and comprehensive formatting"""
        for record in self:
            try:
                name = record.name or _('New')
                partner_name = record.partner_id.name if record.partner_id else _('No Customer')

                if record.item_count and record.item_count > 0:
                    record.display_name = _("%s - %s (%s files)") % (name, partner_name, record.item_count)
                else:
                    record.display_name = _("%s - %s") % (name, partner_name)
            except Exception as e:
                # Fallback display name in case of any error
                record.display_name = record.name or _("File Retrieval Work Order")

    @api.depends('retrieval_item_ids', 'retrieval_item_ids.estimated_pages')
    def _compute_item_metrics(self):
        """Compute item metrics with enhanced null safety and validation"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                record.item_count = len(items) if items else 0

                if items:
                    # Calculate estimated pages with null safety
                    estimated_pages = 0
                    for item in items:
                        try:
                            pages = item.estimated_pages or 0
                            estimated_pages += pages
                        except (AttributeError, TypeError, ValueError):
                            continue  # Skip items with invalid page counts
                    record.estimated_pages = estimated_pages
                else:
                    record.estimated_pages = 0
            except Exception as e:
                # Fallback values in case of error
                record.item_count = 0
                record.estimated_pages = 0

    @api.depends('retrieval_item_ids.container_id', 'retrieval_item_ids.container_id.storage_location_id')
    def _compute_related_containers(self):
        """Compute related containers and locations with null safety"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                if items:
                    # Get containers with null safety
                    containers = self.env['records.container']
                    locations = self.env['records.location']

                    for item in items:
                        if item.container_id:
                            containers |= item.container_id
                            if item.container_id.storage_location_id:
                                locations |= item.container_id.storage_location_id

                    record.container_ids = [(6, 0, containers.ids)]
                    record.location_ids = [(6, 0, locations.ids)]
                else:
                    record.container_ids = [(6, 0, [])]
                    record.location_ids = [(6, 0, [])]
            except Exception as e:
                # Fallback to empty relations
                record.container_ids = [(6, 0, [])]
                record.location_ids = [(6, 0, [])]

    @api.depends('scheduled_date', 'item_count', 'priority', 'access_coordination_needed')
    def _compute_estimated_completion(self):
        """Compute estimated completion with business logic and null safety"""
        for record in self:
            try:
                if not record.scheduled_date:
                    record.estimated_completion_date = False
                    continue

                item_count = record.item_count or 0

                # Base time calculation
                base_hours = 4  # Minimum time for any retrieval

                # Add time per item (varies by priority)
                if record.priority == '2':  # High priority - faster processing
                    hours_per_item = 1.5
                elif record.priority == '0':  # Low priority - slower processing
                    hours_per_item = 3
                else:  # Normal priority
                    hours_per_item = 2

                total_hours = base_hours + (item_count * hours_per_item)

                # Add extra time for coordination
                if record.access_coordination_needed:
                    total_hours += 8  # Add full day for coordination

                # Calculate estimated completion
                record.estimated_completion_date = record.scheduled_date + timedelta(hours=total_hours)
            except Exception as e:
                # Fallback to basic calculation
                if record.scheduled_date and record.item_count:
                    record.estimated_completion_date = record.scheduled_date + timedelta(hours=24)
                else:
                    record.estimated_completion_date = False

    @api.depends('files_retrieved_count', 'item_count')
    def _compute_progress(self):
        """Compute progress percentage with null safety and validation"""
        for record in self:
            try:
                item_count = record.item_count or 0
                retrieved_count = record.files_retrieved_count or 0

                if item_count > 0:
                    progress = (retrieved_count / item_count) * 100
                    # Ensure progress stays within 0-100% bounds
                    record.progress_percentage = max(0.0, min(100.0, progress))
                else:
                    record.progress_percentage = 0.0
            except Exception as e:
                # Fallback to 0% progress
                record.progress_percentage = 0.0

    @api.depends('retrieval_item_ids.status')
    def _update_progress_metrics(self):
        """Update progress metrics with comprehensive status tracking"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                if not items:
                    record.files_located_count = 0
                    record.files_retrieved_count = 0
                    record.files_quality_approved_count = 0
                    continue

                # Count items in each status with null safety
                located_count = 0
                retrieved_count = 0
                approved_count = 0

                for item in items:
                    try:
                        status = item.status if hasattr(item, 'status') else None
                        if status:
                            if status in ['located', 'retrieved', 'packaged', 'delivered']:
                                located_count += 1
                            if status in ['retrieved', 'packaged', 'delivered']:
                                retrieved_count += 1
                            if status in ['packaged', 'delivered']:
                                approved_count += 1
                    except (AttributeError, TypeError, ValueError):
                        continue  # Skip items with invalid status

                record.files_located_count = located_count
                record.files_retrieved_count = retrieved_count
                record.files_quality_approved_count = approved_count
            except Exception as e:
                # Fallback to zero counts
                record.files_located_count = 0
                record.files_retrieved_count = 0
                record.files_quality_approved_count = 0

    @api.depends('state', 'priority', 'access_coordination_needed', 'item_count')
    def _compute_urgency_score(self):
        """Compute urgency score for work order prioritization"""
        for record in self:
            try:
                score = 0

                # Base score from priority
                priority_scores = {'0': 10, '1': 20, '2': 30}
                score += priority_scores.get(record.priority or '1', 20)

                # Add score for item count (more items = higher urgency)
                item_count = record.item_count or 0
                if item_count > 50:
                    score += 20
                elif item_count > 20:
                    score += 10
                elif item_count > 5:
                    score += 5

                # Add score for coordination needed
                if record.access_coordination_needed:
                    score += 15

                # Add score based on state (active work orders have higher urgency)
                state_scores = {
                    'draft': 0,
                    'confirmed': 5,
                    'locating': 25,
                    'retrieving': 30,
                    'packaging': 20,
                    'delivered': 10,
                    'completed': 0,
                    'cancelled': 0
                }
                score += state_scores.get(record.state, 0)

                record.urgency_score = score
            except Exception as e:
                record.urgency_score = 20  # Default medium urgency

    @api.depends('scheduled_date')
    def _compute_days_until_scheduled(self):
        """Compute days until scheduled date for planning purposes"""
        for record in self:
            try:
                if record.scheduled_date:
                    today = fields.Date.today()
                    scheduled_date = record.scheduled_date.date()
                    delta = (scheduled_date - today).days
                    record.days_until_scheduled = delta
                else:
                    record.days_until_scheduled = 0
            except Exception as e:
                record.days_until_scheduled = 0

    @api.depends('actual_start_date', 'actual_completion_date')
    def _compute_actual_duration_hours(self):
        """Compute actual duration in hours for completed work orders"""
        for record in self:
            try:
                if record.actual_start_date and record.actual_completion_date:
                    delta = record.actual_completion_date - record.actual_start_date
                    record.actual_duration_hours = delta.total_seconds() / 3600.0
                else:
                    record.actual_duration_hours = 0.0
            except Exception as e:
                record.actual_duration_hours = 0.0

    # ============================================================================
    # CONSTRAINT VALIDATION METHODS
    # ============================================================================
    @api.constrains('scheduled_date', 'actual_start_date', 'actual_completion_date')
    def _check_date_consistency(self):
        """Validate logical consistency of date fields"""
        for record in self:
            now = fields.Datetime.now()

            # Scheduled date should not be in the past (allow same day)
            if record.scheduled_date and record.scheduled_date.date() < now.date():
                raise ValidationError(_("Scheduled date cannot be in the past."))

            # Actual start date should not be after actual completion date
            if record.actual_start_date and record.actual_completion_date:
                if record.actual_start_date > record.actual_completion_date:
                    raise ValidationError(_("Actual start date cannot be after actual completion date."))

            # For completed work orders, actual completion date is required
            if record.state == 'completed' and not record.actual_completion_date:
                raise ValidationError(_("Actual completion date is required for completed work orders."))

    @api.constrains('progress_percentage')
    def _check_progress_percentage(self):
        """Validate progress percentage is within valid range"""
        for record in self:
            if record.progress_percentage < 0.0 or record.progress_percentage > 100.0:
                raise ValidationError(_("Progress percentage must be between 0% and 100%."))

    @api.constrains('files_located_count', 'files_retrieved_count', 'files_quality_approved_count', 'item_count')
    def _check_progress_metrics_consistency(self):
        """Validate that progress metrics are consistent with item count"""
        for record in self:
            if record.item_count > 0:
                # Files located should not exceed total items
                if record.files_located_count > record.item_count:
                    raise ValidationError(_("Files located count cannot exceed total item count."))

                # Files retrieved should not exceed files located
                if record.files_retrieved_count > record.files_located_count:
                    raise ValidationError(_("Files retrieved count cannot exceed files located count."))

                # Files quality approved should not exceed files retrieved
                if record.files_quality_approved_count > record.files_retrieved_count:
                    raise ValidationError(_("Files quality approved count cannot exceed files retrieved count."))

    @api.constrains('delivery_method', 'packaging_type', 'delivery_address_id')
    def _check_delivery_requirements(self):
        """Validate delivery method requirements"""
        for record in self:
            if record.delivery_method == 'physical':
                # Physical delivery requires packaging type
                if not record.packaging_type:
                    raise ValidationError(_("Packaging type is required for physical delivery."))

                # Physical delivery should have delivery address
                if not record.delivery_address_id:
                    raise ValidationError(_("Delivery address is required for physical delivery."))

            elif record.delivery_method == 'scan':
                # Scan delivery doesn't need packaging
                if record.packaging_type:
                    raise ValidationError(_("Packaging type should not be set for scan delivery."))

    @api.constrains('state', 'actual_start_date')
    def _check_state_date_consistency(self):
        """Validate state transitions match actual dates"""
        for record in self:
            # Work orders in progress should have actual start date
            if record.state in ['locating', 'retrieving', 'packaging', 'delivered', 'completed']:
                if not record.actual_start_date:
                    raise ValidationError(_("Actual start date is required for work orders in progress."))

            # Draft or confirmed orders should not have actual start date
            if record.state in ['draft', 'confirmed'] and record.actual_start_date:
                raise ValidationError(_("Actual start date should only be set after work begins."))

    @api.constrains('priority', 'access_coordination_needed', 'coordinator_id')
    def _check_coordination_requirements(self):
        """Validate coordination requirements for high priority work orders"""
        for record in self:
            # High priority work orders requiring coordination must have coordinator
            if record.priority == '2' and record.access_coordination_needed:
                if not record.coordinator_id:
                    raise ValidationError(_("High priority work orders requiring coordination must have an assigned coordinator."))

    @api.constrains('partner_id', 'delivery_address_id')
    def _check_delivery_address_relationship(self):
        """Validate delivery address belongs to customer or is the customer"""
        for record in self:
            if record.delivery_address_id and record.partner_id:
                # Delivery address must be customer or child of customer
                if (record.delivery_address_id.id != record.partner_id.id and
                    record.delivery_address_id.parent_id.id != record.partner_id.id):
                    raise ValidationError(_("Delivery address must belong to the customer."))

    @api.constrains('estimated_pages', 'item_count')
    def _check_estimated_pages_reasonable(self):
        """Validate estimated pages is reasonable for item count"""
        for record in self:
            if record.item_count > 0 and record.estimated_pages > 0:
                pages_per_item = record.estimated_pages / record.item_count

                # Warn if pages per item seems unreasonable (over 1000 pages per item)
                if pages_per_item > 1000:
                    raise ValidationError(_("Estimated pages per item (%d) seems unreasonably high. Please verify.") % pages_per_item)

    @api.constrains('state')
    def _check_state_transitions(self):
        """Validate state transitions follow business rules"""
        for record in self:
            # Define valid state transitions
            valid_transitions = {
                'draft': ['confirmed', 'cancelled'],
                'confirmed': ['locating', 'cancelled'],
                'locating': ['retrieving', 'cancelled'],
                'retrieving': ['packaging', 'cancelled'],
                'packaging': ['delivered', 'cancelled'],
                'delivered': ['completed'],
                'completed': [],  # Terminal state
                'cancelled': [],  # Terminal state
            }

            # For new records, any initial state is allowed
            if not record._origin:
                continue

            old_state = record._origin.state
            new_state = record.state

            # Check if transition is valid
            if old_state != new_state:
                if new_state not in valid_transitions.get(old_state, []):
                    raise ValidationError(_("Invalid state transition from '%s' to '%s'.") % (old_state, new_state))

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
        """Confirm work order with enhanced validation and notifications"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft work orders can be confirmed."))

        # Enhanced validation before confirmation
        if not self.retrieval_item_ids:
            raise UserError(_("Cannot confirm work order without retrieval items."))

        if self.access_coordination_needed and not self.coordinator_id:
            raise UserError(_("Coordinator must be assigned for work orders requiring access coordination."))

        # Update state and create audit log
        self.write({'state': 'confirmed'})
        self._create_naid_audit_log('work_order_confirmed')

        # Enhanced notification with work order details
        message_body = _(
            "File retrieval work order confirmed for %s\n"
            "Items: %s\n"
            "Estimated pages: %s\n"
            "Priority: %s\n"
            "Scheduled: %s"
        ) % (
            self.partner_id.name,
            self.item_count,
            self.estimated_pages,
            dict(self._fields['priority'].selection).get(self.priority, 'Unknown'),
            self.scheduled_date.strftime('%Y-%m-%d %H:%M') if self.scheduled_date else 'Not scheduled'
        )

        self.message_post(body=message_body, message_type='notification')

        # Notify coordinator if assigned
        if self.coordinator_id:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.coordinator_id.id,
                summary=_("File Retrieval Work Order Confirmed"),
                note=_("Work order %s has been confirmed and requires coordination.") % self.name
            )

        return True

    def action_start_locating(self):
        """Start file location process with enhanced tracking"""
        self.ensure_one()
        if self.state != 'confirmed':
            raise UserError(_("Only confirmed work orders can start file location."))

        # Validate prerequisites
        if not self.retrieval_item_ids:
            raise UserError(_("Cannot start locating without retrieval items."))

        # Update state and timestamps
        self.write({
            'state': 'locating',
            'actual_start_date': fields.Datetime.now()
        })

        # Create detailed audit log
        self._create_naid_audit_log('location_started')

        # Initialize retrieval items status
        self.retrieval_item_ids.write({'status': 'pending_location'})

        # Enhanced notification
        self.message_post(
            body=_("Started file location process. %s items to locate across %s containers.") % (
                self.item_count, len(self.container_ids)
            ),
            message_type='notification'
        )

        # Create activities for each location if coordination needed
        if self.access_coordination_needed and self.coordinator_id:
            for location in self.location_ids:
                self.activity_schedule(
                    'mail.mail_activity_data_call',
                    user_id=self.coordinator_id.id,
                    summary=_("Coordinate Access - %s") % location.name,
                    note=_("Coordinate access to location %s for work order %s") % (location.name, self.name)
                )

        return True

    def action_start_retrieving(self):
        """Start file retrieval process"""
        self.ensure_one()
        if self.state != 'locating':
            raise UserError(_("File location must be completed before retrieval."))

        # Validate that files have been located
        located_items = self.retrieval_item_ids.filtered(lambda r: r.status in ['located', 'retrieved'])
        if not located_items:
            raise UserError(_("No files have been located yet. Complete location process first."))

        self.write({'state': 'retrieving'})
        self._create_naid_audit_log('retrieval_started')

        self.message_post(
            body=_("Started file retrieval process. %s files located and ready for retrieval.") % len(located_items),
            message_type='notification'
        )

        return True

    def action_start_packaging(self):
        """Start packaging process with delivery method validation"""
        self.ensure_one()
        if self.state != 'retrieving':
            raise UserError(_("File retrieval must be completed before packaging."))

        # Validate delivery requirements
        if self.delivery_method == 'physical':
            if not self.packaging_type:
                raise UserError(_("Packaging type must be specified for physical delivery."))
            if not self.delivery_address_id:
                raise UserError(_("Delivery address must be specified for physical delivery."))

        retrieved_items = self.retrieval_item_ids.filtered(lambda r: r.status == 'retrieved')
        if not retrieved_items:
            raise UserError(_("No files have been retrieved yet."))

        self.write({'state': 'packaging'})
        self._create_naid_audit_log('packaging_started')

        # Update retrieved items status
        retrieved_items.write({'status': 'packaging'})

        message_body = _("Started packaging process for %s delivery.") % (
            dict(self._fields['delivery_method'].selection).get(self.delivery_method, 'unknown')
        )

        if self.delivery_method == 'physical':
            message_body += _("\nPackaging type: %s\nDelivery address: %s") % (
                dict(self._fields['packaging_type'].selection).get(self.packaging_type, 'unknown'),
                self.delivery_address_id.name
            )

        self.message_post(body=message_body, message_type='notification')

        return True

    def action_mark_delivered(self):
        """Mark work order as delivered with quality validation"""
        self.ensure_one()
        if self.state != 'packaging':
            raise UserError(_("Packaging must be completed before delivery."))

        # Quality check - ensure all items are properly packaged
        packaged_items = self.retrieval_item_ids.filtered(lambda r: r.status == 'packaged')
        if len(packaged_items) != self.item_count:
            raise UserError(_("All items must be packaged before marking as delivered."))

        self.write({'state': 'delivered'})
        self._create_naid_audit_log('delivery_completed')

        # Update all items to delivered status
        self.retrieval_item_ids.write({'status': 'delivered'})

        # Enhanced delivery notification
        delivery_details = _("Work order delivered successfully.")
        if self.delivery_method == 'scan':
            delivery_details += _("\nFiles scanned and emailed to: %s") % self.partner_id.email
        else:
            delivery_details += _("\nPhysical delivery to: %s") % self.delivery_address_id.display_name

        self.message_post(body=delivery_details, message_type='notification')

        # Create customer notification activity
        self.activity_schedule(
            'mail.mail_activity_data_email',
            user_id=self.user_id.id,
            summary=_("Notify Customer - Delivery Complete"),
            note=_("Notify customer that work order %s has been delivered.") % self.name
        )

        return True

    def action_complete(self):
        """Complete work order with comprehensive finalization"""
        self.ensure_one()
        if self.state != 'delivered':
            raise UserError(_("Only delivered work orders can be completed."))

        # Final validation
        if not all(item.status == 'delivered' for item in self.retrieval_item_ids):
            raise UserError(_("All retrieval items must be delivered before completion."))

        completion_date = fields.Datetime.now()
        self.write({
            'state': 'completed',
            'actual_completion_date': completion_date
        })

        # Create comprehensive audit log
        self._create_naid_audit_log('work_order_completed')

        # Calculate performance metrics
        if self.actual_start_date:
            duration = completion_date - self.actual_start_date
            duration_hours = duration.total_seconds() / 3600
        else:
            duration_hours = 0

        # Enhanced completion notification with metrics
        completion_message = _(
            "File retrieval work order completed successfully.\n"
            "Items delivered: %s\n"
            "Total pages: %s\n"
            "Duration: %.1f hours\n"
            "Customer: %s"
        ) % (
            self.item_count,
            self.estimated_pages,
            duration_hours,
            self.partner_id.name
        )

        self.message_post(body=completion_message, message_type='notification')

        # Auto-create invoice if rate is specified
        if self.rate_id and not self.invoice_id:
            self._create_invoice()

        return True

    def action_cancel(self):
        """Cancel work order with reason tracking"""
        self.ensure_one()
        if self.state in ['completed', 'cancelled']:
            raise UserError(_("Cannot cancel completed or already cancelled work orders."))

        # Get cancellation reason from context or prompt
        cancel_reason = self.env.context.get('cancel_reason', 'Cancelled by user')

        self.write({'state': 'cancelled'})
        self._create_naid_audit_log('work_order_cancelled')

        # Cancel all related activities
        self.activity_ids.action_close_dialog()

        # Update retrieval items status
        self.retrieval_item_ids.write({'status': 'cancelled'})

        self.message_post(
            body=_("Work order cancelled. Reason: %s") % cancel_reason,
            message_type='notification'
        )

        return True

    def action_view_retrieval_items(self):
        """View retrieval items with enhanced context"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Retrieval Items - %s") % self.name,
            "res_model": "file.retrieval.item",
            "view_mode": "tree,form",
            "domain": [("work_order_id", "=", self.id)],
            "context": {
                "default_work_order_id": self.id,
                "default_partner_id": self.partner_id.id,
                "group_by": "status",
                "search_default_group_status": 1,
            },
            "target": "current",
        }

    def action_view_containers(self):
        """View related containers"""
        self.ensure_one()
        if not self.container_ids:
            raise UserError(_("No containers are associated with this work order."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Containers - %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.container_ids.ids)],
            "context": {"create": False},
            "target": "current",
        }

    def action_view_locations(self):
        """View related storage locations"""
        self.ensure_one()
        if not self.location_ids:
            raise UserError(_("No storage locations are associated with this work order."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Locations - %s") % self.name,
            "res_model": "records.location",
            "view_mode": "tree,form",
            "domain": [("id", "in", self.location_ids.ids)],
            "context": {"create": False},
            "target": "current",
        }

    # ============================================================================
    # BUSINESS WORKFLOW METHODS
    # ============================================================================
    def _create_invoice(self):
        """Create invoice for file retrieval work order"""
        self.ensure_one()
        if not self.rate_id or self.invoice_id:
            return False

        try:
            # Calculate invoice amount based on rate and items/pages
            if self.rate_id.rate_type == 'per_page':
                amount = self.estimated_pages * self.rate_id.amount
                description = _("File retrieval - %s pages at %s per page") % (
                    self.estimated_pages, self.rate_id.amount
                )
            elif self.rate_id.rate_type == 'per_item':
                amount = self.item_count * self.rate_id.amount
                description = _("File retrieval - %s items at %s per item") % (
                    self.item_count, self.rate_id.amount
                )
            else:
                amount = self.rate_id.amount
                description = _("File retrieval - flat rate")

            # Create invoice
            invoice_vals = {
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_line_ids': [(0, 0, {
                    'name': description,
                    'quantity': 1,
                    'price_unit': amount,
                })],
            }

            invoice = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice.id

            self.message_post(
                body=_("Invoice created for %s - Amount: %s") % (description, amount),
                message_type='notification'
            )

            return invoice
        except Exception as e:
            # Log error but don't fail the completion
            self.message_post(
                body=_("Failed to create invoice: %s") % str(e),
                message_type='notification'
            )
            return False

    def _create_naid_audit_log(self, event_type):
        """Create NAID audit log for work order events with enhanced details"""
        if self.env["ir.module.module"].search([
            ("name", "=", "records_management"),
            ("state", "=", "installed")
        ]):
            try:
                audit_data = {
                    "event_type": event_type,
                    "model_name": self._name,
                    "record_id": self.id,
                    "partner_id": self.partner_id.id,
                    "description": _("Work order: %s - %s items") % (self.name, self.item_count),
                    "user_id": self.env.user.id,
                    "timestamp": fields.Datetime.now(),
                    "metadata": {
                        "state": self.state,
                        "priority": self.priority,
                        "item_count": self.item_count,
                        "estimated_pages": self.estimated_pages,
                        "delivery_method": self.delivery_method,
                    }
                }

                self.env["naid.audit.log"].create(audit_data)
            except Exception as e:
                # Don't fail the main operation if audit logging fails
                pass

    def _send_customer_notification(self, message_type, additional_context=None):
        """Send notification to customer about work order progress"""
        self.ensure_one()

        context = {
            'work_order_name': self.name,
            'customer_name': self.partner_id.name,
            'state': self.state,
            'item_count': self.item_count,
            'estimated_pages': self.estimated_pages,
        }

        if additional_context:
            context.update(additional_context)

        # Create email activity or send direct notification based on preferences
        try:
            template_name = f"file_retrieval_{message_type}_template"
            template = self.env.ref(f"records_management.{template_name}", raise_if_not_found=False)

            if template:
                template.with_context(context).send_mail(self.id)
            else:
                # Fallback to activity creation
                self.activity_schedule(
                    'mail.mail_activity_data_email',
                    user_id=self.user_id.id,
                    summary=_("Send Customer Notification"),
                    note=_("Send %s notification to %s for work order %s") % (
                        message_type, self.partner_id.name, self.name
                    )
                )
        except Exception as e:
            # Don't fail the main operation if notification fails
            pass

    def _update_progress_from_items(self):
        """Update work order progress based on retrieval item status changes"""
        self.ensure_one()

        # This method can be called from retrieval items to update parent progress
        self._update_progress_metrics()
        self._compute_progress()

        # Auto-advance state if all items reach certain status
        if self.state == 'locating' and all(item.status in ['located', 'retrieved'] for item in self.retrieval_item_ids):
            self.action_start_retrieving()
        elif self.state == 'retrieving' and all(item.status == 'retrieved' for item in self.retrieval_item_ids):
            self.action_start_packaging()
        elif self.state == 'packaging' and all(item.status == 'packaged' for item in self.retrieval_item_ids):
            self.action_mark_delivered()

    def get_work_order_summary(self):
        """Get comprehensive work order summary for reporting"""
        self.ensure_one()

        summary = {
            'work_order_id': self.id,
            'name': self.name,
            'customer': self.partner_id.name,
            'state': self.state,
            'priority': self.priority,
            'item_count': self.item_count,
            'estimated_pages': self.estimated_pages,
            'progress_percentage': self.progress_percentage,
            'scheduled_date': self.scheduled_date,
            'actual_start_date': self.actual_start_date,
            'actual_completion_date': self.actual_completion_date,
            'delivery_method': self.delivery_method,
            'containers_count': len(self.container_ids),
            'locations_count': len(self.location_ids),
            'urgency_score': getattr(self, 'urgency_score', 0),
            'days_until_scheduled': getattr(self, 'days_until_scheduled', 0),
            'actual_duration_hours': getattr(self, 'actual_duration_hours', 0),
        }

        return summary

