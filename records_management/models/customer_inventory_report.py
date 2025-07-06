from odoo import models, fields, api
from dateutil.relativedelta import relativedelta


class CustomerInventoryReport(models.Model):
    _name = 'customer.inventory.report'
    _description = 'Customer Inventory Report'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'report_date desc, customer_id'

    name = fields.Char(string='Report Name', required=True)
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain=[('is_company', '=', True)])
    report_date = fields.Date(
        string='Report Date', default=fields.Date.today, required=True)
    
    # Inventory Summary Fields
    total_boxes = fields.Integer(
        string='Total Boxes', compute='_compute_inventory_totals', store=True)
    total_documents = fields.Integer(
        string='Total Documents', compute='_compute_inventory_totals',
        store=True)
    active_locations = fields.Integer(
        string='Active Locations', compute='_compute_inventory_totals',
        store=True)
    
    # Related Records
    box_ids = fields.One2many(
        'records.box', 'customer_id', string='Customer Boxes', readonly=True)
    document_ids = fields.One2many(
        'records.document', 'customer_id', string='Customer Documents',
        readonly=True)
    
    # Status and Notes
    status = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('sent', 'Sent to Customer')
    ], default='draft', string='Status')
    notes = fields.Text(string='Notes')
    
    @api.depends('customer_id')
    def _compute_inventory_totals(self):
        for record in self:
            if record.customer_id:
                # Count active boxes for this customer
                record.total_boxes = self.env['records.box'].search_count([
                    ('customer_id', '=', record.customer_id.id),
                    ('state', '!=', 'destroyed')
                ])
                
                # Count documents for this customer
                document_count = self.env['records.document'].search_count([
                    ('customer_id', '=', record.customer_id.id)
                ])
                record.total_documents = document_count
                
                # Count unique locations used by this customer
                locations = self.env['records.box'].search([
                    ('customer_id', '=', record.customer_id.id),
                    ('state', '!=', 'destroyed')
                ]).mapped('location_id')
                record.active_locations = len(locations)
            else:
                record.total_boxes = 0
                record.total_documents = 0
                record.active_locations = 0
    
    def action_confirm_report(self):
        """Confirm the inventory report"""
        self.status = 'confirmed'
    
    def action_send_to_customer(self):
        """Mark report as sent to customer"""
        self.status = 'sent'
    
    @api.model
    def generate_monthly_reports(self):
        """Generate monthly inventory reports for all customers"""
        customers_with_boxes = self.env['records.box'].search([
            ('state', '!=', 'destroyed')
        ]).mapped('customer_id')
        
        today = fields.Date.today()
        report_name = f"Monthly Inventory Report - {today.strftime('%B %Y')}"
        
        for customer in customers_with_boxes:
            # Check if report already exists for this month
            existing_report = self.search([
                ('customer_id', '=', customer.id),
                ('report_date', '>=', today.replace(day=1)),
                ('report_date', '<', (today.replace(day=1) +
                                      relativedelta(months=1)))
            ])
            
            if not existing_report:
                # Create new monthly report
                self.create({
                    'name': f"{report_name} - {customer.name}",
                    'customer_id': customer.id,
                    'report_date': today,
                    'status': 'draft',
                })
        
        return True
    
    def action_generate_pdf_report(self):
        """Generate PDF report for customer inventory"""
        report_ref = 'records_management.action_customer_inventory_report_pdf'
        return self.env.ref(report_ref).report_action(self)


class RecordsDepartment(models.Model):
    _name = 'records.department'
    _description = 'Customer Department'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'company_id, name'

    name = fields.Char(string='Department Name', required=True, tracking=True)
    code = fields.Char(string='Department Code', size=10)
    company_id = fields.Many2one(
        'res.partner', string='Company', required=True,
        domain=[('is_company', '=', True)], tracking=True)
    
    # Department Admin
    admin_id = fields.Many2one(
        'res.partner', string='Department Admin',
        domain="[('parent_id', '=', company_id), ('is_company', '=', False)]")
    
    # Statistics
    total_boxes = fields.Integer(
        string='Total Boxes', compute='_compute_department_stats', store=True)
    total_documents = fields.Integer(
        string='Total Documents', compute='_compute_department_stats', 
        store=True)
    monthly_cost = fields.Float(
        string='Monthly Cost', compute='_compute_department_stats', store=True)
    
    # Users and Access
    user_ids = fields.One2many(
        'records.department.user', 'department_id', string='Department Users')
    active_users_count = fields.Integer(
        string='Active Users', compute='_compute_user_stats')
    
    # Related Records
    box_ids = fields.One2many(
        'records.box', 'department_id', string='Department Boxes')
    document_ids = fields.One2many(
        'records.document', 'department_id', string='Department Documents')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    
    @api.depends('box_ids', 'box_ids.state', 'document_ids')
    def _compute_department_stats(self):
        for dept in self:
            # Count active boxes
            dept.total_boxes = len(dept.box_ids.filtered(
                lambda x: x.state != 'destroyed'))
            
            # Count documents
            dept.total_documents = len(dept.document_ids)
            
            # Calculate monthly storage cost (placeholder - adjust pricing)
            dept.monthly_cost = dept.total_boxes * 15.0  # $15 per box/month
    
    @api.depends('user_ids', 'user_ids.active')
    def _compute_user_stats(self):
        for dept in self:
            dept.active_users_count = len(dept.user_ids.filtered('active'))
    
    def action_invite_user(self):
        """Open wizard to invite new user to department"""
        return {
            'type': 'ir.actions.act_window',
            'name': 'Invite User to Department',
            'res_model': 'records.user.invitation.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_department_id': self.id}
        }


