from odoo import models, fields, api, _

class ContainerRetrievalItem(models.Model):
    _name = 'container.retrieval.item'
    _description = 'Container Retrieval Item'
    _inherit = 'retrieval.item.base'
    _rec_name = 'display_name'

    display_name = fields.Char(string='Display Name', compute='_compute_display_name', store=True)

    # Container-specific fields
    container_id = fields.Many2one('records.container', string='Container', required=True, ondelete='restrict')
    storage_location_id = fields.Many2one('records.location', string='Storage Location', related='container_id.storage_location_id', readonly=True)
    estimated_weight = fields.Float(string='Estimated Weight (kg)', related='container_id.weight', readonly=True)
    actual_weight = fields.Float(string='Actual Weight (kg)')
    dimensions = fields.Char(string='Dimensions (LxWxH)', related='container_id.dimensions', readonly=True)

    status = fields.Selection(selection_add=[
        ('locating', 'Locating'),
        ('delivered', 'Delivered'),
        ('returned', 'Returned')
    ], ondelete={'locating': 'set default', 'delivered': 'set default', 'returned': 'set default'})

    @api.depends('container_id', 'work_order_id.name')
    def _compute_display_name(self):
        for item in self:
            name_parts = []
            if item.work_order_id:
                name_parts.append(f"[{item.work_order_id.name}]")
            if item.container_id:
                name_parts.append(item.container_id.name)
            else:
                name_parts.append(_("New Container Retrieval"))
            item.display_name = " - ".join(name_parts)

    # Container-specific methods
    def action_locate_container(self):
        self.ensure_one()
        # Container location logic
        self.write({'status': 'located'})
        self.message_post(body=_("Container marked as 'Located' by %s", self.env.user.name))
        return True
