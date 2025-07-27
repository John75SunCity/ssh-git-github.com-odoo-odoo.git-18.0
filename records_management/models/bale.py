from odoo import models, fields, api

class Bale(models.Model):
    _name = 'records_management.bale'
    _description = 'Shredded Paper Bale'
    _inherit = ['mail.thread', 'mail.activity.mixin']  # Audit logs, notifications

    name = fields.Char(default=lambda self: self.env['ir.sequence'].next_by_code('records_management.bale'))
    paper_type = fields.Selection([('white', 'White'), ('mix', 'Mix'), ('cardboard', 'Cardboard')], required=True)
    weight = fields.Float(required=True)
    technician_id = fields.Many2one('hr.employee', required=True)
    signature = fields.Binary(attachment=True)
    date = fields.Date(default=fields.Date.today())
    load_id = fields.Many2one('records_management.load')
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company)
    qr_code = fields.Binary(compute='_compute_qr_code')  # Innovative: QR for tracking)

    @api.depends('name', 'paper_type', 'weight', 'technician_id.name', 'date')
    def _compute_qr_code(self):
        import qrcode
        from io import BytesIO
        for bale in self:
            qr = qrcode.QRCode()
            qr.add_data(f'Bale: {bale.name} | Type: {bale.paper_type} | Weight: {bale.weight} | Tech: {bale.technician_id.name} | Date: {bale.date}')
            qr.make(fit=True)
            img = qr.make_image(fill='black', back_color='white')
            buffer = BytesIO()
            img.save(buffer, 'PNG')
            bale.qr_code = buffer.getvalue()