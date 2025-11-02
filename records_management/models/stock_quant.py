from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class StockQuant(models.Model):
    """
    Extend stock.quant to support Records Management ownership tracking.
    
    KEY ARCHITECTURE for Records Management Business Model:
    ========================================================
    
    Problem: Service provider manages physical records FOR customers
    - Customer A's containers stored in Service Provider's warehouse
    - Location changes (pickup, storage, retrieval) must NOT change ownership
    - Need to track: "Whose inventory" vs "Where is it physically"
    
    Odoo's Built-in Solution:
    - owner_id: WHO owns the inventory (Customer partner_id)
    - location_id: WHERE it's physically located (Service provider's warehouse)
    - These are SEPARATE - ownership persists through location changes!
    
    Example:
    --------
    owner_id = City of Las Cruces (res.partner)
    location_id = My Warehouse / Aisle 5 / Shelf B-3 (stock.location)
    
    Result: "City of Las Cruces' inventory" stored in "My Warehouse"
    When moved to different location → owner_id STAYS "City of Las Cruces"
    
    This model extends stock.quant to add records-specific metadata while
    leveraging Odoo's proven inventory tracking, lot/serial numbers, stock
    moves, barcode scanning, and ownership separation.
    """
    
    _inherit = 'stock.quant'

    # ============================================================================
    # RECORDS MANAGEMENT IDENTIFICATION
    # ============================================================================
    is_records_container = fields.Boolean(
        string="Is Records Container",
        default=False,
        help="Identifies this quant as a records management container (box) "
             "rather than standard inventory. Enables records-specific features."
    )
    
    # ============================================================================
    # CUSTOMER OWNERSHIP (uses native owner_id)
    # ============================================================================
    # NOTE: owner_id is a NATIVE Odoo field on stock.quant!
    # We add a related field for clarity in records management context
    customer_id = fields.Many2one(
        related='owner_id',
        string="Container Owner (Customer)",
        store=True,
        help="The customer who owns this container. Uses Odoo's native owner_id "
             "field to ensure ownership persists through location changes. "
             "When container moves from customer site → your warehouse → offsite storage, "
             "the customer_id (owner_id) NEVER changes - only location_id changes."
    )
    
    # ============================================================================
    # RECORDS MANAGEMENT METADATA
    # ============================================================================
    container_state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active/Indexed'),
        ('stored', 'In Storage'),
        ('retrieved', 'Retrieved'),
        ('pending_destruction', 'Pending Destruction'),
        ('destroyed', 'Destroyed'),
    ], string='Container Status', default='draft',
       help="Lifecycle state of the records container")
    
    retention_policy_id = fields.Many2one(
        'records.retention.policy',
        string="Retention Policy",
        help="Retention policy governing this container's lifecycle"
    )
    
    destruction_due_date = fields.Date(
        string="Destruction Due Date",
        help="Date when container becomes eligible for destruction"
    )
    
    is_due_for_destruction = fields.Boolean(
        string="Due for Destruction",
        compute='_compute_is_due_for_destruction',
        store=True,
        help="Automatically computed based on destruction_due_date"
    )
    
    security_level = fields.Selection([
        ('public', 'Public'),
        ('internal', 'Internal'),
        ('confidential', 'Confidential'),
        ('restricted', 'Restricted'),
    ], string='Security Level', default='internal',
       help="Security classification of container contents")
    
    # ============================================================================
    # BILLING INTEGRATION
    # ============================================================================
    billable = fields.Boolean(
        string="Billable",
        default=True,
        help="Whether this container should be included in billing calculations"
    )
    
    monthly_storage_rate = fields.Monetary(
        string="Monthly Storage Rate",
        currency_field='currency_id',
        help="Monthly storage charge for this container"
    )
    
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        default=lambda self: self.env.company.currency_id
    )
    
    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    document_ids = fields.One2many(
        'records.document',
        'quant_id',
        string="Documents",
        help="Individual documents/files within this container"
    )
    
    document_count = fields.Integer(
        string="Document Count",
        compute='_compute_document_count',
        store=True
    )
    
    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_due_date')
    def _compute_is_due_for_destruction(self):
        """Check if container is past its retention period"""
        today = fields.Date.today()
        for quant in self:
            quant.is_due_for_destruction = (
                quant.destruction_due_date and 
                quant.destruction_due_date <= today
            )
    
    @api.depends('document_ids')
    def _compute_document_count(self):
        """Count documents in container"""
        for quant in self:
            quant.document_count = len(quant.document_ids)
    
    # ============================================================================
    # BUSINESS LOGIC
    # ============================================================================
    @api.model
    def get_customer_inventory(self, partner_id):
        """
        Get all containers owned by a specific customer,
        regardless of physical location.
        
        This demonstrates the power of owner_id:
        Returns customer's inventory whether it's:
        - At customer site (temp locations)
        - In your warehouse (internal locations)
        - In transit (transit locations)
        - At offsite storage (partner locations)
        """
        return self.search([
            ('is_records_container', '=', True),
            ('owner_id', '=', partner_id),
        ])
    
    @api.model
    def get_warehouse_inventory_by_customer(self, location_id=None):
        """
        Get containers grouped by customer (owner) for a specific warehouse location.
        
        Shows: "In THIS warehouse, we have inventory belonging to these customers"
        """
        domain = [('is_records_container', '=', True)]
        if location_id:
            domain.append(('location_id', 'child_of', location_id))
        
        quants = self.search(domain)
        
        # Group by owner (customer)
        by_customer = {}
        for quant in quants:
            customer = quant.owner_id
            if customer not in by_customer:
                by_customer[customer] = self.env['stock.quant']
            by_customer[customer] |= quant
        
        return by_customer
    
    # ============================================================================
    # ACTIONS
    # ============================================================================
    def action_view_documents(self):
        """View documents within this container"""
        self.ensure_one()
        return {
            'name': _('Documents in Container'),
            'type': 'ir.actions.act_window',
            'res_model': 'records.document',
            'view_mode': 'tree,form',
            'domain': [('quant_id', '=', self.id)],
            'context': {'default_quant_id': self.id},
        }
    
    def action_schedule_destruction(self):
        """Schedule container for destruction"""
        self.ensure_one()
        if not self.is_due_for_destruction:
            raise UserError(_(
                'This container is not yet due for destruction. '
                'Destruction due date: %s'
            ) % self.destruction_due_date)
        
        self.container_state = 'pending_destruction'
        self.message_post(
            body=_('Container scheduled for destruction by %s') % self.env.user.name
        )
    
    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('is_records_container', 'owner_id')
    def _check_records_container_owner(self):
        """Records containers MUST have an owner (customer)"""
        for quant in self:
            if quant.is_records_container and not quant.owner_id:
                raise ValidationError(_(
                    'Records containers must have an owner (customer). '
                    'The owner_id field tracks which customer owns this inventory, '
                    'even when stored in your warehouse.'
                ))
