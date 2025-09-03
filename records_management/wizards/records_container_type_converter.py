# -*- coding: utf-8 -*-
"""
Records Container Type Converter Wizard

This wizard enables bulk conversion of container types for operational efficiency.
It handles the complex business logic of converting containers between different
types (TYPE 01-06) while maintaining proper audit trails and NAID compliance.

Key Features:
- Bulk container type conversion with validation
- Business rule enforcement for container specifications
- NAID audit trail integration for compliance tracking
- Proper error handling and user feedback
"""

from odoo import models, fields, api, _

from odoo.exceptions import UserError




class RecordsContainerTypeConverterWizard(models.TransientModel):
    _name = "records.container.type.converter.wizard"
    _description = "Records Container Type Converter Wizard"
    _inherit = ['mail.thread']

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string="Conversion Name",
        required=True,
        default=lambda self: _("Container Type Conversion - %s", fields.Date.today()),
        help="Name for this conversion operation"
    )

    # ============================================================================
    # CONVERSION CONFIGURATION
    # ============================================================================
    source_container_type = fields.Selection([
        ('type_01', 'TYPE 01 - Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02 - Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03 - Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04 - Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06 - Pathology Box (0.042 CF)'),
    ], string="Source Container Type", required=True,
       help="Current container type to convert FROM")

    target_container_type = fields.Selection([
        ('type_01', 'TYPE 01 - Standard Box (1.2 CF)'),
        ('type_02', 'TYPE 02 - Legal/Banker Box (2.4 CF)'),
        ('type_03', 'TYPE 03 - Map Box (0.875 CF)'),
        ('type_04', 'TYPE 04 - Odd Size/Temp Box (5.0 CF)'),
        ('type_06', 'TYPE 06 - Pathology Box (0.042 CF)'),
    ], string="Target Container Type", required=True,
       help="New container type to convert TO")

    # ============================================================================
    # CONTAINER SELECTION
    # ============================================================================
    container_ids = fields.Many2many(
        'records.container',
        string="Containers to Convert",
        help="Select containers to convert (will be filtered by source type)"
    )

    partner_id = fields.Many2one(
        'res.partner',
        string="Customer Filter",
        help="Filter containers by customer (optional)"
    )

    location_id = fields.Many2one(
        'records.location',
        string="Location Filter",
        help="Filter containers by location (optional)"
    )

    # ============================================================================
    # CONVERSION RESULTS
    # ============================================================================
    container_count = fields.Integer(
        string="Containers Found",
        compute="_compute_container_count",
        help="Number of containers matching criteria"
    )

    estimated_cost_impact = fields.Monetary(
        string="Estimated Cost Impact",
        compute="_compute_cost_impact",
        currency_field="currency_id",
        help="Estimated monthly cost change from conversion"
    )

    currency_id = fields.Many2one(
        'res.currency',
        string="Currency",
        default=lambda self: self.env.company.currency_id,
        required=True
    )

    # ============================================================================
    # BUSINESS VALIDATION
    # ============================================================================
    validation_warnings = fields.Text(
        string="Validation Warnings",
        compute="_compute_validation_warnings",
        help="Warnings about potential issues with conversion"
    )

    force_conversion = fields.Boolean(
        string="Force Conversion",
        default=False,
        help="Ignore validation warnings and proceed with conversion"
    )

    # ============================================================================
    # AUDIT AND TRACKING
    # ============================================================================
    reason = fields.Text(
        string="Conversion Reason",
        required=True,
        help="Business reason for this container type conversion"
    )

    notes = fields.Text(
        string="Additional Notes",
        help="Additional notes about this conversion"
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('source_container_type', 'partner_id', 'location_id')
    def _compute_container_count(self):
        """Compute number of containers matching criteria"""
        for wizard in self:
            if not wizard.source_container_type:
                wizard.container_count = 0
                continue

            domain = [('container_type', '=', wizard.source_container_type)]

            if wizard.partner_id:
                domain.append(('partner_id', '=', wizard.partner_id.id))

            if wizard.location_id:
                domain.append(('location_id', '=', wizard.location_id.id))

            wizard.container_count = self.env['records.container'].search_count(domain)

    @api.depends('source_container_type', 'target_container_type', 'container_count')
    def _compute_cost_impact(self):
        """Compute estimated cost impact of conversion"""
        for wizard in self:
            if not wizard.source_container_type or not wizard.target_container_type:
                wizard.estimated_cost_impact = 0.0
                continue

            # Get container specifications for cost calculation
            specs = wizard._get_container_specifications()
            source_spec = specs.get(wizard.source_container_type, {})
            target_spec = specs.get(wizard.target_container_type, {})

            # Calculate monthly cost difference per container
            source_cost = source_spec.get('monthly_rate', 0.0)
            target_cost = target_spec.get('monthly_rate', 0.0)
            cost_per_container = target_cost - source_cost

            wizard.estimated_cost_impact = cost_per_container * wizard.container_count

    @api.depends('source_container_type', 'target_container_type')
    def _compute_validation_warnings(self):
        """Generate validation warnings for conversion"""
        for wizard in self:
            warnings = []

            if wizard.source_container_type == wizard.target_container_type:
                warnings.append("Source and target types are the same - no conversion needed")

            if wizard.source_container_type and wizard.target_container_type:
                specs = wizard._get_container_specifications()
                source_spec = specs.get(wizard.source_container_type, {})
                target_spec = specs.get(wizard.target_container_type, {})

                # Volume capacity warnings
                if source_spec.get('volume', 0) > target_spec.get('volume', 0):
                    warnings.append("Converting to smaller volume container - documents may not fit")

                # Weight capacity warnings
                if source_spec.get('max_weight', 0) > target_spec.get('max_weight', 0):
                    warnings.append("Converting to lower weight capacity - may exceed limits")

                # Cost impact warnings
                if wizard.estimated_cost_impact > 1000:
                    warnings.append("High cost impact - review pricing implications")

            wizard.validation_warnings = '\n'.join(warnings) if warnings else ""

    # ============================================================================
    # BUSINESS LOGIC METHODS
    # ============================================================================
    @api.model
    def _get_container_specifications(self):
        """Get container specifications for business validation"""
        return {
            'type_01': {
                'volume': 1.2,
                'max_weight': 35,
                'dimensions': '12" x 15" x 10"',
                'monthly_rate': 12.50,
                'description': 'Standard Box'
            },
            'type_02': {
                'volume': 2.4,
                'max_weight': 65,
                'dimensions': '24" x 15" x 10"',
                'monthly_rate': 18.75,
                'description': 'Legal/Banker Box'
            },
            'type_03': {
                'volume': 0.875,
                'max_weight': 35,
                'dimensions': '42" x 6" x 6"',
                'monthly_rate': 15.00,
                'description': 'Map Box'
            },
            'type_04': {
                'volume': 5.0,
                'max_weight': 75,
                'dimensions': 'Variable',
                'monthly_rate': 25.00,
                'description': 'Odd Size/Temp Box'
            },
            'type_06': {
                'volume': 0.042,
                'max_weight': 40,
                'dimensions': '12" x 6" x 10"',
                'monthly_rate': 10.00,
                'description': 'Pathology Box'
            }
        }

    def _get_containers_to_convert(self):
        """Get containers that match conversion criteria"""
        self.ensure_one()

        domain = [('container_type', '=', self.source_container_type)]

        if self.partner_id:
            domain.append(('partner_id', '=', self.partner_id.id))

        if self.location_id:
            domain.append(('location_id', '=', self.location_id.id))

        if self.container_ids:
            # Use specific containers if selected
            domain.append(('id', 'in', self.container_ids.ids))

        return self.env['records.container'].search(domain)

    def _create_naid_audit_log(self, containers):
        """Create NAID audit log for container type conversion"""
        self.ensure_one()

        log_vals = {
            'name': _("Container Type Conversion: %s", self.name,)
            'event_type': 'container_conversion',
            'event_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'description': _("Converted %d containers from %s to %s") % (
                           len(containers),
                           self.source_container_type,
                           self.target_container_type),
            'reason': self.reason,
            'affected_containers': [(6, 0, containers.ids)]
        }

        return self.env['naid.audit.log'].create(log_vals)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_preview_conversion(self):
        """Preview containers that will be converted"""

        self.ensure_one()

        if not self.source_container_type:
            raise UserError(_("Please select a source container type"))

        containers = self._get_containers_to_convert()

        return {
            'name': _("Containers to Convert"),
            'type': 'ir.actions.act_window',
            'res_model': 'records.container',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', containers.ids)],
            'context': {
                'default_container_type': self.target_container_type,
                'search_default_group_by_partner': 1,
            }
        }

    def action_execute_conversion(self):
        """Execute the container type conversion"""

        self.ensure_one()

        # Validation
        if not self.source_container_type or not self.target_container_type:
            raise UserError(_("Please select both source and target container types"))

        if self.source_container_type == self.target_container_type:
            raise UserError(_("Source and target container types cannot be the same"))

        if not self.reason:
            raise UserError(_("Please provide a reason for this conversion"))

        # Get containers to convert
        containers = self._get_containers_to_convert()

        if not containers:
            raise UserError(_("No containers found matching the specified criteria"))

        # Check for validation warnings
        if self.validation_warnings and not self.force_conversion:
            raise UserError(
                _(
                    "Validation warnings found:\n%s\n\nPlease review and check 'Force Conversion' to proceed."
                )
                % self.validation_warnings
            )

        # Perform conversion
        specs = self._get_container_specifications()
        target_spec = specs.get(self.target_container_type, {})

        conversion_vals = {
            'container_type': self.target_container_type,
            'volume': target_spec.get('volume', 0.0),
            'max_weight': target_spec.get('max_weight', 0.0),
            'dimensions': target_spec.get('dimensions', ''),
        }

        containers.write(conversion_vals)

        # Create audit log
        self._create_naid_audit_log(containers)

        # Update container histories
        for container in containers:
            container.message_post(
                body=_("Container type converted from %s to %s. Reason: %s")
                % (
                    self.source_container_type,
                    self.target_container_type,
                    self.reason,
                )
            )

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _("Conversion Complete"),
                'message': _("%d containers successfully converted from %s to %s")
                           % (len(containers), self.source_container_type, self.target_container_type),
                'type': 'success',
            },
        }

    def action_cancel(self):
        """Cancel the wizard"""

        self.ensure_one()
        return {'type': 'ir.actions.act_window_close'}

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('source_container_type', 'partner_id', 'location_id')
    def _onchange_filter_criteria(self):
        """Update container selection when filter criteria change"""
        if self.source_container_type:
            # Clear container selection when criteria change
            self.container_ids = [(5, 0, 0)]

            # Update domain for container selection
            domain = [('container_type', '=', self.source_container_type)]

            if self.partner_id:
                domain.append(('partner_id', '=', self.partner_id.id))

            if self.location_id:
                domain.append(('location_id', '=', self.location_id.id))

            return {'domain': {'container_ids': domain}}

    @api.onchange('source_container_type', 'target_container_type')
    def _onchange_container_types(self):
        """Provide guidance when container types change"""
        if self.source_container_type and self.target_container_type:
            specs = self._get_container_specifications()
            source_spec = specs.get(self.source_container_type, {})
            target_spec = specs.get(self.target_container_type, {})

            if self.source_container_type == self.target_container_type:
                return {
                    'warning': {
                        'title': _("Same Container Types"),
                        'message': _("Source and target container types are the same. Please select different types for conversion.")
                    }
                }

            # Provide helpful information about the conversion
            volume_change = target_spec.get('volume', 0) - source_spec.get('volume', 0)
            cost_change = target_spec.get('monthly_rate', 0) - source_spec.get('monthly_rate', 0)

            if volume_change < 0:
                return {
                    'warning': {
                        'title': _("Volume Reduction"),
                        'message': _("Converting to a smaller container type. Ensure documents will fit in the new container size.")
                    }
                }

            if cost_change != 0:
                cost_direction = _("increase") if cost_change > 0 else _("decrease")
                return {
                    'warning': {
                        'title': _("Cost Impact"),
                        'message': _(
                            "Converting container type will cause a monthly cost %s of %.2f. Review pricing details."
                        )
                        % (cost_direction, abs(cost_change)),
                    }
                }
