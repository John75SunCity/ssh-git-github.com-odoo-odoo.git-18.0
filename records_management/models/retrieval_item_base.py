from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging


_logger = logging.getLogger(__name__)


class RetrievalItemBase(models.AbstractModel):
    """Base model for retrieval items (scan, file, etc.) providing common functionality"""
    _name = 'retrieval.item.base'
    _description = 'Retrieval Item Base (Abstract)'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string='Item Reference', required=True, tracking=True)
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company)

    # ============================================================================
    # USER ASSIGNMENT AND TRACKING
    # ============================================================================
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned User', default=lambda self: self.env.user, tracking=True)
    retrieved_by_id = fields.Many2one(comodel_name='res.users', string='Retrieved By')
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Very High')
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # STATUS AND WORKFLOW
    # ============================================================================
    status = fields.Selection([
        ('pending', 'Pending'),
        ('searching', 'Searching'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('completed', 'Completed'),
        ('not_found', 'Not Found'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', tracking=True, required=True)

    state = fields.Selection(related='status', string='State')

    # ============================================================================
    # PARTNER AND CUSTOMER INFORMATION
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', tracking=True)

    # ============================================================================
    # LOCATION AND CONTAINER TRACKING
    # ============================================================================
    location_id = fields.Many2one(comodel_name='stock.location', string='Current Location')
    container_id = fields.Many2one(comodel_name='records.container', string='Container')
    current_location = fields.Char(string='Current Location Description')

    # ============================================================================
    # DESCRIPTIONS AND NOTES
    # ============================================================================
    description = fields.Text(string='Item Description')
    notes = fields.Text(string='Notes')
    handling_instructions = fields.Text(string='Handling Instructions')

    # ============================================================================
    # BARCODE AND IDENTIFICATION
    # ============================================================================
    barcode = fields.Char(string='Barcode/ID')
    tracking_number = fields.Char(string='Tracking Number')

    # ============================================================================
    # TIMING FIELDS
    # ============================================================================
    retrieval_date = fields.Datetime(string='Retrieved Date')
    estimated_time = fields.Float(string='Estimated Time (hours)')
    actual_time = fields.Float(string='Actual Time (hours)')

    # ============================================================================
    # SECURITY AND ACCESS
    # ============================================================================
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted')
    ], string='Security Level', default='internal')

    access_authorized_by_id = fields.Many2one(comodel_name='res.users', string='Access Authorized By')
    authorization_date = fields.Datetime(string='Authorization Date')

    # ============================================================================
    # CONDITION TRACKING
    # ============================================================================
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

    condition_notes = fields.Text(string='Condition Notes')

    # ============================================================================
    # SPECIAL HANDLING
    # ============================================================================
    special_handling = fields.Boolean(string='Special Handling Required')
    fragile = fields.Boolean(string='Fragile Item')
    quality_checked = fields.Boolean(string='Quality Checked')
    quality_issues = fields.Text(string='Quality Issues')

    # ============================================================================
    # MEASUREMENTS
    # ============================================================================
    estimated_weight = fields.Float(string='Estimated Weight (kg)')
    actual_weight = fields.Float(string='Actual Weight (kg)')
    dimensions = fields.Char(string='Dimensions (LxWxH)')
    estimated_pages = fields.Integer(string='Estimated Pages', default=0)

    # ============================================================================
    # NOT FOUND HANDLING
    # ============================================================================
    not_found_reason = fields.Selection([
        ('not_in_container', 'Not in Container'),
        ('container_missing', 'Container Missing'),
        ('destroyed', 'Already Destroyed'),
        ('misfiled', 'Misfiled'),
        ('access_denied', 'Access Denied'),
        ('other', 'Other Reason')
    ], string='Not Found Reason')

    not_found_notes = fields.Text(string='Not Found Notes')

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    @api.depends('name', 'barcode', 'status')
    def _compute_display_name(self):
        """Compute display name for the retrieval item"""
        for item in self:
            parts = [item.name or "New Item"]
            if item.barcode:
                parts.append(f"[{item.barcode}]")
            status_display = dict(item._fields['status'].selection).get(item.status, item.status)
            parts.append(f"({status_display})")
            item.display_name = " ".join(parts)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('container_id')
    def _onchange_container_id(self):
        """Update location when container changes"""
        if self.container_id:
            self.current_location = self.container_id.current_location
            self.location_id = self.container_id.location_id

    @api.onchange('status')
    def _onchange_status(self):
        """Handle status changes"""
        if self.status == 'retrieved' and not self.retrieval_date:
            self.retrieval_date = fields.Datetime.now()
            self.retrieved_by_id = self.env.user.id

    # ============================================================================
    # CONSTRAINT METHODS
    # ============================================================================
    @api.constrains('status', 'partner_id')
    def _check_partner_required(self):
        """Ensure partner is set for non-cancelled items"""
        for item in self:
            if item.status != 'cancelled' and not item.partner_id:
                raise ValidationError(_("Customer is required for retrieval items."))

    @api.constrains('estimated_time', 'actual_time')
    def _check_time_values(self):
        """Validate time values are positive"""
        for item in self:
            if item.estimated_time and item.estimated_time < 0:
                raise ValidationError(_("Estimated time must be positive."))
            if item.actual_time and item.actual_time < 0:
                raise ValidationError(_("Actual time must be positive."))

    # ============================================================================
    # STATUS UPDATE METHODS
    # ============================================================================
    def _update_status(self, new_status, message_body=None, extra_vals=None):
        """Update status with optional message and extra values"""
        self.ensure_one()
        vals = {'status': new_status}
        if extra_vals:
            vals.update(extra_vals)

        self.write(vals)

        if message_body:
            self.message_post(body=message_body, message_type='notification')

        return True

    def action_start_retrieval(self):
        """Start the retrieval search process (preferred method name)"""
        self.ensure_one()
        if self.status != 'pending':
            raise UserError(_("Only pending items can start the search process."))

        self._update_status(
            'searching',
            _("Search process started"),
            {'user_id': self.env.user.id}
        )

    def action_start_search(self):
        """DEPRECATED: kept for backward compatibility. Use action_start_retrieval."""
        self.ensure_one()  # Ensure single record per Odoo action method guideline
        _logger.warning("action_start_search is deprecated; use action_start_retrieval instead.")
        return self.action_start_retrieval()

    def action_mark_located(self):
        """Mark item as located"""
        self.ensure_one()
        if self.status not in ['pending', 'searching']:
            raise UserError(_("Item must be pending or searching to be marked as located."))

        self._update_status(
            'located',
            _("Item has been located"),
            {'retrieval_date': fields.Datetime.now()}
        )

    def action_mark_retrieved(self):
        """Mark item as retrieved"""
        self.ensure_one()
        if self.status != 'located':
            raise UserError(_("Item must be located before it can be retrieved."))

        self._update_status(
            'retrieved',
            _("Item has been retrieved"),
            {
                'retrieval_date': fields.Datetime.now(),
                'retrieved_by_id': self.env.user.id
            }
        )

    def action_mark_completed(self):
        """Mark item as completed"""
        self.ensure_one()
        if self.status != 'retrieved':
            raise UserError(_("Item must be retrieved before it can be completed."))

        self._update_status(
            'completed',
            _("Item processing completed")
        )

    def action_mark_not_found(self, reason='not_in_container', notes=''):
        """Mark item as not found"""
        self.ensure_one()
        if self.status not in ['pending', 'searching']:
            raise UserError(_("Only pending or searching items can be marked as not found."))

        self._update_status(
            'not_found',
            _("Item marked as not found"),
            {
                'not_found_reason': reason,
                'not_found_notes': notes or _("Item not found after search.")
            }
        )

    def action_cancel(self):
        """Cancel the retrieval item"""
        self.ensure_one()
        if self.status in ['completed', 'not_found']:
            raise UserError(_("Cannot cancel completed or not found items."))

        self._update_status(
            'cancelled',
            _("Item has been cancelled")
        )

    # ============================================================================
    # SEARCH AND UTILITY METHODS
    # ============================================================================
    def find_by_status(self, status_list=None):
        """Search items by status"""
        if not status_list:
            status_list = ['pending', 'searching', 'located']

        domain = [('status', 'in', status_list)]
        return self.search(domain, order='priority desc, create_date desc')

    def find_by_partner(self, partner_id, limit=None):
        """Search items by partner"""
        domain = [('partner_id', '=', partner_id)]
        return self.search(domain, limit=limit, order='create_date desc')

    def get_high_priority_items(self, partner_id=None):
        """Get high and very high priority items"""
        domain = [
            ('priority', 'in', ['2', '3']),
            ('status', 'in', ['pending', 'searching', 'located'])
        ]
        if partner_id:
            domain.append(('partner_id', '=', partner_id))

        return self.search(domain, order='priority desc, create_date desc')

    # ============================================================================
    # AUDIT AND LOGGING
    # ============================================================================
    def log_activity(self, activity_type, notes=''):
        """Log activity for audit trail"""
        self.ensure_one()
        activity_msg = _("Activity logged")
        if notes:
            activity_msg += ": " + notes
        self.message_post(
            body=activity_msg,
            message_type='notification'
        )
        return True

    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    def get_status_color(self):
        """Get color for status display"""
        self.ensure_one()
        color_map = {
            'pending': 'secondary',
            'searching': 'info',
            'located': 'warning',
            'retrieved': 'primary',
            'completed': 'success',
            'not_found': 'danger',
            'cancelled': 'dark'
        }
        return color_map.get(self.status, 'secondary')

    def get_priority_color(self):
        """Get color for priority display"""
        self.ensure_one()
        color_map = {
            '0': 'secondary',  # Low
            '1': 'info',       # Normal
            '2': 'warning',    # High
            '3': 'danger'      # Very High
        }
        return color_map.get(self.priority, 'info')
