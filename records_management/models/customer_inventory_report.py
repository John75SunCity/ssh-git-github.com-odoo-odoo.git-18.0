from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
from dateutil.relativedelta import relativedelta
from datetime import timedelta


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
        # Storage Services
        ('store_box', 'Box Storage'),
        ('store_map', 'Map Box Storage'),
        ('store_pallet', 'Pallet Storage'),
        ('store_specialty', 'Specialty Box Storage'),
        
        # Product Sales
        ('sell_boxes', 'New Boxes (10 Pack) with Delivery'),
        
        # Box Management
        ('add_box', 'New Box Setup'),
        ('refile_box', 'Refile Box'),
        ('refile_file', 'Refile File/Folder'),
        ('permanent_removal', 'Permanent Removal of Box'),
        
        # Transportation & Delivery
        ('delivery', 'Delivery Service'),
        ('pickup', 'Pickup Service'),
        ('trip_charge', 'Trip Charge'),
        
        # Destruction Services
        ('shredding', 'Shredding per Box'),
        ('hard_drive_destruction', 'Hard Drive Destruction'),
        ('uniform_destruction', 'Uniform Destruction'),
        
        # Retrieval Services - Regular
        ('retrieval_box_regular', 'Regular Retrieval - Box'),
        ('retrieval_file_regular', 'Regular Retrieval - File'),
        
        # Retrieval Services - Rush
        ('retrieval_box_rush', 'Rush Retrieval - Box (4hr)'),
        ('retrieval_file_rush', 'Rush Retrieval - File (4hr)'),
        ('rush_service_4hr', 'Rush Service 4HR'),
        
        # Retrieval Services - Emergency
        ('retrieval_box_emergency', 'Emergency Retrieval - Box (1hr)'),
        ('retrieval_file_emergency', 'Emergency Retrieval - File (1hr)'),
        ('emergency_service_1hr', 'Emergency Service 1HR'),
        ('same_day_service', 'Same Day Service'),
        
        # Shred Bin Services
        ('shred_bin_32', '32 Gallon Bin Service'),
        ('shred_bin_64', '64 Gallon Bin Service'),
        ('shred_bin_96', '96 Gallon Bin Service'),
        ('shred_bin_console', 'Shred Console Service'),
        ('shred_bin_mobile_32', '32 Gallon Mobile Console'),
        ('shred_bin_mobile_64', '64 Gallon Mobile'),
        ('shred_bin_mobile_96', '96 Gallon Mobile'),
        ('shredinator_23', '23 Gallon Shredinator'),
        
        # Shred Box Services
        ('shred_box_standard', 'Shred Box - Standard Size'),
        ('shred_box_double', 'Shred Box - Double Size'),
        ('shred_box_large', 'Shred Box - Odd/Large'),
        
        # One-Time Services
        ('one_time_64g_bin', 'One Time 64G Bin Service'),
        ('one_time_96g_bin', 'One Time 96G Bin Service'),
        
        # Special Services
        ('labor', 'Labor'),
        ('indexing', 'Indexing per Box'),
        ('file_not_found', 'File Not Found'),
        ('unlock_bin', 'Unlock Shred Bin'),
        ('key_delivery', 'Key Delivery'),
        ('shred_a_thon', 'Shred-A-Thon'),
        ('damaged_bin', 'Damaged Property - Bin'),
        
        # Other
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


