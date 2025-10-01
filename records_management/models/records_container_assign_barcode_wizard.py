from odoo import models, fields, api, _
from odoo.exceptions import UserError


class RecordsContainerAssignBarcodeWizard(models.TransientModel):
    _name = 'records.container.assign.barcode.wizard'
    _description = 'Assign Physical Barcode to Container'

    container_id = fields.Many2one(
        comodel_name='records.container',
        string='Container',
        required=True,
        help='Container that will receive a physical warehouse barcode.'
    )
    temp_barcode = fields.Char(related='container_id.temp_barcode', string='Temporary Barcode', readonly=True)
    current_barcode = fields.Char(related='container_id.barcode', string='Current Physical Barcode', readonly=True)
    new_barcode = fields.Char(string='New Physical Barcode', required=True, help='Scan or enter the physical barcode to assign.')
    force_reassign = fields.Boolean(string='Force Reassign', help='Allow replacing an existing physical barcode (logs audit event).')

    @api.model
    def default_get(self, fields_list):
        vals = super().default_get(fields_list)
        active_id = self.env.context.get('active_id')
        if active_id and 'container_id' in fields_list and not vals.get('container_id'):
            vals['container_id'] = active_id
        return vals

    def action_assign(self):
        self.ensure_one()
        if not self.new_barcode:
            raise UserError(_("A physical barcode value is required."))
        ctx = {}
        if self.force_reassign:
            ctx['force_reassign'] = True
        self.container_id.with_context(**ctx).action_assign_physical_barcode(self.new_barcode)
        return {'type': 'ir.actions.act_window_close'}
