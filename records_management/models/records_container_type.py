from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class RecordsContainerType(models.Model):
    _name = 'records.container.type'
    _description = 'Records Container Type'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ============================================================================
    # CORE & IDENTIFICATION FIELDS
    # ============================================================================
    name = fields.Char(string="Type Name", required=True, index=True)
    code = fields.Char(string="Type Code", required=True, index=True)
    active = fields.Boolean(default=True)
    sequence = fields.Integer(string="Sequence", default=10)
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company, required=True, readonly=True)
    currency_id = fields.Many2one(related='company_id.currency_id', readonly=True, comodel_name='res.currency')
    description = fields.Text(string="Description")

    # ============================================================================
    # PHYSICAL SPECIFICATIONS
    # ============================================================================
    dimensions = fields.Char(string="Dimensions (LxWxH)", help="e.g., 12x15x10")
    length = fields.Float(string="Length (in)")
    width = fields.Float(string="Width (in)")
    height = fields.Float(string="Height (in)")
    cubic_feet = fields.Float(string="Cubic Feet", compute='_compute_cubic_feet', store=True)
    weight_capacity = fields.Float(string="Weight Capacity (lbs)")
    average_weight_lbs = fields.Float(string="Average Weight (lbs)", help="Average weight of containers of this type")

    # ============================================================================
    # PRICING & BILLING
    # ============================================================================
    standard_rate = fields.Monetary(string="Standard Monthly Rate", currency_field="currency_id", tracking=True)
    setup_fee = fields.Monetary(string="Setup Fee", currency_field="currency_id", tracking=True)
    handling_fee = fields.Monetary(string="Handling Fee", currency_field="currency_id", tracking=True)
    destruction_fee = fields.Monetary(string="Destruction Fee", currency_field="currency_id", tracking=True)

    # ============================================================================
    # RELATIONSHIPS & STATISTICS
    # ============================================================================
    container_ids = fields.One2many('records.container', 'container_type_id', string="Containers")
    container_count = fields.Integer(string="Container Count", compute='_compute_container_count', store=True)

    # ============================================================================
    # STATE & LIFECYCLE
    # ============================================================================
    state = fields.Selection([
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('archived', 'Archived')
    ], string="Status", default='draft', required=True, tracking=True)

    # ============================================================================
    # SQL CONSTRAINTS
    # ============================================================================
    _code_company_uniq = models.Constraint('unique(code, company_id)', _('The container type code must be unique per company.'))
    _name_company_uniq = models.Constraint('unique(name, company_id)', _('The container type name must be unique per company.'))

    # ============================================================================
    # COMPUTE METHODS
    # ============================================================================
    @api.depends('length', 'width', 'height')
    def _compute_cubic_feet(self):
        """Calculate volume in cubic feet from dimensions in inches."""
        for record in self:
            if record.length > 0 and record.width > 0 and record.height > 0:
                # Convert cubic inches to cubic feet (1728 cubic inches = 1 cubic foot)
                record.cubic_feet = (record.length * record.width * record.height) / 1728
            else:
                record.cubic_feet = 0.0

    @api.depends('container_ids')
    def _compute_container_count(self):
        for record in self:
            record.container_count = len(record.container_ids)

    # ============================================================================
    # ONCHANGE METHODS
    # ============================================================================
    @api.onchange('length', 'width', 'height')
    def _onchange_dimensions(self):
        """Update the display dimensions string when individual dimensions change."""
        if self.length > 0 and self.width > 0 and self.height > 0:
            self.dimensions = f"{self.length}x{self.width}x{self.height}"
        else:
            self.dimensions = ""

    # ============================================================================
    # ACTION METHODS
    # ============================================================================
    def action_activate(self):
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_("Only draft container types can be activated."))
        self.write({'state': 'active'})
        self.message_post(body=_("Container type has been activated."))

    def action_archive(self):
        self.ensure_one()
        if self.container_count > 0:
            raise UserError(_("You cannot archive a container type that is still in use by containers."))
        self.write({'state': 'archived', 'active': False})
        self.message_post(body=_("Container type has been archived."))

    def action_view_containers(self):
        self.ensure_one()
        return {
            "name": _("Containers of Type: %s", self.name),
            "type": "ir.actions.act_window",
            "res_model": "records.container",
            "view_mode": "tree,form,kanban",
            "domain": [("container_type_id", "=", self.id)],
            "context": {"default_container_type_id": self.id},
        }

    # ============================================================================
    # CONSTRAINTS
    # ============================================================================
    @api.constrains('length', 'width', 'height', 'weight_capacity')
    def _check_positive_values(self):
        for record in self:
            if record.length < 0 or record.width < 0 or record.height < 0 or record.weight_capacity < 0:
                raise ValidationError(_("Physical dimensions and capacity must be non-negative."))

    @api.constrains('standard_rate', 'setup_fee', 'handling_fee', 'destruction_fee')
    def _check_positive_pricing(self):
        for record in self:
            if record.standard_rate < 0 or record.setup_fee < 0 or record.handling_fee < 0 or record.destruction_fee < 0:
                raise ValidationError(_("Pricing fields cannot be negative."))
