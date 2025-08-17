from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import ValidationError


class FileRetrievalWorkOrderItem(models.Model):
    _name = 'file.retrieval.work.order.item'
    _description = 'File Retrieval Work Order Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char()
    display_name = fields.Char()
    description = fields.Text()
    sequence = fields.Integer()
    company_id = fields.Many2one()
    active = fields.Boolean()
    work_order_id = fields.Many2one()
    partner_id = fields.Many2one()
    file_name = fields.Char()
    estimated_pages = fields.Integer()
    actual_pages = fields.Integer()
    file_type = fields.Selection()
    file_format = fields.Selection()
    container_id = fields.Many2one()
    container_location = fields.Char()
    location_notes = fields.Text()
    file_position = fields.Char()
    status = fields.Selection()
    condition = fields.Selection()
    quality_notes = fields.Text()
    quality_approved = fields.Boolean()
    quality_approved_by_id = fields.Many2one()
    quality_approved_date = fields.Datetime()
    date_located = fields.Datetime()
    date_retrieved = fields.Datetime()
    date_quality_checked = fields.Datetime()
    state = fields.Selection()
    activity_ids = fields.One2many()
    message_follower_ids = fields.One2many()
    message_ids = fields.One2many()
    context = fields.Char(string='Context')
    domain = fields.Char(string='Domain')
    help = fields.Char(string='Help')
    res_model = fields.Char(string='Res Model')
    type = fields.Selection(string='Type')
    view_mode = fields.Char(string='View Mode')

    # ============================================================================
    # METHODS
    # ============================================================================
    def _compute_display_name(self):
            """Compute display name combining reference and description"""
            for record in self:
                if record.description:
                    # Limit description to 50 characters for display:
                    if len(record.description) > 50:
                        short_desc = record.description[:47] + "..."
                    else:
                        short_desc = record.description
                    record.display_name = _("%(name)s - %(desc)s", name=record.name, desc=short_desc)
                else:
                    record.display_name = record.name or _("New Item")

        # ============================================================================
            # ACTION METHODS
        # ============================================================================

    def action_mark_located(self):
            """Mark item as located"""
            self.ensure_one()
            self.write({)}
                "status": "located",
                "date_located": fields.Datetime.now()


            # Update work order progress
            if hasattr(self.work_order_id, '_update_progress_metrics'):
                self.work_order_id._update_progress_metrics()

            self.message_post()
                body=_("File located successfully"),
                message_type="notification"

            return True


    def action_mark_retrieved(self):
            """Mark item as retrieved"""
            self.ensure_one()
            if self.status not in ["located", "retrieving"]:
                raise ValidationError()
                    _("Item must be located before it can be retrieved")


            self.write({)}
                "status": "retrieved",
                "date_retrieved": fields.Datetime.now()


            # Update work order progress
            if hasattr(self.work_order_id, '_update_progress_metrics'):
                self.work_order_id._update_progress_metrics()

            self.message_post()
                body=_("File retrieved successfully"),
                message_type="notification"

            return True


    def action_quality_check(self):
            """Perform quality check on retrieved file"""
            self.ensure_one()
            if self.status != "retrieved":
                raise ValidationError()
                    _("Item must be retrieved before quality check")


            return {}
                "type": "ir.actions.act_window",
                "name": _("Quality Check"),
                "res_model": "file.quality.check.wizard",
                "view_mode": "form",
                "target": "new",
                "context": {}
                    "default_item_id": self.id,
                    "default_work_order_id": self.work_order_id.id,




    def action_approve_quality(self):
            """Approve quality for this item""":
            self.ensure_one()
            self.write({)}
                "status": "quality_checked",
                "quality_approved": True,
                "quality_approved_by_id": self.env.user.id,
                "quality_approved_date": fields.Datetime.now(),
                "date_quality_checked": fields.Datetime.now(),


            # Update work order progress
            if hasattr(self.work_order_id, '_update_progress_metrics'):
                self.work_order_id._update_progress_metrics()

            self.message_post()
                body=_("File quality approved by %s", self.env.user.name),
                message_type="notification",

            return True


    def action_mark_not_found(self):
            """Mark item as not found"""
            self.ensure_one()
            self.write({"status": "not_found"})

            self.message_post()
                body=_("File marked as not found"),
                message_type="notification"


            # Update work order progress
            if hasattr(self.work_order_id, '_update_progress_metrics'):
                self.work_order_id._update_progress_metrics()

            return True


    def action_mark_damaged(self):
            """Mark item as damaged"""
            self.ensure_one()
            self.write({)}
                "status": "damaged",
                "condition": "damaged"


            self.message_post()
                body=_("File marked as damaged"),
                message_type="notification"


            # Update work order progress
            if hasattr(self.work_order_id, '_update_progress_metrics'):
                self.work_order_id._update_progress_metrics()

            return True


    def action_start_locating(self):
            """Start the locating process"""
            self.ensure_one()
            if self.status != "pending":
                raise ValidationError()
                    _("Can only start locating pending items")


            self.write({"status": "locating"})
            self.message_post()
                body=_("Started locating file"),
                message_type="notification"

            return True


    def action_start_retrieving(self):
            """Start the retrieving process"""
            self.ensure_one()
            if self.status != "located":
                raise ValidationError()
                    _("Can only start retrieving located items")


            self.write({"status": "retrieving"})
            self.message_post()
                body=_("Started retrieving file"),
                message_type="notification"

            return True


    def action_package(self):
            """Package the item for delivery""":
            self.ensure_one()
            if self.status != "quality_checked":
                raise ValidationError()
                    _("Item must pass quality check before packaging")


            self.write({"status": "packaged"})
            self.message_post()
                body=_("File packaged for delivery"),:
                message_type="notification"

            return True

        # ============================================================================
            # BUSINESS METHODS
        # ============================================================================

    def get_retrieval_summary(self):
            """Get retrieval summary for this item""":
            self.ensure_one()
            return {}
                'item_reference': self.name,
                'file_name': self.file_name or '',
                'file_type': self.file_type,
                'file_format': self.file_format,
                'status': self.status,
                'condition': self.condition or '',
                'estimated_pages': self.estimated_pages,
                'actual_pages': self.actual_pages or 0,
                'container': self.container_id.name if self.container_id else '',:
                'quality_approved': self.quality_approved,
                'location_notes': self.location_notes or '',



    def update_progress_status(self, new_status, notes=None):
            """Update item status with optional notes"""
            self.ensure_one()
            vals = {'status': new_status}

            # Set timing fields based on status
            if new_status == 'located':

    def get_status_statistics(self):
            """Get statistics by status"""
            return self.read_group()
                domain=[],
                fields=['status'],
                groupby=['status']


        # ============================================================================
            # VALIDATION METHODS
        # ============================================================================

    def _check_page_counts(self):
            """Validate page counts are positive"""
            for record in self:
                if record.estimated_pages < 0:
                    raise ValidationError(_("Estimated pages cannot be negative"))
                if record.actual_pages and record.actual_pages < 0:
                    raise ValidationError(_("Actual pages cannot be negative"))


    def _check_quality_approval_consistency(self):
            """Ensure quality approval is consistent with status"""
            for record in self:
                if record.quality_approved and record.status not in [:]
                    "quality_checked", "packaged"

                    raise ValidationError()
                        _("Quality can only be approved for quality checked or packaged items"):



    def _check_unique_reference_per_order(self):
            """Ensure item reference is unique within work order"""
            for record in self:
                if record.work_order_id and record.name:
                    existing = self.search([)]
                        ('work_order_id', '=', record.work_order_id.id),
                        ('name', '=', record.name),
                        ('id', '!=', record.id)

                    if existing:
                        raise ValidationError()
                            _("Item reference %s already exists in this work order", record.name)


        # ============================================================================
            # ORM OVERRIDES
        # ============================================================================

    def create(self, vals_list):
            """Override create to generate sequence and validate"""
            for vals in vals_list:
                if vals.get("name", "New") == "New":
                    vals["name"] = self.env["ir.sequence").next_by_code(]
                        "file.retrieval.work.order.item"
                    ) or _("New"

            return super().create(vals_list)


    def write(self, vals):
            """Override write to track important changes"""
            result = super().write(vals)

            # Track status changes
            if "status" in vals:
                for record in self:
                    status_display = dict(record._fields['status'].selection).get(vals["status"], vals["status"])
                    record.message_post()
                        body=_("Item status changed to %s", status_display)


            return result

        # ============================================================================
            # UTILITY METHODS
        # ============================================================================

    def name_get(self):
            """Custom name display"""
            result = []
            for record in self:
                name = record.display_name or record.name
                result.append((record.id, name))
            return result


    def _name_search(self, name="", args=None, operator="ilike", limit=100, name_get_uid=None):
            """Enhanced search by name, file name, or description"""
            args = args or []
            domain = []

            if name:
                domain = []
                    "|", "|", "|",
                    ("name", operator, name),
                    ("file_name", operator, name),
                    ("description", operator, name),
                    ("display_name", operator, name),


            return self._search(domain + args, limit=limit, access_rights_uid=name_get_uid)


    def get_item_details(self):
            """Get detailed information about the item"""
            self.ensure_one()
            return {}
                'reference': self.name,
                'file_name': self.file_name,
                'description': self.description,
                'type': self.file_type,
                'format': self.file_format,
                'status': self.status,
                'condition': self.condition,
                'estimated_pages': self.estimated_pages,
                'actual_pages': self.actual_pages,
                'container': self.container_id.name if self.container_id else None,:
                'location': self.container_location,
                'position': self.file_position,
                'quality_approved': self.quality_approved,
                'quality_notes': self.quality_notes,


        # ============================================================================
            # REPORTING METHODS
        # ============================================================================

    def generate_retrieval_report(self, work_order_ids=None, date_from=None, date_to=None):
            """Generate retrieval report for items""":
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

            return {}
                'total_items': total_items,
                'by_status': by_status,
                'by_type': by_type,
                'total_pages': total_pages,
                'items': [item.get_retrieval_summary() for item in items],:
                'quality_approval_rate': len(items.filtered('quality_approved')) / total_items * 100 if total_items > 0 else 0,:

