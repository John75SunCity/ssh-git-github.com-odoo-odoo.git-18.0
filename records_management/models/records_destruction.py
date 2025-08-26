from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError


class RecordsDestruction(models.Model):
    _name = 'records.destruction'
    _description = 'Records Destruction'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'destruction_date desc, name'
    _rec_name = 'name'

    # ============================================================================
    # CORE IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(
        string='Name',
        required=True,
        default=lambda self: _('New'),
        tracking=True,
        index=True
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        default=lambda self: self.env.company,
        required=True
    )
    active = fields.Boolean(
        string='Active',
        default=True
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', tracking=True, required=True)

    # ============================================================================
    # BUSINESS SPECIFIC FIELDS
    # ============================================================================
    destruction_date = fields.Datetime(
        string='Destruction Date',
        tracking=True
    )
    destruction_method = fields.Selection([
        ('shredding', 'Shredding'),
        ('incineration', 'Incineration'),
        ('pulverization', 'Pulverization'),
        ('degaussing', 'Degaussing'),
    ], string='Destruction Method', tracking=True)

    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible User',
        default=lambda self: self.env.user,
        tracking=True
    )
    compliance_id = fields.Many2one(
        'naid.compliance.checklist',
        string='NAID Compliance Record'
    )
    naid_compliant = fields.Boolean(
        string='NAID Compliant',
        default=True,
        help='Indicates if destruction follows NAID AAA standards'
    )
    certificate_generated = fields.Boolean(
        string='Certificate Generated',
        default=False,
        tracking=True
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes about the destruction process'
    )

    # ============================================================================
    # RELATIONSHIP FIELDS
    # ============================================================================
    destruction_item_ids = fields.One2many(
        'destruction.item',
        'destruction_id',
        string='Destruction Items'
    )

    # Coordinator link (inverse of work.order.coordinator.destruction_ids)
    coordinator_id = fields.Many2one(
        comodel_name='work.order.coordinator',
        string='Coordinator',
        ondelete='set null',
        index=True,
        help='Work Order Coordinator responsible for this destruction.'
    )

    # ============================================================================
    # COMPUTED FIELDS
    # ============================================================================
    item_count = fields.Integer(
        string='Item Count',
        compute='_compute_item_count',
        store=True
    )
    total_weight = fields.Float(
        string='Total Weight (lbs)',
        compute='_compute_total_weight',
        store=True,
        digits=(12, 2)
    )

    # Mail Thread Framework Fields (REQUIRED for mail.thread inheritance)
    activity_ids = fields.One2many(
        'mail.activity',
        'res_id',
        string='Activities'
    )
    message_follower_ids = fields.One2many(
        'mail.followers',
        'res_id',
        string='Followers'
    )
    message_ids = fields.One2many(
        'mail.message',
        'res_id',
        string='Messages'
    )

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('destruction_item_ids')
    def _compute_item_count(self):
        """Compute the total number of destruction items"""
        for record in self:
            record.item_count = len(record.destruction_item_ids)

    @api.depends('destruction_item_ids', 'destruction_item_ids.weight')
    def _compute_total_weight(self):
        """Compute the total weight of all destruction items"""
        for record in self:
            record.total_weight = sum(record.destruction_item_ids.mapped('weight'))

    # ============================================================================
    # ORM METHODS
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence number"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code('records.destruction') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_schedule(self):
        """Schedule destruction operation"""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Can only schedule draft destructions'))
        self.write({'state': 'scheduled'})
        self.message_post(body=_('Destruction scheduled'))

    def action_start(self):
        """Start destruction operation"""
        self.ensure_one()
        if self.state != 'scheduled':
            raise UserError(_('Can only start scheduled destructions'))
        self.write({'state': 'in_progress'})
        self.message_post(body=_('Destruction started'))

    def action_complete(self):
        """Complete destruction operation"""
        self.ensure_one()
        if self.state != 'in_progress':
            raise UserError(_('Can only complete in-progress destructions'))
        self.write({
            'state': 'completed',
            'destruction_date': fields.Datetime.now()
        })
        self.message_post(body=_('Destruction completed'))

    def action_cancel(self):
        """Cancel destruction operation"""
        self.ensure_one()
        if self.state == 'completed':
            raise UserError(_('Cannot cancel completed destructions'))
        self.write({'state': 'cancelled'})
        self.message_post(body=_('Destruction cancelled'))

    def action_generate_certificate(self):
        """Generate destruction certificate"""
        self.ensure_one()
        if self.state != 'completed':
            raise UserError(_('Can only generate certificates for completed destructions'))

        # Create NAID certificate if not exists
        if not self.certificate_generated:
            certificate_vals = {
                'name': _('Destruction Certificate - %s') % self.name,
                'partner_id': self.partner_id.id,
                'destruction_date': self.destruction_date,
                'destruction_method': self.destruction_method,
                'total_weight': self.total_weight,
                'destruction_id': self.id,
            }

            certificate = self.env['naid.certificate'].create(certificate_vals)
            self.write({'certificate_generated': True})
            self.message_post(body=_('Destruction certificate generated'))

            return {
                'type': 'ir.actions.act_window',
                'name': _('Destruction Certificate'),
                'res_model': 'naid.certificate',
                'res_id': certificate.id,
                'view_mode': 'form',
                'target': 'current',
            }

    # ============================================================================
    # VALIDATION METHODS
    # ============================================================================
    @api.constrains('destruction_date')
    def _check_destruction_date(self):
        """Validate destruction date"""
        for record in self:
            if record.destruction_date and record.destruction_date > fields.Datetime.now():
                raise ValidationError(_('Destruction date cannot be in the future'))

    @api.constrains('destruction_item_ids', 'state')
    def _check_destruction_items(self):
        """Validate destruction items"""
        for record in self:
            if record.state in ['in_progress', 'completed'] and not record.destruction_item_ids:
                raise ValidationError(_('Destruction must have at least one item to process'))


