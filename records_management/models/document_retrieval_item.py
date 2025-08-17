from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import UserError, ValidationError


class DocumentRetrievalItem(models.Model):
    _name = 'document.retrieval.item'
    _description = 'Document Retrieval Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string='Item Reference', required=True, tracking=True)
    company_id = fields.Many2one()
    user_id = fields.Many2one()
    active = fields.Boolean(string='Active')
    work_order_id = fields.Many2one()
    sequence = fields.Integer(string='Sequence')
    priority = fields.Selection()
    document_id = fields.Many2one('records.document')
    container_id = fields.Many2one('records.container')
    location_id = fields.Many2one('records.location')
    item_type = fields.Selection()
    description = fields.Text(string='Item Description')
    barcode = fields.Char(string='Barcode/ID')
    status = fields.Selection()
    current_location = fields.Char(string='Current Location')
    storage_location_id = fields.Many2one('records.location')
    searched_container_ids = fields.Many2many()
    containers_accessed_count = fields.Integer()
    containers_not_found_count = fields.Integer()
    requested_file_name = fields.Char(string='Requested File Name')
    estimated_time = fields.Float(string='Estimated Time (hours)')
    actual_time = fields.Float(string='Actual Time (hours)')
    difficulty_level = fields.Selection()
    retrieval_date = fields.Datetime(string='Retrieved Date')
    retrieved_by_id = fields.Many2one('res.users')
    condition_notes = fields.Text(string='Condition Notes')
    special_handling = fields.Boolean(string='Special Handling Required')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_issues = fields.Text(string='Quality Issues')
    completeness_verified = fields.Boolean(string='Completeness Verified')
    search_attempt_ids = fields.One2many()
    total_search_attempts = fields.Integer()
    not_found_reason = fields.Selection()
    not_found_notes = fields.Text()
    file_discovered = fields.Boolean()
    discovery_date = fields.Datetime()
    discovery_container_id = fields.Many2one()
    retrieval_notes = fields.Text(string='Retrieval Notes')
    partner_id = fields.Many2one()
    handling_instructions = fields.Text(string='Handling Instructions')
    fragile = fields.Boolean(string='Fragile Item')
    estimated_weight = fields.Float(string='Estimated Weight (kg)')
    actual_weight = fields.Float(string='Actual Weight (kg)')
    dimensions = fields.Char(string='Dimensions (LxWxH)')
    security_level = fields.Selection()
    access_authorized_by_id = fields.Many2one('res.users')
    authorization_date = fields.Datetime(string='Authorization Date')
    condition_before = fields.Selection()
    condition_after = fields.Selection()
    scan_required = fields.Boolean(string='Scan Required')
    scan_completed = fields.Boolean(string='Scan Completed')
    digital_format = fields.Selection()
    scan_quality = fields.Selection()
    return_required = fields.Boolean(string='Return Required')
    return_date = fields.Date(string='Return Date')
    return_location_id = fields.Many2one('records.location')
    return_notes = fields.Text(string='Return Notes')
    retrieval_cost = fields.Monetary()
    container_access_cost = fields.Monetary()
    total_cost = fields.Monetary()
    currency_id = fields.Many2one()
    tracking_number = fields.Char(string='Tracking Number')
    audit_trail = fields.Text(string='Audit Trail')
    display_name = fields.Char(string='Display Name')
    location_display = fields.Char(string='Location Display')
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    effective_priority = fields.Selection(string='Effective Priority')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_currency_id(self):
            for item in self:
                if item.work_order_id and item.work_order_id.currency_id:
                    item.currency_id = item.work_order_id.currency_id
                else:
                    item.currency_id = item.company_id.currency_id or self.env.company.currency_id


    def _compute_containers_accessed_count(self):
            for item in self:
                item.containers_accessed_count = len(item.searched_container_ids)


    def _compute_containers_not_found_count(self):
            for item in self:
                unsuccessful_searches = item.search_attempt_ids.filtered(lambda x: not x.found)
                item.containers_not_found_count = len(unsuccessful_searches)


    def _compute_total_search_attempts(self):
            for item in self:
                item.total_search_attempts = len(item.search_attempt_ids)


    def _compute_retrieval_cost(self):
            for item in self:
                retrieval_rate = 0.0
                if item.partner_id:
                    negotiated_rate = self.env["customer.negotiated.rates"].search([)]
                        ("partner_id", "=", item.partner_id.id),
                        ("active", "=", True),

                    if negotiated_rate:
                        retrieval_rate = negotiated_rate.get_effective_rate("managed_retrieval_rate")

                if not retrieval_rate:
                    base_rate = self.env["base.rate"].search([)]
                        ("service_type", "=", "retrieval"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),

                    if base_rate:
                        retrieval_rate = base_rate.managed_retrieval_rate or 3.50

                item.retrieval_cost = retrieval_rate or 3.50


    def _compute_container_access_cost(self):
            for item in self:
                if not item.containers_not_found_count:
                    item.container_access_cost = 0.0
                    continue

                access_rate = 0.0
                if item.partner_id:
                    negotiated_rate = self.env["customer.negotiated.rates"].search([)]
                        ("partner_id", "=", item.partner_id.id),
                        ("rate_type", "=", "container_access"),
                        ("state", "=", "active"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),

                    if negotiated_rate:
                        access_rate = negotiated_rate.get_effective_rate("container_access_rate")

                if not access_rate:
                    base_rate = self.env["base.rate"].search([)]
                        ("service_type", "=", "container_access"),
                        ("state", "=", "confirmed"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),

                    if base_rate:
                        access_rate = base_rate.external_per_bin_rate or 3.50

                access_rate = access_rate or 3.50
                item.container_access_cost = item.containers_not_found_count * access_rate


    def _compute_total_cost(self):
            for item in self:
                total = item.retrieval_cost + item.container_access_cost
                partner = item.partner_id

                if item.work_order_id and item.work_order_id.delivery_required and partner:
                    delivery_fee = 0.0
                    negotiated_delivery = self.env["customer.negotiated.rates"].search([)]
                        ("partner_id", "=", partner.id),
                        ("rate_type", "=", "delivery"),
                        ("state", "=", "active"),
                        ("active", "=", True),
                        "|",
                        ("expiry_date", "=", False),
                        ("expiry_date", ">=", fields.Date.today()),

                    if negotiated_delivery:
                        delivery_fee = negotiated_delivery.get_effective_rate("pickup_rate")
                    else:
                        base_delivery = self.env["base.rate"].search([)]
                            ("service_type", "=", "delivery"),
                            ("state", "=", "confirmed"),
                            ("active", "=", True),
                            "|",
                            ("expiry_date", "=", False),
                            ("expiry_date", ">=", fields.Date.today()),

                        if base_delivery:
                            delivery_fee = base_delivery.pickup_rate
                    total += delivery_fee or 25.0

                if item.status == "not_found" and partner:
                    not_found_fee = 0.0
                    negotiated_not_found = self.env["customer.negotiated.rates"].search([)]
                        ("partner_id", "=", partner.id),
                        ("rate_type", "=", "not_found_search"),
                        ("state", "=", "active"),
                        ("active", "=", True),

                    if negotiated_not_found:
                        not_found_fee = negotiated_not_found.get_effective_rate("managed_retrieval_rate")
                    else:
                        base_not_found = self.env["base.rate"].search([)]
                            ("service_type", "=", "not_found_search"),
                            ("state", "=", "confirmed"),
                            ("active", "=", True),

                        if base_not_found:
                            not_found_fee = base_not_found.managed_retrieval_rate
                    total += not_found_fee or 3.50

                item.total_cost = total


    def _compute_display_name(self):
            for item in self:
                parts = [item.name or "New Item"]
                if item.item_type:
                    type_display = dict(item._fields["item_type"].selection).get(item.item_type, item.item_type)
                    parts.append("(%s)" % type_display)
                if item.barcode:
                    parts.append("[%s]" % item.barcode)
                item.display_name = " ".join(parts)


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

    def _onchange_container_id(self):
            if self.container_id:
                self.current_location = self.container_id.current_location
                self.storage_location_id = self.container_id.storage_location_id


    def _onchange_document_id(self):
            if self.document_id:
                if self.document_id.container_id:
                    self.container_id = self.document_id.container_id
                if self.item_type == "document" and not self.name and self.document_id.name:
                    self.name = self.document_id.name


    def _onchange_item_type(self):
            if self.item_type in ("container", "box"):
                self.document_id = False


    def _onchange_priority(self):
            """Update sequence based on priority for ordering""":
            if self.priority:
                priority_sequence_map = {}
                    '0': 100,  # Low priority - higher sequence number
                    '1': 50,   # Normal priority
                    '2': 20,   # High priority - lower sequence number
                    '3': 10,   # Very High priority - lowest sequence number

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
            for item in self:
                if item.status != "pending":
                    raise UserError(_("Only pending items can be located."))
                item._update_status()
                    "located",
                    _("Item located by %s", self.env.user.name),
                    {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}



    def action_retrieve_item(self):
            for item in self:
                if item.status != "located":
                    raise UserError(_("Item must be located before retrieval."))
                item._update_status()
                    "retrieved",
                    _("Item retrieved by %s", self.env.user.name),
                    {"retrieval_date": fields.Datetime.now(), "retrieved_by_id": self.env.user.id}



    def action_package_item(self):
            for item in self:
                if item.status != "retrieved":
                    raise UserError(_("Item must be retrieved before packaging."))
                item._update_status("packaged", _("Item packaged by %s", self.env.user.name))


    def action_deliver_item(self):
            for item in self:
                if item.status != "packaged":
                    raise UserError(_("Item must be packaged before delivery."))
                item._update_status("delivered", _("Item delivered by %s", self.env.user.name))


    def action_return_item(self):
            for item in self:
                if item.status != "delivered":
                    raise UserError(_("Item must be delivered before return."))
                item._update_status()
                    "returned",
                    _("Item returned by %s", self.env.user.name),
                    {"return_date": fields.Date.today()}


        # ============================================================================
            # SEARCH WORKFLOW ACTION METHODS
        # ============================================================================

    def action_begin_search_process(self):
            for item in self:
                if item.status != "pending":
                    raise UserError(_("Only pending items can start the search process."))
                item._update_status()
                    "searching",
                    _("Search started by %s for file: %s", self.env.user.name, item.requested_file_name or item.name)



    def action_record_container_search(self, container_id, found=False, notes=""):
            self.ensure_one()
            if container_id not in self.searched_container_ids.ids:
                self.searched_container_ids = [(4, container_id)]

            self.env["document.search.attempt"].create({)}
                "retrieval_item_id": self.id,
                "container_id": container_id,
                "searched_by_id": self.env.user.id,
                "search_date": fields.Datetime.now(),
                "found": found,
                "notes": notes,


            if found:
                self.write({)}
                    "status": "located",
                    "file_discovered": True,
                    "discovery_date": fields.Datetime.now(),
                    "discovery_container_id": container_id,
                    "container_id": container_id,

            return True


    def action_mark_not_found(self, reason="not_in_container", notes=""):
            for item in self:
                reason_display = dict(item._fields["not_found_reason"].selection).get(reason, reason)
                message = _()
                    "File marked as NOT FOUND by %s. Searched %s containers (%s unsuccessful). Reason: %s",
                    self.env.user.name,
                    item.containers_accessed_count,
                    item.containers_not_found_count,
                    reason_display

                item._update_status()
                    "not_found",
                    message,
                    {"not_found_reason": reason, "not_found_notes": notes or _("File not found after search.")}



    def action_barcode_discovered_file(self, barcode, document_vals=None):
            self.ensure_one()
            if not self.file_discovered:
                raise UserError(_("File must be marked as discovered before barcoding."))

            self.write({"barcode": barcode, "status": "located"})

            if document_vals and self.discovery_container_id:
                document_vals.update({)}
                    "name": self.requested_file_name or self.name,
                    "barcode": barcode,
                    "container_id": self.discovery_container_id.id,
                    "partner_id": self.partner_id.id if self.partner_id else False,:

                document = self.env["records.document"].create(document_vals)
                self.document_id = document.id

            self.message_post()
                body=_("File barcoded by %s with barcode: %s", self.env.user.name, barcode),
                message_type="notification",

            return True

        # ============================================================================
            # SEARCH AND QUERY METHODS
        # ============================================================================

    def search_items_by_status(self, status_list=None):
            """Search retrieval items by status"""
            if not status_list:
                status_list = ['pending', 'searching', 'located']

            domain = [('status', 'in', status_list)]
            return self.search(domain, order='priority desc, create_date desc')


    def search_items_by_partner(self, partner_id, limit=None):
            """Search retrieval items by partner"""
            domain = [('partner_id', '=', partner_id)]
            return self.search(domain, limit=limit, order='create_date desc')


    def search_related_containers(self):
            """Search for containers related to this item""":
            self.ensure_one()
            if self.partner_id:
                return self.env['records.container'].search([)]
                    ('partner_id', '=', self.partner_id.id),
                    ('state', '=', 'active')

            return self.env['records.container']


    def search_items_by_priority(self, priority_level='2', limit=None):
            """Search retrieval items by priority level"""
            domain = [('priority', '>=', priority_level)]
            return self.search(domain, limit=limit, order='priority desc, create_date desc')


    def get_high_priority_items(self, partner_id=None):
            """Get high and very high priority items"""
            domain = [('priority', 'in', ['2', '3']), ('status', 'in', ['pending', 'searching', 'located'])]
            if partner_id:
                domain.append(('partner_id', '=', partner_id))
            return self.search(domain, order='priority desc, create_date desc'))))))))))))))))

