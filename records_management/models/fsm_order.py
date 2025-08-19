from odoo import models, fields, api, _
from odoo.exceptions import UserError

class FsmOrder(models.Model):
    _inherit = 'fsm.order'

    # ============================================================================
    # SHREDDING SERVICE FIELDS
    # ============================================================================
    service_type = fields.Selection([
        ('on_site_shredding', 'On-Site Shredding'),
        ('off_site_shredding', 'Off-Site Shredding'),
        ('hard_drive_destruction', 'Hard Drive Destruction'),
        ('product_destruction', 'Product Destruction'),
    ], string="Service Type", tracking=True)

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
    container_ids = fields.Many2many('records.container', string="Containers for Service")
    container_count = fields.Integer(string="Container Count", compute='_compute_container_totals', store=True)
    total_weight = fields.Float(string="Total Weight (kg)", compute='_compute_container_totals', store=True)

    # ============================================================================
    # COMPLIANCE & CERTIFICATION
    # ============================================================================
    certificate_required = fields.Boolean(string="Certificate Required", default=True)
    certificate_id = fields.Many2one('shredding.certificate', string="Destruction Certificate", readonly=True, copy=False)
    naid_compliance_required = fields.Boolean(string="NAID Compliance Required", default=True)
    witness_required = fields.Boolean(string="Witness Required")
    witness_name = fields.Char(string="Witness Name")

    # ============================================================================
    # PHOTO DOCUMENTATION
    # ============================================================================
    photo_ids = fields.One2many('shredding.service.photo', 'shredding_service_id', string="Photo Documentation")
    photo_count = fields.Integer(compute='_compute_photo_count', string="Photo Count")

    # ============================================================================
    # EQUIPMENT & RESOURCES
    # ============================================================================
    shredding_equipment_id = fields.Many2one('maintenance.equipment', string="Shredding Equipment", domain="[('equipment_category', '=', 'shredder')]")

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('container_ids', 'container_ids.weight')
    def _compute_container_totals(self):
        for order in self:
            order.container_count = len(order.container_ids)
            order.total_weight = sum(order.container_ids.mapped('weight'))

    @api.depends('photo_ids')
    def _compute_photo_count(self):
        for order in self:
            order.photo_count = len(order.photo_ids)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_complete(self):
        # Override to add certificate generation
        res = super().action_complete()
        for order in self:
            if order.certificate_required and not order.certificate_id:
                order._generate_certificate()
        return res

    def action_view_photos(self):
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

    # ============================================================================
    # HELPER METHODS
    # ============================================================================
    def _generate_certificate(self):
        self.ensure_one()
        if 'shredding.certificate' not in self.env:
            return

        certificate_vals = {
            'partner_id': self.partner_id.id,
            'destruction_date': fields.Date.context_today(self),
            'destruction_method': self.destruction_method,
            'shredding_service_ids': [(6, 0, self.ids)],
            'destruction_equipment': self.shredding_equipment_id.name if self.shredding_equipment_id else False,
            'equipment_serial_number': self.shredding_equipment_id.serial_no if self.shredding_equipment_id else False,
            'operator_name': self.user_id.name,
        }
        certificate = self.env['shredding.certificate'].create(certificate_vals)
        self.certificate_id = certificate.id
        self.message_post(
            body=_("Destruction Certificate %s generated.") % certificate.name,
            attachment_ids=[(4, certificate.id)]
        )
