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

    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    
    def notify_file_located(self, file_name, location):
        """Send notification when file is physically located and scanned."""
        self.ensure_one()
        
        if not self.notify_on_file_located or self.notification_method == 'none':
            return
        
        # Update tracking fields
        self.write({
            'file_located_date': fields.Datetime.now(),
            'file_located_by': self.env.user.id,
        })
        
        subject = _('File Located: %s') % file_name
        message = _(
            "Good news! We've located your file.\n\n"
            "File: %s\n"
            "Location: %s\n"
            "Request: %s\n"
            "Located by: %s on %s\n\n"
            "Your request is being processed and will be ready for delivery soon."
        ) % (
            file_name,
            location,
            self.name,
            self.env.user.name,
            fields.Datetime.now().strftime('%m/%d/%Y %I:%M %p')
        )
        
        # Send email notification
        if self.notification_method in ['email', 'both']:
            self.message_post(
                body=message,
                subject=subject,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=self.partner_id.ids,
            )
            # Send email to partner
            mail_values = {
                'subject': subject,
                'body_html': message.replace('\n', '<br/>'),
                'email_to': self.partner_id.email,
                'auto_delete': False,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
        
        # Send SMS notification
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            sms_message = _(
                "File Located: %s at %s. Request %s is being processed. - Records Management"
            ) % (file_name, location, self.name)
            self.env['sms.sms'].sudo().create({
                'number': self.partner_id.mobile,
                'body': sms_message,
            }).send()
    
    def notify_ready_for_delivery(self):
        """Send notification when order is prepped and ready for transit."""
        self.ensure_one()
        
        if not self.notify_on_ready_for_delivery or self.notification_method == 'none':
            return
        
        # Update tracking fields
        self.write({
            'ready_for_delivery_date': fields.Datetime.now(),
            'ready_for_delivery_by': self.env.user.id,
        })
        
        # Count items ready
        container_count = len(self.container_ids)
        file_count = len(self.file_ids)
        
        subject = _('Order Ready for Delivery: %s') % self.name
        message = _(
            "Your order has been prepared and is ready for delivery!\n\n"
            "Request: %s\n"
            "Items Ready:\n"
            "  - Containers: %d\n"
            "  - Files: %d\n"
            "Prepared by: %s on %s\n\n"
            "Estimated delivery: [See delivery schedule]\n\n"
            "Track your order at: /my/requests/%s"
        ) % (
            self.name,
            container_count,
            file_count,
            self.env.user.name,
            fields.Datetime.now().strftime('%m/%d/%Y %I:%M %p'),
            self.id
        )
        
        # Send email notification
        if self.notification_method in ['email', 'both']:
            self.message_post(
                body=message,
                subject=subject,
                message_type='notification',
                subtype_xmlid='mail.mt_comment',
                partner_ids=self.partner_id.ids,
            )
            mail_values = {
                'subject': subject,
                'body_html': message.replace('\n', '<br/>'),
                'email_to': self.partner_id.email,
                'auto_delete': False,
            }
            self.env['mail.mail'].sudo().create(mail_values).send()
        
        # Send SMS notification
        if self.notification_method in ['sms', 'both'] and self.partner_id.mobile:
            sms_message = _(
                "Order %s ready for delivery! %d containers, %d files. Track at: [portal link] - Records Management"
            ) % (self.name, container_count, file_count)
            self.env['sms.sms'].sudo().create({
                'number': self.partner_id.mobile,
                'body': sms_message,
            }).send()
    
    @api.model
    def search_matching_containers(self, file_name, date_from=None, date_to=None, alpha_range=None, partner_id=None):
        """
        Intelligent container matching for file search requests.
        Returns containers likely to contain the searched file.
        
        Args:
            file_name: Name of file being searched
            date_from: Earliest possible file date
            date_to: Latest possible file date
            alpha_range: Alphabetical range (e.g., 'A-D' or 'Jane-Mary')
            partner_id: Customer partner ID
        
        Returns:
            recordset of records.container
        """
        domain = [('partner_id', '=', partner_id)] if partner_id else []
        
        # Start with all customer's containers
        Container = self.env['records.container'].sudo()
        matching_containers = Container.search(domain)
        scored_containers = []
        
        for container in matching_containers:
            score = 0
            reasons = []
            
            # 1. Date range matching (highest priority)
            if date_from or date_to:
                container_date_from = container.date_range_start
                container_date_to = container.date_range_end
                
                if container_date_from and container_date_to:
                    # Check if date ranges overlap
                    if date_from and date_to:
                        if (container_date_from <= date_to and container_date_to >= date_from):
                            score += 50
                            reasons.append(_('Date range matches: %s to %s') % (
                                container_date_from.strftime('%m/%d/%Y'),
                                container_date_to.strftime('%m/%d/%Y')
                            ))
                    elif date_from and container_date_from <= date_from <= container_date_to:
                        score += 40
                        reasons.append(_('Contains date %s') % date_from.strftime('%m/%d/%Y'))
                    elif date_to and container_date_from <= date_to <= container_date_to:
                        score += 40
                        reasons.append(_('Contains date %s') % date_to.strftime('%m/%d/%Y'))
            
            # 2. Alphabetical range matching
            if alpha_range and container.alpha_range:
                # Simple contains check (can be enhanced)
                if alpha_range.upper() in container.alpha_range.upper():
                    score += 30
                    reasons.append(_('Alpha range matches: %s') % container.alpha_range)
                # Check if file name falls within alpha range
                elif file_name:
                    file_first_letter = file_name[0].upper()
                    container_range = container.alpha_range.upper()
                    # Example: container has "A-D", file is "Jane" (J)
                    if '-' in container_range:
                        range_parts = container_range.split('-')
                        if len(range_parts) == 2:
                            start_letter = range_parts[0].strip()[0] if range_parts[0].strip() else 'A'
                            end_letter = range_parts[1].strip()[0] if range_parts[1].strip() else 'Z'
                            if start_letter <= file_first_letter <= end_letter:
                                score += 25
                                reasons.append(_('File name falls in alpha range %s') % container.alpha_range)
            
            # 3. Content type/description keyword matching
            if file_name and container.content_description:
                # Extract key terms from file name
                file_terms = file_name.lower().split()
                description_lower = container.content_description.lower()
                
                for term in file_terms:
                    if len(term) > 3 and term in description_lower:
                        score += 10
                        reasons.append(_('Contains keyword: %s') % term)
            
            # 4. Container name/number matching
            if file_name:
                container_name_lower = (container.name or '').lower()
                container_number_lower = (container.container_number or '').lower()
                file_name_lower = file_name.lower()
                
                # Check for term files, HR files, etc.
                if 'term' in file_name_lower and 'term' in container_name_lower:
                    score += 20
                    reasons.append(_('Container name suggests term files'))
                
                # Extract department/category from file name (e.g., "HR-1000")
                if container.container_number and any(dept in file_name_lower for dept in ['hr', 'finance', 'legal', 'admin']):
                    if any(dept in container_number_lower for dept in ['hr', 'finance', 'legal', 'admin']):
                        score += 15
                        reasons.append(_('Department/category match'))
            
            # 5. Contents type matching
            if container.contents_type:
                contents_lower = container.contents_type.lower()
                if file_name:
                    # Check if file name suggests same contents type
                    if any(keyword in file_name.lower() for keyword in ['personnel', 'employee', 'hr']) and 'personnel' in contents_lower:
                        score += 15
                        reasons.append(_('Contents type match: %s') % container.contents_type)
            
            if score > 0:
                scored_containers.append({
                    'container': container,
                    'score': score,
                    'reasons': reasons
                })
        
        # Sort by score descending
        scored_containers.sort(key=lambda x: x['score'], reverse=True)
        
        # Return containers with scores > 0, attach matching info
        result = Container.browse([c['container'].id for c in scored_containers])
        
        # Store matching reasons for display
        for idx, container_data in enumerate(scored_containers):
            container_data['container'].matching_score = container_data['score']
            container_data['container'].matching_reasons = ', '.join(container_data['reasons'])
        
        return result

    def _create_work_order(self):
        """Create an FSM task for service-type requests."""
        self.ensure_one()
        if self.request_type in ['destruction', 'pickup', 'retrieval', 'shredding', 'scanning', 'audit'] and not self.work_order_id:
            fsm_project = self.env.ref('industry_fsm.fsm_project', raise_if_not_found=False)
            if not fsm_project:
                raise UserError(_("FSM Project not found. Please ensure the Field Service module is installed correctly."))

            # Map request type to task name prefix
            type_labels = {
                'destruction': _("Destruction Service"),
                'pickup': _("Pickup Service"),
                'retrieval': _("File Retrieval"),
                'shredding': _("Shredding Service"),
                'scanning': _("Document Scanning"),
                'audit': _("Compliance Audit"),
            }
            task_name = "%s: %s" % (type_labels.get(self.request_type, _("Service")), self.name)
            
            task_vals = {
                "name": task_name,
                "project_id": fsm_project.id,
                "partner_id": self.partner_id.id,
                "user_ids": [(6, 0, [self.user_id.id])] if self.user_id else [],
                "date_deadline": self.deadline.date() if self.deadline else fields.Date.today(),
                "description": self.description,
            }
            task = self.env['project.task'].create(task_vals)
            self.work_order_id = task.id
            self.message_post(body=_("Work Order %s created.", task.name))
            return task
        return False

    def action_create_work_order(self):
        """
        Manual action to create work order from customer request.
        Allows internal staff to convert any portal request into a work order
        as if they took the order directly from the customer.
        """
        self.ensure_one()
        if self.work_order_id:
            raise UserError(_("A work order already exists for this request: %s", self.work_order_id.name))
        
        # If request is in draft, auto-approve it first
        if self.state == 'draft':
            self.write({'state': 'submitted', 'requested_date': fields.Datetime.now()})
            self.message_post(body=_("Request auto-submitted by staff for work order creation."))
        
        if self.state == 'submitted':
            self.write({'state': 'approved'})
            self.message_post(body=_("Request approved by %s for work order creation.", self.env.user.name))
        
        # Create the work order
        task = self._create_work_order()
        
        if task:
            # Automatically start progress
            self.write({'state': 'in_progress'})
            return {
                'type': 'ir.actions.act_window',
                'name': _('Work Order'),
                'res_model': 'project.task',
                'view_mode': 'form',
                'res_id': task.id,
                'target': 'current',
            }
        else:
            raise UserError(_("Could not create work order. Request type may not support work orders."))

    def action_view_work_order(self):
        """Open the linked work order."""
        self.ensure_one()
        if not self.work_order_id:
            raise UserError(_("No work order linked to this request."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Work Order'),
            'res_model': 'project.task',
            'view_mode': 'form',
            'res_id': self.work_order_id.id,
            'target': 'current',
        }
