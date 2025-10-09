from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

# Note: Translation warnings during module loading are expected
# for constraint definitions - this is non-blocking behavior


class ShredBin(models.Model):
    _name = 'shred.bin'
    _description = 'Customer Shred Bin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Bin Number", required=True, copy=False, help="Unique identifier for the shred bin.")
    barcode = fields.Char(string="Barcode", copy=False, required=False)
    active = fields.Boolean(default=True)
    company_id = fields.Many2one(
        "res.company", string="Company", default=lambda self: self.env.company, required=True, readonly=True, index=True
    )

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one(comodel_name='res.partner', string="Customer", required=True, ondelete='restrict', tracking=True)
    department_id = fields.Many2one(
        "records.department",
        string="Department",
        domain=lambda self: self._department_domain(),
    )

    def _department_domain(self):
        partner_id = self.partner_id.id if self.partner_id else False
        return [("partner_id", "=", partner_id)] if partner_id else []

    user_id = fields.Many2one(comodel_name='res.users', string="Service Representative", tracking=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('deployed', 'Deployed'),
        ('in_service', 'In Service'),
        ('full', 'Full'),
        ('collecting', 'In Transit'),
        ('maintenance', 'Maintenance'),
        ('retired', 'Retired'),
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SPECIFICATIONS & DETAILS
    # ============================================================================
    bin_size = fields.Selection([
        ('23', '23 Gallon Shredinator'),
        ('32g', '32 Gallon Bin'),
        ('32c', '32 Gallon Console'),
        ('64', '64 Gallon Bin'),
        ('96', '96 Gallon Bin'),
    ], string="Bin Size", required=True, tracking=True)

    capacity_pounds = fields.Float(
        string="Capacity (lbs)",
        compute="_compute_capacity_pounds",
        store=True,
        help="Estimated weight capacity based on bin size: 23 Gallon Shredinator=60 lbs, 32 Gallon Bin=125 lbs, 32 Gallon Console=90 lbs, 64 Gallon Bin=240 lbs, 96 Gallon Bin=340 lbs. Values based on manufacturer specifications.",
    )
    is_locked = fields.Boolean(string="Is Locked?", default=True)
    description = fields.Text(string="Notes / Description")
    customer_location = fields.Char(string="Specific Location", help="e.g., 'Break Room, 2nd Floor'")

    # ============================================================================
    # SERVICE & USAGE
    # ============================================================================
    service_ids = fields.One2many('project.task', 'shred_bin_id', string="Service Orders")
    service_count = fields.Integer(string="Service Count", compute='_compute_service_count', store=True)
    last_service_date = fields.Datetime(string="Last Service Date", readonly=True)
    needs_collection = fields.Boolean(string="Needs Collection", compute='_compute_needs_collection', store=True)
    product_id = fields.Many2one(comodel_name='barcode.product', string='Barcode Product', ondelete='set null', index=True, help='Optional link to a barcode product template associated with this shred bin.')

    _sql_constraints = [
        ('_name_company_uniq', 'unique(name, company_id)', _('The Bin Number must be unique per company.')),
        ('_barcode_company_uniq', 'unique(barcode, company_id)', _('The Barcode must be unique per company if set.')),
    ]

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('partner_id', 'department_id')
    def _check_department_partner(self):
        """Ensure department belongs to the same partner"""
        for record in self:
            if record.department_id and record.department_id.partner_id != record.partner_id:
                raise ValidationError(_("Department must belong to the selected customer."))

    @api.constrains('name')
    def _check_name_format(self):
        """Validate bin name format"""
        for record in self:
            if not record.name or len(record.name.strip()) < 3:
                raise ValidationError(_("Bin number must be at least 3 characters long."))

    # ============================================================================
    # ORM OVERRIDES
    # ============================================================================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate sequence numbers"""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New') or not vals.get('name'):
                vals['name'] = self.env['ir.sequence'].next_by_code('shred.bin') or _('New')
        return super().create(vals_list)

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('bin_size')
    def _compute_capacity_pounds(self):
        # Mapping based on standard manufacturer capacity specifications for shred bins
        # Source: Industry-standard shredding equipment guidelines (update if specs change)
        capacity_map = {
            '23': 60, '32g': 125, '32c': 90, '64': 240, '96': 340
        }
        for record in self:
            record.capacity_pounds = capacity_map.get(record.bin_size, 0)

    @api.depends('service_ids')
    def _compute_service_count(self):
        for record in self:
            record.service_count = len(record.service_ids)

    @api.depends('state')
    def _compute_needs_collection(self):
        for record in self:
            record.needs_collection = record.state == 'full'

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_deploy(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft bins can be deployed."))
        if not self.partner_id:
            raise UserError(_("Cannot deploy bin without assigned customer."))
        self.write({'state': 'deployed'})
        self.message_post(body=_("Bin deployed by %s.") % self.env.user.name)
        return True

    def action_mark_full(self):
        self.ensure_one()
        if self.state not in ['in_service', 'deployed']:
            raise UserError(_("Only bins in service or deployed can be marked as full."))
        self.write({'state': 'full'})
        self.message_post(body=_("Bin marked as full by %s.") % self.env.user.name)
        return True

    def action_start_collection(self):
        self.ensure_one()
        if self.state != 'full':
            raise UserError(_("Only full bins can be collected."))
        self.write({'state': 'collecting'})
        self.message_post(body=_("Bin collection started by %s.") % self.env.user.name)
        return True

    def action_complete_service(self):
        self.ensure_one()
        if self.state != 'collecting':
            raise UserError(_("Only bins being collected can have service completed."))
        self.write({
            'state': 'in_service',
            'last_service_date': fields.Datetime.now(),
        })
        self.message_post(body=_("Bin service completed by %s.") % self.env.user.name)
        return True

    def action_view_services(self):
        self.ensure_one()
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', self.service_ids.ids)],
            'context': {
                'default_shred_bin_id': self.id,
                'default_partner_id': self.partner_id.id,
            },
        }
