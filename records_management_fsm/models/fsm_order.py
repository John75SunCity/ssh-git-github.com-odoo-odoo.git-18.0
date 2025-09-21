from odoo import models, fields, api, _
from odoo.exceptions import UserError


class FsmOrder(models.Model):
    """
    Extends the 'project.task' model to include shredding service-specific fields,
    methods, and business logic. This model supports various shredding services
    such as on-site shredding, off-site shredding, and hard drive destruction,
    while ensuring compliance with NAID AAA standards.
    """
    # Pure extension of project.task (avoid clone warning)
    _inherit = 'project.task'
    _description = 'FSM Order Management'

    # ============================================================================
    # SHREDDING SERVICE FIELDS
    # ============================================================================
    service_type = fields.Selection(
        [
            ("on_site_shredding", "Mobile Shredding"),
            ("off_site_shredding", "Off-Site Shredding"),
            ("hard_drive_destruction", "Hard Drive Destruction"),
            ("product_destruction", "Product Destruction"),
        ],
        string="Service Type",
        tracking=True,
    )

    material_type = fields.Selection([
        ('paper', 'Paper'),
        ('media', 'Digital Media'),
        ('product', 'Products'),
        ('mixed', 'Mixed Materials')
    ], string="Material Type", default='paper')

    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('degaussing', 'Degaussing'),
        ('incineration', 'Incineration'),
        ('disintegration', 'Disintegration')
    ], string="Destruction Method", default='shredding')

    # ============================================================================
    # QUANTITIES & FINANCIALS
    # ============================================================================
    container_ids = fields.Many2many(
        comodel_name='records.container',
        relation='fsm_task_records_container_rel',
        column1='task_id',
        column2='container_id',
        string="Containers for Service"
    )
    container_count = fields.Integer(
        string="Container Count",
        compute='_compute_container_totals',
        store=True
    )
    total_weight = fields.Float(
        string="Total Weight (kg)",
        compute='_compute_container_totals',
        store=True
    )

    # ============================================================================
    # COMPLIANCE & CERTIFICATION
    # ============================================================================
    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    certificate_id = fields.Many2one(
        comodel_name='shredding.certificate',
        string="Shredding Certificate",
        readonly=True,
        copy=False
    )
    naid_compliance_required = fields.Boolean(string="NAID Compliance Required", default=True)
    witness_required = fields.Boolean(string="Witness Required")
    witness_name = fields.Char(string="Witness Name")

    # ============================================================================
    # PHOTO DOCUMENTATION
    # ============================================================================
    photo_ids = fields.One2many(
        comodel_name='shredding.service.photo',
        inverse_name='shredding_service_id',
        string="Photo Documentation"
    )
    photo_count = fields.Integer(
        compute='_compute_photo_count',
        string="Photo Count"
    )

    # ============================================================================
    # EQUIPMENT & RESOURCES
    # ============================================================================
    shredding_equipment_id = fields.Many2one(
        comodel_name='maintenance.equipment',
        string="Shredding Equipment",
        domain=[('equipment_category', '=', 'shredder')]
    )

    # ============================================================================
    # BIN DETAILS
    # ============================================================================
    bin_details_ids = fields.One2many(
        comodel_name='shredding.service.bin',
        inverse_name='shredding_service_id',
        string='Bin Details',
    )

    # ============================================================================
    # VEHICLE & TECHNICIAN DETAILS
    # ============================================================================
    vehicle_id = fields.Many2one(
        comodel_name='fleet.vehicle',
        string="Vehicle Used",
        readonly=True
    )
    technician_id = fields.Many2one(
        comodel_name='res.users',
        string="Technician",
        readonly=True
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_ids', 'container_ids.container_type_id', 'container_ids.container_type_id.average_weight_lbs')
    def _compute_container_totals(self):
        """
        Computes the total number of containers and their estimated weight
        based on the container type's average weight. This method ensures
        safe dependency handling for accurate calculations.
        """
        for order in self:
            order.container_count = len(order.container_ids)

            # Safe computation of estimated weight using container type definitions
            estimated_weight = 0.0
            for container in order.container_ids:
                if (hasattr(container, 'container_type_id') and
                    container.container_type_id and
                    hasattr(container.container_type_id, 'average_weight_lbs') and
                    container.container_type_id.average_weight_lbs):
                    estimated_weight += container.container_type_id.average_weight_lbs
            order.total_weight = estimated_weight

    @api.depends('photo_ids')
    def _compute_photo_count(self):
        """
        Computes the total number of photos attached to the shredding service
        for documentation purposes.
        """
        for order in self:
            order.photo_count = len(order.photo_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_complete(self):
        """
        Overrides the default 'action_complete' method to include additional
        logic for certificate generation, vehicle assignment, and technician
        assignment when completing a shredding service.
        """
        self.ensure_one()
        res = super().action_complete()
        for order in self:
            try:
                if order.certificate_required and not order.certificate_id:
                    order._generate_certificate()
                if not order.vehicle_id:
                    vehicle = self.env['fleet.vehicle'].search([('driver_id', '=', order.user_id.id)], limit=1)
                    if vehicle:
                        order.vehicle_id = vehicle.id
                if not order.technician_id:
                    order.technician_id = order.user_id.id
            except Exception as e:
                raise UserError(_("Error completing shredding service: %s") % str(e))  # fixed interpolation
        return res

    def action_view_photos(self):
        """
        Opens a window to display the photo documentation associated with
        the shredding service. Ensures that the current record is selected.

        Returns:
            dict: An action dictionary to open the photo documentation view.
        """
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': _('Photo Documentation'),
            'res_model': 'shredding.service.photo',
            'view_mode': 'kanban,tree,form',
            'domain': [('shredding_service_id', '=', self.id)],
            'context': {'default_shredding_service_id': self.id}
        }

    def action_view_certificate(self):
        """
        Opens the destruction certificate associated with the shredding service.
        Raises an error if no certificate has been generated.

        Returns:
            dict: An action dictionary to open the certificate form view.

        Raises:
            UserError: If no certificate is available for the service.
        """
        self.ensure_one()
        if not self.certificate_id:
            raise UserError(_("No certificate has been generated for this service."))
        return {
            'type': 'ir.actions.act_window',
            'name': _('Destruction Certificate'),
            'res_model': 'shredding.certificate',
            'res_id': self.certificate_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_generate_certificate(self):
        """
        Manual action to generate a destruction certificate.
        """
        self.ensure_one()
        if self.certificate_id:
            raise UserError(_("A certificate has already been generated for this service."))

        self._generate_certificate()

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": _("Certificate Generated"),
                "message": _("Destruction certificate %s has been generated successfully.") % (
                    self.certificate_id.name if self.certificate_id and self.certificate_id.name else "(unknown)"
                ),
                "type": "success",
                "sticky": False,
            },
        }

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _generate_certificate(self):
        """
        Generates a destruction certificate for the shredding service.
        Includes details such as partner information, destruction method,
        equipment used, and bin details. Posts a message with the generated
        certificate as an attachment.
        """
        self.ensure_one()
        try:
            ShreddingCertificate = self.env['shredding.certificate']
        except KeyError:
            return False

        # Prepare bin details for the certificate
        bin_details = []
        for bin_detail in self.bin_details_ids:
            if hasattr(bin_detail, 'bin_size') and hasattr(bin_detail, 'barcode'):
                bin_details.append({
                    'bin_size': bin_detail.bin_size,
                    'barcode': bin_detail.barcode,
                })

        certificate_vals = {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'destruction_date': fields.Date.context_today(self),
            'destruction_method': self.destruction_method,
            'shredding_service_ids': [(6, 0, self.ids)],
            'destruction_equipment': self.shredding_equipment_id.name if self.shredding_equipment_id else False,
            'equipment_serial_number': self.shredding_equipment_id.serial_no if self.shredding_equipment_id else False,
            'operator_name': self.user_id.name if self.user_id else False,
            'bin_details': bin_details,
        }
        try:
            certificate = ShreddingCertificate.create(certificate_vals)
            self.certificate_id = certificate.id
            self.message_post(
                body=_("Destruction Certificate %s generated.") % certificate.name
            )
            return certificate
        except Exception as e:
            raise UserError(_("Failed to generate certificate: %s") % str(e))

    def _prepare_certificate_vals(self):
        """
        Prepare certificate values for creation.
        Separated for easier testing and customization.
        """
        self.ensure_one()

        # Prepare bin details for the certificate
        bin_details = []
        for bin_detail in self.bin_details_ids:
            if hasattr(bin_detail, 'bin_size') and hasattr(bin_detail, 'barcode'):
                bin_details.append({
                    'bin_size': bin_detail.bin_size,
                    'barcode': bin_detail.barcode,
                })

        return {
            'partner_id': self.partner_id.id if self.partner_id else False,
            'destruction_date': fields.Date.context_today(self),
            'destruction_method': self.destruction_method,
            'shredding_service_ids': [(6, 0, self.ids)],
            'destruction_equipment': self.shredding_equipment_id.name if self.shredding_equipment_id else False,
            'equipment_serial_number': self.shredding_equipment_id.serial_no if self.shredding_equipment_id else False,
            'operator_name': self.user_id.name if self.user_id else False,
            'bin_details': bin_details,
        }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('witness_required', 'witness_name')
    def _check_witness_required(self):
        """Validate that witness name is provided when witness is required."""
        for record in self:
            if record.witness_required and not record.witness_name:
                raise UserError(_("Witness name is required when a witness is required."))

    @api.constrains('naid_compliance_required', 'certificate_required')
    def _check_naid_compliance(self):
        """Validate NAID compliance requirements."""
        for record in self:
            if record.naid_compliance_required and not record.certificate_required:
                raise UserError(_("Certificate is required when NAID compliance is required."))

    @api.onchange('naid_compliance_required')
    def _onchange_naid_compliance_required(self):
        """Auto-correct certificate_required when NAID compliance is required."""
        if self.naid_compliance_required:
            self.certificate_required = True

    # Renamed helper to satisfy naming lint (_selection_ prefix)
    def _selection_label(self, field_name, value):
        """Return display label for a selection field."""
        selection = dict(self._fields[field_name].selection)
        return selection.get(value)

    def get_service_summary(self):
        """
        Get a summary of the service details for reporting.
        """
        self.ensure_one()
        return {
            'service_type': self._selection_label('service_type', self.service_type),
            'material_type': self._selection_label('material_type', self.material_type),
            'destruction_method': self._selection_label('destruction_method', self.destruction_method),
            'container_count': self.container_count,
            'total_weight': self.total_weight,
            'certificate_generated': bool(self.certificate_id),
            'photo_count': self.photo_count,
            'witness_present': bool(self.witness_name),
        }

    def can_generate_certificate(self):
        """
        Check if the service is ready for certificate generation.
        """
        self.ensure_one()
        if self.certificate_id:
            return False, _("Certificate already generated")

        if not self.partner_id:
            return False, _("Customer is required for certificate generation")

        if not self.destruction_method:
            return False, _("Destruction method is required")

        if self.witness_required and not self.witness_name:
            return False, _("Witness name is required")

        return True, _("Ready for certificate generation")