class RecordsBillingConfig(models.Model):
    _name = 'records.billing.config'
    _description = 'Billing Configuration for Records Management'
    _rec_name = 'name'

    name = fields.Char(string='Configuration Name', required=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)
    
    # Storage Pricing (Monthly Recurring)
    storage_rate_per_box = fields.Float(
        string='Box Storage Rate (Monthly)',
        default=0.32, digits=(12, 4),
        help="Monthly storage fee per standard box")
    map_box_storage_rate = fields.Float(
        string='Map Box Storage Rate (Monthly)',
        default=0.45, digits=(12, 4),
        help="Monthly storage fee per map box")
    pallet_storage_rate = fields.Float(
        string='Pallet Storage Rate (Monthly)', 
        default=2.50, digits=(12, 4),
        help="Monthly storage fee per pallet")
    specialty_box_storage_rate = fields.Float(
        string='Specialty Box Storage Rate (Monthly)',
        default=0.50, digits=(12, 4),
        help="Monthly storage fee per specialty box")
    monthly_minimum_fee = fields.Float(
        string='Monthly Minimum Storage Fee',
        default=45.00, digits=(12, 2),
        help="Minimum monthly storage charge")
    
    # Transportation & Delivery
    pickup_base_fee = fields.Float(
        string='Pickup Base Fee', default=25.00, digits=(12, 2))
    delivery_base_fee = fields.Float(
        string='Delivery Base Fee', default=25.00, digits=(12, 2))
    trip_charge = fields.Float(
        string='Trip Charge', default=15.00, digits=(12, 2))
    transportation_rate_per_mile = fields.Float(
        string='Transportation Rate per Mile', default=0.75, digits=(12, 2))
    
    # Box Management Services
    new_box_fee = fields.Float(
        string='New Box Setup Fee', default=2.50, digits=(12, 2))
    refile_box_fee = fields.Float(
        string='Refile Box Fee', default=3.00, digits=(12, 2))
    refile_filefolder_fee = fields.Float(
        string='Refile File/Folder Fee', default=1.50, digits=(12, 2))
    permanent_removal_fee = fields.Float(
        string='Permanent Removal Fee', default=2.00, digits=(12, 2))
    
    # Destruction Services
    shredding_per_box_fee = fields.Float(
        string='Shredding per Box Fee', default=3.50, digits=(12, 2))
    hard_drive_destruction_fee = fields.Float(
        string='Hard Drive Destruction Fee', default=15.00, digits=(12, 2))
    uniform_destruction_fee = fields.Float(
        string='Uniform Destruction Fee', default=25.00, digits=(12, 2))
    
    # Retrieval Services - Regular
    regular_retrieval_box_fee = fields.Float(
        string='Regular Retrieval - Box', default=8.50, digits=(12, 2))
    regular_retrieval_file_fee = fields.Float(
        string='Regular Retrieval - File', default=3.50, digits=(12, 2))
    
    # Retrieval Services - Rush (4 hour)
    rush_retrieval_box_fee = fields.Float(
        string='Rush Retrieval - Box (4hr)', default=15.00, digits=(12, 2))
    rush_retrieval_file_fee = fields.Float(
        string='Rush Retrieval - File (4hr)', default=8.50, digits=(12, 2))
    rush_service_4hr_fee = fields.Float(
        string='Rush Service 4HR Fee', default=25.00, digits=(12, 2))
    
    # Retrieval Services - Emergency (1 hour)
    emergency_retrieval_box_fee = fields.Float(
        string='Emergency Retrieval - Box (1hr)', default=25.00, digits=(12, 2))
    emergency_retrieval_file_fee = fields.Float(
        string='Emergency Retrieval - File (1hr)', default=15.00, digits=(12, 2))
    emergency_service_1hr_fee = fields.Float(
        string='Emergency Service 1HR Fee', default=50.00, digits=(12, 2))
    same_day_service_fee = fields.Float(
        string='Same Day Service Fee', default=35.00, digits=(12, 2))
    
    # Shred Bin Services - Container Sizes
    shred_bin_32_gallon_fee = fields.Float(
        string='32 Gallon Bin Service', default=25.00, digits=(12, 2))
    shred_bin_64_gallon_fee = fields.Float(
        string='64 Gallon Bin Service', default=35.00, digits=(12, 2))
    shred_bin_96_gallon_fee = fields.Float(
        string='96 Gallon Bin Service', default=45.00, digits=(12, 2))
    shred_bin_console_fee = fields.Float(
        string='Shred Console Service', default=30.00, digits=(12, 2))
    shred_bin_mobile_fee = fields.Float(
        string='Mobile Bin Service', default=40.00, digits=(12, 2))
    shredinator_23_gallon_fee = fields.Float(
        string='23 Gallon Shredinator', default=20.00, digits=(12, 2))
    
    # Shred Box Services
    shred_box_standard_fee = fields.Float(
        string='Shred Box - Standard Size', default=15.00, digits=(12, 2))
    shred_box_double_fee = fields.Float(
        string='Shred Box - Double Size', default=25.00, digits=(12, 2))
    shred_box_large_fee = fields.Float(
        string='Shred Box - Odd/Large', default=35.00, digits=(12, 2))
    
    # One-Time Bin Services
    one_time_64g_bin_fee = fields.Float(
        string='One Time 64G Bin Service', default=45.00, digits=(12, 2))
    one_time_96g_bin_fee = fields.Float(
        string='One Time 96G Bin Service', default=55.00, digits=(12, 2))
    
    # Special Services
    labor_hourly_rate = fields.Float(
        string='Labor Hourly Rate', default=35.00, digits=(12, 2))
    indexing_per_box_fee = fields.Float(
        string='Indexing per Box Fee', default=12.50, digits=(12, 2))
    file_not_found_fee = fields.Float(
        string='File Not Found Fee', default=5.00, digits=(12, 2))
    unlock_shred_bin_fee = fields.Float(
        string='Unlock Shred Bin Fee', default=15.00, digits=(12, 2))
    key_delivery_fee = fields.Float(
        string='Key Delivery Fee', default=10.00, digits=(12, 2))
    shred_a_thon_fee = fields.Float(
        string='Shred-A-Thon Fee', default=250.00, digits=(12, 2))
    damaged_property_bin_fee = fields.Float(
        string='Damaged Property - Bin Fee', default=75.00, digits=(12, 2))
    
    # Product Sales
    file_box_10_pack_price = fields.Float(
        string='File Box 10-Pack Price (with delivery)', default=45.00, digits=(12, 2))
    
    active = fields.Boolean(string='Active', default=True)