class RecordsDepartmentUser(models.Model):
    _name = 'records.department.user'
    _description = 'Department User Access'
    _rec_name = 'user_id'

    department_id = fields.Many2one(
        'records.department', string='Department', required=True, 
        ondelete='cascade')
    user_id = fields.Many2one(
        'res.partner', string='User', required=True,
        domain="[('is_company', '=', False)]")
    email = fields.Char(related='user_id.email', readonly=True)
    
    # Access Levels
    access_level = fields.Selection([
        ('viewer', 'Viewer - View Only + Basic Services'),
        ('user', 'User - View + Add/Edit + Request Services'),
        ('dept_admin', 'Department Admin - Full Department Access'),
        ('company_admin', 'Company Admin - Full Company Access')
    ], string='Access Level', required=True, default='viewer')
    
    # Permissions
    can_view_inventory = fields.Boolean(string='View Inventory', default=True)
    can_add_boxes = fields.Boolean(string='Add Boxes/Documents')
    can_request_services = fields.Boolean(string='Request Services',
                                          default=True)
    can_request_deletion = fields.Boolean(string='Request Deletion')
    can_approve_deletion = fields.Boolean(string='Approve Deletion')
    can_view_billing = fields.Boolean(string='View Department Billing')
    
    # Status
    active = fields.Boolean(string='Active', default=True)
    invited_date = fields.Datetime(string='Invited Date',
                                   default=fields.Datetime.now)
    last_login = fields.Datetime(string='Last Login')
    
    @api.onchange('access_level')
    def _onchange_access_level(self):
        """Set permissions based on access level"""
        if self.access_level == 'viewer':
            self.can_view_inventory = True
            self.can_add_boxes = False
            self.can_request_services = True  # Basic services only
            self.can_request_deletion = False
            self.can_approve_deletion = False
            self.can_view_billing = False
        elif self.access_level == 'user':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = False
            self.can_view_billing = False
        elif self.access_level == 'dept_admin':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = True  # Can approve for department
            self.can_view_billing = True  # Department billing only
        elif self.access_level == 'company_admin':
            self.can_view_inventory = True
            self.can_add_boxes = True
            self.can_request_services = True
            self.can_request_deletion = True
            self.can_approve_deletion = True  # Can approve for company
            self.can_view_billing = True  # Full company billing


class RecordsUserInvitationWizard(models.TransientModel):
    _name = 'records.user.invitation.wizard'
    _description = 'User Invitation Wizard'

    department_id = fields.Many2one(
        'records.department', string='Department', required=True)
    
    # User Information
    name = fields.Char(string='Full Name', required=True)
    email = fields.Char(string='Email', required=True)
    phone = fields.Char(string='Phone')
    job_title = fields.Char(string='Job Title')
    
    # Access Level
    access_level = fields.Selection([
        ('viewer', 'Viewer - View Only'),
        ('user', 'User - View + Request Services'),
        ('admin', 'Admin - Full Department Access')
    ], string='Access Level', required=True, default='viewer')
    
    # Message
    invitation_message = fields.Text(
        string='Invitation Message',
        default="You have been invited to access our Records Management "
                "portal.")
    
    def action_send_invitation(self):
        """Send invitation email and create user"""
        # Create or find the user
        user = self.env['res.partner'].search([
            ('email', '=', self.email),
            ('parent_id', '=', self.department_id.company_id.id)
        ], limit=1)
        
        if not user:
            user = self.env['res.partner'].create({
                'name': self.name,
                'email': self.email,
                'phone': self.phone,
                'function': self.job_title,
                'parent_id': self.department_id.company_id.id,
                'is_company': False,
                'customer_rank': 1,
            })
        
        # Create department user record
        self.env['records.department.user'].create({
            'department_id': self.department_id.id,
            'user_id': user.id,
            'access_level': self.access_level,
        })
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': f'Invitation sent to {self.email}',
                'type': 'success',
                'sticky': False,
            }
        }


