from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)

class ShreddingServiceBin(models.Model):
    """
    Represents a physical shredding service bin with detailed business logic.

    This model manages shredding bins, tracks their lifecycle, and handles
    service events such as tipping, pickup, and maintenance. It integrates with
    billing, work orders, and NAID compliance audit logs.

    Key Features:
    - Barcode-based identification and validation
    - Automatic or manual bin size determination with weight and volume capacities
    - Tracks service events and calculates billing charges
    - Supports multiple service events per billing period
    - Integrates with work orders for cross-departmental tracking
    - Provides NAID-compliant audit logs for all bin-related activities

    Business Rules:
    - Barcodes must be exactly 10 digits and unique across all bins
    - Bin size is determined from the barcode unless manual override is enabled
    - Each service event generates a billable charge based on base rates
    - Bins can be serviced multiple times per day, with each service tracked

    This model is critical for managing shredding services and ensuring compliance
    with NAID AAA standards.
    """

    _name = 'shredding.service.bin'
    _description = 'Shredding Service Bin - Real Business Logic'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'last_service_date desc, barcode'
    _rec_name = 'display_name'

    # ============================================================================
    # CORE IDENTIFICATION
    # ============================================================================
    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(default=10, help="Display sequence")

    barcode = fields.Char(
        string="Barcode",
        required=True,
        index=True,
        tracking=True,
        help="Unique 10-digit barcode for bin identification"
    )

    current_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Current Customer Location",
        tracking=True,
        help="Customer location where this bin is currently placed (bins belong to our company)"
    )

    current_department_id = fields.Many2one(
        comodel_name='records.department',
        string="Current Department",
        tracking=True,
        help="Specific department where bin is currently located"
    )

    last_scan_location_id = fields.Many2one(
        comodel_name='records.location',
        string="Last Scan Location",
        tracking=True,
        help="Location where bin was last scanned/serviced"
    )

    last_scan_customer_id = fields.Many2one(
        comodel_name='res.partner',
        string="Last Scan Customer",
        tracking=True,
        help="Customer where bin was last scanned for service"
    )

    # ============================================================================
    # BIN SPECIFICATIONS (Barcode + Manual Override)
    # ============================================================================
    bin_size = fields.Selection([
        ('23', '23 Gallon Shredinator'),
        ('32g', '32 Gallon Bin'),
        ('32c', '32 Gallon Console'),
        ('64', '64 Gallon Bin'),
        ('96', '96 Gallon Bin'),
    ], string="Bin Size",
       compute='_compute_bin_specifications',
       store=True,
       readonly=False,
       tracking=True,
       help="Determined from barcode or manually selected if barcode unreadable")

    manual_size_override = fields.Boolean(
        string="Manual Size Override",
        default=False,
        help="Check this to manually select bin size when barcode is unreadable"
    )

    barcode_scan_status = fields.Selection([
        ('valid', 'Valid Scan'),
        ('invalid_characters', 'Invalid Characters (contains %, etc.)'),
        ('wrong_length', 'Wrong Length'),
        ('manual_entry', 'Manual Entry'),
        ('unreadable', 'Unreadable - Manual Override')
    ], string="Barcode Scan Status",
       compute='_compute_barcode_validation',
       store=True,
       help="Status of barcode scan validation")

    weight_capacity_lbs = fields.Float(
        string="Weight Capacity (lbs)",
        compute='_compute_bin_specifications',
        store=True,
        help="Maximum weight capacity based on bin size"
    )

    estimated_weight_per_service = fields.Float(
        string="Estimated Weight per Service (lbs)",
        compute='_compute_estimated_weights',
        store=True,
        help="Estimated weight from base rates per service event"
    )

    volume_capacity_cf = fields.Float(
        string="Volume Capacity (CF)",
        compute='_compute_bin_specifications',
        store=True,
        help="Physical volume capacity in cubic feet"
    )

    # ============================================================================
    # SERVICE EVENT TRACKING (Multiple Tips Per Day)
    # ============================================================================
    current_fill_level = fields.Selection([
        ('0', 'Empty (0%)'),
        ('25', 'Quarter Full (25%)'),
        ('50', 'Half Full (50%)'),
        ('75', 'Three-Quarters Full (75%)'),
        ('100', 'Full (100%)')
    ], string="Current Fill Level", default='0', tracking=True)

    last_service_date = fields.Datetime(
        string="Last Service Date",
        tracking=True,
        help="When this bin was last serviced/tipped"
    )

    total_services_count = fields.Integer(
        string="Total Services (All Time)",
        compute='_compute_service_statistics',
        store=True,
        help="Total number of times this bin has been serviced"
    )

    current_period_services = fields.Integer(
        string="Services This Period",
        compute='_compute_service_statistics',
        store=True,
        help="Number of services in current billing period"
    )

    # ============================================================================
    # WORK ORDER RELATIONSHIPS (Cross Work Order Support)
    # ============================================================================
    service_event_ids = fields.One2many(
        comodel_name='shredding.service.event',
        inverse_name='bin_id',
        string="Service Events",
        help="All service events for this bin across all work orders"
    )

    current_work_order_id = fields.Many2one(
        comodel_name='project.task',
        string="Current Work Order",
        help="Current work order this bin is assigned to"
    )

    # ============================================================================
    # BILLING INTEGRATION
    # ============================================================================
    base_rate_per_service = fields.Monetary(
        string="Base Rate per Service",
        compute='_compute_billing_rates',
        store=True,
        currency_field='currency_id',
        help="Base rate charged per service event from base rates"
    )

    currency_id = fields.Many2one(
        comodel_name='res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # STATUS AND LIFECYCLE
    # ============================================================================
    status = fields.Selection([
        ('available', 'Available'),
        ('in_service', 'In Service'),
        ('full', 'Full - Ready for Pickup'),
        ('in_transit', 'In Transit'),
        ('being_serviced', 'Being Serviced'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired')
    ], string="Status", default='available', tracking=True)

    location_id = fields.Many2one(
        comodel_name='records.location',
        string="Current Location",
        tracking=True,
        help="Current physical location of the bin"
    )

    # ============================================================================
    # COMPUTED DISPLAY FIELDS
    # ============================================================================
    display_name = fields.Char(
        compute='_compute_display_name',
        store=True,
        help="Human readable bin identification"
    )

    service_summary = fields.Text(
        compute='_compute_service_summary',
        string="Service Summary",
        help="Summary of recent service activity"
    )

    # ============================================================================
    # CORE COMPUTE METHODS
    # ============================================================================
    @api.depends('barcode')
    def _compute_barcode_validation(self):
        """Validate barcode scan and detect issues."""
        for record in self:
            if not record.barcode:
                record.barcode_scan_status = 'manual_entry'
                continue

            barcode_clean = record.barcode.strip()

            # Check for invalid characters (% symbol, etc.)
            if '%' in barcode_clean or not barcode_clean.replace('-', '').replace(' ', '').isalnum():
                record.barcode_scan_status = 'invalid_characters'
                continue

            # Check length
            if len(barcode_clean) != 10:
                record.barcode_scan_status = 'wrong_length'
                continue

            # Check if all digits (valid scan)
            if barcode_clean.isdigit():
                record.barcode_scan_status = 'valid'
            else:
                record.barcode_scan_status = 'manual_entry'

    @api.depends('barcode', 'manual_size_override', 'barcode_scan_status')
    def _compute_bin_specifications(self):
        """
        Determine bin size and specifications from barcode or manual selection.
        Business Rule: Only use barcode if scan is valid, otherwise require manual selection
        """
        for record in self:
            # If manual override is enabled, don't auto-compute
            if record.manual_size_override:
                if not record.bin_size:
                    record.bin_size = '32g'  # Default to 32 gallon bin
                # Keep existing specifications based on current bin_size
                record._update_specifications_from_size()
                continue

            if not record.barcode or record.barcode_scan_status != 'valid':
                # Invalid or no barcode - set defaults and require manual selection
                record.bin_size = '32g'  # Default to 32 gallon bin
                record.weight_capacity_lbs = 125.0
                record.volume_capacity_cf = 32/7.48  # ~4.28 CF
                continue

            # Check if barcode exists in barcode.product system
            barcode_product = self.env['barcode.product'].search([
                ('barcode', '=', record.barcode),
                ('product_category', '=', 'shred_bin')
            ], limit=1)

            if barcode_product and hasattr(barcode_product, 'container_type') and barcode_product.container_type:
                # Map barcode product types to actual bin sizes
                specs = {
                    'type_01': {'size': '23', 'weight': 60, 'volume': 23/7.48},    # 23 gallon
                    'type_02': {'size': '32g', 'weight': 125, 'volume': 32/7.48},  # 32 gallon bin
                    'type_03': {'size': '32c', 'weight': 90, 'volume': 32/7.48},   # 32 gallon console
                    'type_04': {'size': '64', 'weight': 240, 'volume': 64/7.48},   # 64 gallon
                    'type_06': {'size': '96', 'weight': 340, 'volume': 96/7.48},   # 96 gallon
                }
                spec = specs.get(barcode_product.container_type, specs['type_02'])
                record.bin_size = spec['size']
                record.weight_capacity_lbs = spec['weight']
                record.volume_capacity_cf = spec['volume']
            else:
                # No barcode product found - require manual selection
                record.bin_size = '32g'  # Default to 32 gallon bin
                record.weight_capacity_lbs = 125.0
                record.volume_capacity_cf = 32/7.48  # ~4.28 CF

    def _update_specifications_from_size(self):
        """Update weight and volume specifications based on selected bin size."""
        self.ensure_one()
        # Use actual bin capacities from shred_bin model
        specs = {
            '23': {'weight': 60, 'volume': 23/7.48},    # 23 gallon = ~3.07 CF
            '32g': {'weight': 125, 'volume': 32/7.48},  # 32 gallon = ~4.28 CF
            '32c': {'weight': 90, 'volume': 32/7.48},   # 32 gallon console = ~4.28 CF
            '64': {'weight': 240, 'volume': 64/7.48},   # 64 gallon = ~8.56 CF
            '96': {'weight': 340, 'volume': 96/7.48},   # 96 gallon = ~12.83 CF
        }
        spec = specs.get(self.bin_size, specs['32g'])  # Default to 32g if not found
        self.weight_capacity_lbs = spec['weight']
        self.volume_capacity_cf = spec['volume']

    @api.depends('bin_size', 'weight_capacity_lbs')
    def _compute_estimated_weights(self):
        """Calculate estimated weight per service from base rates."""
        for record in self:
            if not record.weight_capacity_lbs:
                record.estimated_weight_per_service = 0.0
                continue

            # Get destruction base rate for weight estimation
            base_rate = self.env['base.rates'].search([
                ('rate_type', '=', 'destruction'),
                ('active', '=', True),
                ('effective_date', '<=', fields.Date.today()),
                '|', ('expiry_date', '=', False), ('expiry_date', '>', fields.Date.today())
            ], limit=1)

            if base_rate and hasattr(base_rate, 'unit_type') and base_rate.unit_type == 'per_item':
                # Estimate 60-80% capacity utilization per service
                capacity_factor = 0.7  # 70% average fill
                record.estimated_weight_per_service = record.weight_capacity_lbs * capacity_factor
            else:
                # Fallback estimation
                record.estimated_weight_per_service = record.weight_capacity_lbs * 0.7

    @api.depends('bin_size')
    def _compute_billing_rates(self):
        """Calculate billing rate per service from base rates."""
        for record in self:
            # Get current destruction rate
            base_rate = self.env['base.rates'].search([
                ('rate_type', '=', 'destruction'),
                ('active', '=', True),
                ('effective_date', '<=', fields.Date.today()),
                '|', ('expiry_date', '=', False), ('expiry_date', '>', fields.Date.today())
            ], order='effective_date desc', limit=1)

            if base_rate and hasattr(base_rate, 'unit_type'):
                if base_rate.unit_type == 'per_item':
                    record.base_rate_per_service = base_rate.base_rate
                elif base_rate.unit_type == 'per_box':
                    # Convert to per service based on bin size
                    size_multiplier = {
                        '23': 0.6,   # 23 gallon - smaller rate
                        '32g': 1.0,  # 32 gallon bin - base rate
                        '32c': 0.8,  # 32 gallon console - slightly less due to design
                        '64': 1.8,   # 64 gallon - larger rate
                        '96': 2.5,   # 96 gallon - highest rate
                    }.get(record.bin_size, 1.0)
                    record.base_rate_per_service = base_rate.base_rate * size_multiplier
                else:
                    record.base_rate_per_service = base_rate.base_rate
            else:
                # Fallback rates based on actual bin sizes
                fallback_rates = {
                    '23': 20.00,   # 23 gallon Shredinator
                    '32g': 35.00,  # 32 gallon bin
                    '32c': 30.00,  # 32 gallon console
                    '64': 65.00,   # 64 gallon bin
                    '96': 95.00,   # 96 gallon bin
                }
                record.base_rate_per_service = fallback_rates.get(record.bin_size, 35.00)

    @api.depends('service_event_ids')
    def _compute_service_statistics(self):
        """Compute service statistics from service events."""
        current_billing_cutoff = datetime.now() - timedelta(days=30)

        for record in self:
            if not record.service_event_ids:
                record.total_services_count = 0
                record.current_period_services = 0
                continue

            record.total_services_count = len(record.service_event_ids)

            # Current billing period (last 30 days)
            current_period_events = record.service_event_ids.filtered(
                lambda e: e.service_date and e.service_date >= current_billing_cutoff
            )
            record.current_period_services = len(current_period_events)

    @api.depends('barcode', 'bin_size', 'current_period_services', 'current_customer_id')
    def _compute_display_name(self):
        """Generate display name with service count and location."""
        for record in self:
            if record.barcode and record.bin_size:
                size_label = dict(record._fields['bin_size'].selection).get(record.bin_size, 'Unknown')
                tips_text = "" if record.current_period_services == 0 else _(" (%s tips)") % record.current_period_services

                # Add location info if available
                location_text = ""
                if record.current_customer_id:
                    location_text = _(" @ %s") % record.current_customer_id.name
                elif record.last_scan_customer_id:
                    location_text = _(" (last @ %s)") % record.last_scan_customer_id.name

                record.display_name = _("Bin %s - %s%s%s") % (record.barcode, size_label, tips_text, location_text)
            else:
                record.display_name = record.barcode or _("New Bin")

    @api.depends('service_event_ids', 'last_service_date', 'current_period_services')
    def _compute_service_summary(self):
        """Generate service summary text."""
        for record in self:
            if not record.service_event_ids:
                record.service_summary = _("No service events recorded")
                continue

            summary_parts = [
                _("Total Services: %s") % record.total_services_count,
                _("This Period: %s") % record.current_period_services
            ]

            if record.last_service_date:
                days_since = (datetime.now() - record.last_service_date).days
                summary_parts.append(_("Last Service: %s days ago") % days_since)

            record.service_summary = " | ".join(summary_parts)

    # ============================================================================
    # BUSINESS METHODS - Barcode Handling
    # ============================================================================
    def action_fix_barcode_scan(self):
        """Action to fix a bad barcode scan."""
        self.ensure_one()

        if self.barcode_scan_status == 'invalid_characters':
            # Clean up common scan issues
            cleaned_barcode = self.barcode.replace('%', '').replace(' ', '').replace('-', '')
            if len(cleaned_barcode) == 10 and cleaned_barcode.isdigit():
                self.barcode = cleaned_barcode
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'message': _('Barcode cleaned and corrected to: %s') % cleaned_barcode,
                        'type': 'success',
                    }
                }

        # If can't auto-fix, open dialog for manual entry
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.bin.barcode.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_bin_id': self.id,
                'default_current_barcode': self.barcode,
                'default_scan_issue': self.barcode_scan_status,
            },
            'name': _('Fix Barcode Scan'),
        }

    def action_enable_manual_override(self):
        """Enable manual size selection when barcode is unreadable."""
        self.ensure_one()
        self.write({
            'manual_size_override': True,
            'barcode_scan_status': 'unreadable'
        })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Manual size override enabled. Please select the correct bin size.'),
                'type': 'warning',
            }
        }

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('barcode')
    def _onchange_barcode(self):
        """Validate barcode on change and alert for issues."""
        if self.barcode:
            self.barcode = self.barcode.strip().upper()

            # Check for scan issues
            if '%' in self.barcode:
                return {
                    'warning': {
                        'title': _('Bad Barcode Scan'),
                        'message': _('The barcode contains invalid characters (%%). This indicates a bad scan. Please re-scan or manually enter the barcode.')
                    }
                }
            if len(self.barcode.strip()) != 10:
                return {
                    'warning': {
                        'title': _('Invalid Barcode Length'),
                        'message': _('Shred bin barcodes must be exactly 10 digits. Current length: %s. Please check the barcode.') % len(self.barcode.strip())
                    }
                }
            if not self.barcode.strip().isdigit():
                return {
                    'warning': {
                        'title': _('Invalid Barcode Format'),
                        'message': _('Shredding bin barcodes must contain only digits. Please check the barcode or enable manual override.')
                    }
                }

    @api.onchange('manual_size_override')
    def _onchange_manual_size_override(self):
        """Handle manual size override toggle."""
        if self.manual_size_override:
            if not self.bin_size:
                self.bin_size = '32g'  # Default to 32 gallon bin
        else:
            # Re-compute from barcode when override is disabled
            self._compute_bin_specifications()

    @api.onchange('bin_size')
    def _onchange_bin_size(self):
        """Update specifications when bin size is manually changed."""
        if self.manual_size_override and self.bin_size:
            self._update_specifications_from_size()

    # ============================================================================
    # SERVICE EVENT MANAGEMENT METHODS
    # ============================================================================
    def action_create_service_event(self, customer_id=None, location_id=None):
        """Create a new service event for this bin at specified location."""
        self.ensure_one()

        if self.status not in ['available', 'in_service', 'full']:
            raise UserError(_("Cannot service bin in current status: %s") % self.status)

        # Update location tracking from scan
        update_vals = {}
        if customer_id:
            update_vals['last_scan_customer_id'] = customer_id
            # If bin doesn't have current customer, set it
            if not self.current_customer_id:
                update_vals['current_customer_id'] = customer_id

        if location_id:
            update_vals['last_scan_location_id'] = location_id

        # Create service event
        service_event = self.env['shredding.service.event'].create({
            'bin_id': self.id,
            'work_order_id': self.current_work_order_id.id if self.current_work_order_id else False,
            'service_date': fields.Datetime.now(),
            'service_type': 'tip',
            'actual_weight_lbs': self.estimated_weight_per_service,
            'billable_amount': self.base_rate_per_service,
            'performed_by_id': self.env.user.id,
            'service_customer_id': customer_id,
            'service_location_id': location_id,
        })

        # Update bin status and location info
        update_vals.update({
            'last_service_date': fields.Datetime.now(),
            'current_fill_level': '0',  # Reset to empty after service
            'status': 'available'
        })

        self.write(update_vals)

        # Create audit log for NAID compliance
        customer_name = self.env['res.partner'].browse(customer_id).name if customer_id else 'Unknown'
        self._create_service_audit_log('bin_serviced',
            _("Bin serviced at %s - Service Event %s created") % (customer_name, service_event.id))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'shredding.service.event',
            'res_id': service_event.id,
            'view_mode': 'form',
            'target': 'current',
            'name': _('Service Event Created'),
        }

    # ============================================================================
    # UTILITY AND REPORTING METHODS
    # ============================================================================
    def get_billing_line_items(self, date_from=None, date_to=None):
        """Get billing line items for this bin within date range."""
        self.ensure_one()

        domain = [('bin_id', '=', self.id)]
        if date_from:
            domain.append(('service_date', '>=', date_from))
        if date_to:
            domain.append(('service_date', '<=', date_to))

        service_events = self.env['shredding.service.event'].search(domain)

        line_items = []
        for event in service_events:
            line_items.append({
                'date': event.service_date,
                'description': _("Bin %s - %s Service") % (self.barcode, event.service_type.title()),
                'quantity': 1,
                'unit_price': event.billable_amount,
                'total': event.billable_amount,
                'weight_lbs': event.actual_weight_lbs,
                'work_order': event.work_order_id.name if event.work_order_id else '',
            })

        return line_items

    def get_service_frequency_analysis(self):
        """Analyze service frequency for this bin."""
        self.ensure_one()

        if not self.service_event_ids:
            return {'frequency': 'no_data', 'average_days': 0, 'recommendation': 'Monitor usage'}

        # Calculate average days between services
        events = self.service_event_ids.sorted('service_date')
        if len(events) < 2:
            return {'frequency': 'insufficient_data', 'average_days': 0, 'recommendation': 'Need more data'}

        total_days = 0
        for i in range(1, len(events)):
            days_between = (events[i].service_date - events[i-1].service_date).days
            total_days += days_between

        average_days = total_days / (len(events) - 1)

        if average_days <= 7:
            frequency = 'very_high'
            recommendation = 'Consider upsizing bin or additional bins'
        elif average_days <= 14:
            frequency = 'high'
            recommendation = 'Monitor closely, may need additional capacity'
        elif average_days <= 30:
            frequency = 'normal'
            recommendation = 'Current size appropriate'
        else:
            frequency = 'low'
            recommendation = 'Consider downsizing if pattern continues'

        return {
            'frequency': frequency,
            'average_days': round(average_days, 1),
            'recommendation': recommendation,
            'total_events': len(events)
        }

    # ============================================================================
    # NAID COMPLIANCE AND AUDIT
    # ============================================================================
    def _create_service_audit_log(self, event_type, description):
        """Create NAID compliance audit log."""
        try:
            if 'naid.audit.log' in self.env:
                self.env['naid.audit.log'].create({
                    'event_type': event_type,
                    'description': description,
                    'user_id': self.env.user.id,
                    'res_model': self._name,
                    'res_id': self.id,
                    'event_date': fields.Datetime.now(),
                    'partner_id': self.current_customer_id.id if self.current_customer_id else False,
                })
        except Exception as e:
            _logger.warning("Failed to create audit log: %s", str(e))

    # ============================================================================
    # CONSTRAINTS AND VALIDATION
    # ============================================================================
    @api.constrains('barcode', 'manual_size_override')
    def _check_barcode_format(self):
        """Validate barcode format for shred bins."""
        for record in self:
            if record.barcode and not record.manual_size_override:
                barcode_clean = record.barcode.strip()

                # Check for invalid characters that indicate bad scan
                if '%' in barcode_clean or not barcode_clean.replace('-', '').replace(' ', '').isalnum():
                    raise ValidationError(_(
                        "Bad barcode scan detected (contains %%). Please fix the scan or enable manual override. Current: %s"
                    ) % record.barcode)

                # Only enforce strict format if not using manual override
                if len(barcode_clean) != 10:
                    raise ValidationError(_(
                        "Shredding bin barcodes must be exactly 10 digits long. Current: %s (length: %s). Enable manual override if barcode is unreadable."
                    ) % (record.barcode, len(barcode_clean)))

                if not barcode_clean.isdigit():
                    raise ValidationError(_(
                        "Shredding bin barcodes must contain only digits. Current: %s. Enable manual override if barcode is unreadable."
                    ) % record.barcode)

            # If manual override is enabled, require bin size to be set
            if record.manual_size_override and not record.bin_size:
                raise ValidationError(_("When using manual override, you must select a bin size."))

    @api.constrains('barcode')
    def _check_barcode_unique(self):
        """Ensure barcode is unique across all bins (company-wide since we own all bins)."""
        for record in self:
            if record.barcode:
                existing = self.search([
                    ('barcode', '=', record.barcode),
                    ('id', '!=', record.id)
                ])
                if existing:
                    raise ValidationError(_(
                        "Barcode '%s' already exists for another bin. Each bin must have a unique barcode company-wide."
                    ) % record.barcode)

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to initialize bin properly."""
        bins = super().create(vals_list)
        for bin_record in bins:
            customer_name = bin_record.current_customer_id.name if bin_record.current_customer_id else 'Unassigned'
            bin_record._create_service_audit_log('bin_created',
                _("Shredding bin created: %s - placed at %s") % (bin_record.barcode, customer_name))
        return bins
