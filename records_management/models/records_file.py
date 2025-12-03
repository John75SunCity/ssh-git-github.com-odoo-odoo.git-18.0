from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class RecordsFile(models.Model):
    """
    File Folders within Records Containers.
    
    Business Context:
    - Containers hold file folders
    - File folders can be removed from containers for delivery to customer
    - Each file gets its own barcode and inventory tracking (stock.quant)
    - Files can contain individual documents
    
    Hierarchy:
    Container (BOX-12345)
      └─ File Folder (FILE-HR-2024-001) ← This model
          └─ Document (DOC-CONTRACT-JD-001)
    
    Odoo Integration:
    - quant_id: Links to stock.quant for inventory tracking
    - owner_id: Customer ownership (from quant)
    - location_id: Physical location (from quant)
    - parent_quant_id: Container it came from
    """
    
    _name = 'records.file'
    _description = 'Records File Folder'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'
    
    # ============================================================================
    # CORE IDENTIFICATION (Customer-Defined)
    # ============================================================================
    name = fields.Char(
        string="File Name/Number",
        required=True,
        tracking=True,
        help="Customer's name for this file folder. Examples:\n"
             "- Patient name: 'John Doe'\n"
             "- Case number: 'CASE-2024-001'\n"
             "- Department: 'HR Personnel Files'\n"
             "Customer uses their own naming/numbering system."
    )
    
    barcode = fields.Char(
        string="File Barcode",
        tracking=True,
        copy=False,
        index=True,
        help="Pre-printed barcode assigned to this file folder.\n"
             "Assigned when file is removed from container and needs independent tracking.\n"
             "Scanning this barcode displays: file name, location, customer, parent container, etc."
    )
    
    temp_barcode = fields.Char(
        string="Temporary Barcode",
        copy=False,
        index=True,
        help="Auto-generated temporary barcode for files without physical barcodes.\n"
             "Generated during Container Indexing Service workflow."
    )
    
    # ============================================================================
    # STOCK INTEGRATION (Hierarchical Inventory Tracking)
    # ============================================================================
    quant_id = fields.Many2one(
        'stock.quant',
        string="Inventory Quant",
        tracking=True,
        ondelete='restrict',
        help="Links this file to Odoo's stock system for movement tracking, "
             "barcode scanning, and location management"
    )
    
    package_id = fields.Many2one(
        'stock.quant.package',
        string="Stock Package",
        readonly=True,
        help="Auto-created package for Stock Barcode app compatibility."
    )
    
    owner_id = fields.Many2one(
        related='quant_id.owner_id',
        string="Owner (Customer)",
        store=True,
        help="Customer who owns this file"
    )
    
    location_id = fields.Many2one(
        related='quant_id.location_id',
        string="Stock Location",
        store=True,
        help="Physical location from stock quant (if tracked independently)"
    )
    
    current_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Current Location",
        compute='_compute_current_location_id',
        store=True,
        help="Effective current location: from stock quant if tracked independently, "
             "otherwise inherited from parent container"
    )
    
    parent_quant_id = fields.Many2one(
        related='quant_id.parent_quant_id',
        string="Parent Container",
        store=True,
        help="Container this file came from (for return tracking)"
    )
    
    # ============================================================================
    # CONTAINER RELATIONSHIP (Business Logic)
    # ============================================================================
    container_id = fields.Many2one(
        'records.container',
        string="Belongs to Container",
        tracking=True,
        help="Which container this file belongs to (when stored inside container)"
    )
    
    # ============================================================================
    # CUSTOMER RELATIONSHIP
    # ============================================================================
    partner_id = fields.Many2one(
        'res.partner',
        string="Customer",
        compute='_compute_partner_id',
        store=True,
        help="Customer who owns this file (inherited from container or owner)"
    )
    
    department_id = fields.Many2one(
        'records.department',
        string="Department",
        compute='_compute_department_id',
        store=True,
        tracking=True,
        help="Department this file belongs to (inherited from container)"
    )
    
    stock_owner_id = fields.Many2one(
        "res.partner",
        string="Stock Owner",
        tracking=True,
        index=True,
        compute='_compute_stock_owner_id',
        store=True,
        help="Inventory ownership hierarchy: Company → Department → Child Department. "
             "Auto-filled from Container or Customer selection. "
             "Organizational unit ownership (not individual users)."
    )
    
    # Active flag for archiving
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Uncheck to archive this file. Archived files are hidden from default views.'
    )
    
    # Portal tracking
    created_via_portal = fields.Boolean(
        string='Created via Portal',
        default=False,
        help='Indicates this file folder was created through the customer portal'
    )
    
    # Responsible Person - defaults to customer's portal user
    responsible_person_id = fields.Many2one(
        comodel_name='res.users',
        string='Responsible',
        tracking=True,
        help='Person responsible for this file. Defaults to customer\'s portal user or department contact.'
    )

    # ============================================================================
    # DOCUMENT RELATIONSHIPS
    # ============================================================================
    document_ids = fields.One2many(
        'records.document',
        'file_id',
        string="Documents in File",
        help="Individual documents/papers within this file folder"
    )
    
    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_document_count',
        store=True
    )
    
    # ============================================================================
    # METADATA
    # ============================================================================
    description = fields.Text(
        string="Description",
        help="Detailed description of file contents"
    )
    
    file_category = fields.Selection([
        ('administrative', 'Administrative'),
        ('financial', 'Financial'),
        ('legal', 'Legal'),
        ('hr', 'Human Resources'),
        ('operational', 'Operational'),
        ('compliance', 'Compliance'),
        ('other', 'Other'),
    ], string="File Category", tracking=True)
    
    date_created = fields.Date(
        string="Date Created",
        default=fields.Date.context_today,
        tracking=True
    )
    
    received_date = fields.Date(
        string="Received Date",
        default=fields.Date.context_today,
        tracking=True,
        help="Date when the file was received from the customer"
    )
    
    # ============================================================================
    # STATUS TRACKING
    # Files are either IN their container or OUT (delivered to customer).
    # When a file is added to a container, it's automatically "in".
    # When delivered via a request order, it becomes "out".
    # When technician scans container then file barcode, it returns to "in".
    # ============================================================================
    state = fields.Selection([
        ('in', 'In Storage'),        # File is in its container at warehouse
        ('out', 'Out'),              # File was removed and delivered to customer
    ], string='Status', default='in', required=True, tracking=True,
    help="File status: IN = Inside container at warehouse | OUT = Removed and delivered to customer. "
         "Returns to IN when technician scans container barcode then file barcode.")
    
    # Container's state (for reference/filtering)
    container_state = fields.Selection(
        related='container_id.state',
        string='Container Status',
        store=True,
        readonly=True,
        help="Status of the container this file belongs to."
    )
    
    # ============================================================================
    # LEGAL CITATIONS & RECORD SERIES (Optional Compliance Features)
    # ============================================================================
    record_series_id = fields.Many2one(
        comodel_name='record.series',
        string='Record Series',
        tracking=True,
        help='Optional: Assign a record series for grouping and retention policy management. '
             'Can be inherited from container or set independently.'
    )
    legal_citation_ids = fields.Many2many(
        comodel_name='legal.citation',
        relation='file_legal_citation_rel',
        column1='file_id',
        column2='citation_id',
        string='Legal Citations',
        tracking=True,
        help='Optional: Legal citations that justify retention policy for this file. '
             'Can be inherited from container/record series or set manually.'
    )
    disposition_id = fields.Many2one(
        comodel_name='record.disposition',
        string='Disposition Method',
        tracking=True,
        help='Optional: How this file should be handled at end of retention. '
             'Can be inherited from container/record series or set manually.'
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Count documents in this file"""
        for file in self:
            file.document_count = len(file.document_ids)

    @api.depends('location_id', 'container_id.current_location_id')
    def _compute_current_location_id(self):
        """
        Compute effective current location for display.
        
        Priority:
        1. File's own location_id (if tracked independently via quant)
        2. Container's current_location_id (if file is inside a container)
        3. Empty (if neither applies)
        """
        for file in self:
            if file.location_id:
                # File has its own stock quant location
                file.current_location_id = file.location_id.id
            elif file.container_id and file.container_id.current_location_id:
                # Inherit location from parent container
                file.current_location_id = file.container_id.current_location_id.id
            else:
                file.current_location_id = False
    
    @api.depends('owner_id', 'container_id.partner_id')
    def _compute_partner_id(self):
        """Compute customer from owner or container"""
        for file in self:
            if file.owner_id:
                file.partner_id = file.owner_id.id
            elif file.container_id and file.container_id.partner_id:
                file.partner_id = file.container_id.partner_id.id
            else:
                file.partner_id = False

    @api.depends('container_id.department_id')
    def _compute_department_id(self):
        """Compute department from container"""
        for file in self:
            if file.container_id and file.container_id.department_id:
                file.department_id = file.container_id.department_id.id
            else:
                file.department_id = False

    @api.depends('container_id.stock_owner_id', 'partner_id')
    def _compute_stock_owner_id(self):
        """Compute stock owner from container or customer for organizational hierarchy"""
        for file in self:
            if file.container_id and file.container_id.stock_owner_id:
                # Inherit from container's stock owner
                file.stock_owner_id = file.container_id.stock_owner_id.id
            elif file.partner_id:
                # Use customer as stock owner
                file.stock_owner_id = file.partner_id.id
            else:
                file.stock_owner_id = False

    # ============================================================================
    # CUSTOMER/DEPARTMENT USER HELPERS
    # ============================================================================
    @api.model
    def _get_customer_responsible_user(self, vals):
        """
        Get the appropriate responsible user for a file based on customer/department.
        
        Priority:
        1. Department's responsible user (user_id)
        2. First portal user of the department (user_ids)
        3. Customer's (partner) first portal user
        4. None (will remain empty)
        
        This ensures files are assigned to the customer's team, not internal staff.
        """
        # Try to get department first
        department_id = vals.get('department_id')
        if not department_id and vals.get('container_id'):
            container = self.env['records.container'].browse(vals['container_id'])
            department_id = container.department_id.id if container.department_id else None
        
        if department_id:
            department = self.env['records.department'].browse(department_id)
            # Priority 1: Department's responsible user
            if department.user_id and department.user_id.active:
                return department.user_id.id
            # Priority 2: First active portal user in department
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            if portal_group and department.user_ids:
                portal_users = department.user_ids.filtered(
                    lambda u: u.active and portal_group in u.groups_id
                )
                if portal_users:
                    return portal_users[0].id
        
        # Try to get partner
        partner_id = vals.get('partner_id')
        if not partner_id:
            if vals.get('container_id'):
                container = self.env['records.container'].browse(vals['container_id'])
                partner_id = container.partner_id.id if container.partner_id else None
            elif vals.get('owner_id'):
                partner_id = vals['owner_id']
        
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            commercial_partner = partner.commercial_partner_id
            # Find portal users linked to this customer
            portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
            if portal_group:
                portal_users = self.env['res.users'].search([
                    ('partner_id', 'child_of', commercial_partner.id),
                    ('groups_id', 'in', [portal_group.id]),
                    ('active', '=', True),
                ], limit=1)
                if portal_users:
                    return portal_users[0].id
        
        return False

    def _add_customer_followers(self):
        """
        Auto-add customer's portal users as followers on this file.
        
        This ensures customers receive notifications about their files.
        Only adds users who are:
        - Active
        - Portal users (group_portal)
        - Related to the customer (partner)
        """
        self.ensure_one()
        
        partner = self.partner_id or (self.container_id.partner_id if self.container_id else False)
        if not partner:
            return
        
        commercial_partner = partner.commercial_partner_id
        
        # Find all portal users for this customer
        portal_group = self.env.ref('base.group_portal', raise_if_not_found=False)
        if not portal_group:
            return
        
        # Get portal users related to this customer
        portal_users = self.env['res.users'].search([
            ('partner_id', 'child_of', commercial_partner.id),
            ('groups_id', 'in', [portal_group.id]),
            ('active', '=', True),
        ])
        
        if portal_users:
            # Get partner IDs of portal users to add as followers
            partner_ids = portal_users.mapped('partner_id').ids
            # Subscribe them as followers (avoid duplicates automatically)
            self.message_subscribe(partner_ids=partner_ids)

    def _generate_temp_barcode(self):
        """
        Generate temporary barcode with container prefix.
        
        Format: {CONTAINER_NUMBER}-FILE-{SEQUENCE}
        Example: REC-0302-FILE-1, HR-1001-A-FILE-2
        
        If no container, uses just FILE-{SEQUENCE}
        """
        self.ensure_one()
        sequence = self.env['ir.sequence'].next_by_code('records.file.temp.barcode')
        if not sequence:
            sequence = str(self.id)
        
        if self.container_id and self.container_id.name:
            return f"{self.container_id.name}-FILE-{sequence}"
        return f"FILE-{sequence}"
    
    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """
        Create file record.
        
        WORKFLOW:
        1. User removes file from container
        2. Types file name (customer's naming system)
        3. Assigns pre-printed barcode from sheet
        4. System creates stock.quant link (if tracking needed)
        
        AUTO-DEFAULTS:
        - responsible_person_id: Customer's portal user or department user
        - Followers: Customer's portal users are auto-subscribed
        
        NOTE: Barcode is MANUALLY assigned, not auto-generated
        """
        # Pre-process vals to set responsible_person_id to customer/department user
        for vals in vals_list:
            if not vals.get('responsible_person_id'):
                vals['responsible_person_id'] = self._get_customer_responsible_user(vals)
        
        files = super().create(vals_list)
        
        for file in files:
            # Auto-generate temp_barcode if not provided
            if not file.temp_barcode and not file.barcode:
                file.temp_barcode = file._generate_temp_barcode()
            
            # Auto-add customer's portal users as followers
            file._add_customer_followers()
            
            # Auto-create stock.quant.package for barcode scanning
            # File packages are nested under container's package
            file._create_or_update_stock_package()
            
            # Auto-create draft staging location if file is in draft and has no container
            if file.state == 'draft' and not file.container_id and file.partner_id:
                draft_location = self._get_or_create_draft_staging_location(file.partner_id)
                if draft_location and not file.staging_location_id:
                    file.staging_location_id = draft_location.id
            
            # If container specified and file needs inventory tracking
            if file.container_id and file.container_id.quant_id and file.barcode:
                # Create stock.quant for this file (only if barcode assigned)
                if not file.quant_id:
                    quant = self.env['stock.quant'].create({
                        'product_id': self._get_default_product().id,
                        'lot_id': self._create_lot_for_file(file).id,
                        'owner_id': file.container_id.quant_id.owner_id.id,
                        'location_id': file.container_id.quant_id.location_id.id,
                        'quantity': 1.0,
                        'is_records_file': True,
                        'parent_quant_id': file.container_id.quant_id.id,
                    })
                    file.quant_id = quant.id
                    file.state = 'stored'
            
            # NAID Audit Log - File Creation
            self.env['naid.audit.log'].sudo().create({
                'name': _('File Created: %s') % file.name,
                'action_type': 'file_created',
                'description': _('File folder created: %s (Barcode: %s, Container: %s)') % (
                    file.name,
                    file.barcode or file.temp_barcode or 'N/A',
                    file.container_id.name if file.container_id else 'None'
                ),
                'user_id': self.env.user.id,
            })
        
        return files
    
    def write(self, vals):
        """Override write to add NAID audit logging for file updates."""
        result = super().write(vals)
        
        # Sync stock package when barcode or container changes
        if 'barcode' in vals or 'temp_barcode' in vals or 'container_id' in vals:
            for file in self:
                file._create_or_update_stock_package()
        
        for file in self:
            # Track important field changes
            important_fields = ['name', 'barcode', 'container_id', 'state', 'location_id']
            changed_fields = [field for field in important_fields if field in vals]
            
            if changed_fields:
                description_parts = [_('File updated: %s') % file.name]
                if 'name' in vals:
                    description_parts.append(_('Name changed'))
                if 'barcode' in vals:
                    description_parts.append(_('Barcode: %s') % (vals['barcode'] or 'Removed'))
                if 'container_id' in vals:
                    container = self.env['records.container'].browse(vals['container_id']) if vals['container_id'] else None
                    description_parts.append(_('Container: %s') % (container.name if container else 'Removed'))
                if 'state' in vals:
                    description_parts.append(_('State: %s') % vals['state'])
                
                self.env['naid.audit.log'].sudo().create({
                    'name': _('File Updated: %s') % file.name,
                    'action_type': 'file_updated',
                    'description': ', '.join(description_parts),
                    'user_id': self.env.user.id,
                })
        
        return result
    
    def unlink(self):
        """Override unlink to add NAID audit logging for file deletion."""
        for file in self:
            self.env['naid.audit.log'].sudo().create({
                'name': _('File Deleted: %s') % file.name,
                'action_type': 'unlink',
                'description': _('File folder deleted: %s (Barcode: %s, Container: %s)') % (
                    file.name,
                    file.barcode or file.temp_barcode or 'N/A',
                    file.container_id.name if file.container_id else 'None'
                ),
                'user_id': self.env.user.id,
            })
        
        return super().unlink()
    
    def _get_or_create_draft_staging_location(self, partner):
        """
        Get or create a virtual staging location for draft files.
        
        Naming pattern: [Partner Name] / Draft Files
        Example: "City of El Paso / Draft Files"
        
        This provides a default location for files in draft state before they're
        assigned to physical containers.
        """
        if not partner:
            return False
        
        # Search for existing draft location
        draft_location = self.env['customer.staging.location'].search([
            ('partner_id', '=', partner.id),
            ('name', '=', 'Draft Files'),
        ], limit=1)
        
        if draft_location:
            return draft_location
        
        # Create new draft staging location
        draft_location = self.env['customer.staging.location'].create({
            'name': 'Draft Files',
            'partner_id': partner.id,
            'description': 'Auto-created virtual location for draft files awaiting container assignment',
            'active': True,
        })
        
        return draft_location
    
    def _get_default_product(self):
        """Get or create the default 'File Folder' product"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-FILE-FOLDER')
        ], limit=1)
        
        if not product:
            # Create file folder product with serial tracking (Odoo 18+)
            product_vals = {
                'name': 'Records File Folder',
                'default_code': 'RM-FILE-FOLDER',
                'type': 'consu',  # Odoo 18+ uses 'consu' (consumable)
                'tracking': 'serial',
                'categ_id': self.env.ref('stock.product_category_all').id,
            }
                
            product = self.env['product.product'].create(product_vals)
        
        return product
    
    def _create_lot_for_file(self, file):
        """
        Create serial number (lot) for this file using assigned barcode.
        
        NOTE: Barcode must already be assigned (from pre-printed sheet)
        """
        if not file.barcode:
            raise UserError(_(
                "Cannot create inventory tracking without barcode. "
                "Please assign a pre-printed barcode to this file first."
            ))
        
        return self.env['stock.lot'].create({
            'name': file.barcode,
            'product_id': self._get_default_product().id,
            'company_id': self.env.company.id,
        })
    
    def _create_or_update_stock_package(self):
        """
        Create or update stock.quant.package for Stock Barcode compatibility.
        
        This enables Odoo's Stock Barcode to recognize file barcodes.
        """
        self.ensure_one()
        
        barcode = self.barcode or self.temp_barcode
        if not barcode:
            return
        
        # If file already has a package, update it
        if self.package_id:
            if self.package_id.name != barcode:
                self.package_id.write({'name': barcode})
            return
        
        # Search for existing package with this barcode
        existing_package = self.env['stock.quant.package'].search([
            ('name', '=', barcode)
        ], limit=1)
        
        if existing_package:
            self.write({'package_id': existing_package.id})
            return
        
        # Create new package
        package_vals = {
            'name': barcode,
            'company_id': self.company_id.id if hasattr(self, 'company_id') and self.company_id else self.env.company.id,
        }
        
        package = self.env['stock.quant.package'].create(package_vals)
        self.write({'package_id': package.id})
    
    def action_assign_barcode_and_track(self):
        """
        User action: Assign barcode from pre-printed sheet and enable tracking.
        
        WORKFLOW:
        1. File removed from container
        2. User enters file name (customer's naming system)
        3. User clicks "Assign Barcode" 
        4. System prompts for barcode from pre-printed sheet
        5. Creates stock.quant for independent tracking
        
        Returns: Form wizard to assign barcode
        """
        self.ensure_one()
        
        if self.quant_id:
            raise UserError(_("This file already has inventory tracking enabled."))
        
        if not self.container_id:
            raise UserError(_("File must belong to a container to enable tracking."))
        
        return {
            'name': _('Assign Barcode to File'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.file',
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'form_view_ref': 'records_management.view_records_file_assign_barcode_form',
            },
        }
    
    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_retrieve_from_container(self):
        """
        Action: Remove file from container for delivery/retrieval.
        Creates stock picking to move file out of warehouse.
        """
        self.ensure_one()
        
        if self.state != 'stored':
            raise UserError(_("File must be in 'Stored in Container' state to retrieve."))
        
        if not self.quant_id:
            raise UserError(_("File must have inventory tracking (quant_id) to retrieve."))
        
        # Create retrieval picking
        picking_type = self.env['stock.picking.type'].search([
            ('code', '=', 'outgoing'),
        ], limit=1)
        
        picking = self.env['stock.picking'].create({
            'picking_type_id': picking_type.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
            'partner_id': self.owner_id.id,
            'origin': f"Retrieve File: {self.name}",
        })
        
        self.env['stock.move'].create({
            'name': self.name,
            'product_id': self.quant_id.product_id.id,
            'product_uom_qty': 1,
            'product_uom': self.quant_id.product_id.uom_id.id,
            'picking_id': picking.id,
            'location_id': self.location_id.id,
            'location_dest_id': self.env.ref('stock.stock_location_customers').id,
        })
        
        self.state = 'retrieved'
        self.message_post(body=_("File retrieved from container by %s") % self.env.user.name)
        
        return {
            'name': _('File Retrieval'),
            'type': 'ir.actions.act_window',
            'res_model': 'stock.picking',
            'res_id': picking.id,
            'view_mode': 'form',
        }
    
    def action_return_to_container(self):
        """
        Action: Return file to its parent container.
        Uses stock.quant.action_return_to_parent for movement.
        """
        self.ensure_one()
        
        if not self.quant_id:
            raise UserError(_("File must have inventory tracking to return."))
        
        if not self.quant_id.parent_quant_id:
            raise UserError(_("File has no parent container to return to."))
        
        # Delegate to stock.quant method
        result = self.quant_id.action_return_to_parent()
        
        self.state = 'returned'
        self.message_post(body=_("File returned to container %s") % self.container_id.name)
        
        return result
    
    def action_view_documents(self):
        """View documents within this file"""
        self.ensure_one()
        return {
            'name': _('Documents in File: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'list,form',
            'domain': [('file_id', '=', self.id)],
            'context': {'default_file_id': self.id},
        }
    
    def action_view_movement_history(self):
        """View stock moves for this file"""
        self.ensure_one()
        
        if not self.quant_id or not self.quant_id.lot_id:
            raise UserError(_("File must have inventory tracking to view movement history."))
        
        return {
            'name': _('Movement History: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'stock.move.line',
            'view_mode': 'list,form',
            'domain': [('lot_id', '=', self.quant_id.lot_id.id)],
        }

    def action_upload_document(self):
        """Upload new document/PDF to this file"""
        self.ensure_one()
        return {
            'name': _('Upload Documents to File: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'document.upload.wizard',
            'view_mode': 'form',
            'context': {
                'default_file_id': self.id,
            },
            'target': 'new',
        }
    
    def action_add_documents(self):
        """Add existing documents to this file"""
        self.ensure_one()
        return {
            'name': _('Add Documents to File: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'list',
            'domain': [('file_id', '=', False), ('partner_id', '=', self.partner_id.id if self.partner_id else False)],
            'context': {
                'default_file_id': self.id,
                'default_container_id': self.container_id.id if self.container_id else False,
                'search_default_available': 1,
            },
            'target': 'new',
        }
    
    def action_remove_documents(self):
        """Remove documents from this file"""
        self.ensure_one()
        return {
            'name': _('Remove Documents from File: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'list',
            'domain': [('file_id', '=', self.id)],
            'context': {
                'file_remove_mode': True,
                'active_file_id': self.id,
            },
            'target': 'new',
        }

    def action_view_container(self):
        """View the container this file belongs to"""
        self.ensure_one()
        if not self.container_id:
            raise UserError(_("This file is not assigned to any container."))
        return {
            'name': _('Container: %s') % self.container_id.name,
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'res_id': self.container_id.id,
            'view_mode': 'form',
        }

    def action_generate_barcode(self):
        """Generate barcode for this file"""
        self.ensure_one()
        if not self.barcode and not self.temp_barcode:
            # Generate temp barcode if none exists
            self.temp_barcode = self._generate_temp_barcode()
        
        # Return print action using the report action
        return self.env.ref('records_management.report_file_barcode').report_action(self)

    def action_generate_qr_code(self):
        """Generate QR code for this file
        
        QR code contains secure portal URL requiring authentication.
        Prevents unauthorized access to sensitive file metadata.
        """
        self.ensure_one()
        if not self.temp_barcode:
            self.temp_barcode = self._generate_temp_barcode()
        
        # Return QR code generation action using the report action
        return self.env.ref('records_management.report_file_qrcode').report_action(self)
    
    # ============================================================================
    # LABEL PRINTING METHODS (ZPL + Labelary API)
    # ============================================================================
    
    def action_print_barcode_label(self):
        """
        Generate and download a professional barcode label for this file folder.
        
        Enhanced with reprint detection, signature requirement, and chatter logging.
        Label size: 2.5935" x 1" (standard file folder labels, 30 per page)
        """
        self.ensure_one()
        
        barcode = self.barcode or self.temp_barcode
        if not barcode:
            raise UserError(_("Folder must have a barcode before printing labels."))
        
        # Check for previous print
        previous_print = self.env['ir.attachment'].search([
            ('res_model', '=', self._name),
            ('res_id', '=', self.id),
            ('name', 'ilike', 'folder_label'),
        ], limit=1)
        
        if previous_print:
            return {
                'name': _('Confirm Barcode Reprint'),
                'type': 'ir.actions.act_window',
                'res_model': 'barcode.reprint.wizard',
                'view_mode': 'form',
                'target': 'new',
                'context': {
                    'default_file_id': self.id,
                    'default_barcode': barcode,
                    'default_previous_print_date': previous_print.create_date,
                    'default_record_type': 'folder',
                }
            }
        
        # Generate label
        generator = self.env['zpl.label.generator']
        result = generator.generate_folder_label(self)
        
        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
            'description': f"Folder barcode label printed by {self.env.user.name}",
        })
        
        # Log in chatter
        self.message_post(
            body=_("Folder barcode label printed by %s<br/>Barcode: <strong>%s</strong>") % (
                self.env.user.name,
                barcode
            ),
            subject=_("Barcode Label Printed"),
            attachment_ids=[attachment.id],
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    def action_print_qr_label(self):
        """
        Generate QR code label that links to customer portal login.
        
        Label size: 1" x 1.25" (49 per sheet)
        Logs print action in chatter.
        """
        self.ensure_one()
        
        generator = self.env['zpl.label.generator']
        result = generator.generate_qr_label(self, record_type='folder')
        
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'res_model': self._name,
            'res_id': self.id,
            'mimetype': 'application/pdf',
            'description': f"QR code label printed by {self.env.user.name}",
        })
        
        # Log in chatter
        self.message_post(
            body=_("QR code label printed by %s") % self.env.user.name,
            subject=_("QR Label Printed"),
            attachment_ids=[attachment.id],
        )
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    @api.model
    def action_print_batch_labels(self, folder_ids=None):
        """
        Print barcode labels for multiple folders in a single PDF.
        
        Args:
            folder_ids (list): List of folder IDs to print labels for.
                              If None, uses active_ids from context.
        
        Returns:
            Action to download multi-page PDF with all labels.
        """
        if folder_ids is None:
            folder_ids = self.env.context.get('active_ids', [])
        
        if not folder_ids:
            raise UserError(_("No folders selected for batch label printing."))
        
        folders = self.browse(folder_ids)
        
        generator = self.env['zpl.label.generator']
        result = generator.generate_batch_folder_labels(folders)
        
        attachment = self.env['ir.attachment'].create({
            'name': result['filename'],
            'type': 'binary',
            'datas': result['pdf_data'],
            'mimetype': 'application/pdf',
        })
        
        return {
            'type': 'ir.actions.act_url',
            'url': f'/web/content/{attachment.id}?download=true',
            'target': 'new',
        }
    
    # ============================================================================
    # BILLING & WORK ORDER AUTOMATION METHODS (Mirror container logic)
    # ============================================================================
    
    def _create_destruction_charges(self):
        """
        Create invoice charges for file destruction.
        
        Destruction includes:
        - Per-item removal fee
        - Per-item shredding fee
        
        Creates 2 invoice line items.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Cannot create destruction charges: No customer assigned to file %s") % self.name)
        
        # Get or create draft invoice for customer
        invoice = self._get_or_create_draft_invoice()
        
        # Get product for removal and shredding fees
        removal_product = self._get_removal_fee_product()
        shredding_product = self._get_shredding_fee_product()
        
        # Create invoice lines
        invoice_line_vals = [
            {
                'product_id': removal_product.id,
                'name': _('File Removal Fee - %s') % self.name,
                'quantity': 1,
                'price_unit': removal_product.list_price * 0.5,  # Files are half price of containers
                'move_id': invoice.id,
            },
            {
                'product_id': shredding_product.id,
                'name': _('File Shredding Fee - %s') % self.name,
                'quantity': 1,
                'price_unit': shredding_product.list_price * 0.5,  # Files are half price of containers
                'move_id': invoice.id,
            }
        ]
        
        self.env['account.move.line'].create(invoice_line_vals)
        
        # Log charge creation
        total = (removal_product.list_price + shredding_product.list_price) * 0.5
        self.message_post(
            body=_("Destruction charges created:<br/>• Removal fee: %s<br/>• Shredding fee: %s<br/>Total: %s") % (
                removal_product.list_price * 0.5,
                shredding_product.list_price * 0.5,
                total
            ),
            subject=_("Destruction Charges Created")
        )
        
        return invoice
    
    def _create_removal_charges(self):
        """
        Create invoice charges for permanent removal (perm-out).
        
        Perm-Out includes:
        - Per-item removal fee ONLY (no shredding)
        
        Creates 1 invoice line item.
        """
        self.ensure_one()
        
        if not self.partner_id:
            raise UserError(_("Cannot create removal charges: No customer assigned to file %s") % self.name)
        
        # Get or create draft invoice for customer
        invoice = self._get_or_create_draft_invoice()
        
        # Get product for removal fee
        removal_product = self._get_removal_fee_product()
        
        # Create invoice line
        invoice_line_vals = {
            'product_id': removal_product.id,
            'name': _('File Removal Fee (Perm-Out) - %s') % self.name,
            'quantity': 1,
            'price_unit': removal_product.list_price * 0.5,  # Files are half price of containers
            'move_id': invoice.id,
        }
        
        self.env['account.move.line'].create(invoice_line_vals)
        
        # Log charge creation
        self.message_post(
            body=_("Removal charges created (Perm-Out):<br/>• Removal fee: %s") % (removal_product.list_price * 0.5),
            subject=_("Perm-Out Charges Created")
        )
        
        return invoice
    
    def _get_or_create_draft_invoice(self):
        """Get existing draft invoice or create new one for customer"""
        invoice = self.env['account.move'].search([
            ('partner_id', '=', self.partner_id.id),
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft'),
        ], limit=1)
        
        if not invoice:
            invoice = self.env['account.move'].create({
                'partner_id': self.partner_id.id,
                'move_type': 'out_invoice',
                'invoice_date': fields.Date.today(),
            })
        
        return invoice
    
    def _get_removal_fee_product(self):
        """Get product for removal fees"""
        return self.env['product.product'].search([
            ('default_code', '=', 'RM-REMOVAL-FEE'),
        ], limit=1)
    
    def _get_shredding_fee_product(self):
        """Get product for shredding fees"""
        return self.env['product.product'].search([
            ('default_code', '=', 'RM-SHREDDING-FEE'),
        ], limit=1)
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('barcode')
    def _check_barcode_unique(self):
        """Ensure barcode is unique"""
        for file in self:
            if file.barcode:
                duplicate = self.search([
                    ('barcode', '=', file.barcode),
                    ('id', '!=', file.id),
                ], limit=1)
                if duplicate:
                    raise ValidationError(_(
                        "Barcode %s is already used by file: %s"
                    ) % (file.barcode, duplicate.name))
