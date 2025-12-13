from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShreddingServiceEvent(models.Model):
    """
    Tracks individual service events for bins.
    
    BILLING LOGIC:
    - A billable event = one full bin's contents collected (not number of scans)
    - TIP: 1 scan = 1 billable (bin emptied in place)
    - SWAP: 2 scans (OUT + IN) = 1 billable (old full bin picked up, new empty left)
    - The "swap_in" scan is just inventory movement, NOT billable
    
    Scan Types:
    - tip: Bin emptied and returned to same location (BILLABLE)
    - swap_out: Full bin picked up for processing (BILLABLE - the actual service)
    - swap_in: Empty bin placed at location (NOT billable - just inventory)
    - pickup: Bin removed entirely from location (context-dependent)
    - delivery: Bin delivered to new location (NOT billable - just placement)
    """

    _name = 'shredding.service.event'
    _description = 'Shredding Service Event'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'service_date desc'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE FIELDS
    # ============================================================================
    bin_id = fields.Many2one(
        comodel_name='shredding.service.bin',
        string="Bin",
        required=True,
        ondelete='cascade',
        index=True
    )

    work_order_id = fields.Many2one(
        comodel_name='project.task',
        string="FSM Task",
        help="FSM task this service event is part of (for scheduling)"
    )
    shredding_work_order_id = fields.Many2one(
        comodel_name='work.order.shredding',
        string="Shredding Work Order",
        help="Shredding work order this service event is part of",
        index=True
    )

    service_date = fields.Datetime(
        string="Service Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )

    service_type = fields.Selection([
        ('tip', 'Tip/Empty'),           # Bin emptied in place - BILLABLE
        ('swap_out', 'Swap Out'),       # Full bin picked up - BILLABLE (the service)
        ('swap_in', 'Swap In'),         # Empty bin placed - NOT billable (just inventory)
        ('pickup', 'Pickup'),           # Bin removed from location
        ('delivery', 'Delivery'),       # Bin delivered to location - NOT billable
        ('maintenance', 'Maintenance'), # Maintenance scan
    ], string="Service Type", default='tip', required=True, tracking=True)

    # ============================================================================
    # BILLING CONTROL
    # ============================================================================
    is_billable = fields.Boolean(
        string="Billable",
        compute='_compute_is_billable',
        store=True,
        help="Whether this service event should generate a billing charge"
    )
    
    # Link swap_in to its corresponding swap_out for billing pairing
    swap_pair_id = fields.Many2one(
        comodel_name='shredding.service.event',
        string="Swap Pair",
        help="For swap_in events, links to the corresponding swap_out event"
    )

    # ============================================================================
    # LOCATION TRACKING (Where Service Occurred)
    # ============================================================================
    service_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Customer",
        help="Customer location where service was performed"
    )

    service_location_id = fields.Many2one(
        comodel_name='stock.location',
        string="Service Location",
        help="Specific location where bin was serviced"
    )

    service_department_id = fields.Many2one(
        comodel_name='records.department',
        string="Service Department",
        help="Department where service was performed"
    )

    # ============================================================================
    # FILL LEVEL AT SERVICE (Technician Selection)
    # Default is FULL - technician only needs to change if bin was not full
    # ============================================================================
    fill_level_at_service = fields.Selection([
        ('100', 'Full (100%)'),
        ('75', 'Three-Quarters (75%)'),
        ('50', 'Half Full (50%)'),
        ('25', 'Quarter Full (25%)'),
        ('0', 'Empty (0%)')
    ], string="Fill Level at Service",
       default='100',
       required=True,
       tracking=True,
       help="Fill level when bin was serviced. Default is Full - technician only changes if different.")

    # ============================================================================
    # WEIGHT CALCULATIONS (Estimated vs Actual)
    # Estimated = Standard weight for bin size (always 100%)
    # Actual = Estimated × Fill Level % (captures real field conditions)
    # ============================================================================
    estimated_weight_lbs = fields.Float(
        string="Estimated Weight (lbs)",
        compute='_compute_weights',
        store=True,
        help="Standard weight for this bin size when full (100%)"
    )

    actual_weight_lbs = fields.Float(
        string="Actual Weight (lbs)",
        compute='_compute_weights',
        store=True,
        help="Calculated: Estimated Weight × Fill Level %. Reflects actual material serviced."
    )

    weight_variance_lbs = fields.Float(
        string="Weight Variance (lbs)",
        compute='_compute_weights',
        store=True,
        help="Difference between estimated and actual weight (negative = less than expected)"
    )

    # ============================================================================
    # BILLING
    # ============================================================================
    billable_amount = fields.Monetary(
        string="Billable Amount",
        currency_field='currency_id',
        compute='_compute_billable_amount',
        store=True,
        readonly=False,
        tracking=True,
        help="Calculated from bin size rate; only applies to billable events"
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        related='bin_id.currency_id'
    )

    # ============================================================================
    # SERVICE DETAILS
    # ============================================================================
    performed_by_id = fields.Many2one(
        comodel_name='res.users',
        string="Performed By",
        required=True,
        default=lambda self: self.env.user
    )

    notes = fields.Text(string="Service Notes")

    # ============================================================================
    # COMPUTE METHODS FOR WEIGHT CALCULATIONS
    # ============================================================================
    @api.depends('bin_id', 'bin_id.weight_capacity_lbs', 'fill_level_at_service')
    def _compute_weights(self):
        """
        Calculate estimated and actual weights based on bin size and fill level.
        
        Estimated Weight = Standard weight for bin size (100% full)
        Actual Weight = Estimated × Fill Level %
        
        Example: 32g Console = 90 lbs full
        - Full (100%): Actual = 90 lbs
        - Half (50%): Actual = 45 lbs  
        - Quarter (25%): Actual = 22.5 lbs
        """
        for record in self:
            if not record.bin_id:
                record.estimated_weight_lbs = 0.0
                record.actual_weight_lbs = 0.0
                record.weight_variance_lbs = 0.0
                continue

            # Estimated = Standard weight for bin size (always 100%)
            record.estimated_weight_lbs = record.bin_id.weight_capacity_lbs or 0.0

            # Actual = Estimated × Fill Level %
            fill_pct = int(record.fill_level_at_service or '100') / 100.0
            record.actual_weight_lbs = record.estimated_weight_lbs * fill_pct

            # Variance = Actual - Estimated (negative = less than expected)
            record.weight_variance_lbs = record.actual_weight_lbs - record.estimated_weight_lbs

    # ============================================================================
    # COMPUTE METHODS FOR BILLING
    # ============================================================================
    @api.depends('service_type')
    def _compute_is_billable(self):
        """
        Determine if this service event should generate a billing charge.
        
        BILLABLE:
        - tip: Bin emptied in place
        - swap_out: Full bin picked up (the actual "service" in a swap)
        
        NOT BILLABLE:
        - swap_in: Empty bin placed (just inventory tracking)
        - delivery: Bin delivered to new location
        - maintenance: Internal maintenance scan
        """
        for record in self:
            record.is_billable = record.service_type in ('tip', 'swap_out')

    @api.depends('is_billable', 'bin_id', 'bin_id.base_rate_per_service')
    def _compute_billable_amount(self):
        """
        Calculate billable amount based on bin size rate.
        Only billable events get an amount; others are $0.
        """
        for record in self:
            if record.is_billable and record.bin_id:
                record.billable_amount = record.bin_id.base_rate_per_service or 0.0
            else:
                record.billable_amount = 0.0

    # ============================================================================
    # BILLING INTEGRATION
    # ============================================================================
    invoice_line_id = fields.Many2one(
        comodel_name='account.move.line',
        string="Invoice Line",
        readonly=True,
        help="Generated invoice line for this service event"
    )

    billing_status = fields.Selection([
        ('pending', 'Pending Billing'),
        ('billed', 'Billed'),
        ('paid', 'Paid')
    ], string="Billing Status", default='pending', tracking=True)

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    display_name = fields.Char(compute='_compute_display_name', store=True)
    customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Customer Location",
        compute='_compute_customer_fields',
        store=True,
        help="Customer location where service was performed (for reporting)"
    )

    @api.depends('bin_id')
    def _compute_customer_fields(self):
        """Compute customer field for backward compatibility."""
        for record in self:
            if record.service_customer_id:
                record.customer_id = record.service_customer_id.id
            elif record.bin_id and record.bin_id.current_customer_id:
                record.customer_id = record.bin_id.current_customer_id.id
            else:
                record.customer_id = False

    @api.depends('bin_id', 'service_date', 'service_type', 'service_customer_id')
    def _compute_display_name(self):
        """Generate display name for service event with location info."""
        for record in self:
            if record.bin_id and record.service_date:
                date_str = record.service_date.strftime('%m/%d %H:%M') if record.service_date else 'No Date'

                # Add customer location if available (fixed translation formatting)
                location_text = ""
                if record.service_customer_id:
                    location_text = _(" @ %s") % record.service_customer_id.name
                elif record.bin_id.current_customer_id:
                    location_text = _(" @ %s") % record.bin_id.current_customer_id.name

                record.display_name = _("Bin %s - %s (%s)%s") % (
                    record.bin_id.barcode,
                    record.service_type.title(),
                    date_str,
                    location_text
                )
            else:
                record.display_name = _("Service Event")

    # ============================================================================
    # BUSINESS METHODS
    # ============================================================================
    def action_create_invoice_line(self):
        """Create invoice line for this service event."""
        self.ensure_one()

        if not self.is_billable:
            raise UserError(_("This service event is not billable (type: %s)") % self.service_type)

        if self.invoice_line_id:
            raise UserError(_("Invoice line already exists for this service event"))

        if not self.service_customer_id and not self.bin_id.current_customer_id:
            raise UserError(_("No customer location specified for billing"))

        # This would integrate with accounting module to create invoice lines
        # For now, just mark as billed
        self.write({
            'billing_status': 'billed'
        })

        return True

    @api.model
    def create_tip_event(self, bin_id, customer_id=None, work_order_id=None, shredding_work_order_id=None, notes=None):
        """
        Create a TIP service event - bin emptied in place.
        
        BILLABLE: Yes (1 scan = 1 charge)
        
        Args:
            bin_id: shredding.service.bin record or ID
            customer_id: res.partner ID where service occurred
            work_order_id: project.task FSM work order ID
            shredding_work_order_id: work.order.shredding ID
            notes: Optional service notes
        
        Returns:
            shredding.service.event record
        """
        bin_record = self.env['shredding.service.bin'].browse(bin_id) if isinstance(bin_id, int) else bin_id
        
        event = self.create({
            'bin_id': bin_record.id,
            'service_type': 'tip',
            'service_customer_id': customer_id or bin_record.current_customer_id.id,
            'work_order_id': work_order_id,
            'shredding_work_order_id': shredding_work_order_id,
            'notes': notes,
        })
        
        # Update bin status
        bin_record.write({
            'current_fill_level': '0',  # Now empty
            'last_service_date': event.service_date,
        })
        
        return event

    @api.model
    def create_swap_events(self, old_bin_id, new_bin_id, customer_id, work_order_id=None, shredding_work_order_id=None, notes=None):
        """
        Create a SWAP - pick up full bin, leave empty bin.
        
        BILLABLE: 1 charge total (for the swap_out, not the swap_in)
        
        This creates TWO events:
        1. swap_out on old_bin (BILLABLE) - full bin picked up
        2. swap_in on new_bin (NOT billable) - empty bin placed
        
        Args:
            old_bin_id: shredding.service.bin being picked up (full)
            new_bin_id: shredding.service.bin being left behind (empty)
            customer_id: res.partner ID where swap occurred
            work_order_id: project.task FSM work order ID
            shredding_work_order_id: work.order.shredding ID
            notes: Optional service notes
        
        Returns:
            tuple(swap_out_event, swap_in_event)
        """
        old_bin = self.env['shredding.service.bin'].browse(old_bin_id) if isinstance(old_bin_id, int) else old_bin_id
        new_bin = self.env['shredding.service.bin'].browse(new_bin_id) if isinstance(new_bin_id, int) else new_bin_id
        
        # 1. Create swap_out event (BILLABLE - this is the actual service)
        swap_out = self.create({
            'bin_id': old_bin.id,
            'service_type': 'swap_out',
            'service_customer_id': customer_id,
            'work_order_id': work_order_id,
            'shredding_work_order_id': shredding_work_order_id,
            'notes': notes or _("Picked up full bin, replaced with %s") % new_bin.barcode,
        })
        
        # Update old bin - now in transit back to warehouse
        old_bin.write({
            'status': 'in_transit',
            'current_customer_id': False,
            'current_fill_level': '100',  # Still full until processed
        })
        old_bin._record_movement('in_transit', reason=_("Swap out - picked up from customer"))
        
        # 2. Create swap_in event (NOT billable - just inventory tracking)
        swap_in = self.create({
            'bin_id': new_bin.id,
            'service_type': 'swap_in',
            'service_customer_id': customer_id,
            'work_order_id': work_order_id,
            'shredding_work_order_id': shredding_work_order_id,
            'swap_pair_id': swap_out.id,  # Link to the billable event
            'notes': notes or _("Placed empty bin, replacing %s") % old_bin.barcode,
        })
        
        # Update new bin - now in service at customer
        new_bin.write({
            'status': 'in_service',
            'current_customer_id': customer_id,
            'current_fill_level': '0',  # Empty
        })
        new_bin._record_movement('in_service', reason=_("Swap in - placed at customer"))
        
        return swap_out, swap_in

    @api.model
    def create_delivery_event(self, bin_id, customer_id, work_order_id=None, shredding_work_order_id=None, notes=None):
        """
        Create a DELIVERY event - new bin placed at customer (not a swap).
        
        BILLABLE: No (just placing equipment)
        
        Args:
            bin_id: shredding.service.bin being delivered
            customer_id: res.partner ID where bin is placed
            work_order_id: project.task FSM work order ID
            shredding_work_order_id: work.order.shredding ID
            notes: Optional notes
        
        Returns:
            shredding.service.event record
        """
        bin_record = self.env['shredding.service.bin'].browse(bin_id) if isinstance(bin_id, int) else bin_id
        
        event = self.create({
            'bin_id': bin_record.id,
            'service_type': 'delivery',
            'service_customer_id': customer_id,
            'work_order_id': work_order_id,
            'shredding_work_order_id': shredding_work_order_id,
            'notes': notes,
        })
        
        # Update bin status
        bin_record.write({
            'status': 'in_service',
            'current_customer_id': customer_id,
            'current_fill_level': '0',
        })
        bin_record._record_movement('in_service', reason=_("Delivered to customer"))
        
        return event

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to update bin statistics."""
        events = super().create(vals_list)
        for event in events:
            # Update bin's last service date
            if event.bin_id:
                event.bin_id.write({
                    'last_service_date': event.service_date
                })
        return events