class RecordsBillingPeriod(models.Model):
    _name = 'records.billing.period'
    _description = 'Monthly Billing Period'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _order = 'period_start desc'

    name = fields.Char(string='Period Name', required=True)
    period_start = fields.Date(string='Period Start', required=True)
    period_end = fields.Date(string='Period End', required=True)
    
    # Status
    state = fields.Selection([
        ('draft', 'Draft'),
        ('calculating', 'Calculating'),
        ('ready', 'Ready for Review'),
        ('approved', 'Approved'),
        ('invoiced', 'Invoiced'),
        ('closed', 'Closed')
    ], string='Status', default='draft', tracking=True)
    
    # Billing Lines
    billing_line_ids = fields.One2many(
        'records.billing.line', 'billing_period_id',
        string='Billing Lines')
    
    # Totals
    total_storage_boxes = fields.Integer(
        string='Total Storage Boxes', compute='_compute_totals', store=True)
    total_storage_amount = fields.Float(
        string='Total Storage Amount', compute='_compute_totals', store=True)
    total_services_amount = fields.Float(
        string='Total Services Amount', compute='_compute_totals', store=True)
    total_products_amount = fields.Float(
        string='Total Products Amount', compute='_compute_totals', store=True)
    total_amount = fields.Float(
        string='Total Amount', compute='_compute_totals', store=True)
    
    # Invoice Integration
    invoice_ids = fields.One2many(
        'account.move', 'billing_period_id', string='Generated Invoices')
    invoice_count = fields.Integer(
        string='Invoice Count', compute='_compute_invoice_count')
    
    @api.depends('billing_line_ids', 'billing_line_ids.amount')
    def _compute_totals(self):
        for period in self:
            storage_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'storage')
            service_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'service')
            product_lines = period.billing_line_ids.filtered(
                lambda line: line.line_type == 'product')
            
            period.total_storage_boxes = sum(storage_lines.mapped('quantity'))
            period.total_storage_amount = sum(storage_lines.mapped('amount'))
            period.total_services_amount = sum(service_lines.mapped('amount'))
            period.total_products_amount = sum(product_lines.mapped('amount'))
            period.total_amount = (period.total_storage_amount + 
                                   period.total_services_amount + 
                                   period.total_products_amount)
    
    @api.depends('invoice_ids')
    def _compute_invoice_count(self):
        for period in self:
            period.invoice_count = len(period.invoice_ids)
    
    def action_calculate_billing(self):
        """Calculate billing for all customers for this period"""
        self.ensure_one()
        self.state = 'calculating'
        
        # Clear existing billing lines
        self.billing_line_ids.unlink()
        
        billing_config = self.env['records.billing.config'].search([
            ('active', '=', True)
        ], limit=1)
        
        if not billing_config:
            raise ValidationError("No active billing configuration found.")
        
        # Get all customers with boxes during this period
        customers_with_boxes = self.env['records.box'].search([
            ('customer_id', '!=', False),
            ('state', '!=', 'destroyed')
        ]).mapped('customer_id')
        
        for customer in customers_with_boxes:
            self._calculate_customer_billing(customer, billing_config)
        
        # Calculate service billing
        self._calculate_service_billing(billing_config)
        
        self.state = 'ready'
    
    def _calculate_customer_billing(self, customer, config):
        """Calculate storage billing for a specific customer"""
        # Count different types of storage containers for this customer
        boxes = self.env['records.box'].search([
            ('customer_id', '=', customer.id),
            ('state', '!=', 'destroyed'),
        ])
        
        # Group boxes by department for department-level billing
        departments = boxes.mapped('department_id')
        if not departments:
            # Customer has no departments, bill at company level
            self._calculate_company_level_billing(customer, boxes, config)
        else:
            # Customer has departments, calculate billing per department
            self._calculate_department_level_billing(customer, departments, config)
    
    def _calculate_company_level_billing(self, customer, boxes, config):
        """Calculate billing for company without departments"""
        # Group boxes by storage type (you may need to add storage_type field to records.box)
        storage_types = {
            'standard': boxes.filtered(lambda b: not hasattr(b, 'storage_type') or b.storage_type == 'standard'),
            'map': boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'map'),
            'specialty': boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'specialty'),
        }
        
        # Count pallets (you may need to add pallet tracking)
        pallet_count = 0  # TODO: Implement pallet counting logic
        
        total_storage_cost = 0.0
        billing_lines = []
        
        # Calculate storage for each type
        for storage_type, box_list in storage_types.items():
            if not box_list:
                continue
                
            box_count = len(box_list)
            if storage_type == 'standard':
                rate = config.storage_rate_per_box
                description = f'Storage for {box_count} standard boxes'
            elif storage_type == 'map':
                rate = config.map_box_storage_rate
                description = f'Storage for {box_count} map boxes'
            elif storage_type == 'specialty':
                rate = config.specialty_box_storage_rate
                description = f'Storage for {box_count} specialty boxes'
            
            storage_amount = box_count * rate
            total_storage_cost += storage_amount
            
            # Create billing line for this storage type
            billing_lines.append({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': description,
                'quantity': box_count,
                'unit_price': rate,
                'amount': storage_amount,
            })
        
        # Add pallet storage if any
        if pallet_count > 0:
            pallet_amount = pallet_count * config.pallet_storage_rate
            total_storage_cost += pallet_amount
            billing_lines.append({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': f'Pallet storage for {pallet_count} pallets',
                'quantity': pallet_count,
                'unit_price': config.pallet_storage_rate,
                'amount': pallet_amount,
            })
        
        # Create all storage billing lines
        for line_data in billing_lines:
            self.env['records.billing.line'].create(line_data)
        
        # Check if monthly minimum applies
        if total_storage_cost > 0 and total_storage_cost < config.monthly_minimum_fee:
            minimum_adjustment = config.monthly_minimum_fee - total_storage_cost
            self.env['records.billing.line'].create({
                'billing_period_id': self.id,
                'customer_id': customer.id,
                'line_type': 'storage',
                'description': 'Monthly Storage Minimum Fee',
                'quantity': 1,
                'unit_price': minimum_adjustment,
                'amount': minimum_adjustment,
            })
            
        return True
    
    def _calculate_department_level_billing(self, customer, departments, config):
        """Calculate billing broken down by department"""
        customer_total = 0.0
        department_totals = {}
        
        for department in departments:
            dept_boxes = self.env['records.box'].search([
                ('customer_id', '=', customer.id),
                ('department_id', '=', department.id),
                ('state', '!=', 'destroyed'),
            ])
            
            # Group boxes by storage type for this department
            storage_types = {
                'standard': dept_boxes.filtered(lambda b: not hasattr(b, 'storage_type') or b.storage_type == 'standard'),
                'map': dept_boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'map'),
                'specialty': dept_boxes.filtered(lambda b: hasattr(b, 'storage_type') and b.storage_type == 'specialty'),
            }
            
            dept_total = 0.0
            
            # Calculate storage for each type in this department
            for storage_type, box_list in storage_types.items():
                if not box_list:
                    continue
                    
                box_count = len(box_list)
                if storage_type == 'standard':
                    rate = config.storage_rate_per_box
                    description = f'{department.name} - Storage for {box_count} standard boxes'
                elif storage_type == 'map':
                    rate = config.map_box_storage_rate
                    description = f'{department.name} - Storage for {box_count} map boxes'
                elif storage_type == 'specialty':
                    rate = config.specialty_box_storage_rate
                    description = f'{department.name} - Storage for {box_count} specialty boxes'
                
                storage_amount = box_count * rate
                dept_total += storage_amount
                
                # Create billing line for this department's storage
                self.env['records.billing.line'].create({
                    'billing_period_id': self.id,
                    'customer_id': customer.id,
                    'department_id': department.id,
                    'line_type': 'storage',
                    'description': description,
                    'quantity': box_count,
                    'unit_price': rate,
                    'amount': storage_amount,
                })
            
            department_totals[department.id] = dept_total
            customer_total += dept_total
        
        # Handle minimum fee logic - check customer's billing preference
        billing_preference = customer.billing_preference or 'consolidated'
        minimum_fee_per_dept = customer.minimum_fee_per_department or False
        
        if minimum_fee_per_dept:
            # Apply minimum fee per department
            for department in departments:
                dept_total = department_totals.get(department.id, 0.0)
                if dept_total > 0 and dept_total < config.monthly_minimum_fee:
                    minimum_adjustment = config.monthly_minimum_fee - dept_total
                    self.env['records.billing.line'].create({
                        'billing_period_id': self.id,
                        'customer_id': customer.id,
                        'department_id': department.id,
                        'line_type': 'storage',
                        'description': f'{department.name} - Monthly Storage Minimum Fee',
                        'quantity': 1,
                        'unit_price': minimum_adjustment,
                        'amount': minimum_adjustment,
                    })
        else:
            # Apply minimum fee at company level, distribute proportionally
            if customer_total > 0 and customer_total < config.monthly_minimum_fee:
                minimum_adjustment = config.monthly_minimum_fee - customer_total
                
                # Distribute minimum fee proportionally across departments
                for department in departments:
                    dept_total = department_totals.get(department.id, 0.0)
                    if dept_total > 0:
                        dept_proportion = dept_total / customer_total
                        dept_minimum = minimum_adjustment * dept_proportion
                        
                        self.env['records.billing.line'].create({
                            'billing_period_id': self.id,
                            'customer_id': customer.id,
                            'department_id': department.id,
                            'line_type': 'storage',
                            'description': f'{department.name} - Monthly Minimum Fee (Proportional)',
                            'quantity': 1,
                            'unit_price': dept_minimum,
                            'amount': dept_minimum,
                        })
        
        return True
    
    def _calculate_service_billing(self, config):
        """Calculate billing for services completed during this period"""
        # Get completed service requests during this period
        service_requests = self.env['records.service.request'].search([
            ('state', '=', 'completed'),
            ('completion_date', '>=', self.period_start),
            ('completion_date', '<=', self.period_end),
        ])
        
        for service in service_requests:
            if service.actual_cost > 0:
                self.env['records.billing.line'].create({
                    'billing_period_id': self.id,
                    'customer_id': service.customer_id.id,
                    'service_request_id': service.id,
                    'line_type': 'service',
                    'description': service.name,
                    'quantity': 1,
                    'unit_price': service.actual_cost,
                    'amount': service.actual_cost,
                })
    
    def action_generate_invoices(self):
        """Generate invoices based on customer billing preferences"""
        if self.state != 'approved':
            raise UserError("Only approved billing periods can generate invoices")
        
        # Get all customers with billing lines
        customers = self.billing_line_ids.mapped('customer_id')
        
        for customer in customers:
            self._generate_customer_invoices(customer)
        
        self.state = 'invoiced'
        return True
    
    def _generate_customer_invoices(self, customer):
        """Generate invoices for a customer based on their billing preference"""
        billing_preference = customer.billing_preference or 'consolidated'
        customer_lines = self.billing_line_ids.filtered(
            lambda l: l.customer_id.id == customer.id)
        
        if billing_preference == 'consolidated':
            self._generate_consolidated_invoice(customer, customer_lines)
        elif billing_preference == 'separate':
            self._generate_separate_invoices(customer, customer_lines)
        elif billing_preference == 'hybrid':
            self._generate_hybrid_invoices(customer, customer_lines)
    
    def _generate_consolidated_invoice(self, customer, billing_lines):
        """Generate one invoice with department breakdown"""
        if not billing_lines:
            return
        
        # Create invoice header
        invoice_vals = {
            'partner_id': customer.id,
            'move_type': 'out_invoice',
            'invoice_date': self.period_end,
            'billing_period_id': self.id,
            'narration': f'Records Management Services for {self.name}',
        }
        
        invoice = self.env['account.move'].create(invoice_vals)
        
        # Group lines by department for better organization
        departments = billing_lines.mapped('department_id')
        
        if departments:
            # Customer has departments - group by department
            for department in departments:
                dept_lines = billing_lines.filtered(
                    lambda l: l.department_id.id == department.id)
                if dept_lines:
                    self._add_department_section_to_invoice(
                        invoice, department, dept_lines)
            
            # Add lines without department (company-level charges)
            company_lines = billing_lines.filtered(lambda l: not l.department_id)
            if company_lines:
                self._add_department_section_to_invoice(
                    invoice, None, company_lines)
        else:
            # Customer has no departments - add all lines directly
            self._add_billing_lines_to_invoice(invoice, billing_lines)
        
        # Finalize the invoice
        invoice.action_post()
        return invoice
    
    def _generate_separate_invoices(self, customer, billing_lines):
        """Generate separate invoices per department"""
        departments = billing_lines.mapped('department_id')
        invoices = []
        
        for department in departments:
            dept_lines = billing_lines.filtered(
                lambda l: l.department_id.id == department.id)
            if not dept_lines:
                continue
            
            # Get department billing contact if configured
            dept_billing = customer.department_billing_contact_ids.filtered(
                lambda dbc: dbc.department_id.id == department.id)
            
            billing_partner = (dept_billing.billing_contact_id.id 
                             if dept_billing else customer.id)
            
            # Create separate invoice for this department
            invoice_vals = {
                'partner_id': billing_partner,
                'move_type': 'out_invoice',
                'invoice_date': self.period_end,
                'billing_period_id': self.id,
                'narration': f'Records Management Services for '
                           f'{department.name} - {self.name}',
            }
            
            # Add PO number if configured
            if dept_billing and dept_billing.default_po_number:
                invoice_vals['ref'] = dept_billing.default_po_number
            
            invoice = self.env['account.move'].create(invoice_vals)
            self._add_billing_lines_to_invoice(invoice, dept_lines)
            invoice.action_post()
            invoices.append(invoice)
        
        # Handle company-level charges (lines without department)
        company_lines = billing_lines.filtered(lambda l: not l.department_id)
        if company_lines:
            invoice_vals = {
                'partner_id': customer.id,
                'move_type': 'out_invoice',
                'invoice_date': self.period_end,
                'billing_period_id': self.id,
                'narration': f'Records Management Services (Company) - '
                           f'{self.name}',
            }
            
            invoice = self.env['account.move'].create(invoice_vals)
            self._add_billing_lines_to_invoice(invoice, company_lines)
            invoice.action_post()
            invoices.append(invoice)
        
        return invoices
    
    def _generate_hybrid_invoices(self, customer, billing_lines):
        """Generate consolidated storage, separate service invoices"""
        storage_lines = billing_lines.filtered(
            lambda l: l.line_type == 'storage')
        service_lines = billing_lines.filtered(
            lambda l: l.line_type in ['service', 'product'])
        
        invoices = []
        
        # Consolidated storage invoice
        if storage_lines:
            invoices.append(
                self._generate_consolidated_invoice(customer, storage_lines))
        
        # Separate service invoices by department
        if service_lines:
            invoices.extend(
                self._generate_separate_invoices(customer, service_lines))
        
        return invoices
    
    def _add_department_section_to_invoice(self, invoice, department, lines):
        """Add a department section with subtotal to invoice"""
        if department:
            # Add department header as a display line
            self.env['account.move.line'].create({
                'move_id': invoice.id,
                'name': f'\n=== {department.name} ===',
                'display_type': 'line_section',
            })
        
        # Add the actual billing lines
        self._add_billing_lines_to_invoice(invoice, lines)
        
        # Add department subtotal if there are multiple departments
        if department and len(lines.mapped('department_id')) > 1:
            dept_total = sum(lines.mapped('amount'))
            self.env['account.move.line'].create({
                'move_id': invoice.id,
                'name': f'{department.name} Subtotal: ${dept_total:,.2f}',
                'display_type': 'line_note',
            })
    
    def _add_billing_lines_to_invoice(self, invoice, billing_lines):
        """Add billing lines to invoice as invoice lines"""
        # Get default product and account (you may need to configure these)
        default_product = self.env['product.product'].search([
            ('name', '=', 'Records Management Services')], limit=1)
        
        if not default_product:
            # Create default product if it doesn't exist
            default_product = self.env['product.product'].create({
                'name': 'Records Management Services',
                'type': 'service',
                'categ_id': self.env.ref('product.product_category_all').id,
            })
        
        for line in billing_lines:
            invoice_line_vals = {
                'move_id': invoice.id,
                'product_id': default_product.id,
                'name': line.description,
                'quantity': line.quantity,
                'price_unit': line.unit_price,
                'account_id': default_product.property_account_income_id.id or
                            default_product.categ_id.property_account_income_categ_id.id,
            }
            
            self.env['account.move.line'].create(invoice_line_vals)
        

