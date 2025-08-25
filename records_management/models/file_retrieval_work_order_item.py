from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class FileRetrievalWorkOrderItem(models.Model):
    _name = 'file.retrieval.work.order.item'
    _description = 'File Retrieval Work Order Item'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'work_order_id, sequence, name'
    _rec_name = 'display_name'

    # ============================================================================
    # FIELDS
    # ============================================================================
    name = fields.Char(string="Item Reference", required=True, index=True, copy=False, default=lambda self: _('New'))
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    description = fields.Text(string="Description")
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one('res.company', string='Company', related='work_order_id.company_id', store=True)
    active = fields.Boolean(string='Active', default=True)

    work_order_id = fields.Many2one('file.retrieval.work.order', string='Work Order', required=True, ondelete='cascade')
    partner_id = fields.Many2one('res.partner', string='Customer', related='work_order_id.partner_id', store=True)

    file_name = fields.Char(string="File Name", required=True)
    estimated_pages = fields.Integer(string="Estimated Pages")
    actual_pages = fields.Integer(string="Actual Pages")

    file_type = fields.Selection([('document', 'Document'), ('folder', 'Folder'), ('other', 'Other')], string="File Type")
    file_format = fields.Selection([('paper', 'Paper'), ('digital', 'Digital')], string="File Format")

    container_id = fields.Many2one('records.container', string="Container")
    container_location = fields.Char(string="Location in Container", related='container_id.location_id.name', readonly=True)
    location_notes = fields.Text(string="Location Notes")
    file_position = fields.Char(string="Position in Container")

    status = fields.Selection([
        ('pending', 'Pending'),
        ('locating', 'Locating'),
        ('located', 'Located'),
        ('retrieving', 'Retrieving'),
        ('retrieved', 'Retrieved'),
        ('quality_checked', 'Quality Checked'),
        ('packaged', 'Packaged'),
        ('not_found', 'Not Found'),
        ('damaged', 'Damaged'),
    ], string='Status', default='pending', tracking=True)

    condition = fields.Selection([('good', 'Good'), ('fair', 'Fair'), ('poor', 'Poor'), ('damaged', 'Damaged')], string="Condition")
    quality_notes = fields.Text(string="Quality Notes")
    quality_approved = fields.Boolean(string="Quality Approved")
    quality_approved_by_id = fields.Many2one('res.users', string="Approved By")
    quality_approved_date = fields.Datetime(string="Approved Date")

    date_located = fields.Datetime(string="Date Located")
    date_retrieved = fields.Datetime(string="Date Retrieved")
    date_quality_checked = fields.Datetime(string="Date Quality Checked")

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('estimated_pages', 'actual_pages')
    def _check_page_counts(self):
        for record in self:
            if record.estimated_pages < 0:
                raise ValidationError(_("Estimated pages cannot be negative."))
            if record.actual_pages and record.actual_pages < 0:
                raise ValidationError(_("Actual pages cannot be negative."))

    @api.constrains('quality_approved', 'status')
    def _check_quality_approval_consistency(self):
        for record in self:
            if record.quality_approved and record.status not in ['quality_checked', 'packaged']:
                raise ValidationError(_("Quality can only be approved for items that have passed the quality check."))

    @api.constrains('name', 'work_order_id')
    def _check_unique_reference_per_order(self):
        for record in self:
            if record.work_order_id and record.name and record.name != _('New'):
                domain = [
                    ('work_order_id', '=', record.work_order_id.id),
                    ('name', '=', record.name),
                    ('id', '!=', record.id)
                ]
                if self.search_count(domain) > 0:
                    raise ValidationError(_("Item reference '%s' must be unique per work order.", record.name))

    # ============================================================================
    # COMPUTED METHODS
    # ============================================================================
    @api.depends('name', 'file_name')
    def _compute_display_name(self):
        for record in self:
            if record.file_name:
                record.display_name = f"{record.name} - {record.file_name}"
            else:
                record.display_name = record.name or _("New Item")

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_located(self):
        self.ensure_one()
        self.write({
            "status": "located",
            "date_located": fields.Datetime.now()
        })
        self.message_post(body=_("File marked as located."), message_type="notification")
        return True

    def action_mark_retrieved(self):
        self.ensure_one()
        if self.status not in ["located", "retrieving"]:
            raise UserError(_("Item must be located before it can be retrieved."))
        self.write({
            "status": "retrieved",
            "date_retrieved": fields.Datetime.now()
        })
        self.message_post(body=_("File marked as retrieved."), message_type="notification")
        return True

    def action_quality_check(self):
        self.ensure_one()
        if self.status != "retrieved":
            raise UserError(_("Item must be retrieved before a quality check can be performed."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Quality Check"),
            "res_model": "file.quality.check.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {
                "default_item_id": self.id,
                "default_work_order_id": self.work_order_id.id,
            }
        }

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("name", _("New")) == _("New"):
                sequence_code = 'file.retrieval.work.order.item'
                vals["name"] = self.env["ir.sequence"].next_by_code(sequence_code) or _("New")
        return super().create(vals_list)

    def write(self, vals):
        res = super().write(vals)
        if "status" in vals:
            for record in self:
                if hasattr(record.work_order_id, '_update_progress_metrics'):
                    record.work_order_id._update_progress_metrics()
        return res

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

