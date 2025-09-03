from odoo import models, fields, api, _
from odoo.exceptions import UserError


class ShreddingServiceEvent(models.Model):
    """
    Tracks individual service events for bins.
    Each event represents one "tip" or service action and creates billing charges.
    """

    _name = 'shredding.service.event'
    _description = 'Shredding Service Event (Tip)'
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
        string="Work Order",
        help="Work order this service event is part of"
    )

    service_date = fields.Datetime(
        string="Service Date",
        required=True,
        default=fields.Datetime.now,
        tracking=True
    )

    service_type = fields.Selection([
        ('tip', 'Tip/Empty'),
        ('pickup', 'Pickup'),
        ('exchange', 'Exchange'),
        ('maintenance', 'Maintenance')
    ], string="Service Type", default='tip', required=True, tracking=True)

    # ============================================================================
    # LOCATION TRACKING (Where Service Occurred)
    # ============================================================================
    service_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Service Customer",
        help="Customer location where service was performed"
    )

    service_location_id = fields.Many2one(
        comodel_name='records.location',
        string="Service Location",
        help="Specific location where bin was serviced"
    )

    service_department_id = fields.Many2one(
        comodel_name='records.department',
        string="Service Department",
        help="Department where service was performed"
    )

    # ============================================================================
    # WEIGHT AND BILLING
    # ============================================================================
    actual_weight_lbs = fields.Float(
        string="Actual Weight (lbs)",
        help="Actual weight of material serviced"
    )

    billable_amount = fields.Monetary(
        string="Billable Amount",
        currency_field='currency_id',
        required=True,
        tracking=True
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

                # Add customer location if available
                location_text = ""
                if record.service_customer_id:
                    location_text = _(" @ %s", record.service_customer_id.name)
                elif record.bin_id.current_customer_id:
                    location_text = _(" @ %s", record.bin_id.current_customer_id.name)

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
