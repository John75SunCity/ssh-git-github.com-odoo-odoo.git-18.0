from odoo import api, fields, models, _


class HardDriveScan(models.Model):
    _name = 'hard.drive.scan'
    _description = 'Hard Drive Scan'

    name = fields.Char(string='Name', required=True)
    status = fields.Selection([
        ('pending', 'Pending'),
        ('completed', 'Completed'),
    ], string='Status', default='pending', required=True)

    def action_complete(self):
        for rec in self:
            rec.status = 'completed'
        return True