class RecordsServiceRequest(models.Model):
    _name = 'records.service.request'
    _description = 'Service Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Request Reference', required=True, copy=False,
                       readonly=True, default=lambda self: 'New')
    
    # Request Details
    service_type = fields.Selection([
        ('pickup', 'Pickup New Files'),
        ('return', 'Return Boxes to Warehouse'),
        ('delivery', 'Deliver New File Boxes'),
        ('shredding', 'Shredding Service'),
        ('retrieval', 'Document Retrieval'),
        ('other', 'Other Service')
    ], string='Service Type', required=True, tracking=True)
    
    priority = fields.Selection([
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent')
    ], string='Priority', default='normal', tracking=True)
    
    # Customer/Department Info
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]", tracking=True)
    department_id = fields.Many2one(
        'records.department', string='Department', tracking=True)
    requested_by = fields.Many2one(
        'res.partner', string='Requested By', required=True, tracking=True)
    
    # Service Details
    description = fields.Html(string='Description', required=True)
    box_ids = fields.Many2many(
        'records.box', string='Related Boxes',
        help="Boxes related to this service request")
    quantity = fields.Integer(string='Quantity', default=1)
    special_instructions = fields.Text(string='Special Instructions')
    
    # Scheduling
    requested_date = fields.Datetime(
        string='Requested Date', default=fields.Datetime.now, tracking=True)
    scheduled_date = fields.Datetime(string='Scheduled Date', tracking=True)
    completed_date = fields.Datetime(string='Completed Date', tracking=True)
    
    # Status and Workflow
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('approved', 'Approved'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    
    # Costs and Billing
    estimated_cost = fields.Float(string='Estimated Cost')
    actual_cost = fields.Float(string='Actual Cost')
    billing_notes = fields.Text(string='Billing Notes')
    
    # Approval
    approved_by = fields.Many2one('res.partner', string='Approved By')
    approval_date = fields.Datetime(string='Approval Date')
    approval_notes = fields.Text(string='Approval Notes')
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'records.service.request') or 'New')
        return super().create(vals_list)
    
    def action_submit(self):
        """Submit service request for approval"""
        self.state = 'submitted'
    
    def action_approve(self):
        """Approve service request"""
        self.write({
            'state': 'approved',
            'approved_by': self.env.user.partner_id.id,
            'approval_date': fields.Datetime.now()
        })
    
    def action_schedule(self):
        """Schedule the service"""
        self.state = 'scheduled'
    
    def action_start(self):
        """Start service execution"""
        self.state = 'in_progress'
    
    def action_complete(self):
        """Mark service as completed"""
        self.write({
            'state': 'completed',
            'completed_date': fields.Datetime.now()
        })
    
    def action_cancel(self):
        """Cancel service request"""
        self.state = 'cancelled'


