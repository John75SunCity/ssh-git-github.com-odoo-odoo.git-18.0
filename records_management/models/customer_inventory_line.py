from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError

class CustomerInventoryLine(models.Model):
    _name = 'customer.inventory.line'
    _description = 'Customer Inventory Line'
    _order = 'container_id'

    # ...existing fields (moved from original file)...
    inventory_id = fields.Many2one('customer.inventory', string='Inventory', required=True, ondelete='cascade')
    container_id = fields.Many2one('records.container', string='Container', required=True)
    location_id = fields.Many2one('records.location', string='Location', related='container_id.location_id', store=True)
    file_count = fields.Integer(string='Actual Count')
    expected_file_count = fields.Integer(string='Expected Count')
    previous_file_count = fields.Integer(string='Previous Count')
    verified = fields.Boolean(string='Verified', default=False)
    verification_date = fields.Datetime(string='Verification Date', readonly=True)
    verified_by_id = fields.Many2one('res.users', string='Verified By', readonly=True)
    notes = fields.Text(string='Notes')
    has_variance = fields.Boolean(string='Has Variance', compute='_compute_variance', store=True)
    variance_amount = fields.Integer(string='Variance', compute='_compute_variance', store=True)
    variance_percentage = fields.Float(string='Variance %', compute='_compute_variance', store=True)
    variance_reason = fields.Selection([
        ('counting_error', 'Counting Error'),
        ('missing_files', 'Missing Files'),
        ('extra_files', 'Extra Files'),
        ('system_error', 'System Error'),
        ('other', 'Other')
    ], string='Variance Reason')
    variance_notes = fields.Text(string='Variance Notes')
    container_type_id = fields.Many2one('records.container.type', related='container_id.container_type_id',
                                        string='Container Type', store=True)
    department_id = fields.Many2one('records.department', related='container_id.department_id',
                                    string='Department', store=True)

    @api.depends('file_count', 'expected_file_count')
    def _compute_variance(self):
        for line in self:
            if line.expected_file_count > 0:
                line.variance_amount = line.file_count - line.expected_file_count
                line.has_variance = line.variance_amount != 0
                line.variance_percentage = (line.variance_amount / line.expected_file_count) * 100
            else:
                line.variance_amount = 0
                line.has_variance = False
                line.variance_percentage = 0.0

    def action_verify_line(self):
        self.ensure_one()
        self.write({
            'verified': True,
            'verification_date': fields.Datetime.now(),
            'verified_by_id': self.env.user.id
        })
        self.inventory_id.message_post(body=_(
            "Container %(container)s verified by %(user)s (Count: %(count)s)"
        ) % {
            'container': self.container_id.name,
            'user': self.env.user.name,
            'count': self.file_count,
        })

    def action_update_system_count(self):
        self.ensure_one()
        if not self.has_variance:
            raise UserError(_("No variance to resolve."))
        if not self.env.user.has_group('records_management.group_records_manager'):
            raise UserError(_("Only managers can update system counts."))
        self.container_id.write({'file_count': self.file_count})
        self.write({'expected_file_count': self.file_count})
        self.inventory_id.message_post(body=_(
            "System count updated for container %(container)s: %(files)s files"
        ) % {
            'container': self.container_id.name,
            'files': self.file_count,
        })

    def action_investigate_variance(self):
        self.ensure_one()
        if not self.has_variance:
            raise UserError(_("No variance to investigate."))
        self.env['mail.activity'].create({
            'activity_type_id': self.env.ref('mail.mail_activity_data_call').id,
            'summary': _("Investigate Variance - Container %(container)s") % {
                'container': self.container_id.name,
            },
            'note': _(
                "Variance of %(variance)s files detected. Expected: %(expected)s, Actual: %(actual)s"
            ) % {
                'variance': self.variance_amount,
                'expected': self.expected_file_count,
                'actual': self.file_count,
            },
            'res_id': self.inventory_id.id,
            'res_model_id': self.env.ref('records_management.model_customer_inventory').id,
            'user_id': self.inventory_id.user_id.id,
        })

    @api.constrains('file_count')
    def _check_file_count(self):
        for line in self:
            if line.file_count < 0:
                raise ValidationError(_("File count cannot be negative."))
