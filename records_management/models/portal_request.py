from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class PortalRequest(models.Model):
    _name = 'portal.request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Portal Customer Request'
    _order = 'priority desc, create_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    name = fields.Char(string='Request #', required=True, copy=False, readonly=True, default='New', index=True)
    title = fields.Char(string='Request Title', help='Descriptive title for this request')
    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)
    company_id = fields.Many2one(comodel_name='res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    active = fields.Boolean(default=True)
    partner_id = fields.Many2one(comodel_name='res.partner', string='Customer', required=True, tracking=True)
    user_id = fields.Many2one(comodel_name='res.users', string='Assigned To', tracking=True)
    # Contextual label disambiguation (Batch 2)
    description = fields.Html(string='Request Details', required=True)
    
    @api.depends('name', 'title', 'request_type', 'partner_id')
    def _compute_display_name(self):
        for record in self:
            if record.title:
                record.display_name = "%s - %s" % (record.name, record.title)
            elif record.partner_id:
                record.display_name = "%s - %s" % (record.name, record.partner_id.name)
            else:
                record.display_name = record.name

    # Portal-specific fields (added for controller compatibility)
    department_id = fields.Many2one(
        comodel_name='records.department', 
        string='Department',
        help='Department associated with this request'
    )
    requester_id = fields.Many2one(
        comodel_name='res.partner',
        string='Requester Contact',
        help='The specific contact who submitted the request'
    )
    target_location_id = fields.Many2one(
        comodel_name='stock.location',
        string='Target Location',
        help='Target location for move/retrieval requests'
    )
    pickup_date = fields.Date(
        string='Preferred Pickup Date',
        help='Customer preferred date for pickup'
    )
    notes = fields.Text(
        string='Additional Notes',
        help='Additional notes or instructions from portal user'
    )
    created_via_portal = fields.Boolean(
        string='Created via Portal',
        default=False,
        help='Indicates this request was submitted through customer portal'
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('rejected', 'Rejected'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', readonly=True, tracking=True)

    request_type = fields.Selection([
        ('destruction', 'Destruction'),
        ('pickup', 'Pickup'),
        ('retrieval', 'File Retrieval'),
        ('file_search', 'File Search'),
        ('scanning', 'Document Scanning'),
        ('shredding', 'Shredding Service'),
        ('audit', 'Audit Request'),
        ('consultation', 'Consultation'),
        ('other', 'Other'),
    ], string='Request Type', required=True, default='other', tracking=True)

    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent'),
    ], string='Priority', default='1', tracking=True)

    # ============================================================================
    # DATE & TIME TRACKING
    # ============================================================================
    requested_date = fields.Datetime(string='Requested Date', readonly=True)
    deadline = fields.Datetime(string='Deadline', tracking=True)
    completion_date = fields.Datetime(string='Completion Date', readonly=True)
    estimated_hours = fields.Float(string='Estimated Hours', tracking=True)
    actual_hours = fields.Float(string='Actual Hours', readonly=True)
    is_overdue = fields.Boolean(string='Is Overdue', compute='_compute_is_overdue', store=True)

    # --------------------------------------------------------------------------
    # VIRTUAL / SEARCH OPTIMIZATION FIELDS (Dynamic date domain refactor)
    # --------------------------------------------------------------------------
    requested_last_7d = fields.Boolean(
        string='Requested Last 7 Days',
        compute='_compute_requested_period_flags',
        search='_search_requested_last_7d',
        help='Indicates the request was created (requested) within the past 7 days.'
    )
    requested_last_30d = fields.Boolean(
        string='Requested Last 30 Days',
        compute='_compute_requested_period_flags',
        search='_search_requested_last_30d',
        help='Indicates the request was created (requested) within the past 30 days.'
    )

    # ============================================================================
    # BILLING & COST
    # ============================================================================
    currency_id = fields.Many2one(comodel_name='res.currency', related='company_id.currency_id', string='Currency')
    estimated_cost = fields.Monetary(string='Estimated Cost', currency_field='currency_id', tracking=True)
    actual_cost = fields.Monetary(string='Actual Cost', currency_field='currency_id', readonly=True)
    billing_status = fields.Selection([
        ('not_billable', 'Not Billable'),
        ('to_bill', 'To Bill'),
        ('billed', 'Billed'),
    ], string='Billing Status', default='not_billable', tracking=True)

    # ============================================================================
    # COMPLIANCE & SIGNATURES (NAID AAA)
    # ============================================================================
    requires_naid_compliance = fields.Boolean(string='NAID Compliance Required')
    customer_signature = fields.Binary(string='Customer Signature', copy=False)
    customer_signature_date = fields.Datetime(string='Customer Signature Date', readonly=True)
    technician_signature = fields.Binary(string='Technician Signature', copy=False)
    technician_signature_date = fields.Datetime(string='Technician Signature Date', readonly=True)
    certificate_of_destruction_id = fields.Many2one(comodel_name='ir.attachment', string='Certificate of Destruction', readonly=True)

    # ============================================================================
    # RELATIONAL & COMPUTED FIELDS
    # ============================================================================
    work_order_id = fields.Many2one(comodel_name='project.task', string='Work Order', readonly=True)
    attachment_count = fields.Integer(compute='_compute_attachment_count', string='Attachments')
    
    # Container and File Relationships
    container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='portal_request_container_rel',
        column1='request_id',
        column2='container_id',
        string='Containers',
        help='Containers related to this request'
    )
    file_ids = fields.Many2many(
        comodel_name='records.file',
        relation='portal_request_file_rel',
        column1='request_id',
        column2='file_id',
        string='Files',
        help='Files related to this request'
    )
    
    # File Search Fields
    search_file_name = fields.Char(string='File Name to Search', help='Name of file customer is looking for')
    search_date_from = fields.Date(string='File Date From', help='Earliest possible file date')
    search_date_to = fields.Date(string='File Date To', help='Latest possible file date')
    search_alpha_range = fields.Char(string='Alphabetical Range', help='E.g., A-D, Jane-Mary')
    suggested_container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='portal_request_suggested_container_rel',
        column1='request_id',
        column2='container_id',
        string='Suggested Containers',
        help='Containers that might contain the searched file (auto-populated)'
    )
    selected_search_container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='portal_request_selected_search_container_rel',
        column1='request_id',
        column2='container_id',
        string='Selected Search Containers',
        help='Containers customer wants us to search through'
    )
    
    # Notification Preferences
    notify_on_file_located = fields.Boolean(
        string='Notify When File Located',
        default=True,
        help='Send notification when technician scans and locates the file'
    )
    notify_on_ready_for_delivery = fields.Boolean(
        string='Notify When Ready for Delivery',
        default=True,
        help='Send notification when order is prepped and ready for transit'
    )
    notification_method = fields.Selection([
        ('email', 'Email Only'),
        ('sms', 'SMS/Text Only'),
        ('both', 'Email and SMS'),
        ('none', 'No Notifications'),
    ], string='Notification Method', default='email', required=True)
    
    # Tracking Fields
    file_located_date = fields.Datetime(string='File Located Date', readonly=True)
    file_located_by = fields.Many2one(comodel_name='res.users', string='Located By', readonly=True)
    ready_for_delivery_date = fields.Datetime(string='Ready for Delivery Date', readonly=True)
    ready_for_delivery_by = fields.Many2one(comodel_name='res.users', string='Prepared By', readonly=True)
    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Shredding Service',
        help='Selected shredding service for this request'
    )
    assigned_operator_id = fields.Many2one(
        'naid.operator.certification',
        string='Assigned Operator',
        help='NAID certified operator assigned to this service request'
    )
    retrieval_items = fields.Text(
        string='Retrieval Items JSON',
        help='JSON data containing retrieval item details (containers, documents, files)'
    )

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('deadline', 'requested_date')
    def _check_deadline_dates(self):
        for record in self:
            if record.deadline and record.requested_date and record.deadline < record.requested_date:
                raise ValidationError(_("Deadline cannot be before the requested date."))

    @api.constrains('estimated_cost', 'actual_cost')
    def _check_cost_values(self):
        for record in self:
            if (record.estimated_cost and record.estimated_cost < 0) or (record.actual_cost and record.actual_cost < 0):
                raise ValidationError(_("Costs cannot be negative."))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('deadline', 'state')
    def _compute_is_overdue(self):
        for record in self:
            record.is_overdue = (
                record.deadline and
                record.deadline < fields.Datetime.now() and
                record.state not in ('completed', 'cancelled', 'rejected')
            )

    @api.depends('requested_date')
    def _compute_requested_period_flags(self):
        """Compute recency flags for requested_date to remove Python arithmetic from view domains."""
        today = fields.Date.context_today(self)
        # Define date thresholds
        from datetime import timedelta as _td
        last_7 = today - _td(days=7)
        last_30 = today - _td(days=30)
        for rec in self:
            rd = rec.requested_date.date() if rec.requested_date else None
            rec.requested_last_7d = bool(rd and rd >= last_7)
            rec.requested_last_30d = bool(rd and rd >= last_30)

    # ------------------------------------------------------------------
    # SEARCH HELPERS
    # ------------------------------------------------------------------
    def _search_requested_last_7d(self, operator, value):
        truthy = {True, '1', 1, 'true', 'True'}
        today = fields.Date.context_today(self)
        from datetime import timedelta as _td
        last_7 = today - _td(days=7)
        if operator in ('=', '==') and value in truthy:
            return [('requested_date', '>=', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        if operator in ('!=', '<>') and value in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        if operator in ('=', '==') and value not in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_7) + ' 00:00:00'))]
        return [('id', '!=', 0)]

    def _search_requested_last_30d(self, operator, value):
        truthy = {True, '1', 1, 'true', 'True'}
        today = fields.Date.context_today(self)
        from datetime import timedelta as _td
        last_30 = today - _td(days=30)
        if operator in ('=', '==') and value in truthy:
            return [('requested_date', '>=', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        if operator in ('!=', '<>') and value in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        if operator in ('=', '==') and value not in truthy:
            return ['|', ('requested_date', '=', False), ('requested_date', '<', fields.Datetime.to_datetime(str(last_30) + ' 00:00:00'))]
        return [('id', '!=', 0)]

    def _compute_attachment_count(self):
        for record in self:
            record.attachment_count = self.env['ir.attachment'].search_count([
                ('res_model', '=', self._name), ('res_id', '=', record.id)
            ])

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            # If name is being passed in (from old code), move it to title field
            if vals.get('name') and vals.get('name') not in ('New', _('New')):
                # Old code passed descriptive name, move it to title
                vals['title'] = vals.get('name')
                vals['name'] = 'New'
            # Generate sequence number for request #
            if vals.get('name', 'New') == 'New':
                vals['name'] = self.env['ir.sequence'].next_by_code('portal.request') or 'New'
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_submit(self):
        self.ensure_one()
        self.write({'state': 'submitted', 'requested_date': fields.Datetime.now()})
        self.message_post(body=_("Request submitted by %s.", self.env.user.name))
        return True

    def action_approve(self):
        self.ensure_one()
        if self.state != 'submitted':
            raise UserError(_("Only submitted requests can be approved."))
        self.write({'state': 'approved'})
        self.message_post(body=_("Request approved by %s.", self.env.user.name))
        self._create_work_order()
        return True

    def action_reject(self):
        # This would typically open a wizard to ask for a rejection reason
        self.ensure_one()
        self.write({'state': 'rejected'})
        self.message_post(body=_("Request rejected by %s.", self.env.user.name))
        return True

    def action_start_progress(self):
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_("Only approved requests can be started."))
        self.write({'state': 'in_progress'})
        self.message_post(body=_("Work has started on this request."))

    def action_complete(self):
        self.ensure_one()
        self.write({'state': 'completed', 'completion_date': fields.Datetime.now()})
        self.message_post(body=_("Request has been completed."))
        self._create_billing_and_invoice()

    def _create_billing_and_invoice(self):
        if self.request_type != 'destruction':
            return  # Only for destruction requests; expand as needed
        
        billing = self.env['records.billing'].create({
            'partner_id': self.partner_id.id,
            'date': fields.Date.today(),
            'billing_config_id': self.partner_id.billing_config_id.id if hasattr(self.partner_id, 'billing_config_id') else False,
            'billing_line_ids': [(0, 0, {
                'description': 'Destruction Service for Request %s' % self.name,
                'quantity': 1,  # Adjust based on actual items
                'price_unit': 100.0,  # Replace with rate from config or profile
            })],
            'state': 'confirmed',
        })
        billing.action_create_invoice()

    def action_cancel(self):
        self.ensure_one()
        if self.state in ['completed']:
            raise UserError(_("Completed requests cannot be cancelled."))
        self.write({'state': 'cancelled'})
        self.message_post(body=_("Request has been cancelled."))

    def action_view_attachments(self):
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Attachments'),
            'res_model': 'ir.attachment',
            'view_mode': 'kanban,list,form',
            'domain': [('res_model', '=', self._name), ('res_id', '=', self.id)],
            'context': {'default_res_model': self._name, 'default_res_id': self.id},
        }

    def action_convert_to_work_order(self):
        """Convert this single request to a work order."""
        self.ensure_one()
        if self.state not in ['submitted', 'approved']:
            raise UserError(_("Only submitted or approved requests can be converted to work orders."))
        if self.work_order_id:
            raise UserError(_("This request already has a linked work order."))
        
        work_order = self._create_work_order()
        if work_order:
            self.write({'state': 'in_progress'})
            self.message_post(body=_("Converted to work order."))
            return {
                'type': 'ir.actions.act_window',
                'name': _('Work Order'),
                'res_model': work_order._name,
                'view_mode': 'form',
                'res_id': work_order.id,
                'target': 'current',
            }
        return False

    @api.model
    def action_batch_convert_to_work_orders(self):
        """Convert selected requests to individual work orders."""
        requests = self.env['portal.request'].browse(self.env.context.get('active_ids', []))
        if not requests:
            raise UserError(_("No requests selected."))
        
        created_orders = self.env[self._name]
        for request in requests:
            if request.state not in ['submitted', 'approved']:
                continue
            if request.work_order_id:
                continue
            work_order = request._create_work_order()
            if work_order:
                request.write({'state': 'in_progress'})
                request.message_post(body=_("Converted to individual work order %s.") % work_order.name)
                created_orders |= work_order
        
        if created_orders:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Created Work Orders'),
                'res_model': created_orders._name,
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_orders.ids)],
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}

    @api.model
    def action_merge_convert_to_work_orders(self):
        """Merge selected requests by customer/department and convert to consolidated work orders."""
        requests = self.env['portal.request'].browse(self.env.context.get('active_ids', []))
        if not requests:
            raise UserError(_("No requests selected."))
        
        # Group by (partner_id, department_id)
        groups = {}
        for request in requests:
            if request.state not in ['submitted', 'approved'] or request.work_order_id:
                continue
            key = (request.partner_id.id, request.department_id.id if request.department_id else 0)
            if key not in groups:
                groups[key] = []
            groups[key].append(request)
        
        created_orders = self.env[self._name]
        for key, group_requests in groups.items():
            if not group_requests:
                continue
            
            lead_request = group_requests[0]
            # Create consolidated work order
            work_order_vals = {
                'partner_id': lead_request.partner_id.id,
                'department_id': lead_request.department_id.id,
                'portal_request_id': lead_request.id,  # Link to lead request
                'description': _("Merged from requests: %s") % ', '.join(r.name for r in group_requests),
                # Add other mapped fields, summing quantities if applicable
            }
            
            # Handle different types
            if lead_request.request_type == 'shredding':
                work_order_vals.update({
                    'name': self.env['ir.sequence'].next_by_code('work.order.shredding') or _('New'),
                    'shredding_service_type': lead_request.shredding_service_id.service_type if lead_request.shredding_service_id else 'onsite',
                    'scheduled_date': min(r.pickup_date for r in group_requests if r.pickup_date) or fields.Datetime.now(),
                    'priority': max(r.priority for r in group_requests),
                    'special_instructions': '\n'.join(r.notes for r in group_requests if r.notes),
                })
                work_order = self.env['work.order.shredding'].create(work_order_vals)
            else:
                # For FSM-based
                fsm_project = self.env.ref('industry_fsm.fsm_project')
                task_vals = {
                    'name': _("Merged %s: %s") % (lead_request.request_type, ', '.join(r.name for r in group_requests)),
                    'project_id': fsm_project.id,
                    'partner_id': lead_request.partner_id.id,
                    'description': work_order_vals['description'],
                }
                work_order = self.env['project.task'].create(task_vals)
            
            # Link all requests to this work order
            for request in group_requests:
                request.write({
                    'work_order_id': work_order.id,
                    'state': 'in_progress'
                })
                request.message_post(body=_("Merged into consolidated work order %s.") % work_order.name)
            
            created_orders |= work_order
        
        if created_orders:
            return {
                'type': 'ir.actions.act_window',
                'name': _('Created Consolidated Work Orders'),
                'res_model': created_orders._name,
                'view_mode': 'list,form',
                'domain': [('id', 'in', created_orders.ids)],
                'target': 'current',
            }
        return {'type': 'ir.actions.act_window_close'}
    # ...existing code...
