# DEPRECATED: This model will be replaced by specialized retrieval models
# Keep for migration purposes only

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class DocumentRetrievalItem(models.Model):
    _name = 'document.retrieval.item'
    _description = 'Document Retrieval Item (DEPRECATED)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Item Reference', required=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    user_id = fields.Many2one('res.users', string='Assigned User', default=lambda self: self.env.user)
    active = fields.Boolean(string='Active', default=True)
    work_order_id = fields.Many2one('records.retrieval.work.order', string='Work Order')
    sequence = fields.Integer(string='Sequence', default=10)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1')
    document_id = fields.Many2one('records.document', string='Document')
    container_id = fields.Many2one('records.container', string='Container')
    location_id = fields.Many2one('records.location', string='Location')
    item_type = fields.Selection([
        ('document', 'Document'),
        ('container', 'Container'),
        ('box', 'Box'),
        ('file', 'File')
    ], string='Item Type', default='document')
    description = fields.Text(string='Item Description')
    barcode = fields.Char(string='Barcode/ID')
    status = fields.Selection([
        ('pending', 'Pending'),
        ('searching', 'Searching'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('packaged', 'Packaged'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned'),
        ('not_found', 'Not Found')
    ], string='Status', default='pending', tracking=True)
    current_location = fields.Char(string='Current Location')
    storage_location_id = fields.Many2one('records.location', string='Storage Location')
    searched_container_ids = fields.Many2many('records.container', 'document_retrieval_searched_container_rel', 'retrieval_item_id', 'container_id', string='Searched Containers')
    containers_accessed_count = fields.Integer(string='Containers Accessed', compute='_compute_containers_accessed_count')
    containers_not_found_count = fields.Integer(string='Containers Not Found', compute='_compute_containers_not_found_count')
    requested_file_name = fields.Char(string='Requested File Name')
    estimated_time = fields.Float(string='Estimated Time (hours)')
    actual_time = fields.Float(string='Actual Time (hours)')
    difficulty_level = fields.Selection([
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('very_hard', 'Very Hard')
    ], string='Difficulty Level', default='medium')
    retrieval_date = fields.Datetime(string='Retrieved Date')
    retrieved_by_id = fields.Many2one('res.users', string='Retrieved By')
    condition_notes = fields.Text(string='Condition Notes')
    special_handling = fields.Boolean(string='Special Handling Required')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_issues = fields.Text(string='Quality Issues')
    completeness_verified = fields.Boolean(string='Completeness Verified')
    search_attempt_ids = fields.One2many('document.search.attempt', 'retrieval_item_id', string='Search Attempts')
    total_search_attempts = fields.Integer(string='Total Search Attempts', compute='_compute_total_search_attempts')
    not_found_reason = fields.Selection([
        ('not_in_container', 'Not in Container'),
        ('container_missing', 'Container Missing'),
        ('destroyed', 'Already Destroyed'),
        ('misfiled', 'Misfiled'),
        ('other', 'Other Reason')
    ], string='Not Found Reason')
    not_found_notes = fields.Text(string='Not Found Notes')
    file_discovered = fields.Boolean(string='File Discovered')
    discovery_date = fields.Datetime(string='Discovery Date')
    discovery_container_id = fields.Many2one('records.container', string='Discovery Container')
    retrieval_notes = fields.Text(string='Retrieval Notes')
    partner_id = fields.Many2one('res.partner', string='Customer')
    handling_instructions = fields.Text(string='Handling Instructions')
    fragile = fields.Boolean(string='Fragile Item')
    estimated_weight = fields.Float(string='Estimated Weight (kg)')
    actual_weight = fields.Float(string='Actual Weight (kg)')
    dimensions = fields.Char(string='Dimensions (LxWxH)')
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal')
    access_authorized_by_id = fields.Many2one('res.users', string='Access Authorized By')
    authorization_date = fields.Datetime(string='Authorization Date')
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
    scan_required = fields.Boolean(string='Scan Required')
    scan_completed = fields.Boolean(string='Scan Completed')
    digital_format = fields.Selection([
        ('pdf', 'PDF'),
        ('tiff', 'TIFF'),
        ('jpg', 'JPEG'),
        ('png', 'PNG')
    ], string='Digital Format')
    scan_quality = fields.Selection([
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('archive', 'Archive Quality')
    ], string='Scan Quality')
    return_required = fields.Boolean(string='Return Required')
    return_date = fields.Date(string='Return Date')
    return_location_id = fields.Many2one('records.location', string='Return Location')
    return_notes = fields.Text(string='Return Notes')
    retrieval_cost = fields.Monetary(
        string="Retrieval Cost", compute="_compute_retrieval_cost", currency_field="currency_id"
    )
    container_access_cost = fields.Monetary(
        string="Container Access Cost", compute="_compute_container_access_cost", currency_field="currency_id"
    )
    total_cost = fields.Monetary(string="Total Cost", compute="_compute_total_cost", currency_field="currency_id")
    currency_id = fields.Many2one('res.currency', string='Currency', compute='_compute_currency_id')
    tracking_number = fields.Char(string='Tracking Number')
    audit_trail = fields.Text(string='Audit Trail')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name')
    location_display = fields.Char(string='Location Display', compute='_compute_location_display')
    state = fields.Selection(related='status', string='State')
    effective_priority = fields.Selection(related='priority', string='Effective Priority')

    # Class-level constant for maintainability
    DEFAULT_ACTIVE_STATUSES = ["pending", "searching", "located"]

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('work_order_id.currency_id', 'company_id.currency_id')
    def _compute_currency_id(self):
        for item in self:
            if item.work_order_id and item.work_order_id.currency_id:
                item.currency_id = item.work_order_id.currency_id
            else:
                item.currency_id = item.company_id.currency_id or self.env.company.currency_id

    @api.depends('searched_container_ids')
    def _compute_containers_accessed_count(self):
        for item in self:
            item.containers_accessed_count = len(item.searched_container_ids)

    @api.depends('search_attempt_ids.found')
    def _compute_containers_not_found_count(self):
        for item in self:
            unsuccessful_searches = item.search_attempt_ids.filtered(lambda x: not x.found)
            item.containers_not_found_count = len(unsuccessful_searches)

    @api.depends('search_attempt_ids')
    def _compute_total_search_attempts(self):
        for item in self:
            item.total_search_attempts = len(item.search_attempt_ids)

    @api.depends('partner_id')
    def _compute_retrieval_cost(self):
        for item in self:
            retrieval_rate = 0.0
            if item.partner_id:
                negotiated_rate = self.env["customer.negotiated.rate"].search(
                    [
                        ("partner_id", "=", item.partner_id.id),
                        ("active", "=", True),
                    ],
                    limit=1,
                )

                if negotiated_rate:
                    retrieval_rate = negotiated_rate.get_effective_rate("managed_retrieval_rate")

            if not retrieval_rate:
                base_rate = self.env["base.rate"].search([
                    ("service_type", "=", "retrieval"),
                    ("state", "=", "confirmed"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)

                if base_rate:
                    retrieval_rate = base_rate.managed_retrieval_rate or 3.50

            item.retrieval_cost = retrieval_rate or 3.50

    @api.depends('containers_not_found_count', 'partner_id')
    def _compute_container_access_cost(self):
        for item in self:
            if not item.containers_not_found_count:
                item.container_access_cost = 0.0
                continue

            access_rate = 0.0
            if item.partner_id:
                negotiated_rate = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", item.partner_id.id),
                    ("rate_type", "=", "container_access"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)

                if negotiated_rate:
                    access_rate = negotiated_rate.get_effective_rate("container_access_rate")

            if not access_rate:
                base_rate = self.env["base.rate"].search([
                    ("service_type", "=", "container_access"),
                    ("state", "=", "confirmed"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)

                if base_rate:
                    access_rate = base_rate.external_per_bin_rate or 3.50

            access_rate = access_rate or 3.50
            item.container_access_cost = item.containers_not_found_count * access_rate

    @api.depends('retrieval_cost', 'container_access_cost', 'work_order_id.delivery_method', 'status', 'partner_id')
    def _compute_total_cost(self):
        for item in self:
            total = item.retrieval_cost + item.container_access_cost
            partner = item.partner_id

            if item.work_order_id and item.work_order_id.delivery_method == 'physical' and partner:
                delivery_fee = 0.0
                negotiated_delivery = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", partner.id),
                    ("rate_type", "=", "delivery"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                    "|",
                    ("expiry_date", "=", False),
                    ("expiry_date", ">=", fields.Date.today()),
                ], limit=1)

                if negotiated_delivery:
                    delivery_fee = negotiated_delivery.get_effective_rate("pickup_rate")
                else:
                    base_delivery = self.env["base.rate"].search([
                        ("service_type", "=", "delivery"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),
                    ], limit=1)

                    if base_delivery:
                        delivery_fee = base_delivery.pickup_rate
                total += delivery_fee or 25.0

            if item.status == "not_found" and partner:
                not_found_fee = 0.0
                negotiated_not_found = self.env["customer.negotiated.rates"].search([
                    ("partner_id", "=", partner.id),
                    ("rate_type", "=", "not_found_search"),
                    ("state", "=", "active"),
                    ("active", "=", True),
                ], limit=1)

                if negotiated_not_found:
                    not_found_fee = negotiated_not_found.get_effective_rate("managed_retrieval_rate")
                else:
                    base_not_found = self.env["base.rate"].search([
                        ("service_type", "=", "not_found_search"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                    ], limit=1)

                    if base_not_found:
                        not_found_fee = base_not_found.managed_retrieval_rate
                total += not_found_fee or 3.50

            item.total_cost = total

    @api.depends('name', 'item_type', 'barcode')
    def _compute_display_name(self):
        for item in self:
            parts = [item.name or "New Item"]
            if item.item_type:
                type_display = dict(item._fields["item_type"].selection).get(item.item_type, item.item_type)
                parts.append("(%s)" % type_display)
            if item.barcode:
                parts.append("[%s]" % item.barcode)
            item.display_name = " ".join(parts)

    @api.depends('storage_location_id', 'current_location')
    def _compute_location_display(self):
        for item in self:
            if item.storage_location_id:
                item.location_display = item.storage_location_id.name
            elif item.current_location:
                item.location_display = item.current_location
            else:
                item.location_display = _("Location Unknown")

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        if self.container_id:
            self.current_location = self.container_id.current_location
            self.storage_location_id = self.container_id.location_id

    @api.onchange('document_id')
    def _onchange_document_id(self):
        if self.document_id:
            if self.document_id.container_id:
                self.container_id = self.document_id.container_id
            if self.item_type == "document" and not self.name and self.document_id.name:
                self.name = self.document_id.name

    @api.onchange('item_type')
    def _onchange_item_type(self):
        if self.item_type in ("container", "box"):
            self.document_id = False

    @api.onchange('priority')
    def _onchange_priority(self):
        """Update sequence based on priority for ordering"""
        if self.priority:
            priority_sequence_map = {
                '0': 100,  # Low priority - higher sequence number
                '1': 50,   # Normal priority
                '2': 20,   # High priority - lower sequence number
                '3': 10,   # Very High priority - lowest sequence number
            }
            self.sequence = priority_sequence_map.get(self.priority, 50)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def _update_status(self, new_status, message_body, extra_vals=None):
        self.ensure_one()
        vals = {"status": new_status}
        if extra_vals:
            vals.update(extra_vals)
        self.write(vals)
        self.message_post(body=message_body, message_type="notification")

    def action_locate_item(self):
        self.ensure_one()
        for item in self:
            if item.status != "pending":
                raise UserError(_("Only pending items can be located."))
            item._update_status(
                "located",
                _("Item located by %s", self.env.user.name),
                {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}
            )

    def action_retrieve_item(self):
        self.ensure_one()
        for item in self:
            if item.status != "located":
                raise UserError(_("Item must be located before retrieval."))
            item._update_status(
                "retrieved",
                _("Item retrieved by %s", self.env.user.name),
                {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}
            )

    def action_package_item(self):
        self.ensure_one()
        for item in self:
            if item.status != "retrieved":
                raise UserError(_("Item must be retrieved before packaging."))
            item._update_status("packaged", _("Item packaged by %s", self.env.user.name))

    def action_deliver_item(self):
        self.ensure_one()
        for item in self:
            if item.status != "packaged":
                raise UserError(_("Item must be packaged before delivery."))
            item._update_status("delivered", _("Item delivered by %s", self.env.user.name))
            if item.status != "delivered":
                raise UserError(_("Item must be delivered before return."))
            item._update_status(
                "returned",
                _("Item returned by %s", self.env.user.name),
                {"return_date": fields.Date.today()}
            )

    # ============================================================================
    # SEARCH WORKFLOW ACTION METHODS
    # ============================================================================
    def action_begin_search_process(self):
        self.ensure_one()
        for item in self:
            if item.status != "pending":
                raise UserError(_("Only pending items can start the search process."))
            item._update_status(
                "searching",
                _("Search started by %s for file: %s", self.env.user.name, item.requested_file_name or item.name)
            )

    def action_record_container_search(self, container_id, found=False, notes=""):
        self.ensure_one()
        if container_id not in self.searched_container_ids.ids:
            self.searched_container_ids = [(4, container_id)]

        self.env["document.search.attempt"].create({
            "retrieval_item_id": self.id,
            "container_id": container_id,
            "searched_by_id": self.env.user.id,
            "search_date": fields.Datetime.now(),
            "found": found,
            "notes": notes,
        })

        if found:
            self.write({
                "status": "located",
                "file_discovered": True,
                "discovery_date": fields.Datetime.now(),
                "discovery_container_id": container_id,
                "container_id": container_id,
            })

        return True

    def action_mark_not_found(self, reason="not_in_container", notes=""):
        self.ensure_one()
        for item in self:
            reason_display = dict(item._fields["not_found_reason"].selection).get(reason, reason)
            message = _(
                "File marked as NOT FOUND by %s. Searched %s containers (%s unsuccessful). Reason: %s",
                self.env.user.name,
                item.containers_accessed_count,
                item.containers_not_found_count,
                reason_display
            )

            item._update_status(
                "not_found",
                message,
                {"not_found_reason": reason, "not_found_notes": notes or _("File not found after search.")}
            )

    def action_barcode_discovered_file(self, barcode, document_vals=None):
        self.ensure_one()
        if not self.file_discovered:
            raise UserError(_("File must be marked as discovered before barcoding."))

        self.write({"barcode": barcode, "status": "located"})

        if document_vals and self.discovery_container_id:
            document_vals.update({
                "name": self.requested_file_name or self.name,
                "barcode": barcode,
                "container_id": self.discovery_container_id.id,
                "partner_id": self.partner_id.id if self.partner_id else False,
            })

            document = self.env["records.document"].create(document_vals)
            self.document_id = document.id

        self.message_post(
            body=_("File barcoded by %s with barcode: %s", self.env.user.name, barcode),
            message_type="notification",
        )

        return True

    # ============================================================================
    # SEARCH AND QUERY METHODS
    # ============================================================================
    def search_items_by_status(self, status_list=None):
        """Search retrieval items by status"""
        if not status_list:
            status_list = self.DEFAULT_ACTIVE_STATUSES  # Use constant instead of hardcoded list

        domain = [('status', 'in', status_list)]
        return self.search(domain, order='priority desc, create_date desc')

    def search_items_by_partner(self, partner_id, limit=None):
        """Search retrieval items by partner"""
        domain = [('partner_id', '=', partner_id)]
        return self.search(domain, limit=limit, order='create_date desc')

    def search_related_containers(self):
        """Search for containers related to this item"""
        self.ensure_one()
        if self.partner_id:
            return self.env['records.container'].search([
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'active')
            ])

        return self.env['records.container']

    def search_items_by_priority(self, priority_level='2', limit=None):
        """Search retrieval items by priority level"""
        domain = [('priority', '>=', priority_level)]
        return self.search(domain, limit=limit, order='priority desc, create_date desc')

    def get_high_priority_items(self, partner_id=None):
        """
        Return a recordset of high and very high priority retrieval items (priority '2' or '3'),
        filtered by status ('pending', 'searching', or 'located'), and optionally filtered by partner.

        :param partner_id: Optional partner ID to filter items by customer.
        :return: recordset of document.retrieval.item records matching the criteria.
        """
        domain = [
            ("priority", "in", ["2", "3"]),
            ("status", "in", self.DEFAULT_ACTIVE_STATUSES),
        ]  # Use constant instead of hardcoded list
        if partner_id:
            domain.append(('partner_id', '=', partner_id))
        return self.search(domain, order='priority desc, create_date desc')
