from odoo import models, fields, api, _
from odoo.exceptions import UserError


class WorkOrderLine(models.Model):
    """
    Work Order Line Items for per-unit billing.
    
    BILLING MODEL:
    - Each scan/item creates a line with barcode, timestamp, product, qty
    - For bins: product is the bin size (96 gallon, 64 gallon, etc.)
    - For containers (destruction): product is Retrieval + Perm Out + Shred Box fees
    - For shred boxes (customer-supplied): technician enters qty × Shred Box rate
    
    The work order totals are calculated from sum of line items.
    """
    
    _name = 'work.order.line'
    _description = 'Work Order Line Item'
    _order = 'scan_timestamp desc, sequence, id'
    
    # ============================================================================
    # PARENT WORK ORDER LINKS
    # ============================================================================
    shredding_work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string="Shredding Work Order",
        ondelete='cascade',
        index=True
    )
    retrieval_work_order_id = fields.Many2one(
        comodel_name='work.order.retrieval',
        string="Retrieval Work Order",
        ondelete='cascade',
        index=True
    )
    
    sequence = fields.Integer(string="Sequence", default=10)
    
    # ============================================================================
    # LINE ITEM IDENTIFICATION
    # ============================================================================
    name = fields.Char(
        string="Description",
        required=True,
        help="Auto-generated from scanned item or manually entered"
    )
    
    barcode = fields.Char(
        string="Barcode",
        index=True,
        help="Barcode of scanned item (bin or container)"
    )
    
    scan_timestamp = fields.Datetime(
        string="Scan Time",
        default=fields.Datetime.now,
        readonly=True,
        help="When the item was scanned"
    )
    
    scanned_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Scanned By",
        default=lambda self: self.env.user,
        readonly=True
    )
    
    # ============================================================================
    # LINKED ITEMS (what was scanned)
    # ============================================================================
    container_id = fields.Many2one(
        comodel_name='records.container',
        string="Container",
        help="Linked container from inventory (for destruction/retrieval)"
    )
    
    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Shredding Bin",
        help="Linked shredding bin (for bin service)"
    )
    
    line_type = fields.Selection([
        ('bin_service', 'Bin Service'),
        ('container_destruction', 'Container Destruction'),
        ('container_retrieval', 'Container Retrieval'),
        ('shred_box', 'Shred Box (Customer Supplied)'),
        ('manual', 'Manual Entry'),
    ], string="Line Type", default='manual', required=True)
    
    # ============================================================================
    # PRODUCT AND BILLING
    # ============================================================================
    product_id = fields.Many2one(
        comodel_name='product.product',
        string="Product",
        required=True,
        help="The service/product being billed"
    )
    
    quantity = fields.Float(
        string="Quantity",
        default=1.0,
        required=True
    )
    
    uom_id = fields.Many2one(
        comodel_name='uom.uom',
        string="Unit of Measure",
        related='product_id.uom_id',
        readonly=True
    )
    
    unit_price = fields.Float(
        string="Unit Price",
        digits='Product Price',
        compute='_compute_unit_price',
        store=True,
        readonly=False,
        help="Price per unit. Auto-filled from product but can be overridden."
    )
    
    subtotal = fields.Monetary(
        string="Subtotal",
        compute='_compute_subtotal',
        store=True,
        currency_field='currency_id'
    )
    
    currency_id = fields.Many2one(
        comodel_name='res.currency',
        compute='_compute_currency_id',
        store=True
    )
    
    # Customer-specific pricing
    customer_rate_applied = fields.Boolean(
        string="Customer Rate Applied",
        default=False,
        help="True if customer-specific pricing was applied"
    )
    
    # ============================================================================
    # STATUS TRACKING
    # ============================================================================
    state = fields.Selection([
        ('pending', 'Pending'),
        ('processed', 'Processed'),
        ('invoiced', 'Invoiced'),
        ('cancelled', 'Cancelled'),
    ], string="Status", default='pending')
    
    notes = fields.Text(string="Notes")
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('shredding_work_order_id.partner_id', 'retrieval_work_order_id.partner_id')
    def _compute_currency_id(self):
        for line in self:
            partner = (line.shredding_work_order_id.partner_id or 
                      line.retrieval_work_order_id.partner_id)
            if partner and partner.property_product_pricelist:
                line.currency_id = partner.property_product_pricelist.currency_id
            else:
                line.currency_id = self.env.company.currency_id
    
    @api.depends('product_id', 'shredding_work_order_id.partner_id', 'retrieval_work_order_id.partner_id')
    def _compute_unit_price(self):
        """Get unit price from customer pricelist or product default."""
        for line in self:
            if not line.product_id:
                line.unit_price = 0.0
                continue
                
            partner = (line.shredding_work_order_id.partner_id or 
                      line.retrieval_work_order_id.partner_id)
            
            if partner and partner.property_product_pricelist:
                # Use customer's pricelist
                pricelist = partner.property_product_pricelist
                price = pricelist._get_product_price(
                    line.product_id, 
                    line.quantity or 1.0
                )
                line.unit_price = price
                line.customer_rate_applied = True
            else:
                # Use product list price
                line.unit_price = line.product_id.list_price
                line.customer_rate_applied = False
    
    @api.depends('quantity', 'unit_price')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.quantity * line.unit_price
    
    # ============================================================================
    # LINE CREATION HELPERS
    # ============================================================================
    @api.model
    def create_from_bin_scan(self, bin_record, work_order, service_type='tip'):
        """
        Create a line item from a bin scan.
        
        Args:
            bin_record: shredding.service.bin record
            work_order: work.order.shredding record
            service_type: 'tip' or 'swap'
            
        Returns:
            work.order.line record
        """
        # Get the appropriate product for this bin size
        product = bin_record._get_service_product()
        if not product:
            raise UserError(_("No service product found for bin size %s") % bin_record.bin_size)
        
        return self.create({
            'shredding_work_order_id': work_order.id,
            'name': _("Bin Service - %s") % bin_record.name,
            'barcode': bin_record.barcode,
            'bin_id': bin_record.id,
            'line_type': 'bin_service',
            'product_id': product.id,
            'quantity': 1.0,
        })
    
    @api.model
    def create_from_container_destruction(self, container, work_order):
        """
        Create line items for container destruction.
        Creates 3 charges: Retrieval + Perm Out + Shred Box
        
        Args:
            container: records.container record
            work_order: work.order.shredding record
            
        Returns:
            recordset of work.order.line records
        """
        lines = self.env['work.order.line']
        
        # Get the three fee products
        retrieval_product = self.env.ref(
            'records_management.product_retrieval_service', 
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'REC-RETRIEVAL')], limit=1)
        
        perm_out_product = self.env.ref(
            'records_management.product_perm_out_fee',
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'RM-PERMOUT-FEE')], limit=1)
        
        shred_box_product = self.env.ref(
            'records_management.product_shred_box',
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'SHRED-BOX')], limit=1)
        
        base_vals = {
            'shredding_work_order_id': work_order.id,
            'barcode': container.barcode,
            'container_id': container.id,
            'line_type': 'container_destruction',
            'quantity': 1.0,
        }
        
        # Retrieval fee
        if retrieval_product:
            lines |= self.create({
                **base_vals,
                'name': _("Retrieval Fee - %s") % container.name,
                'product_id': retrieval_product.id,
                'sequence': 1,
            })
        
        # Perm Out fee
        if perm_out_product:
            lines |= self.create({
                **base_vals,
                'name': _("Perm Out Fee - %s") % container.name,
                'product_id': perm_out_product.id,
                'sequence': 2,
            })
        
        # Shred Box fee (destruction)
        if shred_box_product:
            lines |= self.create({
                **base_vals,
                'name': _("Destruction Fee - %s") % container.name,
                'product_id': shred_box_product.id,
                'sequence': 3,
            })
        
        return lines
    
    @api.model
    def create_from_container_retrieval(self, container, work_order):
        """
        Create line items for container retrieval (Perm Out).
        Creates 2 charges: Retrieval + Perm Out
        
        Args:
            container: records.container record  
            work_order: work.order.retrieval record
            
        Returns:
            recordset of work.order.line records
        """
        lines = self.env['work.order.line']
        
        retrieval_product = self.env.ref(
            'records_management.product_retrieval_service',
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'REC-RETRIEVAL')], limit=1)
        
        perm_out_product = self.env.ref(
            'records_management.product_perm_out_fee',
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'RM-PERMOUT-FEE')], limit=1)
        
        base_vals = {
            'retrieval_work_order_id': work_order.id,
            'barcode': container.barcode,
            'container_id': container.id,
            'line_type': 'container_retrieval',
            'quantity': 1.0,
        }
        
        # Retrieval fee
        if retrieval_product:
            lines |= self.create({
                **base_vals,
                'name': _("Retrieval Fee - %s") % container.name,
                'product_id': retrieval_product.id,
                'sequence': 1,
            })
        
        # Perm Out fee
        if perm_out_product:
            lines |= self.create({
                **base_vals,
                'name': _("Perm Out Fee - %s") % container.name,
                'product_id': perm_out_product.id,
                'sequence': 2,
            })
        
        return lines
    
    @api.model
    def create_shred_box_line(self, work_order, quantity=1):
        """
        Create a line for customer-supplied shred boxes.
        Technician enters quantity.
        
        Args:
            work_order: work.order.shredding record
            quantity: number of boxes
            
        Returns:
            work.order.line record
        """
        shred_box_product = self.env.ref(
            'records_management.product_shred_box',
            raise_if_not_found=False
        ) or self.env['product.product'].search([('default_code', '=', 'SHRED-BOX')], limit=1)
        
        if not shred_box_product:
            raise UserError(_("Shred Box product not found. Please configure it first."))
        
        return self.create({
            'shredding_work_order_id': work_order.id,
            'name': _("Shred Box (Customer Supplied)"),
            'line_type': 'shred_box',
            'product_id': shred_box_product.id,
            'quantity': quantity,
        })