class RecordsBillingLine(models.Model):
    _name = 'records.billing.line'
    _description = 'Billing Line Item'
    _rec_name = 'description'

    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period', 
        required=True, ondelete='cascade')
    customer_id = fields.Many2one(
        'res.partner', string='Customer', required=True)
    department_id = fields.Many2one(
        'records.department', string='Department')
    service_request_id = fields.Many2one(
        'records.service.request', string='Service Request')
    
    line_type = fields.Selection([
        ('storage', 'Storage Fee'),
        ('service', 'Service Fee'),
        ('product', 'Product Sale'),
        ('adjustment', 'Adjustment')
    ], string='Line Type', required=True)
    
    description = fields.Text(string='Description', required=True)
    quantity = fields.Float(string='Quantity', default=1.0, digits=(12, 2))
    unit_price = fields.Float(string='Unit Price', digits=(12, 4))
    amount = fields.Float(
        string='Amount', compute='_compute_amount', store=True, 
        digits=(12, 2))
    
    # Additional Information
    notes = fields.Text(string='Notes')
    
    @api.depends('quantity', 'unit_price')
    def _compute_amount(self):
        for line in self:
            line.amount = line.quantity * line.unit_price


class RecordsServicePricing(models.Model):
    _name = 'records.service.pricing'
    _description = 'Comprehensive Service Pricing Configuration'
    _rec_name = 'name'

    name = fields.Char(string='Service Name', required=True)
    service_code = fields.Char(string='Service Code', required=True)
    action_code = fields.Char(string='Action Code', help="STORE, SELL, ADD, etc.")
    object_code = fields.Char(string='Object Code', help="01, BX, CONTAINER, etc.")
    
    service_category = fields.Selection([
        ('storage', 'Storage Services'),
        ('product', 'Product Sales'),
        ('box_management', 'Box Management'),
        ('transportation', 'Transportation & Delivery'),
        ('destruction', 'Destruction Services'),
        ('retrieval', 'Retrieval Services'),
        ('shred_bin', 'Shred Bin Services'),
        ('special', 'Special Services')
    ], string='Service Category', required=True)
    
    # Pricing
    base_price = fields.Float(string='Base Price', digits=(12, 2))
    per_unit_price = fields.Float(
        string='Per Unit Price', digits=(12, 4),
        help="Additional cost per unit/box/mile etc.")
    minimum_charge = fields.Float(
        string='Minimum Charge', digits=(12, 2))
    
    # Billing Type
    billing_type = fields.Selection([
        ('invoice', 'Direct Invoice'),
        ('workorder', 'Workorder Required'),
        ('recurring', 'Recurring Monthly')
    ], string='Billing Type', default='invoice')
    
    requires_approval = fields.Boolean(string='Requires Approval', default=False)
    accumulate = fields.Boolean(string='Accumulate Charges', default=False)
    
    # Quantity Breaks
    quantity_breaks = fields.One2many(
        'records.service.pricing.break', 'pricing_id', 
        string='Quantity Breaks')
    
    active = fields.Boolean(string='Active', default=True)
    company_id = fields.Many2one(
        'res.company', string='Company',
        default=lambda self: self.env.company)


