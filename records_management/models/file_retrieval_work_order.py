from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError
from datetime import timedelta, datetime


class FileRetrievalWorkOrder(models.Model):
    _name = 'file.retrieval.work.order'
    _description = 'Complete File Retrieval Work Order Management'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, urgency_score desc, scheduled_date asc, name'
    _rec_name = 'display_name'
    _check_company_auto = True

    # ============================================================================
    # FIELDS - CORE IDENTIFICATION
    # ============================================================================
    name = fields.Char(
        string="Work Order #",
        required=True,
        index=True,
        copy=False,
        default=lambda self: _('New'),
        tracking=True,
        help="Unique identifier for the file retrieval work order"
    )

    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Formatted display name showing work order number, customer, and item count"
    )

    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True,
        index=True
    )

    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        default=lambda self: self.env.user,
        tracking=True,
        required=True,
        help="User responsible for overseeing this work order"
    )

    active = fields.Boolean(string='Active', default=True, tracking=True)

    # ============================================================================
    # FIELDS - STATE AND WORKFLOW
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('locating', 'Locating Files'),
        ('retrieving', 'Retrieving Files'),
        ('packaging', 'Packaging'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ],
        string='Status',
        default='draft',
        tracking=True,
        required=True,
        index=True,
        help="Current status of the file retrieval work order"
    )

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ],
        string='Priority',
        default='1',
        tracking=True,
        required=True,
        help="Priority level for work order scheduling and resource allocation"
    )

    # ============================================================================
    # FIELDS - CUSTOMER AND REQUEST INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        index=True,
        help="Customer requesting the file retrieval service"
    )

    portal_request_id = fields.Many2one(
        'portal.request',
        string='Portal Request',
        help="Associated portal request if work order originated from customer portal"
    )

    request_description = fields.Text(
        string='Request Description',
        required=True,
        help="Detailed description of files and documents to be retrieved"
    )

    request_date = fields.Datetime(
        string='Request Date',
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help="Date and time when the retrieval request was submitted"
    )

    # ============================================================================
    # FIELDS - RETRIEVAL ITEMS AND METRICS
    # ============================================================================
    retrieval_item_ids = fields.One2many(
        'file.retrieval.item',
        'work_order_id',
        string='Retrieval Items',
        help="Individual files and documents to be retrieved as part of this work order"
    )

    item_count = fields.Integer(
        string="Item Count",
        compute='_compute_item_metrics',
        store=True,
        help="Total number of files/documents to be retrieved"
    )

    estimated_pages = fields.Integer(
        string="Estimated Pages",
        compute='_compute_item_metrics',
        store=True,
        help="Total estimated number of pages across all retrieval items"
    )

    estimated_weight_kg = fields.Float(
        string="Estimated Weight (kg)",
        compute='_compute_physical_metrics',
        store=True,
        help="Estimated total weight of physical documents"
    )

    estimated_box_count = fields.Integer(
        string="Estimated Boxes",
        compute='_compute_physical_metrics',
        store=True,
        help="Estimated number of boxes/containers needed for physical delivery"
    )

    # ============================================================================
    # FIELDS - CONTAINER AND LOCATION TRACKING
    # ============================================================================
    container_ids = fields.Many2many(
        'records.container',
        string='Related Containers',
        compute='_compute_related_containers',
        store=True,
        help="Storage containers where requested files are located"
    )

    location_ids = fields.Many2many(
        'records.location',
        string='Related Locations',
        compute='_compute_related_containers',
        store=True,
        help="Storage locations that need to be accessed for file retrieval"
    )

    unique_locations_count = fields.Integer(
        string="Unique Locations",
        compute='_compute_location_metrics',
        store=True,
        help="Number of distinct storage locations to visit"
    )

    access_coordination_needed = fields.Boolean(
        string='Access Coordination Required',
        tracking=True,
        help="Indicates if special access coordination is needed for restricted areas"
    )

    # ============================================================================
    # FIELDS - SCHEDULING AND TIMING
    # ============================================================================
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        tracking=True,
        help="Planned date and time for work order execution"
    )

    estimated_completion_date = fields.Datetime(
        string='Estimated Completion',
        compute='_compute_estimated_completion',
        store=True,
        help="Calculated estimated completion date based on workload and priority"
    )

    actual_start_date = fields.Datetime(
        string='Actual Start Date',
        tracking=True,
        help="Actual date and time when work order execution began"
    )

    actual_completion_date = fields.Datetime(
        string='Actual Completion Date',
        tracking=True,
        help="Actual date and time when work order was completed"
    )

    deadline_date = fields.Datetime(
        string='Deadline',
        tracking=True,
        help="Customer-requested or business-required deadline for completion"
    )

    # ============================================================================
    # FIELDS - DELIVERY AND PACKAGING
    # ============================================================================
    delivery_method = fields.Selection([
        ('scan', 'Scan & Email'),
        ('physical', 'Physical Delivery'),
        ('pickup', 'Customer Pickup'),
        ('courier', 'Courier Service')
    ],
        string='Delivery Method',
        tracking=True,
        help="Method for delivering retrieved files to customer"
    )

    packaging_type = fields.Selection([
        ('box', 'Standard Box'),
        ('envelope', 'Document Envelope'),
        ('tube', 'Document Tube'),
        ('binder', 'Ring Binder'),
        ('folder', 'File Folder')
    ],
        string='Packaging Type',
        help="Type of packaging for physical delivery"
    )

    delivery_address_id = fields.Many2one(
        'res.partner',
        string='Delivery Address',
        help="Address where physical documents should be delivered"
    )

    delivery_instructions = fields.Text(
        string='Delivery Instructions',
        help="Special instructions for delivery (e.g., security requirements, access codes)"
    )

    delivery_contact_id = fields.Many2one(
        'res.partner',
        string='Delivery Contact',
        help="Specific contact person for delivery coordination"
    )

    delivery_phone = fields.Char(
        string='Delivery Phone',
        help="Phone number for delivery coordination"
    )

    # ============================================================================
    # FIELDS - PROGRESS TRACKING
    # ============================================================================
    progress_percentage = fields.Float(
        string='Progress %',
        compute='_compute_progress',
        store=True,
        aggregator='avg',
        help="Overall completion percentage of the work order"
    )

    files_located_count = fields.Integer(
        string='Files Located',
        compute='_compute_progress_metrics',
        store=True,
        help="Number of files that have been physically located"
    )

    files_retrieved_count = fields.Integer(
        string='Files Retrieved',
        compute='_compute_progress_metrics',
        store=True,
        help="Number of files that have been retrieved from storage"
    )

    files_quality_approved_count = fields.Integer(
        string='Files Quality Approved',
        compute='_compute_progress_metrics',
        store=True,
        help="Number of files that have passed quality control"
    )

    files_packaged_count = fields.Integer(
        string='Files Packaged',
        compute='_compute_progress_metrics',
        store=True,
        help="Number of files that have been packaged for delivery"
    )

    files_delivered_count = fields.Integer(
        string='Files Delivered',
        compute='_compute_progress_metrics',
        store=True,
        help="Number of files that have been delivered to customer"
    )

    # ============================================================================
    # FIELDS - TEAM AND COORDINATION
    # ============================================================================
    coordinator_id = fields.Many2one(
        'res.users',
        string='Coordinator',
        tracking=True,
        help="Team coordinator responsible for access and logistics coordination"
    )

    retrieval_team_ids = fields.Many2many(
        'res.users',
        string='Retrieval Team',
        help="Team members assigned to execute the file retrieval"
    )

    quality_inspector_id = fields.Many2one(
        'res.users',
        string='Quality Inspector',
        help="User responsible for quality control of retrieved files"
    )

    # ============================================================================
    # FIELDS - FINANCIAL AND BILLING
    # ============================================================================
    rate_id = fields.Many2one(
        'base.rate',
        string='Rate',
        help="Billing rate structure for this work order"
    )

    invoice_id = fields.Many2one(
        'account.move',
        string='Invoice',
        readonly=True,
        help="Generated invoice for this work order"
    )

    estimated_cost = fields.Monetary(
        string='Estimated Cost',
        compute='_compute_financial_metrics',
        store=True,
        currency_field='currency_id',
        help="Estimated cost based on rate and item count/pages"
    )

    actual_cost = fields.Monetary(
        string='Actual Cost',
        currency_field='currency_id',
        help="Actual cost incurred for work order execution"
    )

    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # FIELDS - COMPUTED METRICS AND ANALYTICS
    # ============================================================================
    urgency_score = fields.Integer(
        string='Urgency Score',
        compute='_compute_urgency_score',
        store=True,
        help="Calculated urgency score for prioritizing work orders (higher = more urgent)"
    )

    days_until_scheduled = fields.Integer(
        string='Days Until Scheduled',
        compute='_compute_days_until_scheduled',
        store=True,
        help="Number of days until the scheduled execution date"
    )

    actual_duration_hours = fields.Float(
        string='Actual Duration (Hours)',
        compute='_compute_actual_duration_hours',
        store=True,
        help="Total hours spent on work order execution"
    )

    efficiency_rating = fields.Selection([
        ('excellent', 'Excellent (>120%)'),
        ('good', 'Good (100-120%)'),
        ('average', 'Average (80-100%)'),
        ('poor', 'Poor (<80%)')
    ],
        string='Efficiency Rating',
        compute='_compute_efficiency_rating',
        store=True,
        help="Performance rating compared to estimated completion time"
    )

    complexity_score = fields.Integer(
        string='Complexity Score',
        compute='_compute_complexity_score',
        store=True,
        help="Calculated complexity based on locations, items, and coordination needs"
    )

    # ============================================================================
    # FIELDS - QUALITY AND COMPLIANCE
    # ============================================================================
    quality_score = fields.Float(
        string='Quality Score %',
        compute='_compute_quality_metrics',
        store=True,
        help="Quality score based on accuracy and completeness"
    )

    missing_files_count = fields.Integer(
        string='Missing Files',
        compute='_compute_quality_metrics',
        store=True,
        help="Number of requested files that could not be located"
    )

    damaged_files_count = fields.Integer(
        string='Damaged Files',
        compute='_compute_quality_metrics',
        store=True,
        help="Number of files found to be damaged during retrieval"
    )

    naid_compliance_verified = fields.Boolean(
        string='NAID Compliance Verified',
        help="Indicates if NAID chain of custody requirements have been verified"
    )

    audit_trail_complete = fields.Boolean(
        string='Audit Trail Complete',
        compute='_compute_compliance_status',
        store=True,
        help="Indicates if complete audit trail documentation is available"
    )

    # ============================================================================
    # FIELDS - CUSTOMER SATISFACTION
    # ============================================================================
    customer_satisfaction_rating = fields.Selection([
        ('1', 'Very Dissatisfied'),
        ('2', 'Dissatisfied'),
        ('3', 'Neutral'),
        ('4', 'Satisfied'),
        ('5', 'Very Satisfied')
    ],
        string='Customer Satisfaction',
        help="Customer satisfaction rating for completed work order"
    )

    customer_feedback = fields.Text(
        string='Customer Feedback',
        help="Customer comments and feedback about the service"
    )

    follow_up_required = fields.Boolean(
        string='Follow-up Required',
        help="Indicates if additional follow-up action is needed"
    )

    follow_up_notes = fields.Text(
        string='Follow-up Notes',
        help="Notes about required follow-up actions"
    )

    # ============================================================================
    # FIELDS - ADDITIONAL TRACKING
    # ============================================================================
    special_instructions = fields.Text(
        string='Special Instructions',
        help="Special handling instructions for this work order"
    )

    risk_level = fields.Selection([
        ('low', 'Low Risk'),
        ('medium', 'Medium Risk'),
        ('high', 'High Risk'),
        ('critical', 'Critical Risk')
    ],
        string='Risk Level',
        compute='_compute_risk_assessment',
        store=True,
        help="Risk assessment based on item value, access requirements, and complexity"
    )

    insurance_required = fields.Boolean(
        string='Insurance Required',
        help="Indicates if special insurance coverage is required"
    )

    insurance_value = fields.Monetary(
        string='Insurance Value',
        currency_field='currency_id',
        help="Total insured value of documents being retrieved"
    )

    temperature_controlled = fields.Boolean(
        string='Temperature Controlled',
        help="Indicates if documents require temperature-controlled handling"
    )

    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('top_secret', 'Top Secret')
    ],
        string='Confidentiality Level',
        default='internal',
        help="Security classification of documents being retrieved"
    )

    # ============================================================================
    # COMPUTED METHODS - CORE DISPLAY AND METRICS
    # ============================================================================
    @api.depends('name', 'partner_id.name', 'item_count', 'state')
    def _compute_display_name(self):
        """Compute enhanced display name with status and progress indicators"""
        for record in self:
            try:
                name = record.name or _('New')
                partner_name = record.partner_id.name if record.partner_id else _('No Customer')

                # Add state indicator
                state_labels = dict(record._fields['state'].selection)
                state_label = state_labels.get(record.state, record.state)

                if record.item_count and record.item_count > 0:
                    if record.progress_percentage > 0:
                        record.display_name = _("%s - %s (%s files - %.0f%% complete)") % (
                            name, partner_name, record.item_count, record.progress_percentage
                        )
                    else:
                        record.display_name = _("%s - %s (%s files)") % (name, partner_name, record.item_count)
                else:
                    record.display_name = _("%s - %s [%s]") % (name, partner_name, state_label)
            except Exception:
                record.display_name = record.name or _("File Retrieval Work Order")

    @api.depends('retrieval_item_ids', 'retrieval_item_ids.estimated_pages')
    def _compute_item_metrics(self):
        """Compute comprehensive item metrics with enhanced validation"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                record.item_count = len(items) if items else 0

                if items:
                    # Calculate estimated pages with comprehensive null safety
                    estimated_pages = 0
                    for item in items:
                        try:
                            pages = getattr(item, 'estimated_pages', 0) or 0
                            if isinstance(pages, (int, float)) and pages >= 0:
                                estimated_pages += int(pages)
                        except (AttributeError, TypeError, ValueError):
                            continue
                    record.estimated_pages = estimated_pages
                else:
                    record.estimated_pages = 0
            except Exception:
                record.item_count = 0
                record.estimated_pages = 0

    @api.depends('retrieval_item_ids.estimated_pages', 'packaging_type')
    def _compute_physical_metrics(self):
        """Compute physical delivery metrics"""
        for record in self:
            try:
                # Estimate weight based on pages (average 5g per page)
                pages = record.estimated_pages or 0
                record.estimated_weight_kg = (pages * 5) / 1000.0  # Convert grams to kg

                # Estimate box count based on packaging type and pages
                if record.packaging_type == 'box':
                    pages_per_box = 1000  # Standard box capacity
                elif record.packaging_type == 'envelope':
                    pages_per_box = 100   # Envelope capacity
                else:
                    pages_per_box = 500   # Default capacity

                record.estimated_box_count = max(1, (pages // pages_per_box) + (1 if pages % pages_per_box else 0))
            except Exception:
                record.estimated_weight_kg = 0.0
                record.estimated_box_count = 1

    @api.depends('retrieval_item_ids.container_id', 'retrieval_item_ids.container_id.storage_location_id')
    def _compute_related_containers(self):
        """Compute related containers and locations with comprehensive null safety"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                if items:
                    containers = self.env['records.container']
                    locations = self.env['records.location']

                    for item in items:
                        try:
                            if hasattr(item, 'container_id') and item.container_id:
                                containers |= item.container_id
                                if hasattr(item.container_id, 'storage_location_id') and item.container_id.storage_location_id:
                                    locations |= item.container_id.storage_location_id
                        except (AttributeError, TypeError):
                            continue

                    record.container_ids = [(6, 0, containers.ids)]
                    record.location_ids = [(6, 0, locations.ids)]
                else:
                    record.container_ids = [(6, 0, [])]
                    record.location_ids = [(6, 0, [])]
            except Exception:
                record.container_ids = [(6, 0, [])]
                record.location_ids = [(6, 0, [])]

    @api.depends('location_ids')
    def _compute_location_metrics(self):
        """Compute location-related metrics"""
        for record in self:
            try:
                record.unique_locations_count = len(record.location_ids)
            except Exception:
                record.unique_locations_count = 0

    @api.depends('scheduled_date', 'item_count', 'priority', 'access_coordination_needed', 'complexity_score')
    def _compute_estimated_completion(self):
        """Enhanced completion time estimation with complexity factors"""
        for record in self:
            try:
                if not record.scheduled_date:
                    record.estimated_completion_date = False
                    continue

                item_count = record.item_count or 0
                base_hours = 2  # Minimum time for setup and coordination

                # Priority-based processing speed
                priority_multipliers = {'0': 1.5, '1': 1.0, '2': 0.7, '3': 0.5}
                multiplier = priority_multipliers.get(record.priority or '1', 1.0)

                # Base time per item
                hours_per_item = 1.5 * multiplier
                item_hours = item_count * hours_per_item

                # Location complexity factor
                location_factor = 1.0
                if record.unique_locations_count > 5:
                    location_factor = 1.5
                elif record.unique_locations_count > 2:
                    location_factor = 1.2

                # Coordination overhead
                coordination_hours = 0
                if record.access_coordination_needed:
                    coordination_hours = 4 + (record.unique_locations_count * 0.5)

                # Calculate total time
                total_hours = (base_hours + item_hours) * location_factor + coordination_hours

                record.estimated_completion_date = record.scheduled_date + timedelta(hours=total_hours)
            except Exception:
                if record.scheduled_date:
                    record.estimated_completion_date = record.scheduled_date + timedelta(hours=8)
                else:
                    record.estimated_completion_date = False

    @api.depends('files_retrieved_count', 'item_count', 'state')
    def _compute_progress(self):
        """Enhanced progress calculation with state-based weighting"""
        for record in self:
            try:
                item_count = record.item_count or 0
                if item_count == 0:
                    record.progress_percentage = 0.0
                    continue

                # State-based progress calculation
                state_progress = {
                    'draft': 0.0,
                    'confirmed': 5.0,
                    'locating': 10.0,
                    'retrieving': 25.0,
                    'packaging': 75.0,
                    'delivered': 95.0,
                    'completed': 100.0,
                    'cancelled': 0.0
                }

                base_progress = state_progress.get(record.state, 0.0)

                # Add item-based progress within current state
                item_progress = 0.0
                if record.state in ['locating', 'retrieving', 'packaging']:
                    retrieved_ratio = (record.files_retrieved_count or 0) / item_count
                    located_ratio = (record.files_located_count or 0) / item_count

                    if record.state == 'locating':
                        item_progress = located_ratio * 15.0  # Up to 15% for location progress
                    elif record.state == 'retrieving':
                        item_progress = retrieved_ratio * 50.0  # Up to 50% for retrieval progress
                    elif record.state == 'packaging':
                        item_progress = retrieved_ratio * 20.0  # Up to 20% for packaging progress

                total_progress = base_progress + item_progress
                record.progress_percentage = max(0.0, min(100.0, total_progress))
            except Exception:
                record.progress_percentage = 0.0

    @api.depends('retrieval_item_ids.status')
    def _compute_progress_metrics(self):
        """Comprehensive progress metrics with multiple status tracking"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                if not items:
                    record.files_located_count = 0
                    record.files_retrieved_count = 0
                    record.files_quality_approved_count = 0
                    record.files_packaged_count = 0
                    record.files_delivered_count = 0
                    continue

                # Initialize counters
                located_count = retrieved_count = approved_count = 0
                packaged_count = delivered_count = 0

                # Count items by status with comprehensive status mapping
                for item in items:
                    try:
                        status = getattr(item, 'status', None) or getattr(item, 'state', None)
                        if not status:
                            continue

                        # Status progression tracking
                        status_hierarchy = [
                            ('pending', 'draft', 'new'),
                            ('searching', 'locating'),
                            ('located', 'found'),
                            ('retrieved', 'pulled'),
                            ('quality_checked', 'approved'),
                            ('packaged', 'packed'),
                            ('delivered', 'completed', 'done')
                        ]

                        # Determine status level
                        status_level = 0
                        for level, statuses in enumerate(status_hierarchy):
                            if status in statuses:
                                status_level = level
                                break

                        # Update counters based on status level
                        if status_level >= 2:  # located or higher
                            located_count += 1
                        if status_level >= 3:  # retrieved or higher
                            retrieved_count += 1
                        if status_level >= 4:  # quality checked or higher
                            approved_count += 1
                        if status_level >= 5:  # packaged or higher
                            packaged_count += 1
                        if status_level >= 6:  # delivered
                            delivered_count += 1

                    except (AttributeError, TypeError, ValueError):
                        continue

                # Set computed values
                record.files_located_count = located_count
                record.files_retrieved_count = retrieved_count
                record.files_quality_approved_count = approved_count
                record.files_packaged_count = packaged_count
                record.files_delivered_count = delivered_count

            except Exception:
                record.files_located_count = 0
                record.files_retrieved_count = 0
                record.files_quality_approved_count = 0
                record.files_packaged_count = 0
                record.files_delivered_count = 0

    # ============================================================================
    # COMPUTED METHODS - ADVANCED ANALYTICS
    # ============================================================================
    @api.depends('state', 'priority', 'access_coordination_needed', 'item_count', 'deadline_date', 'complexity_score')
    def _compute_urgency_score(self):
        """Enhanced urgency calculation with multiple factors"""
        for record in self:
            try:
                score = 0

                # Priority base score
                priority_scores = {'0': 10, '1': 25, '2': 40, '3': 60}
                score += priority_scores.get(record.priority or '1', 25)

                # Item count factor
                item_count = record.item_count or 0
                if item_count > 100:
                    score += 30
                elif item_count > 50:
                    score += 20
                elif item_count > 20:
                    score += 15
                elif item_count > 10:
                    score += 10
                elif item_count > 5:
                    score += 5

                # Coordination complexity
                if record.access_coordination_needed:
                    score += 20

                # Deadline urgency
                if record.deadline_date:
                    try:
                        days_to_deadline = (record.deadline_date.date() - fields.Date.today()).days
                        if days_to_deadline < 0:
                            score += 50  # Overdue
                        elif days_to_deadline <= 1:
                            score += 40  # Due today/tomorrow
                        elif days_to_deadline <= 3:
                            score += 30  # Due within 3 days
                        elif days_to_deadline <= 7:
                            score += 20  # Due within a week
                        elif days_to_deadline <= 14:
                            score += 10  # Due within 2 weeks
                    except (AttributeError, TypeError, ValueError):
                        pass

                # State-based urgency
                state_scores = {
                    'draft': 0, 'confirmed': 5, 'locating': 35, 'retrieving': 40,
                    'packaging': 30, 'delivered': 15, 'completed': 0, 'cancelled': 0
                }
                score += state_scores.get(record.state, 0)

                # Complexity factor
                complexity = getattr(record, 'complexity_score', 0)
                if complexity > 80:
                    score += 25
                elif complexity > 60:
                    score += 15
                elif complexity > 40:
                    score += 10

                record.urgency_score = min(score, 200)  # Cap at 200
            except Exception:
                record.urgency_score = 25

    @api.depends('item_count', 'unique_locations_count', 'access_coordination_needed', 'confidentiality_level')
    def _compute_complexity_score(self):
        """Calculate work order complexity score"""
        for record in self:
            try:
                score = 0

                # Item count complexity
                item_count = record.item_count or 0
                if item_count > 100:
                    score += 40
                elif item_count > 50:
                    score += 30
                elif item_count > 20:
                    score += 20
                elif item_count > 10:
                    score += 15
                elif item_count > 5:
                    score += 10

                # Location complexity
                location_count = record.unique_locations_count or 0
                score += min(location_count * 5, 30)  # Max 30 points for locations

                # Coordination requirements
                if record.access_coordination_needed:
                    score += 20

                # Security/confidentiality complexity
                confidentiality_scores = {
                    'public': 0, 'internal': 5, 'confidential': 15,
                    'restricted': 25, 'top_secret': 35
                }
                score += confidentiality_scores.get(record.confidentiality_level, 5)

                # Special requirements
                if record.temperature_controlled:
                    score += 10
                if record.insurance_required:
                    score += 10

                record.complexity_score = min(score, 100)  # Cap at 100
            except Exception:
                record.complexity_score = 20

    @api.depends('scheduled_date')
    def _compute_days_until_scheduled(self):
        """Enhanced days until scheduled calculation"""
        for record in self:
            try:
                if record.scheduled_date:
                    today = fields.Datetime.now()
                    delta = record.scheduled_date - today
                    record.days_until_scheduled = delta.days

                    # Handle partial days
                    if delta.total_seconds() > 0 and delta.days == 0:
                        record.days_until_scheduled = 1  # Same day but future time
                else:
                    record.days_until_scheduled = 999  # No schedule = far future
            except Exception:
                record.days_until_scheduled = 0

    @api.depends('actual_start_date', 'actual_completion_date')
    def _compute_actual_duration_hours(self):
        """Enhanced duration calculation with business hours consideration"""
        for record in self:
            try:
                if record.actual_start_date and record.actual_completion_date:
                    delta = record.actual_completion_date - record.actual_start_date
                    total_hours = delta.total_seconds() / 3600.0

                    # Cap at reasonable maximum (30 days)
                    record.actual_duration_hours = min(total_hours, 720.0)
                else:
                    record.actual_duration_hours = 0.0
            except Exception:
                record.actual_duration_hours = 0.0

    @api.depends('actual_duration_hours', 'estimated_completion_date', 'actual_completion_date')
    def _compute_efficiency_rating(self):
        """Calculate efficiency rating compared to estimates"""
        for record in self:
            try:
                if (record.estimated_completion_date and record.actual_completion_date and
                    record.scheduled_date):

                    estimated_hours = (record.estimated_completion_date - record.scheduled_date).total_seconds() / 3600
                    actual_hours = record.actual_duration_hours

                    if estimated_hours > 0 and actual_hours > 0:
                        efficiency_ratio = estimated_hours / actual_hours

                        if efficiency_ratio >= 1.2:
                            record.efficiency_rating = 'excellent'
                        elif efficiency_ratio >= 1.0:
                            record.efficiency_rating = 'good'
                        elif efficiency_ratio >= 0.8:
                            record.efficiency_rating = 'average'
                        else:
                            record.efficiency_rating = 'poor'
                    else:
                        record.efficiency_rating = 'average'
                else:
                    record.efficiency_rating = False
            except Exception:
                record.efficiency_rating = False

    # ============================================================================
    # COMPUTED METHODS - FINANCIAL METRICS
    # ============================================================================
    @api.depends('rate_id', 'estimated_pages', 'item_count')
    def _compute_financial_metrics(self):
        """Calculate estimated costs based on rate structure"""
        for record in self:
            try:
                if not record.rate_id:
                    record.estimated_cost = 0.0
                    continue

                rate = record.rate_id
                amount = 0.0

                # Calculate based on rate type
                if hasattr(rate, 'rate_type'):
                    if rate.rate_type == 'per_page':
                        amount = (record.estimated_pages or 0) * (rate.amount or 0)
                    elif rate.rate_type == 'per_item':
                        amount = (record.item_count or 0) * (rate.amount or 0)
                    elif rate.rate_type == 'flat_rate':
                        amount = rate.amount or 0
                    else:
                        amount = rate.amount or 0
                else:
                    # Fallback to basic amount
                    amount = rate.amount or 0

                record.estimated_cost = amount
            except Exception:
                record.estimated_cost = 0.0

    # ============================================================================
    # COMPUTED METHODS - QUALITY AND COMPLIANCE
    # ============================================================================
    @api.depends('retrieval_item_ids.quality_status', 'missing_files_count', 'damaged_files_count')
    def _compute_quality_metrics(self):
        """Calculate quality metrics and missing/damaged file counts"""
        for record in self:
            try:
                items = record.retrieval_item_ids
                if not items:
                    record.quality_score = 100.0
                    record.missing_files_count = 0
                    record.damaged_files_count = 0
                    continue

                total_items = len(items)
                missing_count = 0
                damaged_count = 0
                quality_issues = 0

                for item in items:
                    try:
                        # Check for missing files
                        if hasattr(item, 'status') and item.status in ['missing', 'not_found']:
                            missing_count += 1
                            quality_issues += 1

                        # Check for damaged files
                        if hasattr(item, 'condition') and item.condition in ['damaged', 'poor']:
                            damaged_count += 1
                            quality_issues += 1

                        # Check quality status if available
                        if hasattr(item, 'quality_status') and item.quality_status in ['failed', 'rejected']:
                            quality_issues += 1
                    except (AttributeError, TypeError):
                        continue

                # Calculate quality score
                if total_items > 0:
                    quality_ratio = max(0, (total_items - quality_issues) / total_items)
                    record.quality_score = quality_ratio * 100.0
                else:
                    record.quality_score = 100.0

                record.missing_files_count = missing_count
                record.damaged_files_count = damaged_count

            except Exception:
                record.quality_score = 100.0
                record.missing_files_count = 0
                record.damaged_files_count = 0

    @api.depends('naid_compliance_verified', 'retrieval_item_ids')
    def _compute_compliance_status(self):
        """Calculate compliance status and audit trail completeness"""
        for record in self:
            try:
                # Check if audit trail is complete
                audit_complete = True

                # Basic audit requirements
                if not record.actual_start_date and record.state not in ['draft', 'confirmed']:
                    audit_complete = False

                if record.state == 'completed' and not record.actual_completion_date:
                    audit_complete = False

                # Check retrieval items have proper tracking
                for item in record.retrieval_item_ids:
                    try:
                        if hasattr(item, 'status') and not item.status:
                            audit_complete = False
                            break
                    except (AttributeError, TypeError):
                        audit_complete = False
                        break

                record.audit_trail_complete = audit_complete
            except Exception:
                record.audit_trail_complete = False

    @api.depends('complexity_score', 'confidentiality_level', 'insurance_value')
    def _compute_risk_assessment(self):
        """Calculate risk level based on multiple factors"""
        for record in self:
            try:
                risk_score = 0

                # Complexity-based risk
                complexity = getattr(record, 'complexity_score', 0)
                if complexity > 80:
                    risk_score += 40
                elif complexity > 60:
                    risk_score += 30
                elif complexity > 40:
                    risk_score += 20
                elif complexity > 20:
                    risk_score += 10

                # Confidentiality-based risk
                confidentiality_risk = {
                    'public': 0, 'internal': 10, 'confidential': 25,
                    'restricted': 40, 'top_secret': 60
                }
                risk_score += confidentiality_risk.get(record.confidentiality_level, 10)

                # Insurance value risk
                if record.insurance_value:
                    if record.insurance_value > 1000000:  # > $1M
                        risk_score += 30
                    elif record.insurance_value > 100000:  # > $100K
                        risk_score += 20
                    elif record.insurance_value > 10000:   # > $10K
                        risk_score += 10

                # Special requirements
                if record.temperature_controlled:
                    risk_score += 15
                if record.access_coordination_needed:
                    risk_score += 10

                # Determine risk level
                if risk_score >= 80:
                    record.risk_level = 'critical'
                elif risk_score >= 60:
                    record.risk_level = 'high'
                elif risk_score >= 30:
                    record.risk_level = 'medium'
                else:
                    record.risk_level = 'low'

            except Exception:
                record.risk_level = 'medium'

    # ============================================================================
    # CONSTRAINT VALIDATION METHODS
    # ============================================================================
    @api.constrains('partner_id')
    def _check_partner_required(self):
        """Validate that customer is specified"""
        for record in self:
            if not record.partner_id:
                raise ValidationError(_("Customer is required for file retrieval work orders."))

    @api.constrains('scheduled_date', 'actual_start_date', 'actual_completion_date', 'deadline_date')
    def _check_date_consistency(self):
        """Comprehensive date validation with logical constraints"""
        for record in self:
            now = fields.Datetime.now()

            # Scheduled date validation
            if record.scheduled_date:
                # Allow scheduling up to 1 year in advance
                max_future = now + timedelta(days=365)
                if record.scheduled_date > max_future:
                    raise ValidationError(_("Scheduled date cannot be more than 1 year in the future."))

            # Deadline validation
            if record.deadline_date and record.scheduled_date:
                if record.deadline_date < record.scheduled_date:
                    raise ValidationError(_("Deadline cannot be before scheduled date."))

            # Actual dates validation
            if record.actual_start_date and record.actual_completion_date:
                if record.actual_start_date > record.actual_completion_date:
                    raise ValidationError(_("Actual start date cannot be after actual completion date."))

                # Duration reasonableness check
                duration = record.actual_completion_date - record.actual_start_date
                if duration.days > 90:  # 90 days maximum
                    raise ValidationError(_("Work order duration cannot exceed 90 days."))

            # Completion date requirements
            if record.state == 'completed':
                if not record.actual_completion_date:
                    raise ValidationError(_("Actual completion date is required for completed work orders."))
                if not record.actual_start_date:
                    raise ValidationError(_("Actual start date is required for completed work orders."))

    @api.constrains('progress_percentage')
    def _check_progress_percentage(self):
        """Validate progress percentage bounds"""
        for record in self:
            if not (0.0 <= record.progress_percentage <= 100.0):
                raise ValidationError(_("Progress percentage must be between 0% and 100%."))

    @api.constrains('files_located_count', 'files_retrieved_count', 'files_quality_approved_count',
                    'files_packaged_count', 'files_delivered_count', 'item_count')
    def _check_progress_metrics_consistency(self):
        """Validate logical consistency of progress metrics"""
        for record in self:
            if record.item_count <= 0:
                continue  # Skip validation for empty work orders

            # Validate metric progression
            metrics = [
                ('files_located_count', 'located'),
                ('files_retrieved_count', 'retrieved'),
                ('files_quality_approved_count', 'quality approved'),
                ('files_packaged_count', 'packaged'),
                ('files_delivered_count', 'delivered')
            ]

            previous_count = 0
            for field_name, description in metrics:
                current_count = getattr(record, field_name, 0)

                # Each metric should not exceed total items
                if current_count > record.item_count:
                    raise ValidationError(
                        _("Number of %s files (%d) cannot exceed total item count (%d).") %
                        (description, current_count, record.item_count)
                    )

                # Each metric should not exceed previous metric
                if current_count > previous_count and field_name != 'files_located_count':
                    previous_field = metrics[metrics.index((field_name, description)) - 1][0]
                    previous_desc = metrics[metrics.index((field_name, description)) - 1][1]
                    raise ValidationError(
                        _("Number of %s files (%d) cannot exceed number of %s files (%d).") %
                        (description, current_count, previous_desc, previous_count)
                    )

                previous_count = max(previous_count, current_count)

    @api.constrains('delivery_method', 'packaging_type', 'delivery_address_id', 'delivery_contact_id')
    def _check_delivery_requirements(self):
        """Validate delivery method requirements and consistency"""
        for record in self:
            if record.delivery_method == 'physical':
                if not record.packaging_type:
                    raise ValidationError(_("Packaging type is required for physical delivery."))
                if not record.delivery_address_id:
                    raise ValidationError(_("Delivery address is required for physical delivery."))

            elif record.delivery_method == 'pickup':
                if record.packaging_type:
                    record.packaging_type = False  # Auto-clear for pickup

            elif record.delivery_method == 'scan':
                if record.packaging_type:
                    raise ValidationError(_("Packaging type should not be set for scan delivery."))
                if record.delivery_address_id:
                    record.delivery_address_id = False  # Auto-clear for scan

            elif record.delivery_method == 'courier':
                if not record.delivery_address_id:
                    raise ValidationError(_("Delivery address is required for courier service."))
                if not record.delivery_contact_id:
                    raise ValidationError(_("Delivery contact is required for courier service."))

    @api.constrains('state', 'actual_start_date', 'retrieval_item_ids')
    def _check_state_requirements(self):
        """Validate state transition requirements"""
        for record in self:
            # Work orders in active states need actual start date
            if record.state in ['locating', 'retrieving', 'packaging', 'delivered', 'completed']:
                if not record.actual_start_date:
                    raise ValidationError(_("Actual start date is required for work orders in progress."))

            # Draft/confirmed orders should not have actual start date
            if record.state in ['draft', 'confirmed'] and record.actual_start_date:
                raise ValidationError(_("Actual start date should only be set after work begins."))

            # Cannot confirm without retrieval items unless it's a service-only work order
            if record.state != 'draft' and not record.retrieval_item_ids:
                if record.delivery_method != 'scan':  # Scan orders might not have items initially
                    raise ValidationError(_("Cannot advance work order without retrieval items."))

    @api.constrains('priority', 'access_coordination_needed', 'coordinator_id')
    def _check_coordination_requirements(self):
        """Validate coordination requirements for complex work orders"""
        for record in self:
            # High/urgent priority work orders with coordination need a coordinator
            if record.priority in ['2', '3'] and record.access_coordination_needed:
                if not record.coordinator_id:
                    raise ValidationError(
                        _("High priority work orders requiring coordination must have an assigned coordinator.")
                    )

            # Multiple locations require coordination
            if record.unique_locations_count > 3 and not record.access_coordination_needed:
                # Auto-enable coordination for complex multi-location orders
                record.access_coordination_needed = True

    @api.constrains('partner_id', 'delivery_address_id', 'delivery_contact_id')
    def _check_partner_relationships(self):
        """Validate partner relationships and permissions"""
        for record in self:
            if record.delivery_address_id and record.partner_id:
                # Delivery address must be customer or child/contact of customer
                valid_delivery_partner = (
                    record.delivery_address_id.id == record.partner_id.id or
                    record.delivery_address_id.parent_id.id == record.partner_id.id or
                    record.partner_id.id in record.delivery_address_id.child_ids.ids
                )

                if not valid_delivery_partner:
                    raise ValidationError(_("Delivery address must belong to or be associated with the customer."))

            if record.delivery_contact_id and record.partner_id:
                # Delivery contact must be related to customer
                valid_contact = (
                    record.delivery_contact_id.id == record.partner_id.id or
                    record.delivery_contact_id.parent_id.id == record.partner_id.id or
                    record.partner_id.id in record.delivery_contact_id.child_ids.ids
                )

                if not valid_contact:
                    raise ValidationError(_("Delivery contact must be associated with the customer."))

    @api.constrains('estimated_pages', 'item_count', 'estimated_cost')
    def _check_reasonable_values(self):
        """Validate that estimated values are reasonable"""
        for record in self:
            # Pages per item reasonableness
            if record.item_count > 0 and record.estimated_pages > 0:
                pages_per_item = record.estimated_pages / record.item_count
                if pages_per_item > 2000:  # 2000 pages per item seems excessive
                    raise ValidationError(
                        _("Estimated pages per item (%d) seems unreasonably high. Please verify.") % pages_per_item
                    )

            # Cost reasonableness (if specified)
            if record.estimated_cost > 0 and record.item_count > 0:
                cost_per_item = record.estimated_cost / record.item_count
                if cost_per_item > 10000:  # $10,000 per item seems excessive
                    raise ValidationError(
                        _("Estimated cost per item (%.2f) seems unreasonably high. Please verify.") % cost_per_item
                    )

    @api.constrains('state', 'urgency_score', 'priority')
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
                valid_next_states = valid_transitions.get(old_state, [])
                if new_state not in valid_next_states:
                    raise ValidationError(
                        _("Invalid state transition from '%s' to '%s'. Valid next states: %s") %
                        (old_state, new_state, ', '.join(valid_next_states))
                    )

    @api.constrains('insurance_value', 'insurance_required')
    def _check_insurance_consistency(self):
        """Validate insurance requirements and values"""
        for record in self:
            if record.insurance_required and not record.insurance_value:
                raise ValidationError(_("Insurance value must be specified when insurance is required."))

            if record.insurance_value and record.insurance_value < 0:
                raise ValidationError(_("Insurance value cannot be negative."))

    @api.constrains('confidentiality_level', 'special_instructions')
    def _check_security_requirements(self):
        """Validate security and confidentiality requirements"""
        for record in self:
            # High confidentiality levels require special instructions
            if record.confidentiality_level in ['restricted', 'top_secret']:
                if not record.special_instructions:
                    raise ValidationError(
                        _("Special instructions are required for %s documents.") %
                        dict(record._fields['confidentiality_level'].selection)[record.confidentiality_level]
                    )

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create method with sequence generation and defaults"""
        for vals in vals_list:
            # Generate sequence number
            if vals.get('name', _('New')) == _('New'):
                sequence = self.env['ir.sequence'].next_by_code('file.retrieval.work.order')
                vals['name'] = sequence or _('New')

            # Set default request date if not provided
            if 'request_date' not in vals:
                vals['request_date'] = fields.Datetime.now()

            # Auto-enable coordination for complex orders
            if vals.get('item_count', 0) > 20 or vals.get('unique_locations_count', 0) > 3:
                vals.setdefault('access_coordination_needed', True)

            # Set default confidentiality level based on partner
            if 'confidentiality_level' not in vals and vals.get('partner_id'):
                partner = self.env['res.partner'].browse(vals['partner_id'])
                if hasattr(partner, 'default_confidentiality_level'):
                    vals['confidentiality_level'] = partner.default_confidentiality_level

        records = super().create(vals_list)

        # Post-creation actions
        for record in records:
            # Create initial NAID audit log
            record._create_naid_audit_log('work_order_created', {
                'creation_method': 'manual',
                'created_by': self.env.user.name,
            })

            # Auto-assign coordinator for high-priority orders
            if record.priority in ['2', '3'] and record.access_coordination_needed and not record.coordinator_id:
                default_coordinator = self._get_default_coordinator()
                if default_coordinator:
                    record.coordinator_id = default_coordinator.id

        return records

    def write(self, vals):
        """Enhanced write method with change tracking"""
        # Track important field changes
        tracked_fields = ['state', 'priority', 'delivery_method', 'coordinator_id', 'scheduled_date']
        changes = {}

        for record in self:
            for field in tracked_fields:
                if field in vals:
                    old_value = getattr(record, field, None)
                    new_value = vals[field]
                    if old_value != new_value:
                        changes.setdefault(record.id, {})[field] = {
                            'old': old_value,
                            'new': new_value
                        }

        result = super().write(vals)

        # Post-write actions
        for record in self:
            record_changes = changes.get(record.id, {})

            # Create audit logs for significant changes
            if record_changes:
                record._create_naid_audit_log('work_order_updated', {
                    'changes': record_changes,
                    'updated_by': self.env.user.name,
                })

            # Auto-update progress if items changed
            if 'retrieval_item_ids' in vals:
                record._compute_progress_metrics()

            # Trigger notifications for state changes
            if 'state' in vals:
                record._handle_state_change_notifications(record_changes.get('state', {}))

        return result

    def unlink(self):
        """Enhanced unlink with validation and cleanup"""
        for record in self:
            # Prevent deletion of active work orders
            if record.state in ['locating', 'retrieving', 'packaging']:
                raise UserError(_("Cannot delete work order '%s' that is currently in progress.") % record.name)

            # Prevent deletion if invoiced
            if record.invoice_id and record.invoice_id.state == 'posted':
                raise UserError(_("Cannot delete work order '%s' that has a posted invoice.") % record.name)

            # Create deletion audit log
            record._create_naid_audit_log('work_order_deleted', {
                'deleted_by': self.env.user.name,
                'deletion_reason': self.env.context.get('deletion_reason', 'User requested'),
            })

        return super().unlink()

    @api.model
    def _get_default_coordinator(self):
        """Get default coordinator for auto-assignment"""
        try:
            # Look for users with 'File Retrieval Coordinator' role
            coordinator_group = self.env.ref('records_management.group_file_retrieval_coordinator', raise_if_not_found=False)
            if coordinator_group:
                coordinators = coordinator_group.users
                if coordinators:
                    return coordinators[0]  # Return first available coordinator
        except Exception:
            pass
        return None

    # ============================================================================
    # ACTION METHODS - STATE TRANSITIONS
    # ============================================================================
    def action_confirm(self):
        """Comprehensive work order confirmation with enhanced validation"""
        for record in self:
            # State validation
            if record.state != 'draft':
                raise UserError(_("Only draft work orders can be confirmed."))

            # Business rule validation
            if not record.scheduled_date:
                raise UserError(_("Scheduled date must be set before confirmation."))

            if record.access_coordination_needed and not record.coordinator_id:
                # Try to auto-assign coordinator
                default_coordinator = self._get_default_coordinator()
                if default_coordinator:
                    record.coordinator_id = default_coordinator.id
                else:
                    raise UserError(_("Coordinator must be assigned for work orders requiring access coordination."))

            # Update state and tracking
            record.write({
                'state': 'confirmed',
                'request_date': fields.Datetime.now()
            })

            # Create comprehensive audit log
            record._create_naid_audit_log('work_order_confirmed', {
                'confirmed_by': self.env.user.name,
                'confirmation_date': fields.Datetime.now(),
                'item_count': record.item_count,
                'estimated_pages': record.estimated_pages,
                'priority': record.priority,
                'coordinator': record.coordinator_id.name if record.coordinator_id else None,
            })

            # Enhanced notification with comprehensive details
            confirmation_details = _(
                "File retrieval work order confirmed:\n"
                "• Customer: %s\n"
                "• Items: %s files\n"
                "• Estimated pages: %s\n"
                "• Priority: %s\n"
                "• Scheduled: %s\n"
                "• Locations: %s\n"
                "• Delivery method: %s"
            ) % (
                record.partner_id.name,
                record.item_count,
                record.estimated_pages,
                dict(record._fields['priority'].selection).get(record.priority, 'Unknown'),
                record.scheduled_date.strftime('%Y-%m-%d %H:%M') if record.scheduled_date else 'Not scheduled',
                record.unique_locations_count,
                dict(record._fields['delivery_method'].selection).get(record.delivery_method, 'Not specified')
            )

            record.message_post(
                body=confirmation_details,
                message_type='notification',
                subtype_xmlid='mail.mt_note'
            )

            # Notify team members
            record._notify_team_members('confirmed')

            # Schedule activities
            record._schedule_coordination_activities()

        return True

    def action_start_locating(self):
        """Start comprehensive file location process"""
        for record in self:
            # Validation
            if record.state != 'confirmed':
                raise UserError(_("Only confirmed work orders can start file location."))

            if not record.retrieval_item_ids:
                raise UserError(_("Cannot start locating without retrieval items."))

            # Update state and tracking
            start_time = fields.Datetime.now()
            record.write({
                'state': 'locating',
                'actual_start_date': start_time
            })

            # Initialize retrieval items
            for item in record.retrieval_item_ids:
                if hasattr(item, 'status') and not item.status:
                    item.status = 'pending_location'

            # Create audit log
            record._create_naid_audit_log('location_started', {
                'start_time': start_time,
                'started_by': self.env.user.name,
                'items_to_locate': record.item_count,
                'locations_to_visit': record.unique_locations_count,
            })

            # Comprehensive notification
            location_details = _(
                "File location process started:\n"
                "• Items to locate: %s\n"
                "• Storage containers: %s\n"
                "• Unique locations: %s\n"
                "• Coordination required: %s\n"
                "• Assigned coordinator: %s"
            ) % (
                record.item_count,
                len(record.container_ids),
                record.unique_locations_count,
                'Yes' if record.access_coordination_needed else 'No',
                record.coordinator_id.name if record.coordinator_id else 'None'
            )

            record.message_post(body=location_details, message_type='notification')

            # Create location-specific activities
            record._create_location_activities()

            # Notify team
            record._notify_team_members('location_started')

        return True

    def action_start_retrieving(self):
        """Start comprehensive file retrieval process"""
        for record in self:
            if record.state != 'locating':
                raise UserError(_("File location must be completed before retrieval."))

            # Validate location progress
            located_items = record.retrieval_item_ids.filtered(
                lambda r: hasattr(r, 'status') and r.status in ['located', 'retrieved']
            )

            if not located_items:
                raise UserError(_("No files have been located yet. Complete location process first."))

            # Check if minimum location threshold is met
            location_percentage = len(located_items) / record.item_count * 100 if record.item_count > 0 else 0
            if location_percentage < 50:  # Require at least 50% located
                raise UserError(
                    _("At least 50%% of files must be located before starting retrieval. Currently: %.1f%%") %
                    location_percentage
                )

            # Update state
            record.write({'state': 'retrieving'})

            # Create audit log
            record._create_naid_audit_log('retrieval_started', {
                'located_items': len(located_items),
                'location_percentage': location_percentage,
                'started_by': self.env.user.name,
            })

            # Notification with progress details
            retrieval_details = _(
                "File retrieval process started:\n"
                "• Files located: %s of %s (%.1f%%)\n"
                "• Ready for retrieval: %s\n"
                "• Estimated completion: %s"
            ) % (
                len(located_items),
                record.item_count,
                location_percentage,
                len(located_items),
                record.estimated_completion_date.strftime('%Y-%m-%d %H:%M') if record.estimated_completion_date else 'Not calculated'
            )

            record.message_post(body=retrieval_details, message_type='notification')

            # Create retrieval activities
            record._create_retrieval_activities()

            # Notify team
            record._notify_team_members('retrieval_started')

        return True

    def action_start_packaging(self):
        """Start comprehensive packaging process with quality validation"""
        for record in self:
            if record.state != 'retrieving':
                raise UserError(_("File retrieval must be completed before packaging."))

            # Validate delivery requirements
            if record.delivery_method == 'physical':
                if not record.packaging_type:
                    raise UserError(_("Packaging type must be specified for physical delivery."))
                if not record.delivery_address_id:
                    raise UserError(_("Delivery address must be specified for physical delivery."))
            elif record.delivery_method == 'courier':
                if not record.delivery_contact_id:
                    raise UserError(_("Delivery contact must be specified for courier service."))

            # Validate retrieval progress
            retrieved_items = record.retrieval_item_ids.filtered(
                lambda r: hasattr(r, 'status') and r.status in ['retrieved', 'packaged']
            )

            if not retrieved_items:
                raise UserError(_("No files have been retrieved yet."))

            retrieval_percentage = len(retrieved_items) / record.item_count * 100 if record.item_count > 0 else 0
            if retrieval_percentage < 80:  # Require 80% retrieved
                raise UserError(
                    _("At least 80%% of files must be retrieved before packaging. Currently: %.1f%%") %
                    retrieval_percentage
                )

            # Update state
            record.write({'state': 'packaging'})

            # Update item statuses
            for item in retrieved_items:
                if hasattr(item, 'status') and item.status == 'retrieved':
                    item.status = 'packaging'

            # Create audit log
            record._create_naid_audit_log('packaging_started', {
                'retrieved_items': len(retrieved_items),
                'retrieval_percentage': retrieval_percentage,
                'delivery_method': record.delivery_method,
                'packaging_type': record.packaging_type,
                'started_by': self.env.user.name,
            })

            # Enhanced notification
            packaging_details = _(
                "Packaging process started:\n"
                "• Files retrieved: %s of %s (%.1f%%)\n"
                "• Delivery method: %s\n"
                "• Packaging type: %s\n"
                "• Delivery address: %s\n"
                "• Special instructions: %s"
            ) % (
                len(retrieved_items),
                record.item_count,
                retrieval_percentage,
                dict(record._fields['delivery_method'].selection).get(record.delivery_method, 'Unknown'),
                dict(record._fields['packaging_type'].selection).get(record.packaging_type, 'N/A'),
                record.delivery_address_id.display_name if record.delivery_address_id else 'N/A',
                record.delivery_instructions or 'None'
            )

            record.message_post(body=packaging_details, message_type='notification')

            # Create packaging activities
            record._create_packaging_activities()

            # Notify team
            record._notify_team_members('packaging_started')

        return True

    def action_mark_delivered(self):
        """Mark work order as delivered with comprehensive quality validation"""
        for record in self:
            if record.state != 'packaging':
                raise UserError(_("Packaging must be completed before delivery."))

            # Quality validation
            packaged_items = record.retrieval_item_ids.filtered(
                lambda r: hasattr(r, 'status') and r.status in ['packaged', 'delivered']
            )

            packaging_percentage = len(packaged_items) / record.item_count * 100 if record.item_count > 0 else 0
            if packaging_percentage < 95:  # Require 95% packaged
                raise UserError(
                    _("At least 95%% of files must be packaged before delivery. Currently: %.1f%%") %
                    packaging_percentage
                )

            # Final quality check
            if record.missing_files_count > 0:
                if not self.env.context.get('force_delivery_with_missing_files'):
                    raise UserError(
                        _("Cannot deliver with %d missing files. Use 'Force Delivery' if customer approves.") %
                        record.missing_files_count
                    )

            # Update state
            delivery_time = fields.Datetime.now()
            record.write({'state': 'delivered'})

            # Update all packaged items to delivered
            for item in packaged_items:
                if hasattr(item, 'status'):
                    item.status = 'delivered'

            # Create comprehensive audit log
            record._create_naid_audit_log('delivery_completed', {
                'delivery_time': delivery_time,
                'delivery_method': record.delivery_method,
                'items_delivered': len(packaged_items),
                'missing_files': record.missing_files_count,
                'damaged_files': record.damaged_files_count,
                'quality_score': record.quality_score,
                'delivered_by': self.env.user.name,
            })

            # Enhanced delivery notification
            delivery_summary = record._generate_delivery_summary()
            record.message_post(body=delivery_summary, message_type='notification')

            # Customer notification
            record._send_customer_delivery_notification()

            # Create follow-up activities
            record._create_delivery_follow_up_activities()

            # Notify team
            record._notify_team_members('delivered')

        return True

    def action_complete(self):
        """Complete work order with comprehensive finalization and reporting"""
        for record in self:
            if record.state != 'delivered':
                raise UserError(_("Only delivered work orders can be completed."))

            # Final validation
            if not all(hasattr(item, 'status') and item.status == 'delivered' for item in record.retrieval_item_ids):
                raise UserError(_("All retrieval items must be delivered before completion."))

            # Completion processing
            completion_time = fields.Datetime.now()
            record.write({
                'state': 'completed',
                'actual_completion_date': completion_time
            })

            # Calculate performance metrics
            performance_data = record._calculate_performance_metrics()

            # Create comprehensive completion audit log
            record._create_naid_audit_log('work_order_completed', {
                'completion_time': completion_time,
                'total_duration_hours': record.actual_duration_hours,
                'efficiency_rating': record.efficiency_rating,
                'quality_score': record.quality_score,
                'customer_satisfaction': record.customer_satisfaction_rating,
                'performance_metrics': performance_data,
                'completed_by': self.env.user.name,
            })

            # Generate completion report
            completion_report = record._generate_completion_report()
            record.message_post(
                body=completion_report,
                message_type='notification',
                subject=_("Work Order Completed - %s") % record.name
            )

            # Auto-create invoice if configured
            if record.rate_id and not record.invoice_id:
                record._create_comprehensive_invoice()

            # Customer satisfaction survey
            record._schedule_customer_satisfaction_survey()

            # Final notifications
            record._send_completion_notifications()

            # Update team performance metrics
            record._update_team_performance_metrics()

        return True

    def action_cancel(self):
        """Cancel work order with comprehensive reason tracking and cleanup"""
        for record in self:
            if record.state in ['completed']:
                raise UserError(_("Cannot cancel completed work orders."))

            if record.state == 'cancelled':
                raise UserError(_("Work order is already cancelled."))

            # Get cancellation details
            cancel_reason = self.env.context.get('cancel_reason', 'Cancelled by user')
            cancel_details = self.env.context.get('cancel_details', '')

            # Update state
            record.write({
                'state': 'cancelled',
                'follow_up_required': bool(cancel_details),
                'follow_up_notes': cancel_details if cancel_details else f"Cancelled: {cancel_reason}"
            })

            # Cancel all related activities
            record.activity_ids.action_close_dialog()

            # Update retrieval items
            for item in record.retrieval_item_ids:
                if hasattr(item, 'status'):
                    item.status = 'cancelled'

            # Create cancellation audit log
            record._create_naid_audit_log('work_order_cancelled', {
                'cancellation_reason': cancel_reason,
                'cancellation_details': cancel_details,
                'cancelled_by': self.env.user.name,
                'items_affected': record.item_count,
                'progress_at_cancellation': record.progress_percentage,
            })

            # Notification
            cancellation_message = _(
                "Work order cancelled:\n"
                "• Reason: %s\n"
                "• Progress at cancellation: %.1f%%\n"
                "• Items affected: %s\n"
                "• Additional details: %s"
            ) % (cancel_reason, record.progress_percentage, record.item_count, cancel_details or 'None')

            record.message_post(body=cancellation_message, message_type='notification')

            # Notify stakeholders
            record._notify_cancellation_stakeholders(cancel_reason, cancel_details)

        return True

    # ============================================================================
    # ACTION METHODS - VIEW HELPERS
    # ============================================================================
    def action_view_retrieval_items(self):
        """Enhanced view of retrieval items with context and grouping"""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Retrieval Items - %s") % self.name,
            "res_model": "file.retrieval.item",
            "view_mode": "tree,form,kanban",
            "domain": [("work_order_id", "=", self.id)],
            "context": {
                "default_work_order_id": self.id,
                "default_partner_id": self.partner_id.id,
                "group_by": "status",
                "search_default_group_status": 1,
                "search_default_pending": 1,
                "create": True,
                "edit": True,
            },
            "target": "current",
        }

    def action_view_containers(self):
        """Enhanced view of related containers with location context"""
        self.ensure_one()
        if not self.container_ids:
            raise UserError(_("No containers are associated with this work order."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Related Containers - %s") % self.name,
            "res_model": "records.container",
            "view_mode": "tree,form,kanban",
            "domain": [("id", "in", self.container_ids.ids)],
            "context": {
                "create": False,
                "group_by": "storage_location_id",
                "search_default_group_location": 1,
                "work_order_context": True,
                "work_order_id": self.id,
            },
            "target": "current",
        }

    def action_view_locations(self):
        """Enhanced view of storage locations with access information"""
        self.ensure_one()
        if not self.location_ids:
            raise UserError(_("No storage locations are associated with this work order."))

        return {
            "type": "ir.actions.act_window",
            "name": _("Storage Locations - %s") % self.name,
            "res_model": "records.location",
            "view_mode": "tree,form,map",
            "domain": [("id", "in", self.location_ids.ids)],
            "context": {
                "create": False,
                "work_order_context": True,
                "work_order_id": self.id,
                "show_access_info": True,
            },
            "target": "current",
        }

    def action_view_audit_logs(self):
        """View NAID audit logs for this work order"""
        self.ensure_one()
        try:
            return {
                "type": "ir.actions.act_window",
                "name": _("Audit Logs - %s") % self.name,
                "res_model": "naid.audit.log",
                "view_mode": "tree,form",
                "domain": [
                    ("model_name", "=", self._name),
                    ("record_id", "=", self.id),
                ],
                "context": {
                    "create": False,
                    "edit": False,
                    "group_by": "event_type",
                },
                "target": "current",
            }
        except Exception:
            raise UserError(_("Audit log model is not available in this system."))

    def action_view_performance_dashboard(self):
        """View performance dashboard for this work order"""
        self.ensure_one()

        dashboard_data = self._generate_performance_dashboard_data()

        return {
            "type": "ir.actions.act_window",
            "name": _("Performance Dashboard - %s") % self.name,
            "res_model": "file.retrieval.work.order",
            "view_mode": "form",
            "res_id": self.id,
            "context": {
                "dashboard_mode": True,
                "dashboard_data": dashboard_data,
                "readonly": True,
            },
            "target": "new",
        }

    def action_generate_report(self):
        """Generate comprehensive work order report"""
        self.ensure_one()
        return self.env.ref('records_management.file_retrieval_work_order_report').report_action(self)

    def action_export_data(self):
        """Export work order data in multiple formats"""
        self.ensure_one()
        export_data = self._prepare_export_data()

        return {
            "type": "ir.actions.act_window",
            "name": _("Export Work Order Data - %s") % self.name,
            "res_model": "file.retrieval.export.wizard",
            "view_mode": "form",
            "context": {
                "default_work_order_id": self.id,
                "default_export_data": export_data,
            },
            "target": "new",
        }

    # ============================================================================
    # BUSINESS WORKFLOW HELPER METHODS
    # ============================================================================
    def _create_comprehensive_invoice(self):
        """Create detailed invoice with enhanced line items and metadata"""
        self.ensure_one()
        if not self.rate_id or self.invoice_id:
            return False

        try:
            # Calculate comprehensive invoice amounts
            invoice_lines = self._calculate_invoice_lines()

            # Create invoice with enhanced metadata
            invoice_vals = {
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_origin': self.name,
                'ref': f"File Retrieval - {self.name}",
                'invoice_line_ids': invoice_lines,
                'invoice_date': fields.Date.today(),
                'work_order_id': self.id,  # Custom field if available
            }

            invoice = self.env['account.move'].create(invoice_vals)
            self.invoice_id = invoice.id

            # Enhanced notification with invoice details
            total_amount = sum(line[2]['price_subtotal'] for line in invoice_lines)
            invoice_message = _(
                "Invoice created for file retrieval service:\n"
                "• Invoice: %s\n"
                "• Amount: %s %s\n"
                "• Items: %s files\n"
                "• Pages: %s\n"
                "• Rate type: %s"
            ) % (
                invoice.name,
                total_amount,
                self.currency_id.name,
                self.item_count,
                self.estimated_pages,
                getattr(self.rate_id, 'rate_type', 'Standard')
            )

            self.message_post(body=invoice_message, message_type='notification')

            return invoice
        except Exception as e:
            self.message_post(
                body=_("Failed to create invoice: %s") % str(e),
                message_type='notification'
            )
            return False

    def _calculate_invoice_lines(self):
        """Calculate detailed invoice lines based on rate structure"""
        lines = []

        if not self.rate_id:
            return lines

        rate = self.rate_id

        # Primary service line
        if hasattr(rate, 'rate_type'):
            if rate.rate_type == 'per_page':
                quantity = self.estimated_pages or 0
                description = _("File retrieval service - %s pages") % quantity
            elif rate.rate_type == 'per_item':
                quantity = self.item_count or 0
                description = _("File retrieval service - %s items") % quantity
            else:
                quantity = 1
                description = _("File retrieval service - flat rate")
        else:
            quantity = 1
            description = _("File retrieval service")

        # Main service line
        lines.append((0, 0, {
            'name': description,
            'quantity': quantity,
            'price_unit': rate.amount or 0,
            'account_id': self._get_service_account_id(),
        }))

        # Additional charges based on complexity
        if self.access_coordination_needed and quantity > 0:
            coordination_fee = (rate.amount or 0) * 0.1  # 10% surcharge
            lines.append((0, 0, {
                'name': _("Access coordination fee"),
                'quantity': 1,
                'price_unit': coordination_fee,
                'account_id': self._get_service_account_id(),
            }))

        # Rush service fee for urgent priority
        if self.priority == '3' and quantity > 0:
            rush_fee = (rate.amount or 0) * 0.25  # 25% surcharge
            lines.append((0, 0, {
                'name': _("Urgent priority rush service fee"),
                'quantity': 1,
                'price_unit': rush_fee,
                'account_id': self._get_service_account_id(),
            }))

        # Special handling fees
        if self.insurance_required and self.insurance_value > 0:
            insurance_fee = min(self.insurance_value * 0.001, 500)  # 0.1% of value, max $500
            lines.append((0, 0, {
                'name': _("Insurance and special handling fee"),
                'quantity': 1,
                'price_unit': insurance_fee,
                'account_id': self._get_service_account_id(),
            }))

        return lines

    def _get_service_account_id(self):
        """Get appropriate service account for invoicing"""
        try:
            # Try to find service revenue account
            service_account = self.env['account.account'].search([
                ('code', 'like', '4%'),  # Revenue accounts
                ('name', 'ilike', 'service'),
                ('company_id', '=', self.company_id.id),
            ], limit=1)

            if service_account:
                return service_account.id

            # Fallback to default income account
            return self.env.company.account_default_pos_receivable_account_id.id
        except Exception:
            return None

    def _create_naid_audit_log(self, event_type, additional_metadata=None):
        """Enhanced NAID audit log creation with comprehensive metadata"""
        if not self.env["ir.module.module"].search([
            ("name", "=", "records_management"),
            ("state", "=", "installed")
        ]):
            return

        try:
            # Base audit data
            audit_data = {
                "event_type": event_type,
                "model_name": self._name,
                "record_id": self.id,
                "partner_id": self.partner_id.id if self.partner_id else None,
                "description": _("Work order: %s - %s items") % (self.name, self.item_count),
                "user_id": self.env.user.id,
                "timestamp": fields.Datetime.now(),
                "company_id": self.company_id.id,
            }

            # Enhanced metadata
            metadata = {
                "work_order_name": self.name,
                "state": self.state,
                "priority": self.priority,
                "item_count": self.item_count,
                "estimated_pages": self.estimated_pages,
                "unique_locations": self.unique_locations_count,
                "delivery_method": self.delivery_method,
                "progress_percentage": self.progress_percentage,
                "urgency_score": self.urgency_score,
                "complexity_score": getattr(self, 'complexity_score', 0),
                "quality_score": getattr(self, 'quality_score', 0),
                "customer_name": self.partner_id.name if self.partner_id else None,
                "coordinator": self.coordinator_id.name if self.coordinator_id else None,
            }

            # Add additional metadata if provided
            if additional_metadata:
                metadata.update(additional_metadata)

            audit_data["metadata"] = metadata

            # Add chain of custody information
            if hasattr(self, 'retrieval_item_ids'):
                custody_info = []
                for item in self.retrieval_item_ids:
                    if hasattr(item, 'container_id') and item.container_id:
                        custody_info.append({
                            'item_description': getattr(item, 'description', 'Unknown'),
                            'container_name': item.container_id.name,
                            'location': item.container_id.storage_location_id.name if item.container_id.storage_location_id else 'Unknown',
                            'status': getattr(item, 'status', 'Unknown'),
                        })

                if custody_info:
                    audit_data["chain_of_custody"] = custody_info

            self.env["naid.audit.log"].create(audit_data)
        except Exception:
            # Don't fail the main operation if audit logging fails
            pass

    def _notify_team_members(self, event_type):
        """Notify relevant team members about work order events"""
        notification_users = self.env['res.users']

        # Always notify assigned user
        if self.user_id:
            notification_users |= self.user_id

        # Notify coordinator for coordination events
        if self.coordinator_id and event_type in ['confirmed', 'location_started', 'coordination_needed']:
            notification_users |= self.coordinator_id

        # Notify retrieval team
        if self.retrieval_team_ids and event_type in ['location_started', 'retrieval_started']:
            notification_users |= self.retrieval_team_ids

        # Notify quality inspector
        if self.quality_inspector_id and event_type in ['packaging_started', 'delivered']:
            notification_users |= self.quality_inspector_id

        # Send notifications
        for user in notification_users:
            if user != self.env.user:  # Don't notify the current user
                self._send_user_notification(user, event_type)

    def _send_user_notification(self, user, event_type):
        """Send notification to specific user"""
        try:
            notification_templates = {
                'confirmed': _("Work order %s has been confirmed and assigned to you."),
                'location_started': _("File location has started for work order %s."),
                'retrieval_started': _("File retrieval has started for work order %s."),
                'packaging_started': _("Packaging has started for work order %s."),
                'delivered': _("Work order %s has been delivered and needs your attention."),
                'completed': _("Work order %s has been completed."),
            }

            message = notification_templates.get(event_type, _("Work order %s status has been updated.")) % self.name

            # Create activity for the user
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=user.id,
                summary=_("Work Order Notification"),
                note=message
            )
        except Exception:
            pass

    def _schedule_coordination_activities(self):
        """Schedule coordination activities based on work order requirements"""
        if not self.access_coordination_needed or not self.coordinator_id:
            return

        # Schedule location access coordination
        for location in self.location_ids:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_call',
                    user_id=self.coordinator_id.id,
                    summary=_("Coordinate Access - %s") % location.name,
                    note=_("Coordinate access to location %s for work order %s. Estimated %d items to retrieve.") % (
                        location.name, self.name, self.item_count
                    ),
                    date_deadline=self.scheduled_date.date() if self.scheduled_date else fields.Date.today()
                )
            except Exception:
                continue

    def _create_location_activities(self):
        """Create specific activities for each location that needs to be visited"""
        for location in self.location_ids:
            # Count items in this location
            location_items = self.retrieval_item_ids.filtered(
                lambda item: hasattr(item, 'container_id') and
                           item.container_id and
                           item.container_id.storage_location_id == location
            )

            if location_items:
                try:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=self.user_id.id,
                        summary=_("Locate Files - %s") % location.name,
                        note=_("Locate %d items at %s for work order %s") % (
                            len(location_items), location.name, self.name
                        )
                    )
                except Exception:
                    continue

    def _create_retrieval_activities(self):
        """Create retrieval activities based on located items"""
        if self.retrieval_team_ids:
            # Assign to retrieval team
            for team_member in self.retrieval_team_ids:
                try:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=team_member.id,
                        summary=_("Retrieve Files - %s") % self.name,
                        note=_("Retrieve located files for work order %s. %d items ready for retrieval.") % (
                            self.name, self.files_located_count
                        )
                    )
                except Exception:
                    continue
        else:
            # Assign to main user
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=self.user_id.id,
                    summary=_("Retrieve Files - %s") % self.name,
                    note=_("Retrieve %d located files for work order %s") % (
                        self.files_located_count, self.name
                    )
                )
            except Exception:
                pass

    def _create_packaging_activities(self):
        """Create packaging and quality control activities"""
        # Quality control activity
        if self.quality_inspector_id:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_todo',
                    user_id=self.quality_inspector_id.id,
                    summary=_("Quality Control - %s") % self.name,
                    note=_("Perform quality control and packaging for %d retrieved files.") % self.files_retrieved_count
                )
            except Exception:
                pass

        # Packaging activity
        try:
            self.activity_schedule(
                'mail.mail_activity_data_todo',
                user_id=self.user_id.id,
                summary=_("Package Files - %s") % self.name,
                note=_("Package %d files using %s for %s delivery.") % (
                    self.files_retrieved_count,
                    dict(self._fields['packaging_type'].selection).get(self.packaging_type, 'standard packaging'),
                    dict(self._fields['delivery_method'].selection).get(self.delivery_method, 'unknown')
                )
            )
        except Exception:
            pass

    def _create_delivery_follow_up_activities(self):
        """Create follow-up activities after delivery"""
        # Customer satisfaction survey
        try:
            self.activity_schedule(
                'mail.mail_activity_data_email',
                user_id=self.user_id.id,
                summary=_("Customer Satisfaction Survey - %s") % self.partner_id.name,
                note=_("Send customer satisfaction survey for work order %s") % self.name,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )
        except Exception:
            pass

        # Quality follow-up if there were issues
        if self.missing_files_count > 0 or self.damaged_files_count > 0:
            try:
                self.activity_schedule(
                    'mail.mail_activity_data_call',
                    user_id=self.user_id.id,
                    summary=_("Quality Follow-up - %s") % self.name,
                    note=_("Follow up on quality issues: %d missing, %d damaged files") % (
                        self.missing_files_count, self.damaged_files_count
                    ),
                    date_deadline=fields.Date.today() + timedelta(days=2)
                )
            except Exception:
                pass

    def _send_customer_delivery_notification(self):
        """Send comprehensive delivery notification to customer"""
        try:
            # Prepare delivery summary
            delivery_data = {
                'work_order_name': self.name,
                'customer_name': self.partner_id.name,
                'items_delivered': self.files_delivered_count,
                'total_items': self.item_count,
                'delivery_method': dict(self._fields['delivery_method'].selection).get(self.delivery_method, 'Unknown'),
                'delivery_date': fields.Datetime.now(),
                'quality_score': getattr(self, 'quality_score', 100),
                'missing_files': self.missing_files_count,
                'damaged_files': self.damaged_files_count,
            }

            # Try to send via email template
            template_name = 'file_retrieval_delivery_notification_template'
            try:
                template = self.env.ref(f'records_management.{template_name}')
                template.with_context(delivery_data).send_mail(self.id)
            except Exception:
                # Fallback to activity creation
                self.activity_schedule(
                    'mail.mail_activity_data_email',
                    user_id=self.user_id.id,
                    summary=_("Send Delivery Notification"),
                    note=_("Send delivery notification to %s for work order %s") % (
                        self.partner_id.name, self.name
                    )
                )
        except Exception:
            pass

    def _generate_delivery_summary(self):
        """Generate comprehensive delivery summary"""
        summary = _(
            "File Retrieval Work Order Delivered Successfully\n"
            "═══════════════════════════════════════════════\n"
            "Work Order: %s\n"
            "Customer: %s\n"
            "Delivery Date: %s\n\n"
            "DELIVERY SUMMARY:\n"
            "• Total Items Requested: %d\n"
            "• Items Delivered: %d\n"
            "• Delivery Method: %s\n"
            "• Quality Score: %.1f%%\n\n"
        ) % (
            self.name,
            self.partner_id.name,
            fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
            self.item_count,
            self.files_delivered_count,
            dict(self._fields['delivery_method'].selection).get(self.delivery_method, 'Unknown'),
            getattr(self, 'quality_score', 100.0)
        )

        # Add quality issues if any
        if self.missing_files_count > 0 or self.damaged_files_count > 0:
            summary += _(
                "QUALITY ISSUES:\n"
                "• Missing Files: %d\n"
                "• Damaged Files: %d\n\n"
            ) % (self.missing_files_count, self.damaged_files_count)

        # Add delivery details
        if self.delivery_method == 'physical':
            summary += _(
                "DELIVERY DETAILS:\n"
                "• Packaging: %s\n"
                "• Delivery Address: %s\n"
                "• Special Instructions: %s\n\n"
            ) % (
                dict(self._fields['packaging_type'].selection).get(self.packaging_type, 'Standard'),
                self.delivery_address_id.display_name if self.delivery_address_id else 'Customer address',
                self.delivery_instructions or 'None'
            )
        elif self.delivery_method == 'scan':
            summary += _(
                "SCAN DELIVERY:\n"
                "• Files scanned and emailed to: %s\n"
                "• Email delivery completed\n\n"
            ) % (self.partner_id.email or 'Customer email')

        return summary

    def _calculate_performance_metrics(self):
        """Calculate comprehensive performance metrics"""
        metrics = {}

        try:
            # Duration metrics
            if self.actual_start_date and self.actual_completion_date:
                actual_duration = self.actual_completion_date - self.actual_start_date
                metrics['actual_duration_hours'] = actual_duration.total_seconds() / 3600

                if self.estimated_completion_date and self.scheduled_date:
                    estimated_duration = self.estimated_completion_date - self.scheduled_date
                    estimated_hours = estimated_duration.total_seconds() / 3600

                    if estimated_hours > 0:
                        metrics['efficiency_ratio'] = estimated_hours / metrics['actual_duration_hours']
                        metrics['time_variance_hours'] = metrics['actual_duration_hours'] - estimated_hours

            # Quality metrics
            metrics['completion_rate'] = (self.files_delivered_count / self.item_count * 100) if self.item_count > 0 else 0
            metrics['quality_score'] = getattr(self, 'quality_score', 100.0)
            metrics['missing_file_rate'] = (self.missing_files_count / self.item_count * 100) if self.item_count > 0 else 0
            metrics['damage_rate'] = (self.damaged_files_count / self.item_count * 100) if self.item_count > 0 else 0

            # Complexity metrics
            metrics['complexity_score'] = getattr(self, 'complexity_score', 0)
            metrics['locations_per_item'] = self.unique_locations_count / self.item_count if self.item_count > 0 else 0
            metrics['pages_per_item'] = self.estimated_pages / self.item_count if self.item_count > 0 else 0

            # Cost metrics
            if self.estimated_cost > 0:
                metrics['cost_per_item'] = self.estimated_cost / self.item_count
                metrics['cost_per_page'] = self.estimated_cost / self.estimated_pages if self.estimated_pages > 0 else 0

        except Exception:
            pass

        return metrics

    def _generate_completion_report(self):
        """Generate comprehensive completion report"""
        performance_data = self._calculate_performance_metrics()

        report = _(
            "FILE RETRIEVAL WORK ORDER COMPLETION REPORT\n"
            "═══════════════════════════════════════════════════════════\n"
            "Work Order: %s\n"
            "Customer: %s\n"
            "Completion Date: %s\n"
            "Total Duration: %.1f hours\n\n"
            "SUMMARY STATISTICS:\n"
            "• Items Requested: %d\n"
            "• Items Delivered: %d (%.1f%%)\n"
            "• Total Pages: %d\n"
            "• Locations Visited: %d\n"
            "• Quality Score: %.1f%%\n"
            "• Urgency Score: %d\n"
            "• Complexity Score: %d\n\n"
        ) % (
            self.name,
            self.partner_id.name,
            self.actual_completion_date.strftime('%Y-%m-%d %H:%M'),
            performance_data.get('actual_duration_hours', 0),
            self.item_count,
            self.files_delivered_count,
            performance_data.get('completion_rate', 0),
            self.estimated_pages,
            self.unique_locations_count,
            performance_data.get('quality_score', 100),
            self.urgency_score,
            performance_data.get('complexity_score', 0)
        )

        # Performance analysis
        efficiency_ratio = performance_data.get('efficiency_ratio', 1.0)
        if efficiency_ratio >= 1.2:
            performance_rating = _("Excellent (Ahead of schedule)")
        elif efficiency_ratio >= 1.0:
            performance_rating = _("Good (On schedule)")
        elif efficiency_ratio >= 0.8:
            performance_rating = _("Satisfactory (Slightly behind)")
        else:
            performance_rating = _("Needs improvement (Behind schedule)")

        report += _(
            "PERFORMANCE ANALYSIS:\n"
            "• Efficiency Rating: %s\n"
            "• Time Variance: %+.1f hours\n"
            "• Cost per Item: %.2f\n"
            "• Pages per Item: %.1f\n\n"
        ) % (
            performance_rating,
            performance_data.get('time_variance_hours', 0),
            performance_data.get('cost_per_item', 0),
            performance_data.get('pages_per_item', 0)
        )

        # Quality issues
        if self.missing_files_count > 0 or self.damaged_files_count > 0:
            report += _(
                "QUALITY ISSUES IDENTIFIED:\n"
                "• Missing Files: %d (%.1f%%)\n"
                "• Damaged Files: %d (%.1f%%)\n"
                "• Recommended Actions: Review storage conditions and retrieval procedures\n\n"
            ) % (
                self.missing_files_count,
                performance_data.get('missing_file_rate', 0),
                self.damaged_files_count,
                performance_data.get('damage_rate', 0)
            )

        return report

    def _schedule_customer_satisfaction_survey(self):
        """Schedule customer satisfaction survey"""
        try:
            self.activity_schedule(
                'mail.mail_activity_data_email',
                user_id=self.user_id.id,
                summary=_("Customer Satisfaction Survey"),
                note=_("Send customer satisfaction survey for completed work order %s") % self.name,
                date_deadline=fields.Date.today() + timedelta(days=1)
            )
        except Exception:
            pass

    def _send_completion_notifications(self):
        """Send completion notifications to all stakeholders"""
        # Notify customer
        self._send_customer_notification('completion', {
            'completion_date': self.actual_completion_date,
            'duration_hours': self.actual_duration_hours,
            'quality_score': getattr(self, 'quality_score', 100),
        })

        # Notify internal team
        completion_message = _(
            "Work order %s completed successfully for %s. Duration: %.1f hours, Quality: %.1f%%"
        ) % (self.name, self.partner_id.name, self.actual_duration_hours, getattr(self, 'quality_score', 100))

        # Send to management/supervisors
        try:
            management_group = self.env.ref('records_management.group_records_manager')
            for manager in management_group.users:
                if manager != self.env.user:
                    self.activity_schedule(
                        'mail.mail_activity_data_todo',
                        user_id=manager.id,
                        summary=_("Work Order Completed"),
                        note=completion_message
                    )
        except Exception:
            pass

    def _update_team_performance_metrics(self):
        """Update performance metrics for team members"""
        # This could integrate with HR or performance management systems
        pass

    def _notify_cancellation_stakeholders(self, reason, details):
        """Notify relevant parties about work order cancellation"""
        cancellation_message = _(
            "Work order %s has been cancelled.\nReason: %s\nDetails: %s"
        ) % (self.name, reason, details or 'None provided')

        # Notify customer
        self._send_customer_notification('cancellation', {
            'cancellation_reason': reason,
            'cancellation_details': details,
        })

        # Notify team members
        self._notify_team_members('cancelled')

    def _send_customer_notification(self, notification_type, context_data=None):
        """Enhanced customer notification system"""
        try:
            base_context = {
                'work_order_name': self.name,
                'customer_name': self.partner_id.name,
                'state': self.state,
                'item_count': self.item_count,
                'estimated_pages': self.estimated_pages,
            }

            if context_data:
                base_context.update(context_data)

            # Try to send via email template
            template_name = f'file_retrieval_{notification_type}_template'
            try:
                template = self.env.ref(f'records_management.{template_name}')
                template.with_context(base_context).send_mail(self.id)
            except Exception:
                # Fallback to activity creation
                self.activity_schedule(
                    'mail.mail_activity_data_email',
                    user_id=self.user_id.id,
                    summary=_("Send Customer Notification"),
                    note=_("Send %s notification to %s for work order %s") % (
                        notification_type, self.partner_id.name, self.name
                    )
                )
        except Exception:
            pass

    def _handle_state_change_notifications(self, state_changes):
        """Handle notifications for state changes"""
        if not state_changes:
            return

        old_state = state_changes.get('old')
        new_state = state_changes.get('new')

        if not old_state or not new_state:
            return

        # Send appropriate notifications based on state change
        notification_map = {
            ('draft', 'confirmed'): 'confirmed',
            ('confirmed', 'locating'): 'location_started',
            ('locating', 'retrieving'): 'retrieval_started',
            ('retrieving', 'packaging'): 'packaging_started',
            ('packaging', 'delivered'): 'delivered',
            ('delivered', 'completed'): 'completed',
        }

        notification_type = notification_map.get((old_state, new_state))
        if notification_type:
            self._send_customer_notification(notification_type)

    # ============================================================================
    # REPORTING AND ANALYTICS METHODS
    # ============================================================================
    def _generate_performance_dashboard_data(self):
        """Generate data for performance dashboard"""
        return {
            'basic_metrics': {
                'progress_percentage': self.progress_percentage,
                'urgency_score': self.urgency_score,
                'quality_score': getattr(self, 'quality_score', 100),
                'complexity_score': getattr(self, 'complexity_score', 0),
            },
            'completion_metrics': {
                'files_located': self.files_located_count,
                'files_retrieved': self.files_retrieved_count,
                'files_packaged': self.files_packaged_count,
                'files_delivered': self.files_delivered_count,
                'total_files': self.item_count,
            },
            'time_metrics': {
                'days_until_scheduled': self.days_until_scheduled,
                'actual_duration_hours': self.actual_duration_hours,
                'estimated_completion': self.estimated_completion_date,
                'efficiency_rating': getattr(self, 'efficiency_rating', None),
            },
            'quality_metrics': {
                'missing_files': self.missing_files_count,
                'damaged_files': self.damaged_files_count,
                'quality_score': getattr(self, 'quality_score', 100),
            }
        }

    def _prepare_export_data(self):
        """Prepare comprehensive data for export"""
        return {
            'work_order': {
                'name': self.name,
                'state': self.state,
                'priority': self.priority,
                'customer': self.partner_id.name,
                'request_date': self.request_date,
                'scheduled_date': self.scheduled_date,
                'completion_date': self.actual_completion_date,
            },
            'metrics': {
                'item_count': self.item_count,
                'estimated_pages': self.estimated_pages,
                'progress_percentage': self.progress_percentage,
                'quality_score': getattr(self, 'quality_score', 100),
                'urgency_score': self.urgency_score,
                'actual_duration_hours': self.actual_duration_hours,
            },
            'delivery': {
                'delivery_method': self.delivery_method,
                'packaging_type': self.packaging_type,
                'delivery_address': self.delivery_address_id.display_name if self.delivery_address_id else None,
            },
            'items': [
                {
                    'description': getattr(item, 'description', ''),
                    'status': getattr(item, 'status', ''),
                    'container': item.container_id.name if hasattr(item, 'container_id') and item.container_id else '',
                    'estimated_pages': getattr(item, 'estimated_pages', 0),
                }
                for item in self.retrieval_item_ids
            ]
        }

    def get_work_order_summary(self):
        """Enhanced work order summary for reporting and API"""
        summary = {
            # Basic Information
            'work_order_id': self.id,
            'name': self.name,
            'display_name': self.display_name,
            'state': self.state,
            'priority': self.priority,

            # Customer Information
            'customer_id': self.partner_id.id,
            'customer_name': self.partner_id.name,

            # Metrics
            'item_count': self.item_count,
            'estimated_pages': self.estimated_pages,
            'progress_percentage': self.progress_percentage,
            'quality_score': getattr(self, 'quality_score', 100),
            'urgency_score': self.urgency_score,
            'complexity_score': getattr(self, 'complexity_score', 0),

            # Dates
            'request_date': self.request_date,
            'scheduled_date': self.scheduled_date,
            'actual_start_date': self.actual_start_date,
            'actual_completion_date': self.actual_completion_date,
            'estimated_completion_date': self.estimated_completion_date,

            # Delivery
            'delivery_method': self.delivery_method,
            'packaging_type': self.packaging_type,

            # Progress Tracking
            'files_located_count': self.files_located_count,
            'files_retrieved_count': self.files_retrieved_count,
            'files_packaged_count': self.files_packaged_count,
            'files_delivered_count': self.files_delivered_count,

            # Quality Issues
            'missing_files_count': self.missing_files_count,
            'damaged_files_count': self.damaged_files_count,

            # Location Information
            'containers_count': len(self.container_ids),
            'unique_locations_count': self.unique_locations_count,

            # Team Information
            'assigned_user': self.user_id.name if self.user_id else None,
            'coordinator': self.coordinator_id.name if self.coordinator_id else None,

            # Performance Metrics
            'days_until_scheduled': self.days_until_scheduled,
            'actual_duration_hours': self.actual_duration_hours,
            'efficiency_rating': getattr(self, 'efficiency_rating', None),

            # Financial
            'estimated_cost': self.estimated_cost,
            'currency': self.currency_id.name,
            'invoice_created': bool(self.invoice_id),

            # Risk and Compliance
            'risk_level': getattr(self, 'risk_level', 'medium'),
            'confidentiality_level': self.confidentiality_level,
            'insurance_required': self.insurance_required,
            'naid_compliance_verified': self.naid_compliance_verified,
            'audit_trail_complete': getattr(self, 'audit_trail_complete', False),

            # Customer Satisfaction
            'customer_satisfaction_rating': self.customer_satisfaction_rating,
            'follow_up_required': self.follow_up_required,
        }

        return summary

    # ============================================================================
    # UTILITY AND HELPER METHODS
    # ============================================================================
    def _get_state_progress_mapping(self):
        """Get state to progress percentage mapping"""
        return {
            'draft': 0,
            'confirmed': 10,
            'locating': 25,
            'retrieving': 50,
            'packaging': 75,
            'delivered': 90,
            'completed': 100,
            'cancelled': 0,
        }

    def _get_priority_urgency_mapping(self):
        """Get priority to urgency score mapping"""
        return {
            '0': 25,    # Low priority
            '1': 50,    # Normal priority
            '2': 100,   # High priority
            '3': 200,   # Urgent priority
        }

    def _validate_business_rules(self):
        """Validate business rules specific to file retrieval"""
        errors = []

        # Customer validation
        if not self.partner_id:
            errors.append(_("Customer is required for file retrieval work orders"))
        elif not self.partner_id.active:
            errors.append(_("Customer account is inactive"))

        # Item validation
        if self.item_count <= 0:
            errors.append(_("Work order must have at least one item"))

        # Location validation
        if self.state not in ['draft', 'cancelled'] and not self.location_ids:
            errors.append(_("Storage locations must be specified before processing"))

        # Delivery validation
        if self.delivery_method == 'scan' and not self.partner_id.email:
            errors.append(_("Customer email is required for scan delivery"))

        if self.delivery_method == 'physical' and not self.delivery_address_id:
            if not self.partner_id.street:
                errors.append(_("Delivery address is required for physical delivery"))

        # Insurance validation
        if self.insurance_required and self.insurance_value <= 0:
            errors.append(_("Insurance value must be greater than zero when insurance is required"))

        return errors

    def _optimize_retrieval_sequence(self):
        """Optimize the sequence of file retrieval for efficiency"""
        if not self.retrieval_item_ids:
            return []

        # Group items by location for efficient retrieval
        location_groups = {}
        for item in self.retrieval_item_ids:
            if hasattr(item, 'container_id') and item.container_id and item.container_id.storage_location_id:
                location = item.container_id.storage_location_id
                if location not in location_groups:
                    location_groups[location] = []
                location_groups[location].append(item)

        # Suggest optimal retrieval sequence
        sequence_suggestions = []
        sequence = 1

        for location, items in location_groups.items():
            sequence_suggestions.append({
                'location': location.name,
                'item_count': len(items),
                'suggested_sequence': sequence,
                'items': [getattr(item, 'name', 'Unknown') for item in items]
            })
            sequence += 1

        return sequence_suggestions

    def _calculate_carbon_footprint(self):
        """Calculate estimated carbon footprint for the retrieval operation"""
        footprint = 0.0

        try:
            # Base footprint for office operations (kgCO2)
            base_footprint = 0.5

            # Transportation footprint based on locations
            location_distance = len(self.location_ids) * 2.5  # Estimated km per location
            transport_footprint = location_distance * 0.2  # kgCO2 per km

            # Packaging footprint
            packaging_factors = {
                'envelope': 0.01,
                'folder': 0.05,
                'box': 0.2,
                'tube': 0.1,
                'digital': 0.0,
            }
            packaging_footprint = packaging_factors.get(self.packaging_type, 0.05)

            # Delivery footprint
            delivery_factors = {
                'physical': 2.0,
                'scan': 0.1,
                'pickup': 0.0,
                'courier': 1.5,
            }
            delivery_footprint = delivery_factors.get(self.delivery_method, 1.0)

            footprint = base_footprint + transport_footprint + packaging_footprint + delivery_footprint

        except Exception:
            footprint = 1.0  # Default estimate

        return round(footprint, 2)

    # ============================================================================
    # API AND INTEGRATION METHODS
    # ============================================================================
    @api.model
    def get_dashboard_statistics(self, date_from=None, date_to=None):
        """Get dashboard statistics for work orders"""
        domain = []

        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        work_orders = self.search(domain)

        stats = {
            'total_orders': len(work_orders),
            'active_orders': len(work_orders.filtered(lambda wo: wo.state not in ['completed', 'cancelled'])),
            'completed_orders': len(work_orders.filtered(lambda wo: wo.state == 'completed')),
            'cancelled_orders': len(work_orders.filtered(lambda wo: wo.state == 'cancelled')),
            'total_items': sum(work_orders.mapped('item_count')),
            'total_pages': sum(work_orders.mapped('estimated_pages')),
            'avg_urgency_score': sum(work_orders.mapped('urgency_score')) / len(work_orders) if work_orders else 0,
            'avg_quality_score': sum(getattr(wo, 'quality_score', 100) for wo in work_orders) / len(work_orders) if work_orders else 100,
        }

        return stats

    def get_api_data(self):
        """Get work order data for API consumption"""
        self.ensure_one()

        return {
            'id': self.id,
            'name': self.name,
            'state': self.state,
            'priority': self.priority,
            'customer': {
                'id': self.partner_id.id,
                'name': self.partner_id.name,
                'email': self.partner_id.email,
            },
            'metrics': {
                'item_count': self.item_count,
                'estimated_pages': self.estimated_pages,
                'progress_percentage': self.progress_percentage,
                'urgency_score': self.urgency_score,
                'quality_score': getattr(self, 'quality_score', 100),
            },
            'dates': {
                'request_date': self.request_date.isoformat() if self.request_date else None,
                'scheduled_date': self.scheduled_date.isoformat() if self.scheduled_date else None,
                'actual_start_date': self.actual_start_date.isoformat() if self.actual_start_date else None,
                'actual_completion_date': self.actual_completion_date.isoformat() if self.actual_completion_date else None,
            },
            'delivery': {
                'method': self.delivery_method,
                'packaging': self.packaging_type,
                'address': self.delivery_address_id.display_name if self.delivery_address_id else None,
            },
            'team': {
                'assigned_user': self.user_id.name if self.user_id else None,
                'coordinator': self.coordinator_id.name if self.coordinator_id else None,
            },
            'locations': [
                {
                    'id': loc.id,
                    'name': loc.name,
                    'address': getattr(loc, 'display_name', loc.name),
                }
                for loc in self.location_ids
            ],
            'created_date': self.create_date.isoformat(),
            'last_updated': self.write_date.isoformat(),
        }