class RecordsDeletionRequest(models.Model):
    _name = 'records.deletion.request'
    _description = 'Deletion Request with Approval Workflow'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'create_date desc'

    name = fields.Char(string='Deletion Reference', required=True, copy=False,
                       readonly=True, default=lambda self: 'New')
    
    # Request Details
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]", tracking=True)
    department_id = fields.Many2one(
        'records.department', string='Department', required=True,
        tracking=True)
    requested_by = fields.Many2one(
        'res.partner', string='Requested By', required=True, tracking=True)
    
    # Items to Delete
    box_ids = fields.Many2many(
        'records.box', string='Boxes to Delete', required=True)
    document_ids = fields.Many2many(
        'records.document', string='Documents to Delete')
    
    # Justification and Details
    deletion_reason = fields.Selection([
        ('retention_expired', 'Retention Period Expired'),
        ('customer_request', 'Customer Request'),
        ('legal_requirement', 'Legal Requirement'),
        ('space_optimization', 'Space Optimization'),
        ('other', 'Other')
    ], string='Deletion Reason', required=True, tracking=True)
    justification = fields.Html(
        string='Justification', required=True,
        help="Detailed justification for the deletion request")
    
    # Approval Workflow - Requires BOTH department and company admin approval
    dept_admin_approval = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Department Admin Approval', default='pending', tracking=True)
    dept_admin_approved_by = fields.Many2one(
        'res.partner', string='Dept Admin Approved By')
    dept_admin_approval_date = fields.Datetime(
        string='Dept Admin Approval Date')
    dept_admin_signature = fields.Binary(string='Dept Admin Signature')
    dept_admin_notes = fields.Text(string='Department Admin Notes')
    
    company_admin_approval = fields.Selection([
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ], string='Company Admin Approval', default='pending', tracking=True)
    company_admin_approved_by = fields.Many2one(
        'res.partner', string='Company Admin Approved By')
    company_admin_approval_date = fields.Datetime(
        string='Company Admin Approval Date')
    company_admin_signature = fields.Binary(string='Company Admin Signature')
    company_admin_notes = fields.Text(string='Company Admin Notes')
    
    # Overall Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('submitted', 'Awaiting Approval'),
        ('dept_approved', 'Department Approved'),
        ('fully_approved', 'Fully Approved'),
        ('rejected', 'Rejected'),
        ('executed', 'Deletion Executed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True,
       compute='_compute_state', store=True)
    
    # Billing and Execution
    deletion_cost = fields.Float(string='Deletion Cost')
    billing_date = fields.Date(string='Billing Date')
    execution_date = fields.Date(string='Execution Date')
    executed_by = fields.Many2one('res.users', string='Executed By')
    execution_notes = fields.Text(string='Execution Notes')
    
    @api.depends('dept_admin_approval', 'company_admin_approval')
    def _compute_state(self):
        for record in self:
            if record.dept_admin_approval == 'rejected' or \
               record.company_admin_approval == 'rejected':
                record.state = 'rejected'
            elif (record.dept_admin_approval == 'approved' and 
                  record.company_admin_approval == 'approved'):
                if record.execution_date:
                    record.state = 'executed'
                else:
                    record.state = 'fully_approved'
            elif record.dept_admin_approval == 'approved':
                record.state = 'dept_approved'
            elif (record.dept_admin_approval == 'pending' and 
                  record.company_admin_approval == 'pending'):
                if record.name != 'New':
                    record.state = 'submitted'
                else:
                    record.state = 'draft'
    
    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'New') == 'New':
                vals['name'] = (
                    self.env['ir.sequence'].next_by_code(
                        'records.deletion.request') or 'New')
        return super().create(vals_list)
    
    def action_submit_for_approval(self):
        """Submit deletion request for approval"""
        self.state = 'submitted'
    
    def action_dept_admin_approve(self):
        """Department admin approves deletion"""
        self.write({
            'dept_admin_approval': 'approved',
            'dept_admin_approved_by': self.env.user.partner_id.id,
            'dept_admin_approval_date': fields.Datetime.now()
        })
    
    def action_dept_admin_reject(self):
        """Department admin rejects deletion"""
        self.dept_admin_approval = 'rejected'
    
    def action_company_admin_approve(self):
        """Company admin approves deletion"""
        self.write({
            'company_admin_approval': 'approved',
            'company_admin_approved_by': self.env.user.partner_id.id,
            'company_admin_approval_date': fields.Datetime.now()
        })
    
    def action_company_admin_reject(self):
        """Company admin rejects deletion"""
        self.company_admin_approval = 'rejected'
    
    def action_execute_deletion(self):
        """Execute the approved deletion and bill immediately"""
        if self.state != 'fully_approved':
            raise ValidationError(
                "Deletion can only be executed after full approval")
        
        # Mark boxes as destroyed
        self.box_ids.write({
            'state': 'destroyed',
            'destruction_date': fields.Date.today()
        })
        
        # Mark documents as destroyed
        self.document_ids.write({'state': 'destroyed'})
        
        # Update deletion record
        self.write({
            'execution_date': fields.Date.today(),
            'executed_by': self.env.user.id,
            'billing_date': fields.Date.today(),
            'state': 'executed'
        })
        
        # TODO: Trigger billing process here
        return True


class RecordsBulkUserImport(models.TransientModel):
    _name = 'records.bulk.user.import'
    _description = 'Bulk User Import Wizard'

    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True,
        domain="[('is_company', '=', True)]")
    department_id = fields.Many2one(
        'records.department', string='Department',
        help="Leave empty to assign users to company level")
    
    # CSV Upload
    csv_file = fields.Binary(string='CSV File', required=True)
    csv_filename = fields.Char(string='Filename')
    
    # Default Settings
    default_access_level = fields.Selection([
        ('viewer', 'Viewer - View Only + Basic Services'),
        ('user', 'User - View + Add/Edit + Request Services'),
        ('dept_admin', 'Department Admin - Full Department Access'),
        ('company_admin', 'Company Admin - Full Company Access')
    ], string='Default Access Level', default='viewer')
    
    # Preview and Results
    preview_data = fields.Text(string='Preview Data', readonly=True)
    import_results = fields.Text(string='Import Results', readonly=True)
    
    def action_preview_import(self):
        """Preview the CSV data before importing"""
        # TODO: Implement CSV parsing and preview
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'records.bulk.user.import',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
        }
    
    def action_import_users(self):
        """Import users from CSV file"""
        # TODO: Implement actual CSV import logic
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': 'Users imported successfully',
                'type': 'success',
                'sticky': False,
            }
        }