class RecordsServicePricingBreak(models.Model):
    _name = 'records.service.pricing.break'
    _description = 'Service Pricing Quantity Breaks'
    _rec_name = 'min_quantity'

    pricing_id = fields.Many2one(
        'records.service.pricing', string='Pricing', 
        required=True, ondelete='cascade')
    min_quantity = fields.Float(string='Minimum Quantity', required=True)
    max_quantity = fields.Float(string='Maximum Quantity')
    unit_price = fields.Float(string='Unit Price', digits=(12, 4))
    discount_percent = fields.Float(string='Discount %', digits=(5, 2))


# Add billing period reference to account.move (invoices)
class AccountMove(models.Model):
    _inherit = 'account.move'
    
    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period',
        help="The billing period this invoice was generated from")


# Enhanced the existing RecordsServiceRequest model
class RecordsServiceRequestEnhanced(models.Model):
    _inherit = 'records.service.request'

    # Enhanced pricing fields
    actual_cost = fields.Float(
        string='Actual Cost', digits=(12, 2),
        help="Final billed amount for this service")
    cost_breakdown = fields.Text(
        string='Cost Breakdown',
        help="Detailed breakdown of how the cost was calculated")
    
    # Billing integration
    billing_period_id = fields.Many2one(
        'records.billing.period', string='Billing Period')
    billing_line_id = fields.Many2one(
        'records.billing.line', string='Billing Line')
    invoiced = fields.Boolean(string='Invoiced', default=False)
    completion_date = fields.Datetime(string='Completion Date')
    
    # Additional service details for pricing
    distance_miles = fields.Float(
        string='Distance (Miles)', digits=(8, 2),
        help="Distance for transportation cost calculation")
    boxes_count = fields.Integer(
        string='Number of Boxes', default=1)
    hard_drives_count = fields.Integer(
        string='Number of Hard Drives', default=0)