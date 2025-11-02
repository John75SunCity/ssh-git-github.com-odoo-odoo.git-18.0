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
    # CORE IDENTIFICATION
    # ============================================================================
    name = fields.Char(
        string="File Name",
        required=True,
        tracking=True,
        help="Descriptive name of this file folder (e.g., 'HR Personnel 2024', 'Invoices Q1')"
    )
    
    barcode = fields.Char(
        string="File Barcode",
        tracking=True,
        copy=False,
        help="Unique barcode for tracking this file when removed from container"
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
    
    owner_id = fields.Many2one(
        related='quant_id.owner_id',
        string="Owner (Customer)",
        store=True,
        help="Customer who owns this file"
    )
    
    location_id = fields.Many2one(
        related='quant_id.location_id',
        string="Current Location",
        store=True,
        help="Physical location of this file (warehouse, customer site, transit, etc.)"
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
    
    # ============================================================================
    # STATUS TRACKING
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('stored', 'Stored in Container'),
        ('retrieved', 'Retrieved from Container'),
        ('at_customer', 'At Customer Site'),
        ('in_transit', 'In Transit'),
        ('returned', 'Returned to Container'),
    ], string='Status', default='draft', tracking=True)
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Count documents in this file"""
        for file in self:
            file.document_count = len(file.document_ids)
    
    # ============================================================================
    # LIFECYCLE METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Create file and optionally link to stock.quant"""
        files = super().create(vals_list)
        
        for file in files:
            # Auto-generate barcode if not provided
            if not file.barcode:
                file.barcode = f"FILE-{file.id:06d}"
            
            # If container specified, inherit owner from container
            if file.container_id and file.container_id.quant_id:
                # Create stock.quant for this file
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
        
        return files
    
    def _get_default_product(self):
        """Get or create the default 'File Folder' product"""
        product = self.env['product.product'].search([
            ('default_code', '=', 'RM-FILE-FOLDER')
        ], limit=1)
        
        if not product:
            product = self.env['product.product'].create({
                'name': 'Records File Folder',
                'default_code': 'RM-FILE-FOLDER',
                'type': 'product',
                'tracking': 'serial',
                'categ_id': self.env.ref('stock.product_category_all').id,
            })
        
        return product
    
    def _create_lot_for_file(self, file):
        """Create serial number (lot) for this file"""
        return self.env['stock.lot'].create({
            'name': file.barcode,
            'product_id': self._get_default_product().id,
            'company_id': self.env.company.id,
        })
    
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
            'view_mode': 'tree,form',
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
            'view_mode': 'tree,form',
            'domain': [('lot_id', '=', self.quant_id.lot_id.id)],
        }
    
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
