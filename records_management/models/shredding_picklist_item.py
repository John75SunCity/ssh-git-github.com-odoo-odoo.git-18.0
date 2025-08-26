from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ShreddingPicklistItem(models.Model):
    _name = 'shredding.picklist.item'
    _description = 'Shredding Picklist Item'
    _order = 'sequence, id'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    batch_id = fields.Many2one('shredding.inventory.batch', string="Batch", required=True, ondelete='cascade')
    sequence = fields.Integer(string="Sequence", default=10)
    display_name = fields.Char(string="Display Name", compute='_compute_display_name', store=True)
    barcode = fields.Char(string="Barcode", related='container_id.barcode', readonly=True, store=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('picked', 'Picked'),
        ('verified', 'Verified'),
        ('not_found', 'Not Found'),
    ], string="Status", default='pending', required=True)

    # ============================================================================
    # ITEM & LOCATION
    # ============================================================================
    container_id = fields.Many2one('records.container', string="Container", ondelete='restrict')
    document_id = fields.Many2one('records.document', string="Document", ondelete='restrict')
    expected_location_id = fields.Many2one('stock.location', string="Expected Location", related='container_id.location_id', readonly=True)

    # ============================================================================
    # PICKING & VERIFICATION
    # ============================================================================
    picked_by_id = fields.Many2one('res.users', string="Picked By", readonly=True)
    picked_date = fields.Datetime(string="Picked Date", readonly=True)
    verified_by_id = fields.Many2one('res.users', string="Verified By", readonly=True)
    verified_date = fields.Datetime(string="Verified Date", readonly=True)
    notes = fields.Text(string="Notes")
    picking_instructions = fields.Text(string="Picking Instructions")

    # ============================================================================
    # COMPUTE & CONSTRAINTS
    # ============================================================================
    @api.depends('container_id', 'document_id')
    def _compute_display_name(self):
        for item in self:
            if item.container_id:
                item.display_name = item.container_id.name
            elif item.document_id:
                item.display_name = item.document_id.name
            else:
                item.display_name = _("Unassigned Item")

    @api.constrains('container_id', 'document_id')
    def _check_item_specified(self):
        for record in self:
            if not record.container_id and not record.document_id:
                raise ValidationError(_("Each picklist item must have a container or a document specified."))

    @api.constrains('picked_date', 'verified_date')
    def _check_date_sequence(self):
        for record in self:
            if record.picked_date and record.verified_date and record.verified_date < record.picked_date:
                raise ValidationError(_("The verification date cannot be earlier than the picked date."))

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_mark_picked(self):
        self.ensure_one()
        self.write({
            'status': 'picked',
            'picked_by_id': self.env.user.id,
            'picked_date': fields.Datetime.now()
        })
    self.batch_id.message_post(body=_('Item %s marked as picked') % self.display_name)

    def action_mark_verified(self):
        self.ensure_one()
        if self.status != 'picked':
            raise UserError(_("Only picked items can be verified."))
        self.write({
            'status': 'verified',
            'verified_by_id': self.env.user.id,
            'verified_date': fields.Datetime.now()
        })
    self.batch_id.message_post(body=_('Item %s marked as verified') % self.display_name)

    def action_mark_not_found(self):
        self.ensure_one()
        self.write({'status': 'not_found'})
    self.batch_id.message_post(body=_('Item %s marked as not found') % self.display_name)

    def action_reset_to_pending(self):
        self.ensure_one()
        self.write({
            'status': 'pending',
            'picked_by_id': False,
            'picked_date': False,
            'verified_by_id': False,
            'verified_date': False,
        })
    self.batch_id.message_post(body=_('Item %s reset to pending') % self.display_name)

