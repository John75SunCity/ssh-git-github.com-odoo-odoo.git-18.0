from odoo import api, fields, models, _


class RecordsRetrievalOrderLine(models.Model):
    _name = 'records.retrieval.order.line'
    _description = 'Retrieval Order Line'
    _inherit = ['mail.thread']
    _order = 'priority desc, order_id, name'

    order_id = fields.Many2one('records.retrieval.order', string='Retrieval Order', required=True, ondelete='cascade', index=True)
    name = fields.Char(string='Line Reference', required=True, copy=False, default=lambda self: _('New'))
    file_name = fields.Char(string='File Name', required=True, tracking=True)
    file_description = fields.Char(string='Description')
    item_type = fields.Selection([
        ('file', 'File'),
        ('folder', 'Folder'),
        ('container', 'Container'),
        ('scan', 'Scan Target'),
        ('other', 'Other')
    ], string='Item Type', default='file')
    container_id = fields.Many2one('records.container', string='Container')
    location_id = fields.Many2one('records.location', string='Location', related='container_id.location_id', store=True)
    position_note = fields.Char(string='Position / Slot')
    barcode = fields.Char(string='Barcode')
    estimated_pages = fields.Integer(string='Est. Pages', default=0)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('located', 'Located'),
        ('retrieved', 'Retrieved'),
        ('delivered', 'Delivered'),
        ('completed', 'Completed'),
        ('not_found', 'Not Found'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='pending', tracking=True, required=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1')
    assigned_user_id = fields.Many2one('res.users', string='Assigned To')
    retrieved_by_id = fields.Many2one('res.users', string='Retrieved By')
    date_retrieved = fields.Datetime(string='Date Retrieved')
    date_delivered = fields.Datetime(string='Date Delivered')
    notes = fields.Text(string='Notes')

    def action_mark_located(self):
        self.ensure_one()
        if self.status == 'pending':
            self.status = 'located'

    def action_mark_retrieved(self):
        self.ensure_one()
        if self.status in ['pending', 'located']:
            self.write({'status': 'retrieved', 'date_retrieved': fields.Datetime.now(), 'retrieved_by_id': self.env.user.id})

    def action_mark_delivered(self):
        self.ensure_one()
        if self.status == 'retrieved':
            self.write({'status': 'delivered', 'date_delivered': fields.Datetime.now()})

    def action_complete(self):
        self.ensure_one()
        if self.status == 'delivered':
            self.status = 'completed'

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.retrieval.order.line') or _('New')
        return super().create(vals_list)
