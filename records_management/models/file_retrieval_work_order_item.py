from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FileRetrievalWorkOrderItem(models.Model):
    _name = 'file.retrieval.work.order.item'
    _description = 'File Retrieval Work Order Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Item Reference",
        required=True,
        index=True,
        copy=False,
        default=lambda self: _('New'),
        help="Unique reference number for this retrieval item within the work order"
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help="Display name combining reference and file name for easy identification"
    )
    description = fields.Text(
        string="Description",
        help="Detailed description of the file or document to be retrieved"
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Order sequence for processing this item within the work order"
    )
    company_id = fields.Many2one(
        comodel_name='res.company',
        string='Company',
        related='work_order_id.company_id',
        store=True,
        help="Company responsible for this retrieval item"
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help="Uncheck to archive this item without deleting it"
    )

    # ============================================================================
    # WORK ORDER RELATIONSHIP
    # ============================================================================
    work_order_id = fields.Many2one(
        comodel_name='file.retrieval.work.order',
        string='Work Order',
        required=True,
        ondelete='cascade',
        index=True,
        help="Parent work order containing this retrieval item"
    )
    partner_id = fields.Many2one(
        comodel_name='res.partner',
        string='Customer',
        related='work_order_id.partner_id',
        store=True,
        help="Customer who requested this file retrieval"
    )
    work_order_state = fields.Selection(
        related='work_order_id.state',
        string='Work Order Status',
        store=True,
        help="Current status of the parent work order"
    )
    work_order_priority = fields.Selection(
        related='work_order_id.priority',
        string='Work Order Priority',
        store=True,
        help="Priority level inherited from parent work order"
    )

    # ============================================================================
    # FILE INFORMATION
    # ============================================================================
    file_name = fields.Char(
        string="File Name",
        required=True,
        index=True,
        help="Name of the file or document to be retrieved"
    )
    file_reference = fields.Char(
        string="File Reference",
        help="Customer's internal reference number for this file"
    )
    file_description = fields.Text(
        string="File Description",
        help="Detailed description of the file contents and purpose"
    )
    estimated_pages = fields.Integer(
        string="Estimated Pages",
        default=1,
        help="Estimated number of pages in this file"
    )
    actual_pages = fields.Integer(
        string="Actual Pages",
        help="Actual number of pages found during retrieval"
    )
    page_variance = fields.Integer(
        string="Page Variance",
        compute='_compute_page_metrics',
        store=True,
        help="Difference between estimated and actual pages"
    )
    page_accuracy_percentage = fields.Float(
        string="Page Accuracy %",
        compute='_compute_page_metrics',
        store=True,
        help="Accuracy percentage of page estimation"
    )

    # ============================================================================
    # FILE CLASSIFICATION
    # ============================================================================
    file_type = fields.Selection([
        ('document', 'Document'),
        ('folder', 'Folder'),
        ('book', 'Book/Manual'),
        ('blueprint', 'Blueprint'),
        ('photograph', 'Photograph'),
        ('certificate', 'Certificate'),
        ('contract', 'Contract'),
        ('correspondence', 'Correspondence'),
        ('report', 'Report'),
        ('other', 'Other')
    ], string="File Type", default='document', help="Classification of the file type")

    file_format = fields.Selection([
        ('paper', 'Paper'),
        ('digital', 'Digital'),
        ('microfilm', 'Microfilm'),
        ('blueprint_paper', 'Blueprint Paper'),
        ('photo_paper', 'Photographic Paper'),
        ('mixed', 'Mixed Format')
    ], string="File Format", default='paper', help="Physical format of the file")

    file_size = fields.Selection([
        ('letter', 'Letter (8.5x11)'),
        ('legal', 'Legal (8.5x14)'),
        ('tabloid', 'Tabloid (11x17)'),
        ('a4', 'A4'),
        ('a3', 'A3'),
        ('custom', 'Custom Size'),
        ('mixed', 'Mixed Sizes')
    ], string="File Size", help="Physical dimensions of the file")

    confidentiality_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal Use'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
        ('top_secret', 'Top Secret')
    ], string="Confidentiality Level", default='internal', help="Security classification level")

    # ============================================================================
    # LOCATION AND CONTAINER INFORMATION
    # ============================================================================
    container_id = fields.Many2one(
        comodel_name='records.container',
        string="Container",
        index=True,
        help="Physical container where this file is stored"
    )
    container_location = fields.Char(
        string="Container Location",
        related='container_id.location_id.name',
        readonly=True,
        store=True,
        help="Storage location of the container"
    )
    container_barcode = fields.Char(
        string="Container Barcode",
        related='container_id.barcode',
        readonly=True,
        store=True,
        help="Barcode identifier of the container"
    )
    location_notes = fields.Text(
        string="Location Notes",
        help="Additional notes about the file location within the container"
    )
    file_position = fields.Char(
        string="Position in Container",
        help="Specific position within the container (e.g., folder, section, page range)"
    )
    shelf_location = fields.Char(
        string="Shelf Location",
        help="Specific shelf or section location for easier retrieval"
    )
    access_difficulty = fields.Selection([
        ('easy', 'Easy Access'),
        ('moderate', 'Moderate Access'),
        ('difficult', 'Difficult Access'),
        ('restricted', 'Restricted Access')
    ], string="Access Difficulty", default='easy', help="Difficulty level for accessing this file")

    # ============================================================================
    # STREAMLINED STATUS WORKFLOW - FAST & EFFICIENT
    # ============================================================================
    status = fields.Selection([
        ('pending', 'Pending'),          # Waiting for technician assignment
        ('assigned', 'Assigned'),        # Assigned to technician
        ('retrieved', 'Retrieved'),      # File scanned and retrieved
        ('delivered', 'Delivered'),      # Delivered to customer
        ('not_found', 'Not Found'),      # File could not be located
        ('cancelled', 'Cancelled')       # Request cancelled
    ], string='Status', default='pending', tracking=True,
       help="Streamlined status for efficient barcode workflow")

    # ============================================================================
    # ESSENTIAL TRACKING FIELDS - STREAMLINED FOR BARCODE WORKFLOW
    # ============================================================================

    # Core dates for workflow tracking
    date_assigned = fields.Datetime(string="Assigned Date", help="When item was assigned to technician")
    date_retrieved = fields.Datetime(string="Retrieved Date", help="When file was scanned/retrieved")
    date_delivered = fields.Datetime(string="Delivered Date", help="When file was delivered to customer")

    # Simple condition tracking
    condition = fields.Selection([
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('damaged', 'Damaged')
    ], string="Condition", help="File condition when retrieved")

    notes = fields.Text(string="Notes", help="General notes about retrieval")

    # ============================================================================
    # TIMESTAMPS AND TRACKING
    # ============================================================================
    date_assigned = fields.Datetime(
        string="Date Assigned",
        help="When this item was assigned to a team member"
    )
    date_location_started = fields.Datetime(
        string="Location Started",
        help="When location process started"
    )
    date_located = fields.Datetime(
        string="Date Located",
        help="When the file was successfully located"
    )
    date_retrieval_started = fields.Datetime(
        string="Retrieval Started",
        help="When physical retrieval process started"
    )
    date_retrieved = fields.Datetime(
        string="Date Retrieved",
        help="When the file was successfully retrieved"
    )
    date_quality_checked = fields.Datetime(
        string="Date Quality Checked",
        help="When quality control was completed"
    )
    date_packaged = fields.Datetime(
        string="Date Packaged",
        help="When the file was packaged for delivery"
    )
    date_delivered = fields.Datetime(
        string="Date Delivered",
        help="When the file was delivered to customer"
    )

    # Duration calculations
    location_duration_hours = fields.Float(
        string="Location Duration (Hours)",
        compute='_compute_duration_metrics',
        store=True,
        help="Time taken to locate the file"
    )
    retrieval_duration_hours = fields.Float(
        string="Retrieval Duration (Hours)",
        compute='_compute_duration_metrics',
        store=True,
        help="Time taken to retrieve the file after location"
    )
    total_processing_hours = fields.Float(
        string="Total Processing Hours",
        compute='_compute_duration_metrics',
        store=True,
        help="Total time from assignment to completion"
    )

    # ============================================================================
    # TEAM ASSIGNMENT
    # ============================================================================
    assigned_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Assigned To",
        tracking=True,
        help="Team member assigned to retrieve this item"
    )
    locator_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Located By",
        help="Team member who located this file"
    )
    retriever_user_id = fields.Many2one(
        comodel_name='res.users',
        string="Retrieved By",
        help="Team member who physically retrieved this file"
    )
    quality_checker_id = fields.Many2one(
        comodel_name='res.users',
        string="Quality Checker",
        help="Team member who performed quality control"
    )
    coordinator_notes = fields.Text(
        string="Coordinator Notes",
        help="Notes from the work order coordinator"
    )

    # ============================================================================
    # SPECIAL REQUIREMENTS
    # ============================================================================
    special_handling_required = fields.Boolean(
        string="Special Handling Required",
        help="Whether this item requires special handling procedures"
    )
    special_handling_notes = fields.Text(
        string="Special Handling Notes",
        help="Details about required special handling"
    )
    fragile_item = fields.Boolean(
        string="Fragile Item",
        help="Mark if this is a fragile item requiring careful handling"
    )
    high_value_item = fields.Boolean(
        string="High Value Item",
        help="Mark if this is a high-value item requiring extra security"
    )
    rush_item = fields.Boolean(
        string="Rush Item",
        help="Mark if this item has urgent priority within the work order"
    )
    customer_priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string="Customer Priority", default='1', help="Priority assigned by customer")

    # ============================================================================
    # DELIVERY AND PACKAGING
    # ============================================================================
    packaging_type = fields.Selection([
        ('envelope', 'Envelope'),
        ('folder', 'Folder'),
        ('box', 'Document Box'),
        ('tube', 'Document Tube'),
        ('protective_sleeve', 'Protective Sleeve'),
        ('archival_box', 'Archival Box'),
        ('custom', 'Custom Packaging')
    ], string="Packaging Type", help="Type of packaging used for this item")

    packaging_notes = fields.Text(
        string="Packaging Notes",
        help="Special notes about packaging requirements or methods used"
    )
    delivery_method = fields.Selection([
        ('with_order', 'With Work Order'),
        ('separate', 'Separate Delivery'),
        ('scan_only', 'Scan Only'),
        ('digital_copy', 'Digital Copy')
    ], string="Delivery Method", default='with_order', help="How this item will be delivered")

    scan_required = fields.Boolean(
        string="Scan Required",
        help="Whether this item needs to be scanned"
    )
    scan_quality = fields.Selection([
        ('standard', 'Standard (200 DPI)'),
        ('high', 'High (300 DPI)'),
        ('archival', 'Archival (600 DPI)')
    ], string="Scan Quality", help="Required scanning quality/resolution")

    digital_copy_created = fields.Boolean(
        string="Digital Copy Created",
        help="Whether a digital copy has been created"
    )
    digital_file_size_mb = fields.Float(
        string="Digital File Size (MB)",
        help="Size of the digital copy in megabytes"
    )

    # ============================================================================
    # FINANCIAL AND COSTING
    # ============================================================================
    estimated_cost = fields.Float(
        string="Estimated Cost",
        help="Estimated cost for retrieving this specific item"
    )
    actual_cost = fields.Float(
        string="Actual Cost",
        help="Actual cost incurred for this item"
    )
    cost_variance = fields.Float(
        string="Cost Variance",
        compute='_compute_financial_metrics',
        store=True,
        help="Difference between estimated and actual costs"
    )
    cost_per_page = fields.Float(
        string="Cost per Page",
        compute='_compute_financial_metrics',
        store=True,
        help="Calculated cost per page for this item"
    )
    billable_hours = fields.Float(
        string="Billable Hours",
        help="Number of hours to bill for this item"
    )
    hourly_rate = fields.Float(
        string="Hourly Rate",
        help="Rate per hour for billing calculations"
    )

    # ============================================================================
    # ANALYTICS AND PERFORMANCE
    # ============================================================================
    retrieval_difficulty_score = fields.Float(
        string="Retrieval Difficulty Score",
        compute='_compute_performance_metrics',
        store=True,
        help="Score indicating retrieval difficulty (0-100)"
    )
    efficiency_score = fields.Float(
        string="Efficiency Score",
        compute='_compute_performance_metrics',
        store=True,
        help="Overall efficiency score for this item"
    )
    customer_importance = fields.Float(
        string="Customer Importance",
        default=50.0,
        help="Customer-assigned importance score (0-100)"
    )
    business_impact_score = fields.Float(
        string="Business Impact Score",
        compute='_compute_performance_metrics',
        store=True,
        help="Score indicating business impact of delays"
    )

    # ============================================================================
    # COMPLIANCE AND AUDIT
    # ============================================================================
    naid_compliant = fields.Boolean(
        string="NAID Compliant",
        default=True,
        help="Whether retrieval follows NAID compliance standards"
    )
    audit_trail_complete = fields.Boolean(
        string="Audit Trail Complete",
        compute='_compute_compliance_status',
        store=True,
        help="Whether complete audit trail exists for this item"
    )
    chain_of_custody_verified = fields.Boolean(
        string="Chain of Custody Verified",
        help="Whether chain of custody has been verified"
    )
    access_logged = fields.Boolean(
        string="Access Logged",
        default=True,
        help="Whether access to this item is being logged"
    )
    retention_category = fields.Char(
        string="Retention Category",
        help="Document retention category for compliance"
    )

    # ============================================================================
    # NOTES AND COMMUNICATION
    # ============================================================================
    internal_notes = fields.Text(
        string="Internal Notes",
        help="Internal notes not visible to customer"
    )
    customer_notes = fields.Text(
        string="Customer Notes",
        help="Notes that may be shared with customer"
    )
    retrieval_instructions = fields.Text(
        string="Retrieval Instructions",
        help="Specific instructions for retrieving this item"
    )
    handling_warnings = fields.Text(
        string="Handling Warnings",
        help="Important warnings about handling this item"
    )

    # ============================================================================
    # CONSTRAINT VALIDATION FRAMEWORK
    # ============================================================================
    @api.constrains('status', 'date_assigned', 'date_located', 'date_retrieved',
                    'date_quality_checked', 'date_packaged', 'date_delivered')
    def _check_status_date_consistency(self):
        """Validate that dates are consistent with status progression"""
        for record in self:
            # Status progression validation
            status_order = ['pending', 'assigned', 'locating', 'located', 'access_requested',
                           'retrieving', 'retrieved', 'quality_checking', 'quality_checked',
                           'packaging', 'packaged', 'delivered']

            current_index = status_order.index(record.status) if record.status in status_order else -1

            # Date requirements based on status
            if current_index >= status_order.index('assigned') and not record.date_assigned:
                raise ValidationError(_("Date Assigned is required for status: %s") % record.status)

            if current_index >= status_order.index('located') and not record.date_located:
                raise ValidationError(_("Date Located is required for status: %s") % record.status)

            if current_index >= status_order.index('retrieved') and not record.date_retrieved:
                raise ValidationError(_("Date Retrieved is required for status: %s") % record.status)

            if current_index >= status_order.index('quality_checked') and not record.date_quality_checked:
                raise ValidationError(_("Date Quality Checked is required for status: %s") % record.status)

            if current_index >= status_order.index('packaged') and not record.date_packaged:
                raise ValidationError(_("Date Packaged is required for status: %s") % record.status)

            if current_index >= status_order.index('delivered') and not record.date_delivered:
                raise ValidationError(_("Date Delivered is required for status: %s") % record.status)

            # Chronological order validation
            dates_to_check = [
                (record.date_assigned, 'Date Assigned'),
                (record.date_located, 'Date Located'),
                (record.date_retrieved, 'Date Retrieved'),
                (record.date_quality_checked, 'Date Quality Checked'),
                (record.date_packaged, 'Date Packaged'),
                (record.date_delivered, 'Date Delivered')
            ]

            previous_date = None
            previous_field = None

            for date_value, field_name in dates_to_check:
                if date_value:
                    if previous_date and date_value < previous_date:
                        raise ValidationError(
                            _("%s (%s) cannot be earlier than %s (%s)") %
                            (field_name, date_value, previous_field, previous_date)
                        )
                    previous_date = date_value
                    previous_field = field_name

    @api.constrains('quality_approved', 'status', 'quality_score')
    def _check_quality_requirements(self):
        """Validate quality approval requirements and constraints"""
        for record in self:
            # Quality approval required for certain statuses
            if record.status in ['quality_checked', 'packaging', 'packaged', 'delivered']:
                if record.quality_approved is None:
                    raise ValidationError(
                        _("Quality approval decision is required for status: %s") % record.status
                    )

            # Cannot proceed if quality not approved
            if record.status in ['packaging', 'packaged', 'delivered'] and record.quality_approved is False:
                raise ValidationError(
                    _("Cannot proceed to %s status without quality approval") % record.status
                )

            # Quality score validation
            if record.quality_score < 0 or record.quality_score > 100:
                raise ValidationError(_("Quality score must be between 0 and 100"))

            # Minimum quality threshold for delivery
            if record.status == 'delivered' and record.quality_score < 50:
                raise ValidationError(
                    _("Items with quality score below 50 cannot be delivered without special approval")
                )

    @api.constrains('estimated_pages', 'actual_pages')
    def _check_page_constraints(self):
        """Validate page counts and related constraints"""
        for record in self:
            if record.estimated_pages is not None and record.estimated_pages < 0:
                raise ValidationError(_("Estimated pages cannot be negative"))

            if record.actual_pages is not None and record.actual_pages < 0:
                raise ValidationError(_("Actual pages cannot be negative"))

            # Warning for significant variances
            if (record.estimated_pages and record.actual_pages and
                record.estimated_pages > 0):
                variance_percent = abs(record.actual_pages - record.estimated_pages) / record.estimated_pages * 100

                if variance_percent > 200:  # 200% variance
                    raise ValidationError(
                        _("Page variance of %d%% is unusually high. Please verify the counts.") %
                        variance_percent
                    )

    @api.constrains('estimated_cost', 'actual_cost')
    def _check_cost_constraints(self):
        """Validate cost constraints and business rules"""
        for record in self:
            if record.estimated_cost is not None and record.estimated_cost < 0:
                raise ValidationError(_("Estimated cost cannot be negative"))

            if record.actual_cost is not None and record.actual_cost < 0:
                raise ValidationError(_("Actual cost cannot be negative"))

            # Cost variance threshold validation
            if (record.estimated_cost and record.actual_cost and
                record.estimated_cost > 0):
                variance_percent = abs(record.actual_cost - record.estimated_cost) / record.estimated_cost * 100

                if variance_percent > 300:  # 300% cost variance
                    raise ValidationError(
                        _("Cost variance of %d%% exceeds acceptable limits. Please review.") %
                        variance_percent
                    )

    @api.constrains('customer_priority', 'work_order_id')
    def _check_priority_consistency(self):
        """Validate priority consistency between item and work order"""
        for record in self:
            if record.work_order_id and record.customer_priority:
                # Item priority should not exceed work order priority by more than 1 level
                item_priority = int(record.customer_priority)
                wo_priority = int(record.work_order_id.customer_priority or '1')

                if item_priority > wo_priority + 1:
                    raise ValidationError(
                        _("Item priority (%s) cannot be significantly higher than work order priority (%s)") %
                        (item_priority, wo_priority)
                    )

    @api.constrains('assigned_to_id', 'team_lead_id', 'reviewer_id')
    def _check_team_assignment_rules(self):
        """Validate team assignment business rules"""
        for record in self:
            # Cannot assign to same person for different roles
            if record.assigned_to_id and record.team_lead_id:
                if record.assigned_to_id == record.team_lead_id:
                    raise ValidationError(_("Team lead cannot be the same as the assigned team member"))

            if record.assigned_to_id and record.reviewer_id:
                if record.assigned_to_id == record.reviewer_id:
                    raise ValidationError(_("Reviewer cannot be the same as the assigned team member"))

            # Reviewer required for high-value items
            if record.high_value_item and record.status in ['quality_checking', 'quality_checked']:
                if not record.reviewer_id:
                    raise ValidationError(_("Reviewer assignment is required for high-value items"))

    @api.constrains('rush_item', 'work_order_id')
    def _check_rush_item_constraints(self):
        """Validate rush item business rules"""
        for record in self:
            if record.rush_item:
                # Rush items require higher priority
                if record.customer_priority in ['0']:  # Low priority
                    raise ValidationError(_("Rush items cannot have low priority"))

                # Rush items should have work order rush flag
                if record.work_order_id and not record.work_order_id.rush_delivery:
                    raise ValidationError(
                        _("Rush items should be part of a rush delivery work order")
                    )

    @api.constrains('chain_of_custody_verified', 'status', 'high_value_item')
    def _check_chain_of_custody_requirements(self):
        """Validate chain of custody requirements"""
        for record in self:
            # Chain of custody required for certain statuses
            custody_required_statuses = ['retrieved', 'quality_checked', 'packaged', 'delivered']

            if record.status in custody_required_statuses and not record.chain_of_custody_verified:
                raise ValidationError(
                    _("Chain of custody verification is required for status: %s") % record.status
                )

            # High-value items require custody verification earlier
            if (record.high_value_item and
                record.status in ['located', 'retrieving'] and
                not record.chain_of_custody_verified):
                raise ValidationError(
                    _("High-value items require chain of custody verification before retrieval")
                )

    @api.constrains('delivery_method', 'packaging_type', 'digital_delivery_format')
    def _check_delivery_consistency(self):
        """Validate delivery method and packaging consistency"""
        for record in self:
            # Digital delivery validation
            if record.delivery_method == 'digital':
                if not record.digital_delivery_format:
                    raise ValidationError(
                        _("Digital delivery format is required for digital delivery method")
                    )

                # Packaging should be minimal for digital delivery
                if record.packaging_type in ['archival_box', 'protective_case']:
                    raise ValidationError(
                        _("Physical packaging type '%s' is incompatible with digital delivery") %
                        record.packaging_type
                    )

            # Physical delivery validation
            if record.delivery_method in ['courier', 'pickup', 'mail']:
                if not record.packaging_type:
                    raise ValidationError(
                        _("Packaging type is required for physical delivery method")
                    )

    @api.constrains('confidentiality_level', 'access_level', 'special_handling_required')
    def _check_security_requirements(self):
        """Validate security and confidentiality requirements"""
        for record in self:
            # High confidentiality requires special handling
            confidential_levels = ['confidential', 'highly_confidential', 'top_secret']

            if record.confidentiality_level in confidential_levels:
                if not record.special_handling_required:
                    raise ValidationError(
                        _("Special handling is required for confidentiality level: %s") %
                        record.confidentiality_level
                    )

                # Restricted access for confidential items
                if record.access_level not in ['restricted', 'authorized_only']:
                    raise ValidationError(
                        _("Confidential items require restricted access level")
                    )

            # Top secret requires additional security
            if record.confidentiality_level == 'top_secret':
                if not record.chain_of_custody_verified:
                    raise ValidationError(
                        _("Top secret items require chain of custody verification")
                    )

    @api.constrains('billable_hours', 'hourly_rate', 'estimated_cost')
    def _check_billing_consistency(self):
        """Validate billing and financial consistency"""
        for record in self:
            if record.billable_hours is not None and record.billable_hours < 0:
                raise ValidationError(_("Billable hours cannot be negative"))

            if record.hourly_rate is not None and record.hourly_rate < 0:
                raise ValidationError(_("Hourly rate cannot be negative"))

            # Validate estimated cost calculation
            if (record.billable_hours and record.hourly_rate and record.estimated_cost):
                calculated_cost = record.billable_hours * record.hourly_rate
                variance = abs(calculated_cost - record.estimated_cost)

                if variance > 10:  # $10 tolerance
                    raise ValidationError(
                        _("Estimated cost (%s) does not match calculated cost (%s) based on hours and rate") %
                        (record.estimated_cost, calculated_cost)
                    )

    @api.constrains('name', 'work_order_id')
    def _check_unique_reference_per_order(self):
        """Validate unique item references within work orders"""
        for record in self:
            if record.work_order_id and record.name and record.name != _('New'):
                domain = [
                    ('work_order_id', '=', record.work_order_id.id),
                    ('name', '=', record.name),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("Item reference '%s' must be unique per work order.") % record.name)

    @api.constrains('overall_performance_score', 'quality_score', 'efficiency_score')
    def _check_performance_score_validity(self):
        """Validate performance score calculations"""
        for record in self:
            scores_to_check = [
                (record.overall_performance_score, 'Overall Performance Score'),
                (record.quality_score, 'Quality Score'),
                (record.efficiency_score, 'Efficiency Score'),
            ]

            for score, field_name in scores_to_check:
                if score is not None and (score < 0 or score > 100):
                    raise ValidationError(
                        _("%s must be between 0 and 100, got: %s") % (field_name, score)
                    )

    # ============================================================================
    # COMPUTED METHODS - ENHANCED ANALYTICS AND SCORING
    # ============================================================================
    @api.depends('name', 'file_name', 'file_reference')
    def _compute_display_name(self):
        """Enhanced display name with comprehensive information"""
        for record in self:
            components = []

            if record.name and record.name != _('New'):
                components.append(record.name)

            if record.file_name:
                components.append(record.file_name)

            if record.file_reference:
                components.append(f"[{record.file_reference}]")

            if record.status and record.status != 'pending':
                status_display = dict(record._fields['status'].selection)[record.status]
                components.append(f"({status_display})")

            record.display_name = " - ".join(components) if components else _("New Item")

    @api.depends('estimated_pages', 'actual_pages')
    def _compute_page_metrics(self):
        """Calculate page-related metrics and accuracy"""
        for record in self:
            if record.estimated_pages and record.actual_pages:
                record.page_variance = record.actual_pages - record.estimated_pages

                # Calculate accuracy percentage
                if record.estimated_pages > 0:
                    accuracy = 100 - (abs(record.page_variance) / record.estimated_pages * 100)
                    record.page_accuracy_percentage = max(0, accuracy)
                else:
                    record.page_accuracy_percentage = 0
            else:
                record.page_variance = 0
                record.page_accuracy_percentage = 0

    @api.depends('status')
    def _compute_progress_metrics(self):
        """Calculate progress percentage based on status"""
        status_progress = {
            'pending': 0,
            'assigned': 5,
            'locating': 15,
            'located': 30,
            'access_requested': 35,
            'retrieving': 50,
            'retrieved': 70,
            'quality_checking': 80,
            'quality_checked': 85,
            'packaging': 90,
            'packaged': 95,
            'delivered': 100,
            'not_found': 0,
            'damaged': 60,  # Partial progress since item was found
            'access_denied': 20,
            'cancelled': 0,
        }

        for record in self:
            record.progress_percentage = status_progress.get(record.status, 0)

    @api.depends('condition', 'quality_approved', 'actual_pages', 'estimated_pages', 'quality_issues')
    def _compute_quality_metrics(self):
        """Calculate comprehensive quality metrics"""
        for record in self:
            quality_score = 100.0
            completeness_score = 100.0

            # Condition scoring
            condition_scores = {
                'excellent': 100,
                'good': 85,
                'fair': 70,
                'poor': 50,
                'damaged': 25,
                'deteriorated': 30,
                'fragile': 80,  # Not necessarily low quality, just requires care
            }

            if record.condition:
                quality_score = condition_scores.get(record.condition, 100)

            # Quality approval impact
            if record.quality_approved is False:  # Explicitly not approved
                quality_score *= 0.5

            # Page completeness scoring
            if record.estimated_pages and record.actual_pages:
                if record.actual_pages >= record.estimated_pages:
                    completeness_score = 100
                else:
                    completeness_score = (record.actual_pages / record.estimated_pages) * 100
            elif record.estimated_pages and not record.actual_pages:
                completeness_score = 0  # Expected pages but none found

            # Quality issues impact
            if record.quality_issues:
                issue_count = len(record.quality_issues.split('\n')) if record.quality_issues else 0
                quality_score -= min(issue_count * 10, 50)  # Max 50 point reduction

            # Status-based adjustments
            if record.status == 'not_found':
                quality_score = 0
                completeness_score = 0
            elif record.status == 'damaged':
                quality_score = min(quality_score, 40)

            record.quality_score = max(0, quality_score)
            record.completeness_score = max(0, completeness_score)

    @api.depends('date_assigned', 'date_located', 'date_retrieved', 'date_quality_checked', 'date_delivered')
    def _compute_duration_metrics(self):
        """Calculate time duration metrics for performance analysis"""
        for record in self:
            record.location_duration_hours = 0
            record.retrieval_duration_hours = 0
            record.total_processing_hours = 0

            # Location duration
            if record.date_assigned and record.date_located:
                location_delta = record.date_located - record.date_assigned
                record.location_duration_hours = location_delta.total_seconds() / 3600

            # Retrieval duration
            if record.date_located and record.date_retrieved:
                retrieval_delta = record.date_retrieved - record.date_located
                record.retrieval_duration_hours = retrieval_delta.total_seconds() / 3600

            # Total processing duration
            if record.date_assigned:
                end_date = (record.date_delivered or
                           record.date_packaged or
                           record.date_quality_checked or
                           record.date_retrieved or
                           fields.Datetime.now())

                total_delta = end_date - record.date_assigned
                record.total_processing_hours = total_delta.total_seconds() / 3600

    @api.depends('estimated_cost', 'actual_cost', 'actual_pages', 'billable_hours', 'hourly_rate')
    def _compute_financial_metrics(self):
        """Calculate financial and costing metrics"""
        for record in self:
            # Cost variance
            if record.estimated_cost and record.actual_cost:
                record.cost_variance = record.actual_cost - record.estimated_cost
            else:
                record.cost_variance = 0

            # Cost per page
            cost_for_calculation = record.actual_cost or record.estimated_cost or 0
            pages_for_calculation = record.actual_pages or record.estimated_pages or 0

            if pages_for_calculation > 0:
                record.cost_per_page = cost_for_calculation / pages_for_calculation
            else:
                record.cost_per_page = 0

            # Update estimated cost if not set
            if not record.estimated_cost and record.billable_hours and record.hourly_rate:
                record.estimated_cost = record.billable_hours * record.hourly_rate

    @api.depends('access_difficulty', 'file_type', 'condition', 'special_handling_required',
                 'location_duration_hours', 'retrieval_duration_hours')
    def _compute_performance_metrics(self):
        """Calculate performance and difficulty metrics"""
        for record in self:
            # Base difficulty scoring
            difficulty_score = 20  # Base score

            # Access difficulty impact
            access_scores = {
                'easy': 10,
                'moderate': 25,
                'difficult': 50,
                'restricted': 75,
            }
            difficulty_score += access_scores.get(record.access_difficulty, 25)

            # File type complexity
            type_complexity = {
                'document': 5,
                'folder': 15,
                'book': 20,
                'blueprint': 30,
                'photograph': 25,
                'certificate': 10,
                'contract': 15,
                'correspondence': 8,
                'report': 12,
                'other': 20,
            }
            difficulty_score += type_complexity.get(record.file_type, 20)

            # Condition impact
            condition_difficulty = {
                'excellent': 0,
                'good': 5,
                'fair': 15,
                'poor': 30,
                'damaged': 40,
                'deteriorated': 35,
                'fragile': 50,
            }
            difficulty_score += condition_difficulty.get(record.condition, 10)

            # Special handling requirements
            if record.special_handling_required:
                difficulty_score += 20
            if record.fragile_item:
                difficulty_score += 15
            if record.high_value_item:
                difficulty_score += 10

            record.retrieval_difficulty_score = min(100, difficulty_score)

            # Efficiency scoring (inverse of time taken vs standard)
            efficiency_score = 100

            # Standard benchmarks (hours)
            standard_location_time = 0.5
            standard_retrieval_time = 0.3

            if record.location_duration_hours > 0:
                location_efficiency = (standard_location_time / record.location_duration_hours) * 100
                efficiency_score = min(efficiency_score, location_efficiency)

            if record.retrieval_duration_hours > 0:
                retrieval_efficiency = (standard_retrieval_time / record.retrieval_duration_hours) * 100
                efficiency_score = min(efficiency_score, retrieval_efficiency)

            # Quality impact on efficiency
            if record.quality_score < 80:
                efficiency_score *= (record.quality_score / 100)

            record.efficiency_score = max(0, min(100, efficiency_score))

            # Business impact scoring
            impact_score = record.customer_importance or 50

            # Priority impact
            priority_multipliers = {
                '0': 0.5,  # Low
                '1': 1.0,  # Normal
                '2': 1.5,  # High
                '3': 2.0,  # Urgent
            }
            multiplier = priority_multipliers.get(record.customer_priority, 1.0)
            impact_score *= multiplier

            # Work order priority impact
            if record.work_order_priority:
                wo_multipliers = {
                    '0': 0.8,
                    '1': 1.0,
                    '2': 1.3,
                    '3': 1.8,
                }
                wo_multiplier = wo_multipliers.get(record.work_order_priority, 1.0)
                impact_score *= wo_multiplier

            # Rush item bonus
            if record.rush_item:
                impact_score *= 1.5

            record.business_impact_score = min(100, impact_score)

    @api.depends('status', 'date_assigned', 'date_located', 'date_retrieved', 'quality_approved',
                 'chain_of_custody_verified', 'access_logged')
    def _compute_compliance_status(self):
        """Calculate compliance and audit trail completeness"""
        for record in self:
            audit_complete = True

            # Check required timestamps based on status
            if record.status in ['located', 'retrieved', 'quality_checked', 'packaged', 'delivered']:
                if not record.date_assigned:
                    audit_complete = False
                if not record.date_located:
                    audit_complete = False

            if record.status in ['retrieved', 'quality_checked', 'packaged', 'delivered']:
                if not record.date_retrieved:
                    audit_complete = False

            if record.status in ['quality_checked', 'packaged', 'delivered']:
                if not record.date_quality_checked:
                    audit_complete = False
                if record.quality_approved is None:  # Must be explicitly approved/rejected
                    audit_complete = False

            # Chain of custody requirements
            if record.status in ['retrieved', 'quality_checked', 'packaged', 'delivered']:
                if not record.chain_of_custody_verified:
                    audit_complete = False

            # Access logging requirements
            if not record.access_logged:
                audit_complete = False

            record.audit_trail_complete = audit_complete

    @api.depends('status', 'progress_percentage', 'quality_score', 'efficiency_score')
    def _compute_overall_performance_score(self):
        """Calculate overall performance score combining multiple factors"""
        for record in self:
            if record.status in ['not_found', 'cancelled']:
                record.overall_performance_score = 0
            else:
                # Weighted scoring
                progress_weight = 0.3
                quality_weight = 0.4
                efficiency_weight = 0.3

                overall_score = (
                    (record.progress_percentage * progress_weight) +
                    (record.quality_score * quality_weight) +
                    (record.efficiency_score * efficiency_weight)
                )

                record.overall_performance_score = overall_score

    # ============================================================================
    # ADDITIONAL COMPUTED FIELDS FOR ANALYTICS
    # ============================================================================
    overall_performance_score = fields.Float(
        string="Overall Performance Score",
        compute='_compute_overall_performance_score',
        store=True,
        help="Composite score combining progress, quality, and efficiency"
    )

    @api.depends('status', 'date_assigned', 'work_order_id.scheduled_date')
    def _compute_urgency_indicators(self):
        """Calculate urgency and deadline indicators"""
        for record in self:
            record.is_overdue = False
            record.days_until_deadline = 0
            record.urgency_level = 'normal'

            if record.work_order_id.scheduled_date and record.date_assigned:
                deadline = record.work_order_id.scheduled_date
                current_date = fields.Date.today()

                delta = deadline - current_date
                record.days_until_deadline = delta.days

                # Determine if overdue
                if delta.days < 0 and record.status not in ['delivered', 'packaged']:
                    record.is_overdue = True

                # Determine urgency level
                if delta.days <= 1:
                    record.urgency_level = 'critical'
                elif delta.days <= 3:
                    record.urgency_level = 'high'
                elif delta.days <= 7:
                    record.urgency_level = 'medium'
                else:
                    record.urgency_level = 'normal'

    is_overdue = fields.Boolean(
        string="Is Overdue",
        compute='_compute_urgency_indicators',
        store=True,
        help="Whether this item is past its deadline"
    )

    days_until_deadline = fields.Integer(
        string="Days Until Deadline",
        compute='_compute_urgency_indicators',
        store=True,
        help="Number of days until work order deadline"
    )

    urgency_level = fields.Selection([
        ('normal', 'Normal'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('critical', 'Critical')
    ], string="Urgency Level", compute='_compute_urgency_indicators', store=True, help="Calculated urgency level")

    @api.depends('container_id', 'location_duration_hours', 'access_difficulty')
    def _compute_location_efficiency_metrics(self):
        """Calculate location-specific efficiency metrics"""
        for record in self:
            record.location_accessibility_score = 100
            record.container_efficiency_score = 100

            # Access difficulty impact
            access_scores = {
                'easy': 100,
                'moderate': 75,
                'difficult': 50,
                'restricted': 25,
            }
            record.location_accessibility_score = access_scores.get(record.access_difficulty, 75)

            # Container organization efficiency
            if record.container_id:
                # This could be enhanced with container-specific metrics
                container_items = self.search_count([
                    ('container_id', '=', record.container_id.id),
                    ('status', 'in', ['located', 'retrieved', 'quality_checked', 'packaged'])
                ])

                if container_items > 10:  # High-traffic container
                    record.container_efficiency_score = 85
                elif container_items > 5:
                    record.container_efficiency_score = 90

            # Time efficiency adjustment
            if record.location_duration_hours:
                if record.location_duration_hours <= 0.25:  # 15 minutes
                    record.location_accessibility_score = min(100, record.location_accessibility_score + 10)
                elif record.location_duration_hours > 2:  # Over 2 hours
                    record.location_accessibility_score *= 0.7

    location_accessibility_score = fields.Float(
        string="Location Accessibility Score",
        compute='_compute_location_efficiency_metrics',
        store=True,
        help="Score indicating how accessible this item's location is"
    )

    container_efficiency_score = fields.Float(
        string="Container Efficiency Score",
        compute='_compute_location_efficiency_metrics',
        store=True,
        help="Score indicating container organization efficiency"
    )

    # ============================================================================
    # COMPREHENSIVE ACTION METHODS
    # ============================================================================

    # Status Transition Actions
    def action_assign(self):
        """Assign item to team member"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only pending items can be assigned"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Assign Item'),
            'res_model': 'file.retrieval.assignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_start_location(self):
        """Start the location process"""
        self.ensure_one()
        if self.status not in ['assigned', 'pending']:
            raise UserError(_("Item must be assigned before starting location"))

        if not self.assigned_to_id:
            raise UserError(_("Item must be assigned to a team member before starting location"))

        self.write({
            'status': 'locating',
            'date_assigned': self.date_assigned or fields.Datetime.now()
        })

        self.message_post(
            body=_("Location process started by %s") % self.env.user.name,
            message_type="notification"
        )

        return True

    def action_mark_located(self):
        """Mark item as located"""
        self.ensure_one()
        if self.status not in ['locating', 'assigned']:
            raise UserError(_("Item must be in locating status to mark as located"))

        self.write({
            'status': 'located',
            'date_located': fields.Datetime.now()
        })

        self.message_post(
            body=_("File located by %s") % self.env.user.name,
            message_type="notification"
        )

        # Send notification to work order coordinator
        self._send_location_notification()

        return True

    def action_request_access(self):
        """Request access to restricted location"""
        self.ensure_one()
        if self.status != 'located':
            raise UserError(_("Item must be located before requesting access"))

        if self.access_difficulty not in ['restricted']:
            raise UserError(_("Access request is only needed for restricted locations"))

        self.write({
            'status': 'access_requested',
            'access_logged': True
        })

        self.message_post(
            body=_("Access requested for restricted location by %s") % self.env.user.name,
            message_type="notification"
        )

        return True

    def action_start_retrieval(self):
        """Start the retrieval process"""
        self.ensure_one()
        if self.status not in ['located', 'access_requested']:
            raise UserError(_("Item must be located (and have access if needed) before starting retrieval"))

        self.write({
            'status': 'retrieving'
        })

        self.message_post(
            body=_("Retrieval started by %s") % self.env.user.name,
            message_type="notification"
        )

        return True

    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.ensure_one()
        if self.status not in ['retrieving', 'located', 'access_requested']:
            raise UserError(_("Item must be in retrieval process to mark as retrieved"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark as Retrieved'),
            'res_model': 'file.retrieval.retrieved.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_quality_check(self):
        """Initiate quality check process"""
        self.ensure_one()
        if self.status != 'retrieved':
            raise UserError(_("Item must be retrieved before quality check"))

        self.write({
            'status': 'quality_checking'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Quality Check'),
            'res_model': 'file.quality.check.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
                'default_condition': self.condition,
                'default_actual_pages': self.actual_pages,
            }
        }

    def action_approve_quality(self):
        """Approve quality check"""
        self.ensure_one()
        if self.status not in ['quality_checking', 'retrieved']:
            raise UserError(_("Item must be in quality checking status"))

        self.write({
            'status': 'quality_checked',
            'quality_approved': True,
            'date_quality_checked': fields.Datetime.now(),
            'reviewer_id': self.env.user.id
        })

        self.message_post(
            body=_("Quality approved by %s") % self.env.user.name,
            message_type="notification"
        )

        return True

    def action_reject_quality(self):
        """Reject quality check"""
        self.ensure_one()
        if self.status not in ['quality_checking', 'retrieved']:
            raise UserError(_("Item must be in quality checking status"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reject Quality'),
            'res_model': 'file.quality.rejection.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_start_packaging(self):
        """Start packaging process"""
        self.ensure_one()
        if self.status != 'quality_checked':
            raise UserError(_("Item must pass quality check before packaging"))

        if not self.quality_approved:
            raise UserError(_("Only quality-approved items can be packaged"))

        self.write({
            'status': 'packaging'
        })

        return {
            'type': 'ir.actions.act_window',
            'name': _('Package Item'),
            'res_model': 'file.packaging.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_mark_packaged(self):
        """Mark item as packaged"""
        self.ensure_one()
        if self.status not in ['packaging', 'quality_checked']:
            raise UserError(_("Item must be in packaging status"))

        self.write({
            'status': 'packaged',
            'date_packaged': fields.Datetime.now()
        })

        self.message_post(
            body=_("Item packaged by %s") % self.env.user.name,
            message_type="notification"
        )

        return True

    def action_deliver(self):
        """Deliver item to customer"""
        self.ensure_one()
        if self.status != 'packaged':
            raise UserError(_("Item must be packaged before delivery"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Deliver Item'),
            'res_model': 'file.delivery.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
                'default_delivery_method': self.delivery_method,
            }
        }

    def action_mark_delivered(self):
        """Mark item as delivered (internal use)"""
        self.ensure_one()
        self.write({
            'status': 'delivered',
            'date_delivered': fields.Datetime.now()
        })

        self.message_post(
            body=_("Item delivered by %s") % self.env.user.name,
            message_type="notification"
        )

        # Update work order progress
        if self.work_order_id and hasattr(self.work_order_id, '_update_progress_metrics'):
            self.work_order_id._update_progress_metrics()

        return True

    # Team Coordination Actions
    def action_reassign_team(self):
        """Reassign item to different team member"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reassign Team'),
            'res_model': 'file.retrieval.reassignment.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_current_assignee_id': self.assigned_to_id.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_escalate_priority(self):
        """Escalate item priority"""
        self.ensure_one()

        current_priority = int(self.customer_priority or '1')
        if current_priority >= 3:
            raise UserError(_("Item is already at maximum priority"))

        new_priority = str(current_priority + 1)

        self.write({
            'customer_priority': new_priority,
            'rush_item': new_priority == '3'  # Urgent items are rush items
        })

        self.message_post(
            body=_("Priority escalated to %s by %s") % (
                dict(self._fields['customer_priority'].selection)[new_priority],
                self.env.user.name
            ),
            message_type="notification"
        )

        # Send escalation notification
        self._send_escalation_notification()

        return True

    def action_request_support(self):
        """Request support for difficult retrieval"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Request Support'),
            'res_model': 'file.support.request.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
                'default_requested_by_id': self.env.user.id,
            }
        }

    # Status Management Actions
    def action_mark_not_found(self):
        """Mark item as not found"""
        self.ensure_one()
        if self.status in ['delivered', 'packaged']:
            raise UserError(_("Cannot mark delivered or packaged items as not found"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark as Not Found'),
            'res_model': 'file.not.found.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_mark_damaged(self):
        """Mark item as damaged"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Mark as Damaged'),
            'res_model': 'file.damage.report.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_reset_status(self):
        """Reset item status (admin only)"""
        self.ensure_one()

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only Records Managers can reset item status"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Reset Status'),
            'res_model': 'file.status.reset.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_current_status': self.status,
            }
        }

    def action_cancel_item(self):
        """Cancel item retrieval"""
        self.ensure_one()

        if self.status in ['delivered']:
            raise UserError(_("Cannot cancel delivered items"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Cancel Item'),
            'res_model': 'file.cancellation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    def action_force_complete(self):
        """Force complete item (emergency use)"""
        self.ensure_one()

        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only Records Managers can force complete items"))

        self.write({
            'status': 'delivered',
            'date_delivered': fields.Datetime.now(),
            'force_completed': True
        })

        self.message_post(
            body=_("Item force completed by %s - Emergency override") % self.env.user.name,
            message_type="notification"
        )

        return True

    # Quality Management Actions
    def action_request_quality_review(self):
        """Request additional quality review"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Request Quality Review'),
            'res_model': 'file.quality.review.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
                'default_current_quality_score': self.quality_score,
            }
        }

    def action_create_digital_copy(self):
        """Create digital copy of document"""
        self.ensure_one()

        if self.status not in ['retrieved', 'quality_checking', 'quality_checked']:
            raise UserError(_("Item must be retrieved before creating digital copy"))

        return {
            'type': 'ir.actions.act_window',
            'name': _('Create Digital Copy'),
            'res_model': 'file.digital.copy.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    # Workflow Management Actions
    def action_view_audit_trail(self):
        """View complete audit trail for item"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Audit Trail - %s') % self.name,
            'res_model': 'naid.audit.log',
            'view_mode': 'tree,form',
            'domain': [
                ('reference_model', '=', self._name),
                ('reference_id', '=', self.id)
            ],
            'context': {'create': False}
        }

    def action_generate_performance_report(self):
        """Generate performance report for item"""
        self.ensure_one()

        return {
            'type': 'ir.actions.act_window',
            'name': _('Performance Report - %s') % self.name,
            'res_model': 'file.retrieval.performance.report',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_item_id': self.id,
                'default_work_order_id': self.work_order_id.id,
            }
        }

    # ============================================================================
    # NOTIFICATION HELPER METHODS
    # ============================================================================
    def _send_location_notification(self):
        """Send notification when item is located"""
        try:
            if self.work_order_id.customer_id:
                template_id = self.env.ref('records_management.email_template_item_located', False)
                if template_id:
                    template_id.send_mail(self.id, force_send=False)
        except Exception as e:
            _logger.warning("Failed to send location notification: %s", str(e))

    def _send_escalation_notification(self):
        """Send notification for priority escalation"""
        try:
            template_id = self.env.ref('records_management.email_template_priority_escalation', False)
            if template_id:
                template_id.send_mail(self.id, force_send=False)
        except Exception as e:
            _logger.warning("Failed to send escalation notification: %s", str(e))

    # ============================================================================
    # ENHANCED ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Enhanced create with audit logging and business rule validation"""
        for vals in vals_list:
            # Generate sequence-based name if not provided
            if vals.get("name", _("New")) == _("New"):
                sequence_code = 'file.retrieval.work.order.item'
                vals["name"] = self.env["ir.sequence"].next_by_code(sequence_code) or _("New")

            # Set default dates based on status
            if vals.get('status') == 'assigned' and not vals.get('date_assigned'):
                vals['date_assigned'] = fields.Datetime.now()

            # Set default priority if not specified
            if not vals.get('customer_priority'):
                vals['customer_priority'] = '1'  # Normal priority

            # Initialize tracking fields
            if not vals.get('access_logged'):
                vals['access_logged'] = True

            # Set initial audit information
            vals.update({
                'created_by_id': self.env.user.id,
                'last_updated_by_id': self.env.user.id,
            })

        # Create records
        records = super().create(vals_list)

        # Post-creation activities
        for record in records:
            # Create audit log entry
            record._create_audit_log('created', 'Item created', {
                'reference': record.name,
                'work_order': record.work_order_id.name if record.work_order_id else None,
                'status': record.status,
                'assigned_to': record.assigned_to_id.name if record.assigned_to_id else None,
            })

            # Update work order metrics
            if record.work_order_id and hasattr(record.work_order_id, '_update_progress_metrics'):
                record.work_order_id._update_progress_metrics()

            # Send notifications for assignments
            if record.assigned_to_id:
                record._send_assignment_notification()

        return records

    def write(self, vals):
        """Enhanced write with change tracking and notifications"""
        # Track changes for audit logging
        changes_to_log = {}
        status_changed = False
        assignment_changed = False

        for record in self:
            # Track status changes
            if 'status' in vals and vals['status'] != record.status:
                changes_to_log['status_change'] = {
                    'from': record.status,
                    'to': vals['status']
                }
                status_changed = True

                # Auto-set timestamps based on status
                if vals['status'] == 'assigned' and not vals.get('date_assigned'):
                    vals['date_assigned'] = fields.Datetime.now()
                elif vals['status'] == 'located' and not vals.get('date_located'):
                    vals['date_located'] = fields.Datetime.now()
                elif vals['status'] == 'retrieved' and not vals.get('date_retrieved'):
                    vals['date_retrieved'] = fields.Datetime.now()
                elif vals['status'] == 'quality_checked' and not vals.get('date_quality_checked'):
                    vals['date_quality_checked'] = fields.Datetime.now()
                elif vals['status'] == 'packaged' and not vals.get('date_packaged'):
                    vals['date_packaged'] = fields.Datetime.now()
                elif vals['status'] == 'delivered' and not vals.get('date_delivered'):
                    vals['date_delivered'] = fields.Datetime.now()

            # Track assignment changes
            if 'assigned_to_id' in vals and vals['assigned_to_id'] != record.assigned_to_id.id:
                changes_to_log['assignment_change'] = {
                    'from': record.assigned_to_id.name if record.assigned_to_id else None,
                    'to': self.env['res.users'].browse(vals['assigned_to_id']).name if vals['assigned_to_id'] else None
                }
                assignment_changed = True

            # Track quality approval changes
            if 'quality_approved' in vals and vals['quality_approved'] != record.quality_approved:
                changes_to_log['quality_approval'] = {
                    'from': record.quality_approved,
                    'to': vals['quality_approved'],
                    'reviewer': self.env.user.name
                }

            # Track priority changes
            if 'customer_priority' in vals and vals['customer_priority'] != record.customer_priority:
                changes_to_log['priority_change'] = {
                    'from': record.customer_priority,
                    'to': vals['customer_priority']
                }

        # Update last modified information
        vals['last_updated_by_id'] = self.env.user.id
        vals['last_update_date'] = fields.Datetime.now()

        # Perform the write
        result = super().write(vals)

        # Post-write activities
        for record in self:
            # Create audit log for significant changes
            if changes_to_log:
                record._create_audit_log('updated', 'Item updated', changes_to_log)

            # Update work order progress metrics
            if status_changed and record.work_order_id:
                if hasattr(record.work_order_id, '_update_progress_metrics'):
                    record.work_order_id._update_progress_metrics()

            # Send notifications for status changes
            if status_changed:
                record._send_status_change_notification(
                    changes_to_log.get('status_change', {}).get('from'),
                    changes_to_log.get('status_change', {}).get('to')
                )

            # Send notifications for assignment changes
            if assignment_changed:
                record._send_assignment_notification()

                # Notify previous assignee of change
                previous_assignee_name = changes_to_log.get('assignment_change', {}).get('from')
                if previous_assignee_name:
                    record._send_reassignment_notification(previous_assignee_name)

        return result

    def unlink(self):
        """Enhanced unlink with business rule protection"""
        for record in self:
            # Prevent deletion if item is in progress
            protected_statuses = ['retrieving', 'retrieved', 'quality_checking', 'quality_checked',
                                'packaging', 'packaged']

            if record.status in protected_statuses:
                raise ValidationError(
                    _("Cannot delete item '%s' with status '%s'. Please cancel or complete the item first.") %
                    (record.name, record.status)
                )

            # Prevent deletion if part of delivered work order
            if record.status == 'delivered':
                raise ValidationError(
                    _("Cannot delete delivered item '%s'. Items must be archived instead of deleted.") %
                    record.name
                )

            # Prevent deletion if high-value item without special permissions
            if record.high_value_item and not self.env.user.has_group('records_management.group_records_manager'):
                raise ValidationError(
                    _("Only Records Managers can delete high-value items. Please contact an administrator.")
                )

            # Create audit log before deletion
            record._create_audit_log('deleted', 'Item deleted', {
                'reference': record.name,
                'status_at_deletion': record.status,
                'work_order': record.work_order_id.name if record.work_order_id else None,
                'deleted_by': self.env.user.name
            })

        # Update work order metrics after deletion
        work_orders_to_update = self.mapped('work_order_id')

        result = super().unlink()

        # Update work order progress after item deletion
        for work_order in work_orders_to_update:
            if hasattr(work_order, '_update_progress_metrics'):
                work_order._update_progress_metrics()

        return result

    def copy(self, default=None):
        """Enhanced copy with proper field handling"""
        if default is None:
            default = {}

        # Reset status and dates for copied items
        copy_defaults = {
            'status': 'pending',
            'date_assigned': None,
            'date_located': None,
            'date_retrieved': None,
            'date_quality_checked': None,
            'date_packaged': None,
            'date_delivered': None,
            'quality_approved': None,
            'chain_of_custody_verified': False,
            'access_logged': False,
            'actual_pages': None,
            'actual_cost': None,
            # Reset computed scores
            'quality_score': 0,
            'efficiency_score': 0,
            'overall_performance_score': 0,
            # Clear completion tracking
            'location_duration_hours': 0,
            'retrieval_duration_hours': 0,
            'total_processing_hours': 0,
        }

        # Add copy suffix to name
        if 'name' not in default:
            copy_defaults['name'] = _("%s (Copy)") % self.name

        # Merge with provided defaults
        copy_defaults.update(default)

        # Create the copy
        copied_record = super().copy(copy_defaults)

        # Create audit log for copy
        copied_record._create_audit_log('copied', 'Item copied', {
            'original_reference': self.name,
            'new_reference': copied_record.name,
            'copied_by': self.env.user.name
        })

        return copied_record

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        """Enhanced search with optimized queries"""
        # Add default ordering if not specified
        if not order:
            order = 'customer_priority desc, date_assigned desc, name'

        # Optimize query for common filters
        if args:
            optimized_args = []
            for arg in args:
                if isinstance(arg, (list, tuple)) and len(arg) == 3:
                    field, operator, value = arg

                    # Optimize status searches
                    if field == 'status' and operator == 'in' and isinstance(value, list):
                        # Use more efficient query for multiple status values
                        optimized_args.append(arg)
                    else:
                        optimized_args.append(arg)
                else:
                    optimized_args.append(arg)
            args = optimized_args

        return super().search(args, offset=offset, limit=limit, order=order, count=count)

    # ============================================================================
    # HELPER METHODS FOR ORM OPERATIONS
    # ============================================================================
    def _create_audit_log(self, action, description, details=None):
        """Create audit log entry for significant actions"""
        try:
            if self.env.get('naid.audit.log'):
                self.env['naid.audit.log'].create({
                    'reference_model': self._name,
                    'reference_id': self.id,
                    'action_type': action,
                    'description': description,
                    'user_id': self.env.user.id,
                    'timestamp': fields.Datetime.now(),
                    'details': str(details) if details else '',
                    'ip_address': self._get_user_ip(),
                })
        except Exception as e:
            # Don't fail operations if audit logging fails
            _logger.warning("Failed to create audit log: %s", str(e))

    def _get_user_ip(self):
        """Get current user's IP address"""
        try:
            request = self.env.context.get('request')
            if request:
                return request.httprequest.environ.get('REMOTE_ADDR', 'Unknown')
        except:
            pass
        return 'System'

    def _send_assignment_notification(self):
        """Send notification to assigned team member"""
        if not self.assigned_to_id:
            return

        try:
            template_id = self.env.ref('records_management.email_template_item_assignment', False)
            if template_id:
                template_id.send_mail(self.id, force_send=False)
        except Exception as e:
            _logger.warning("Failed to send assignment notification: %s", str(e))

    def _send_status_change_notification(self, old_status, new_status):
        """Send notification for status changes"""
        if not old_status or not new_status:
            return

        # Notify stakeholders for significant status changes
        notification_statuses = ['located', 'retrieved', 'quality_checked', 'delivered', 'not_found']

        if new_status in notification_statuses:
            try:
                template_id = self.env.ref('records_management.email_template_status_change', False)
                if template_id:
                    template_id.send_mail(self.id, force_send=False)
            except Exception as e:
                _logger.warning("Failed to send status change notification: %s", str(e))

    def _send_reassignment_notification(self, previous_assignee_name):
        """Send notification to previous assignee about reassignment"""
        try:
            # Send notification to inform about reassignment
            message = _("Item %s has been reassigned to %s") % (
                self.name,
                self.assigned_to_id.name if self.assigned_to_id else _("Unassigned")
            )

            self.message_post(
                body=message,
                subject=_("Item Reassignment Notification"),
                message_type='notification'
            )
        except Exception as e:
            _logger.warning("Failed to send reassignment notification: %s", str(e))

    # ============================================================================
    # NAME/SEARCH METHODS
    # ============================================================================
    def name_get(self):
        result = []
        for record in self:
            name = record.display_name or record.name
            result.append((record.id, name))
        return result

    @api.model
    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
        args = args or []
        domain = []
        if name:
            domain = [
                "|", "|",
                ("name", operator, name),
                ("file_name", operator, name),
                ("description", operator, name),
            ]
        return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_item_details(self):
        """Get detailed information about the item"""
        self.ensure_one()
        return {
            'reference': self.name,
            'file_name': self.file_name,
            'description': self.description,
            'type': self.file_type,
            'format': self.file_format,
            'status': self.status,
            'condition': self.condition,
            'estimated_pages': self.estimated_pages,
            'actual_pages': self.actual_pages,
            'container': self.container_id.name if self.container_id else None,
            'location': self.container_location,
            'position': self.file_position,
            'quality_approved': self.quality_approved,
            'quality_notes': self.quality_notes,
        }

    def get_retrieval_summary(self):
        """Get retrieval summary for this item"""
        self.ensure_one()
        return {
            'item_reference': self.name,
            'file_name': self.file_name or '',
            'file_type': self.file_type,
            'file_format': self.file_format,
            'status': self.status,
            'condition': self.condition or '',
            'estimated_pages': self.estimated_pages,
            'actual_pages': self.actual_pages or 0,
            'container': self.container_id.name if self.container_id else '',
            'quality_approved': self.quality_approved,
            'location_notes': self.location_notes or '',
        }

    # ============================================================================
    # REPORTING METHODS
    # ============================================================================
    def generate_retrieval_report(self, work_order_ids=None, date_from=None, date_to=None):
        """Generate retrieval report for items"""
        domain = []

        if work_order_ids:
            domain.append(('work_order_id', 'in', work_order_ids))
        if date_from:
            domain.append(('create_date', '>=', date_from))
        if date_to:
            domain.append(('create_date', '<=', date_to))

        items = self.search(domain)

        # Compile statistics
        total_items = len(items)
        by_status = {}
        by_type = {}
        total_pages = 0

        for item in items:
            # By status
            if item.status not in by_status:
                by_status[item.status] = 0
            by_status[item.status] += 1

            # By type
            if item.file_type not in by_type:
                by_type[item.file_type] = 0
            by_type[item.file_type] += 1

            # Total pages
            if item.actual_pages:
                total_pages += item.actual_pages
            elif item.estimated_pages:
                total_pages += item.estimated_pages

        return {
            'total_items': total_items,
            'by_status': by_status,
            'by_type': by_type,
            'total_pages': total_pages,
            'items': [item.get_retrieval_summary() for item in items],
            'quality_approval_rate': len(items.filtered('quality_approved')) / total_items * 100 if total_items > 0 else 0,
        }

    # ============================================================================
    # BUSINESS LOGIC HELPER METHODS
    # ============================================================================

    # Performance Optimization Methods
    def optimize_retrieval_path(self):
        """Optimize retrieval path based on location and container data"""
        self.ensure_one()

        optimization_data = {
            'item_id': self.id,
            'container_id': self.container_id.id if self.container_id else None,
            'location': self.container_location,
            'access_difficulty': self.access_difficulty,
            'estimated_duration': 0,
            'suggested_tools': [],
            'prerequisites': [],
            'optimal_time_slot': None
        }

        # Calculate estimated duration based on complexity
        base_duration = 0.5  # 30 minutes base

        # Adjust for access difficulty
        difficulty_multipliers = {
            'easy': 1.0,
            'moderate': 1.5,
            'difficult': 2.0,
            'restricted': 3.0
        }

        difficulty_multiplier = difficulty_multipliers.get(self.access_difficulty, 1.0)
        optimization_data['estimated_duration'] = base_duration * difficulty_multiplier

        # Suggest tools based on file type and condition
        if self.file_type in ['blueprint', 'photograph']:
            optimization_data['suggested_tools'].append('Protective sleeves')

        if self.condition in ['fragile', 'deteriorated']:
            optimization_data['suggested_tools'].extend(['Gloves', 'Support boards'])

        if self.file_format == 'microfilm':
            optimization_data['suggested_tools'].append('Microfilm reader')

        # Prerequisites based on security level
        if self.confidentiality_level in ['confidential', 'highly_confidential']:
            optimization_data['prerequisites'].append('Security clearance verification')

        if self.high_value_item:
            optimization_data['prerequisites'].append('Manager approval')

        # Suggest optimal time slot
        if self.rush_item:
            optimization_data['optimal_time_slot'] = 'Immediate'
        elif self.access_difficulty == 'restricted':
            optimization_data['optimal_time_slot'] = 'During restricted access hours'
        else:
            optimization_data['optimal_time_slot'] = 'Standard business hours'

        return optimization_data

    def calculate_efficiency_metrics(self):
        """Calculate detailed efficiency metrics for this item"""
        self.ensure_one()

        metrics = {
            'overall_efficiency': self.efficiency_score or 0,
            'location_efficiency': 0,
            'retrieval_efficiency': 0,
            'quality_efficiency': 0,
            'time_utilization': 0,
            'cost_efficiency': 0,
            'recommendations': []
        }

        # Location efficiency
        if self.location_duration_hours:
            standard_location_time = 0.5
            if self.location_duration_hours <= standard_location_time:
                metrics['location_efficiency'] = 100
            else:
                metrics['location_efficiency'] = min(100, (standard_location_time / self.location_duration_hours) * 100)

        # Retrieval efficiency
        if self.retrieval_duration_hours:
            standard_retrieval_time = 0.3
            if self.retrieval_duration_hours <= standard_retrieval_time:
                metrics['retrieval_efficiency'] = 100
            else:
                metrics['retrieval_efficiency'] = min(100, (standard_retrieval_time / self.retrieval_duration_hours) * 100)

        # Quality efficiency (based on accuracy and score)
        if self.quality_score:
            metrics['quality_efficiency'] = self.quality_score

        # Time utilization
        if self.total_processing_hours:
            expected_total_time = 2.0  # 2 hours expected total
            if self.total_processing_hours <= expected_total_time:
                metrics['time_utilization'] = 100
            else:
                metrics['time_utilization'] = min(100, (expected_total_time / self.total_processing_hours) * 100)

        # Cost efficiency
        if self.estimated_cost and self.actual_cost:
            if self.actual_cost <= self.estimated_cost:
                metrics['cost_efficiency'] = 100
            else:
                metrics['cost_efficiency'] = max(0, (self.estimated_cost / self.actual_cost) * 100)

        # Generate recommendations
        if metrics['location_efficiency'] < 80:
            metrics['recommendations'].append('Review location procedures for efficiency')

        if metrics['retrieval_efficiency'] < 80:
            metrics['recommendations'].append('Consider additional training for retrieval team')

        if metrics['quality_efficiency'] < 90:
            metrics['recommendations'].append('Implement additional quality control measures')

        return metrics

    def get_performance_benchmarks(self):
        """Get performance benchmarks for similar items"""
        self.ensure_one()

        # Find similar items for benchmarking
        similar_items = self.search([
            ('file_type', '=', self.file_type),
            ('access_difficulty', '=', self.access_difficulty),
            ('status', 'in', ['delivered', 'packaged']),
            ('id', '!=', self.id)
        ], limit=50)

        if not similar_items:
            return None

        # Calculate benchmarks
        benchmarks = {
            'avg_location_time': sum(item.location_duration_hours for item in similar_items if item.location_duration_hours) / len(similar_items.filtered('location_duration_hours')) if similar_items.filtered('location_duration_hours') else 0,
            'avg_retrieval_time': sum(item.retrieval_duration_hours for item in similar_items if item.retrieval_duration_hours) / len(similar_items.filtered('retrieval_duration_hours')) if similar_items.filtered('retrieval_duration_hours') else 0,
            'avg_total_time': sum(item.total_processing_hours for item in similar_items if item.total_processing_hours) / len(similar_items.filtered('total_processing_hours')) if similar_items.filtered('total_processing_hours') else 0,
            'avg_quality_score': sum(item.quality_score for item in similar_items if item.quality_score) / len(similar_items.filtered('quality_score')) if similar_items.filtered('quality_score') else 0,
            'quality_approval_rate': len(similar_items.filtered('quality_approved')) / len(similar_items) * 100 if similar_items else 0,
            'sample_size': len(similar_items)
        }

        return benchmarks

    # Analytics Generation Methods
    def generate_performance_report_data(self):
        """Generate comprehensive performance report data"""
        self.ensure_one()

        report_data = {
            'item_info': {
                'reference': self.name,
                'file_name': self.file_name,
                'work_order': self.work_order_id.name if self.work_order_id else None,
                'customer': self.work_order_id.customer_id.name if self.work_order_id and self.work_order_id.customer_id else None,
                'created_date': self.create_date,
                'completed_date': self.date_delivered or self.date_packaged,
            },
            'performance_metrics': {
                'overall_score': self.overall_performance_score,
                'quality_score': self.quality_score,
                'efficiency_score': self.efficiency_score,
                'business_impact_score': self.business_impact_score,
                'completeness_score': self.completeness_score,
            },
            'time_analysis': {
                'location_duration': self.location_duration_hours,
                'retrieval_duration': self.retrieval_duration_hours,
                'total_processing_time': self.total_processing_hours,
                'status_timeline': self._get_status_timeline(),
            },
            'quality_analysis': {
                'condition': self.condition,
                'quality_approved': self.quality_approved,
                'page_accuracy': self.page_accuracy_percentage,
                'quality_issues': self.quality_issues,
            },
            'cost_analysis': {
                'estimated_cost': self.estimated_cost,
                'actual_cost': self.actual_cost,
                'cost_variance': self.cost_variance,
                'cost_per_page': self.cost_per_page,
            },
            'recommendations': self._generate_improvement_recommendations(),
        }

        return report_data

    def _get_status_timeline(self):
        """Get detailed status progression timeline"""
        timeline = []

        status_dates = [
            ('assigned', self.date_assigned),
            ('located', self.date_located),
            ('retrieved', self.date_retrieved),
            ('quality_checked', self.date_quality_checked),
            ('packaged', self.date_packaged),
            ('delivered', self.date_delivered),
        ]

        for status, date in status_dates:
            if date:
                timeline.append({
                    'status': status,
                    'date': date,
                    'display_name': dict(self._fields['status'].selection).get(status, status)
                })

        return timeline

    def _generate_improvement_recommendations(self):
        """Generate improvement recommendations based on performance"""
        recommendations = []

        # Performance-based recommendations
        if self.efficiency_score < 70:
            recommendations.append({
                'type': 'efficiency',
                'priority': 'high',
                'recommendation': 'Review and optimize retrieval procedures'
            })

        if self.quality_score < 80:
            recommendations.append({
                'type': 'quality',
                'priority': 'medium',
                'recommendation': 'Implement additional quality control measures'
            })

        # Time-based recommendations
        if self.location_duration_hours and self.location_duration_hours > 1:
            recommendations.append({
                'type': 'location',
                'priority': 'medium',
                'recommendation': 'Improve location tracking and organization'
            })

        # Cost-based recommendations
        if self.cost_variance and abs(self.cost_variance) > 50:
            recommendations.append({
                'type': 'cost',
                'priority': 'high',
                'recommendation': 'Review cost estimation procedures'
            })

        return recommendations

    def get_analytics_data(self):
        """Get analytics data for dashboard display"""
        self.ensure_one()

        return {
            'item_id': self.id,
            'reference': self.name,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'quality_metrics': {
                'score': self.quality_score,
                'approved': self.quality_approved,
                'completeness': self.completeness_score,
            },
            'performance_metrics': {
                'efficiency': self.efficiency_score,
                'overall': self.overall_performance_score,
                'business_impact': self.business_impact_score,
            },
            'time_metrics': {
                'location_hours': self.location_duration_hours,
                'retrieval_hours': self.retrieval_duration_hours,
                'total_hours': self.total_processing_hours,
            },
            'urgency_indicators': {
                'is_overdue': self.is_overdue,
                'urgency_level': self.urgency_level,
                'days_until_deadline': self.days_until_deadline,
                'rush_item': self.rush_item,
            },
            'team_info': {
                'assigned_to': self.assigned_to_id.name if self.assigned_to_id else None,
                'team_lead': self.team_lead_id.name if self.team_lead_id else None,
                'reviewer': self.reviewer_id.name if self.reviewer_id else None,
            }
        }

    # API Integration Helper Methods
    def prepare_api_data(self, include_sensitive=False):
        """Prepare data for external API consumption"""
        self.ensure_one()

        api_data = {
            'id': self.id,
            'reference': self.name,
            'file_name': self.file_name,
            'file_type': self.file_type,
            'status': self.status,
            'progress_percentage': self.progress_percentage,
            'estimated_pages': self.estimated_pages,
            'actual_pages': self.actual_pages,
            'quality_approved': self.quality_approved,
            'date_created': self.create_date.isoformat() if self.create_date else None,
            'date_assigned': self.date_assigned.isoformat() if self.date_assigned else None,
            'date_completed': (self.date_delivered or self.date_packaged).isoformat() if (self.date_delivered or self.date_packaged) else None,
        }

        # Include sensitive data only if authorized
        if include_sensitive:
            api_data.update({
                'customer_priority': self.customer_priority,
                'confidentiality_level': self.confidentiality_level,
                'container_location': self.container_location,
                'quality_score': self.quality_score,
                'efficiency_score': self.efficiency_score,
                'cost_data': {
                    'estimated_cost': self.estimated_cost,
                    'actual_cost': self.actual_cost,
                    'cost_variance': self.cost_variance,
                }
            })

        return api_data

    def sync_with_external_system(self, system_name, data_mapping=None):
        """Sync item data with external system"""
        self.ensure_one()

        try:
            sync_data = {
                'item_reference': self.name,
                'status': self.status,
                'last_updated': fields.Datetime.now().isoformat(),
                'sync_timestamp': fields.Datetime.now().isoformat(),
            }

            # Apply custom data mapping if provided
            if data_mapping:
                for local_field, external_field in data_mapping.items():
                    if hasattr(self, local_field):
                        sync_data[external_field] = getattr(self, local_field)

            # Log sync attempt
            self._create_audit_log('external_sync', f'Synced with {system_name}', {
                'system': system_name,
                'data_sent': sync_data,
                'sync_time': fields.Datetime.now().isoformat()
            })

            return {
                'success': True,
                'system': system_name,
                'data': sync_data,
                'timestamp': fields.Datetime.now()
            }

        except Exception as e:
            _logger.error(f"Failed to sync with {system_name}: {str(e)}")
            return {
                'success': False,
                'system': system_name,
                'error': str(e),
                'timestamp': fields.Datetime.now()
            }

    # Utility and Validation Methods
    def validate_business_rules(self):
        """Validate all business rules for the item"""
        self.ensure_one()

        validation_results = {
            'valid': True,
            'warnings': [],
            'errors': [],
            'checks_performed': []
        }

        # Status progression validation
        try:
            self._check_status_date_consistency()
            validation_results['checks_performed'].append('Status progression')
        except ValidationError as e:
            validation_results['valid'] = False
            validation_results['errors'].append(str(e))

        # Quality requirements validation
        try:
            self._check_quality_requirements()
            validation_results['checks_performed'].append('Quality requirements')
        except ValidationError as e:
            validation_results['valid'] = False
            validation_results['errors'].append(str(e))

        # Team assignment validation
        try:
            self._check_team_assignment_rules()
            validation_results['checks_performed'].append('Team assignments')
        except ValidationError as e:
            validation_results['valid'] = False
            validation_results['errors'].append(str(e))

        # Security requirements validation
        try:
            self._check_security_requirements()
            validation_results['checks_performed'].append('Security requirements')
        except ValidationError as e:
            validation_results['warnings'].append(str(e))

        # Performance threshold checks
        if self.efficiency_score < 50:
            validation_results['warnings'].append('Efficiency score below threshold')

        if self.quality_score < 60:
            validation_results['warnings'].append('Quality score below acceptable level')

        return validation_results

    @api.model
    def cleanup_orphaned_data(self):
        """Clean up orphaned or inconsistent item data"""
        cleanup_results = {
            'items_processed': 0,
            'items_fixed': 0,
            'issues_found': [],
            'actions_taken': []
        }

        # Find items with missing work orders
        orphaned_items = self.search([('work_order_id', '=', False)])

        for item in orphaned_items:
            cleanup_results['items_processed'] += 1
            cleanup_results['issues_found'].append(f'Item {item.name} has no work order')

            # Archive orphaned items
            if item.status not in ['delivered', 'cancelled']:
                item.write({
                    'status': 'cancelled',
                    'notes': 'Cancelled due to missing work order during cleanup'
                })
                cleanup_results['items_fixed'] += 1
                cleanup_results['actions_taken'].append(f'Cancelled orphaned item {item.name}')

        # Find items with inconsistent dates
        inconsistent_dates = self.search([
            ('date_located', '!=', False),
            ('date_assigned', '=', False)
        ])

        for item in inconsistent_dates:
            cleanup_results['items_processed'] += 1
            cleanup_results['issues_found'].append(f'Item {item.name} has inconsistent dates')

            # Fix missing assigned date
            item.write({'date_assigned': item.date_located})
            cleanup_results['items_fixed'] += 1
            cleanup_results['actions_taken'].append(f'Fixed assigned date for {item.name}')

        _logger.info(f"Cleanup completed: {cleanup_results}")
        return cleanup_results

    def get_item_dependencies(self):
        """Get all dependencies and related records for this item"""
        self.ensure_one()

        dependencies = {
            'work_order': self.work_order_id.id if self.work_order_id else None,
            'container': self.container_id.id if self.container_id else None,
            'assigned_user': self.assigned_to_id.id if self.assigned_to_id else None,
            'team_lead': self.team_lead_id.id if self.team_lead_id else None,
            'reviewer': self.reviewer_id.id if self.reviewer_id else None,
            'audit_logs': self.env['naid.audit.log'].search_count([
                ('reference_model', '=', self._name),
                ('reference_id', '=', self.id)
            ]) if self.env.get('naid.audit.log') else 0,
            'related_items': self.search_count([
                ('work_order_id', '=', self.work_order_id.id),
                ('id', '!=', self.id)
            ]) if self.work_order_id else 0,
        }

        return dependencies

