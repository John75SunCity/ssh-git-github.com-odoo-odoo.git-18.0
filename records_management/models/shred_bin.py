from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class ShredBin(models.Model):
    _name = 'shred.bin'
    _description = 'Customer Shred Bin'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Bin Number", required=True, copy=False, help="Unique identifier for the shred bin.")
    barcode = fields.Char(string="Barcode", copy=False)
    active = fields.Boolean(default=True, tracking=True)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)

    # ============================================================================
    # RELATIONSHIPS
    # ============================================================================
    partner_id = fields.Many2one('res.partner', string="Customer", required=True, ondelete='restrict', tracking=True)
    department_id = fields.Many2one('records.department', string="Department", domain="[('partner_id', '=', partner_id)]")
    user_id = fields.Many2one('res.users', string="Service Representative", tracking=True)

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

    capacity_pounds = fields.Float(string="Capacity (lbs)", compute='_compute_capacity_pounds', store=True, help="Estimated weight capacity based on bin size.")
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

    _sql_constraints = [
        ('name_company_uniq', 'unique(name, company_id)', 'The Bin Number must be unique per company.'),
        ('barcode_company_uniq', 'unique(barcode, company_id)', 'The Barcode must be unique per company if set.'),
    ]

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('bin_size')
    def _compute_capacity_pounds(self):
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
    self.write({'state': 'deployed'})
    self.message_post(body=_("Bin deployed by %s.") % self.env.user.name)

    def action_mark_full(self):
        self.ensure_one()
        if self.state not in ['in_service', 'deployed']:
            raise UserError(_("Only bins in service can be marked as full."))
    self.write({'state': 'full'})
    self.message_post(body=_("Bin marked as full by %s.") % self.env.user.name)

    def action_start_collection(self):
        self.ensure_one()
        if self.state != 'full':
            raise UserError(_("Only full bins can be collected."))
    self.write({'state': 'collecting'})
    self.message_post(body=_("Bin collection started by %s.") % self.env.user.name)

    def action_complete_service(self):
        self.ensure_one()
        if self.state != 'collecting':
            raise UserError(_("Only bins in transit can have service completed."))
        self.write({
            'state': 'in_service',
            'last_service_date': fields.Datetime.now()
        })
        self.message_post(body=_("Bin service completed by %s.") % self.env.user.name)

    def action_view_services(self):
        self.ensure_one()
        return {
            'name': _('Service Orders'),
            'type': 'ir.actions.act_window',
            'res_model': 'project.task',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', self.service_ids.ids)],
            'context': {'default_shred_bin_id': self.id, 'default_partner_id': self.partner_id.id},
        }
