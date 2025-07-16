# New file: Model for temporary inventory additions from portal. Generates temp barcodes, converts to pickup request. Internal verification assigns physical barcodes, preserving audit trail for NAID compliance.

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class TempInventory(models.Model):
    _name = 'temp.inventory'
    _description = 'Temporary Customer Inventory'
    _inherit = ['mail.thread']

    name = fields.Char(string='Temp Reference', default='New')
    partner_id = fields.Many2one('res.partner', string='Customer', required=True)
    inventory_type = fields.Selection([
        ('box', 'Box'),
        ('document', 'Document'),
        ('file', 'File'),
    ], string='Type', required=True)
    temp_barcode = fields.Char(string='Temporary Barcode', readonly=True)
    description = fields.Text()
    state = fields.Selection([
        ('temp', 'Temporary'),
        ('requested', 'Pickup Requested'),
        ('verified', 'Verified'),
    ], default='temp')
    physical_barcode = fields.Char(string='Physical Barcode')
    audit_log = fields.Html(string='Audit Trail', readonly=True)
    pickup_request_id = fields.Many2one('pickup.request', string='Pickup Request')

    @api.model_create_multi
    def create(self, vals_list):
        res = super().create(vals_list)
        for record in res:
            if record.name == 'New':
                record.name = self.env['ir.sequence'].next_by_code('temp.inventory') or 'New'
            record.temp_barcode = f'TEMP-{record.inventory_type.upper()}-{record.name}'
            record._append_audit_log(_('Created by customer on %s.', fields.Datetime.now()))
        return res

    def action_add_to_pickup(self):
        # Multi-select: Create/batch to pickup request
        pickup = self.env['pickup.request'].create({
            'customer_id': self.partner_id.id,
            'request_item_ids': [(0, 0, {
                'product_id': self.env.ref('records_management.product_inventory_add', raise_if_not_found=False).id or False,  # Assume product
                'quantity': 1,
                'notes': self.description,
            }) for item in self],
        })
        self.write({'state': 'requested', 'pickup_request_id': pickup.id})
        for item in self:
            item._append_audit_log(_('Added to pickup request %s.', pickup.name))

    def action_verify_physical(self):
        # Internal action: Assign physical barcode, link to real inventory
        if not self.physical_barcode:
            raise ValidationError(_("Enter physical barcode."))
        if self.inventory_type == 'box':
            box = self.env['records.box'].create({
                'name': self.temp_barcode,  # Temp as initial ref
                'barcode': self.physical_barcode,
                'customer_id': self.partner_id.id,
                'description': self.description,
            })
        elif self.inventory_type == 'document':
            document = self.env['records.document'].create({
                'name': self.description or self.temp_barcode,
                'barcode': self.physical_barcode,
                'customer_id': self.partner_id.id,
                'description': self.description,
            })
        elif self.inventory_type == 'file':
            # Create file record or link to document
            file_record = self.env['records.document'].create({
                'name': self.description or self.temp_barcode,
                'barcode': self.physical_barcode,
                'customer_id': self.partner_id.id,
                'description': self.description,
                'document_type': 'file',
            })
        
        self.state = 'verified'
        self._append_audit_log(_('Verified and assigned physical barcode %s on %s.', self.physical_barcode, fields.Datetime.now()))

    def _append_audit_log(self, message):
        current_log = self.audit_log or ''
        self.audit_log = current_log + f'<p>{message}</p>'
