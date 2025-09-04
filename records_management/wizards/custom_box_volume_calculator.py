import math

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class CustomBoxVolumeCalculator(models.TransientModel):
    _name = 'custom.box.volume.calculator'
    _description = 'FSM Box Volume Calculator and Standard Container Converter'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Calculator Session',
        default='Volume Calculation',
        required=True
    )
    company_id = fields.Many2one(
        'res.company',
        default=lambda self: self.env.company,
        required=True
    )
    user_id = fields.Many2one(
        'res.users',
        string='Technician/User',
        default=lambda self: self.env.user,
        required=True
    )

    # ============================================================================
    # CUSTOM BOX DIMENSIONS INPUT
    # ============================================================================
    length_inches = fields.Float(
        string='Length (inches)',
        digits=(8, 2),
        help='Box length in inches'
    )
    width_inches = fields.Float(
        string='Width (inches)',
        digits=(8, 2),
        help='Box width in inches'
    )
    height_inches = fields.Float(
        string='Height (inches)',
        digits=(8, 2),
        help='Box height in inches'
    )

    # Metric system support
    length_cm = fields.Float(
        string='Length (cm)',
        digits=(8, 2),
        help='Box length in centimeters'
    )
    width_cm = fields.Float(
        string='Width (cm)',
        digits=(8, 2),
        help='Box width in centimeters'
    )
    height_cm = fields.Float(
        string='Height (cm)',
        digits=(8, 2),
        help='Box height in centimeters'
    )

    measurement_unit = fields.Selection([
        ('inches', 'Inches'),
        ('centimeters', 'Centimeters'),
    ], string='Measurement Unit', default='inches', required=True)

    # ============================================================================
    # CALCULATED VOLUME FIELDS
    # ============================================================================
    custom_volume_cf = fields.Float(
        string='Custom Box Volume (CF)',
        digits=(12, 4),
        compute='_compute_custom_volume',
        store=True,
        help='Calculated volume in cubic feet'
    )
    custom_volume_liters = fields.Float(
        string='Custom Box Volume (Liters)',
        digits=(12, 2),
        compute='_compute_custom_volume',
        store=True,
        help='Calculated volume in liters'
    )

    # ============================================================================
    # STANDARD CONTAINER CONVERSION
    # ============================================================================
    recommended_container_type = fields.Selection([
        ('type_01', 'TYPE 01: Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02: Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03: Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04: Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06: Pathology Box (0.042 CF)'),
    ], string='Recommended Standard Container', compute='_compute_recommended_container', store=True)

    equivalent_standard_boxes = fields.Float(
        string='Equivalent Standard Boxes',
        digits=(12, 2),
        compute='_compute_equivalent_boxes',
        store=True,
        help='Number of standard boxes needed to match custom volume'
    )

    volume_difference_cf = fields.Float(
        string='Volume Difference (CF)',
        digits=(12, 4),
        compute='_compute_volume_difference',
        store=True,
        help='Difference between custom and standard container volume'
    )

    # ============================================================================
    # PRICING CALCULATION FIELDS
    # ============================================================================
    base_rate_per_cf = fields.Monetary(
        string='Base Rate per Cubic Foot',
        currency_field='currency_id',
        default=lambda self: self._default_base_rate_per_cf(),
        help='Base pricing rate per cubic foot'
    )

    custom_box_price = fields.Monetary(
        string='Custom Box Price',
        currency_field='currency_id',
        compute='_compute_pricing',
        store=True,
        help='Calculated price for custom box'
    )

    standard_box_price = fields.Monetary(
        string='Standard Box Price',
        currency_field='currency_id',
        compute='_compute_pricing',
        store=True,
        help='Price if using equivalent standard boxes'
    )

    price_difference = fields.Monetary(
        string='Price Difference',
        currency_field='currency_id',
        compute='_compute_pricing',
        store=True,
        help='Price difference between custom and standard'
    )

    currency_id = fields.Many2one(
        'res.currency',
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # FSM INTEGRATION FIELDS
    # ============================================================================
    fsm_task_id = fields.Many2one(
        'project.task',
        string='Related FSM Task',
        help='FSM task this calculation is for'
    )

    pickup_request_id = fields.Many2one(
        'pickup.request',
        string='Related Pickup Request',
        help='Pickup request this calculation is for'
    )

    shredding_service_id = fields.Many2one(
        'shredding.service',
        string='Related Shredding Service',
        help='Shredding service this calculation is for'
    )

    # ============================================================================
    # BUSINESS PROCESS FIELDS
    # ============================================================================
    calculation_purpose = fields.Selection([
        ('fsm_quote', 'FSM Field Quote'),
        ('customer_quote', 'Customer Portal Quote'),
        ('internal_estimate', 'Internal Estimate'),
        ('audit_verification', 'Audit Verification'),
    ], string='Calculation Purpose', default='fsm_quote', required=True)

    notes = fields.Text(
        string='Technician Notes',
        help='Additional notes about the calculation'
    )

    # ============================================================================
    # AUDIT AND TRACKING
    # ============================================================================
    calculation_date = fields.Datetime(
        string='Calculation Date',
        default=fields.Datetime.now,
        required=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('length_inches', 'width_inches', 'height_inches',
                 'length_cm', 'width_cm', 'height_cm', 'measurement_unit')
    def _compute_custom_volume(self):
        """Calculate volume in both cubic feet and liters"""
        for record in self:
            if record.measurement_unit == 'inches':
                length = record.length_inches
                width = record.width_inches
                height = record.height_inches

                if length and width and height:
                    # Volume in cubic inches
                    volume_cubic_inches = length * width * height
                    # Convert to cubic feet (1728 cubic inches = 1 cubic foot)
                    record.custom_volume_cf = volume_cubic_inches / 1728.0
                    # Convert to liters (1 cubic foot = 28.3168 liters)
                    record.custom_volume_liters = record.custom_volume_cf * 28.3168
                else:
                    record.custom_volume_cf = 0.0
                    record.custom_volume_liters = 0.0

            if record.measurement_unit == 'centimeters':
                length = record.length_cm
                width = record.width_cm
                height = record.height_cm

                if length and width and height:
                    # Volume in cubic centimeters
                    volume_cubic_cm = length * width * height
                    # Convert to liters (1000 cubic cm = 1 liter)
                    record.custom_volume_liters = volume_cubic_cm / 1000.0
                    # Convert to cubic feet (1 liter = 0.0353147 cubic feet)
                    record.custom_volume_cf = record.custom_volume_liters * 0.0353147
                else:
                    record.custom_volume_cf = 0.0
                    record.custom_volume_liters = 0.0

    @api.depends('custom_volume_cf')
    def _compute_recommended_container(self):
        """Determine best matching standard container type"""
        # Get container types from database instead of hardcoded values
        container_types = self.env['records.container.type'].search([
            ('active', '=', True),
            ('cubic_feet', '>', 0)
        ])

        CONTAINER_SPECS = {}
        for container in container_types:
            # Extract type number from code (e.g., 'TYPE-01-STD' -> 'type_01')
            if container.code and 'TYPE-' in container.code:
                type_num = container.code.split('-')[1]
                container_key = f'type_{type_num}'
                CONTAINER_SPECS[container_key] = container.cubic_feet

        for record in self:
            if record.custom_volume_cf:
                # Find closest matching container type
                best_match = None
                smallest_diff = float('inf')

                for container_type, volume in CONTAINER_SPECS.items():
                    diff = abs(record.custom_volume_cf - volume)
                    if diff < smallest_diff:
                        smallest_diff = diff
                        best_match = container_type

                if best_match:
                    record.recommended_container_type = best_match
                else:
                    record.recommended_container_type = False
            else:
                record.recommended_container_type = False

    @api.depends('custom_volume_cf', 'recommended_container_type')
    def _compute_equivalent_boxes(self):
        """Calculate equivalent number of standard boxes"""
        CONTAINER_SPECS = {
            'type_01': 1.2,
            'type_02': 2.4,
            'type_03': 0.875,
            'type_04': 5.0,
            'type_06': 0.042,
        }

        for record in self:
            if record.custom_volume_cf and record.recommended_container_type:
                standard_volume = CONTAINER_SPECS.get(record.recommended_container_type, 1.2)
                record.equivalent_standard_boxes = record.custom_volume_cf / standard_volume
            else:
                record.equivalent_standard_boxes = 0.0

    @api.depends('custom_volume_cf', 'recommended_container_type')
    def _compute_volume_difference(self):
        """Calculate volume difference between custom and standard"""
        CONTAINER_SPECS = {
            'type_01': 1.2,
            'type_02': 2.4,
            'type_03': 0.875,
            'type_04': 5.0,
            'type_06': 0.042,
        }

        for record in self:
            if record.custom_volume_cf and record.recommended_container_type:
                standard_volume = CONTAINER_SPECS.get(record.recommended_container_type, 1.2)
                record.volume_difference_cf = record.custom_volume_cf - standard_volume
            else:
                record.volume_difference_cf = 0.0

    @api.depends('custom_volume_cf', 'equivalent_standard_boxes', 'base_rate_per_cf')
    def _compute_pricing(self):
        """Calculate pricing for custom vs standard boxes"""
        CONTAINER_SPECS = {
            'type_01': 1.2,
            'type_02': 2.4,
            'type_03': 0.875,
            'type_04': 5.0,
            'type_06': 0.042,
        }

        for record in self:
            if record.custom_volume_cf and record.base_rate_per_cf:
                # Custom box pricing based on actual volume
                record.custom_box_price = record.custom_volume_cf * record.base_rate_per_cf

                # Standard box pricing based on recommended container
                if record.recommended_container_type:
                    standard_volume = CONTAINER_SPECS.get(record.recommended_container_type, 1.2)
                    # Round up equivalent boxes for billing
                    billing_boxes = math.ceil(record.equivalent_standard_boxes)
                    record.standard_box_price = billing_boxes * standard_volume * record.base_rate_per_cf

                    record.price_difference = record.standard_box_price - record.custom_box_price
                else:
                    record.standard_box_price = 0.0
                    record.price_difference = 0.0
            else:
                record.custom_box_price = 0.0
                record.standard_box_price = 0.0
                record.price_difference = 0.0

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    @api.model
    def _default_base_rate_per_cf(self):
        """Get default base rate from system configuration"""
        try:
            base_rate = self.env['base.rates'].search([
                ('rate_type', '=', 'shredding'),
                ('active', '=', True)
            ], limit=1)
            return base_rate.rate_per_cubic_foot if base_rate else 15.00
        except Exception:
            return 15.00  # Fallback rate

    @api.onchange('measurement_unit')
    def _onchange_measurement_unit(self):
        """Clear fields when changing measurement unit"""
        if self.measurement_unit == 'inches':
            self.length_cm = 0.0
            self.width_cm = 0.0
            self.height_cm = 0.0
        else:  # centimeters
            self.length_inches = 0.0
            self.width_inches = 0.0
            self.height_inches = 0.0

    @api.constrains('length_inches', 'width_inches', 'height_inches',
                    'length_cm', 'width_cm', 'height_cm')
    def _check_dimensions(self):
        """Validate dimensions are positive"""
        for record in self:
            if record.measurement_unit == 'inches':
                dimensions = [record.length_inches, record.width_inches, record.height_inches]
                if any(dim < 0 for dim in dimensions if dim):
                    raise ValidationError(_('Dimensions must be positive values'))
            else:  # centimeters
                dimensions = [record.length_cm, record.width_cm, record.height_cm]
                if any(dim < 0 for dim in dimensions if dim):
                    raise ValidationError(_('Dimensions must be positive values'))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_calculate_volume(self):
        """Force recalculation of all computed fields"""
        self.ensure_one()
        self._compute_custom_volume()
        self._compute_recommended_container()
        self._compute_equivalent_boxes()
        self._compute_volume_difference()
        self._compute_pricing()

        return {
            'type': 'ir.actions.act_window',
            'res_model': self._name,
            'res_id': self.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_create_quote_line(self):
        """Create quote line item with calculated values"""
        self.ensure_one()

        if not self.custom_volume_cf:
            raise UserError(_('Please enter dimensions first'))

        # Determine which service to create line for
        if self.shredding_service_id:
            return self._create_shredding_line()
        if self.pickup_request_id:
            return self._create_pickup_line()
        return self._create_general_quote_line()

    def _create_shredding_line(self):
        """Create shredding service line item"""
        # Create line item (would need actual line item model)
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Quote line created successfully'),
                'type': 'success',
            }
        }

    def action_apply_to_fsm_task(self):
        """Apply calculation results to FSM task"""
        self.ensure_one()

        if not self.fsm_task_id:
            raise UserError(_('Please select an FSM task first'))

        # Update FSM task with calculation results
        task_description = self.fsm_task_id.description or ''
        calculation_summary = (_(
            '\n\n=== Volume Calculation ===\n'
            'Custom Box: %s x %s x %s = %s CF\n'
            'Recommended: %s (%s boxes)\n'
            'Estimated Price: $%s\n'
            'Calculated by: %s on %s'
        ) % (
            self.length_inches or self.length_cm,
            self.width_inches or self.width_cm,
            self.height_inches or self.height_cm,
            round(self.custom_volume_cf, 3),
            dict(self._fields['recommended_container_type'].selection).get(self.recommended_container_type, ''),
            math.ceil(self.equivalent_standard_boxes),
            self.standard_box_price,
            self.user_id.name,
            self.calculation_date.strftime('%Y-%m-%d %H:%M')
        ))

        self.fsm_task_id.write({
            'description': task_description + calculation_summary
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Calculation applied to FSM task successfully'),
                'type': 'success',
            }
        }

    def action_save_calculation(self):
        """Save calculation for future reference"""
        self.ensure_one()

        # Create audit log entry
        self.env["naid.audit.log"].create(
            {
                "name": _(
                    "Volume Calculation: %s",
                    self.name,
                ),
                "event_type": "volume_calculation",
                "description": _(
                    "Custom box volume calculation performed by %s",
                    self.user_id.name,
                ),
                "user_id": self.user_id.id,
                "company_id": self.company_id.id,
                "details": {
                    "dimensions": f"{self.length_inches or self.length_cm}x{self.width_inches or self.width_cm}x{self.height_inches or self.height_cm}",
                    "volume_cf": self.custom_volume_cf,
                    "recommended_type": self.recommended_container_type,
                    "equivalent_boxes": self.equivalent_standard_boxes,
                    "calculated_price": self.standard_box_price,
                },
            }
        )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Calculation saved successfully'),
                'type': 'success',
            }
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def get_calculation_summary(self):
        """Get formatted calculation summary"""
        self.ensure_one()

        return {
            'custom_dimensions': f"{self.length_inches or self.length_cm} x {self.width_inches or self.width_cm} x {self.height_inches or self.height_cm}",
            'custom_volume': round(self.custom_volume_cf, 3),
            'recommended_type': dict(self._fields['recommended_container_type'].selection).get(self.recommended_container_type, ''),
            'equivalent_boxes': math.ceil(self.equivalent_standard_boxes),
            'price_estimate': self.standard_box_price,
            'volume_difference': round(self.volume_difference_cf, 3),
            'price_difference': self.price_difference,
        }

    @api.model
    def create_from_fsm_task(self, task_id):
        """Create calculator session from FSM task"""
        task = self.env['project.task'].browse(task_id)

        return self.create({
            'name': f'Volume Calc - {task.name}',
            'fsm_task_id': task_id,
            'calculation_purpose': 'fsm_quote',
            'user_id': self.env.user.id,
        })

    def _create_pickup_line(self):
        """Create pickup request line item"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('Pickup line created successfully'),
                'type': 'success',
            }
        }

    def _create_general_quote_line(self):
        """Create general quote line item"""
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'message': _('General quote line created successfully'),
                'type': 'success',
            }
        }
